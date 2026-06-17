"""Retry pass over `_out/cleaned_v3_all.jsonl` — re-runs the rewriter only on
records whose `rewriter_status` is not "ok", and loops passes until either
everything succeeds or `--max-passes` is hit.

Algorithm per pass:
  1. Read the JSONL into a dict keyed by (batch_id, gen_index). If a key has
     multiple lines (an earlier failure + a later retry), keep the latest.
  2. Pull records whose status != "ok". If empty → done.
  3. Re-run the rewriter (v3 prompt) on those records, multi-threaded.
  4. Update the dict with the new results.
  5. Atomically rewrite the file with all current records.
  6. Repeat until clean or max-passes.

DO NOT run this concurrently with `clean_reasoning_all.py` on the same output
file — the rewrite step would clobber in-flight writes from the main run.
Wait for the main pass to finish first.

Usage:
    python3 -u -m data_synthesis.cultural.clean_reasoning_retry \
        [--workers 10] [--max-passes 5] [--out path]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import openai

from data_synthesis.core.client import make_deepseek_client
from data_synthesis.cultural.clean_reasoning_pilot_v3 import REWRITER_PROMPT


REWRITER_MODEL = "deepseek-v4-pro"

DEFAULT_PATH = Path(__file__).resolve().parent / "_out" / "cleaned_v3_all.jsonl"

QUOTA_EXHAUSTED = threading.Event()
DICT_LOCK = threading.Lock()


def record_key(rec: dict) -> str:
    return f"{rec.get('batch_id', '_')}:{rec.get('gen_index', '_')}"


def load_dedup(path: Path) -> dict[str, dict]:
    """Read all lines; keep the latest occurrence per (batch_id, gen_index)."""
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    with path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[record_key(r)] = r
    return out


def atomic_write(path: Path, records_by_key: dict[str, dict]) -> None:
    """Rewrite the file atomically: temp file, then rename."""
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.stem + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w") as f:
            for rec in records_by_key.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def call_rewriter(client: openai.Client, prompt: str, max_retries: int = 4) -> tuple[str | None, str]:
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
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 30))
                continue
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
                print(f"[retry] QUOTA EXHAUSTED — {body}", file=sys.stderr, flush=True)
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


def retry_one(client: openai.Client, rec: dict, records_by_key: dict[str, dict]) -> tuple[str, str]:
    key = record_key(rec)
    if QUOTA_EXHAUSTED.is_set():
        return key, "quota_exhausted"

    prompt = REWRITER_PROMPT.format(
        question=rec.get("question", ""),
        reasoning=rec.get("original_reasoning") or rec.get("reasoning", ""),
        answer=rec.get("answer", ""),
    )
    t0 = time.time()
    cleaned, status = call_rewriter(client, prompt)
    elapsed = time.time() - t0

    new_rec = dict(rec)
    new_rec["cleaned_reasoning"] = cleaned
    new_rec["rewriter_model"] = REWRITER_MODEL
    new_rec["rewriter_status"] = status
    new_rec["rewriter_elapsed"] = round(elapsed, 2)
    # ensure original_reasoning is preserved (if older format had `reasoning`)
    if "original_reasoning" not in new_rec and "reasoning" in new_rec:
        new_rec["original_reasoning"] = new_rec.pop("reasoning")

    with DICT_LOCK:
        records_by_key[key] = new_rec
    return key, status


def run_pass(client: openai.Client, records_by_key: dict[str, dict], workers: int) -> tuple[int, int]:
    """One retry pass over all not-ok records. Returns (n_recovered, n_still_failed)."""
    failed = [r for r in records_by_key.values() if r.get("rewriter_status") != "ok"]
    if not failed:
        return 0, 0

    print(f"[retry] pass: {len(failed)} records to retry with {workers} workers", file=sys.stderr)
    recovered = 0
    still_failed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(retry_one, client, r, records_by_key) for r in failed]
        for i, fut in enumerate(as_completed(futures), 1):
            _key, status = fut.result()
            if status == "ok":
                recovered += 1
            else:
                still_failed += 1
            if i % 20 == 0 or i == len(failed):
                print(
                    f"[retry]   progress {i:>4}/{len(failed)}  "
                    f"recovered={recovered}  still_failed={still_failed}",
                    file=sys.stderr, flush=True,
                )
            if QUOTA_EXHAUSTED.is_set():
                for f in futures:
                    f.cancel()
                break
    return recovered, still_failed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--max-passes", type=int, default=5, help="cap number of retry passes")
    p.add_argument("--pause-between-passes", type=float, default=30.0,
                   help="seconds to wait between passes (lets API recover)")
    p.add_argument("--out", type=Path, default=DEFAULT_PATH, help="JSONL file to retry in place")
    args = p.parse_args()

    if not args.out.exists():
        print(f"[retry] no file at {args.out}", file=sys.stderr)
        return 1

    records_by_key = load_dedup(args.out)
    n_total = len(records_by_key)
    n_failed_initial = sum(1 for r in records_by_key.values() if r.get("rewriter_status") != "ok")
    print(f"[retry] file:   {args.out}", file=sys.stderr)
    print(f"[retry] total:  {n_total:,} unique records", file=sys.stderr)
    print(f"[retry] failed: {n_failed_initial} → will retry up to {args.max_passes} passes", file=sys.stderr)

    if n_failed_initial == 0:
        print("[retry] nothing to do — all records already ok", file=sys.stderr)
        return 0

    client = make_deepseek_client()

    for pass_no in range(1, args.max_passes + 1):
        print(f"\n[retry] === PASS {pass_no}/{args.max_passes} ===", file=sys.stderr)
        recovered, still_failed = run_pass(client, records_by_key, args.workers)
        atomic_write(args.out, records_by_key)
        print(
            f"[retry] pass {pass_no} complete: recovered={recovered}  still_failed={still_failed}  "
            f"(file rewritten with {len(records_by_key):,} records)",
            file=sys.stderr,
        )
        if QUOTA_EXHAUSTED.is_set():
            print("[retry] quota exhausted — stopping", file=sys.stderr)
            break
        if still_failed == 0:
            print("[retry] all records ok — done", file=sys.stderr)
            break
        if pass_no < args.max_passes:
            print(f"[retry] pausing {args.pause_between_passes:.0f}s before next pass", file=sys.stderr)
            time.sleep(args.pause_between_passes)

    final_failed = sum(1 for r in records_by_key.values() if r.get("rewriter_status") != "ok")
    print(
        f"\n[retry] done. final state: {n_total - final_failed:,} ok, {final_failed} still failing"
        f" (out of {n_failed_initial} initial failures)",
        file=sys.stderr,
    )
    return 0 if final_failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
