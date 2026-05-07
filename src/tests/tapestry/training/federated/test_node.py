"""Tests for the federated training node."""

from __future__ import annotations

import torch

from tapestry.training.federated.node import MiniTransformer, TrainingNode
from tapestry.training.federated.privacy import DifferentialPrivacy


def _sample_data() -> list[list[int]]:
    """Generate a small set of byte-encoded training samples."""
    texts = [
        "hello world",
        "federated learning",
        "privacy preserving",
        "data sovereignty",
    ]
    return [list(t.encode("utf-8")) for t in texts]


class TestMiniTransformer:
    """Smoke tests for the transformer model."""

    def test_forward_shape(self) -> None:
        """Output logits have the correct shape."""
        model = MiniTransformer(vocab_size=128, d_model=32, n_heads=2, n_layers=1)
        x = torch.randint(0, 128, (2, 10))
        logits = model(x)
        assert logits.shape == (2, 10, 128)

    def test_different_sequence_lengths(self) -> None:
        """Model handles varying sequence lengths."""
        model = MiniTransformer(vocab_size=128, d_model=32, n_heads=2, n_layers=1)
        for seq_len in [1, 5, 20]:
            x = torch.randint(0, 128, (1, seq_len))
            logits = model(x)
            assert logits.shape == (1, seq_len, 128)


class TestTrainingNode:
    """Tests for local training and update generation."""

    def _make_node(self, with_dp: bool = False) -> TrainingNode:
        model = MiniTransformer(vocab_size=256, d_model=32, n_heads=2, n_layers=1)
        dp = DifferentialPrivacy(max_grad_norm=1.0, noise_multiplier=0.1) if with_dp else None
        return TrainingNode(
            node_id="test-node",
            model=model,
            train_data=_sample_data(),
            dp=dp,
            lr=1e-3,
            local_epochs=1,
            batch_size=4,
        )

    def test_train_local_returns_update(self) -> None:
        """train_local produces a NodeUpdate with correct metadata."""
        node = self._make_node()
        update = node.train_local(round_num=1)

        assert update.node_id == "test-node"
        assert update.round_num == 1
        assert update.num_samples > 0
        assert "loss" in update.metadata
        assert update.metadata["loss"] > 0

    def test_state_delta_has_all_keys(self) -> None:
        """The update contains deltas for every model parameter."""
        node = self._make_node()
        update = node.train_local(round_num=1)
        model_keys = set(node.model.state_dict().keys())
        assert set(update.state_delta.keys()) == model_keys

    def test_state_delta_is_nonzero(self) -> None:
        """At least some parameters should change after training."""
        node = self._make_node()
        update = node.train_local(round_num=1)
        norms = [torch.norm(v).item() for v in update.state_delta.values()]
        assert any(n > 0 for n in norms)

    def test_dp_node_returns_update(self) -> None:
        """Node with differential privacy still produces valid updates."""
        node = self._make_node(with_dp=True)
        update = node.train_local(round_num=1)

        assert update.node_id == "test-node"
        assert len(update.state_delta) > 0

    def test_receive_global_model(self) -> None:
        """Receiving a global model replaces local weights."""
        node = self._make_node()
        # Create a fake global state (all zeros).
        zero_state = {k: torch.zeros_like(v) for k, v in node.model.state_dict().items()}
        node.receive_global_model(zero_state)

        for v in node.model.state_dict().values():
            assert torch.all(v == 0)

    def test_loss_decreases_over_rounds(self) -> None:
        """Local loss should generally decrease across multiple rounds."""
        node = self._make_node()
        losses = []
        for rnd in range(1, 6):
            update = node.train_local(round_num=rnd)
            losses.append(update.metadata["loss"])

        # Final loss should be lower than initial loss.
        assert losses[-1] < losses[0]
