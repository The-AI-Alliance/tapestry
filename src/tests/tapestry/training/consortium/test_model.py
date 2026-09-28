"""Unit and property-based tests for TinyCausalModel."""

import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from tapestry.training.consortium import TinyCausalModel
from tests.test_utils.hypothesis.model_strategies import tiny_causal_models


# ---------------------------------------------------------------------------
# Constructor / structural tests
# ---------------------------------------------------------------------------


def test_default_construction():
    """Default vocab_size and hidden_size produce a model with the expected layers."""
    model = TinyCausalModel()
    assert model.embedding.num_embeddings == 256
    assert model.embedding.embedding_dim == 32
    assert model.proj.in_features == 32
    assert model.proj.out_features == 256


@given(
    st.integers(min_value=1, max_value=512),
    st.integers(min_value=1, max_value=64),
)
def test_construction_wires_layers_to_vocab_and_hidden_size(vocab_size, hidden_size):
    """Embedding and projection dimensions always match the constructor arguments."""
    model = TinyCausalModel(vocab_size=vocab_size, hidden_size=hidden_size)
    assert model.embedding.num_embeddings == vocab_size
    assert model.embedding.embedding_dim == hidden_size
    assert model.proj.in_features == hidden_size
    assert model.proj.out_features == vocab_size


# ---------------------------------------------------------------------------
# Forward-pass shape tests
# ---------------------------------------------------------------------------


@given(tiny_causal_models())
def test_forward_output_shape_matches_vocab_size(model):
    """Output last-dimension equals vocab_size for any (batch, seq) input."""
    batch, seq = 2, 5
    ids = torch.randint(0, model.embedding.num_embeddings, (batch, seq))
    logits = model(ids)
    assert logits.shape == (batch, seq, model.embedding.num_embeddings)


@given(
    tiny_causal_models(),
    st.integers(min_value=1, max_value=8),
    st.integers(min_value=1, max_value=16),
)
@settings(deadline=None)
def test_forward_output_shape_varies_with_batch_and_seq(model, batch, seq):
    """Output shape tracks (batch, seq, vocab_size) across all sizes."""
    ids = torch.randint(0, model.embedding.num_embeddings, (batch, seq))
    logits = model(ids)
    assert logits.shape == (batch, seq, model.embedding.num_embeddings)


def test_forward_single_token():
    """A single-token sequence produces a (1, 1, vocab_size) output."""
    model = TinyCausalModel(vocab_size=16, hidden_size=4)
    ids = torch.tensor([[0]])
    logits = model(ids)
    assert logits.shape == (1, 1, 16)


# ---------------------------------------------------------------------------
# Output dtype / device tests
# ---------------------------------------------------------------------------


@given(tiny_causal_models())
def test_output_is_float32(model):
    """Logits are always float32 (the default torch dtype)."""
    ids = torch.randint(0, model.embedding.num_embeddings, (1, 4))
    logits = model(ids)
    assert logits.dtype == torch.float32


# ---------------------------------------------------------------------------
# Determinism test
# ---------------------------------------------------------------------------


def test_forward_is_deterministic():
    """The same input always produces the same logits (no stochastic layers)."""
    model = TinyCausalModel(vocab_size=32, hidden_size=8)
    model.eval()
    ids = torch.tensor([[1, 2, 3]])
    first = model(ids)
    second = model(ids)
    assert torch.equal(first, second)


# ---------------------------------------------------------------------------
# State-dict round-trip test
# ---------------------------------------------------------------------------


@given(tiny_causal_models())
def test_state_dict_round_trip_preserves_weights(model):
    """Loading a saved state dict restores identical parameters."""
    ids = torch.randint(0, model.embedding.num_embeddings, (1, 4))
    original_logits = model(ids)

    state = {k: v.clone() for k, v in model.state_dict().items()}
    restored = TinyCausalModel(
        vocab_size=model.embedding.num_embeddings,
        hidden_size=model.embedding.embedding_dim,
    )
    restored.load_state_dict(state)

    assert torch.equal(restored(ids), original_logits)


# ---------------------------------------------------------------------------
# Token-boundary tests
# ---------------------------------------------------------------------------


def test_forward_accepts_token_id_zero():
    """Token id 0 (a valid embedding index) does not raise."""
    model = TinyCausalModel(vocab_size=16, hidden_size=4)
    ids = torch.zeros(1, 3, dtype=torch.long)
    logits = model(ids)
    assert logits.shape == (1, 3, 16)


def test_forward_accepts_max_token_id():
    """Token id vocab_size-1 (the last valid index) does not raise."""
    vocab_size = 16
    model = TinyCausalModel(vocab_size=vocab_size, hidden_size=4)
    ids = torch.full((1, 3), vocab_size - 1, dtype=torch.long)
    logits = model(ids)
    assert logits.shape == (1, 3, vocab_size)


def test_forward_rejects_out_of_range_token_id():
    """A token id equal to vocab_size raises an IndexError from the embedding layer."""
    vocab_size = 16
    model = TinyCausalModel(vocab_size=vocab_size, hidden_size=4)
    ids = torch.full((1, 1), vocab_size, dtype=torch.long)
    with pytest.raises(IndexError):
        model(ids)
