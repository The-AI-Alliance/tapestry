#!/usr/bin/env python3
"""Run deterministic metrics around the Tapestry consortium-training PoC."""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from consortium_experiment import (  # noqa: E402
    ConsortiumExperimentRunner,
    ExperimentConfig,
    NodeSpec,
    PolicySpec,
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


def _default_config(rounds: int, seed: int) -> ExperimentConfig:
    return ExperimentConfig(
        seed=seed,
        rounds=rounds,
        policy=PolicySpec(
            name="quality_floor_capped",
            quality_floor=0.75,
            max_node_weight=0.5,
        ),
        nodes=[
            NodeSpec(
                node_id=node_id,
                jurisdiction=node_id.title(),
                corpus=_encode(corpus),
                quality_score=QUALITY_SCORES[node_id],
                local_epochs=2,
                lr=0.01,
            )
            for node_id, corpus in DOMAIN_CORPORA.items()
        ],
    )


def main() -> None:
    """Run the default deterministic consortium-training experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="runs/consortium_experiment", help="directory for metrics.jsonl and summary.json"
    )
    parser.add_argument("--rounds", type=int, default=3, help="number of consortium-training rounds")
    parser.add_argument("--seed", type=int, default=7, help="random seed for deterministic runs")
    args = parser.parse_args()

    result = ConsortiumExperimentRunner(_default_config(rounds=args.rounds, seed=args.seed)).run()
    result.write_json(args.out)

    print("Tapestry consortium-training PoC metrics")
    print(f"  output dir                 : {args.out}")
    print(f"  rounds                     : {result.summary.rounds}")
    print(f"  policy                     : {result.summary.policy_name}")
    print(f"  final artifact count       : {result.summary.final_artifact_count}")
    print(f"  rejected contributions     : {result.summary.total_rejected_contributions}")
    print(f"  max observed node weight   : {result.summary.max_observed_node_weight:.3f}")
    print(f"  final shared-base delta L2 : {result.summary.final_shared_base_delta_norm:.6f}")


if __name__ == "__main__":
    main()
