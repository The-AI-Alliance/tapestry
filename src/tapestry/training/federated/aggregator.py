"""Central aggregator for federated training rounds.

Implements Federated Averaging (FedAvg): the aggregator holds the
canonical global model, distributes it to participating nodes, collects
their weight updates, and merges them via a sample-weighted average.

The aggregator never sees raw training data — only weight deltas that
have (optionally) been clipped and noised by each node's local DP engine.

Reference:
    McMahan et al., "Communication-Efficient Learning of Deep Networks
    from Decentralized Data" (AISTATS 2017)
"""

from __future__ import annotations

import copy

import torch
import torch.nn as nn

from tapestry.training.federated.protocols import NodeUpdate, RoundResult


class Aggregator:
    """Federated Averaging (FedAvg) aggregator.

    Maintains the global model and orchestrates one round of federated
    training by:

        1. Broadcasting the current global state to all nodes.
        2. Collecting ``NodeUpdate`` objects from each node.
        3. Computing a weighted average of the deltas (weighted by
           ``num_samples``).
        4. Applying the averaged delta to the global model.

    Args:
        global_model: The model architecture that defines the parameter
            structure.  The aggregator deep-copies this and owns the
            canonical global weights.
    """

    def __init__(self, global_model: nn.Module) -> None:
        self.global_model = copy.deepcopy(global_model)
        self._round = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def global_state(self) -> dict[str, torch.Tensor]:
        """Current global model state dict (read-only snapshot)."""
        return {k: v.clone() for k, v in self.global_model.state_dict().items()}

    def aggregate(self, updates: list[NodeUpdate]) -> RoundResult:
        """Merge a list of node updates into a new global model.

        Uses sample-weighted Federated Averaging: each node's delta is
        scaled by ``node.num_samples / total_samples`` before summation.

        Args:
            updates: Weight updates collected from participating nodes.

        Returns:
            A ``RoundResult`` containing the new global state and
            diagnostics.

        Raises:
            ValueError: If ``updates`` is empty.
        """
        if not updates:
            raise ValueError("Cannot aggregate zero updates")

        self._round += 1

        # Weighted average of deltas.
        total_samples = sum(u.num_samples for u in updates)
        averaged_delta: dict[str, torch.Tensor] = {}

        for name in updates[0].state_delta:
            averaged_delta[name] = sum(
                u.state_delta[name] * (u.num_samples / total_samples)
                for u in updates
            )  # type: ignore[assignment]

        # Apply averaged delta to global model.
        current_state = self.global_model.state_dict()
        new_state = {
            name: current_state[name] + averaged_delta[name]
            for name in current_state
        }
        self.global_model.load_state_dict(new_state)

        # Compute weighted average loss from node metadata.
        avg_loss = sum(
            u.metadata.get("loss", 0.0) * u.num_samples for u in updates
        ) / total_samples

        return RoundResult(
            round_num=self._round,
            aggregated_state=self.global_state,
            participating_nodes=[u.node_id for u in updates],
            avg_loss=avg_loss,
        )
