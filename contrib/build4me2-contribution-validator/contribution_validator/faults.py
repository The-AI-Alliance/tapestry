"""Fault injection helpers for exercising the validator.

These produce the kinds of malformed contributions the validator is meant to
stop: missing or extra tensors, wrong shapes or dtypes, NaN/inf values, and
implausibly large updates. They are used by the tests and the demo runner.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace

import torch
from torch import nn

from tapestry.training.consortium import SovereignCycleResult, SovereignTrainingNode
from tapestry.training.consortium.messages import ModelState

Fault = Callable[[ModelState], ModelState]


def _first_name(state: ModelState) -> str:
    """Name of the first floating point tensor, which every fault below targets."""
    for name, tensor in state.items():
        if tensor.is_floating_point():
            return name
    raise ValueError("state has no floating point tensor to corrupt")


def inject_nan(state: ModelState, count: int = 1) -> ModelState:
    """Overwrite the first ``count`` elements of the first tensor with NaN."""
    name = _first_name(state)
    tensor = state[name].clone().contiguous()
    tensor.view(-1)[:count] = float("nan")
    return {**state, name: tensor}


def inject_inf(state: ModelState, count: int = 1) -> ModelState:
    """Overwrite the first ``count`` elements of the first tensor with +inf."""
    name = _first_name(state)
    tensor = state[name].clone().contiguous()
    tensor.view(-1)[:count] = float("inf")
    return {**state, name: tensor}


def drop_parameter(state: ModelState) -> ModelState:
    """Remove the first tensor from the state."""
    name = _first_name(state)
    return {key: value for key, value in state.items() if key != name}


def add_parameter(state: ModelState, name: str = "unexpected.weight") -> ModelState:
    """Add a tensor the shared base does not have."""
    return {**state, name: torch.zeros(1)}


def reshape_parameter(state: ModelState) -> ModelState:
    """Replace the first tensor with one of a different shape."""
    name = _first_name(state)
    tensor = state[name]
    return {**state, name: torch.zeros(tensor.numel() + 1, dtype=tensor.dtype)}


def cast_parameters(state: ModelState, dtype: torch.dtype = torch.float16) -> ModelState:
    """Cast every floating point tensor to ``dtype``."""
    return {name: tensor.to(dtype) if tensor.is_floating_point() else tensor for name, tensor in state.items()}


def scale_parameters(state: ModelState, factor: float = 1000.0) -> ModelState:
    """Multiply every floating point tensor by ``factor`` to produce an implausibly large update.

    Integer buffers are left alone so the fault exercises magnitude limits only,
    not dtype checks.
    """
    return {name: tensor * factor if tensor.is_floating_point() else tensor for name, tensor in state.items()}


class FaultInjectingNode(SovereignTrainingNode):  # pylint: disable=too-few-public-methods
    """A sovereign node whose shared contribution is corrupted by ``fault``.

    The node trains normally and keeps a correct sovereign artifact. Only the
    contribution handed to the coordinator is altered, which mirrors a
    transport, serialization, or software fault on the way to the shared
    boundary.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        node_id: str,
        jurisdiction: str,
        model: nn.Module,
        sovereign_corpus: Sequence[list[int]],
        quality_score: float,
        fault: Fault,
        local_epochs: int = 3,
        lr: float = 1e-3,
        batch_size: int = 8,
    ) -> None:
        super().__init__(
            node_id=node_id,
            jurisdiction=jurisdiction,
            model=model,
            sovereign_corpus=sovereign_corpus,
            quality_score=quality_score,
            local_epochs=local_epochs,
            lr=lr,
            batch_size=batch_size,
        )
        self.fault = fault

    def run_sovereign_cycle(self, round_num: int, base_state: ModelState) -> SovereignCycleResult:
        """Run the normal cycle, then corrupt the outgoing contribution."""
        result = super().run_sovereign_cycle(round_num, base_state)
        corrupted = replace(result.contribution, local_model_state=self.fault(result.contribution.local_model_state))
        return SovereignCycleResult(artifact=result.artifact, contribution=corrupted)
