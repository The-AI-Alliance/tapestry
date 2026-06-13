#!/usr/bin/env python3
"""Run the EXP-001 minimal go/no-go (Base / Language-matched / Grounded).

Smoke mode (default) runs on a byte-level toy model so the full pipeline is
exercised without downloads or GPUs. Its numbers are noise; it proves the
plumbing. See tech-docs/experiments/cultural-cpt-validation.md.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cultural_cpt import ExperimentConfig, run_experiment  # noqa: E402


def main() -> None:
    """Run a single deterministic EXP-001 minimal experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="smoke", choices=("smoke", "hf"))
    parser.add_argument("--culture", default="vietnam", help="target culture (must have WVS ground truth)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=4, help="CPT epochs per arm")
    parser.add_argument("--model-name", default="", help="HF model id (real mode)")
    parser.add_argument("--corpus-path", default="", help="real corpus source (empty = placeholder)")
    parser.add_argument("--out", default="runs/cultural_cpt_validation")
    args = parser.parse_args()

    config = ExperimentConfig(
        mode=args.mode,
        culture=args.culture,
        seed=args.seed,
        epochs=args.epochs,
        model_name=args.model_name,
        corpus_path=args.corpus_path,
    )
    result = run_experiment(config)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("EXP-001 cultural-CPT validation (minimal go/no-go)")
    print(f"  mode            : {result.mode}")
    print(f"  culture         : {result.culture}  target=({result.target_ts:+.2f}, {result.target_ss:+.2f})")
    print(f"  seed            : {result.seed}")
    print("  arm                  TS      SS    dist   shift   capability")
    for arm in result.arms:
        loss = "  -  " if arm.train_loss is None else f"{arm.train_loss:.3f}"
        print(
            f"    {arm.arm:<16} {arm.ts:+.2f}   {arm.ss:+.2f}   "
            f"{arm.distance_to_target:.3f}  {arm.shift_toward_target:+.3f}   "
            f"{arm.capability_acc:.2f}  (loss {loss})"
        )
    print(f"  decisive (grounded - language-matched shift): {result.decisive_grounded_vs_language:+.3f}")
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


if __name__ == "__main__":
    main()
