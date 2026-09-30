"""Property-based and unit tests for OuterMerge and OuterMergeStrategy."""

import pytest
import torch
from hypothesis import given
from hypothesis import strategies as st

from tapestry.training.consortium import OuterMerge, OuterMergeStrategy
from tests.test_utils.hypothesis.model_strategies import (
    learning_rates,
    momenta,
    outer_merges,
    parameter_names,
    tensor_elements,
    uniform_weights,
)

# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------


@given(st.floats(min_value=-1.0, max_value=0.0))
def test_non_positive_outer_lr_raises_for_delta_and_momentum_delta_merge_strategy(outer_lr):
    for strat in [OuterMergeStrategy.DELTA, OuterMergeStrategy.MOMENTUM_DELTA]:
        with pytest.raises(ValueError, match=f"Expect outer_lr > 0.0 for strategy {strat}"):
            OuterMerge(strategy=strat, outer_lr=outer_lr)


@given(st.floats(min_value=-1.0, max_value=1.0))
def test_outer_lr_ignored_for_weighted_average_merge_strategy(outer_lr):
    _ = OuterMerge(strategy=OuterMergeStrategy.WEIGHTED_AVERAGE, outer_lr=outer_lr)


@given(st.floats(min_value=1.0, max_value=10.0))
def test_outer_momentum_at_greater_than_or_equal_to_one_raises(outer_momentum):
    with pytest.raises(ValueError, match="OuterMergeStrategy.MOMENTUM_DELTA requires outer_momentum > 0 and < 1.0."):
        OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_momentum=outer_momentum)


def test_momentum_delta_requires_nonzero_momentum():
    with pytest.raises(ValueError, match="OuterMergeStrategy.MOMENTUM_DELTA requires outer_momentum"):
        OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_momentum=0.0)


def test_invalid_strategy_string_raises():
    with pytest.raises(ValueError):
        OuterMerge(strategy="not-a-strategy")


def test_strategy_string_alias_weighted_average():
    merge = OuterMerge(strategy="weighted-average")
    assert merge.strategy is OuterMergeStrategy.WEIGHTED_AVERAGE


def test_strategy_string_alias_delta():
    merge = OuterMerge(strategy="delta", outer_lr=0.5)
    assert merge.strategy is OuterMergeStrategy.DELTA


def test_strategy_string_alias_momentum_delta():
    merge = OuterMerge(strategy="momentum-delta", outer_lr=0.5, outer_momentum=0.9)
    assert merge.strategy is OuterMergeStrategy.MOMENTUM_DELTA


@given(outer_merges())
def test_outer_merges_hypothesis_strategy_generates_valid_outer_merges(outer_merge):
    pass  # Any exceptions thrown during construction of outer_merge would be a failure.


# ---------------------------------------------------------------------------
# WEIGHTED_AVERAGE — unit tests
# ---------------------------------------------------------------------------


def test_weighted_average_single_node_reproduces_its_state():
    """One node with weight 1.0 → output equals that node's state exactly."""
    prev = {"w": torch.tensor([0.0, 0.0])}
    local = {"only": {"w": torch.tensor([3.0, 7.0])}}
    result = OuterMerge().merge(prev, local, {"only": 1.0})
    assert torch.allclose(result["w"], torch.tensor([3.0, 7.0]))


def test_weighted_average_two_equal_nodes_produces_elementwise_mean():
    """Two nodes with equal weight → output is their elementwise average."""
    prev = {"w": torch.tensor([0.0])}
    local = {
        "a": {"w": torch.tensor([2.0])},
        "b": {"w": torch.tensor([8.0])},
    }
    result = OuterMerge().merge(prev, local, {"a": 0.5, "b": 0.5})
    assert result["w"].item() == pytest.approx(5.0)


def test_weighted_average_ignores_previous_state():
    """Weighted-average output depends only on local states, not the previous base."""
    local = {"n": {"w": torch.tensor([4.0])}}
    weights = {"n": 1.0}

    prev_a = {"w": torch.tensor([0.0])}
    prev_b = {"w": torch.tensor([100.0])}

    result_a = OuterMerge().merge(prev_a, local, weights)
    result_b = OuterMerge().merge(prev_b, local, weights)

    assert torch.allclose(result_a["w"], result_b["w"])


# ---------------------------------------------------------------------------
# WEIGHTED_AVERAGE — Hypothesis properties
# ---------------------------------------------------------------------------


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
)
def test_weighted_average_output_keys_match_local_state_keys(param_names, size):
    """Output keys always match the parameter names in the local states."""
    prev = {name: torch.zeros(size) for name in param_names}
    local = {"a": {name: torch.ones(size) for name in param_names}}
    result = OuterMerge().merge(prev, local, {"a": 1.0})
    assert set(result) == set(param_names)


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
    n_nodes=st.integers(min_value=1, max_value=5),
)
def test_weighted_average_output_shapes_match_input_shapes(param_names, size, n_nodes):
    """Every output tensor must have the same shape as the corresponding input tensors."""
    prev = {name: torch.zeros(size) for name in param_names}
    node_ids = [f"n{i}" for i in range(n_nodes)]
    local = {nid: {name: torch.ones(size) for name in param_names} for nid in node_ids}
    weights = uniform_weights(node_ids)
    result = OuterMerge().merge(prev, local, weights)
    for name in param_names:
        assert result[name].shape == prev[name].shape


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=3, unique=True),
    size=st.integers(min_value=1, max_value=6),
    n_nodes=st.integers(min_value=2, max_value=5),
)
def test_weighted_average_result_is_within_node_value_range(param_names, size, n_nodes):
    """Each output element must lie within the range [min, max] across all node values.

    This is the convex-combination invariant for non-negative weights summing to 1.
    """
    node_ids = [f"n{i}" for i in range(n_nodes)]
    prev = {name: torch.zeros(size) for name in param_names}
    # Build local states with incrementing offsets so they're clearly distinct.
    local = {nid: {name: torch.full((size,), float(i)) for name in param_names} for i, nid in enumerate(node_ids)}
    weights = uniform_weights(node_ids)
    result = OuterMerge().merge(prev, local, weights)

    for name in param_names:
        all_node_vals = torch.stack([local[nid][name] for nid in node_ids])
        lo = all_node_vals.min()
        hi = all_node_vals.max()
        assert result[name].min() >= lo - 1e-5
        assert result[name].max() <= hi + 1e-5


# ---------------------------------------------------------------------------
# DELTA — unit tests
# ---------------------------------------------------------------------------


def test_delta_zero_delta_returns_previous_state():
    """When local state equals the base, delta merge leaves the state unchanged."""
    state = {"w": torch.tensor([5.0, -3.0])}
    local = {"a": {"w": torch.tensor([5.0, -3.0])}}
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=0.7)
    result = merge.merge(state, local, {"a": 1.0})
    assert torch.allclose(result["w"], state["w"])


def test_delta_outer_lr_one_applies_full_weighted_delta():
    """outer_lr=1.0 means the full weighted delta is added to the previous base."""
    prev = {"w": torch.tensor([2.0])}
    local = {
        "a": {"w": torch.tensor([4.0])},  # delta = +2
        "b": {"w": torch.tensor([8.0])},  # delta = +6
    }
    # Weighted delta = 0.5 * 2 + 0.5 * 6 = 4.0 → result = 2 + 4 = 6
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=1.0)
    result = merge.merge(prev, local, {"a": 0.5, "b": 0.5})
    assert result["w"].item() == pytest.approx(6.0)


def test_delta_outer_lr_scales_the_update():
    """outer_lr < 1.0 applies a proportionally smaller update to the previous base."""
    prev = {"w": torch.tensor([0.0])}
    local = {"a": {"w": torch.tensor([10.0])}}  # delta = +10
    # outer_lr=0.3 → result = 0 + 10 * 0.3 = 3.0
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=0.3)
    result = merge.merge(prev, local, {"a": 1.0})
    assert result["w"].item() == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# DELTA — Hypothesis properties
# ---------------------------------------------------------------------------


def test_delta_outer_merge_applies_scaled_weighted_delta() -> None:
    """Delta merge applies weighted node deltas to the previous base."""
    previous_state = {"weight": torch.tensor([4.0])}
    local_states = {
        "a": {"weight": torch.tensor([6.0])},
        "b": {"weight": torch.tensor([10.0])},
    }
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=0.5)

    merged = merge.merge(previous_state, local_states, {"a": 0.25, "b": 0.75})

    # Weighted delta is 0.25 * 2 + 0.75 * 6 = 5.0; outer_lr applies half.
    assert merged["weight"].item() == pytest.approx(6.5)


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
    outer_lr=learning_rates(),
)
def test_delta_output_keys_match_previous_state_keys(param_names, size, outer_lr):
    """Delta merge output keys must match previous_state, not just local_states."""
    prev = {name: torch.zeros(size) for name in param_names}
    local = {"a": {name: torch.ones(size) for name in param_names}}
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=outer_lr)
    result = merge.merge(prev, local, {"a": 1.0})
    assert set(result) == set(param_names)


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
    outer_lr=learning_rates(),
    n_nodes=st.integers(min_value=1, max_value=5),
)
def test_delta_output_shapes_match_previous_state_shapes(param_names, size, outer_lr, n_nodes):
    """Every delta-merge output tensor must have the same shape as the previous base tensor."""
    node_ids = [f"n{i}" for i in range(n_nodes)]
    prev = {name: torch.zeros(size) for name in param_names}
    local = {nid: {name: torch.ones(size) for name in param_names} for nid in node_ids}
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=outer_lr)
    result = merge.merge(prev, local, uniform_weights(node_ids))
    for name in param_names:
        assert result[name].shape == prev[name].shape


@given(
    size=st.integers(min_value=1, max_value=8),
    outer_lr=learning_rates(),
    delta=tensor_elements(),
)
def test_delta_single_node_result_matches_analytic_formula(size, outer_lr, delta):
    """Single-node delta merge: result = previous + delta * outer_lr, elementwise."""
    base_val = 1.0  # arbitrary fixed base
    prev = {"w": torch.full((size,), base_val)}
    local = {"a": {"w": torch.full((size,), base_val + delta)}}
    merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=outer_lr)
    result = merge.merge(prev, local, {"a": 1.0})
    expected = base_val + delta * outer_lr
    assert torch.allclose(result["w"], torch.full((size,), expected), atol=1e-4)


# ---------------------------------------------------------------------------
# MOMENTUM_DELTA — unit tests
# ---------------------------------------------------------------------------


def test_momentum_delta_first_round_matches_plain_delta():
    """First round: velocity is zero so momentum-delta equals a plain delta step."""
    prev = {"w": torch.tensor([0.0])}
    local = {"a": {"w": torch.tensor([5.0])}}  # delta = 5
    # Both merges share outer_lr=1.0; momentum initialises to zero.
    md_merge = OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_lr=1.0, outer_momentum=0.5)
    d_merge = OuterMerge(strategy=OuterMergeStrategy.DELTA, outer_lr=1.0)

    md_result = md_merge.merge(prev, local, {"a": 1.0})
    d_result = d_merge.merge(prev, local, {"a": 1.0})

    assert torch.allclose(md_result["w"], d_result["w"])


def test_momentum_delta_second_round_exceeds_plain_delta():
    """Second round: accumulated velocity pushes the update beyond a plain delta step."""
    prev = {"w": torch.tensor([0.0])}
    local = {"a": {"w": torch.tensor([1.0])}}
    merge = OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_lr=1.0, outer_momentum=0.5)

    first = merge.merge(prev, local, {"a": 1.0})
    second = merge.merge(first, {"a": {"w": torch.tensor([first["w"].item() + 1.0])}}, {"a": 1.0})

    # Without momentum, second step would be +1.0; with momentum it is > 1.0.
    plain_second = first["w"].item() + 1.0
    assert second["w"].item() > plain_second - 1e-6


def test_momentum_delta_velocity_persists_across_merge_instances():
    """The velocity buffer is instance-local; two separate OuterMerge objects are independent."""
    prev = {"w": torch.tensor([0.0])}
    local = {"a": {"w": torch.tensor([1.0])}}
    m1 = OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_lr=1.0, outer_momentum=0.9)
    m2 = OuterMerge(strategy=OuterMergeStrategy.MOMENTUM_DELTA, outer_lr=1.0, outer_momentum=0.9)

    # Advance m1 two rounds.
    r1 = m1.merge(prev, local, {"a": 1.0})
    m1.merge(r1, {"a": {"w": torch.tensor([r1["w"].item() + 1.0])}}, {"a": 1.0})

    # m2 first round should still equal a plain delta (velocity = 0).
    m2_first = m2.merge(prev, local, {"a": 1.0})
    assert m2_first["w"].item() == pytest.approx(1.0)


@given(
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
    outer_lr=learning_rates(),
    outer_momentum=momenta(),
    n_rounds=st.integers(min_value=1, max_value=4),
)
def test_momentum_delta_output_keys_and_shapes_stable_across_rounds(
    param_names, size, outer_lr, outer_momentum, n_rounds
):
    """Keys and tensor shapes must remain consistent across multiple momentum-delta rounds."""
    merge = OuterMerge(
        strategy=OuterMergeStrategy.MOMENTUM_DELTA,
        outer_lr=outer_lr,
        outer_momentum=outer_momentum,
    )
    state = {name: torch.zeros(size) for name in param_names}
    for _ in range(n_rounds):
        local = {"a": {name: torch.ones(size) for name in param_names}}
        state = merge.merge(state, local, {"a": 1.0})
        assert set(state) == set(param_names)
        for name in param_names:
            assert state[name].shape == torch.zeros(size).shape


def test_momentum_delta_outer_merge_accumulates_outer_velocity() -> None:
    """Momentum merge carries an ordinary outer momentum buffer across rounds."""
    previous_state = {"weight": torch.tensor([0.0])}
    local_states = {"a": {"weight": torch.tensor([1.0])}}
    merge = OuterMerge(
        strategy=OuterMergeStrategy.MOMENTUM_DELTA,
        outer_lr=1.0,
        outer_momentum=0.5,
    )

    first = merge.merge(previous_state, local_states, {"a": 1.0})
    second = merge.merge(first, {"a": {"weight": torch.tensor([2.0])}}, {"a": 1.0})

    assert first["weight"].item() == pytest.approx(1.0)
    assert second["weight"].item() == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# Cross-strategy structural invariants (Hypothesis)
# ---------------------------------------------------------------------------


@given(
    strategy=st.sampled_from([OuterMergeStrategy.WEIGHTED_AVERAGE, OuterMergeStrategy.DELTA]),
    param_names=st.lists(parameter_names(), min_size=1, max_size=4, unique=True),
    size=st.integers(min_value=1, max_value=8),
    n_nodes=st.integers(min_value=1, max_value=4),
)
def test_all_strategies_return_matching_keys_and_shapes(strategy, param_names, size, n_nodes):
    """For every non-momentum strategy, output keys and shapes must match previous_state."""
    outer_lr = 0.5 if strategy is OuterMergeStrategy.DELTA else 1.0
    merge = OuterMerge(strategy=strategy, outer_lr=outer_lr)
    node_ids = [f"n{i}" for i in range(n_nodes)]
    prev = {name: torch.zeros(size) for name in param_names}
    local = {nid: {name: torch.ones(size) for name in param_names} for nid in node_ids}
    result = merge.merge(prev, local, uniform_weights(node_ids))

    assert set(result) == set(param_names)
    for name in param_names:
        assert result[name].shape == prev[name].shape
