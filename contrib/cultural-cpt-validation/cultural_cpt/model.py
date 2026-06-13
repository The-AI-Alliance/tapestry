"""Language-model backends for the cultural-CPT validation harness.

Two backends share one ``LanguageModel`` protocol so the experiment code is
identical regardless of scale:

- ``ByteCausalModel`` — a byte-level toy model (vocab 256) used for **smoke
  mode**. It makes the full pipeline (arms -> CPT -> instrument -> scoring ->
  comparison) runnable in CI without GPUs or downloads. Its coordinates are
  noise; it validates plumbing, not the hypothesis.
- ``HFCausalModel`` — a real Hugging Face causal LM (Qwen/Llama/Mistral class)
  for **real mode**. This is where the actual EXP-001 signal comes from. It is
  a documented stub until `transformers` is added as a dependency.
"""

from __future__ import annotations

import copy
import math
from typing import Protocol, Sequence, runtime_checkable

import torch
from torch import nn

from tapestry.training.consortium import TinyCausalModel

_BYTE_VOCAB = 256


@runtime_checkable
class LanguageModel(Protocol):
    """Minimal interface the experiment needs from any model backend."""

    def train_on_texts(self, texts: Sequence[str], *, epochs: int, lr: float) -> float:
        """Continued-pretrain on raw text. Returns mean training loss."""
        ...

    def score_continuation(self, prompt: str, continuation: str) -> float:
        """Mean per-token log-probability of ``continuation`` given ``prompt``.

        This is the single primitive both instruments rely on: the WVS survey
        scores each answer option this way, and the capability probe scores each
        multiple-choice answer this way.
        """
        ...

    def clone(self) -> "LanguageModel":
        """Return an independent copy (so each arm starts from the same base)."""
        ...


class ByteCausalModel:
    """Byte-level toy causal LM for smoke runs.

    Wraps :class:`TinyCausalModel` so the harness reuses the existing consortium
    PoC model. Text is UTF-8 byte-encoded, giving a fixed 256-token vocabulary
    shared across all arms (so base and continued-pretrained models stay
    comparable).
    """

    def __init__(self, hidden_size: int = 64, seed: int = 0) -> None:
        torch.manual_seed(seed)
        self._net = TinyCausalModel(vocab_size=_BYTE_VOCAB, hidden_size=hidden_size)
        self._hidden_size = hidden_size
        self._seed = seed

    @staticmethod
    def _encode(text: str) -> list[int]:
        return list(text.encode("utf-8")) or [0]

    def clone(self) -> "ByteCausalModel":
        twin = ByteCausalModel.__new__(ByteCausalModel)
        twin._net = copy.deepcopy(self._net)
        twin._hidden_size = self._hidden_size
        twin._seed = self._seed
        return twin

    def train_on_texts(self, texts: Sequence[str], *, epochs: int, lr: float) -> float:
        sequences = [self._encode(t) for t in texts if t.strip()]
        sequences = [s for s in sequences if len(s) >= 2]
        if not sequences:
            raise ValueError("no usable training text")

        self._net.train()
        optimizer = torch.optim.AdamW(self._net.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()
        total, steps = 0.0, 0
        for _ in range(epochs):
            for seq in sequences:
                ids = torch.tensor(seq, dtype=torch.long).unsqueeze(0)
                optimizer.zero_grad()
                logits = self._net(ids[:, :-1])
                loss = criterion(logits.reshape(-1, _BYTE_VOCAB), ids[:, 1:].reshape(-1))
                loss.backward()
                optimizer.step()
                total += loss.item()
                steps += 1
        return total / max(steps, 1)

    @torch.no_grad()
    def score_continuation(self, prompt: str, continuation: str) -> float:
        self._net.eval()
        prompt_ids = self._encode(prompt)
        cont_ids = self._encode(continuation)
        ids = torch.tensor(prompt_ids + cont_ids, dtype=torch.long).unsqueeze(0)
        logits = self._net(ids[:, :-1])
        log_probs = torch.log_softmax(logits, dim=-1).squeeze(0)
        # Score only the continuation tokens.
        start = len(prompt_ids) - 1
        targets = ids[0, 1:]
        total = 0.0
        for pos in range(start, targets.numel()):
            total += log_probs[pos, targets[pos]].item()
        n = max(len(cont_ids), 1)
        return total / n if not math.isnan(total) else float("-inf")


class HFCausalModel:
    """Real Hugging Face causal LM backend (real mode). Documented stub.

    Wiring this up is the single change that turns the harness from a plumbing
    test into a real EXP-001 run. It requires adding `transformers` (and likely
    `accelerate`) to the project dependencies. ``score_continuation`` is a
    standard teacher-forced log-prob and ``train_on_texts`` is a short CPT loop;
    both are intentionally left unimplemented so no one mistakes a stub for a
    result.
    """

    def __init__(self, model_name: str, device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device

    def _unavailable(self) -> "NotImplementedError":
        return NotImplementedError(
            "HFCausalModel is a stub. To enable real mode: add `transformers` to "
            "the project deps, load AutoModelForCausalLM/AutoTokenizer for "
            f"'{self.model_name}', implement train_on_texts as a CPT loop and "
            "score_continuation as a teacher-forced log-prob over the "
            "continuation tokens (mirroring ByteCausalModel)."
        )

    def clone(self) -> "HFCausalModel":  # pragma: no cover - stub
        raise self._unavailable()

    def train_on_texts(self, texts: Sequence[str], *, epochs: int, lr: float) -> float:  # pragma: no cover - stub
        raise self._unavailable()

    def score_continuation(self, prompt: str, continuation: str) -> float:  # pragma: no cover - stub
        raise self._unavailable()


def make_base_model(mode: str, *, hidden_size: int = 64, seed: int = 0, model_name: str = "") -> LanguageModel:
    """Build the shared base model all arms start from."""
    if mode == "smoke":
        return ByteCausalModel(hidden_size=hidden_size, seed=seed)
    if mode == "hf":
        if not model_name:
            raise ValueError("hf mode requires --model-name")
        return HFCausalModel(model_name=model_name)
    raise ValueError(f"unknown mode: {mode!r} (expected 'smoke' or 'hf')")
