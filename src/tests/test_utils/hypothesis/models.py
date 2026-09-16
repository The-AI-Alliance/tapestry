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


def tiny_causal_models(
    min_vocab_size: int = 32,
    max_vocab_size: int = 1028,
    min_hidden_size: int = 2,
    max_hidden_size: int = 16,
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
