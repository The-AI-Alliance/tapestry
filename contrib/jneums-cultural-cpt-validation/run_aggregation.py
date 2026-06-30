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

from cultural_cpt import (  # noqa: E402
    AggregationConfig,
    run_aggregation,
    run_aggregation_resampled,
)


def _run_banded(config: AggregationConfig, args, out_dir: Path) -> None:
    """Corpus-resampled sweep: run the aggregation over N draws and band the curves."""

    def _on_draw(d: int, res) -> None:
        curve = " -> ".join(f"{x:.3f}" for x in res.separability_curve)
        print(f"  [draw {d + 1}/{args.corpus_draws}] shift-sep curve: {curve}", flush=True)

    print(
        f"\nResampled aggregation-survival sweep: {args.corpus_draws} draws "
        f"@ fraction {args.corpus_fraction} (base seed {args.corpus_base_seed})",
        flush=True,
    )
    result = run_aggregation_resampled(
        config,
        draws=args.corpus_draws,
        sample_fraction=args.corpus_fraction,
        base_sample_seed=args.corpus_base_seed,
        on_draw=_on_draw,
        cache_dir=out_dir,
    )
    (out_dir / "result_resampled.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")

    print("\nAggregation-survival, corpus-resampled (mean +/- std across draws)")
    print(f"  mode     : {result.mode}")
    print(f"  cultures : {', '.join(result.cultures)}")
    print(f"  draws    : {len(result.sample_seeds)} (seeds {result.sample_seeds}) @ fraction {result.sample_fraction}")
    print("  round   shift-sep        abs-sep          merge-cos        retained")
    for b in result.rounds:
        print(
            f"    {b.round_num:<5} {b.shift_sep_mean:.3f}+/-{b.shift_sep_std:.3f}   "
            f"{b.abs_sep_mean:.3f}+/-{b.abs_sep_std:.3f}   "
            f"{b.merge_cosine_mean:+.3f}+/-{b.merge_cosine_std:.3f}   "
            f"{b.retained_mean:.3f}+/-{b.retained_std:.3f}"
        )
    band = "  ".join(f"{m:.3f}+/-{s:.3f}" for m, s in result.shift_separability_band)
    print(f"  shift-separability band: {band}")

    # Same diagnostic-aware classification as the single run, on the banded means.
    first, last = result.rounds[0], result.rounds[-1]
    shift_shrinking = last.shift_sep_mean < first.shift_sep_mean
    interfering = last.merge_cosine_mean <= 0.0 or last.retained_mean < 0.5
    if shift_shrinking and interfering:
        trend = "shift-sep shrinking, but via merge INTERFERENCE (not homogenization)"
    elif shift_shrinking:
        trend = "shift-sep shrinking with aligned updates -> cultural HOMOGENIZATION"
    else:
        trend = "shift-sep holding/growing -> sovereign alignment surviving"
    print(f"  trend: {trend}")
    spreading = last.abs_sep_mean >= first.abs_sep_mean
    print(
        f"  abs-coords: nodes {'SPREADING apart (staying distinct)' if spreading else 'CONVERGING toward a centroid'}"
        f"  (abs-sep {first.abs_sep_mean:.3f} -> {last.abs_sep_mean:.3f})"
    )
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


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
    parser.add_argument(
        "--corpus-draws",
        type=int,
        default=1,
        help=">=2 resamples each culture's grounded corpus over N draws and bands the curves",
    )
    parser.add_argument(
        "--corpus-fraction", type=float, default=0.7, help="per-draw fraction of each culture's grounded pool (0,1)"
    )
    parser.add_argument("--corpus-base-seed", type=int, default=0, help="first corpus draw seed (draw d uses base+d)")
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

    if args.corpus_draws >= 2:
        _run_banded(config, args, out_dir)
        return

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
    abs_vals = [m.abs_pairwise_distance for m in result.rounds]
    print(f"  abs-separability curve  : {' -> '.join(f'{x:.3f}' for x in abs_vals)}")

    # Classify the outcome from BOTH the shift-separability direction AND the
    # weight-space merge diagnostics, so the one-line trend never prejudges the cause:
    # a shrinking shift-curve with conflicting/cancelling fork updates is merge
    # INTERFERENCE, not cultural homogenization (cf. arXiv:2605.25846, LITERATURE.md §6).
    # A naive "shrinking == homogenizing" label is misleading -- e.g. shift-sep can dip
    # while absolute coordinates SPREAD apart (sovereign alignment surviving a lossy merge).
    shift_shrinking = result.separability_curve[-1] < result.separability_curve[0]
    last = result.rounds[-1]
    interfering = last.mean_update_cosine <= 0.0 or last.retained_update_ratio < 0.5
    if shift_shrinking and interfering:
        trend = "shift-sep shrinking, but via merge INTERFERENCE (not homogenization)"
    elif shift_shrinking:
        trend = "shift-sep shrinking with aligned updates -> cultural HOMOGENIZATION"
    else:
        trend = "shift-sep holding/growing -> sovereign alignment surviving"
    print(f"  trend: {trend}")
    spreading = abs_vals[-1] >= abs_vals[0]
    print(
        f"  abs-coords: nodes {'SPREADING apart (staying distinct)' if spreading else 'CONVERGING toward a centroid'}"
        f"  (abs-sep {abs_vals[0]:.3f} -> {abs_vals[-1]:.3f})"
    )
    # Detailed merge-mode read (companion to the trend word above).
    if shift_shrinking:
        if interfering:
            print(
                "  read: shift-separability is shrinking WITH conflicting/cancelling fork updates "
                "(low cosine / retained) -> merge INTERFERENCE, not pure cultural homogenization "
                "(cf. arXiv:2605.25846)."
            )
        else:
            print(
                "  read: shift-separability is shrinking while fork updates stay aligned (high cosine / "
                "retained) -> genuine cultural HOMOGENIZATION toward the centroid."
            )
    if result.smoke_caveat:
        print(f"\n  {result.smoke_caveat}")


if __name__ == "__main__":
    main()
