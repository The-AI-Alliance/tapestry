"""Coordinator for the consortium-training proof of concept."""

from __future__ import annotations

import copy
from collections.abc import Sequence

import torch
from torch import nn

from .node import SovereignTrainingNode
from .policy import ContributionPolicy
from .messages import (
    ConsortiumRoundResult,
    ModelState,
    SovereignModelArtifact,
)


class ConsortiumCoordinator:
    """Evolve a shared base from governed sovereign node contributions."""

    def __init__(
        self,
        base_model: nn.Module,
        contribution_policy: ContributionPolicy | None = None,
    ) -> None:
        self.base_model = copy.deepcopy(base_model)
        self.contribution_policy = contribution_policy or ContributionPolicy()
        self.sovereign_artifacts: dict[str, SovereignModelArtifact] = {}
        self._round = 0

    @property
    def shared_base_state(self) -> ModelState:
        """Snapshot of the current shared base model state."""
        return {name: tensor.clone() for name, tensor in self.base_model.state_dict().items()}

    def run_round(self, nodes: Sequence[SovereignTrainingNode]) -> ConsortiumRoundResult:
        """Run one N+1 consortium cycle across sovereign nodes."""
        self._round += 1
        previous_state = self.shared_base_state

        cycle_results = [node.run_sovereign_cycle(self._round, previous_state) for node in nodes]
        for result in cycle_results:
            self.sovereign_artifacts[result.artifact.node_id] = result.artifact

        contributions = [result.contribution for result in cycle_results]
        weights = self.contribution_policy.weights(
            {contribution.node_id: contribution.quality_score for contribution in contributions}
        )
        accepted = list(weights)
        rejected = [contribution.node_id for contribution in contributions if contribution.node_id not in weights]

        if weights:
            local_states_by_node = {
                contribution.node_id: contribution.local_model_state for contribution in contributions
            }
            integrated_state = self._apply_weighted_average(local_states_by_node, weights)
            self.base_model.load_state_dict(integrated_state)

        return ConsortiumRoundResult(
            round_num=self._round,
            previous_base_state=previous_state,
            shared_base_state=self.shared_base_state,
            accepted_nodes=accepted,
            rejected_nodes=rejected,
            contribution_weights=weights,
        )

    @staticmethod
    def _apply_weighted_average(
        local_states_by_node: dict[str, ModelState],
        weights: dict[str, float],
    ) -> ModelState:
        """FedAvg-class weighted average of contributed local model weight vectors."""
        sample_state = next(iter(local_states_by_node.values()))
        next_state: ModelState = {}
        for name, _base_tensor in sample_state.items():
            averaged = torch.zeros_like(sample_state[name])
            for node_id, weight in weights.items():
                averaged = averaged + local_states_by_node[node_id][name] * weight
            next_state[name] = averaged
        return next_state
