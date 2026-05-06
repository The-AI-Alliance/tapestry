"""Tapestry Federated Training Framework.

A privacy-preserving federated learning system that enables distributed model
training across sovereign data domains without exposing raw data. Implements
Federated Averaging (FedAvg) with differential privacy guarantees.

Architecture:
    - TrainingNode: Holds local data, trains locally, exports DP-protected updates
    - Aggregator: Collects and merges weight updates via federated averaging
    - DifferentialPrivacy: Gradient clipping and calibrated noise injection
    - FederatedProtocol: Communication interface between nodes and aggregator

Reference:
    McMahan et al., "Communication-Efficient Learning of Deep Networks
    from Decentralized Data" (2017) — FedAvg
    Abadi et al., "Deep Learning with Differential Privacy" (2016) — DP-SGD
"""

from tapestry.training.federated.aggregator import Aggregator
from tapestry.training.federated.node import TrainingNode
from tapestry.training.federated.privacy import DifferentialPrivacy
from tapestry.training.federated.protocols import (
    FederatedProtocol,
    NodeUpdate,
    RoundResult,
)

__all__ = [
    "Aggregator",
    "DifferentialPrivacy",
    "FederatedProtocol",
    "NodeUpdate",
    "RoundResult",
    "TrainingNode",
]
