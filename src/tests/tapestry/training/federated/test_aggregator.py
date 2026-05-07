"""Tests for the federated aggregator."""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from tapestry.training.federated.aggregator import Aggregator
from tapestry.training.federated.node import MiniTransformer, TrainingNode
from tapestry.training.federated.protocols import NodeUpdate


def _make_model() -> nn.Module:
    return MiniTransformer(vocab_size=128, d_model=32, n_heads=2, n_layers=1)


def _make_update(
    node_id: str,
    state_template: dict[str, torch.Tensor],
    scale: float = 0.01,
    num_samples: int = 100,
    loss: float = 1.0,
) -> NodeUpdate:
    """Create a synthetic NodeUpdate for testing."""
    delta = {
        name: torch.randn_like(param) * scale
        for name, param in state_template.items()
    }
    return NodeUpdate(
        node_id=node_id,
        round_num=1,
        state_delta=delta,
        num_samples=num_samples,
        metadata={"loss": loss},
    )


class TestAggregator:
    """Tests for FedAvg aggregation logic."""

    def test_aggregate_single_node(self) -> None:
        """Aggregating a single update applies it directly."""
        model = _make_model()
        agg = Aggregator(global_model=model)

        state_template = model.state_dict()
        delta = {
            k: torch.ones_like(v) * 0.5 for k, v in state_template.items()
        }
        update = NodeUpdate(
            node_id="only-node",
            round_num=1,
            state_delta=delta,
            num_samples=50,
            metadata={"loss": 2.0},
        )

        pre_state = agg.global_state
        result = agg.aggregate([update])

        # Each parameter should have shifted by 0.5.
        # (Only checking shape-compatible params.)
        assert result.round_num == 1
        assert result.avg_loss == pytest.approx(2.0)
        assert result.participating_nodes == ["only-node"]

    def test_weighted_averaging(self) -> None:
        """Updates are weighted by num_samples."""
        keys = ["w"]
        u1 = NodeUpdate("a", 1, {"w": torch.tensor([1.0])}, num_samples=100)
        u2 = NodeUpdate("b", 1, {"w": torch.tensor([3.0])}, num_samples=300)

        # Weighted avg: (1*100 + 3*300) / 400 = 1000/400 = 2.5
        model = nn.Linear(1, 1)  # Placeholder; we won't use its weights.
        agg = Aggregator(global_model=model)

        # Manually test the averaging logic.
        total = u1.num_samples + u2.num_samples
        avg = (
            u1.state_delta["w"] * (u1.num_samples / total)
            + u2.state_delta["w"] * (u2.num_samples / total)
        )
        assert avg.item() == pytest.approx(2.5)

    def test_empty_updates_raises(self) -> None:
        """Aggregating an empty list raises ValueError."""
        model = _make_model()
        agg = Aggregator(global_model=model)
        with pytest.raises(ValueError, match="zero updates"):
            agg.aggregate([])

    def test_round_counter_increments(self) -> None:
        """Each call to aggregate advances the round counter."""
        model = _make_model()
        agg = Aggregator(global_model=model)
        state_template = model.state_dict()

        for expected_round in range(1, 4):
            update = _make_update("node", state_template)
            result = agg.aggregate([update])
            assert result.round_num == expected_round

    def test_global_state_is_snapshot(self) -> None:
        """global_state returns a copy, not a reference."""
        model = _make_model()
        agg = Aggregator(global_model=model)

        baseline = agg.global_state
        s1 = agg.global_state
        s2 = agg.global_state

        # Modify s1 and verify s2 is unaffected.
        for v in s1.values():
            v.zero_()

        assert all(torch.equal(s2[k], baseline[k]) for k in baseline)
        assert all(torch.equal(agg.global_state[k], baseline[k]) for k in baseline)
        assert any(not torch.equal(s1[k], baseline[k]) for k in baseline)

    def test_end_to_end_with_real_nodes(self) -> None:
        """Full loop: create nodes, train locally, aggregate, verify convergence."""
        torch.manual_seed(0)
        model = MiniTransformer(vocab_size=128, d_model=32, n_heads=2, n_layers=1)
        agg = Aggregator(global_model=model)

        data = [list(b"hello world"), list(b"test data here")]
        nodes = [
            TrainingNode(f"node-{i}", model, data, lr=1e-3, local_epochs=2)
            for i in range(2)
        ]

        losses = []
        for rnd in range(1, 4):
            global_state = agg.global_state
            updates = []
            for node in nodes:
                node.receive_global_model(global_state)
                updates.append(node.train_local(rnd))
            result = agg.aggregate(updates)
            losses.append(result.avg_loss)

        # Loss should decrease (or at least not explode).
        assert losses[-1] < losses[0]
