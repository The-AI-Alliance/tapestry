"""
Hypothesis generates for models.
Hypothesis is a Python property-based testing framework.
https://hypothesis.readthedocs.io/en/latest/
"""

from hypothesis import strategies as st
from tapestry.training.consortium import (
    SovereignTrainingNode,
    TinyCausalModel,
)


def quality_floors(min_value=0.0, max_value=0.9):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)

def max_node_weights(min_value=0.1, max_value=1.0):
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False)

def node_ids(min_size=1, max_size=12, alphabet=lambda: st.characters(whitelist_categories=("Ll", "Lu", "Nd"))):
    return st.text(min_size=min_size, max_size=max_size, alphabet=alphabet())

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

def learning_rates(min_value=0.01, max_value=0.1):
    return st.floats(min_value=min_value, max_value=max_value)

def make_corpus(offset: int = 0) -> list[list[int]]:
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]

def sovereign_corpuses(corpus_offsets=corpus_offsets):
    return corpus_offsets().map(lambda offset: make_corpus(offset))

a_sovereign_corpus = make_corpus()
an_empty_sovereign_corpus=[]

def empty_sovereign_corpuses():
    return st.just(an_empty_sovereign_corpus)

def one_element_sovereign_corpuses(element = 1):
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
    return st.tuples(
        st.integers(min_value=min_vocab_size, max_value=max_vocab_size),
        st.integers(min_value=min_hidden_size, max_value=max_hidden_size),
    ).map(lambda tup: TinyCausalModel(vocab_size=tup[0], hidden_size=tup[1]))

a_tiny_causal_model = TinyCausalModel(32,2)

def one_tiny_causal_model():
    return st.just(a_tiny_causal_model)

def sovereign_training_nodes(
    models = tiny_causal_models,
    node_ids = node_ids,
    jurisdictions = jurisdictions,
    quality_scores = normalized_scores,
    sovereign_corpus = sovereign_corpuses,
    local_epochs = local_epochs,
    learning_rates = learning_rates,
):
    return st.tuples(
        models(),
        node_ids(),
        jurisdictions(),
        quality_scores(),
        corpus_offsets(),
        local_epochs(),
        learning_rates(),
    ).map(lambda tup: SovereignTrainingNode(
        model=tup[0],
        node_id=tup[1],
        jurisdiction=tup[2],
        sovereign_corpus=make_corpus(tup[3]),
        quality_score=tup[4],
        local_epochs=tup[5],
        lr=tup[6],
    ))
