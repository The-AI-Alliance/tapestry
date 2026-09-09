"""
Stage 4 Training: RLVF (Reinforcement Learning with Verifier Feedback)

Motivation:
  LIRE achieved near-perfect logical invariance (variant4: 0.741→0.999) but
  catastrophically hurt logical sensitivity (variant2/3: 1.0→0.47). This is
  because LIRE's invariance loss makes the model output the SAME answer for
  ANY rule change — including changes that SHOULD alter the answer (v2/v3).

Core insight:
  forward_chain() is an exact logical oracle. For each example:
    - variant4 (equivalent rules): forward_chain gives SAME GT → RL reward teaches INVARIANCE
    - variant2/3 (different logic): forward_chain gives DIFFERENT GT → RL reward teaches SENSITIVITY
  One reward signal naturally balances BOTH objectives.

Algorithm: REINFORCE for binary classifier
  π(a|x) = softmax(model(x))       # policy
  a_s ~ π(·|x)                     # sampled action (T or F)
  r = +1 if a_s == forward_chain(x, q), else -1
  L = -(r - b) * log π(a_s|x)     # policy gradient with baseline b

Training data (mixed):
  - train.csv   : base_positive + base_negative + variant2 + variant3 + hard_mixed
  - train_lire_pairs.csv : (base, variant4_equiv) pairs for invariance training

The REINFORCE loss naturally:
  - Encourages correct predictions (positive reward)
  - Discourages incorrect predictions (negative reward)
  - Focuses learning where the model is weakest (v4 demorgan, v4 double_neg)
"""

import argparse
import os
import sys
import random

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

# Add project root to path for forward_chain import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scripts.utils.forward_chain import forward_chain, check_answer

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


# ─────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────


def oracle_label(facts_str: str, rules_str: str, question: str) -> int:
    """Compute ground-truth label via forward_chain oracle."""
    try:
        closure = forward_chain(facts_str, rules_str)
        result = check_answer(question, closure)
        if result is True:
            return 1
        elif result is False:
            return 0
        # Fallback: parse from question keyword
        return -1
    except Exception:
        return -1


def build_mixed_dataset(
    train_csv: str,
    pairs_csv: str,
    tokenizer,
    max_length: int = 512,
    v4_ratio: float = 0.5,
    use_oracle: bool = True,
):
    """
    Build mixed training dataset with base/v2/v3 and variant4 pairs.

    v4_ratio: fraction of samples that come from variant4 equivalences.
    """
    # ── Load train.csv (base + v2 + v3 + hard_mixed) ────────────────────────
    df_train = pd.read_csv(train_csv)
    print(f"  train.csv: {len(df_train)} rows, types={df_train['type'].value_counts().to_dict()}")

    train_samples = []
    for _, row in df_train.iterrows():
        facts = str(row["facts"])
        rules = str(row["rules"])
        questions = str(row["questions"]).split(" | ")
        answers = str(row["answers"]).split(" | ")
        for q, a in zip(questions, answers):
            if use_oracle:
                lbl = oracle_label(facts, rules, q)
                if lbl == -1:
                    # Oracle couldn't verify; use CSV label as fallback
                    lbl = 1 if a.strip() == "T" else 0
            else:
                lbl = 1 if a.strip() == "T" else 0
            text = facts + " " + rules + " " + q
            enc = tokenizer(text, truncation=True, padding="max_length", max_length=max_length)
            train_samples.append(
                {
                    "input_ids": enc["input_ids"],
                    "attention_mask": enc["attention_mask"],
                    "labels": lbl,
                    "source": "train",
                }
            )

    print(f"  train samples: {len(train_samples)}")

    # ── Load variant4 pairs ──────────────────────────────────────────────────
    df_pairs = pd.read_csv(pairs_csv)
    print(f"  pairs.csv: {len(df_pairs)} rows")

    v4_samples = []
    for _, row in df_pairs.iterrows():
        questions = str(row["questions"]).split(" | ")
        answers = str(row["answers"]).split(" | ")
        base_facts = str(row["base_facts"])
        base_rules = str(row["base_rules"])
        equiv_facts = str(row["equiv_facts"])
        equiv_rules = str(row["equiv_rules"])
        for q, a in zip(questions, answers):
            lbl = 1 if a.strip() == "T" else 0
            # Add both base and equiv as separate samples (same label)
            for f, r in [(base_facts, base_rules), (equiv_facts, equiv_rules)]:
                text = f + " " + r + " " + q
                enc = tokenizer(text, truncation=True, padding="max_length", max_length=max_length)
                v4_samples.append(
                    {
                        "input_ids": enc["input_ids"],
                        "attention_mask": enc["attention_mask"],
                        "labels": lbl,
                        "source": "v4",
                    }
                )

    print(f"  variant4 samples: {len(v4_samples)}")

    # ── Balanced mix ────────────────────────────────────────────────────────
    # Subsample v4 to match desired ratio
    target_v4 = int(len(train_samples) * v4_ratio / (1 - v4_ratio))
    if len(v4_samples) > target_v4:
        v4_samples = random.sample(v4_samples, target_v4)

    all_samples = train_samples + v4_samples
    random.shuffle(all_samples)
    print(f"  Total mixed samples: {len(all_samples)}")
    return Dataset.from_list(all_samples)


# ─────────────────────────────────────────────────────────
# REINFORCE Trainer
# ─────────────────────────────────────────────────────────


class RLVFTrainer(Trainer):
    """
    REINFORCE trainer for binary classifier.

    Loss: L = -(r - b) * log π(a_s | x)

    Where:
      a_s   = action sampled from softmax(logits)
      r     = +1 if correct, -1 if wrong  (from forward_chain oracle GT)
      b     = running mean baseline to reduce variance
      π(a_s|x) = probability of sampled action under current policy
    """

    def __init__(self, baseline_momentum: float = 0.99, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseline_momentum = baseline_momentum
        self._baseline = 0.0  # running mean reward baseline
        self._step_count = 0

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs["labels"]  # (B,) — oracle GT: 0 or 1
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        # Forward pass
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits  # (B, 2)

        # Sample actions from current policy (stochastic exploration)
        with torch.no_grad():
            probs = F.softmax(logits.float(), dim=-1)  # (B, 2)
            # During training: stochastic sampling for exploration
            actions = torch.multinomial(probs, num_samples=1).squeeze(-1)  # (B,)

        # Compute rewards: +1 if correct, -1 if wrong
        correct = (actions == labels).float()  # (B,) — 1 if correct
        rewards = correct * 2 - 1  # +1 or -1

        # Update running baseline (exponential moving average)
        mean_r = rewards.mean().item()
        self._baseline = self.baseline_momentum * self._baseline + (1 - self.baseline_momentum) * mean_r
        baseline = torch.tensor(self._baseline, device=rewards.device)
        advantages = rewards - baseline  # (B,) — variance-reduced

        # Log probability of sampled action
        log_probs_all = F.log_softmax(logits.float(), dim=-1)  # (B, 2)
        log_probs = log_probs_all.gather(1, actions.unsqueeze(1)).squeeze(1)  # (B,)

        # REINFORCE loss: maximize E[r * log π(a|x)]
        loss = -(advantages.detach() * log_probs).mean()

        # Diagnostic logging
        self._step_count += 1
        if self._step_count % 20 == 0:
            acc = correct.mean().item()
            print(
                f"  step={self.state.global_step} "
                f"acc={acc:.3f} "
                f"mean_r={mean_r:.3f} "
                f"baseline={self._baseline:.3f} "
                f"loss={loss.item():.4f}",
                flush=True,
            )

        return (loss, outputs) if return_outputs else loss


# ─────────────────────────────────────────────────────────
# Custom collator
# ─────────────────────────────────────────────────────────


def rlvf_collator(batch):
    return {
        "input_ids": torch.tensor([x["input_ids"] for x in batch]),
        "attention_mask": torch.tensor([x["attention_mask"] for x in batch]),
        "labels": torch.tensor([x["labels"] for x in batch]),
    }


# ─────────────────────────────────────────────────────────
# Model loading helpers
# ─────────────────────────────────────────────────────────


def build_lora_config(model_name: str) -> LoraConfig:
    lower = model_name.lower()
    if "qwen3" in lower:
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


# ─────────────────────────────────────────────────────────
# Main training function
# ─────────────────────────────────────────────────────────


def train_rlvf(
    model_key: str = "qwen",
    train_csv: str = "data/train.csv",
    pairs_csv: str = "data/train_lire_pairs.csv",
    stage1_dir: str = None,
    output_dir: str = None,
    v4_ratio: float = 0.5,
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 1e-5,
    max_length: int = 512,
    baseline_momentum: float = 0.99,
):
    model_name = MODEL_LIST[model_key]
    if stage1_dir is None:
        stage1_dir = STAGE1_DIRS[model_key]
    if output_dir is None:
        output_dir = f"./trained_models/{model_key}_rlvf"

    print("=" * 70)
    print(f"RLVF Training — {model_key}")
    print(f"  base model   : {model_name}")
    print(f"  stage1 dir   : {stage1_dir}")
    print(f"  train data   : {train_csv}")
    print(f"  v4 pairs     : {pairs_csv}")
    print(f"  v4 ratio     : {v4_ratio:.0%}")
    print(f"  epochs       : {epochs}")
    print(f"  output       : {output_dir}")
    print("=" * 70)

    # Tokenizer
    tok_dir = stage1_dir if os.path.exists(stage1_dir) else model_name
    try:
        tokenizer = AutoTokenizer.from_pretrained(tok_dir, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    print(f"  Loaded tokenizer from: {tok_dir}")

    # Dataset
    print("\nBuilding mixed training dataset...")
    dataset = build_mixed_dataset(
        train_csv,
        pairs_csv,
        tokenizer,
        max_length=max_length,
        v4_ratio=v4_ratio,
    )

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
        print(f"  Loaded stage1 LoRA from: {stage1_dir}")
    else:
        if _stage1_task and _stage1_task != "SEQ_CLS":
            print(f"  Stage1 task_type={_stage1_task} ≠ SEQ_CLS → applying fresh LoRA")
        model = get_peft_model(base_model, build_lora_config(model_name))
        print("  Applied fresh LoRA")

    if hasattr(model, "print_trainable_parameters"):
        model.print_trainable_parameters()

    # Gradient checkpointing for large models (saves memory at cost of speed)
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    # Estimate total steps
    grad_acc = 8 if batch_size <= 2 else 4
    steps_per_epoch = len(dataset) // (batch_size * grad_acc)
    total_steps = steps_per_epoch * epochs
    print(f"\n  Dataset size    : {len(dataset)}")
    print(f"  Steps per epoch : {steps_per_epoch}")
    print(f"  Total steps     : {total_steps}")

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
        gradient_accumulation_steps=grad_acc,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
    )

    trainer = RLVFTrainer(
        baseline_momentum=baseline_momentum,
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=rlvf_collator,
        processing_class=tokenizer,
    )

    print("\nStarting RLVF training...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"\nRLVF model saved to: {output_dir}")


# ─────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RLVF Training")
    parser.add_argument("--model", type=str, default="qwen", choices=["qwen", "qwen3", "llama", "bert"])
    parser.add_argument("--train_csv", type=str, default="data/train.csv")
    parser.add_argument("--pairs_csv", type=str, default="data/train_lire_pairs.csv")
    parser.add_argument("--stage1_dir", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument(
        "--v4_ratio", type=float, default=0.5, help="Fraction of batch from variant4 equivalences (default: 0.5)"
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--baseline_momentum", type=float, default=0.99)
    args = parser.parse_args()

    train_rlvf(
        model_key=args.model,
        train_csv=args.train_csv,
        pairs_csv=args.pairs_csv,
        stage1_dir=args.stage1_dir,
        output_dir=args.output_dir,
        v4_ratio=args.v4_ratio,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_length=args.max_length,
        baseline_momentum=args.baseline_momentum,
    )
