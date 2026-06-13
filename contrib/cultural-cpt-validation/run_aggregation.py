#!/usr/bin/env python3
"""Run the aggregation-survival experiment: do cultures survive FedAvg?

Smoke mode (default) runs the multi-node consortium loop on a byte-level toy
model. Its separability curve is noise; it proves the plumbing. See
tech-docs/experiments/cultural-cpt-validation.md (consortium extension).
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cultural_cpt import AggregationConfig, run_aggregation  # noqa: E402


def main() -> None:
    """Run a single deterministic aggregation-survival experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cultures", default="vietnam,sweden,usa", help="comma-separated cultures")
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument(
        "--corpus-path",
        default="",
        help="real data root; expects <path>/<culture>/ per culture (empty = placeholder)",
    )
    parser.add_argument("--out", default="runs/cultural_cpt_aggregation")
    args = parser.parse_args()

    cultures = tuple(c.strip() for c in args.cultures.split(",") if c.strip())
    config = AggregationConfig(
        cultures=cultures, rounds=args.rounds, seed=args.seed, epochs=args.epochs, corpus_path=args.corpus_path
    )
    result = run_aggregation(config)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("Aggregation-survival experiment (do cultures survive FedAvg?)")
    print(f"  mode     : {result.mode}")
    print(f"  cultures : {', '.join(result.cultures)}")
    print(f"  seed     : {result.seed}")
    print("  round   separability   dist-to-centroid   per-culture (TS,SS)")
    for metric in result.rounds:
        coords = "  ".join(f"{n.culture[:3]}({n.ts:+.2f},{n.ss:+.2f})" for n in metric.nodes)
        print(
            f"    {metric.round_num:<5} {metric.mean_pairwise_distance:>9.3f}   "
            f"{metric.mean_distance_to_centroid:>14.3f}   {coords}"
        )
    curve = " -> ".join(f"{x:.3f}" for x in result.separability_curve)
    print(f"  separability curve: {curve}")
    trend = "shrinking (homogenizing)" if result.separability_curve[-1] < result.separability_curve[0] else "holding/growing"
    print(f"  trend: {trend}")
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


if __name__ == "__main__":
    main()
