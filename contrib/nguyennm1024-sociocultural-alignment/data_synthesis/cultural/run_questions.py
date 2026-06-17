"""Stage 1: resumable cultural question generation.

For each scenario in the cultural spec, generate enough questions to reach
the target volume. Each scenario worker runs its own while loop, retrying
batches until target is hit or `max_attempts` consecutive empty/failed
calls. So a single `python -m cultural.run_questions ...` run will (in
the happy path) finish all scenarios without manual re-runs.

Resumable: re-running reads existing questions.jsonl and only fills the
deficit per scenario. Append-per-batch means Ctrl-C loses at most one
in-flight batch per worker.

Usage (from data_synthesis/):
    python -m cultural.run_questions
    python -m cultural.run_questions --run-dir runs/pilot --scenarios filial_piety_career_vs_family,hoang_sa_truong_sa --n 15
    python -m cultural.run_questions --use-spec-volumes --concurrency 30
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core import (
    DEFAULT_MODEL,
    append_records,
    iter_scenarios,
    load_spec,
    make_client,
    read_records,
)
from core.question_gen import generate_questions_for_scenario
from cultural.prompts import QUESTION_GEN_PROMPT


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SPEC_PATH = REPO_ROOT / "topics" / "cultural_data_coverage_v2.json"
DEFAULT_RUN_DIR = REPO_ROOT / "runs" / "cultural"
BATCH_SIZE = 20
DEFAULT_MAX_ATTEMPTS = 5


def _plan(
    spec_path: Path,
    run_dir: Path,
    scenario_filter: set[str] | None,
    n_per_scenario: int | None,
    use_spec_volumes: bool,
) -> tuple[list[tuple[dict, int, list[str]]], int, int]:
    """Return (work_units, total_have, total_target) where each work unit is
    (scenario, n_needed, existing_questions_for_scenario). The existing list
    seeds the avoid-list so resume runs don't generate duplicates of what's
    already on disk."""
    spec = load_spec(spec_path)
    scenarios = list(iter_scenarios(spec))
    if scenario_filter:
        scenarios = [s for s in scenarios if s["scenario_id"] in scenario_filter]

    by_scn: dict[str, list[str]] = {}
    for r in read_records(run_dir / "questions.jsonl"):
        if "question" in r:
            by_scn.setdefault(r["scenario_id"], []).append(r["question"])

    work: list[tuple[dict, int, list[str]]] = []
    total_have = 0
    total_target = 0
    for s in scenarios:
        target = s["volume"] if use_spec_volumes else (n_per_scenario or 15)
        existing = by_scn.get(s["scenario_id"], [])
        have = len(existing)
        total_have += min(have, target)
        total_target += target
        if have < target:
            work.append((s, target - have, existing))
    return work, total_have, total_target


def _fill_scenario(
    scenario: dict,
    n_needed: int,
    questions_path: Path,
    client,
    disk_lock: threading.Lock,
    seed_questions: list[str] | None = None,
    batch_size: int = BATCH_SIZE,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Keep calling the LLM until n_needed questions are produced for this
    scenario, or until `max_attempts` consecutive empty/failed calls.

    Each batch is appended to disk under disk_lock (crash-tolerant). Each
    successive batch in the loop includes the previously-generated questions
    (this run + `seed_questions` from disk) in the prompt to discourage
    cross-batch duplication.
    """
    accumulated: list[str] = list(seed_questions or [])
    written = 0
    consecutive_failures = 0
    batches = 0
    while written < n_needed and consecutive_failures < max_attempts:
        chunk = min(batch_size, n_needed - written)
        records = generate_questions_for_scenario(
            scenario,
            QUESTION_GEN_PROMPT,
            chunk,
            client,
            model=model,
            previous_questions=accumulated if accumulated else None,
        )
        with disk_lock:
            append_records(questions_path, records)
        batches += 1
        new_questions = [r["question"] for r in records if "question" in r]
        if new_questions:
            accumulated.extend(new_questions)
            written += len(new_questions)
            consecutive_failures = 0
        else:
            consecutive_failures += 1
    return {
        "scenario_id": scenario["scenario_id"],
        "written": written,
        "needed": n_needed,
        "batches": batches,
        "gave_up": consecutive_failures >= max_attempts,
    }


def run(
    spec_path: Path = DEFAULT_SPEC_PATH,
    run_dir: Path = DEFAULT_RUN_DIR,
    n_per_scenario: int | None = None,
    use_spec_volumes: bool = False,
    scenario_filter: set[str] | None = None,
    concurrency: int = 20,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
) -> None:
    work, total_have, total_target = _plan(
        spec_path, run_dir, scenario_filter, n_per_scenario, use_spec_volumes
    )
    print(
        f"On disk: {total_have} questions. Target: {total_target}. "
        f"Scenarios to fill: {len(work)} (deficit {sum(n for _, n, _ in work)}).",
        file=sys.stderr,
    )
    print(f"Model: {model}  base_url: {base_url or '(default Moonshot)'}", file=sys.stderr)
    if not work:
        return

    questions_path = run_dir / "questions.jsonl"
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    client = make_client(api_key=api_key, base_url=base_url)
    disk_lock = threading.Lock()
    t0 = time.time()
    completed = 0
    gave_up: list[str] = []
    total_written = 0

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(
                _fill_scenario,
                s,
                n_needed,
                questions_path,
                client,
                disk_lock,
                existing,
                BATCH_SIZE,
                max_attempts,
                model,
            ): (s, n_needed)
            for s, n_needed, existing in work
        }
        for fut in as_completed(futures):
            s, n_needed = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                print(f"  ! {s['scenario_id']}: {e!r}", file=sys.stderr)
                completed += 1
                continue
            total_written += result["written"]
            completed += 1
            tag = "GAVE UP" if result["gave_up"] else "ok"
            print(
                f"  [{completed}/{len(work)}] {s['scenario_id'][:35]:35s} "
                f"{result['written']}/{n_needed} in {result['batches']} batches [{tag}] "
                f"({time.time() - t0:.0f}s)",
                file=sys.stderr,
            )
            if result["gave_up"]:
                gave_up.append(s["scenario_id"])

    print(
        f"\nDone. Wrote {total_written} questions to {questions_path} in {time.time() - t0:.0f}s",
        file=sys.stderr,
    )
    if gave_up:
        print(
            f"  ! {len(gave_up)} scenarios gave up after {max_attempts} consecutive failures:",
            file=sys.stderr,
        )
        for sid in gave_up:
            print(f"      {sid}", file=sys.stderr)
        print(
            "  Re-run to retry, or investigate (content filter? bad prompt?).",
            file=sys.stderr,
        )


def main() -> None:
    p = argparse.ArgumentParser(description="Resumable cultural question generation.")
    p.add_argument("--spec", default=str(DEFAULT_SPEC_PATH))
    p.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    p.add_argument(
        "--scenarios",
        default=None,
        help="comma-separated scenario IDs (default: all in spec)",
    )
    p.add_argument(
        "--n",
        type=int,
        default=None,
        help="target questions per scenario (default 15; ignored if --use-spec-volumes)",
    )
    p.add_argument(
        "--use-spec-volumes",
        action="store_true",
        help="use scenario.volume from spec as the per-scenario target",
    )
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument(
        "--max-attempts",
        type=int,
        default=DEFAULT_MAX_ATTEMPTS,
        help=f"give up a scenario after this many consecutive empty/failed batches (default {DEFAULT_MAX_ATTEMPTS})",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="LLM API key. Defaults to KIMI_API_KEY env var. For OpenAI use $OPENAI_API_KEY.",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help="LLM base URL. Default Moonshot (https://api.moonshot.ai/v1). For OpenAI use https://api.openai.com/v1.",
    )
    p.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model id (default {DEFAULT_MODEL}). For OpenAI use e.g. gpt-4o-mini.",
    )
    args = p.parse_args()

    run(
        spec_path=Path(args.spec),
        run_dir=Path(args.run_dir),
        n_per_scenario=args.n,
        use_spec_volumes=args.use_spec_volumes,
        scenario_filter=set(args.scenarios.split(",")) if args.scenarios else None,
        concurrency=args.concurrency,
        max_attempts=args.max_attempts,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
    )


if __name__ == "__main__":
    main()
