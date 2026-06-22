#!/usr/bin/env python
"""Offline pack the prepared SFT data into FIXED-length 16k blocks.

Why: constant per-step memory. Every training block is exactly `block` tokens,
so GPU memory is identical on every step — the run cannot spike and crash.
Each block concatenates whole examples; `position_ids` reset at each example
boundary so FlashAttention treats them as separate sequences (no cross-example
attention). `labels` are -100 on prompt/pad tokens (response-only loss).

Tokenization is batched through apply_chat_template for speed. Inputs are the
already-windowed `prepared/*.jsonl` (so nothing exceeds the block).

Output: datasets saved with save_to_disk to prepared/packed/{train,val_*}.
"""
import argparse, json, os
from datasets import Dataset
from transformers import AutoTokenizer
from chat_template import CHAT_TEMPLATE


def load_jsonl(p):
    with open(p) as f:
        return [json.loads(l) for l in f]


def tokenize_all(tok, rows, chunk=1000):
    """Batched apply_chat_template -> (input_ids, assistant_mask) per row."""
    ids_all, mask_all = [], []
    convs = [r["messages"] for r in rows]
    for i in range(0, len(convs), chunk):
        enc = tok.apply_chat_template(
            convs[i:i + chunk], tokenize=True, return_assistant_tokens_mask=True,
            return_dict=True, add_generation_prompt=False)
        ids_all.extend(enc["input_ids"])
        mask_all.extend(enc["assistant_masks"])
    return ids_all, mask_all


def pack(ids_all, mask_all, block, pad_id):
    blocks_i, blocks_l, blocks_p = [], [], []
    ci, cl, cp = [], [], []

    def flush():
        nonlocal ci, cl, cp
        if not ci:
            return
        if len(ci) < block:
            padn = block - len(ci)
            ci += [pad_id] * padn
            cl += [-100] * padn
            cp += list(range(padn))          # pad tail = its own dummy sequence
        blocks_i.append(ci); blocks_l.append(cl); blocks_p.append(cp)
        ci, cl, cp = [], [], []

    for ids, mask in zip(ids_all, mask_all):
        if len(ids) > block:
            ids, mask = ids[:block], mask[:block]
        if len(ci) + len(ids) > block:
            flush()
        labels = [t if m else -100 for t, m in zip(ids, mask)]
        ci += ids; cl += labels; cp += list(range(len(ids)))
    flush()
    return {"input_ids": blocks_i, "labels": blocks_l, "position_ids": blocks_p}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/workspace/training_data/prepared")
    ap.add_argument("--out", default="/workspace/training_data/prepared/packed")
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--block", type=int, default=16384)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.chat_template = CHAT_TEMPLATE
    pad_id = tok.convert_tokens_to_ids("<|finetune_right_pad_id|>")
    if pad_id is None or pad_id < 0:
        pad_id = tok.eos_token_id

    os.makedirs(args.out, exist_ok=True)
    for name in ["train", "val_cultural", "val_rehearsal"]:
        path = os.path.join(args.data, f"{name}.jsonl")
        if not os.path.exists(path):
            print(f"[{name:14s}] (no file, skip)", flush=True); continue
        rows = load_jsonl(path)
        ids_all, mask_all = tokenize_all(tok, rows)
        cols = pack(ids_all, mask_all, args.block, pad_id)
        ds = Dataset.from_dict(cols)
        ds.save_to_disk(os.path.join(args.out, name))
        tok_total = sum(len(x) for x in ids_all)
        trained = sum(sum(1 for v in l if v != -100) for l in cols["labels"])
        print(f"[{name:14s}] rows={len(rows):6d} blocks={len(ds):5d} "
              f"tokens={tok_total/1e6:.1f}M trained_frac={trained/(len(ds)*args.block):.2f}",
              flush=True)


if __name__ == "__main__":
    main()
