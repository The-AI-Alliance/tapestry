"""Stage 2: resumable cultural answer synthesis.

Reads questions from the run directory's questions.jsonl, finds which
haven't been answered yet (by checking records.jsonl), and synthesizes
the rest. Each record is appended to disk as it completes — so a Ctrl-C
loses at most the in-flight calls.

Can run in parallel with stage 1: while questions.jsonl is being appended,
this stage picks up what's already there. Re-run after new questions land
to pick them up.

Usage (from data_synthesis/):
    python -m cultural.run_answers
    python -m cultural.run_answers --run-dir runs/cultural --concurrency 30
    python -m cultural.run_answers --no-gloss
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core import (
    DEFAULT_MODEL,
    append_records,
    make_client,
    read_records,
    synthesize_one,
)
from cultural.personas import get_persona


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUN_DIR = REPO_ROOT / "runs" / "cultural"


def _question_key(r: dict) -> tuple:
    """Stable key for matching questions to records across resume."""
    return (r["scenario_id"], r["batch_id"], r["gen_index"])


def _plan(
    run_dir: Path,
    worker_index: int = 0,
    num_workers: int = 1,
) -> tuple[list[dict], int, int]:
    """Compute pending questions. When `num_workers > 1`, partition the todo
    list by hash so multiple worker processes can run in parallel without
    duplicating work."""
    all_q = [r for r in read_records(run_dir / "questions.jsonl") if "question" in r]
    # Truthy check, not key-presence: a record with `answer=""` is a streaming
    # call that succeeded but yielded zero content (typically when a reasoning
    # model exhausts max_tokens before emitting any visible output). Treat it
    # as pending so the next run retries it.
    done_keys = {
        _question_key(r) for r in read_records(run_dir / "records.jsonl") if r.get("answer")
    }
    todo = [q for q in all_q if _question_key(q) not in done_keys]
    if num_workers > 1:
        import hashlib
        def deterministic_bucket(k: tuple) -> int:
            h = hashlib.md5(repr(k).encode()).digest()
            return int.from_bytes(h[:4], "big") % num_workers
        todo = [q for q in todo if deterministic_bucket(_question_key(q)) == worker_index]
    return todo, len(all_q), len(done_keys)


def run(
    run_dir: Path = DEFAULT_RUN_DIR,
    concurrency: int = 15,
    persona: str = "vietnamese",
    gloss_native_terms: bool = True,
    max_tokens: int = 16000,
    max_retries: int = 2,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    worker_index: int = 0,
    num_workers: int = 1,
) -> None:
    todo, total_q, total_done = _plan(run_dir, worker_index, num_workers)
    print(
        f"Questions on disk: {total_q}, already answered: {total_done}, "
        f"this worker ({worker_index+1}/{num_workers}) to do: {len(todo)}",
        file=sys.stderr,
    )
    print(f"Model: {model}  base_url: {base_url or '(default Moonshot)'}", file=sys.stderr)
    if not todo:
        return

    system_prompt = get_persona(persona, gloss_native_terms=gloss_native_terms)
    client = make_client(api_key=api_key, base_url=base_url)
    records_path = run_dir / "records.jsonl"
    t0 = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(
                synthesize_one,
                q["question"],
                system_prompt,
                client=client,
                model=model,
                max_tokens=max_tokens,
                max_retries=max_retries,
            ): q
            for q in todo
        }
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {
                    "question": q["question"],
                    "answer_model": model,
                    "error": "unknown",
                    "error_message": repr(e),
                }
            merged = {**q, **rec, "persona": persona}
            append_records(records_path, [merged])
            completed += 1
            print(
                f"  [{completed}/{len(todo)}] +1 ({time.time() - t0:.0f}s)",
                file=sys.stderr,
                flush=True,
            )

    print(
        f"\nDone. Wrote {completed} records to {records_path} in {time.time() - t0:.0f}s",
        file=sys.stderr,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Resumable cultural answer synthesis.")
    p.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    p.add_argument("--concurrency", type=int, default=15)
    p.add_argument("--persona", default="vietnamese")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument(
        "--no-gloss",
        dest="gloss_native_terms",
        action="store_false",
        help="Disable inline gloss of native-language terms on first use.",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="LLM API key. Defaults to KIMI_API_KEY env var. For OpenAI use $OPENAI_API_KEY.",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help="LLM base URL. Default Moonshot. For OpenAI use https://api.openai.com/v1.",
    )
    p.add_argument(
        "--worker-index", type=int, default=0,
        help="0-based worker index for parallel runs. Default 0.",
    )
    p.add_argument(
        "--num-workers", type=int, default=1,
        help="Total worker count for hash-partitioning pending questions across "
             "parallel processes. Default 1 (no partition).",
    )
    args = p.parse_args()

    run(
        run_dir=Path(args.run_dir),
        concurrency=args.concurrency,
        persona=args.persona,
        model=args.model,
        max_tokens=args.max_tokens,
        max_retries=args.max_retries,
        gloss_native_terms=args.gloss_native_terms,
        api_key=args.api_key,
        base_url=args.base_url,
        worker_index=args.worker_index,
        num_workers=args.num_workers,
    )


if __name__ == "__main__":
    main()
