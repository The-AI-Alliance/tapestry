"""Consortium-training proof of concept for Project Tapestry.

This package models the Tapestry-specific Shared-Base Loop described in the ADRs:
one governed shared base plus N participant-owned sovereign model artifacts.
Nodes train locally on sovereign corpora (Contributed CPT) and share local model
weight vectors for FedAvg-class integration back into the shared base.
"""

from .coordinator import ConsortiumCoordinator
from .merge import OuterMergeOptimizer, OuterMergeStrategy
from .model import TinyCausalModel
from .node import SovereignTrainingNode
from .policy import ContributionPolicy, ContributionWeighting
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
    "ContributionWeighting",
    "OuterMergeOptimizer",
    "OuterMergeStrategy",
    "SovereignContribution",
    "SovereignCycleResult",
    "SovereignModelArtifact",
    "SovereignTrainingNode",
    "TinyCausalModel",
]
