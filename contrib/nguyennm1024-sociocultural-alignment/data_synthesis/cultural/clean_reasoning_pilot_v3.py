"""Pilot v3: v2's simple prompt + Vietnam-specificity constraint + length nudge.

Adds two constraints to v2:
  1. Reasoning must reflect specifically present-day Vietnamese (SRV) culture
     and values — not generic Confucian/East-Asian/Asian framing, not Western
     individualist framing, not diaspora as the default.
  2. Length proportional to question type (short for simple questions, longer for scenarios).

Same sampling as v1/v2 (use the same --seed to land on the same 20 records and
compare directly). Writes to `_pilot_v3/cleaned.jsonl` + `_pilot_v3/report.md`.

Usage:
    python3 -m data_synthesis.cultural.clean_reasoning_pilot_v3 \
        [--n 20] [--min-chars 1000] [--max-chars 8000] [--seed 0]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import openai

from data_synthesis.core.client import make_deepseek_client


ROOT = Path(__file__).resolve().parent
RECORDS_PATH = Path("runs/cultural/records.jsonl")
OUT_DIR = ROOT / "_pilot_v3"
OUT_JSONL = OUT_DIR / "cleaned.jsonl"
OUT_REPORT = OUT_DIR / "report.md"

REWRITER_MODEL = "deepseek-v4-pro"


REWRITER_PROMPT = """Here is a question, the reasoning, and the answer. This (question, reasoning, answer) triple will be used to train another model.

The question and the answer will be preserved exactly as written. Your job is to rewrite ONLY the reasoning.

Rewrite the reasoning so that it is:

- Straightforward and clean.

- Free of any meta-prompt content from the teacher: no "as a Vietnamese person...", no "I need to / I should / let me draft / wait / check against constraints", no "the user is asking", no references to system prompts, personas, instructions, or being an AI.

- Specifically grounded in present-day Vietnamese (Socialist Republic of Vietnam) culture and values — the lived experience of the ~100M people living in Vietnam today. NOT generic Confucian / East Asian / Asian framing. NOT Western individualist framing. NOT overseas-Vietnamese / diaspora framing as the default (unless the question itself is about the diaspora). When a value or mechanism is named, anchor it in concrete Vietnamese reality: Vietnamese terms with brief gloss, Vietnamese institutions, Vietnamese economic and historical context (e.g., post-Đổi Mới, urban–rural divide, specific regions like Hà Nội / TP.HCM / Mekong Delta / Central Highlands), Vietnamese generational dynamics. If the original reasoning leans on abstract collectivist / Confucian language, replace it with the specific Vietnamese mechanism.

- Preserves every helpful fact, idiom, mechanism, or insight about Vietnam and Vietnamese culture that the original reasoning contained.

- Proportional in length to the question. Short factual or judgment questions: ~100–200 words. Open-ended explanation or scenario questions: up to ~300 words. Never pad by restating, summarizing, or repeating earlier points.

- Need to have clean signal of ending the reasoning so we can avoid student model reasoning infinite.

- The current reasoning are good at connecting question to the answer, you must take advantage from that instead of writing all from scratch. Make sure the data will be clean, connected in natural flow.

- Must end the reasoning with a clear signal that thinking is finished and the answer is about to follow. This signal must VARY across records — do NOT default to the same closing phrase every time. Examples of the kind of variety wanted (do not copy these verbatim; invent fresh phrasings):
    • "So the honest answer here is a 9."
    • "That settles it — the gesture is polite, not rude."
    • "On balance, the framing the answer should take is X."
    • "With that in mind, here's how the message should go."
    • "I'm confident in the answer now."
    • "Alright, time to put it into words."
  Each record's closing must be different in wording from the others. The pattern is: a settled commit OR a brief readiness-to-answer signal, but never the same phrase repeated across records.

Output ONLY the rewritten reasoning as plain text. No preamble, no headers, no JSON, no quotation marks around it.

QUESTION:
{question}

REASONING:
{reasoning}

ANSWER:
{answer}"""


def sample_records(path: Path, n: int, min_chars: int, max_chars: int, seed: int) -> list[dict]:
    by_topic: dict[str, list[dict]] = defaultdict(list)
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            reasoning = r.get("reasoning") or ""
            if not (min_chars <= len(reasoning) <= max_chars):
                continue
            by_topic[r.get("topic_id", "_unknown")].append(r)

    rng = random.Random(seed)
    topics = sorted(by_topic.keys())
    rng.shuffle(topics)

    out: list[dict] = []
    while len(out) < n and topics:
        for t in list(topics):
            bucket = by_topic[t]
            if not bucket:
                topics.remove(t)
                continue
            out.append(bucket.pop(rng.randrange(len(bucket))))
            if len(out) >= n:
                break
    return out


def call_rewriter(client: openai.Client, prompt: str, max_retries: int = 2) -> str | None:
    for attempt in range(max_retries + 1):
        try:
            r = client.chat.completions.create(
                model=REWRITER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            text = (r.choices[0].message.content or "").strip()
            return text or None
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            print(f"[warn] rewriter call failed: {e}", file=sys.stderr)
            return None
    return None


def write_report(rows: list[dict], path: Path) -> None:
    lines = ["# Cultural-reasoning rewriter pilot (v3 — Vietnam-specific + length-tuned)", ""]
    lines.append(f"Records: {len(rows)}  •  Model: `{REWRITER_MODEL}`")
    lines.append("")
    for i, row in enumerate(rows, 1):
        orig = row["original_reasoning"]
        clean = row.get("cleaned_reasoning") or "(rewriter failed)"
        lines.append(f"## {i}. `{row['topic_id']}` / `{row['scenario_id']}`")
        lines.append("")
        lines.append(f"**Question:** {row['question']}")
        lines.append("")
        lines.append(f"**Answer (unchanged, first 400 chars):** {row['answer'][:400]}…")
        lines.append("")
        lines.append(f"**Original reasoning** ({len(orig)} chars):")
        lines.append("")
        lines.append("> " + orig.replace("\n", "\n> "))
        lines.append("")
        lines.append(f"**Cleaned reasoning** ({len(clean)} chars):")
        lines.append("")
        lines.append("> " + clean.replace("\n", "\n> "))
        lines.append("")
        lines.append("---")
        lines.append("")
    path.write_text("\n".join(lines))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--min-chars", type=int, default=1000)
    p.add_argument("--max-chars", type=int, default=8000)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[pilot-v3] sampling {args.n} records (reasoning in [{args.min_chars}, {args.max_chars}] chars)", file=sys.stderr)
    samples = sample_records(RECORDS_PATH, args.n, args.min_chars, args.max_chars, args.seed)
    print(f"[pilot-v3] sampled {len(samples)} records across {len({s.get('topic_id') for s in samples})} topics", file=sys.stderr)

    client = make_deepseek_client()
    rows: list[dict] = []
    with OUT_JSONL.open("w") as fout:
        for i, rec in enumerate(samples, 1):
            question = rec["question"]
            reasoning = rec["reasoning"]
            answer = rec["answer"]
            prompt = REWRITER_PROMPT.format(question=question, reasoning=reasoning, answer=answer)

            t0 = time.time()
            cleaned = call_rewriter(client, prompt)
            elapsed = time.time() - t0
            ok = bool(cleaned)
            print(
                f"[{i:>2}/{len(samples)}] {rec.get('topic_id','?')[:30]:<30} "
                f"orig={len(reasoning):>5} → clean={len(cleaned) if cleaned else 0:>4}  "
                f"{elapsed:>5.1f}s  {'OK' if ok else 'FAIL'}",
                file=sys.stderr, flush=True,
            )

            row = {
                "topic_id": rec.get("topic_id"),
                "scenario_id": rec.get("scenario_id"),
                "question": question,
                "answer": answer,
                "original_reasoning": reasoning,
                "cleaned_reasoning": cleaned,
                "rewriter_model": REWRITER_MODEL,
                "elapsed_sec": round(elapsed, 2),
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            fout.flush()
            rows.append(row)

    write_report(rows, OUT_REPORT)
    n_ok = sum(1 for r in rows if r["cleaned_reasoning"])
    print(f"\n[pilot-v3] done: {n_ok}/{len(rows)} cleaned successfully", file=sys.stderr)
    print(f"[pilot-v3] jsonl:  {OUT_JSONL}", file=sys.stderr)
    print(f"[pilot-v3] report: {OUT_REPORT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
