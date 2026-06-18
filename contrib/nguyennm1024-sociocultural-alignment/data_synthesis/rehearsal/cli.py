"""CLI entry for the rehearsal pipeline.

Usage:
    python -m rehearsal.cli download              [--test-only | --train-only] [--source X]
    python -m rehearsal.cli decontam-build        [--only T1,T2] [--out PATH]
    python -m rehearsal.cli questions extract     [--source X | --category Y] [--limit N]
    python -m rehearsal.cli questions augment     # not yet implemented
    python -m rehearsal.cli questions generate    # not yet implemented
    python -m rehearsal.cli questions nih         # not yet implemented
    python -m rehearsal.cli solve                 [--category X]     # not yet implemented
    python -m rehearsal.cli verify                [--category X]     # not yet implemented
    python -m rehearsal.cli validate                                  # not yet implemented
    python -m rehearsal.cli assemble                                  # not yet implemented
    python -m rehearsal.cli pilot                                     # not yet implemented
"""
from __future__ import annotations

import argparse
import sys


def _cmd_download(args: argparse.Namespace) -> int:
    from .data.download import run_download
    results = run_download(
        train_only=args.train_only,
        test_only=args.test_only,
        source_filter=args.source,
    )
    return 1 if any(r.status == "failed" for r in results) else 0


def _cmd_decontam_build(args: argparse.Namespace) -> int:
    from .data.decontam import build_index
    only = args.only.split(",") if args.only else None
    build_index(out_path=args.out, only=only)
    return 0


def _cmd_questions_extract(args: argparse.Namespace) -> int:
    from .data.extract import extract_all, EXTRACTORS
    if args.source and args.source not in EXTRACTORS:
        print(f"error: no extractor registered for source '{args.source}'. "
              f"Available: {sorted(EXTRACTORS)}", file=sys.stderr)
        return 2
    results = extract_all(
        category_filter=args.category,
        source_filter=args.source,
        limit_per_source=args.limit,
    )
    print("", file=sys.stderr)
    print(f"[questions extract] summary: {len(results)} source(s) processed",
          file=sys.stderr)
    for name, n in sorted(results.items()):
        print(f"  {name}: {n}", file=sys.stderr)
    any_failed = any(n == -1 for n in results.values())
    return 1 if any_failed else 0


def _cmd_not_implemented(args: argparse.Namespace) -> int:
    full = args.subcommand
    if hasattr(args, "questions_op"):
        full += " " + args.questions_op
    print(f"error: subcommand '{full}' not yet implemented", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="rehearsal",
        description="CLI entry for the rehearsal pipeline.",
    )
    sub = p.add_subparsers(dest="subcommand", required=True)

    # download ------------------------------------------------------------
    sp = sub.add_parser("download", help="Fetch HF datasets into the local cache.")
    sp.add_argument("--train-only", action="store_true")
    sp.add_argument("--test-only", action="store_true")
    sp.add_argument("--source", default=None)
    sp.set_defaults(func=_cmd_download)

    # decontam-build ------------------------------------------------------
    sp = sub.add_parser("decontam-build",
                        help="Build the exact + 13-gram decontam index.")
    sp.add_argument("--only", default=None,
                    help="Comma-separated DecontamTestset names to index.")
    from .data.decontam import DEFAULT_INDEX_PATH
    sp.add_argument("--out", default=str(DEFAULT_INDEX_PATH),
                    help=f"Output pickle path (default: {DEFAULT_INDEX_PATH}).")
    sp.set_defaults(func=_cmd_decontam_build)

    # questions (with sub-operations) ------------------------------------
    qp = sub.add_parser("questions", help="Build the per-category question pool.")
    qsub = qp.add_subparsers(dest="questions_op", required=True)

    qe = qsub.add_parser("extract",
                         help="Extract questions from cached public HF datasets.")
    qe.add_argument("--source", default=None,
                    help="Single source name. Omit to run all wired sources.")
    qe.add_argument("--category", default=None,
                    help="Restrict to one category (e.g. mmlu_shaped).")
    qe.add_argument("--limit", type=int, default=None,
                    help="Cap rows per source (useful for spot-checks).")
    qe.set_defaults(func=_cmd_questions_extract)

    for op, help_text in [
        ("augment", "Augment public seeds: B2 GSM8K variants, B6 IFEval constraints (stubbed)."),
        ("generate", "Fresh-generated questions: B5 GPQA, B7 BFCL, B10 anti-modecollapse (stubbed)."),
        ("nih", "Programmatic NIH long-context items (stubbed)."),
    ]:
        op_sp = qsub.add_parser(op, help=help_text)
        op_sp.set_defaults(func=_cmd_not_implemented)

    # downstream stubs ----------------------------------------------------
    for name, help_text in [
        ("solve", "Run Kimi K2.6 on the question pool (stubbed)."),
        ("verify", "Per-category answer verification (stubbed)."),
        ("validate", "Distribution-match validation (stubbed)."),
        ("assemble", "Sample to 40K, write final JSONL (stubbed)."),
        ("pilot", "10%% end-to-end pilot (stubbed)."),
    ]:
        sp = sub.add_parser(name, help=help_text)
        sp.set_defaults(func=_cmd_not_implemented)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
