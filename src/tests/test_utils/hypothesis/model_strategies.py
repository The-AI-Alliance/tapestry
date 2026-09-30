"""
Hypothesis generates for models.
Hypothesis is a Python property-based testing framework.
https://hypothesis.readthedocs.io/en/latest/
"""

import torch

from hypothesis import strategies as st
from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    ContributionWeighting,
    OuterMerge,
    OuterMergeStrategy,
    SovereignTrainingNode,
    TinyCausalModel,
)


def quality_floors(min_value=0.0, max_value=0.9):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)


def max_node_weights(min_value=0.1, max_value=1.0):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)


# Node IDs: short unique ASCII strings.
def node_ids(min_size=1, max_size=8):
    return st.text(
        min_size=min_size, max_size=max_size, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
    )


# Parameter names: short ASCII strings.
def parameter_names(min_size=1, max_size=8):
    return st.text(
        min_size=min_size, max_size=max_size, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
    )


def model_states(param_names: list[str], size: int):
    """Strategy: a ModelState dict with fixed param names and 1-D tensors of `size` elements."""
    return st.fixed_dictionaries(
        {name: st.lists(tensor_elements(), min_size=size, max_size=size).map(torch.tensor) for name in param_names}
    )


def multi_node_states(param_names: list[str], size: int, min_nodes: int = 1, max_nodes: int = 4):
    """Strategy: dict[node_id -> ModelState], all sharing the same param_names and size."""
    return st.dictionaries(
        node_ids(),
        model_states(param_names, size),
        min_size=min_nodes,
        max_size=max_nodes,
    )


def uniform_weights(node_ids: list[str]) -> dict[str, float]:
    """Equal weight for every node in a list."""
    w = 1.0 / len(node_ids)
    return {nid: w for nid in node_ids}


def scores(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=allow_nan, allow_infinity=allow_infinity)


def quality_score_maps(node_ids=node_ids, scores=scores, min_size=1, max_size=12):
    """Dictionaries mapping node IDs to non-negative quality scores."""
    return st.dictionaries(node_ids(), scores(), min_size=min_size, max_size=max_size)


def jurisdictions(min_size=1, max_size=12):
    return st.text(min_size=min_size, max_size=max_size)


def normalized_scores(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False):
    return scores(min_value=min_value, max_value=max_value, allow_nan=allow_nan, allow_infinity=allow_infinity)


def corpus_offsets(min_value=0, max_value=10):
    return st.integers(min_value=min_value, max_value=max_value)


def local_epochs(min_value=1, max_value=10):
    return st.integers(min_value=min_value, max_value=max_value)


def learning_rates(min_value=1e-3, max_value=4.0):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)


# Valid momentum values (strictly between 0 and 1).
def momenta(min_value=1e-3, max_value=0.99):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)


# Finite float tensors with a controlled range to avoid inf/nan arithmetic.
def tensor_elements(min_value=-1e3, max_value=1e3):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False)


def batch_sizes(min_value=1, max_value=16):
    return st.integers(min_value=min_value, max_value=max_value)


def make_corpus(offset: int = 0) -> list[list[int]]:
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]


def sovereign_corpuses(corpus_offsets=corpus_offsets):
    return corpus_offsets().map(lambda offset: make_corpus(offset))


a_sovereign_corpus = make_corpus()
an_empty_sovereign_corpus = []


def empty_sovereign_corpuses():
    return st.just(an_empty_sovereign_corpus)


def one_element_sovereign_corpuses(element=1):
    return st.just([[element]])


def tiny_causal_models(
    min_vocab_size=32,
    max_vocab_size=1028,
    min_hidden_size=2,
    max_hidden_size=16,
):
    """
    A Hypothesis strategy for generating `TinyCausalModel` instances.

    Args:
        - min_vocab_size (int):  The minimum size for a model's vocabulary.
        - max_vocab_size (int):  The maximum size for a model's vocabulary.
        - min_hidden_size (int): The minimum number of hidden layers.
        - max_hidden_size (int): The maximum number of hidden layers.

    Returns:
        A strategy for `TinyCausalModel` instances.
    """
    return st.builds(
        TinyCausalModel,
        vocab_size=st.integers(min_value=min_vocab_size, max_value=max_vocab_size),
        hidden_size=st.integers(min_value=min_hidden_size, max_value=max_hidden_size),
    )  # .map(lambda tup: TinyCausalModel(vocab_size=tup[0], hidden_size=tup[1]))


a_tiny_causal_model = TinyCausalModel(32, 2)


def one_tiny_causal_model():
    return st.just(a_tiny_causal_model)


def sovereign_training_nodes(
    node_ids=node_ids,
    jurisdictions=jurisdictions,
    models=tiny_causal_models,
    sovereign_corpuses=sovereign_corpuses,
    quality_scores=normalized_scores,
    local_epochs=local_epochs,
    learning_rates=learning_rates,
    batch_sizes=batch_sizes,
):
    return st.builds(
        SovereignTrainingNode,
        node_id=node_ids(),
        jurisdiction=jurisdictions(),
        model=models(),
        sovereign_corpus=sovereign_corpuses(),
        quality_score=quality_scores(),
        local_epochs=local_epochs(),
        lr=learning_rates(),
        batch_size=batch_sizes(),
    )


def contribution_weightings():
    return st.sampled_from(
        [
            ContributionWeighting.QUALITY,
            ContributionWeighting.EQUAL,
        ]
    )


def contribution_policies(
    quality_floors=quality_floors,
    max_node_weights=max_node_weights,
    contribution_weightings=contribution_weightings,
):
    return st.builds(
        ContributionPolicy,
        quality_floor=quality_floors(),
        max_node_weight=max_node_weights(),
        weighting=contribution_weightings(),
    )


def outer_merge_strategies():
    return st.sampled_from(
        [
            OuterMergeStrategy.WEIGHTED_AVERAGE,
            OuterMergeStrategy.DELTA,
            OuterMergeStrategy.MOMENTUM_DELTA,
        ]
    )


def weighted_average_outer_merges():
    return st.just(
        OuterMerge(
            strategy=OuterMergeStrategy.WEIGHTED_AVERAGE,
            outer_lr=1.0,
            outer_momentum=0.0,
        )
    )


def delta_outer_merges(
    outer_learning_rates=learning_rates,
):
    return st.builds(
        OuterMerge,
        strategy=st.just(OuterMergeStrategy.DELTA),
        outer_lr=outer_learning_rates(),
        outer_momentum=st.just(0.0),
    )


def momentum_delta_outer_merges(
    outer_learning_rates=learning_rates,
    outer_momenta=momenta,
):
    return st.builds(
        OuterMerge,
        strategy=st.just(OuterMergeStrategy.MOMENTUM_DELTA),
        outer_lr=outer_learning_rates(),
        outer_momentum=momenta(),
    )


def outer_merges(
    outer_learning_rates=learning_rates,
    outer_momenta=momenta,
):
    return st.one_of(
        weighted_average_outer_merges(),
        delta_outer_merges(outer_learning_rates=outer_learning_rates),
        momentum_delta_outer_merges(outer_learning_rates=outer_learning_rates, outer_momenta=outer_momenta),
    )


def consortium_coordinators(
    models=tiny_causal_models,
    contribution_policies=contribution_policies,
    outer_merges=outer_merges,
):
    return st.builds(
        ConsortiumCoordinator,
        base_model=models(),
        contribution_policy=contribution_policies(),
        outer_merge=outer_merges(),
    )
