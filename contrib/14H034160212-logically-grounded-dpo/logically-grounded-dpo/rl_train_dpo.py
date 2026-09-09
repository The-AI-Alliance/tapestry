"""
RLearner-LLM Step 3 (Recommended): DPO Fine-tuning with LoRA
TRL 0.7.1 + Transformers 4.31.0 compatible (llm-tuning conda env)

Direct Preference Optimization trains the model to prefer high-quality
explanations (chosen) over low-quality ones (rejected) without a separate
reward model during training.

Dataset format expected (from rl_build_preference_data.py):
  {"prompt": "<Alpaca prompt ending with ### Response:\\n>",
   "chosen": "<good explanation>",
   "rejected": "<bad explanation>"}

Usage (4x A100 80GB, GPUs 4-7):
    CUDA_VISIBLE_DEVICES=4,5,6,7 torchrun --nproc_per_node=4 --master_port 29501 \\
        rl_train_dpo.py \\
        --model_name_or_path /data/shared/llama2/llama-2-13b-hf \\
        --sft_adapter_path ./rl_sft_llama2_13b_generator \\
        --preference_data_path ./rl_preference_data/preference_pairs.json \\
        --output_dir ./rl_dpo_llama2_13b_generator \\
        --num_train_epochs 2 \\
        --per_device_train_batch_size 1 \\
        --gradient_accumulation_steps 8 \\
        --beta 0.1 \\
        --bf16 True \\
        --gradient_checkpointing True \\
        --report_to none
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import torch
import transformers
from datasets import Dataset
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import DPOTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    model_name_or_path: str = field(
        default="/data/shared/llama2/llama-2-13b-hf",
        metadata={"help": "Base model path. Must match the model used for SFT."},
    )
    sft_adapter_path: Optional[str] = field(
        default=None,
        metadata={"help": "SFT LoRA adapter directory. Merged into base before DPO."},
    )
    cache_dir: Optional[str] = field(default="cache")


@dataclass
class DataArguments:
    preference_data_path: str = field(
        default="./rl_preference_data/preference_pairs.json",
        metadata={"help": "Preference pairs JSON (fields: prompt, chosen, rejected)."},
    )
    eval_data_path: Optional[str] = field(default=None)


@dataclass
class DPOArguments:
    beta: float = field(
        default=0.1,
        metadata={"help": "KL penalty coefficient. Lower = more aggressive; higher = conservative."},
    )
    max_length: int = field(
        default=1024,
        metadata={"help": "Max total sequence length (prompt + response)."},
    )
    max_prompt_length: int = field(
        default=512,
        metadata={"help": "Max prompt length. Longer prompts are truncated."},
    )
    min_score_gap_filter: float = field(
        default=0.0,
        metadata={"help": "Skip pairs whose score_gap is below this threshold."},
    )


@dataclass
class LoraArguments:
    lora_r: int = field(default=16)
    lora_alpha: int = field(default=32)
    lora_dropout: float = field(default=0.05)
    lora_target_modules: str = field(
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
    )


def load_preference_dataset(data_path: str, min_score_gap: float = 0.0) -> Dataset:
    """
    Load preference pairs as plain-text {prompt, chosen, rejected}.

    TRL 0.7.1 DPOTrainer expects:
      prompt   -> str (Alpaca-format query ending with '### Response:\\n')
      chosen   -> str (good explanation text only, no prompt prefix)
      rejected -> str (bad explanation text only, no prompt prefix)
    """
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    examples = []
    skipped = 0
    for item in raw_data:
        prompt = item.get("prompt", "").strip()
        chosen = item.get("chosen", "").strip()
        rejected = item.get("rejected", "").strip()
        score_gap = item.get("score_gap", 1.0)

        if not prompt or not chosen or not rejected:
            skipped += 1
            continue
        if score_gap < min_score_gap:
            skipped += 1
            continue

        examples.append({"prompt": prompt, "chosen": chosen, "rejected": rejected})

    logger.info(f"Loaded {len(examples)} preference pairs from {data_path} " f"(skipped {skipped} invalid/low-gap).")
    return Dataset.from_list(examples)


def main():
    parser = transformers.HfArgumentParser(
        (ModelArguments, DataArguments, DPOArguments, LoraArguments, TrainingArguments)
    )
    model_args, data_args, dpo_args, lora_args, training_args = parser.parse_args_into_dataclasses()

    # ── Tokenizer ──────────────────────────────────────────────────────────────
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        padding_side="left",  # DPO prefers left-padding for decoder-only models
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Model ──────────────────────────────────────────────────────────────────
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto",
    )
    model.config.use_cache = False

    # ── Merge SFT LoRA (optional) ──────────────────────────────────────────────
    if model_args.sft_adapter_path and os.path.isdir(model_args.sft_adapter_path):
        logger.info(f"Merging SFT LoRA adapter from {model_args.sft_adapter_path} ...")
        model = PeftModel.from_pretrained(model, model_args.sft_adapter_path)
        model = model.merge_and_unload()
        logger.info("SFT adapter merged into base model.")

    # ── LoRA for DPO ──────────────────────────────────────────────────────────
    target_modules = [m.strip() for m in lora_args.lora_target_modules.split(",")]
    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        lora_dropout=lora_args.lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    # Apply LoRA manually so we can call enable_input_require_grads() before
    # the trainer takes ownership. This fixes "element 0 does not require grad"
    # when gradient_checkpointing=True is used alongside LoRA frozen base weights.
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()
    logger.info(f"DPO LoRA: r={lora_args.lora_r}, alpha={lora_args.lora_alpha}, beta={dpo_args.beta}")

    # ── Dataset ────────────────────────────────────────────────────────────────
    train_dataset = load_preference_dataset(
        data_args.preference_data_path,
        min_score_gap=dpo_args.min_score_gap_filter,
    )
    eval_dataset = None
    if data_args.eval_data_path:
        eval_dataset = load_preference_dataset(data_args.eval_data_path)

    # ── DPO Trainer (TRL 0.7.1 API) ───────────────────────────────────────────
    # In TRL 0.7.1:
    #   - beta is a direct positional/keyword arg (not part of a config class)
    #   - ref_model=None: DPOTrainer creates a frozen copy of the initial model
    #     weights automatically as the reference policy
    #   - max_length and max_prompt_length are direct args (not in TrainingArguments)
    #   - peft_config omitted — LoRA already applied above
    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        beta=dpo_args.beta,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        max_length=dpo_args.max_length,
        max_prompt_length=dpo_args.max_prompt_length,
        disable_dropout=True,
    )

    logger.info("Starting DPO training...")
    logger.info(f"  Training examples: {len(train_dataset)}")
    logger.info(f"  Beta (KL penalty): {dpo_args.beta}")
    logger.info(f"  Max length: {dpo_args.max_length} / prompt: {dpo_args.max_prompt_length}")

    trainer.train()
    trainer.save_model(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)
    logger.info(f"DPO LoRA adapter saved to {training_args.output_dir}")

    # Save training log
    metrics_path = os.path.join(training_args.output_dir, "dpo_train_metrics.json")
    if hasattr(trainer, "state") and trainer.state.log_history:
        with open(metrics_path, "w") as f:
            json.dump(trainer.state.log_history, f, indent=2)
        logger.info(f"Training metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
