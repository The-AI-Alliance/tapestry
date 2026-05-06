"""Tests for the differential privacy module."""

from __future__ import annotations

import pytest
import torch

from tapestry.training.federated.privacy import DifferentialPrivacy


class TestDifferentialPrivacy:
    """Tests for gradient clipping and noise injection."""

    def _make_delta(self, scale: float = 1.0) -> dict[str, torch.Tensor]:
        """Create a simple state delta for testing."""
        return {
            "weight": torch.randn(4, 4) * scale,
            "bias": torch.randn(4) * scale,
        }

    def test_clipping_reduces_large_updates(self) -> None:
        """Updates larger than max_grad_norm are clipped down."""
        dp = DifferentialPrivacy(max_grad_norm=0.01, noise_multiplier=0.0)
        delta = self._make_delta(scale=100.0)

        result = dp.apply(delta)

        total_norm = torch.sqrt(
            sum(torch.sum(t ** 2) for t in result.values())
        ).item()
        assert total_norm <= 0.01 + 1e-6

    def test_small_updates_pass_through(self) -> None:
        """Updates already within the clipping bound are not altered (no noise case)."""
        dp = DifferentialPrivacy(max_grad_norm=1e6, noise_multiplier=0.0)
        delta = self._make_delta(scale=0.001)

        result = dp.apply(delta)

        for name in delta:
            assert torch.allclose(result[name], delta[name], atol=1e-6)

    def test_noise_injection_changes_values(self) -> None:
        """With nonzero noise_multiplier, output differs from clipped input."""
        dp = DifferentialPrivacy(max_grad_norm=10.0, noise_multiplier=1.0)
        delta = self._make_delta(scale=0.1)

        result = dp.apply(delta)

        # At least one tensor should differ (overwhelmingly likely).
        any_different = any(
            not torch.allclose(result[k], delta[k], atol=1e-6) for k in delta
        )
        assert any_different

    def test_budget_tracking(self) -> None:
        """Privacy budget epsilon increases with each round."""
        dp = DifferentialPrivacy(max_grad_norm=1.0, noise_multiplier=0.5)

        dp.apply(self._make_delta())
        eps_1 = dp.current_epsilon
        assert eps_1 > 0

        dp.apply(self._make_delta())
        eps_2 = dp.current_epsilon
        assert eps_2 > eps_1

        assert dp.budget.rounds_consumed == 2

    def test_invalid_max_grad_norm(self) -> None:
        """Negative or zero clipping bounds are rejected."""
        with pytest.raises(ValueError, match="max_grad_norm"):
            DifferentialPrivacy(max_grad_norm=0.0)
        with pytest.raises(ValueError, match="max_grad_norm"):
            DifferentialPrivacy(max_grad_norm=-1.0)

    def test_invalid_noise_multiplier(self) -> None:
        """Negative noise multiplier is rejected."""
        with pytest.raises(ValueError, match="noise_multiplier"):
            DifferentialPrivacy(noise_multiplier=-0.5)

    def test_deterministic_without_noise(self) -> None:
        """With noise_multiplier=0, output is deterministic (clip only)."""
        dp = DifferentialPrivacy(max_grad_norm=1.0, noise_multiplier=0.0)
        delta = self._make_delta(scale=5.0)

        result_a = dp.apply(delta)
        # Reset budget so we can apply again cleanly.
        dp2 = DifferentialPrivacy(max_grad_norm=1.0, noise_multiplier=0.0)
        result_b = dp2.apply(delta)

        for name in delta:
            assert torch.allclose(result_a[name], result_b[name])
