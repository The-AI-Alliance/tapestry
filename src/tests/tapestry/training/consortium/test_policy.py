"""Property-based and unit tests for ContributionPolicy."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tapestry.training.consortium import ContributionPolicy, ContributionWeighting
from tests.test_utils.hypothesis.model_strategies import (
    max_node_weights,
    node_ids,
    quality_floors,
    quality_score_maps,
)

# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------


def test_negative_quality_floor_raises():
    with pytest.raises(ValueError, match="quality_floor"):
        ContributionPolicy(quality_floor=-0.01)


def test_zero_max_node_weight_raises():
    with pytest.raises(ValueError, match="max_node_weight"):
        ContributionPolicy(max_node_weight=0.0)


def test_max_node_weight_above_one_raises():
    with pytest.raises(ValueError, match="max_node_weight"):
        ContributionPolicy(max_node_weight=1.0001)


def test_invalid_weighting_string_raises():
    with pytest.raises(ValueError):
        ContributionPolicy(weighting="unknown")


# ---------------------------------------------------------------------------
# Quality-weighting properties
# ---------------------------------------------------------------------------


@given(quality_floors(), max_node_weights(), quality_score_maps())
def test_quality_weights_sum_to_one_when_non_empty(quality_floor, max_node_weight, scores):
    """For quality weighting, non-empty output always sums to 1.0."""
    policy = ContributionPolicy(quality_floor=quality_floor, max_node_weight=max_node_weight)
    weights = policy.weights(scores)

    if weights:
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


@given(quality_floors(), max_node_weights(), quality_score_maps())
def test_quality_weights_exclude_below_floor(quality_floor, max_node_weight, scores):
    """No node with a score below the quality floor appears in the output."""
    policy = ContributionPolicy(quality_floor=quality_floor, max_node_weight=max_node_weight)
    weights = policy.weights(scores)

    for node_id, score in scores.items():
        if score < quality_floor:
            assert node_id not in weights


@given(
    st.dictionaries(
        node_ids(),
        st.floats(min_value=1e-9, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=12,
    ),
    max_node_weights(),
)
def test_quality_weights_respect_cap_when_enforceable(scores, max_node_weight):
    """No individual weight exceeds max_node_weight when enough nodes are accepted.

    The cap is only enforceable when the number of accepted nodes n satisfies
    ``max_node_weight * n >= 1``, i.e. no single node *must* exceed the cap to
    reach a sum of 1.0.  Below that threshold the cap is vacuous.
    """
    policy = ContributionPolicy(quality_floor=0.0, max_node_weight=max_node_weight)
    weights = policy.weights(scores)

    n = len(weights)
    if n > 0 and max_node_weight * n >= 1.0 + 1e-9:
        # In this regime the cap is enforceable; verify no node exceeds it.
        for w in weights.values():
            assert w <= max_node_weight + 1e-9


@given(quality_floors(), max_node_weights(), quality_score_maps())
def test_quality_weights_all_non_negative(quality_floor, max_node_weight, scores):
    """All output weights must be non-negative."""
    policy = ContributionPolicy(quality_floor=quality_floor, max_node_weight=max_node_weight)
    weights = policy.weights(scores)

    for w in weights.values():
        assert w >= 0.0


@given(quality_floors(), max_node_weights(), quality_score_maps())
def test_quality_output_keys_are_subset_of_input(quality_floor, max_node_weight, scores):
    """Output node IDs are always a subset of input node IDs."""
    policy = ContributionPolicy(quality_floor=quality_floor, max_node_weight=max_node_weight)
    weights = policy.weights(scores)

    assert weights.keys() <= scores.keys()


# ---------------------------------------------------------------------------
# Equal-weighting properties
# ---------------------------------------------------------------------------


@given(quality_floors(), quality_score_maps())
def test_equal_weights_sum_to_one_when_non_empty(quality_floor, scores):
    """For equal weighting, non-empty output always sums to 1.0."""
    policy = ContributionPolicy(quality_floor=quality_floor, weighting=ContributionWeighting.EQUAL)
    weights = policy.weights(scores)

    if weights:
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


@given(quality_floors(), quality_score_maps())
def test_equal_weights_are_uniform(quality_floor, scores_map):
    """Every accepted node receives the same weight under equal weighting."""
    policy = ContributionPolicy(quality_floor=quality_floor, weighting=ContributionWeighting.EQUAL)
    weights = policy.weights(scores_map)

    values = list(weights.values())
    if values:
        expected = 1.0 / len(values)
        for w in values:
            assert w == pytest.approx(expected, abs=1e-9)


@given(quality_floors(), quality_score_maps())
def test_equal_weights_exclude_below_floor(quality_floor, scores_map):
    """Equal weighting still applies the quality floor."""
    policy = ContributionPolicy(quality_floor=quality_floor, weighting=ContributionWeighting.EQUAL)
    weights = policy.weights(scores_map)

    for node_id, score in scores_map.items():
        if score < quality_floor:
            assert node_id not in weights


# ---------------------------------------------------------------------------
# Edge-case unit tests
# ---------------------------------------------------------------------------


def test_all_below_floor_returns_empty():
    """All scores below the floor → empty dict, not an error."""
    policy = ContributionPolicy(quality_floor=0.5)
    assert policy.weights({"a": 0.1, "b": 0.3}) == {}


def test_single_accepted_node_gets_full_weight():
    """One node above the floor receives a weight of 1.0."""
    policy = ContributionPolicy(quality_floor=0.5)
    weights = policy.weights({"only": 0.9, "filtered": 0.2})

    assert set(weights) == {"only"}
    assert weights["only"] == pytest.approx(1.0)


def test_equal_weighting_string_alias():
    """ContributionPolicy accepts the string alias 'equal' for the weighting arg."""
    policy = ContributionPolicy(weighting="equal")
    assert policy.weighting is ContributionWeighting.EQUAL


def test_quality_weighting_string_alias():
    """ContributionPolicy accepts the string alias 'quality' for the weighting arg."""
    policy = ContributionPolicy(weighting="quality")
    assert policy.weighting is ContributionWeighting.QUALITY


def test_all_zero_scores_treated_as_equal():
    """When all accepted scores are 0.0, nodes receive equal weight (no ZeroDivisionError)."""
    policy = ContributionPolicy(quality_floor=0.0)
    weights = policy.weights({"a": 0.0, "b": 0.0, "c": 0.0})

    assert weights == {
        "a": pytest.approx(1 / 3),
        "b": pytest.approx(1 / 3),
        "c": pytest.approx(1 / 3),
    }


def test_empty_scores_returns_empty():
    """An empty input dict always returns an empty dict."""
    policy = ContributionPolicy()
    assert policy.weights({}) == {}
