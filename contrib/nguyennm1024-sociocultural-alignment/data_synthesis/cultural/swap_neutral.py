"""One-shot swap: replace ~10% most VN-explicit questions with culturally-neutral ones.

Motivation: the existing corpus is heavily VN-cued — 73% of questions mention
"Vietnamese" / "Tết" / "Hà Nội" / etc., and 54% contain Vietnamese diacritics.
A model trained on this risks learning "produce Vietnamese cultural framing
ONLY when the user mentions Vietnam." Replacing the strongest-cued ~10% with
universally-framed questions teaches the model that Vietnamese perspective is
the DEFAULT response, not a triggered behavior.

Pipeline:
  1. Score each existing question by VN-explicit signal density.
  2. Remove the top ~10% (default 2,200) from questions.jsonl.
  3. Also drop any matching answers from records.jsonl (orphan cleanup).
  4. Generate ~14 culturally-neutral questions per universal-friendly scenario
     using NEUTRAL_QUESTION_GEN_PROMPT.
  5. Append new questions to questions.jsonl.

Universal-friendly = scenario doesn't reference Vietnam-specific topics
(no T8 national-identity, no T11 diaspora, no VN-only cultural concepts).

Usage:
    python -m cultural.swap_neutral --dry-run
    python -m cultural.swap_neutral  # actually does the swap
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core import (
    append_records,
    iter_scenarios,
    load_spec,
    read_records,
)


def _rewrite_jsonl(path: Path, records: list[dict]) -> None:
    """Atomically replace a JSONL file (write to .tmp, rename). One-shot use
    for the destructive filter step in this swap — append-per-record helpers
    don't fit here."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)
from core.client import DEEPSEEK_MODEL, make_deepseek_client
from core.question_gen import generate_questions_for_scenario
from cultural.prompts import NEUTRAL_QUESTION_GEN_PROMPT


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SPEC_PATH = REPO_ROOT / "topics" / "cultural_data_coverage_v2.json"
DEFAULT_RUN_DIR = REPO_ROOT / "runs" / "cultural"

# Topics that are inherently Vietnam-locked. Neutral questions don't make sense
# for sovereignty/war/diaspora-by-definition/VN-bureaucracy scenarios.
VN_LOCKED_TOPICS = {
    "T8_national_identity_history_politics",
    "T11_diaspora_and_overseas_migration",
    "T12_civic_bureaucratic_legal_life",
}

# Substrings that mark an individual scenario (inside a non-locked topic) as
# still VN-specific — skip these for neutral gen.
VN_SPECIFIC_RE = re.compile(
    r"vietnam|việt|giỗ|tết|đạo mẫu|đạo mau|huế|saigon|mekong|"
    r"cao đài|hoà hảo|cao dai|đầy tháng|ở cữ|hộ khẩu|sổ đỏ|"
    r"hoàng sa|trường sa|bác hồ|nam bộ|bắc bộ|trung bộ|"
    r"hậu duệ|tày|thái|hmong|khmer|cham|"
    r"vietnamese|hcmc|hanoi|saigon",
    re.IGNORECASE,
)


VN_MARKER_RE = re.compile(
    r"\b(vietnam|vietnamese|việt|tết|giỗ|hoàng sa|trường sa|kháng chiến|bác hồ|đạo mẫu|"
    r"hà nội|hồ chí minh|saigon|sài gòn|đà nẵng|huế|tày|thái|hmong|khmer|cham|"
    r"việt kiều|hiếu|đồng bào|đạo hiếu|ngày giỗ|áo dài|đầy tháng|ở cữ|hộ khẩu|sổ đỏ|"
    r"phở|bánh|bún|chùa|đảng|cộng sản|cách mạng|nam bộ|bắc bộ|trung bộ)\b",
    re.IGNORECASE,
)
DIACRITIC_RE = re.compile(
    r"[àáâãèéêìíòóôõùúýăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹĐ]",
    re.IGNORECASE,
)


def _vn_score(text: str) -> int:
    """Higher = more VN-cued. 2 points per marker word, 1 per diacritic char."""
    return len(VN_MARKER_RE.findall(text)) * 2 + len(DIACRITIC_RE.findall(text))


def _is_universal(scenario: dict) -> bool:
    if scenario["topic_id"] in VN_LOCKED_TOPICS:
        return False
    blob = scenario["scenario_id"] + " " + scenario["scenario_description"]
    return not VN_SPECIFIC_RE.search(blob)


def _identify_removals(questions: list[dict], n_remove: int) -> set[tuple]:
    """Return the (scenario_id, batch_id, gen_index) keys of the highest-VN-score questions."""
    scored = [(r, _vn_score(r["question"])) for r in questions]
    scored.sort(key=lambda x: -x[1])
    top = scored[:n_remove]
    return {(r["scenario_id"], r["batch_id"], r["gen_index"]) for r, _ in top}


def _fill_scenario_neutral(
    scenario: dict,
    n_needed: int,
    questions_path: Path,
    client,
    disk_lock: threading.Lock,
    seed_questions: list[str],
    model: str,
    max_attempts: int = 5,
) -> dict:
    """Generate neutral questions for one universal scenario. Mirrors run_questions
    but uses NEUTRAL_QUESTION_GEN_PROMPT and a single batch (n_needed is small)."""
    accumulated = list(seed_questions)
    written = 0
    consecutive_failures = 0
    batches = 0
    while written < n_needed and consecutive_failures < max_attempts:
        chunk = n_needed - written
        records = generate_questions_for_scenario(
            scenario,
            NEUTRAL_QUESTION_GEN_PROMPT,
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


def _generate_neutral(
    todo: list[tuple[dict, int]],
    questions_path: Path,
    surviving_by_scn: dict[str, list[str]],
    model: str,
    api_key: str | None,
    concurrency: int,
) -> None:
    """Run the parallel generation loop. Each (scenario, n_needed) pair gets
    `_fill_scenario_neutral` on a worker thread."""
    client = make_deepseek_client(api_key=api_key) if model.startswith("deepseek") else None
    if client is None:
        raise RuntimeError(f"Unsupported model: {model}. Only deepseek-* supported here.")
    print(f"\nGenerating with {model} (concurrency={concurrency})...", file=sys.stderr)
    disk_lock = threading.Lock()
    t0 = time.time()
    completed = 0
    gave_up: list[str] = []
    total_written = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(
                _fill_scenario_neutral,
                s,
                d,
                questions_path,
                client,
                disk_lock,
                surviving_by_scn.get(s["scenario_id"], []),
                model,
            ): (s, d)
            for s, d in todo
        }
        for fut in as_completed(futures):
            s, d = futures[fut]
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
                f"  [{completed}/{len(todo)}] {s['scenario_id'][:35]:35s} "
                f"{result['written']}/{d} [{tag}] "
                f"({time.time() - t0:.0f}s)",
                file=sys.stderr, flush=True,
            )
            if result["gave_up"]:
                gave_up.append(s["scenario_id"])
    print(f"\nDone. Wrote {total_written} questions in {time.time() - t0:.0f}s", file=sys.stderr)
    if gave_up:
        print(f"  ! {len(gave_up)} scenarios gave up:", file=sys.stderr)
        for sid in gave_up:
            print(f"      {sid}", file=sys.stderr)


def run(
    run_dir: Path,
    spec_path: Path,
    n_remove: int,
    n_per_universal: int,
    concurrency: int,
    model: str,
    api_key: str | None,
    dry_run: bool,
    resume: bool = False,
) -> None:
    questions_path = run_dir / "questions.jsonl"
    records_path = run_dir / "records.jsonl"

    # 1. Read existing data
    all_q = list(read_records(questions_path))
    questions_only = [r for r in all_q if "question" in r]
    error_q = [r for r in all_q if "question" not in r]
    print(f"Existing questions: {len(questions_only)} (+ {len(error_q)} error records)", file=sys.stderr)

    if resume:
        # Skip removal/backup — those happened in the prior run. Only fill the
        # per-scenario deficit (where existing neutral-model count < target).
        spec = load_spec(spec_path)
        scenarios = list(iter_scenarios(spec))
        universal = [s for s in scenarios if _is_universal(s)]
        neutral_count: dict[str, int] = {}
        for r in questions_only:
            if r.get("question_model") == model:
                neutral_count[r["scenario_id"]] = neutral_count.get(r["scenario_id"], 0) + 1
        todo = [(s, n_per_universal - neutral_count.get(s["scenario_id"], 0)) for s in universal]
        todo = [(s, d) for s, d in todo if d > 0]
        print(f"\nResume mode: {len(todo)} scenarios still need neutral questions "
              f"(total deficit {sum(d for _, d in todo)})", file=sys.stderr)
        if not todo:
            print("Nothing to do.", file=sys.stderr)
            return
        if dry_run:
            for s, d in todo:
                print(f"  {s['scenario_id'][:40]:40s} need={d}", file=sys.stderr)
            return
        surviving_by_scn: dict[str, list[str]] = {}
        for r in questions_only:
            surviving_by_scn.setdefault(r["scenario_id"], []).append(r["question"])
        _generate_neutral(
            todo, questions_path, surviving_by_scn, model, api_key, concurrency
        )
        return

    # 2. Identify removals (the n_remove highest-VN-score questions)
    remove_keys = _identify_removals(questions_only, n_remove)
    print(f"Will remove top-{n_remove} most VN-explicit", file=sys.stderr)
    by_topic_removed = Counter(
        r["topic_id"] for r in questions_only
        if (r["scenario_id"], r["batch_id"], r["gen_index"]) in remove_keys
    )
    print("Removals by topic:", file=sys.stderr)
    for t, c in by_topic_removed.most_common():
        print(f"  {t[:42]:42s} {c}", file=sys.stderr)

    # 3. Load universal scenarios
    spec = load_spec(spec_path)
    scenarios = list(iter_scenarios(spec))
    universal = [s for s in scenarios if _is_universal(s)]
    print(f"\nUniversal scenarios: {len(universal)}", file=sys.stderr)
    print(f"Will generate {n_per_universal} neutral questions per universal scenario "
          f"= {n_per_universal * len(universal)} new questions", file=sys.stderr)

    if dry_run:
        print("\n--- DRY RUN: not modifying files ---", file=sys.stderr)
        return

    # 4. Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    q_backup = questions_path.with_suffix(f".jsonl.pre-swap-{ts}.bak")
    r_backup = records_path.with_suffix(f".jsonl.pre-swap-{ts}.bak")
    q_backup.write_bytes(questions_path.read_bytes())
    if records_path.exists():
        r_backup.write_bytes(records_path.read_bytes())
    print(f"\nBacked up to {q_backup.name} and {r_backup.name}", file=sys.stderr)

    # 5. Filter questions.jsonl: keep error records + non-removed real questions
    kept_q_records = error_q + [
        r for r in questions_only
        if (r["scenario_id"], r["batch_id"], r["gen_index"]) not in remove_keys
    ]
    _rewrite_jsonl(questions_path, kept_q_records)
    print(f"Wrote {len(kept_q_records)} records to {questions_path.name} "
          f"(removed {len(questions_only) - (len(kept_q_records) - len(error_q))})", file=sys.stderr)

    # 6. Filter records.jsonl: drop answers whose question was removed
    if records_path.exists():
        all_recs = list(read_records(records_path))
        kept_recs = [
            r for r in all_recs
            if (r.get("scenario_id"), r.get("batch_id"), r.get("gen_index")) not in remove_keys
        ]
        _rewrite_jsonl(records_path, kept_recs)
        n_orphans = len(all_recs) - len(kept_recs)
        print(f"Dropped {n_orphans} orphan answer records from {records_path.name}", file=sys.stderr)

    # 7. Generate neutral questions — fill each universal scenario to target,
    # accounting for already-generated neutral questions from prior runs.
    surviving_by_scn: dict[str, list[str]] = {}
    neutral_count: dict[str, int] = {}
    for r in kept_q_records:
        if "question" in r:
            surviving_by_scn.setdefault(r["scenario_id"], []).append(r["question"])
            if r.get("question_model") == model:
                neutral_count[r["scenario_id"]] = neutral_count.get(r["scenario_id"], 0) + 1
    todo = [(s, n_per_universal - neutral_count.get(s["scenario_id"], 0)) for s in universal]
    todo = [(s, d) for s, d in todo if d > 0]
    print(f"\nFilling {len(todo)} scenarios to target={n_per_universal} "
          f"(total deficit {sum(d for _, d in todo)})", file=sys.stderr)
    _generate_neutral(todo, questions_path, surviving_by_scn, model, api_key, concurrency)

    # 8. Final stats
    final_q = [r for r in read_records(questions_path) if "question" in r]
    final_vn_cued = sum(1 for r in final_q if _vn_score(r["question"]) > 0)
    print(f"\nFinal corpus: {len(final_q)} questions", file=sys.stderr)
    print(f"  VN-cued (score > 0): {final_vn_cued} ({100*final_vn_cued/len(final_q):.1f}%)", file=sys.stderr)
    print(f"  Truly neutral:       {len(final_q) - final_vn_cued} ({100*(len(final_q)-final_vn_cued)/len(final_q):.1f}%)", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Swap 10% most VN-explicit for neutral.")
    p.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    p.add_argument("--spec", default=str(DEFAULT_SPEC_PATH))
    p.add_argument("--n-remove", type=int, default=2200)
    p.add_argument("--n-per-universal", type=int, default=14,
                   help="Neutral questions per universal scenario (default 14, ~2,268 total)")
    p.add_argument("--concurrency", type=int, default=50)
    p.add_argument("--model", default=DEEPSEEK_MODEL)
    p.add_argument("--api-key", default=None)
    p.add_argument("--dry-run", action="store_true", help="Show counts only, don't modify files")
    p.add_argument("--resume", action="store_true",
                   help="Skip removal/backup; only generate the deficit for universal scenarios.")
    args = p.parse_args()

    run(
        run_dir=Path(args.run_dir),
        spec_path=Path(args.spec),
        n_remove=args.n_remove,
        n_per_universal=args.n_per_universal,
        concurrency=args.concurrency,
        model=args.model,
        api_key=args.api_key,
        dry_run=args.dry_run,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
