"""Compatibility exports for consortium-training message dataclasses.

Prefer importing from ``tapestry.training.consortium.messages`` in new code.
This module exists so older imports of ``tapestry.training.consortium.types``
continue to resolve cleanly in editors and tooling.
"""

from .messages import (
    ConsortiumRoundResult,
    ModelState,
    SovereignContribution,
    SovereignCycleResult,
    SovereignModelArtifact,
)

__all__ = [
    "ConsortiumRoundResult",
    "ModelState",
    "SovereignContribution",
    "SovereignCycleResult",
    "SovereignModelArtifact",
]
