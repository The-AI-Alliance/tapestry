"""Federated training node — a sovereign data holder.

Each ``TrainingNode`` represents an independent organisation (or region)
that owns private data. Training happens entirely within the node; only
clipped-and-noised weight *deltas* are released to the aggregator.

This module also provides a lightweight transformer-based language model
(``MiniTransformer``) suitable for demonstrating federated training on
text data without requiring large compute.
"""

from __future__ import annotations

import copy
import math
from typing import Sequence

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from tapestry.training.federated.privacy import DifferentialPrivacy
from tapestry.training.federated.protocols import NodeUpdate


# ======================================================================
# Model: a minimal causal transformer for next-token prediction
# ======================================================================


class MiniTransformer(nn.Module):
    """A tiny GPT-style transformer for demonstration purposes.

    Architecture:
        token_embedding  -> positional_embedding -> N transformer blocks
        -> layer_norm -> linear_head

    Each block is a standard pre-norm transformer decoder layer with
    causal (autoregressive) self-attention.

    Args:
        vocab_size: Number of tokens in the vocabulary.
        d_model: Hidden dimension throughout the model.
        n_heads: Number of attention heads.
        n_layers: Number of transformer blocks.
        max_seq_len: Maximum sequence length for positional embeddings.
        dropout: Dropout probability.
    """

    def __init__(
        self,
        vocab_size: int = 256,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        max_seq_len: int = 64,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_seq_len, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=n_layers
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

        # Weight tying: share embedding and output projection.
        self.head.weight = self.token_emb.weight

        self._init_weights()

    def _init_weights(self) -> None:
        """Small-init for stable training at tiny scale."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self, input_ids: torch.Tensor
    ) -> torch.Tensor:
        """Forward pass returning logits over the vocabulary.

        Args:
            input_ids: ``(batch, seq_len)`` integer token ids.

        Returns:
            Logits of shape ``(batch, seq_len, vocab_size)``.
        """
        seq_len = input_ids.size(1)
        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0)

        x = self.token_emb(input_ids) * math.sqrt(self.d_model)
        x = x + self.pos_emb(positions)

        # Causal mask: True means "mask this position".
        causal_mask = nn.Transformer.generate_square_subsequent_mask(
            seq_len, device=input_ids.device
        )
        x = self.transformer(x, mask=causal_mask, is_causal=True)
        x = self.ln_f(x)
        return self.head(x)


# ======================================================================
# Training Node
# ======================================================================


class TrainingNode:
    """A sovereign training node in the Tapestry federated network.

    Holds private local data, a local copy of the global model, and an
    optional differential-privacy engine. Exposes a ``train_local`` method
    that executes one round of local SGD and returns a ``NodeUpdate``
    containing only the (optionally privatised) weight delta.

    Args:
        node_id: Human-readable identifier, e.g. ``"Node-EU"``.
        model: The model architecture (will be deep-copied internally).
        train_data: Sequence of integer-encoded text samples (each a list
            of token ids).
        dp: Optional ``DifferentialPrivacy`` instance. When provided, all
            outgoing updates are clipped and noised.
        lr: Learning rate for local optimiser.
        local_epochs: Number of full passes over local data per round.
        batch_size: Mini-batch size for local SGD.
    """

    def __init__(
        self,
        node_id: str,
        model: nn.Module,
        train_data: Sequence[list[int]],
        dp: DifferentialPrivacy | None = None,
        lr: float = 1e-3,
        local_epochs: int = 2,
        batch_size: int = 16,
    ) -> None:
        self.node_id = node_id
        self.model = copy.deepcopy(model)
        self.dp = dp
        self.lr = lr
        self.local_epochs = local_epochs
        self.batch_size = batch_size

        self._dataloader = self._build_dataloader(train_data)

    # ------------------------------------------------------------------
    # FederatedProtocol interface
    # ------------------------------------------------------------------

    def receive_global_model(self, state_dict: dict[str, torch.Tensor]) -> None:
        """Replace the local model weights with the global aggregated model."""
        self.model.load_state_dict(state_dict)

    def train_local(self, round_num: int) -> NodeUpdate:
        """Execute local training and return a privatised weight update.

        Steps:
            1. Snapshot current (global) weights.
            2. Train for ``local_epochs`` on local data.
            3. Compute delta = trained_weights - snapshot.
            4. If DP is enabled, clip and noise the delta.
            5. Return the delta as a ``NodeUpdate``.
        """
        # Snapshot before training.
        pre_state = {
            k: v.clone() for k, v in self.model.state_dict().items()
        }

        # Local training.
        avg_loss = self._train_epochs()

        # Compute weight delta.
        post_state = self.model.state_dict()
        delta = {
            k: post_state[k] - pre_state[k] for k in pre_state
        }

        # Apply differential privacy if configured.
        if self.dp is not None:
            delta = self.dp.apply(delta)

        return NodeUpdate(
            node_id=self.node_id,
            round_num=round_num,
            state_delta=delta,
            num_samples=len(self._dataloader.dataset),  # type: ignore[arg-type]
            metadata={"loss": avg_loss},
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_dataloader(
        self, samples: Sequence[list[int]]
    ) -> DataLoader[tuple[torch.Tensor, ...]]:
        """Convert raw token lists into a PyTorch DataLoader."""
        # Pad / truncate to uniform length.
        max_len = max(len(s) for s in samples)
        padded = [s + [0] * (max_len - len(s)) for s in samples]
        tensor = torch.tensor(padded, dtype=torch.long)

        # Input is all tokens except last; target is all tokens except first.
        inputs = tensor[:, :-1]
        targets = tensor[:, 1:]

        dataset = TensorDataset(inputs, targets)
        return DataLoader(
            dataset, batch_size=self.batch_size, shuffle=True, drop_last=False
        )

    def _train_epochs(self) -> float:
        """Run ``local_epochs`` of SGD over local data. Returns avg loss."""
        self.model.train()
        optimiser = torch.optim.AdamW(self.model.parameters(), lr=self.lr)
        criterion = nn.CrossEntropyLoss()

        total_loss = 0.0
        total_steps = 0

        for _ in range(self.local_epochs):
            for input_ids, target_ids in self._dataloader:
                optimiser.zero_grad()
                logits = self.model(input_ids)
                # Flatten (batch*seq, vocab) vs (batch*seq,).
                loss = criterion(
                    logits.reshape(-1, logits.size(-1)),
                    target_ids.reshape(-1),
                )
                loss.backward()
                optimiser.step()

                total_loss += loss.item()
                total_steps += 1

        return total_loss / max(total_steps, 1)
