"""Outer-merge strategies for consortium training."""

from __future__ import annotations

from enum import Enum

import torch

from .messages import ModelState


class OuterMergeStrategy(str, Enum):
    """Supported ways to merge accepted sovereign node updates."""

    WEIGHTED_AVERAGE = "weighted-average"
    DELTA = "delta"
    MOMENTUM_DELTA = "momentum-delta"


class OuterMergeOptimizer:
    """Merge accepted local model states into the shared base.

    ``weighted-average`` is the existing FedAvg-class behavior. ``delta`` applies
    a weighted average of node deltas to the previous shared base, with an outer
    learning rate. ``momentum-delta`` adds a small outer momentum buffer, making
    the PoC capable of comparing DiLoCo-style outer optimizer behavior without
    changing the local sovereign training loop.
    """

    def __init__(
        self,
        strategy: OuterMergeStrategy | str = OuterMergeStrategy.WEIGHTED_AVERAGE,
        outer_lr: float = 1.0,
        outer_momentum: float = 0.0,
    ) -> None:
        self.strategy = OuterMergeStrategy(strategy)
        if outer_lr <= 0.0:
            raise ValueError("outer_lr must be positive")
        if not 0.0 <= outer_momentum < 1.0:
            raise ValueError("outer_momentum must be in [0, 1)")
        if self.strategy is OuterMergeStrategy.MOMENTUM_DELTA and outer_momentum == 0.0:
            raise ValueError("momentum-delta requires outer_momentum > 0")
        self.outer_lr = outer_lr
        self.outer_momentum = outer_momentum
        self._velocity: ModelState = {}

    def merge(
        self,
        previous_state: ModelState,
        local_states_by_node: dict[str, ModelState],
        weights: dict[str, float],
    ) -> ModelState:
        """Return the next shared-base state for the selected merge strategy."""
        if self.strategy is OuterMergeStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average(local_states_by_node, weights)

        weighted_delta = self._weighted_delta(previous_state, local_states_by_node, weights)
        if self.strategy is OuterMergeStrategy.MOMENTUM_DELTA:
            weighted_delta = self._apply_momentum(weighted_delta)

        return {
            name: previous_state[name] + weighted_delta[name] * self.outer_lr
            for name in previous_state
        }

    @staticmethod
    def _weighted_average(
        local_states_by_node: dict[str, ModelState],
        weights: dict[str, float],
    ) -> ModelState:
        """FedAvg-class weighted average of contributed local model states."""
        sample_state = next(iter(local_states_by_node.values()))
        next_state: ModelState = {}
        for name in sample_state:
            averaged = torch.zeros_like(sample_state[name])
            for node_id, weight in weights.items():
                averaged = averaged + local_states_by_node[node_id][name] * weight
            next_state[name] = averaged
        return next_state

    @staticmethod
    def _weighted_delta(
        previous_state: ModelState,
        local_states_by_node: dict[str, ModelState],
        weights: dict[str, float],
    ) -> ModelState:
        """Weighted average of node deltas from the previous shared base."""
        delta_state: ModelState = {}
        for name, base_tensor in previous_state.items():
            delta = torch.zeros_like(base_tensor)
            for node_id, weight in weights.items():
                delta = delta + (local_states_by_node[node_id][name] - base_tensor) * weight
            delta_state[name] = delta
        return delta_state

    def _apply_momentum(self, weighted_delta: ModelState) -> ModelState:
        """Apply outer momentum to weighted deltas."""
        if not self._velocity:
            self._velocity = {
                name: torch.zeros_like(delta)
                for name, delta in weighted_delta.items()
            }

        next_delta: ModelState = {}
        for name, delta in weighted_delta.items():
            velocity = self._velocity[name] * self.outer_momentum + delta
            self._velocity[name] = velocity
            next_delta[name] = velocity
        return next_delta
