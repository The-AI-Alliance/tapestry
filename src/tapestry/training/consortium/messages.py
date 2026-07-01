"""Message and artifact dataclasses for consortium training."""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

ModelState = dict[str, torch.Tensor]


@dataclass(frozen=True)
class SovereignModelArtifact:
    """Participant-owned model produced by a sovereign training cycle."""

    node_id: str
    jurisdiction: str
    stage: str
    model_state: ModelState
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SovereignContribution:
    """Governed contribution from a node back to the shared base."""

    node_id: str
    round_num: int
    local_model_state: ModelState
    quality_score: float
    token_count: int
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SovereignCycleResult:
    """Local sovereign output plus the contribution shared with the coordinator."""

    artifact: SovereignModelArtifact
    contribution: SovereignContribution


@dataclass(frozen=True)
class ConsortiumRoundResult:
    """Outcome of a coordinator integration round."""

    round_num: int
    previous_base_state: ModelState
    shared_base_state: ModelState
    accepted_nodes: list[str]
    rejected_nodes: list[str]
    contribution_weights: dict[str, float]
    outer_merge_strategy: str
