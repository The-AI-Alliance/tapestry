"""Consortium learning: combine independently-trained member models into one.

A *consortium* is a set of member models that were trained separately (for example a
culturally-aligned member and a capability/rehearsal member). A *method* fuses those
members into a single model. **Model soup** (weight-space averaging) is the first
method (see consortium/soup/).

Later methods (TIES / DARE / Fisher-weighted / learned-coefficient merges, then
output-ensembling, then MoE / routing) implement the same `ConsortiumMethod.combine`
contract, so the rest of the pipeline -- and the shared evaluation harness -- treats
their output as just another model.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Member:
    """A trained member model entering the consortium."""
    path: str            # local dir or HF id of the (merged) member model
    name: str = ""       # short label, e.g. "culture" or "rehearsal"
    weight: float = 1.0  # relative weight, for methods that use one


class ConsortiumMethod(ABC):
    """Fuse N member models into one. Implemented by Soup (v1) and future methods."""

    name: str = "consortium-method"

    @abstractmethod
    def combine(self, members: list[Member], out_dir: str, **config) -> str:
        """Combine `members` into a single model, write it to `out_dir`, return `out_dir`."""
        raise NotImplementedError
