"""Deterministic experiment runner for the consortium-training proof of concept."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import torch

from .metrics import max_weight, state_delta_norm
from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    SovereignTrainingNode,
    TinyCausalModel,
)


@dataclass(frozen=True)
class NodeSpec:
    """Configuration for one sovereign participant node in a PoC experiment."""

    node_id: str
    jurisdiction: str
    corpus: Sequence[list[int]]
    quality_score: float
    local_epochs: int = 2
    lr: float = 0.01
    batch_size: int = 8


@dataclass(frozen=True)
class PolicySpec:
    """Configuration for the PoC contribution policy."""

    name: str = "quality_weighted"
    quality_floor: float = 0.0
    max_node_weight: float = 1.0

    def build(self) -> ContributionPolicy:
        """Build the contribution policy for this experiment."""
        return ContributionPolicy(
            quality_floor=self.quality_floor,
            max_node_weight=self.max_node_weight,
        )


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for a deterministic consortium-training PoC experiment."""

    seed: int
    rounds: int
    nodes: Sequence[NodeSpec]
    policy: PolicySpec
    model_vocab_size: int = 128
    model_hidden_size: int = 32


@dataclass(frozen=True)
class RoundMetrics:  # pylint: disable=too-many-instance-attributes
    """Machine-readable metrics for one consortium-training round."""

    round_num: int
    accepted_nodes: list[str]
    rejected_nodes: list[str]
    contribution_weights: dict[str, float]
    max_node_weight: float
    shared_base_delta_norm: float
    sovereign_artifact_count: int
    node_losses: dict[str, float]


@dataclass(frozen=True)
class ExperimentSummary:
    """Summary metrics for a completed consortium-training PoC experiment."""

    seed: int
    rounds: int
    policy_name: str
    final_artifact_count: int
    total_rejected_contributions: int
    max_observed_node_weight: float
    final_shared_base_delta_norm: float


@dataclass(frozen=True)
class ExperimentResult:
    """Complete result for a consortium-training PoC experiment."""

    config: ExperimentConfig
    rounds: list[RoundMetrics]
    summary: ExperimentSummary

    def write_json(self, output_dir: Path | str) -> None:
        """Write round metrics as JSONL and the summary as JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with (output_path / "metrics.jsonl").open("w", encoding="utf-8") as metrics_file:
            for round_metrics in self.rounds:
                metrics_file.write(json.dumps(asdict(round_metrics), sort_keys=True) + "\n")

        with (output_path / "summary.json").open("w", encoding="utf-8") as summary_file:
            json.dump(asdict(self.summary), summary_file, indent=2, sort_keys=True)
            summary_file.write("\n")


class ConsortiumExperimentRunner:  # pylint: disable=too-few-public-methods
    """Run deterministic CI-scale measurements around the existing consortium PoC."""

    def __init__(self, config: ExperimentConfig) -> None:
        if config.rounds < 1:
            raise ValueError("rounds must be at least 1")
        if not config.nodes:
            raise ValueError("at least one node is required")
        self.config = config

    def run(self) -> ExperimentResult:
        """Run the configured consortium-training experiment."""
        random.seed(self.config.seed)
        torch.manual_seed(self.config.seed)

        base_model = TinyCausalModel(
            vocab_size=self.config.model_vocab_size,
            hidden_size=self.config.model_hidden_size,
        )
        coordinator = ConsortiumCoordinator(
            base_model=base_model,
            contribution_policy=self.config.policy.build(),
        )
        nodes = [self._build_node(node_spec, base_model) for node_spec in self.config.nodes]

        round_metrics: list[RoundMetrics] = []
        for _round in range(self.config.rounds):
            result = coordinator.run_round(nodes)
            node_losses = {
                node_id: artifact.metrics["loss"]
                for node_id, artifact in sorted(coordinator.sovereign_artifacts.items())
            }
            round_metrics.append(
                RoundMetrics(
                    round_num=result.round_num,
                    accepted_nodes=result.accepted_nodes,
                    rejected_nodes=result.rejected_nodes,
                    contribution_weights=result.contribution_weights,
                    max_node_weight=max_weight(result.contribution_weights),
                    shared_base_delta_norm=state_delta_norm(
                        result.previous_base_state,
                        result.shared_base_state,
                    ),
                    sovereign_artifact_count=len(coordinator.sovereign_artifacts),
                    node_losses=node_losses,
                )
            )

        summary = ExperimentSummary(
            seed=self.config.seed,
            rounds=self.config.rounds,
            policy_name=self.config.policy.name,
            final_artifact_count=len(coordinator.sovereign_artifacts),
            total_rejected_contributions=sum(len(metrics.rejected_nodes) for metrics in round_metrics),
            max_observed_node_weight=max((metrics.max_node_weight for metrics in round_metrics), default=0.0),
            final_shared_base_delta_norm=round_metrics[-1].shared_base_delta_norm,
        )
        return ExperimentResult(config=self.config, rounds=round_metrics, summary=summary)

    @staticmethod
    def _build_node(node_spec: NodeSpec, base_model: TinyCausalModel) -> SovereignTrainingNode:
        return SovereignTrainingNode(
            node_id=node_spec.node_id,
            jurisdiction=node_spec.jurisdiction,
            model=base_model,
            sovereign_corpus=node_spec.corpus,
            quality_score=node_spec.quality_score,
            local_epochs=node_spec.local_epochs,
            lr=node_spec.lr,
            batch_size=node_spec.batch_size,
        )
