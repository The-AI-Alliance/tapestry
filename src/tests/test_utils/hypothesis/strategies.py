"""
Hypothesis generates for models.
Hypothesis is a Python property-based testing framework.
https://hypothesis.readthedocs.io/en/latest/
"""

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

def quality_floors(min_value = 0.0, max_value = 0.9):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)

def max_node_weights(min_value = 0.1, max_value = 1.0):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)

def node_ids(
        min_size = 1,
        max_size = 12,
        alphabet = st.characters(whitelist_categories=("Ll", "Lu", "Nd"))):
    return st.text(min_size=min_size, max_size=max_size, alphabet=alphabet)

def scores(min_value = 0.0, max_value = 10.0, allow_nan = False, allow_infinity = False):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=allow_nan, allow_infinity=allow_infinity)

def quality_score_maps(
        node_ids = node_ids(),
        scores   = scores(),
        min_size = 1,
        max_size = 12):
    """Dictionaries mapping node IDs to non-negative quality scores."""
    return st.dictionaries(node_ids, scores, min_size=min_size, max_size=max_size)


def tiny_causal_models(
    min_vocab_size  = 32,
    max_vocab_size  = 1028,
    min_hidden_size = 2,
    max_hidden_size = 16,
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

    return st.tuples(
    	st.integers(min_value=min_vocab_size, max_value=max_vocab_size), 
    	st.integers(min_value=min_hidden_size, max_value=max_hidden_size), 
    	).map(lambda tup: TinyCausalModel(vocab_size=tup[0], hidden_size=tup[1]))
