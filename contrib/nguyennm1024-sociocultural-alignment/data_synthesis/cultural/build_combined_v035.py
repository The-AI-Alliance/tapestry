"""Assemble training_data/combined_v0.3.5/ from cultural_concise + rehearsal v0.3.5.

Layout (parallel to combined_v0.2):
  combined_v0.3.5/
    cultural.jsonl     # cultural_concise_train + cultural_concise_val,
                       #   merged and shuffled (seed=42)
    rehearsal.jsonl    # copy of training_data/v0.3.5/rehearsal_all.jsonl
    MANIFEST.md
    README.md
"""
from __future__ import annotations

import random
import shutil
import sys
from pathlib import Path

ROOT = Path("training_data")
SRC_CULTURAL_TRAIN = ROOT / "cultural_concise_train.jsonl"
SRC_CULTURAL_VAL = ROOT / "cultural_concise_val.jsonl"
SRC_REHEARSAL = ROOT / "v0.3.5" / "rehearsal_all.jsonl"

OUT_DIR = ROOT / "combined_v0.3.5"


def count_lines(p: Path) -> int:
    n = 0
    with p.open() as f:
        for _ in f:
            n += 1
    return n


def merge_and_shuffle(paths: list[Path], out: Path, seed: int = 42) -> int:
    lines: list[str] = []
    for p in paths:
        with p.open() as f:
            lines.extend(f.readlines())
    rng = random.Random(seed)
    rng.shuffle(lines)
    with out.open("w") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")
    return len(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[combine] source files:", file=sys.stderr)
    print(f"  cultural train: {SRC_CULTURAL_TRAIN}", file=sys.stderr)
    print(f"  cultural val:   {SRC_CULTURAL_VAL}", file=sys.stderr)
    print(f"  rehearsal:      {SRC_REHEARSAL}", file=sys.stderr)
    print(f"[combine] output dir: {OUT_DIR}", file=sys.stderr)

    # 1. cultural.jsonl = concise train + val, merged and shuffled
    out_cultural = OUT_DIR / "cultural.jsonl"
    n_cultural = merge_and_shuffle(
        [SRC_CULTURAL_TRAIN, SRC_CULTURAL_VAL], out_cultural, seed=42
    )
    print(f"[combine] cultural.jsonl:    {n_cultural:>6,} records (train+val, shuffled seed=42)", file=sys.stderr)

    # 2. rehearsal.jsonl = direct copy of v0.3.5 rehearsal_all
    out_reh = OUT_DIR / "rehearsal.jsonl"
    shutil.copy(SRC_REHEARSAL, out_reh)
    n_reh = count_lines(out_reh)
    print(f"[combine] rehearsal.jsonl:   {n_reh:>6,} records (copied from v0.3.5)", file=sys.stderr)

    total = n_cultural + n_reh
    print(f"[combine] TOTAL:             {total:>6,} records", file=sys.stderr)

    # 3. MANIFEST.md
    manifest = f"""# combined_v0.3.5 manifest

Date: 2026-06-11
State: rehearsal v0.3.5 + cultural (concise reasoning), KEPT SEPARATE, no val split

| File | Records | Notes |
|---|---:|---|
| `rehearsal.jsonl` | {n_reh:,} | Copy of `training_data/v0.3.5/rehearsal_all.jsonl`. Selected final rehearsal build (62.9% MMLU, −0.4 vs base). |
| `cultural.jsonl` | {n_cultural:,} | `cultural_concise_train.jsonl` ({count_lines(SRC_CULTURAL_TRAIN):,}) + `cultural_concise_val.jsonl` ({count_lines(SRC_CULTURAL_VAL):,}) merged, shuffled (seed=42). Reasoning cleaned via `deepseek-v4-pro` rewriter (v3 prompt). |
| **Total** | **{total:,}** | |

## Lineage

| Component | Source | When |
|---|---|---|
| Rehearsal v0.3.5 | `training_data/v0.3.5/rehearsal_all.jsonl` | 2026-06-10 (selected final) |
| Cultural (concise) | `data_synthesis/cultural/_out/cleaned_v3_all.jsonl` | 2026-06-11 (rewriter pass complete) |

## What changed from combined_v0.2

- Rehearsal upgraded: v0.2 (24,764) → v0.3.5 (52,568) — selected final build.
- Cultural: original verbose-reasoning corpus → **concise reasoning** (rewriter-cleaned).
  - Identical record set, identical questions, identical answers.
  - Only the `<THINK>...</THINK>` content changed: cleaned of teacher-side meta
    (persona restatement, "I should...", "Let me draft...", compliance audits)
    while preserving Vietnamese cultural mechanisms, idioms, and the connection
    from question to answer.
"""
    (OUT_DIR / "MANIFEST.md").write_text(manifest)

    # 4. README.md
    readme = f"""# combined_v0.3.5 — rehearsal v0.3.5 + concise cultural

Date: 2026-06-11

## Files

| File | Records |
|---|---:|
| `rehearsal.jsonl` | {n_reh:,} |
| `cultural.jsonl` | {n_cultural:,} |
| **Total** | **{total:,}** |

All files are full corpora with **no val split** (per combined_v0.2 convention).

## Contents

### `rehearsal.jsonl`

Identical to `training_data/v0.3.5/rehearsal_all.jsonl` — the selected final rehearsal build.
Eval: 62.9% MMLU (−0.4 vs base 63.2%); see `training_data/v0.3.5/SELECTED.md` for the
v0.3.5 vs v0.3.6 volume-dilution lesson.

### `cultural.jsonl`

Vietnamese cultural-alignment corpus with **cleaned reasoning traces**:
- train + val of `cultural_concise_{{train,val}}.jsonl`, shuffled (seed=42)
- Each `<THINK>...</THINK>` was rewritten by `deepseek-v4-pro` using the v3 prompt at
  `data_synthesis/cultural/clean_reasoning_pilot_v3.py`.
- The cleaning strips teacher-side meta ("I should...", persona restatement, drafting,
  compliance audits) while preserving Vietnamese cultural mechanisms, idioms, place
  references, and the natural connection from question to answer.
- Questions and answers are byte-for-byte identical to the original
  `cultural_{{train,val}}.jsonl` files.

## Schema

All files use the 3-turn `messages` SFT format (system/user/assistant). Per-record
metadata fields are preserved (`scenario_id`, `topic_id`, `item_type`,
`question_model`, `answer_model` for cultural; `id`, `category`, `source`,
`answer_key`, `provenance` for rehearsal).
"""
    (OUT_DIR / "README.md").write_text(readme)

    print(f"[combine] wrote MANIFEST.md and README.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
