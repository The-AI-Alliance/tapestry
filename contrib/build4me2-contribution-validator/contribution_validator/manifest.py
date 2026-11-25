"""Signed contribution manifests.

A manifest is what a node signs about one contribution: its identity, the
round, the shared base it trained from, the fingerprint of the tensors it
contributes, and the quality score and token count the merge weights depend
on. The node signs the manifest's canonical encoding with its Ed25519 private
key. The coordinator verifies the signature with the public key it holds for
that member, then checks that the signed manifest matches the contribution it
arrived with.

This closes the gap the base fingerprint leaves open: a declared fingerprint is
a plain field anyone can copy, but a signed one binds the sender to the base and
to the exact weights. Verification trusts the roster of member keys it is given.
How those keys are distributed and rotated is out of scope here.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from typing import Any

import torch
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from tapestry.training.consortium import SovereignContribution, SovereignCycleResult
from tapestry.training.consortium.messages import ModelState

from .findings import FindingCode, ValidationFinding
from .fingerprint import (
    FingerprintedContribution,
    FingerprintingNode,
    declared_base_fingerprint,
    fingerprint_state,
    with_base_fingerprint,
)

# Part of the signed bytes, so a signature over a manifest can never be valid
# for any other message signed with the same key. Bump the version whenever the
# manifest fields change, so a signature over one layout never verifies as another.
MANIFEST_FORMAT = "tapestry-contribution-manifest/1"


@dataclass(frozen=True)
class ContributionManifest:
    """The statement a node signs about one contribution."""

    node_id: str
    round_num: int
    base_fingerprint: str
    contribution_fingerprint: str
    quality_score: float
    token_count: int

    def to_bytes(self) -> bytes:
        """Return the canonical encoding that is signed and verified.

        Sorted keys and fixed separators make the bytes independent of field
        order. Raises ``ValueError`` for a non-finite quality score, which
        strict JSON cannot represent.
        """
        encoded = {"format": MANIFEST_FORMAT, **asdict(self)}
        return json.dumps(encoded, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class SignedContribution(FingerprintedContribution):
    """A contribution carrying a manifest and the sender's signature over it.

    Like :class:`~contribution_validator.fingerprint.FingerprintedContribution`,
    this subclass keeps the core message untouched while the contract is
    reviewed.
    """

    manifest: ContributionManifest | None = None
    signature: bytes | None = None


def member_key_roster(member_keys: Mapping[str, Ed25519PublicKey]) -> dict[str, Ed25519PublicKey]:
    """Copy a ``node_id`` to public key roster, rejecting anything that is not an Ed25519 key."""
    roster = dict(member_keys)
    for node_id, key in roster.items():
        if not isinstance(key, Ed25519PublicKey):
            raise TypeError(f"signing key for member {node_id!r} is a {type(key).__name__}, not an Ed25519PublicKey")
    return roster


def sign_contribution(contribution: SovereignContribution, private_key: Ed25519PrivateKey) -> SignedContribution:
    """Return ``contribution`` with a manifest signed by ``private_key``.

    The contribution must already declare its base fingerprint (see
    :func:`~contribution_validator.fingerprint.with_base_fingerprint`), because
    the manifest signs that declaration.
    """
    base_fingerprint = declared_base_fingerprint(contribution)
    if base_fingerprint is None:
        raise ValueError(f"contribution from {contribution.node_id!r} must declare its base fingerprint to be signed")
    manifest = ContributionManifest(
        node_id=contribution.node_id,
        round_num=contribution.round_num,
        base_fingerprint=base_fingerprint,
        contribution_fingerprint=fingerprint_state(contribution.local_model_state),
        quality_score=contribution.quality_score,
        token_count=contribution.token_count,
    )
    fingerprinted = with_base_fingerprint(contribution, base_fingerprint)
    carried = {field.name: getattr(fingerprinted, field.name) for field in fields(FingerprintedContribution)}
    return SignedContribution(**carried, manifest=manifest, signature=private_key.sign(manifest.to_bytes()))


def verify_manifest(
    contribution: SovereignContribution,
    member_keys: Mapping[str, Ed25519PublicKey],
    round_num: int,
    base_fingerprint: str,
) -> list[ValidationFinding]:
    """Check a contribution's signed manifest and return any findings.

    The checks stop at the first of: no manifest, a sender with no registered
    key, or a signature that does not verify, because the manifest says nothing
    trustworthy after any of them. Otherwise every field that differs from the
    contribution, the round being run (``round_num``), or the shared base
    (``base_fingerprint``) is reported. The tensor fingerprint is not compared
    when the state holds non-tensors, since those are already rejected as
    ``not-a-tensor``.
    """
    manifest = getattr(contribution, "manifest", None)
    signature = getattr(contribution, "signature", None)
    if not isinstance(manifest, ContributionManifest) or not isinstance(signature, bytes):
        return [ValidationFinding(code=FindingCode.MANIFEST_MISSING, message="contribution has no signed manifest")]

    public_key = member_keys.get(contribution.node_id)
    if public_key is None:
        return [
            ValidationFinding(
                code=FindingCode.MANIFEST_SIGNER_UNKNOWN,
                message=f"node {contribution.node_id!r} has no registered signing key",
                details={"node_id": contribution.node_id},
            )
        ]

    try:
        public_key.verify(signature, manifest.to_bytes())
    except (InvalidSignature, TypeError, ValueError):
        return [
            ValidationFinding(
                code=FindingCode.MANIFEST_SIGNATURE_INVALID,
                message=f"manifest signature does not verify with the key registered for {contribution.node_id!r}",
                details={"node_id": contribution.node_id},
            )
        ]

    expected: dict[str, Any] = {
        "node_id": contribution.node_id,
        "round_num": round_num,
        "base_fingerprint": base_fingerprint,
        "quality_score": contribution.quality_score,
        "token_count": contribution.token_count,
    }
    state = contribution.local_model_state
    if all(isinstance(tensor, torch.Tensor) for tensor in state.values()):
        expected["contribution_fingerprint"] = fingerprint_state(state)
    return [
        ValidationFinding(
            code=FindingCode.MANIFEST_MISMATCH,
            message=f"signed manifest field {field!r} does not match the expected value",
            details={"field": field, "expected": value, "signed": getattr(manifest, field)},
        )
        for field, value in expected.items()
        if getattr(manifest, field) != value
    ]


class SigningNode(FingerprintingNode):  # pylint: disable=too-few-public-methods
    """A sovereign node that signs a manifest for every contribution it sends.

    Takes the same arguments as ``SovereignTrainingNode`` plus a keyword-only
    ``private_key``.
    """

    def __init__(self, *args: Any, private_key: Ed25519PrivateKey, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._private_key = private_key

    def run_sovereign_cycle(self, round_num: int, base_state: ModelState) -> SovereignCycleResult:
        """Run the fingerprinting cycle and sign the outgoing contribution."""
        result = super().run_sovereign_cycle(round_num, base_state)
        return SovereignCycleResult(
            artifact=result.artifact,
            contribution=sign_contribution(result.contribution, self._private_key),
        )
