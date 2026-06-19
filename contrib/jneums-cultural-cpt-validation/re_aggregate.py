#!/usr/bin/env python3
"""Re-aggregate a multi-seed go/no-go from persisted per-seed checkpoints.

``run_stats.py`` writes each seed's raw result to ``<out>/seeds/seed_<s>.json`` as
it finishes. If aggregation crashes or the box dies before the final write, the
training is NOT lost — point this at the seeds/ dir to rebuild ``result.json`` on
CPU, with no model and no GPU:

    python re_aggregate.py --seeds-dir runs/egypt_stats/seeds --out runs/egypt_stats

Thresholds default to the pre-registered EXP-001 values; override to re-decide.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cultural_cpt.experiment import ArmResult, ExperimentResult  # noqa: E402
from cultural_cpt.stats import StatsConfig, aggregate_runs  # noqa: E402


def _result_from_dict(d: dict) -> ExperimentResult:
    arms = [ArmResult(**a) for a in d["arms"]]
    rest = {k: v for k, v in d.items() if k != "arms"}
    return ExperimentResult(arms=arms, **rest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-dir", required=True, help="dir of seed_<s>.json checkpoints")
    parser.add_argument("--out", default="", help="where to write result.json (default: seeds-dir's parent)")
    parser.add_argument("--min-shift", type=float, default=0.05)
    parser.add_argument("--sigma", type=float, default=2.0)
    parser.add_argument("--max-cap-drop", type=float, default=0.10)
    parser.add_argument("--max-safety-drop", type=float, default=0.10)
    args = parser.parse_args()

    seeds_dir = Path(args.seeds_dir)
    files = sorted(seeds_dir.glob("seed_*.json"), key=lambda p: int(p.stem.split("_")[1]))
    if not files:
        raise SystemExit(f"no seed_*.json checkpoints under {seeds_dir}")
    runs = [_result_from_dict(json.loads(f.read_text())) for f in files]
    seeds = tuple(r.seed for r in runs)
    print(f"re-aggregating {len(runs)} seeds {list(seeds)} from {seeds_dir}")

    config = StatsConfig(
        seeds=seeds,
        min_grounded_shift=args.min_shift,
        sigma_multiple=args.sigma,
        max_capability_drop=args.max_cap_drop,
        max_safety_drop=args.max_safety_drop,
    )
    result = aggregate_runs(runs, config)

    out_dir = Path(args.out) if args.out else seeds_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("  arm                  survey-shift (mean+-std)   behav-shift          capability  refusal")
    for arm in result.arms:
        print(
            f"    {arm.arm:<18} {arm.survey_shift_mean:+.3f} +- {arm.survey_shift_std:.3f}        "
            f"{arm.behavior_shift_mean:+.3f} +- {arm.behavior_shift_std:.3f}    {arm.capability_mean:.2f}        "
            f"{arm.safety_mean:.2f}"
        )
    for comp in result.comparisons:
        print(f"    {comp.name:<24} {comp.mean:+.3f} +- {comp.std:.3f}   z={comp.z:+.2f}")
    print(f"  VERDICT: {'PASS' if result.passed else 'FAIL'}")
    print(f"    {result.verdict}")
    if result.caveat:
        print(f"\n  {result.caveat}")
    print(f"\n  wrote {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
