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


def test_sovereign_node_returns_artifact_and_weight_delta() -> None:
    """A node keeps a sovereign model artifact and shares only a delta."""
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
    assert set(result.contribution.weight_delta) == set(base_state)
    assert any(torch.norm(delta).item() > 0 for delta in result.contribution.weight_delta.values())


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
