"""End-to-end pipeline for cultural-alignment SFT data generation.

Three stages:
  1. Load cultural coverage spec from topics/cultural_data_coverage_v2.json.
  2. For each scenario, generate questions with the cultural prompt template.
  3. For each question, synthesize an answer with the Vietnamese persona.

Use as a library:
    from cultural.pipeline import run_for_scenarios
    records = run_for_scenarios(["scenario_id_1", "scenario_id_2"], n_per_scenario=15)

Or as a CLI:
    python -m cultural.pipeline pilot
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from core import generate_questions, get_scenario, load_spec, synthesize
from cultural.personas import get_persona
from cultural.prompts import QUESTION_GEN_PROMPT


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SPEC_PATH = REPO_ROOT / "topics" / "cultural_data_coverage_v2.json"

PILOT_SCENARIOS = [
    "filial_piety_career_vs_family",  # T1 — value-laden
    "hoang_sa_truong_sa",  # T8 — politically sensitive
]
PILOT_N_PER_SCENARIO = 15


def run_for_scenarios(
    scenario_ids: list[str],
    n_per_scenario: int = 15,
    spec_path: Path | str = DEFAULT_SPEC_PATH,
    gloss_native_terms: bool = True,
    synth_concurrency: int = 15,
) -> list[dict]:
    """Generate questions then synthesize answers for the given scenario_ids.

    Returns merged records (question record + synthesis record, with persona tag).
    """
    spec = load_spec(spec_path)
    scenarios = []
    for sid in scenario_ids:
        s = get_scenario(sid, spec)
        if s is None:
            print(f"  ! scenario not found: {sid}", file=sys.stderr)
            continue
        print(f"  loaded: {s['topic_id']} / {s['scenario_id']}", file=sys.stderr)
        scenarios.append(s)

    print(
        f"\nStage 2: generating ~{n_per_scenario} questions per scenario...",
        file=sys.stderr,
    )
    t0 = time.time()
    question_records = generate_questions(
        scenarios,
        QUESTION_GEN_PROMPT,
        n_per_scenario=n_per_scenario,
        concurrency=max(2, len(scenarios)),
    )
    for s in scenarios:
        scn_recs = [r for r in question_records if r["scenario_id"] == s["scenario_id"]]
        ok = [r for r in scn_recs if "question" in r]
        err = [r for r in scn_recs if "error" in r]
        print(
            f"  {s['scenario_id']}: {len(ok)} questions, {len(err)} errors",
            file=sys.stderr,
        )
    print(f"  stage 2 took {time.time() - t0:.1f}s\n", file=sys.stderr)

    questions_only = [r for r in question_records if "question" in r]
    print(
        f"Stage 3: synthesizing answers for {len(questions_only)} questions...",
        file=sys.stderr,
    )
    t0 = time.time()

    def progress(done: int, total: int) -> None:
        print(f"  [{done}/{total}] ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)

    system_prompt = get_persona("vietnamese", gloss_native_terms=gloss_native_terms)
    synth_records = synthesize(
        [r["question"] for r in questions_only],
        system_prompt=system_prompt,
        concurrency=synth_concurrency,
        on_progress=progress,
    )
    print(f"  stage 3 took {time.time() - t0:.1f}s", file=sys.stderr)

    merged: list[dict] = []
    for q_rec, s_rec in zip(questions_only, synth_records):
        merged.append({**q_rec, **s_rec, "persona": "vietnamese"})
    return merged


def run_pilot(out_dir: Path | None = None) -> Path:
    """Run the canonical 2-scenario pilot. Writes JSONL, returns its path."""
    out_dir = out_dir or Path(__file__).resolve().parent
    print(f"Pilot scenarios: {PILOT_SCENARIOS}\n", file=sys.stderr)
    records = run_for_scenarios(PILOT_SCENARIOS, n_per_scenario=PILOT_N_PER_SCENARIO)

    out_path = out_dir / "_pilot_records.jsonl"
    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  wrote {out_path}", file=sys.stderr)
    return out_path


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    if mode == "pilot":
        run_pilot()
    else:
        sys.exit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
