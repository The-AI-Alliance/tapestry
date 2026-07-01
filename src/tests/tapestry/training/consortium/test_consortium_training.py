"""Tests for the consortium-training proof of concept."""

# pylint: disable=wrong-import-position

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    ContributionWeighting,
    OuterMergeOptimizer,
    OuterMergeStrategy,
    SovereignTrainingNode,
    TinyCausalModel,
)


def _model() -> nn.Module:
    return TinyCausalModel(vocab_size=64, hidden_size=16)


def _corpus(offset: int = 0) -> list[list[int]]:
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]


def test_sovereign_node_returns_artifact_and_local_model_state() -> None:
    """A node keeps a sovereign model artifact and shares its local weight vector."""
    torch.manual_seed(0)
    node = SovereignTrainingNode(
        node_id="vn-node",
        jurisdiction="Vietnam",
        model=_model(),
        sovereign_corpus=_corpus(),
        quality_score=0.82,
        local_epochs=1,
        lr=0.01,
    )
    base_state = {k: v.clone() for k, v in _model().state_dict().items()}

    result = node.run_sovereign_cycle(round_num=1, base_state=base_state)

    assert result.artifact.node_id == "vn-node"
    assert result.artifact.stage == "continued_pretraining"
    assert result.artifact.model_state
    assert result.contribution.node_id == "vn-node"
    assert result.contribution.round_num == 1
    assert result.contribution.quality_score == pytest.approx(0.82)
    assert set(result.contribution.local_model_state) == set(base_state)
    assert any(not torch.equal(result.contribution.local_model_state[name], base_state[name]) for name in base_state)


def test_contribution_policy_applies_quality_floor_and_capture_cap() -> None:
    """Governed weighting drops weak updates and caps dominant nodes."""
    policy = ContributionPolicy(quality_floor=0.7, max_node_weight=0.6)

    weights = policy.weights(
        {
            "strong": 0.95,
            "dominant": 5.0,
            "weak": 0.4,
        }
    )

    assert "weak" not in weights
    assert weights["dominant"] <= 0.6
    assert sum(weights.values()) == pytest.approx(1.0)


def test_equal_contribution_policy_ignores_quality_magnitude_after_floor() -> None:
    """The equal MVP option gives every accepted participant the same influence."""
    policy = ContributionPolicy(quality_floor=0.7, weighting=ContributionWeighting.EQUAL)

    weights = policy.weights(
        {
            "strong": 0.95,
            "dominant": 5.0,
            "weak": 0.4,
        }
    )

    assert "weak" not in weights
    assert weights == {
        "strong": pytest.approx(0.5),
        "dominant": pytest.approx(0.5),
    }


def test_coordinator_maintains_n_plus_one_model_outcome() -> None:
    """One evolved base plus one sovereign artifact per node are retained."""
    torch.manual_seed(1)
    coordinator = ConsortiumCoordinator(
        base_model=_model(),
        contribution_policy=ContributionPolicy(quality_floor=0.1),
    )
    nodes = [
        SovereignTrainingNode(
            node_id="vietnam",
            jurisdiction="Vietnam",
            model=_model(),
            sovereign_corpus=_corpus(0),
            quality_score=0.9,
            local_epochs=1,
            lr=0.01,
        ),
        SovereignTrainingNode(
            node_id="swiss",
            jurisdiction="Switzerland",
            model=_model(),
            sovereign_corpus=_corpus(10),
            quality_score=0.8,
            local_epochs=1,
            lr=0.01,
        ),
    ]

    result = coordinator.run_round(nodes)

    assert result.round_num == 1
    assert result.outer_merge_strategy == OuterMergeStrategy.WEIGHTED_AVERAGE.value
    assert set(result.accepted_nodes) == {"vietnam", "swiss"}
    assert len(coordinator.sovereign_artifacts) == 2
    assert set(coordinator.sovereign_artifacts) == {"vietnam", "swiss"}
    assert coordinator.shared_base_state
    assert any(
        not torch.equal(
            result.previous_base_state[name],
            result.shared_base_state[name],
        )
        for name in result.shared_base_state
    )


def test_weighting_modes_produce_different_integration_results() -> None:
    """The current experiment setup can compare quality-weighted and equal influence policies."""
    local_states = {
        "strong": {"weight": torch.tensor([2.0])},
        "dominant": {"weight": torch.tensor([10.0])},
    }
    quality_weights = ContributionPolicy(weighting="quality").weights(
        {
            "strong": 1.0,
            "dominant": 3.0,
        }
    )
    equal_weights = ContributionPolicy(weighting=ContributionWeighting.EQUAL).weights(
        {
            "strong": 1.0,
            "dominant": 3.0,
        }
    )

    previous_state = {"weight": torch.tensor([0.0])}
    merge = OuterMergeOptimizer()
    quality_state = merge.merge(previous_state, local_states, quality_weights)
    equal_state = merge.merge(previous_state, local_states, equal_weights)

    assert quality_weights["dominant"] > equal_weights["dominant"]
    assert quality_state["weight"].item() == pytest.approx(8.0)
    assert equal_state["weight"].item() == pytest.approx(6.0)


def test_delta_outer_merge_applies_scaled_weighted_delta() -> None:
    """Delta merge applies weighted node deltas to the previous base."""
    previous_state = {"weight": torch.tensor([4.0])}
    local_states = {
        "a": {"weight": torch.tensor([6.0])},
        "b": {"weight": torch.tensor([10.0])},
    }
    merge = OuterMergeOptimizer(strategy=OuterMergeStrategy.DELTA, outer_lr=0.5)

    merged = merge.merge(previous_state, local_states, {"a": 0.25, "b": 0.75})

    # Weighted delta is 0.25 * 2 + 0.75 * 6 = 5.0; outer_lr applies half.
    assert merged["weight"].item() == pytest.approx(6.5)


def test_momentum_delta_outer_merge_accumulates_outer_velocity() -> None:
    """Momentum merge carries an outer optimizer buffer across rounds."""
    previous_state = {"weight": torch.tensor([0.0])}
    local_states = {"a": {"weight": torch.tensor([1.0])}}
    merge = OuterMergeOptimizer(
        strategy=OuterMergeStrategy.MOMENTUM_DELTA,
        outer_lr=1.0,
        outer_momentum=0.5,
    )

    first = merge.merge(previous_state, local_states, {"a": 1.0})
    second = merge.merge(first, {"a": {"weight": torch.tensor([2.0])}}, {"a": 1.0})

    assert first["weight"].item() == pytest.approx(1.0)
    assert second["weight"].item() == pytest.approx(2.5)


def test_low_quality_contribution_does_not_update_shared_base() -> None:
    """A round with no accepted contributions leaves the shared base unchanged."""
    torch.manual_seed(2)
    coordinator = ConsortiumCoordinator(
        base_model=_model(),
        contribution_policy=ContributionPolicy(quality_floor=0.95),
    )
    weak_node = SovereignTrainingNode(
        node_id="weak",
        jurisdiction="Test",
        model=_model(),
        sovereign_corpus=_corpus(),
        quality_score=0.5,
        local_epochs=1,
        lr=0.01,
    )

    result = coordinator.run_round([weak_node])

    assert not result.accepted_nodes
    assert result.rejected_nodes == ["weak"]
    assert all(
        torch.equal(
            result.previous_base_state[name],
            result.shared_base_state[name],
        )
        for name in result.shared_base_state
    )
