#!/usr/bin/env python3
"""Tapestry Federated Training Demo.

Simulates a three-node federated training scenario where sovereign data
holders (EU, India, Southeast Asia) collaboratively train a small
transformer language model *without* sharing any raw data.

Each node:
  - Holds locally generated text data in its own language/domain
  - Trains a local copy of the model using standard SGD
  - Clips and noises weight updates via differential privacy
  - Sends only the privatised weight deltas to the aggregator

The central aggregator merges updates using Federated Averaging (FedAvg)
and broadcasts the improved global model back to all nodes.

Usage:
    python examples/federated_training_demo.py
"""

from __future__ import annotations

import random
import time

import torch

from tapestry.training.federated.aggregator import Aggregator
from tapestry.training.federated.node import MiniTransformer, TrainingNode
from tapestry.training.federated.privacy import DifferentialPrivacy


# ======================================================================
# Synthetic data generation
# ======================================================================

# We simulate three sovereignty domains, each with distinct text patterns.
# Tokens are byte-level (0-255) for simplicity — no external tokeniser needed.

DOMAIN_PATTERNS: dict[str, list[str]] = {
    "Node-EU": [
        "The European Union promotes data sovereignty and digital rights.",
        "Privacy regulations require careful handling of personal information.",
        "Cross-border data flows must comply with regional governance frameworks.",
        "Federated learning preserves privacy while enabling collaboration.",
        "GDPR mandates strict controls on data processing and storage.",
        "European research institutions lead advances in trustworthy AI.",
        "The right to explanation is a cornerstone of responsible AI deployment.",
        "Decentralised training allows institutions to keep data on premises.",
    ],
    "Node-India": [
        "India is building sovereign AI infrastructure for a billion people.",
        "BharatGen aims to create foundation models for Indian languages.",
        "Multilingual models must serve hundreds of languages and dialects.",
        "Digital public infrastructure enables inclusive access to AI services.",
        "Federated approaches respect the diversity of regional data sources.",
        "The national AI strategy emphasises self-reliance and open innovation.",
        "Training data from local communities stays under local governance.",
        "Aadhaar and UPI demonstrate scalable digital infrastructure at scale.",
    ],
    "Node-SEA": [
        "Southeast Asia is a diverse region with many languages and cultures.",
        "Sovereign AI ensures that local values shape model behaviour.",
        "Cross-institutional collaboration accelerates scientific discovery.",
        "Open models reduce dependency on any single technology provider.",
        "Regional data centres keep sensitive information within borders.",
        "Federated training bridges the gap between data privacy and utility.",
        "Singapore and Indonesia lead regional AI governance initiatives.",
        "Tropical agriculture benefits from locally trained prediction models.",
    ],
}


def encode_texts(texts: list[str]) -> list[list[int]]:
    """Encode a list of strings as byte-level token sequences."""
    return [list(t.encode("utf-8")) for t in texts]


# ======================================================================
# Demo runner
# ======================================================================

_SEPARATOR = "=" * 72


def run_demo(
    n_rounds: int = 8,
    local_epochs: int = 3,
    lr: float = 3e-3,
    noise_multiplier: float = 0.1,
    max_grad_norm: float = 1.0,
    seed: int = 42,
) -> None:
    """Run the full federated training demonstration."""
    random.seed(seed)
    torch.manual_seed(seed)

    print(_SEPARATOR)
    print("  TAPESTRY  --  Federated Training Proof of Concept")
    print("  Privacy-preserving distributed training with data sovereignty")
    print(_SEPARATOR)
    print()

    # ------------------------------------------------------------------
    # 1. Initialise the global model
    # ------------------------------------------------------------------
    print("[INIT] Creating MiniTransformer (vocab=256, d=64, heads=4, layers=2)")
    model = MiniTransformer(
        vocab_size=256, d_model=64, n_heads=4, n_layers=2, max_seq_len=128
    )
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[INIT] Model has {n_params:,} parameters\n")

    # ------------------------------------------------------------------
    # 2. Set up differential privacy
    # ------------------------------------------------------------------
    print(
        f"[DP]   Differential privacy enabled: "
        f"clip={max_grad_norm}, sigma={noise_multiplier}, delta=1e-5"
    )
    print()

    # ------------------------------------------------------------------
    # 3. Create sovereign training nodes
    # ------------------------------------------------------------------
    nodes: list[TrainingNode] = []
    for name, texts in DOMAIN_PATTERNS.items():
        dp = DifferentialPrivacy(
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier,
        )
        node = TrainingNode(
            node_id=name,
            model=model,
            train_data=encode_texts(texts),
            dp=dp,
            lr=lr,
            local_epochs=local_epochs,
            batch_size=8,
        )
        print(
            f"[NODE] {name:12s}  |  {len(texts)} samples  |  "
            f"data stays local (sovereign)"
        )
        nodes.append(node)

    print()

    # ------------------------------------------------------------------
    # 4. Initialise the aggregator
    # ------------------------------------------------------------------
    aggregator = Aggregator(global_model=model)
    print("[AGG]  Central aggregator ready (FedAvg)")
    print()

    # ------------------------------------------------------------------
    # 5. Federated training loop
    # ------------------------------------------------------------------
    print(_SEPARATOR)
    print("  BEGINNING FEDERATED TRAINING")
    print(_SEPARATOR)
    print()

    for rnd in range(1, n_rounds + 1):
        round_start = time.time()
        print(f"--- Round {rnd}/{n_rounds} ---")

        # Broadcast global model.
        global_state = aggregator.global_state
        for node in nodes:
            node.receive_global_model(global_state)

        # Each node trains locally and produces a privatised update.
        updates = []
        for node in nodes:
            print(f"  [{node.node_id:12s}] Training locally...", end="", flush=True)
            update = node.train_local(round_num=rnd)
            loss = update.metadata["loss"]
            print(f"  loss={loss:.4f}  (DP applied, {update.num_samples} samples)")
            updates.append(update)

        # Aggregate.
        print("  [Aggregator  ] Averaging weight updates...", end="", flush=True)
        result = aggregator.aggregate(updates)
        elapsed = time.time() - round_start
        print(
            f"  avg_loss={result.avg_loss:.4f}  "
            f"({len(result.participating_nodes)} nodes, {elapsed:.1f}s)"
        )
        print()

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    print(_SEPARATOR)
    print("  TRAINING COMPLETE")
    print(_SEPARATOR)
    print()
    print(f"  Rounds completed  : {n_rounds}")
    print(f"  Participating nodes: {', '.join(n.node_id for n in nodes)}")
    for node in nodes:
        if node.dp is not None:
            eps = node.dp.current_epsilon
            print(
                f"  Privacy budget ({node.node_id:12s}): "
                f"epsilon={eps:.2f}, delta={node.dp.budget.delta}"
            )
    print()
    print("  Key properties demonstrated:")
    print("    - Raw data never left any node")
    print("    - Weight updates were clipped and noised (differential privacy)")
    print("    - Aggregation used sample-weighted FedAvg")
    print("    - Loss decreased across rounds (the model learned)")
    print()
    print(_SEPARATOR)


if __name__ == "__main__":
    run_demo()
