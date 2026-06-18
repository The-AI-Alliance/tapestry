#!/usr/bin/env python
"""ABLATION: fine-tune a FRESH LoRA from base on REHEARSAL DATA ONLY (no cultural).
Tests whether the rehearsal corpus alone preserves benchmarks, or whether it ALSO
teaches the verbose/format problems we found endemic to it. Same generative benchmark
eval as the epoch-2 run, so the trajectory is directly comparable to base (70/75/80/80).
"""
import argparse, os, sys
import torch
from datasets import load_from_disk, load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments, TrainerCallback)
from peft import LoraConfig, get_peft_model
sys.path.insert(0, "/workspace/train"); sys.path.insert(0, "/workspace/eval")
from chat_template import CHAT_TEMPLATE
ANSWER_OPEN, ANSWER_CLOSE = "<ANSWER>", "</ANSWER>"


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--data", default="/workspace/training_data/prepared_rehearsal/packed")
    ap.add_argument("--out", default="/workspace/train/runs/rehearsal_only")
    ap.add_argument("--bs", type=int, default=1)
    ap.add_argument("--ga", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--rank", type=int, default=64)
    ap.add_argument("--alpha", type=int, default=128)
    ap.add_argument("--gpu_mem_frac", type=float, default=0.6)
    ap.add_argument("--save_steps", type=int, default=25)
    ap.add_argument("--save_total_limit", type=int, default=20)
    ap.add_argument("--geneval_steps", type=int, default=50)
    ap.add_argument("--geneval_n", type=int, default=20)
    ap.add_argument("--resume", action="store_true", help="resume from latest checkpoint in --out")
    ap.add_argument("--no_grad_ckpt", action="store_true", help="disable gradient checkpointing (faster, more memory)")
    return ap.parse_args()


def collate(batch):
    return {
        "input_ids": torch.tensor([b["input_ids"] for b in batch], dtype=torch.long),
        "labels": torch.tensor([b["labels"] for b in batch], dtype=torch.long),
        "position_ids": torch.tensor([b["position_ids"] for b in batch], dtype=torch.long),
    }


def build_eval_items(n):
    from tasks import ft_messages, subsample
    items = []
    for task in ["gsm8k", "mmlu", "hellaswag_chat", "arc_challenge"]:
        try:
            d = load_dataset("meta-llama/Llama-3.2-3B-Instruct-evals",
                             name=f"Llama-3.2-3B-Instruct-evals__{task}__details", split="latest")
            for i in subsample(d, n, 123):       # SAME 80-item validation set
                r = d[i]; fp = r["input_final_prompts"]; fp = fp[0] if isinstance(fp, list) else fp
                items.append((task, ft_messages(fp), r["input_correct_responses"]))
        except Exception as e:
            print(f"[geneval] could not build {task}: {e}", flush=True)
    print(f"[geneval] eval-monitor set: {len(items)} items", flush=True)
    return items


class GenEval(TrainerCallback):
    def __init__(self, tok, items, every): self.tok, self.items, self.every = tok, items, every
    def on_step_end(self, args, state, control, model=None, **kw):
        if self.every <= 0 or state.global_step % self.every != 0: return
        try: self._run(model, state.global_step)
        except Exception as e: print(f"[geneval] step {state.global_step} SKIPPED ({type(e).__name__}: {e})", flush=True)
    @torch.no_grad()
    def _run(self, model, step):
        from collections import defaultdict
        from tasks import TASKS
        was_train = model.training; uc = model.config.use_cache; was_ckpt = getattr(model, "is_gradient_checkpointing", False)
        model.eval(); model.config.use_cache = True
        try: model.gradient_checkpointing_disable()
        except Exception: pass
        pad_side = self.tok.padding_side; self.tok.padding_side = "left"
        if self.tok.pad_token is None: self.tok.pad_token = self.tok.eos_token
        cor, tot = defaultdict(int), defaultdict(int); by = defaultdict(list)
        for t, m, g in self.items: by[t].append((m, g))
        for task, rows in by.items():
            for k in range(0, len(rows), 8):
                chunk = rows[k:k+8]
                prompts = [self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True) for m, _ in chunk]
                enc = self.tok(prompts, return_tensors="pt", padding=True, truncation=True, max_length=2560).to(model.device)
                out = model.generate(**enc, max_new_tokens=768, do_sample=False, pad_token_id=self.tok.eos_token_id)
                for j, (_, g) in enumerate(chunk):
                    txt = self.tok.decode(out[j][enc["input_ids"].shape[1]:], skip_special_tokens=True)
                    ans = txt.split(ANSWER_OPEN)[-1].split(ANSWER_CLOSE)[0] if ANSWER_OPEN in txt else txt
                    try: good, _ = TASKS[task]["score"](ans, g)
                    except Exception: good = False
                    cor[task] += bool(good); tot[task] += 1
        msg = "  ".join(f"{t}={cor[t]}/{tot[t]}={cor[t]/max(1,tot[t])*100:.0f}%" for t in sorted(tot))
        print(f"[GENEVAL] step {step}:  {msg}", flush=True)
        self.tok.padding_side = pad_side; model.config.use_cache = uc
        if was_ckpt:
            try: model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            except Exception: pass
        if was_train: model.train()


def main():
    a = parse()
    if a.gpu_mem_frac < 1.0:
        torch.cuda.set_per_process_memory_fraction(a.gpu_mem_frac, 0)
    tok = AutoTokenizer.from_pretrained(a.model); tok.chat_template = CHAT_TEMPLATE
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="flash_attention_2")
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(
        r=a.rank, lora_alpha=a.alpha, lora_dropout=0.05, target_modules="all-linear",
        use_rslora=True, bias="none", task_type="CAUSAL_LM"))
    model.enable_input_require_grads()
    print("[combined-full] FRESH LoRA from base: cultural + rehearsal; val=cultural_val (loss) + MMLU (geneval)", flush=True)

    train_ds = load_from_disk(os.path.join(a.data, "train"))
    val_ds = load_from_disk(os.path.join(a.data, "val_cultural"))
    args = TrainingArguments(
        output_dir=a.out, per_device_train_batch_size=a.bs, gradient_accumulation_steps=a.ga,
        learning_rate=a.lr, lr_scheduler_type="cosine", warmup_ratio=0.03, num_train_epochs=a.epochs,
        bf16=True, gradient_checkpointing=(not a.no_grad_ckpt),
        gradient_checkpointing_kwargs=(None if a.no_grad_ckpt else {"use_reentrant": False}),
        optim="adamw_torch_fused", logging_steps=5, save_steps=a.save_steps,
        save_total_limit=a.save_total_limit, eval_strategy="steps", eval_steps=a.geneval_steps,
        per_device_eval_batch_size=1, report_to="none",
        dataloader_num_workers=2, dataloader_pin_memory=True, seed=1234)  # fresh seed

    items = build_eval_items(a.geneval_n)
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds, data_collator=collate,
                      callbacks=[GenEval(tok, items, a.geneval_steps)] if items else [])
    import glob as _glob
    ckpt = bool(a.resume and _glob.glob(os.path.join(a.out, "checkpoint-*")))
    if items and not ckpt:
        try: GenEval(tok, items, 1)._run(model, 0)   # step-0 baseline = fresh-LoRA-untrained ~= base
        except Exception as e: print(f"[geneval] baseline skipped: {e}", flush=True)
    trainer.train(resume_from_checkpoint=ckpt if ckpt else None)
    trainer.save_model(os.path.join(a.out, "final")); tok.save_pretrained(os.path.join(a.out, "final"))
    print("COMBINED_FULL_DONE ->", os.path.join(a.out, "final"), flush=True)


if __name__ == "__main__":
    main()
