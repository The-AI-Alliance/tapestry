#!/usr/bin/env python3
"""Run the Tapestry consortium-training proof of concept."""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    ContributionWeighting,
    OuterMergeOptimizer,
    OuterMergeStrategy,
    SovereignTrainingNode,
    TinyCausalModel,
)

DOMAIN_CORPORA: dict[str, list[str]] = {
    "vietnam": [
        "Vietnamese public services require local legal context.",
        "Agricultural advice must reflect Mekong Delta climate conditions.",
        "Education examples should match Vietnamese classroom expectations.",
    ],
    "switzerland": [
        "Swiss AI deployments must respect multilingual governance.",
        "Public-sector systems require federal and cantonal context.",
        "Trustworthy AI depends on auditability and institutional neutrality.",
    ],
    "india": [
        "Indian AI systems must work across many languages and scripts.",
        "Digital public infrastructure shapes local adoption patterns.",
        "Health advice must reflect regional institutions and constraints.",
    ],
}


QUALITY_SCORES = {
    "vietnam": 0.90,
    "switzerland": 0.86,
    "india": 0.88,
}


def _encode(texts: list[str]) -> list[list[int]]:
    """Byte-encode text into the tiny model's vocabulary range."""
    return [[token % 128 for token in text.encode("utf-8")] for text in texts]


def run_demo(
    rounds: int = 3,
    seed: int = 7,
    weighting: ContributionWeighting | str = ContributionWeighting.QUALITY,
    outer_merge: OuterMergeStrategy | str = OuterMergeStrategy.WEIGHTED_AVERAGE,
    outer_lr: float = 1.0,
    outer_momentum: float = 0.9,
) -> None:
    """Run a small N+1 consortium-training loop."""
    weighting = ContributionWeighting(weighting)
    outer_merge = OuterMergeStrategy(outer_merge)
    random.seed(seed)
    torch.manual_seed(seed)

    print("=" * 72)
    print("  TAPESTRY -- Consortium Training Proof of Concept")
    print("  One governed shared base + N sovereign participant models")
    print(f"  Contribution weighting: {weighting.value}")
    print(f"  Outer merge: {outer_merge.value}")
    print("=" * 72)

    momentum = outer_momentum if outer_merge is OuterMergeStrategy.MOMENTUM_DELTA else 0.0
    base_model = TinyCausalModel(vocab_size=128, hidden_size=32)
    coordinator = ConsortiumCoordinator(
        base_model=base_model,
        contribution_policy=ContributionPolicy(
            quality_floor=0.75,
            max_node_weight=0.5,
            weighting=weighting,
        ),
        outer_merge=OuterMergeOptimizer(
            strategy=outer_merge,
            outer_lr=outer_lr,
            outer_momentum=momentum,
        ),
    )
    nodes = [
        SovereignTrainingNode(
            node_id=node_id,
            jurisdiction=node_id.title(),
            model=base_model,
            sovereign_corpus=_encode(corpus),
            quality_score=QUALITY_SCORES[node_id],
            local_epochs=2,
            lr=0.01,
        )
        for node_id, corpus in DOMAIN_CORPORA.items()
    ]

    for round_num in range(1, rounds + 1):
        result = coordinator.run_round(nodes)
        print(f"\nRound {round_num}")
        print(f"  accepted nodes : {', '.join(result.accepted_nodes)}")
        rejected = ", ".join(result.rejected_nodes) or "none"
        print(f"  rejected nodes : {rejected}")
        print("  contribution weights:")
        for node_id, weight in sorted(result.contribution_weights.items()):
            print(f"    {node_id:12s} {weight:.3f}")
        print(f"  outer merge      : {result.outer_merge_strategy}")
        print(
            "  sovereign artifacts retained:",
            ", ".join(sorted(coordinator.sovereign_artifacts)),
        )

    print("\nN+1 outcome:")
    print("  1 shared base model evolved by governed contributions")
    artifact_count = len(coordinator.sovereign_artifacts)
    print(f"  {artifact_count} sovereign model artifacts retained")
    print("=" * 72)


def run_weighting_comparison(rounds: int = 3, seed: int = 7) -> None:
    """Run the same scenario with quality-weighted and equal influence policies."""
    for weighting in (ContributionWeighting.QUALITY, ContributionWeighting.EQUAL):
        run_demo(rounds=rounds, seed=seed, weighting=weighting)
        print()


def run_outer_merge_comparison(rounds: int = 3, seed: int = 7) -> None:
    """Run the same scenario with each outer merge strategy."""
    for outer_merge in OuterMergeStrategy:
        run_demo(rounds=rounds, seed=seed, outer_merge=outer_merge)
        print()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Tapestry consortium-training proof of concept.")
    parser.add_argument("--rounds", type=int, default=3, help="Number of consortium-training rounds to run.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed used for deterministic demo setup.")
    parser.add_argument(
        "--weighting",
        choices=(ContributionWeighting.QUALITY.value, ContributionWeighting.EQUAL.value, "compare"),
        default="quality",
        help="Contribution weighting policy to run. Use 'compare' to run quality and equal policies back to back.",
    )
    parser.add_argument(
        "--outer-merge",
        choices=tuple(strategy.value for strategy in OuterMergeStrategy) + ("compare",),
        default=OuterMergeStrategy.WEIGHTED_AVERAGE.value,
        help="Outer merge strategy to run. Use 'compare' to run all strategies back to back.",
    )
    parser.add_argument("--outer-lr", type=float, default=1.0, help="Outer learning rate for delta merge strategies.")
    parser.add_argument(
        "--outer-momentum",
        type=float,
        default=0.9,
        help="Outer momentum used by the momentum-delta merge strategy.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.weighting == "compare":
        run_weighting_comparison(rounds=args.rounds, seed=args.seed)
    elif args.outer_merge == "compare":
        run_outer_merge_comparison(rounds=args.rounds, seed=args.seed)
    else:
        run_demo(
            rounds=args.rounds,
            seed=args.seed,
            weighting=args.weighting,
            outer_merge=args.outer_merge,
            outer_lr=args.outer_lr,
            outer_momentum=args.outer_momentum,
        )
