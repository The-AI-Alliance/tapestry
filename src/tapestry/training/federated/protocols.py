"""Communication protocols and data structures for federated training.

Defines the interfaces and message types exchanged between training nodes
and the central aggregator. All communication is structured around weight
updates — raw data never leaves the node boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import torch


# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NodeUpdate:
    """A privacy-preserving weight update produced by a single training node.

    Contains only model parameter deltas (not raw data or activations).
    When differential privacy is enabled, these deltas have been clipped
    and noised before transmission.

    Attributes:
        node_id: Unique identifier for the originating node.
        round_num: The federated round this update belongs to.
        state_delta: Mapping from parameter name to the change in that
            parameter (new_weight - old_weight) after local training.
        num_samples: Number of local training samples used, for weighted
            aggregation.
        metadata: Optional provenance and diagnostics (e.g., local loss).
    """

    node_id: str
    round_num: int
    state_delta: dict[str, torch.Tensor]
    num_samples: int
    metadata: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RoundResult:
    """The outcome of a single federated training round.

    Attributes:
        round_num: Ordinal round number.
        aggregated_state: The new global model state dict after aggregation.
        participating_nodes: IDs of nodes that contributed updates.
        avg_loss: Weighted average loss across participating nodes.
    """

    round_num: int
    aggregated_state: dict[str, torch.Tensor]
    participating_nodes: list[str]
    avg_loss: float


# ---------------------------------------------------------------------------
# Protocol (structural typing interface)
# ---------------------------------------------------------------------------


@runtime_checkable
class FederatedProtocol(Protocol):
    """Interface that any federated training participant must satisfy."""

    @property
    def node_id(self) -> str:
        """Unique identifier for this participant."""
        ...

    def receive_global_model(self, state_dict: dict[str, torch.Tensor]) -> None:
        """Accept a new global model state from the aggregator."""
        ...

    def train_local(self, round_num: int) -> NodeUpdate:
        """Run one round of local training and return a weight update."""
        ...
