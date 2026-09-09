"""
RLearner-LLM PPO with NLI Reward (LLaMA-2-13B)

Replaces verifier reward with NLI entailment probability:
  reward = P(entailment | premise=explanation, hypothesis=correct_option_text)

This directly optimises the most discriminative metric (NLI), avoiding the
alignment tax observed when using verifier reward for Qwen3.

Usage (two GPUs, actor on cuda:0, NLI on CPU):
    CUDA_VISIBLE_DEVICES=5,7 python rl_train_ppo_nli.py \
        --model_name_or_path /data/shared/llama2/llama-2-13b-hf \
        --sft_adapter_path ./rl_dpo_nli_llama2_generator \
        --output_dir ./rl_ppo_nli_llama2_generator \
        --data_path ./Paul_new_data/Merged_Sydney_Cardiff_Law_Medical_Y1_Y2/generator_merged_avg_3_lenexp_10.json \
        --batch_size 4 --mini_batch_size 1 --ppo_epochs 4 \
        --learning_rate 1e-5 --max_questions 500

Two-stage pipeline: pass --sft_adapter_path ./rl_dpo_nli_llama2_generator to
initialise PPO from the NLI-DPO adapter instead of the SFT adapter.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import torch
import transformers
from datasets import Dataset
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ALPACA_PROMPT = (
    "Below is an instruction that describes a task, paired with an input that "
    "provides further context. Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n"
    "### Input:\n{input}\n\n"
    "### Response:\n"
)


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class ModelArguments:
    model_name_or_path: str = field(default="/data/shared/llama2/llama-2-13b-hf")
    sft_adapter_path: Optional[str] = field(
        default="./rl_sft_llama2_13b_generator",
        metadata={"help": "SFT or DPO-NLI LoRA adapter to initialise the Actor."},
    )
    output_dir: str = field(default="./rl_ppo_nli_llama2_generator")
    nli_model: str = field(default="cross-encoder/nli-deberta-v3-small")
    nli_device: str = field(default="cpu", metadata={"help": "Device for NLI reward model."})
    use_4bit: bool = field(default=False)
    cache_dir: Optional[str] = field(default="cache")
    use_flash_attention: bool = field(default=True)


@dataclass
class DataArguments:
    data_path: str = field(
        default="./Paul_new_data/Merged_Sydney_Cardiff_Law_Medical_Y1_Y2/generator_merged_avg_3_lenexp_10.json"
    )
    max_questions: Optional[int] = field(default=500)


@dataclass
class LoraArguments:
    lora_r: int = field(default=16)
    lora_alpha: int = field(default=32)
    lora_dropout: float = field(default=0.05)
    lora_target_modules: str = field(default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")


# ── Helper functions ──────────────────────────────────────────────────────────


def extract_correct_option_text(input_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract the correct answer option text from training data input field."""
    m = re.search(r"The correct answer is Option ([A-Z])", input_text)
    if not m:
        return None, None
    letter = m.group(1)
    opt_pat = rf"Option {letter}:\s*(.+?)(?:\s+Option [A-Z]:|The correct answer|$)"
    opt_m = re.search(opt_pat, input_text, re.DOTALL)
    return letter, opt_m.group(1).strip() if opt_m else None


# ── NLI Reward Model ──────────────────────────────────────────────────────────


class NLIRewardModel:
    """
    Uses DeBERTa NLI entailment probability as the PPO reward signal.

    reward = P(entailment | premise=explanation, hypothesis=correct_option_text)

    This directly optimises answer-grounded explanation quality — the most
    discriminative metric observed in our experiments.
    """

    def __init__(
        self, model_name: str = "cross-encoder/nli-deberta-v3-small", device: str = "cpu", cache_dir: str = "cache"
    ):
        logger.info(f"Loading NLI reward model: {model_name} on {device} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir, use_fast=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir).to(device)
        self.model.eval()
        self.device = device

        id2label = self.model.config.id2label
        self.entailment_idx = next(k for k, v in id2label.items() if v.lower() == "entailment")
        logger.info(f"NLI reward loaded. entailment_idx={self.entailment_idx}")

    @torch.no_grad()
    def get_rewards(self, correct_options: List[str], explanations: List[str]) -> List[torch.Tensor]:
        """
        Score batch: P(explanation entails correct_option) for each pair.
        Returns list of scalar float tensors in [0, 1].
        """
        # Skip pairs where correct option could not be extracted
        enc = self.tokenizer(
            explanations,
            correct_options,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        logits = self.model(**enc).logits
        probs = torch.softmax(logits, dim=-1)
        entailment_probs = probs[:, self.entailment_idx]
        return [torch.tensor(p.item(), dtype=torch.float32) for p in entailment_probs]


# ── Dataset ───────────────────────────────────────────────────────────────────


def build_ppo_dataset(data_path: str, tokenizer, max_questions: Optional[int] = None) -> Dataset:
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    if max_questions:
        raw_data = raw_data[:max_questions]

    examples = []
    skipped = 0
    for item in raw_data:
        instruction = item.get("instruction", "").replace("</s>", "").strip()
        input_text = item.get("input", "").replace("</s>", "").strip()
        if not input_text:
            continue

        _, correct_opt = extract_correct_option_text(input_text)
        if not correct_opt:
            skipped += 1
            continue  # NLI reward requires correct option text

        prompt = ALPACA_PROMPT.format(instruction=instruction, input=input_text)
        tokenized = tokenizer(prompt, truncation=True, max_length=512)
        examples.append(
            {
                "input_ids": tokenized["input_ids"],
                "query": prompt,
                "question_input": input_text,
                "correct_option": correct_opt,
            }
        )

    logger.info(f"PPO dataset: {len(examples)} questions loaded ({skipped} skipped, no option text)")
    return Dataset.from_list(examples)


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, LoraArguments, PPOConfig))
    model_args, data_args, lora_args, ppo_config = parser.parse_args_into_dataclasses()
    ppo_config.remove_unused_columns = False

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        padding_side="left",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Actor model
    bnb_config = None
    if model_args.use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    attn_impl = "flash_attention_2" if model_args.use_flash_attention else "eager"
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
            quantization_config=bnb_config,
            torch_dtype=torch.bfloat16,
            device_map="auto" if bnb_config else None,
            trust_remote_code=True,
            attn_implementation=attn_impl,
        )
    except Exception:
        logger.warning("flash_attention_2 unavailable, falling back to eager.")
        base_model = AutoModelForCausalLM.from_pretrained(
            model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
            quantization_config=bnb_config,
            torch_dtype=torch.bfloat16,
            device_map="auto" if bnb_config else None,
            trust_remote_code=True,
        )

    if model_args.sft_adapter_path and os.path.isdir(model_args.sft_adapter_path):
        logger.info(f"Merging adapter from {model_args.sft_adapter_path} ...")
        base_model = PeftModel.from_pretrained(base_model, model_args.sft_adapter_path)
        base_model = base_model.merge_and_unload()
        logger.info("Adapter merged.")

    target_modules = [m.strip() for m in lora_args.lora_target_modules.split(",")]
    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        lora_dropout=lora_args.lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    base_model = get_peft_model(base_model, lora_config)
    base_model.print_trainable_parameters()

    actor_model = AutoModelForCausalLMWithValueHead.from_pretrained(base_model)
    if not model_args.use_4bit:
        actor_model = actor_model.cuda()
        logger.info("Actor moved to GPU.")

    # NLI Reward Model (on CPU — no separate GPU needed)
    reward_model = NLIRewardModel(
        model_name=model_args.nli_model,
        device=model_args.nli_device,
        cache_dir=model_args.cache_dir,
    )

    dataset = build_ppo_dataset(
        data_path=data_args.data_path,
        tokenizer=tokenizer,
        max_questions=data_args.max_questions,
    )

    def collator(data):
        return {key: [d[key] for d in data] for key in data[0]}

    ppo_trainer = PPOTrainer(
        config=ppo_config,
        model=actor_model,
        ref_model=None,
        tokenizer=tokenizer,
        dataset=dataset,
        data_collator=collator,
    )

    gen_kwargs = {
        "max_new_tokens": 300,
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 50,
        "repetition_penalty": 1.1,
        "pad_token_id": tokenizer.eos_token_id,
    }

    logger.info("Starting PPO-NLI training (LLaMA-2)...")

    for epoch, batch in enumerate(ppo_trainer.dataloader):
        query_tensors = [torch.tensor(ids, dtype=torch.long) for ids in batch["input_ids"]]
        correct_options = batch["correct_option"]

        response_tensors = ppo_trainer.generate(query_tensors, return_prompt=False, **gen_kwargs)
        batch["response"] = [tokenizer.decode(r, skip_special_tokens=True) for r in response_tensors]

        rewards = reward_model.get_rewards(
            correct_options=correct_options,
            explanations=batch["response"],
        )

        stats = ppo_trainer.step(query_tensors, response_tensors, rewards)
        ppo_trainer.log_stats(stats, batch, rewards)

        if epoch % 50 == 0:
            mean_reward = sum(r.item() for r in rewards) / len(rewards)
            logger.info(
                f"Step {epoch} | Mean NLI reward: {mean_reward:.4f} | " f"KL: {stats.get('objective/kl', 0):.4f}"
            )

    os.makedirs(model_args.output_dir, exist_ok=True)
    ppo_trainer.save_pretrained(model_args.output_dir)
    tokenizer.save_pretrained(model_args.output_dir)
    logger.info(f"PPO-NLI adapter saved to {model_args.output_dir}")


if __name__ == "__main__":
    main()
