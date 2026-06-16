"""Production cultural-reasoning cleaner — runs v3's prompt across the full
records.jsonl in parallel with thread pool, resumable, with quota detection.

Source:
  runs/cultural/records.jsonl  (filter: non-empty `reasoning`)

Output (resumable JSONL):
  data_synthesis/cultural/_out/cleaned_v3_all.jsonl

Each output line preserves the original record's fields and adds:
  - cleaned_reasoning  (str)
  - rewriter_model     (str)
  - rewriter_status    ("ok" / "failed" / "quota_exhausted")
  - rewriter_elapsed   (float seconds)

Resume behavior: on restart, reads the output file, builds the set of
already-processed (batch_id, gen_index) keys, and skips them.

Usage:
    python3 -u -m data_synthesis.cultural.clean_reasoning_all \
        [--workers 10] [--limit N] [--out path] [--src path]
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import openai

from data_synthesis.core.client import make_deepseek_client
from data_synthesis.cultural.clean_reasoning_pilot_v3 import REWRITER_PROMPT


REWRITER_MODEL = "deepseek-v4-pro"

DEFAULT_SRC = Path("runs/cultural/records.jsonl")
DEFAULT_OUT = Path(__file__).resolve().parent / "_out" / "cleaned_v3_all.jsonl"

QUOTA_EXHAUSTED = threading.Event()
WRITE_LOCK = threading.Lock()
DONE_COUNT = 0
FAIL_COUNT = 0
COUNTER_LOCK = threading.Lock()


def record_key(rec: dict) -> str:
    """Stable identifier for dedup: (batch_id, gen_index)."""
    return f"{rec.get('batch_id', '_')}:{rec.get('gen_index', '_')}"


def load_done_keys(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    keys: set[str] = set()
    with out_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            # only treat as done if cleaning actually succeeded
            if r.get("rewriter_status") == "ok" and r.get("cleaned_reasoning"):
                keys.add(record_key(r))
    return keys


def iter_input(src: Path, done_keys: set[str]):
    """Yield records that have non-empty reasoning and aren't already done."""
    with src.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not rec.get("reasoning"):
                continue
            if record_key(rec) in done_keys:
                continue
            yield rec


def call_rewriter(
    client: openai.Client,
    prompt: str,
    max_retries: int = 2,
) -> tuple[str | None, str]:
    """Returns (cleaned_text, status). status in {"ok","quota_exhausted","failed"}."""
    if QUOTA_EXHAUSTED.is_set():
        return None, "quota_exhausted"
    for attempt in range(max_retries + 1):
        try:
            r = client.chat.completions.create(
                model=REWRITER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            text = (r.choices[0].message.content or "").strip()
            if text:
                return text, "ok"
            return None, "failed"
        except openai.APIStatusError as e:
            body = getattr(e, "body", None)
            msg = (str(body.get("message", "")).lower() if isinstance(body, dict) else "")
            err_type = body.get("type") if isinstance(body, dict) else ""
            if (err_type == "exceeded_current_quota_error"
                or "insufficient balance" in msg
                or "suspended" in msg
                or getattr(e, "status_code", None) == 402):
                QUOTA_EXHAUSTED.set()
                print(f"[clean-all] QUOTA EXHAUSTED — {body}", file=sys.stderr, flush=True)
                return None, "quota_exhausted"
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 30))
                continue
            return None, "failed"
        except Exception:
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 30))
                continue
            return None, "failed"
    return None, "failed"


def process_one(client: openai.Client, rec: dict, out_path: Path) -> dict | None:
    global DONE_COUNT, FAIL_COUNT
    if QUOTA_EXHAUSTED.is_set():
        return None

    prompt = REWRITER_PROMPT.format(
        question=rec.get("question", ""),
        reasoning=rec.get("reasoning", ""),
        answer=rec.get("answer", ""),
    )
    t0 = time.time()
    cleaned, status = call_rewriter(client, prompt)
    elapsed = time.time() - t0

    out = dict(rec)
    out["original_reasoning"] = rec.get("reasoning")
    out["cleaned_reasoning"] = cleaned
    out["rewriter_model"] = REWRITER_MODEL
    out["rewriter_status"] = status
    out["rewriter_elapsed"] = round(elapsed, 2)
    # drop redundant raw reasoning field to keep file smaller
    out.pop("reasoning", None)

    with WRITE_LOCK:
        with out_path.open("a") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    with COUNTER_LOCK:
        if status == "ok":
            DONE_COUNT += 1
        else:
            FAIL_COUNT += 1
        n_done = DONE_COUNT
        n_fail = FAIL_COUNT
        n_total = n_done + n_fail

    if n_total % 25 == 0 or status != "ok":
        print(
            f"[{n_total:>5}] {rec.get('topic_id','?')[:28]:<28} "
            f"clean={len(cleaned) if cleaned else 0:>4}  "
            f"{elapsed:>5.1f}s  {status}  (ok={n_done}, fail={n_fail})",
            file=sys.stderr, flush=True,
        )
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=10, help="concurrent worker threads")
    p.add_argument("--limit", type=int, default=None, help="cap records (for smoke-test)")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC, help="input records.jsonl")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output jsonl")
    args = p.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[clean-all] src:     {args.src}", file=sys.stderr)
    print(f"[clean-all] out:     {args.out}", file=sys.stderr)
    print(f"[clean-all] workers: {args.workers}", file=sys.stderr)

    done_keys = load_done_keys(args.out)
    print(f"[clean-all] resume: {len(done_keys)} records already done", file=sys.stderr)

    # Materialize the work queue so we know totals; for 26k records this is fine.
    pending = list(iter_input(args.src, done_keys))
    if args.limit is not None:
        pending = pending[: args.limit]
    n_pending = len(pending)
    print(f"[clean-all] pending: {n_pending} records to process", file=sys.stderr)
    if n_pending == 0:
        print("[clean-all] nothing to do", file=sys.stderr)
        return 0

    client = make_deepseek_client()

    t_start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(process_one, client, rec, args.out) for rec in pending]
        try:
            for fut in as_completed(futures):
                fut.result()
                if QUOTA_EXHAUSTED.is_set():
                    print("[clean-all] quota exhausted — cancelling remaining work", file=sys.stderr)
                    for f in futures:
                        f.cancel()
                    break
        except KeyboardInterrupt:
            print("[clean-all] interrupted — cancelling pending work", file=sys.stderr)
            for f in futures:
                f.cancel()

    elapsed = time.time() - t_start
    print(
        f"\n[clean-all] done: ok={DONE_COUNT} fail={FAIL_COUNT} "
        f"in {elapsed/60:.1f} min  ({elapsed/max(DONE_COUNT,1):.1f}s/record effective)",
        file=sys.stderr,
    )
    return 0 if FAIL_COUNT == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
