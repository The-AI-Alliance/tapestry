#!/usr/bin/env python3
"""Run the aggregation-survival experiment: do cultures survive FedAvg?

Smoke mode (default) runs the multi-node consortium loop on a byte-level toy
model -- its separability curve is noise; it proves the plumbing. Real mode
(``--mode hf``) runs a real Hugging Face base per node on real per-culture
corpora (``--corpus-path`` with ``<path>/<culture>/`` per culture); that is the
T3 signal. See SPEC.md (consortium extension).
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
    parser.add_argument("--mode", default="smoke", choices=("smoke", "hf"))
    parser.add_argument("--cultures", default="vietnam,sweden,usa", help="comma-separated cultures")
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=None, help="CPT lr (default 0.01 smoke / 2e-5 hf)")
    parser.add_argument("--model-name", default="", help="hf mode: base model id all nodes start from")
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"), help="hf compute device")
    parser.add_argument("--dtype", default="float32", choices=("float32", "bfloat16"), help="hf model dtype")
    parser.add_argument(
        "--instrument-lang", default="en", choices=("en", "ar", "vi"), help="survey language for every node"
    )
    parser.add_argument(
        "--corpus-path",
        default="",
        help="real data root; expects <path>/<culture>/ per culture (empty = placeholder)",
    )
    parser.add_argument(
        "--warmup-frac", type=float, default=0.0, help="hf stabilization: fraction of steps in linear LR warmup"
    )
    parser.add_argument(
        "--max-grad-norm", type=float, default=None, help="hf stabilization: clip gradients to this norm (default off)"
    )
    parser.add_argument("--out", default="runs/cultural_cpt_aggregation")
    args = parser.parse_args()

    cultures = tuple(c.strip() for c in args.cultures.split(",") if c.strip())
    lr = args.lr if args.lr is not None else (0.01 if args.mode == "smoke" else 2e-5)
    config = AggregationConfig(
        mode=args.mode,
        cultures=cultures,
        rounds=args.rounds,
        seed=args.seed,
        epochs=args.epochs,
        lr=lr,
        model_name=args.model_name,
        device=args.device,
        dtype=args.dtype,
        instrument_lang=args.instrument_lang,
        corpus_path=args.corpus_path,
        warmup_frac=args.warmup_frac,
        max_grad_norm=args.max_grad_norm,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # A real multi-round HF sweep is many GPU-hours and silent until the end;
    # checkpoint each round so progress is pollable and a preempted spot box
    # resumes for free (re-run the same command -- only unfinished rounds cost GPU).
    def _progress(metric) -> None:
        # Per-node SHIFT (Δ vs the round's shared base, in the node's own language)
        # is the signal; separability is on those shift vectors.
        shifts = "  ".join(f"{n.culture[:3]}[{n.lang}]Δ({n.shift_ts:+.2f},{n.shift_ss:+.2f})" for n in metric.nodes)
        print(
            f"  [round {metric.round_num}] shift-sep={metric.mean_pairwise_distance:.3f} "
            f"abs-sep={metric.abs_pairwise_distance:.3f} to-centroid={metric.mean_distance_to_centroid:.3f}  |  "
            f"merge: cos={metric.mean_update_cosine:+.3f} sign-agree={metric.update_sign_agreement:.3f} "
            f"retained={metric.retained_update_ratio:.3f}   {shifts}",
            flush=True,
        )

    result = run_aggregation(config, on_round=_progress, cache_dir=out_dir / "rounds")
    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("\nAggregation-survival experiment (do cultures survive FedAvg?)")
    print(f"  mode     : {result.mode}")
    print(f"  cultures : {', '.join(result.cultures)}")
    print(f"  seed     : {result.seed}")
    print(
        "  round   shift-sep   abs-sep   to-centroid   merge-cos   sign-agree   retained   per-culture shift Δ(TS,SS)"
    )
    for metric in result.rounds:
        shifts = "  ".join(f"{n.culture[:3]}[{n.lang}]({n.shift_ts:+.2f},{n.shift_ss:+.2f})" for n in metric.nodes)
        print(
            f"    {metric.round_num:<5} {metric.mean_pairwise_distance:>9.3f}   {metric.abs_pairwise_distance:>7.3f}   "
            f"{metric.mean_distance_to_centroid:>10.3f}   {metric.mean_update_cosine:>+8.3f}   "
            f"{metric.update_sign_agreement:>9.3f}   {metric.retained_update_ratio:>7.3f}   {shifts}"
        )
    curve = " -> ".join(f"{x:.3f}" for x in result.separability_curve)
    print(f"  shift-separability curve: {curve}")
    trend = (
        "shrinking (homogenizing)"
        if result.separability_curve[-1] < result.separability_curve[0]
        else "holding/growing"
    )
    print(f"  trend: {trend}")
    # Distinguish the two collapse modes (see aggregation.py docstring / LITERATURE.md §6).
    if result.separability_curve[-1] < result.separability_curve[0]:
        last = result.rounds[-1]
        if last.mean_update_cosine <= 0.0 or last.retained_update_ratio < 0.5:
            print(
                "  read: separability is shrinking WITH conflicting/cancelling fork updates "
                "(low cosine / retained) -> looks like merge INTERFERENCE, not pure cultural "
                "homogenization (cf. arXiv:2605.25846)."
            )
        else:
            print(
                "  read: separability is shrinking while fork updates stay aligned (high cosine / "
                "retained) -> looks like genuine cultural HOMOGENIZATION toward the centroid."
            )
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


if __name__ == "__main__":
    main()
