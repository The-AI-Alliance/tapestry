"""Tiny model used by the consortium-training proof of concept."""

from __future__ import annotations

import torch
from torch import nn


class TinyCausalModel(nn.Module):
    """Small next-token model used to keep the PoC fast and testable."""

    def __init__(self, vocab_size: int = 256, hidden_size: int = 32) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.proj = nn.Linear(hidden_size, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Return next-token logits for ``(batch, sequence)`` token ids."""
        return self.proj(self.embedding(input_ids))
