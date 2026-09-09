"""Metrics helpers for consortium-training PoC experiments."""

from __future__ import annotations

from math import sqrt

import torch

from tapestry.training.consortium.messages import ModelState


def state_delta_norm(before: ModelState, after: ModelState) -> float:
    """Return the L2 norm of the difference between two model states."""
    if set(before) != set(after):
        missing_before = sorted(set(after) - set(before))
        missing_after = sorted(set(before) - set(after))
        raise ValueError(
            "model states must contain the same keys; "
            f"missing_before={missing_before}, missing_after={missing_after}"
        )

    squared_norm = torch.tensor(0.0)
    for name, before_tensor in before.items():
        delta = after[name] - before_tensor
        squared_norm = squared_norm + torch.sum(delta * delta)
    return sqrt(float(squared_norm.item()))


def max_weight(weights: dict[str, float]) -> float:
    """Return the maximum contribution weight, or 0.0 when no nodes are accepted."""
    return max(weights.values(), default=0.0)
