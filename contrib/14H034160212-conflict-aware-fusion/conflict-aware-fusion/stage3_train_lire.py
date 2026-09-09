"""
Stage 3 Training: LIRE (Logical Invariance REgularization)

Core idea:
  L_total = L_SFT + lambda * L_invariance

L_SFT: standard cross-entropy on (base_facts, base_rules, question) -> label
L_invariance: KL divergence between model distributions for logically equivalent inputs
              KL( p(base) || p(variant4) )
              Forces model to produce the same prediction for equivalent formulations.

Why this matters:
  Standard SFT (Qwen) achieves 1.0 on base but only 0.327 on De Morgan variant.
  This is because SFT learns surface patterns, not logical structure.
  LIRE explicitly penalizes inconsistency under logical equivalence.

Data: data/train_lire_pairs.csv
  Columns: group_id, law, base_facts, base_rules, equiv_facts, equiv_rules, questions, answers
  Each row is (base, variant4) pair that should receive identical predictions.
"""

import argparse
import os

os.environ.setdefault("HF_HOME", os.path.join(os.getcwd(), ".cache/huggingface"))
os.environ.setdefault("HF_DATASETS_CACHE", os.path.join(os.environ["HF_HOME"], "datasets"))
os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(os.environ["HF_HOME"], "transformers"))

import torch
import torch.nn.functional as F
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, PeftModel

MODEL_LIST = {
    "qwen": "Qwen/Qwen2-1.5B",
    "qwen3": "/data/shared/qwen3/Qwen3-8B",
    "llama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "bert": "bert-base-uncased",
}

STAGE1_DIRS = {
    "qwen": "./trained_models/qwen",
    "qwen3": "./trained_models/qwen3",
    "llama": "./trained_models/llama",
    "bert": "./trained_models/bert",
}


def encode_text(facts, rules, question, tokenizer, max_length=512):
    text = facts + " " + rules + " " + question
    enc = tokenizer(text, truncation=True, padding="max_length", max_length=max_length)
    return enc["input_ids"], enc["attention_mask"]


def build_lire_dataset(csv_path: str, tokenizer, max_length: int = 512):
    """
    Build dataset of (base, equiv) pairs from train_lire_pairs.csv.
    Each sample has both base and equiv encoded, sharing the same label.
    """
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} pair rows from {csv_path}")

    samples = []
    for _, row in df.iterrows():
        questions = str(row["questions"]).split(" | ")
        answers = str(row["answers"]).split(" | ")
        base_facts = str(row["base_facts"])
        base_rules = str(row["base_rules"])
        equiv_facts = str(row["equiv_facts"])
        equiv_rules = str(row["equiv_rules"])

        for q, a in zip(questions, answers):
            label = 1 if a.strip() == "T" else 0
            b_ids, b_mask = encode_text(base_facts, base_rules, q, tokenizer, max_length)
            e_ids, e_mask = encode_text(equiv_facts, equiv_rules, q, tokenizer, max_length)
            samples.append(
                {
                    "base_input_ids": b_ids,
                    "base_attention_mask": b_mask,
                    "equiv_input_ids": e_ids,
                    "equiv_attention_mask": e_mask,
                    "labels": label,
                }
            )

    print(f"  Total LIRE pair samples: {len(samples)}")
    return Dataset.from_list(samples)


def lire_collator(batch):
    """Stack base and equiv into a single batch for parallel forward pass."""
    return {
        "base_input_ids": torch.tensor([x["base_input_ids"] for x in batch]),
        "base_attention_mask": torch.tensor([x["base_attention_mask"] for x in batch]),
        "equiv_input_ids": torch.tensor([x["equiv_input_ids"] for x in batch]),
        "equiv_attention_mask": torch.tensor([x["equiv_attention_mask"] for x in batch]),
        "labels": torch.tensor([x["labels"] for x in batch]),
    }


class LIRETrainer(Trainer):
    """
    Custom Trainer implementing LIRE loss:
      L = L_SFT(base) + lambda * L_invariance(base, equiv)

    L_invariance = KL(p_base || p_equiv) + KL(p_equiv || p_base)  (symmetric KL)
    """

    def __init__(self, lire_lambda: float = 1.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lire_lambda = lire_lambda

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs["labels"]
        base_ids = inputs["base_input_ids"]
        base_mask = inputs["base_attention_mask"]
        equiv_ids = inputs["equiv_input_ids"]
        equiv_mask = inputs["equiv_attention_mask"]

        # Forward pass: base
        out_base = model(input_ids=base_ids, attention_mask=base_mask)
        logits_base = out_base.logits  # (B, 2)

        # Forward pass: equiv
        out_equiv = model(input_ids=equiv_ids, attention_mask=equiv_mask)
        logits_equiv = out_equiv.logits  # (B, 2)

        # SFT loss (on base only — equiv has same label, so one CE is enough)
        l_sft = F.cross_entropy(logits_base, labels)

        # Invariance loss: symmetric KL divergence
        p_base = F.softmax(logits_base, dim=-1)  # (B, 2)
        p_equiv = F.softmax(logits_equiv, dim=-1)  # (B, 2)
        # KL(p_base || p_equiv) + KL(p_equiv || p_base)
        kl_fwd = F.kl_div(p_equiv.log(), p_base, reduction="batchmean")
        kl_bwd = F.kl_div(p_base.log(), p_equiv, reduction="batchmean")
        l_inv = (kl_fwd + kl_bwd) / 2.0

        loss = l_sft + self.lire_lambda * l_inv

        if self.state.global_step % 20 == 0:
            print(
                f"  step={self.state.global_step} "
                f"l_sft={l_sft.item():.4f} "
                f"l_inv={l_inv.item():.4f} "
                f"l_total={loss.item():.4f}",
                flush=True,
            )

        return (loss, out_base) if return_outputs else loss


def build_lora_config(model_name: str) -> LoraConfig:
    lower = model_name.lower()
    if "qwen3" in lower or "qwen3-8b" in lower:
        # Qwen3 q_norm/k_norm conflict with LoRA on q_proj/k_proj
        target_modules = ["v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    elif "llama" in lower or "qwen" in lower or "tinyllama" in lower:
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    else:
        target_modules = ["query", "value"]
    return LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=target_modules,
        lora_dropout=0.05,
        bias="none",
        task_type="SEQ_CLS",
    )


def train_lire(
    model_key: str = "qwen",
    pairs_path: str = "data/train_lire_pairs.csv",
    stage1_dir: str = None,
    output_dir: str = None,
    lire_lambda: float = 1.0,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-5,
    max_length: int = 512,
):
    model_name = MODEL_LIST[model_key]
    if stage1_dir is None:
        stage1_dir = STAGE1_DIRS[model_key]
    if output_dir is None:
        output_dir = f"./trained_models/{model_key}_lire"

    print("=" * 70)
    print(f"LIRE Training — {model_key}")
    print(f"  base model : {model_name}")
    print(f"  stage1 dir : {stage1_dir}")
    print(f"  pairs      : {pairs_path}")
    print(f"  lambda     : {lire_lambda}")
    print(f"  epochs     : {epochs}")
    print(f"  output     : {output_dir}")
    print("=" * 70)

    # Tokenizer
    if os.path.exists(stage1_dir):
        tokenizer = AutoTokenizer.from_pretrained(stage1_dir)
        print(f"  Loaded tokenizer from stage1: {stage1_dir}")
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print(f"  Loaded tokenizer from base: {model_name}")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # Dataset
    print("\nBuilding LIRE pair dataset...")
    dataset = build_lire_dataset(pairs_path, tokenizer, max_length)

    # Model
    print("\nLoading model...")
    base_model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        torch_dtype=torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    if tokenizer.pad_token_id is not None:
        base_model.config.pad_token_id = tokenizer.pad_token_id

    # Only load stage1 LoRA if its task_type matches SEQ_CLS (avoids CAUSAL_LM conflict)
    _adapter_cfg = os.path.join(stage1_dir, "adapter_config.json")
    _stage1_task = None
    if os.path.exists(_adapter_cfg):
        import json as _json

        with open(_adapter_cfg) as _f:
            _stage1_task = _json.load(_f).get("task_type", "")
    if os.path.exists(stage1_dir) and _stage1_task == "SEQ_CLS":
        model = PeftModel.from_pretrained(base_model, stage1_dir, is_trainable=True)
        print(f"  Loaded stage1 PEFT adapter from {stage1_dir}")
    else:
        if _stage1_task and _stage1_task != "SEQ_CLS":
            print(f"  Stage1 task_type={_stage1_task} ≠ SEQ_CLS → applying fresh LoRA")
        lora_config = build_lora_config(model_name)
        model = get_peft_model(base_model, lora_config)
        print("  Applied fresh LoRA")

    if hasattr(model, "print_trainable_parameters"):
        model.print_trainable_parameters()

    # Training args
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        save_strategy="epoch",
        logging_steps=20,
        remove_unused_columns=False,
        report_to="none",
        fp16=False,
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        gradient_accumulation_steps=2,
    )

    trainer = LIRETrainer(
        lire_lambda=lire_lambda,
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=lire_collator,
        processing_class=tokenizer,
    )

    print("\nStarting LIRE training...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"\nLIRE model saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LIRE Training")
    parser.add_argument("--model", type=str, default="qwen", choices=["qwen", "qwen3", "llama", "bert"])
    parser.add_argument("--pairs", type=str, default="data/train_lire_pairs.csv")
    parser.add_argument("--stage1_dir", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--lire_lambda", type=float, default=1.0, help="Weight of invariance loss (default: 1.0)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=512)
    args = parser.parse_args()

    train_lire(
        model_key=args.model,
        pairs_path=args.pairs,
        stage1_dir=args.stage1_dir,
        output_dir=args.output_dir,
        lire_lambda=args.lire_lambda,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_length=args.max_length,
    )
