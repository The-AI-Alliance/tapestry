"""Unit and property-based tests for SovereignTrainingNode."""

import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from tapestry.training.consortium import SovereignTrainingNode, TinyCausalModel
from tests.test_utils.hypothesis.model_strategies import (
    a_sovereign_corpus,
    a_tiny_causal_model,
    empty_sovereign_corpuses,
    one_element_sovereign_corpuses,
    one_tiny_causal_model,
    sovereign_training_nodes,
    tiny_causal_models,
)

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _node(
    node_id: str = "test-node",
    jurisdiction: str = "TestLand",
    quality_score: float = 0.8,
    sovereign_corpus: list[list[int]] = a_sovereign_corpus,
    local_epochs: int = 1,
    lr: float = 0.01,
    model: TinyCausalModel = a_tiny_causal_model,
) -> SovereignTrainingNode:
    return SovereignTrainingNode(
        node_id=node_id,
        jurisdiction=jurisdiction,
        model=model,
        sovereign_corpus=sovereign_corpus,
        quality_score=quality_score,
        local_epochs=local_epochs,
        lr=lr,
    )


def _base_state(model: TinyCausalModel) -> dict:
    return {k: v.clone() for k, v in model.state_dict().items()}


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


@given(tiny_causal_models())
def test_constructor_deep_copies_model(model):
    """The stored model is independent of the original; mutations do not bleed through."""
    node = _node(model=model)
    with torch.no_grad():
        for param in model.parameters():
            param.fill_(999.0)

    for tensor in node.model.state_dict().values():
        assert tensor.max().item() != pytest.approx(999.0)


@given(sovereign_training_nodes())
def test_constructor_latest_artifact_is_none_before_cycle(node):
    """latest_artifact is None until run_sovereign_cycle is called."""
    assert node.latest_artifact is None


@given(empty_sovereign_corpuses(), one_tiny_causal_model())
def test_empty_corpus_raises(corpus, model):
    """An empty sovereign corpus raises ValueError at construction time."""
    with pytest.raises(ValueError, match="sovereign_corpus must contain at least one"):
        _node(sovereign_corpus=corpus, model=model)


@given(one_element_sovereign_corpuses(), one_tiny_causal_model())
def test_single_token_sequence_raises(corpus, model):
    """A corpus of one-token sequences raises ValueError (no next-token target possible)."""
    with pytest.raises(ValueError, match="at least 2 tokens"):
        _node(sovereign_corpus=corpus, model=model)


# ---------------------------------------------------------------------------
# SovereignCycleResult structure
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes())
@settings(deadline=None)  # For some reason, sometimes this test exceeds the default 300ms for hypothesis.
def test_cycle_result_contains_artifact_and_contribution(node):
    """run_sovereign_cycle returns a SovereignCycleResult with both sub-objects."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state(node.model))

    assert result.artifact is not None
    assert result.contribution is not None


@given(sovereign_training_nodes())
def test_artifact_fields_match_node_metadata(node):
    """The artifact carries the node's id, jurisdiction, and stage tag."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=3, base_state=_base_state(node.model))

    assert result.artifact.node_id == node.node_id
    assert result.artifact.jurisdiction == node.jurisdiction
    assert result.artifact.stage == "continued_pretraining"


@given(sovereign_training_nodes(), st.integers(min_value=1, max_value=10))
def test_contribution_fields_match_node_metadata(node, round_num):
    """The contribution carries the node's id, round number, and quality score."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=round_num, base_state=_base_state(node.model))

    assert result.contribution.node_id == node.node_id
    assert result.contribution.round_num == round_num
    assert result.contribution.quality_score == pytest.approx(node.quality_score)


@given(sovereign_training_nodes())
def test_contribution_model_state_keys_match_base_state(node):
    """The contribution's local_model_state has the same parameter names as the base."""
    torch.manual_seed(0)
    base = _base_state(node.model)
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert set(result.contribution.local_model_state) == set(base)


@given(sovereign_training_nodes())
def test_artifact_model_state_keys_match_base_state(node):
    """The artifact's model_state has the same parameter names as the base."""
    torch.manual_seed(0)
    base = _base_state(node.model)
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert set(result.artifact.model_state) == set(base)


@given(sovereign_training_nodes())
def test_artifact_and_contribution_share_same_state(node):
    """artifact.model_state and contribution.local_model_state are equal tensor-by-tensor."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state(node.model))

    for name in result.artifact.model_state:
        assert torch.equal(
            result.artifact.model_state[name],
            result.contribution.local_model_state[name],
        )


@given(sovereign_training_nodes())
def test_artifact_and_contribution_metrics_contains_loss(node):
    """metrics on the artifact includes a 'loss' key after training."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state(node.model))
    assert "loss" in result.artifact.metrics
    assert "loss" in result.contribution.metrics


@given(sovereign_training_nodes())
def test_contribution_token_count_is_positive(node):
    """token_count must be > 0 for any valid corpus."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state(node.model))
    assert result.contribution.token_count > 0


# ---------------------------------------------------------------------------
# Training actually modifies weights
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes())
def test_local_training_changes_weights_from_base(node):
    """After run_sovereign_cycle, at least one parameter differs from the starting base."""
    torch.manual_seed(0)
    base = _base_state(node.model)
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    assert any(not torch.equal(result.contribution.local_model_state[name], base[name]) for name in base)


@given(sovereign_training_nodes())
def test_base_state_not_mutated_by_cycle(node):
    """run_sovereign_cycle must not modify the caller's base_state dict in-place."""
    torch.manual_seed(0)
    base = _base_state(node.model)
    original_values = _base_state(node.model)

    node.run_sovereign_cycle(round_num=1, base_state=base)

    for name in base:
        assert torch.equal(base[name], original_values[name])


# ---------------------------------------------------------------------------
# latest_artifact updated after cycle
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes())
def test_latest_artifact_is_set_after_cycle(node):
    """latest_artifact holds the most recent artifact after the first cycle."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=1, base_state=_base_state(node.model))
    assert node.latest_artifact is result.artifact


@given(sovereign_training_nodes())
def test_latest_artifact_is_replaced_on_second_cycle(node):
    """A second cycle replaces latest_artifact with the new one."""
    torch.manual_seed(0)
    base = _base_state(node.model)

    result1 = node.run_sovereign_cycle(round_num=1, base_state=base)
    result2 = node.run_sovereign_cycle(round_num=2, base_state=base)

    assert node.latest_artifact is result2.artifact
    assert node.latest_artifact is not result1.artifact


# ---------------------------------------------------------------------------
# round_num is propagated correctly
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes(), st.integers(min_value=1, max_value=10))
# @settings(deadline=None)
def test_round_num_propagated_to_contribution(node, round_num):
    """Whatever round_num is passed, the contribution records it exactly."""
    torch.manual_seed(0)
    result = node.run_sovereign_cycle(round_num=round_num, base_state=_base_state(node.model))
    assert result.contribution.round_num == round_num


# ---------------------------------------------------------------------------
# Property: structural invariants across model sizes and corpora
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes())
# @settings(deadline=None)
def test_cycle_result_structure_invariants_across_model_sizes(node):
    """Structural invariants hold regardless of model size or number of local epochs."""
    torch.manual_seed(0)
    base = _base_state(node.model)
    result = node.run_sovereign_cycle(round_num=1, base_state=base)

    # Identity fields
    assert result.artifact.node_id == node.node_id
    assert result.contribution.node_id == node.node_id
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


# ---------------------------------------------------------------------------
# Property: After cycles, updated artifacts and local model state available.
# ---------------------------------------------------------------------------


@given(sovereign_training_nodes())
@settings(deadline=None)  # For some reason, sometimes this test exceeds the default 300ms for hypothesis.
def test_sovereign_node_returns_artifact_and_local_model_state(node):
    """A node keeps a sovereign model artifact and shares its local weight vector."""
    torch.manual_seed(0)
    base_state = _base_state(node.model)
    result = node.run_sovereign_cycle(round_num=1, base_state=base_state)

    assert result.artifact.node_id == node.node_id
    assert result.artifact.stage == "continued_pretraining"
    assert result.artifact.model_state
    assert result.contribution.node_id == node.node_id
    assert result.contribution.round_num == 1
    assert result.contribution.quality_score == pytest.approx(node.quality_score)
    assert set(result.contribution.local_model_state) == set(base_state)
    assert any(
        not torch.equal(result.contribution.local_model_state[name], base_state[name]) for name in base_state
    ), f"{result.contribution.local_model_state} =?= {base_state}"
