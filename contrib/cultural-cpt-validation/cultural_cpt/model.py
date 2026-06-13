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


def _make_adamw(params, *, lr: float):
    """AdamW optimizer, preferring bitsandbytes 8-bit when available.

    8-bit Adam keeps the optimizer moments in int8 (~2 bytes/param vs. 8 for
    fp32), which is what lets a ~4B full fine-tune fit a single 32GB GPU. It is
    still full-parameter training (every weight gets a gradient) -- not LoRA --
    so the depth-over-shallow test is unchanged. Falls back to torch AdamW (e.g.
    on CPU / smoke) when bitsandbytes is absent.
    """
    try:
        import bitsandbytes as bnb

        return bnb.optim.AdamW8bit(params, lr=lr)
    except Exception:  # pragma: no cover - depends on optional dep / GPU
        return torch.optim.AdamW(params, lr=lr)


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

    def generate(self, prompt: str, *, max_new_tokens: int = 64) -> str:
        """Free-form continuation of ``prompt`` (greedy). Used by the behavioral
        probe's generate mode, where the model acts in an open-ended scenario
        instead of choosing among fixed options."""
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

    def state(self) -> dict[str, torch.Tensor]:
        """Clone of the underlying weight vector (for FedAvg aggregation)."""
        return {name: tensor.clone() for name, tensor in self._net.state_dict().items()}

    def load_state(self, state: dict[str, torch.Tensor]) -> None:
        """Load an aggregated weight vector back into the model."""
        self._net.load_state_dict(state)

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

    @torch.no_grad()
    def generate(self, prompt: str, *, max_new_tokens: int = 64) -> str:
        """Greedy byte-by-byte continuation. Smoke output is gibberish (it
        exercises the generate->judge plumbing, not real behavior)."""
        self._net.eval()
        ids = self._encode(prompt)
        out: list[int] = []
        for _ in range(max_new_tokens):
            x = torch.tensor(ids + out, dtype=torch.long).unsqueeze(0)
            nxt = int(torch.argmax(self._net(x)[0, -1]).item())
            out.append(nxt)
        return bytes(out).decode("utf-8", errors="ignore")


class HFCausalModel:
    """Real Hugging Face causal LM backend (real mode).

    Turns the harness from a plumbing test into a real EXP-001 run.
    ``transformers`` is a lazily-imported optional dependency (see the contrib
    README); install it to use this backend. ``score_continuation`` is a
    teacher-forced mean log-prob over the continuation tokens and
    ``train_on_texts`` is a short continued-pretraining loop — the same two
    primitives the toy backend provides, so the experiment code is unchanged.

    For real cultural signal, pass a proper base/instruct model and real
    corpora. A small model (e.g. ``distilgpt2``) is enough to validate wiring.
    """

    def __init__(self, model_name: str, device: str = "cpu", dtype: str = "float32", max_length: int = 1024) -> None:
        self.model_name = model_name
        self.device = device
        self.dtype = dtype
        # CPT context window. Long documents are chunked into windows of this
        # many tokens; bounds activation memory (a whole Wikipedia article in one
        # backward pass OOMs even a 32GB GPU on a 1.5B model).
        self.max_length = max_length
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError(
                "real mode needs `transformers`; install it (e.g. "
                "`uv pip install transformers`) or use --mode smoke."
            ) from exc
        # bf16 halves the memory of a full-parameter CPT run (params + grads),
        # the difference between fitting a ~4B base on a single GPU or not.
        #
        # The base stays on the CPU; only the per-arm clones move to the compute
        # device (see clone()). The experiment never computes on the base
        # directly (every arm clones it), so this keeps just ONE model copy in
        # VRAM at a time -- essential to fit a 4B full fine-tune in 32GB.
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForCausalLM.from_pretrained(model_name, dtype=getattr(torch, dtype))
        self._model.eval()

    def _shared_init(self, tokenizer, model) -> "HFCausalModel":
        twin = HFCausalModel.__new__(HFCausalModel)
        twin.model_name = self.model_name
        twin.device = self.device
        twin.dtype = self.dtype
        twin.max_length = self.max_length
        twin._tokenizer = tokenizer
        twin._model = model
        return twin

    def clone(self) -> "HFCausalModel":
        # Tokenizer is stateless and shared; the model weights are copied so each
        # arm trains independently from the same base. The base lives on CPU; the
        # copy is moved to the compute device so only one model occupies VRAM.
        # empty_cache first releases the previous arm's freed allocations.
        if self.device != "cpu" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        twin_model = copy.deepcopy(self._model).to(self.device)
        return self._shared_init(self._tokenizer, twin_model)

    def _device(self) -> "torch.device":
        """The device the weights actually live on (CPU for base, GPU for clones)."""
        return next(self._model.parameters()).device

    def _encode(self, text: str) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def train_on_texts(self, texts: Sequence[str], *, epochs: int, lr: float) -> float:
        # Chunk each document into max_length windows so long articles become
        # several training sequences instead of one OOM-inducing pass.
        sequences: list[list[int]] = []
        for text in texts:
            if not text.strip():
                continue
            toks = self._encode(text)
            for start in range(0, len(toks), self.max_length):
                window = toks[start : start + self.max_length]
                if len(window) >= 2:
                    sequences.append(window)
        if not sequences:
            raise ValueError("no usable training text")

        # Gradient checkpointing trades compute for memory (recomputes
        # activations in the backward pass); needs use_cache off.
        dev = self._device()
        self._model.train()
        self._model.config.use_cache = False
        self._model.gradient_checkpointing_enable()
        optimizer = _make_adamw(self._model.parameters(), lr=lr)
        total, steps = 0.0, 0
        for _ in range(epochs):
            for seq in sequences:
                ids = torch.tensor([seq], dtype=torch.long, device=dev)
                optimizer.zero_grad()
                loss = self._model(input_ids=ids, labels=ids).loss
                loss.backward()
                optimizer.step()
                total += loss.item()
                steps += 1
        del optimizer
        self._model.gradient_checkpointing_disable()
        self._model.config.use_cache = True
        self._model.eval()
        if dev.type == "cuda":
            torch.cuda.empty_cache()
        return total / max(steps, 1)

    @torch.no_grad()
    def score_continuation(self, prompt: str, continuation: str) -> float:
        prompt_ids = self._encode(prompt)
        cont_ids = self._encode(continuation)
        if not cont_ids:
            return float("-inf")
        full = prompt_ids + cont_ids
        ids = torch.tensor([full], dtype=torch.long, device=self._device())
        log_probs = torch.log_softmax(self._model(input_ids=ids).logits[0], dim=-1)
        total = 0.0
        # Token at position j is predicted by logits at j-1.
        for j in range(len(prompt_ids), len(full)):
            total += log_probs[j - 1, full[j]].item()
        return total / len(cont_ids)

    @torch.no_grad()
    def generate(self, prompt: str, *, max_new_tokens: int = 64) -> str:
        """Greedy free-form continuation (deterministic), decoded to text."""
        dev = self._device()
        ids = torch.tensor([self._encode(prompt)], dtype=torch.long, device=dev)
        out = self._model.generate(
            ids,
            attention_mask=torch.ones_like(ids),  # single unpadded seq; silences pad==eos warning
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            pad_token_id=self._tokenizer.pad_token_id or self._tokenizer.eos_token_id,
        )
        new_tokens = out[0, ids.shape[1] :].tolist()
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)


def make_base_model(
    mode: str,
    *,
    hidden_size: int = 64,
    seed: int = 0,
    model_name: str = "",
    device: str = "cpu",
    dtype: str = "float32",
) -> LanguageModel:
    """Build the shared base model all arms start from."""
    if mode == "smoke":
        return ByteCausalModel(hidden_size=hidden_size, seed=seed)
    if mode == "hf":
        if not model_name:
            raise ValueError("hf mode requires --model-name")
        return HFCausalModel(model_name=model_name, device=device, dtype=dtype)
    raise ValueError(f"unknown mode: {mode!r} (expected 'smoke' or 'hf')")
