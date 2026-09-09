"""
RLearner-LLM Step 1: SFT Fine-tuning with LoRA
TRL 0.7.1 + Transformers 4.31.0 compatible (llm-tuning conda env)

Fine-tunes LLaMA-2-13B on PeerWise explanation data using LoRA (PEFT).
Uses standard Alpaca prompt format consistent with the legacy ILearner pipeline.

Usage (4x A100 80GB, GPUs 4-7):
    CUDA_VISIBLE_DEVICES=4,5,6,7 torchrun --nproc_per_node=4 --master_port 29500 \\
        rl_train_sft.py \\
        --model_name_or_path /data/shared/llama2/llama-2-13b-hf \\
        --data_path ./Paul_new_data/Merged_Sydney_Cardiff_Law_Medical_Y1_Y2/generator_merged_avg_3_lenexp_10.json \\
        --output_dir ./rl_sft_llama2_13b_generator \\
        --num_train_epochs 3 \\
        --per_device_train_batch_size 1 \\
        --gradient_accumulation_steps 8 \\
        --bf16 True \\
        --gradient_checkpointing True \\
        --report_to none
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import torch
import transformers
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Alpaca-style prompt template — must match rl_build_preference_data.py
ALPACA_TEMPLATE = (
    "Below is an instruction that describes a task, paired with an input that "
    "provides further context. Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n"
    "### Input:\n{input}\n\n"
    "### Response:\n{output}"
)


@dataclass
class ModelArguments:
    model_name_or_path: str = field(
        default="/data/shared/llama2/llama-2-13b-hf",
        metadata={"help": "Local path or HuggingFace model ID. Default: LLaMA-2-13B-HF."},
    )
    cache_dir: Optional[str] = field(default="cache")


@dataclass
class DataArguments:
    data_path: str = field(
        default="./Paul_new_data/Merged_Sydney_Cardiff_Law_Medical_Y1_Y2/generator_merged_avg_3_lenexp_10.json",
        metadata={"help": "Training data JSON with fields: instruction, input, output."},
    )
    eval_data_path: Optional[str] = field(default=None)
    max_seq_length: int = field(default=1024)


@dataclass
class LoraArguments:
    lora_r: int = field(default=16)
    lora_alpha: int = field(default=32)
    lora_dropout: float = field(default=0.05)
    lora_target_modules: str = field(
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        metadata={"help": "Comma-separated LoRA target modules. Works for LLaMA-2/Qwen3."},
    )


def load_peerwise_data(data_path: str) -> Dataset:
    """Load PeerWise JSON and convert to Alpaca text format for SFTTrainer."""
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    examples = []
    skipped = 0
    for item in raw_data:
        instruction = item.get("instruction", "").replace("</s>", "").strip()
        input_text = item.get("input", "").replace("</s>", "").strip()
        output_text = item.get("output", "").replace("</s>", "").strip()

        if not input_text or not output_text:
            skipped += 1
            continue

        text = ALPACA_TEMPLATE.format(
            instruction=instruction,
            input=input_text,
            output=output_text,
        )
        examples.append({"text": text})

    logger.info(f"Loaded {len(examples)} training examples from {data_path} (skipped {skipped} empty).")
    return Dataset.from_list(examples)


def main():
    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, LoraArguments, TrainingArguments))
    model_args, data_args, lora_args, training_args = parser.parse_args_into_dataclasses()

    # ── Tokenizer ──────────────────────────────────────────────────────────────
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        padding_side="right",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        logger.info("pad_token set to eos_token.")

    # ── Model ──────────────────────────────────────────────────────────────────
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    model.config.use_cache = False  # Required when gradient_checkpointing=True

    # ── LoRA ───────────────────────────────────────────────────────────────────
    target_modules = [m.strip() for m in lora_args.lora_target_modules.split(",")]
    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        lora_dropout=lora_args.lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    # Apply LoRA manually so we can call enable_input_require_grads().
    # When gradient_checkpointing=True, PyTorch requires at least one input to
    # have requires_grad=True at each checkpointed module boundary. LoRA freezes
    # the base weights, so we register a forward hook on the input embeddings to
    # propagate gradients through the checkpointed regions.
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    # ── Dataset ────────────────────────────────────────────────────────────────
    train_dataset = load_peerwise_data(data_args.data_path)
    eval_dataset = None
    if data_args.eval_data_path:
        eval_dataset = load_peerwise_data(data_args.eval_data_path)

    # ── SFT Training (TRL 0.7.1 API) ──────────────────────────────────────────
    # peft_config is omitted — LoRA is already applied above.
    # TRL 0.7.1: SFTTrainer takes dataset_text_field and max_seq_length directly.
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=data_args.max_seq_length,
    )

    logger.info("Starting SFT training...")
    logger.info(f"  Model: {model_args.model_name_or_path}")
    logger.info(f"  Training examples: {len(train_dataset)}")
    logger.info(f"  Epochs: {training_args.num_train_epochs}")
    logger.info(f"  Per-device batch size: {training_args.per_device_train_batch_size}")
    logger.info(f"  Gradient accumulation: {training_args.gradient_accumulation_steps}")

    trainer.train()
    trainer.save_model(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)
    logger.info(f"LoRA adapter saved to {training_args.output_dir}")


if __name__ == "__main__":
    main()
