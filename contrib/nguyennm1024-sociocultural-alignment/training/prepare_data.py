#!/usr/bin/env python
"""Prepare the Vietnamese-culture + rehearsal SFT corpus.

Per row:
  * normalise: drop empty/whitespace system messages so both corpora share one
    chat shape (cultural ships system:"" , rehearsal ships none).
  * window: head+tail truncate the longest user message of any row that would
    exceed the cutoff, so the trailing "Question: ..." and the assistant answer
    survive (the NarrativeQA full-book rows are the target). Drop if still over.
  * emit messages-only rows.

Speed: all length measurement uses ONE batched, multithreaded tokenizer call
(the Rust fast tokenizer uses every core) instead of a per-row Python loop.
Oversized contents are char-pretrimmed before tokenizing so we never run a
1.7 MB book through the tokenizer in full.

Outputs (to --out):
  train.jsonl          cultural_train + rehearsal_train, shuffled
  val_cultural.jsonl   cultural_val
  val_rehearsal.jsonl  rehearsal_val
"""
import argparse, json, os, random
from transformers import AutoTokenizer

from chat_template import CHAT_TEMPLATE

# Per-message tokens the chat template adds beyond raw content
# (<|start_header_id|> role <|end_header_id|>\n\n ... <|eot_id|>), plus BOS.
# Deliberately a slight over-estimate so windowed rows comfortably fit.
PER_MSG_OVERHEAD = 8
ROW_OVERHEAD = 8


def load_jsonl(p):
    with open(p) as f:
        return [json.loads(l) for l in f]


def norm_messages(row):
    return [dict(m) for m in row["messages"]
            if not (m["role"] == "system" and not (m["content"] or "").strip())]


def char_pretrim(content, cutoff):
    """Cheap string slice so the tokenizer never sees a full book."""
    cap = cutoff * 4  # chars per side; >> a cutoff-token budget (~2.3 chars/tok)
    if len(content) > 2 * cap:
        return content[:cap] + "\n\n...[document truncated]...\n\n" + content[-cap:], True
    return content, False


def process(rows, tok, cutoff):
    rows = [norm_messages(r) for r in rows]
    # 1) char-pretrim oversized contents, remember which rows were touched
    pre_win = [False] * len(rows)
    for ri, msgs in enumerate(rows):
        for m in msgs:
            if m["role"] == "user" and len(m["content"]) > cutoff * 8:
                m["content"], did = char_pretrim(m["content"], cutoff)
                pre_win[ri] = pre_win[ri] or did

    # 2) ONE batched tokenization of every message content (multithreaded)
    flat, spans = [], []
    for msgs in rows:
        start = len(flat)
        flat.extend(m["content"] for m in msgs)
        spans.append((start, len(flat)))
    ids_list = tok(flat, add_special_tokens=False)["input_ids"]
    lens = [len(x) for x in ids_list]

    # 3) per-row length; token-window the longest user msg if still over cutoff
    out, n_win, n_drop = [], 0, 0
    for ri, msgs in enumerate(rows):
        s, e = spans[ri]
        row_ids = ids_list[s:e]
        row_lens = lens[s:e]
        total = sum(row_lens) + PER_MSG_OVERHEAD * len(msgs) + ROW_OVERHEAD
        windowed = pre_win[ri]
        if total > cutoff:
            uidx = [k for k, m in enumerate(msgs) if m["role"] == "user"]
            if not uidx:
                n_drop += 1
                continue
            k = max(uidx, key=lambda k: row_lens[k])
            budget = cutoff - (total - row_lens[k])
            marker = "\n\n...[document truncated to fit context]...\n\n"
            m_ids = tok(marker, add_special_tokens=False)["input_ids"]
            keep = budget - len(m_ids)
            if keep < 64:
                n_drop += 1
                continue
            head, tail = keep // 2, keep - keep // 2
            new_ids = row_ids[k][:head] + m_ids + row_ids[k][-tail:]
            msgs[k]["content"] = tok.decode(new_ids)
            windowed = True
        if windowed:
            n_win += 1
        out.append({"messages": msgs})
    return out, n_win, n_drop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="/workspace/training_data")
    ap.add_argument("--out", default="/workspace/training_data/prepared")
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--cutoff", type=int, default=16384)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rehearsal_only", action="store_true",
                    help="train on rehearsal_train only (ablation: no cultural data)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.chat_template = CHAT_TEMPLATE

    spec = {
        "train": (["rehearsal_train.jsonl"] if args.rehearsal_only
                  else ["cultural_train.jsonl", "rehearsal_train.jsonl"]),
        "val_rehearsal": ["rehearsal_val.jsonl"],
    }
    if not args.rehearsal_only:
        spec["val_cultural"] = ["cultural_val.jsonl"]
    for name, files in spec.items():
        rows = []
        for f in files:
            rows += load_jsonl(os.path.join(args.data_dir, f))
        out, n_win, n_drop = process(rows, tok, args.cutoff)
        if name == "train":
            random.Random(args.seed).shuffle(out)
        path = os.path.join(args.out, f"{name}.jsonl")
        with open(path, "w") as fh:
            for r in out:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[{name:14s}] in={len(rows):6d} kept={len(out):6d} "
              f"windowed={n_win:4d} dropped={n_drop:4d} -> {path}", flush=True)


if __name__ == "__main__":
    main()
