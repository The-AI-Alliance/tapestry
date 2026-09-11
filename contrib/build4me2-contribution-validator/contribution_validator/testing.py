"""Small fixtures shared by the tests and the demo."""

from __future__ import annotations

import torch

from tapestry.training.consortium import TinyCausalModel
from tapestry.training.consortium.messages import ModelState


def tiny_model(seed: int = 0) -> TinyCausalModel:
    """A seeded tiny model so tests are deterministic."""
    torch.manual_seed(seed)
    return TinyCausalModel(vocab_size=64, hidden_size=16)


def toy_corpus(offset: int = 0) -> list[list[int]]:
    """Three short token sequences shifted by ``offset``."""
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]


def base_state(seed: int = 0) -> ModelState:
    """A cloned state dict of :func:`tiny_model`."""
    return {name: tensor.clone() for name, tensor in tiny_model(seed).state_dict().items()}
