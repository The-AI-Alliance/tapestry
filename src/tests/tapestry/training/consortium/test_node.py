"""Unit and property-based tests for SovereignTrainingNode."""

import copy

import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from tapestry.training.consortium import SovereignTrainingNode, TinyCausalModel
from tests.test_utils.hypothesis.model_strategies import tiny_causal_models

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

_VOCAB = 64
_HIDDEN = 8


def _model() -> TinyCausalModel:
    return TinyCausalModel(vocab_size=_VOCAB, hidden_size=_HIDDEN)


def _corpus(offset: int = 0) -> list[list[int]]:
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]


def _node(
    node_id: str = "test-node",
    jurisdiction: str = "TestLand",
    quality_score: float = 0.8,
    corpus_offset: int = 0,
    local_epochs: int = 1,
    lr: float = 0.01,
) -> SovereignTrainingNode:
    return SovereignTrainingNode(
        node_id=node_id,
        jurisdiction=jurisdiction,
        model=_model(),
        sovereign_corpus=_corpus(corpus_offset),
        quality_score=quality_score,
        local_epochs=local_epochs,
        lr=lr,
    )


def _base_state(model: TinyCausalModel | None = None) -> dict:
    m = model or _model()
    return {k: v.clone() for k, v in m.state_dict().items()}


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


def test_constructor_stores_attributes():
    """All constructor arguments are stored on the node."""
    node = _node(node_id="au-node", jurisdiction="Australia", quality_score=0.75)
    assert node.node_id == "au-node"
    assert node.jurisdiction == "Australia"
    assert node.quality_score == pytest.approx(0.75)
    assert node.local_epochs == 1
    assert node.lr == pytest.approx(0.01)


def test_constructor_deep_copies_model():
    """The stored model is independent of the original; mutations do not bleed through."""
    original = _model()
    node = SovereignTrainingNode(
        node_id="x",
        jurisdiction="X",
        model=original,
        sovereign_corpus=_corpus(),
        quality_score=0.5,
    )
    with torch.no_grad():
        for param in original.parameters():
            param.fill_(999.0)

    for tensor in node.model.state_dict().values():
        assert tensor.max().item() != pytest.approx(999.0)


def test_constructor_latest_artifact_is_none_before_cycle():
    """latest_artifact is None until run_sovereign_cycle is called."""
    assert _node().latest_artifact is None


def test_empty_corpus_raises():
    """An empty sovereign corpus raises ValueError at construction time."""
    with pytest.raises(ValueError, match="sovereign_corpus must contain at least one"):
        SovereignTrainingNode(
            node_id="n",
            jurisdiction="X",
            model=_model(),
            sovereign_corpus=[],
            quality_score=0.5,
        )


def test_single_token_sequence_raises():
    """A corpus of one-token sequences raises ValueError (no next-token target possible)."""
    with pytest.raises(ValueError, match="at least 2 tokens"):
        SovereignTrainingNode(
            node_id="n",
            jurisdiction="X",
            model=_model(),
            sovereign_corpus=[[1]],
            quality_score=0.5,
        )


# ---------------------------------------------------------------------------
# SovereignCycleResult structure
# ---------------------------------------------------------------------------


def test_cycle_result_contains_artifact_and_contribution():
    """run_sovereign_cycle returns a SovereignCycleResult with both sub-objects."""
    torch.manual_seed(0)
    node = _node()
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state())

    assert result.artifact is not None
    assert result.contribution is not None


def test_artifact_fields_match_node_metadata():
    """The artifact carries the node's id, jurisdiction, and stage tag."""
    torch.manual_seed(0)
    node = _node(node_id="br-node", jurisdiction="Brazil")
    result = node.run_sovereign_cycle(round_num=3, base_state=_base_state())

    assert result.artifact.node_id == "br-node"
    assert result.artifact.jurisdiction == "Brazil"
    assert result.artifact.stage == "continued_pretraining"


def test_contribution_fields_match_node_metadata():
    """The contribution carries the node's id, round number, and quality score."""
    torch.manual_seed(0)
    node = _node(node_id="jp-node", quality_score=0.91)
    result = node.run_sovereign_cycle(round_num=7, base_state=_base_state())

    assert result.contribution.node_id == "jp-node"
    assert result.contribution.round_num == 7
    assert result.contribution.quality_score == pytest.approx(0.91)


def test_contribution_model_state_keys_match_base_state():
    """The contribution's local_model_state has the same parameter names as the base."""
    torch.manual_seed(0)
    node = _node()
    base = _base_state()
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert set(result.contribution.local_model_state) == set(base)


def test_artifact_model_state_keys_match_base_state():
    """The artifact's model_state has the same parameter names as the base."""
    torch.manual_seed(0)
    node = _node()
    base = _base_state()
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert set(result.artifact.model_state) == set(base)


def test_artifact_and_contribution_share_same_state():
    """artifact.model_state and contribution.local_model_state are equal tensor-by-tensor."""
    torch.manual_seed(0)
    node = _node()
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state())

    for name in result.artifact.model_state:
        assert torch.equal(
            result.artifact.model_state[name],
            result.contribution.local_model_state[name],
        )


def test_artifact_metrics_contains_loss():
    """metrics on the artifact includes a 'loss' key after training."""
    torch.manual_seed(0)
    result = _node().run_sovereign_cycle(round_num=1, base_state=_base_state())
    assert "loss" in result.artifact.metrics


def test_contribution_metrics_contains_loss():
    """metrics on the contribution includes a 'loss' key after training."""
    torch.manual_seed(0)
    result = _node().run_sovereign_cycle(round_num=1, base_state=_base_state())
    assert "loss" in result.contribution.metrics


def test_contribution_token_count_is_positive():
    """token_count must be > 0 for any valid corpus."""
    torch.manual_seed(0)
    result = _node().run_sovereign_cycle(round_num=1, base_state=_base_state())
    assert result.contribution.token_count > 0


# ---------------------------------------------------------------------------
# Training actually modifies weights
# ---------------------------------------------------------------------------


def test_local_training_changes_weights_from_base():
    """After run_sovereign_cycle, at least one parameter differs from the starting base."""
    torch.manual_seed(0)
    node = _node(local_epochs=2)
    base = _base_state()
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert any(
        not torch.equal(result.contribution.local_model_state[name], base[name])
        for name in base
    )


def test_base_state_not_mutated_by_cycle():
    """run_sovereign_cycle must not modify the caller's base_state dict in-place."""
    torch.manual_seed(0)
    node = _node()
    base = _base_state()
    original_values = {k: v.clone() for k, v in base.items()}

    node.run_sovereign_cycle(round_num=1, base_state=base)

    for name in base:
        assert torch.equal(base[name], original_values[name])


# ---------------------------------------------------------------------------
# latest_artifact updated after cycle
# ---------------------------------------------------------------------------


def test_latest_artifact_is_set_after_cycle():
    """latest_artifact holds the most recent artifact after the first cycle."""
    torch.manual_seed(0)
    node = _node()
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state())
    assert node.latest_artifact is result.artifact


def test_latest_artifact_is_replaced_on_second_cycle():
    """A second cycle replaces latest_artifact with the new one."""
    torch.manual_seed(0)
    node = _node()
    base = _base_state()

    result1 = node.run_sovereign_cycle(round_num=1, base_state=base)
    result2 = node.run_sovereign_cycle(round_num=2, base_state=base)

    assert node.latest_artifact is result2.artifact
    assert node.latest_artifact is not result1.artifact


# ---------------------------------------------------------------------------
# round_num is propagated correctly
# ---------------------------------------------------------------------------


@given(st.integers(min_value=1, max_value=100))
@settings(deadline=None)
def test_round_num_propagated_to_contribution(round_num):
    """Whatever round_num is passed, the contribution records it exactly."""
    torch.manual_seed(0)
    node = _node()
    result = node.run_sovereign_cycle(round_num=round_num, base_state=_base_state())
    assert result.contribution.round_num == round_num


# ---------------------------------------------------------------------------
# Property: structural invariants across model sizes and corpora
# ---------------------------------------------------------------------------


@given(
    tiny_causal_models(min_vocab_size=64, max_vocab_size=128, min_hidden_size=2, max_hidden_size=4),
    st.integers(min_value=1, max_value=4),
)
@settings(deadline=None)
def test_cycle_result_structure_invariants_across_model_sizes(model, local_epochs):
    """Structural invariants hold regardless of model size or number of local epochs."""
    torch.manual_seed(0)
    node = SovereignTrainingNode(
        node_id="prop-node",
        jurisdiction="Prop",
        model=copy.deepcopy(model),
        sovereign_corpus=_corpus(),
        quality_score=0.85,
        local_epochs=local_epochs,
        lr=0.01,
    )
    base = {k: v.clone() for k, v in model.state_dict().items()}
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    # Identity fields
    assert result.artifact.node_id == "prop-node"
    assert result.contribution.node_id == "prop-node"
    assert result.contribution.round_num == 1

    # State-dict keys are consistent
    assert set(result.artifact.model_state) == set(base)
    assert set(result.contribution.local_model_state) == set(base)

    # Artifact and contribution share the same tensors
    for name in base:
        assert torch.equal(
            result.artifact.model_state[name],
            result.contribution.local_model_state[name],
        )

    # Metrics and token count are present and valid
    assert "loss" in result.artifact.metrics
    assert result.contribution.token_count > 0
