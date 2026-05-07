"""Consortium-training proof of concept for Project Tapestry.

This package models the Tapestry-specific training loop described in the ADRs:
one governed shared base plus N participant-owned sovereign model artifacts.
Nodes train locally on sovereign corpora and share only weight deltas for
governed integration back into the shared base.
"""

from .coordinator import ConsortiumCoordinator
from .model import TinyCausalModel
from .node import SovereignTrainingNode
from .policy import ContributionPolicy
from .messages import (
    ConsortiumRoundResult,
    SovereignContribution,
    SovereignCycleResult,
    SovereignModelArtifact,
)

__all__ = [
    "ConsortiumCoordinator",
    "ConsortiumRoundResult",
    "ContributionPolicy",
    "SovereignContribution",
    "SovereignCycleResult",
    "SovereignModelArtifact",
    "SovereignTrainingNode",
    "TinyCausalModel",
]
