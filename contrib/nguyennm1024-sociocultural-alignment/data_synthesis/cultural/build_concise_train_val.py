"""Build training_data/cultural_concise_{train,val}.jsonl from the cleaned
reasoning corpus, preserving the existing cultural_{train,val}.jsonl split
so eval is directly comparable.

Input:
  data_synthesis/cultural/_out/cleaned_v3_all.jsonl   (26,740 records, cleaned)
  training_data/cultural_train.jsonl                  (existing split for matching)
  training_data/cultural_val.jsonl

Output:
  training_data/cultural_concise_train.jsonl
  training_data/cultural_concise_val.jsonl

Matching key: question text (unique per record). For each cleaned record:
  - look up the question in existing train/val to determine split + item_type
  - emit a record in the same packaged schema as cultural_{train,val}.jsonl,
    but with `<THINK>{cleaned_reasoning}</THINK>\n{answer}` as the assistant
    content (vs the original verbose reasoning)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


CLEAN = Path("data_synthesis/cultural/_out/cleaned_v3_all.jsonl")
EXISTING_TRAIN = Path("training_data/cultural_train.jsonl")
EXISTING_VAL = Path("training_data/cultural_val.jsonl")
OUT_TRAIN = Path("training_data/cultural_concise_train.jsonl")
OUT_VAL = Path("training_data/cultural_concise_val.jsonl")


def load_existing_index(path: Path, split: str) -> dict[str, dict]:
    """Map question -> {split, item_type, scenario_id, topic_id, question_model, answer_model}."""
    out: dict[str, dict] = {}
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            msgs = r["messages"]
            # user message is the question
            q = next(m["content"] for m in msgs if m["role"] == "user")
            out[q] = {
                "split": split,
                "scenario_id": r.get("scenario_id"),
                "topic_id": r.get("topic_id"),
                "item_type": r.get("item_type"),
                "question_model": r.get("question_model"),
                "answer_model": r.get("answer_model"),
            }
    return out


def build_packaged(rec: dict, meta: dict) -> dict:
    """Pack a cleaned record into the SFT messages schema."""
    cleaned = rec["cleaned_reasoning"]
    answer = rec["answer"]
    assistant = f"<THINK>{cleaned}</THINK>\n{answer}"
    return {
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": rec["question"]},
            {"role": "assistant", "content": assistant},
        ],
        "scenario_id": meta.get("scenario_id") or rec.get("scenario_id"),
        "topic_id": meta.get("topic_id") or rec.get("topic_id"),
        "item_type": meta.get("item_type"),
        "question_model": meta.get("question_model") or rec.get("question_model"),
        "answer_model": meta.get("answer_model") or rec.get("answer_model"),
    }


def main() -> int:
    print(f"[concise] loading existing split index from", file=sys.stderr)
    print(f"  {EXISTING_TRAIN}", file=sys.stderr)
    print(f"  {EXISTING_VAL}", file=sys.stderr)
    idx = load_existing_index(EXISTING_TRAIN, "train")
    idx.update(load_existing_index(EXISTING_VAL, "val"))
    print(f"[concise] indexed {len(idx):,} questions from existing split", file=sys.stderr)

    print(f"[concise] reading cleaned corpus from {CLEAN}", file=sys.stderr)
    n_train = n_val = n_unmatched = 0
    with CLEAN.open() as fin, OUT_TRAIN.open("w") as ftrain, OUT_VAL.open("w") as fval:
        for line in fin:
            rec = json.loads(line)
            if not rec.get("cleaned_reasoning"):
                continue  # safety
            q = rec["question"]
            meta = idx.get(q)
            if meta is None:
                n_unmatched += 1
                continue
            packaged = build_packaged(rec, meta)
            line_out = json.dumps(packaged, ensure_ascii=False) + "\n"
            if meta["split"] == "train":
                ftrain.write(line_out)
                n_train += 1
            else:
                fval.write(line_out)
                n_val += 1

    print(f"\n[concise] done:", file=sys.stderr)
    print(f"  train:     {n_train:>6,}  →  {OUT_TRAIN}", file=sys.stderr)
    print(f"  val:       {n_val:>6,}  →  {OUT_VAL}", file=sys.stderr)
    print(f"  unmatched: {n_unmatched:>6,}  (cleaned records whose question wasn't in either split)", file=sys.stderr)
    return 0 if n_unmatched == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
