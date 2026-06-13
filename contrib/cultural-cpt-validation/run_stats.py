#!/usr/bin/env python3
"""Multi-seed EXP-001 run with the pre-registered go/no-go decision.

Runs the experiment across several seeds, reports each arm's shift as mean ± std,
the decisive comparisons as effect sizes (z = mean/std), and a PASS/FAIL against
the pre-registered threshold. Smoke mode (default) does this on the toy model,
so the verdict is meaningless — it proves the decision plumbing.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cultural_cpt import ExperimentConfig, StatsConfig, run_multiseed  # noqa: E402


def main() -> None:
    """Run a deterministic multi-seed EXP-001 experiment and decide PASS/FAIL."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="smoke", choices=("smoke", "hf"))
    parser.add_argument("--culture", default="vietnam")
    parser.add_argument("--model-name", default="")
    parser.add_argument("--corpus-path", default="")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=None, help="CPT lr (default 0.01 smoke / 2e-5 hf)")
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"), help="hf compute device")
    parser.add_argument(
        "--dtype", default="float32", choices=("float32", "bfloat16"), help="hf model dtype"
    )
    parser.add_argument(
        "--instrument-lang", default="en", choices=("en", "ar"), help="language to administer the survey in"
    )
    parser.add_argument("--seeds", default="0,1,2,3,4", help="comma-separated seeds")
    parser.add_argument("--min-shift", type=float, default=0.05, help="pre-registered X")
    parser.add_argument("--sigma", type=float, default=2.0, help="pre-registered sigma multiple")
    parser.add_argument("--max-cap-drop", type=float, default=0.10, help="pre-registered Y")
    parser.add_argument("--out", default="runs/cultural_cpt_stats")
    args = parser.parse_args()

    seeds = tuple(int(s) for s in args.seeds.split(",") if s.strip())
    lr = args.lr if args.lr is not None else (0.01 if args.mode == "smoke" else 2e-5)
    config = StatsConfig(
        base=ExperimentConfig(
            mode=args.mode,
            culture=args.culture,
            model_name=args.model_name,
            corpus_path=args.corpus_path,
            epochs=args.epochs,
            lr=lr,
            device=args.device,
            dtype=args.dtype,
            instrument_lang=args.instrument_lang,
        ),
        seeds=seeds,
        min_grounded_shift=args.min_shift,
        sigma_multiple=args.sigma,
        max_capability_drop=args.max_cap_drop,
    )
    result = run_multiseed(config)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("EXP-001 multi-seed go/no-go")
    print(f"  culture : {args.culture}   seeds : {result.seeds}")
    print("  arm                  survey-shift (mean+-std)   behav-shift          capability")
    for arm in result.arms:
        print(
            f"    {arm.arm:<18} {arm.survey_shift_mean:+.3f} +- {arm.survey_shift_std:.3f}        "
            f"{arm.behavior_shift_mean:+.3f} +- {arm.behavior_shift_std:.3f}    {arm.capability_mean:.2f}"
        )
    print("  decisive comparisons (mean +- std, z = effect/noise):")
    for comp in result.comparisons:
        print(f"    {comp.name:<24} {comp.mean:+.3f} +- {comp.std:.3f}   z={comp.z:+.2f}")
    print(f"  VERDICT: {'PASS' if result.passed else 'FAIL'}")
    print(f"    {result.verdict}")
    if result.caveat:
        print(f"\n  {result.caveat}")


if __name__ == "__main__":
    main()
