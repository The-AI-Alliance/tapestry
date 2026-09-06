"""Base-checkpoint fingerprints for consortium contributions.

A fingerprint is a deterministic SHA-256 digest of a model state: every tensor
name, dtype, shape, and raw little-endian bytes, in sorted name order. Two
states that hold the same values produce the same fingerprint regardless of
dict order, device, or memory layout.

Nodes declare the fingerprint of the shared base they trained from. The
validator compares that declaration with the fingerprint of the base the
coordinator actually published for the round, which catches a node that
started from a stale or otherwise wrong base.

This is an honesty check, not a security control. A node that lies about its
fingerprint is not caught here; that needs signed manifests, which remain
follow-up work.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace

import torch
from torch import nn

from tapestry.training.consortium import SovereignContribution, SovereignCycleResult, SovereignTrainingNode
from tapestry.training.consortium.messages import ModelState

FINGERPRINT_PREFIX = "sha256:"


def fingerprint_state(state: ModelState) -> str:
    """Return the fingerprint of a model state as ``sha256:<hex digest>``."""
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().to(device="cpu").contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(",".join(str(dim) for dim in tensor.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        digest.update(b"\0")
    return FINGERPRINT_PREFIX + digest.hexdigest()


def fingerprint_model(model: nn.Module) -> str:
    """Return the fingerprint of a module's current ``state_dict``."""
    return fingerprint_state(dict(model.state_dict()))


@dataclass(frozen=True)
class FingerprintedContribution(SovereignContribution):
    """A contribution that declares which shared base it was trained from.

    This subclass exists so the core ``SovereignContribution`` dataclass stays
    untouched while the contract is reviewed. Promotion would add
    ``base_fingerprint`` to the core message instead.
    """

    base_fingerprint: str | None = None


def declared_base_fingerprint(contribution: SovereignContribution) -> str | None:
    """The base fingerprint a contribution declares, or ``None`` if it declares none."""
    return getattr(contribution, "base_fingerprint", None)


class FingerprintingNode(SovereignTrainingNode):  # pylint: disable=too-few-public-methods
    """A sovereign node that declares the fingerprint of the base it trained from."""

    def run_sovereign_cycle(self, round_num: int, base_state: ModelState) -> SovereignCycleResult:
        """Run the normal cycle and attach the fingerprint of ``base_state``."""
        result = super().run_sovereign_cycle(round_num, base_state)
        return SovereignCycleResult(
            artifact=result.artifact,
            contribution=with_base_fingerprint(result.contribution, fingerprint_state(base_state)),
        )


class StaleBaseNode(FingerprintingNode):  # pylint: disable=too-few-public-methods
    """A node that keeps training from the first base it ever received.

    From the second round on, it ignores the base the coordinator sends and
    honestly declares the fingerprint of the stale base it used. This is the
    "trained from the wrong shared base" fault the fingerprint check exists to
    catch: a node whose sync failed, or that replayed an old checkpoint.
    """

    _stale_base: ModelState | None = None

    def run_sovereign_cycle(self, round_num: int, base_state: ModelState) -> SovereignCycleResult:
        """Train from the remembered first base instead of the one provided."""
        if self._stale_base is None:
            self._stale_base = {name: tensor.clone() for name, tensor in base_state.items()}
        return super().run_sovereign_cycle(round_num, self._stale_base)


def with_base_fingerprint(contribution: SovereignContribution, base_fingerprint: str) -> FingerprintedContribution:
    """Copy a contribution into a :class:`FingerprintedContribution` with the given declaration."""
    if isinstance(contribution, FingerprintedContribution):
        return replace(contribution, base_fingerprint=base_fingerprint)
    return FingerprintedContribution(
        node_id=contribution.node_id,
        round_num=contribution.round_num,
        local_model_state=contribution.local_model_state,
        quality_score=contribution.quality_score,
        token_count=contribution.token_count,
        metrics=contribution.metrics,
        base_fingerprint=base_fingerprint,
    )
