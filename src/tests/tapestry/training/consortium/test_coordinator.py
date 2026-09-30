"""Property-based and unit tests for ConsortiumCoordinator."""

import copy

import pytest
import torch
from hypothesis import given
from hypothesis import strategies as st

from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    OuterMerge,
    OuterMergeStrategy,
    SovereignTrainingNode,
    TinyCausalModel,
)
from tests.test_utils.hypothesis.model_strategies import (
    a_tiny_causal_model,
    consortium_coordinators,
    contribution_policies,
    make_corpus,
    quality_floors,
    tiny_causal_models,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(
    node_id: str = "a node",
    jurisdiction: str = "a jurisdiction",
    model: TinyCausalModel = a_tiny_causal_model,
    quality_score: float = 0.9,
    corpus_offset: int = 0,
    local_epochs: int = 1,
    lr: float = 0.01,
) -> SovereignTrainingNode:
    return SovereignTrainingNode(
        node_id=node_id,
        jurisdiction=jurisdiction,
        model=model,
        sovereign_corpus=make_corpus(corpus_offset),
        quality_score=quality_score,
        local_epochs=local_epochs,
        lr=lr,
    )


# ---------------------------------------------------------------------------
# Constructor defaults
# ---------------------------------------------------------------------------


@given(tiny_causal_models())
def test_default_policy_is_created_when_not_supplied(model):
    """ConsortiumCoordinator creates a default ContributionPolicy when none is given."""
    coordinator = ConsortiumCoordinator(base_model=model)
    assert coordinator.contribution_policy == ContributionPolicy()


@given(tiny_causal_models())
def test_default_outer_merge_is_created_when_not_supplied(model):
    """ConsortiumCoordinator creates a default OuterMerge when none is given."""
    coordinator = ConsortiumCoordinator(base_model=model)
    assert isinstance(coordinator.outer_merge, OuterMerge)
    assert coordinator.outer_merge.strategy is OuterMergeStrategy.WEIGHTED_AVERAGE


@given(tiny_causal_models())
def test_base_model_is_deep_copied_on_init(model):
    """Mutating the original model after construction must not affect the coordinator."""
    original = model
    coordinator = ConsortiumCoordinator(base_model=original)

    # Clobber the original's weights in-place.
    with torch.no_grad():
        for param in original.parameters():
            param.fill_(999.0)

    for tensor in coordinator.base_model.state_dict().values():
        assert tensor.max().item() != pytest.approx(999.0)


# ---------------------------------------------------------------------------
# shared_base_state property
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
def test_shared_base_state_returns_clone_not_alias(coordinator):
    """Each call to shared_base_state must return an independent snapshot."""
    snap1 = coordinator.shared_base_state
    snap2 = coordinator.shared_base_state

    # Same values but not the same tensor objects.
    for name in snap1:
        assert snap1[name] is not snap2[name]
        assert torch.equal(snap1[name], snap2[name])


@given(tiny_causal_models())
def test_shared_base_state_keys_match_model_state_dict(model):
    """shared_base_state must contain exactly the same parameter names as the base model."""
    coordinator = ConsortiumCoordinator(base_model=model)
    assert set(coordinator.shared_base_state) == set(model.state_dict())


# ---------------------------------------------------------------------------
# round_num increments
# ---------------------------------------------------------------------------


@given(consortium_coordinators(), st.integers(min_value=1, max_value=5))
# @settings(deadline=None)
def test_round_num_increments_with_each_run_round(coordinator, num_rounds):
    """ConsortiumCoordinator.run_round increments round_num on every call."""
    torch.manual_seed(0)
    nodes = [_node(model=coordinator.base_model)]

    for expected in range(1, num_rounds + 1):
        result = coordinator.run_round(nodes)
        assert result.round_num == expected


# ---------------------------------------------------------------------------
# Accepted / rejected partitioning
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
# @settings(deadline=None)
def test_accepted_and_rejected_partition_all_nodes(coordinator):
    """accepted_nodes and rejected_nodes together cover every input node exactly once."""
    torch.manual_seed(1)
    quality_floor = coordinator.contribution_policy.quality_floor
    nodes = [
        _node(node_id="above", model=coordinator.base_model, quality_score=quality_floor + 0.1, corpus_offset=0),
        _node(
            node_id="below", model=coordinator.base_model, quality_score=max(quality_floor - 0.1, 0.0), corpus_offset=5
        ),
    ]

    result = coordinator.run_round(nodes)

    all_node_ids = {n.node_id for n in nodes}
    assert set(result.accepted_nodes) | set(result.rejected_nodes) == all_node_ids
    assert set(result.accepted_nodes) & set(result.rejected_nodes) == set()


# @given(quality_floors(min_value=0.0, max_value=0.8))
# @settings(deadline=None)
# def test_accepted_and_rejected_partition_all_nodes(quality_floor):
#     """accepted_nodes and rejected_nodes together cover every input node exactly once."""
#     torch.manual_seed(1)
#     coordinator = ConsortiumCoordinator(
#         base_model=_model(),
#         contribution_policy=ContributionPolicy(quality_floor=quality_floor),
#     )
#     nodes = [
#         _node("above", quality_score=quality_floor + 0.1, corpus_offset=0),
#         _node("below", quality_score=max(quality_floor - 0.1, 0.0), corpus_offset=5),
#     ]

#     result = coordinator.run_round(nodes)

#     all_node_ids = {n.node_id for n in nodes}
#     assert set(result.accepted_nodes) | set(result.rejected_nodes) == all_node_ids
#     assert set(result.accepted_nodes) & set(result.rejected_nodes) == set()


# ---------------------------------------------------------------------------
# contribution_weights ↔ accepted_nodes consistency
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
def test_contribution_weights_keys_match_accepted_nodes(coordinator):
    """contribution_weights must have exactly the same keys as accepted_nodes."""
    torch.manual_seed(2)
    # quality_floor = coordinator.contribution_policy.quality_floor
    nodes = [
        _node(node_id="pass", model=coordinator.base_model, quality_score=0.9, corpus_offset=0),
        _node(node_id="fail", model=coordinator.base_model, quality_score=0.1, corpus_offset=5),
    ]

    result = coordinator.run_round(nodes)

    assert set(result.contribution_weights) == set(result.accepted_nodes)


@given(consortium_coordinators())
def test_contribution_weights_sum_to_one_when_non_empty(coordinator):
    """Weights returned in the result must sum to 1.0 for any accepted set."""
    torch.manual_seed(3)
    nodes = [
        _node(node_id="x", model=coordinator.base_model, quality_score=0.9, corpus_offset=0),
        _node(node_id="y", model=coordinator.base_model, quality_score=0.8, corpus_offset=5),
    ]

    result = coordinator.run_round(nodes)

    if result.contribution_weights:
        assert sum(result.contribution_weights.values()) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Base model update behaviour
# ---------------------------------------------------------------------------


@given(
    consortium_coordinators(
        contribution_policies=lambda: contribution_policies(quality_floors=lambda: quality_floors(min_value=0.1))
    )
)
def test_all_rejected_leaves_shared_base_unchanged(coordinator):
    """When no node is accepted, the shared base must be identical before and after."""
    torch.manual_seed(4)
    # coordinator = ConsortiumCoordinator(
    #     base_model=_model(),
    #     contribution_policy=ContributionPolicy(quality_floor=0.99),
    # )
    weak_quality = coordinator.contribution_policy.quality_floor - 0.05
    result = coordinator.run_round(
        [
            _node(node_id="weak", model=coordinator.base_model, quality_score=weak_quality),
        ]
    )

    assert result.rejected_nodes == ["weak"]
    assert result.accepted_nodes == []
    for name in result.shared_base_state:
        assert torch.equal(result.previous_base_state[name], result.shared_base_state[name])


@given(consortium_coordinators())
def test_accepted_nodes_update_shared_base(coordinator):
    """When at least one node is accepted, the base must change after the round."""
    torch.manual_seed(5)
    # coordinator = ConsortiumCoordinator(
    #     base_model=_model(),
    #     contribution_policy=ContributionPolicy(quality_floor=0.0),
    # )
    result = coordinator.run_round(
        [
            _node(node_id="strong", model=coordinator.base_model, quality_score=0.9),
        ]
    )

    assert result.accepted_nodes == ["strong"]
    assert any(
        not torch.equal(result.previous_base_state[name], result.shared_base_state[name])
        for name in result.shared_base_state
    )


# ---------------------------------------------------------------------------
# Sovereign artifact accumulation
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
def test_sovereign_artifacts_accumulate_across_rounds(coordinator):
    """Each run_round stores an artifact per node; subsequent rounds add to the dict."""
    torch.manual_seed(6)
    # coordinator = ConsortiumCoordinator(base_model=_model())

    _ = coordinator.run_round(
        [
            _node(node_id="alpha", model=coordinator.base_model, quality_score=0.9, corpus_offset=0),
        ]
    )
    assert set(coordinator.sovereign_artifacts) == {"alpha"}

    _ = coordinator.run_round(
        [
            _node(node_id="beta", model=coordinator.base_model, quality_score=0.8, corpus_offset=5),
        ]
    )
    assert set(coordinator.sovereign_artifacts) == {"alpha", "beta"}


@given(consortium_coordinators())
def test_sovereign_artifact_is_overwritten_on_repeat_node(coordinator):
    """A second round for the same node replaces its artifact entry, not appends."""
    torch.manual_seed(7)
    # coordinator = ConsortiumCoordinator(base_model=_model())

    _ = coordinator.run_round(
        [
            _node(node_id="repeat", model=coordinator.base_model, quality_score=0.9, corpus_offset=0),
        ]
    )
    first_artifact = coordinator.sovereign_artifacts["repeat"]

    _ = coordinator.run_round(
        [
            _node(node_id="repeat", model=coordinator.base_model, quality_score=0.9, corpus_offset=0),
        ]
    )
    second_artifact = coordinator.sovereign_artifacts["repeat"]

    assert len(coordinator.sovereign_artifacts) == 1
    assert second_artifact is not first_artifact


# ---------------------------------------------------------------------------
# outer_merge_strategy propagated to result
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
def test_result_reports_correct_outer_merge_strategy(coordinator):
    """outer_merge_strategy in the result must match the configured merge strategy."""
    torch.manual_seed(8)
    # coordinator = ConsortiumCoordinator(
    #     base_model=_model(),
    #     outer_merge=OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=0.5),
    # )
    result = coordinator.run_round(
        [
            _node(model=coordinator.base_model, quality_score=0.9),
        ]
    )
    assert result.outer_merge_strategy == coordinator.outer_merge.strategy


# ---------------------------------------------------------------------------
# Hypothesis: structural invariants across model sizes
# ---------------------------------------------------------------------------


@given(consortium_coordinators())
# @settings(deadline=None)
def test_round_result_structure_invariants(coordinator):
    """ConsortiumRoundResult structural invariants hold across generated model sizes."""
    torch.manual_seed(0)
    # coordinator = ConsortiumCoordinator(
    #     base_model=model,
    #     contribution_policy=ContributionPolicy(quality_floor=quality_floor),
    # )
    quality_floor = coordinator.contribution_policy.quality_floor
    model_copy_1 = copy.deepcopy(coordinator.base_model)
    model_copy_2 = copy.deepcopy(coordinator.base_model)
    nodes = [
        SovereignTrainingNode(
            node_id="p",
            jurisdiction="T",
            model=model_copy_1,
            sovereign_corpus=make_corpus(0),
            quality_score=quality_floor + 0.05,
            local_epochs=1,
            lr=0.01,
        ),
        SovereignTrainingNode(
            node_id="q",
            jurisdiction="T",
            model=model_copy_2,
            sovereign_corpus=make_corpus(5),
            quality_score=max(quality_floor - 0.05, 0.0),
            local_epochs=1,
            lr=0.01,
        ),
    ]

    result = coordinator.run_round(nodes)

    # Structural invariants that must hold regardless of model size or quality floor.
    assert result.round_num == 1
    all_ids = {n.node_id for n in nodes}
    assert set(result.accepted_nodes) | set(result.rejected_nodes) == all_ids
    assert set(result.accepted_nodes) & set(result.rejected_nodes) == set()
    assert set(result.contribution_weights) == set(result.accepted_nodes)
    assert set(result.shared_base_state) == set(coordinator.base_model.state_dict())
    assert set(result.previous_base_state) == set(coordinator.base_model.state_dict())
    if result.contribution_weights:
        assert sum(result.contribution_weights.values()) == pytest.approx(1.0, abs=1e-9)
