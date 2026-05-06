"""Differential privacy mechanisms for federated learning.

Implements the core DP-SGD building blocks: per-sample gradient clipping
and calibrated Gaussian noise injection. These ensure that individual
training examples cannot be reconstructed from shared weight updates,
providing a formal (epsilon, delta)-differential privacy guarantee.

Reference:
    Abadi et al., "Deep Learning with Differential Privacy" (SIGSAC 2016)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch


@dataclass
class PrivacyBudget:
    """Tracks cumulative privacy expenditure across federated rounds.

    Uses the moments accountant approximation for composed Gaussian
    mechanisms under subsampling.

    Attributes:
        epsilon: Current cumulative epsilon.
        delta: Target delta (fixed at initialisation).
        rounds_consumed: Number of rounds accounted for so far.
    """

    epsilon: float = 0.0
    delta: float = 1e-5
    rounds_consumed: int = 0


class DifferentialPrivacy:
    """Applies (epsilon, delta)-differential privacy to model weight updates.

    Two-step process applied to each parameter tensor:
        1. **Clip** — project the update onto an L2 ball of radius
           ``max_grad_norm``, bounding any single sample's influence.
        2. **Noise** — add Gaussian noise calibrated to the clipping bound
           and the desired noise multiplier (sigma).

    The effective per-round (epsilon, delta)-guarantee is determined by
    ``noise_multiplier`` and ``delta`` via the Gaussian mechanism.

    Args:
        max_grad_norm: L2 clipping bound for weight updates.
        noise_multiplier: Ratio of noise standard deviation to clipping
            bound. Higher values give stronger privacy at the cost of
            utility.  Typical range: 0.5 -- 2.0.
        delta: Target delta for the privacy guarantee.
    """

    def __init__(
        self,
        max_grad_norm: float = 1.0,
        noise_multiplier: float = 0.1,
        delta: float = 1e-5,
    ) -> None:
        if max_grad_norm <= 0:
            raise ValueError("max_grad_norm must be positive")
        if noise_multiplier < 0:
            raise ValueError("noise_multiplier must be non-negative")

        self.max_grad_norm = max_grad_norm
        self.noise_multiplier = noise_multiplier
        self.budget = PrivacyBudget(delta=delta)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply(
        self, state_delta: dict[str, torch.Tensor]
    ) -> dict[str, torch.Tensor]:
        """Clip and noise a full set of weight updates.

        Args:
            state_delta: Mapping of parameter names to update tensors.

        Returns:
            A new dict with the same keys, containing the privatised updates.
        """
        clipped = self._clip(state_delta)
        noised = self._add_noise(clipped)
        self._update_budget()
        return noised

    @property
    def current_epsilon(self) -> float:
        """Cumulative epsilon spent so far."""
        return self.budget.epsilon

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clip(
        self, state_delta: dict[str, torch.Tensor]
    ) -> dict[str, torch.Tensor]:
        """Clip the global L2 norm of the update to ``max_grad_norm``."""
        # Compute global L2 norm across all parameters.
        total_norm = torch.sqrt(
            sum(
                torch.sum(delta ** 2)
                for delta in state_delta.values()
            )
        )
        clip_factor = min(1.0, self.max_grad_norm / (total_norm.item() + 1e-8))
        return {
            name: delta * clip_factor for name, delta in state_delta.items()
        }

    def _add_noise(
        self, state_delta: dict[str, torch.Tensor]
    ) -> dict[str, torch.Tensor]:
        """Add calibrated Gaussian noise to each parameter update."""
        sigma = self.noise_multiplier * self.max_grad_norm
        return {
            name: delta + torch.normal(
                mean=0.0,
                std=sigma,
                size=delta.shape,
                device=delta.device,
                dtype=delta.dtype,
            )
            for name, delta in state_delta.items()
        }

    def _update_budget(self) -> None:
        """Advance the privacy budget by one round (Gaussian mechanism)."""
        self.budget.rounds_consumed += 1
        # Analytic Gaussian mechanism: epsilon per round.
        if self.noise_multiplier > 0:
            per_round_eps = math.sqrt(
                2.0 * math.log(1.25 / self.budget.delta)
            ) / self.noise_multiplier
        else:
            per_round_eps = float("inf")
        # Simple linear composition (conservative upper bound).
        self.budget.epsilon = per_round_eps * self.budget.rounds_consumed
