#!/usr/bin/env python3
"""Demonstrate contribution validation in front of the consortium outer merge."""

# pylint: disable=wrong-import-position,wrong-import-order

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from contribution_validator import (
    FingerprintingNode,
    StaleBaseNode,
    ValidatingConsortiumCoordinator,
    ValidationLimits,
)
from contribution_validator.faults import (
    Fault,
    FaultInjectingNode,
    add_parameter,
    cast_parameters,
    drop_parameter,
    inject_inf,
    inject_nan,
    reshape_parameter,
    scale_parameters,
)

from tapestry.training.consortium import (
    ContributionPolicy,
    SovereignTrainingNode,
    TinyCausalModel,
)

FAULTS: dict[str, Fault] = {
    "nan": inject_nan,
    "inf": inject_inf,
    "missing": drop_parameter,
    "extra": add_parameter,
    "shape": reshape_parameter,
    "float16": cast_parameters,
    "scaled": scale_parameters,
}

# Not a state fault: the node trains from a stale base and says so honestly.
STALE_BASE = "stale-base"

DOMAIN_CORPORA: dict[str, list[str]] = {
    "vietnam": [
        "Vietnamese public services require local legal context.",
        "Agricultural advice must reflect Mekong Delta climate conditions.",
    ],
    "switzerland": [
        "Swiss AI deployments must respect multilingual governance.",
        "Public-sector systems require federal and cantonal context.",
    ],
    "india": [
        "Indian AI systems must work across many languages and scripts.",
        "Digital public infrastructure shapes local adoption patterns.",
    ],
}


def _encode(texts: list[str]) -> list[list[int]]:
    return [[token % 128 for token in text.encode("utf-8")] for text in texts]


def _build_nodes(model: TinyCausalModel, faulty_node: str, fault: str | None) -> list[SovereignTrainingNode]:
    nodes: list[SovereignTrainingNode] = []
    for node_id, texts in DOMAIN_CORPORA.items():
        common: dict[str, Any] = {
            "node_id": node_id,
            "jurisdiction": node_id.title(),
            "model": model,
            "sovereign_corpus": _encode(texts),
            "quality_score": 0.9,
            "local_epochs": 1,
            "lr": 0.01,
        }
        if fault is None or node_id != faulty_node:
            nodes.append(FingerprintingNode(**common))
        elif fault == STALE_BASE:
            nodes.append(StaleBaseNode(**common))
        else:
            nodes.append(FaultInjectingNode(fault=FAULTS[fault], **common))
    return nodes


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=2, help="Number of consortium rounds to run.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for model init and local training.")
    parser.add_argument(
        "--fault",
        choices=sorted([*FAULTS, STALE_BASE]),
        default="nan",
        help=(
            "Corruption applied to one node's contribution before it reaches the coordinator. "
            "'stale-base' makes the node train from an old base instead, which the fingerprint check "
            "catches from round 2 on."
        ),
    )
    parser.add_argument("--no-fault", action="store_true", help="Run with all contributions well formed.")
    parser.add_argument(
        "--faulty-node",
        default="india",
        choices=sorted(DOMAIN_CORPORA),
        help="Which node's contribution is corrupted.",
    )
    parser.add_argument(
        "--dtype-policy",
        choices=["exact", "float-compatible"],
        default="exact",
        help="How strictly contributed dtypes must match the shared base.",
    )
    parser.add_argument(
        "--max-global-relative-update",
        type=float,
        default=None,
        help="Reject a contribution whose global update norm exceeds this fraction of the base norm.",
    )
    parser.add_argument(
        "--max-layer-relative-update",
        type=float,
        default=None,
        help="Reject a contribution if any tensor's update norm exceeds this fraction of its base norm.",
    )
    parser.add_argument(
        "--fingerprint-policy",
        choices=["if-present", "require", "ignore"],
        default="if-present",
        help="Whether contributions must declare the fingerprint of the base they trained from.",
    )
    parser.add_argument("--json", action="store_true", help="Print full validation reports as JSON.")
    return parser.parse_args()


def main() -> None:
    """Run the demo."""
    args = _parse_args()
    torch.manual_seed(args.seed)

    limits = ValidationLimits(
        dtype_policy=args.dtype_policy,
        fingerprint_policy=args.fingerprint_policy,
        max_global_relative_update=args.max_global_relative_update,
        max_layer_relative_update=args.max_layer_relative_update,
    )
    model = TinyCausalModel(vocab_size=128, hidden_size=16)
    coordinator = ValidatingConsortiumCoordinator(
        model,
        contribution_policy=ContributionPolicy(quality_floor=0.5, max_node_weight=0.6),
        limits=limits,
    )
    fault = None if args.no_fault else args.fault
    nodes = _build_nodes(model, args.faulty_node, fault)

    print(f"limits: {limits}")
    if fault is not None:
        print(f"fault: {args.fault!r} injected into node {args.faulty_node!r}")

    for _ in range(args.rounds):
        result = coordinator.run_round(nodes)
        reports = coordinator.validation_reports[result.round_num]
        print(
            f"\nround {result.round_num}  base {coordinator.round_summaries[result.round_num].base_fingerprint[:19]}..."
        )
        print(f"  accepted: {result.accepted_nodes}")
        print(f"  rejected: {result.rejected_nodes}")
        print(f"  weights:  { {k: round(v, 3) for k, v in result.contribution_weights.items()} }")
        for node_id, report in reports.items():
            stats = report.global_stats
            verdict = "accepted" if report.accepted else "REJECTED"
            print(
                f"  {node_id:<12} {verdict:<9} update_l2={stats.delta_l2:.4f} "
                f"relative={stats.relative_l2:.4f} non_finite={stats.non_finite_count}"
            )
            for finding in report.findings:
                print(f"    - [{finding.code}] {finding.message}")
        if args.json:
            print(json.dumps({node_id: report.to_dict() for node_id, report in reports.items()}, indent=2))


if __name__ == "__main__":
    main()
