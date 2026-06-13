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
    parser.add_argument(
        "--lr",
        type=float,
        default=None,
        help="CPT learning rate (default: 0.01 for smoke toy model, 2e-5 for a real transformer)",
    )
    parser.add_argument("--model-name", default="", help="HF model id (real mode)")
    parser.add_argument("--corpus-path", default="", help="real corpus source (empty = placeholder)")
    parser.add_argument(
        "--instrument-lang", default="en", choices=("en", "ar"), help="language to administer the survey in"
    )
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"), help="hf mode compute device")
    parser.add_argument(
        "--dtype",
        default="float32",
        choices=("float32", "bfloat16"),
        help="hf mode model dtype (bfloat16 halves CPT memory)",
    )
    parser.add_argument("--out", default="runs/cultural_cpt_validation")
    args = parser.parse_args()

    # A toy byte model tolerates lr=0.01; a real transformer diverges at it.
    lr = args.lr if args.lr is not None else (0.01 if args.mode == "smoke" else 2e-5)

    config = ExperimentConfig(
        mode=args.mode,
        culture=args.culture,
        seed=args.seed,
        epochs=args.epochs,
        lr=lr,
        model_name=args.model_name,
        corpus_path=args.corpus_path,
        device=args.device,
        dtype=args.dtype,
        instrument_lang=args.instrument_lang,
    )
    result = run_experiment(config)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("EXP-001 cultural-CPT validation (minimal go/no-go)")
    print(f"  mode            : {result.mode}")
    print(f"  culture         : {result.culture}  target=({result.target_ts:+.2f}, {result.target_ss:+.2f})")
    print(f"  seed            : {result.seed}")
    print("  arm                survey-shift   behav-shift   mimicry-gap   capability")
    for arm in result.arms:
        loss = "" if arm.train_loss is None else f"  (loss {arm.train_loss:.2f})"
        print(
            f"    {arm.arm:<16} {arm.shift_toward_target:+.3f}        "
            f"{arm.behavior_shift_toward_target:+.3f}        "
            f"{arm.survey_behavior_gap:.3f}         {arm.capability_acc:.2f}{loss}"
        )
    print("  decisive comparisons (grounded survey shift minus other arm):")
    print(f"    vs language-matched   : {result.decisive_grounded_vs_language:+.3f}   (grounding beyond language?)")
    print(f"    vs grounded-translated: {result.decisive_grounded_vs_translated:+.3f}   (content vs language carrier?)")
    print(f"    vs surface-only       : {result.decisive_grounded_vs_surface:+.3f}   (CPT beats prompting?)")

    grounded = next((a for a in result.arms if a.arm == "grounded"), None)
    if grounded is not None:
        # Mimicry signal: survey moved toward target but behavior lagged behind.
        lag = grounded.shift_toward_target - grounded.behavior_shift_toward_target
        verdict = (
            "behavior tracks survey (coherent shift)"
            if abs(lag) < 0.05
            else "survey moved more than behavior (possible mimicry)" if lag > 0 else "behavior moved more than survey"
        )
        print(f"  grounded survey-vs-behavior lag: {lag:+.3f} -> {verdict}")
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


if __name__ == "__main__":
    main()
