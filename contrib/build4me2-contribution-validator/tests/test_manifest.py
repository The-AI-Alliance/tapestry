"""Tests for signed contribution manifests and their use in validation."""

# pylint: disable=wrong-import-position,wrong-import-order,duplicate-code

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from contribution_validator import (
    ContributionValidator,
    FindingCode,
    SignedContribution,
    SigningNode,
    ValidatingConsortiumCoordinator,
    fingerprint_state,
    sign_contribution,
    with_base_fingerprint,
)
from contribution_validator.manifest import MANIFEST_FORMAT
from contribution_validator.testing import base_state as _base_state
from contribution_validator.testing import last_summary as _summary
from contribution_validator.testing import tiny_model as _model
from contribution_validator.testing import toy_corpus as _corpus

from tapestry.training.consortium import SovereignContribution
from tapestry.training.consortium.messages import ModelState


def _key(seed: int) -> Ed25519PrivateKey:
    """A deterministic key, so failures reproduce."""
    return Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32)


KEYS = {"node": _key(1), "other": _key(2)}
ROSTER = {node_id: key.public_key() for node_id, key in KEYS.items()}


def _signed(state: ModelState, round_num: int = 1, node_id: str = "node", key_seed: int = 1) -> SignedContribution:
    plain = SovereignContribution(
        node_id=node_id, round_num=round_num, local_model_state=state, quality_score=0.9, token_count=8
    )
    return sign_contribution(with_base_fingerprint(plain, fingerprint_state(_base_state())), _key(key_seed))


def _validator(round_num: int = 1) -> ContributionValidator:
    return ContributionValidator(_base_state(), member_keys=ROSTER, round_num=round_num)


def test_signed_contribution_from_a_member_is_accepted() -> None:
    """A member's manifest, signed for this round and matching its weights, passes."""
    report = _validator().validate(_signed(_base_state()))

    assert report.accepted, report.finding_codes


def test_manifest_encoding_is_canonical_and_tagged() -> None:
    """The signed bytes are compact sorted JSON that names the manifest format."""
    manifest = _signed(_base_state()).manifest
    assert manifest is not None

    encoded = json.loads(manifest.to_bytes())
    assert encoded["format"] == MANIFEST_FORMAT
    assert manifest.to_bytes() == json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_unsigned_contribution_is_rejected() -> None:
    """With a roster, a contribution without a signed manifest is not admitted."""
    plain = SovereignContribution(
        node_id="node", round_num=1, local_model_state=_base_state(), quality_score=0.9, token_count=8
    )
    report = _validator().validate(plain)

    assert report.finding_codes == (FindingCode.MANIFEST_MISSING,)


def test_sender_without_a_registered_key_is_rejected() -> None:
    """A correctly signed contribution from a node outside the roster is not admitted."""
    report = _validator().validate(_signed(_base_state(), node_id="outsider", key_seed=9))

    assert report.finding_codes == (FindingCode.MANIFEST_SIGNER_UNKNOWN,)
    assert report.findings[0].details == {"node_id": "outsider"}


def test_impersonating_a_member_is_rejected() -> None:
    """A manifest naming a member but signed with another key does not verify."""
    report = _validator().validate(_signed(_base_state(), node_id="node", key_seed=2))

    assert report.finding_codes == (FindingCode.MANIFEST_SIGNATURE_INVALID,)


def test_editing_a_signed_manifest_breaks_the_signature() -> None:
    """Changing any manifest field after signing invalidates the signature."""
    signed = _signed(_base_state())
    assert signed.manifest is not None
    tampered = replace(signed, manifest=replace(signed.manifest, quality_score=1.0))

    assert _validator().validate(tampered).finding_codes == (FindingCode.MANIFEST_SIGNATURE_INVALID,)


def test_weights_changed_after_signing_are_rejected() -> None:
    """Weights that differ from the signed fingerprint are reported as a mismatch."""
    signed = _signed(_base_state())
    altered = {name: tensor.clone() for name, tensor in signed.local_model_state.items()}
    next(iter(altered.values())).view(-1)[0] += 1e-3
    report = _validator().validate(replace(signed, local_model_state=altered))

    assert report.finding_codes == (FindingCode.MANIFEST_MISMATCH,)
    assert report.findings[0].details["field"] == "contribution_fingerprint"


def test_score_changed_after_signing_is_rejected() -> None:
    """The quality score drives merge weights, so it is bound by the signature too."""
    report = _validator().validate(replace(_signed(_base_state()), quality_score=1.0))

    assert report.finding_codes == (FindingCode.MANIFEST_MISMATCH,)
    assert report.findings[0].details == {"field": "quality_score", "expected": 1.0, "signed": 0.9}


def test_replay_in_a_later_round_is_rejected() -> None:
    """A manifest signed for round 1 is not accepted in round 2, even against the same base."""
    report = _validator(round_num=2).validate(_signed(_base_state(), round_num=1))

    assert report.finding_codes == (FindingCode.MANIFEST_MISMATCH,)
    assert report.findings[0].details == {"field": "round_num", "expected": 2, "signed": 1}


def test_signed_false_base_claim_is_attributable_but_not_detected() -> None:
    """A signature proves who declared the base, not that the declaration is true.

    This pins the limit of the check: a member that trains from the wrong base
    and signs the correct digest is still admitted, but the false claim is now
    signed by that member.
    """
    wrong_base = _base_state(seed=1)
    report = _validator().validate(_signed(wrong_base))

    assert report.accepted, report.finding_codes


def test_unencodable_manifest_is_rejected_without_raising() -> None:
    """A manifest that cannot be encoded, such as one with a NaN score, fails verification."""
    signed = _signed(_base_state())
    assert signed.manifest is not None
    nan_manifest = replace(signed, manifest=replace(signed.manifest, quality_score=float("nan")))

    assert _validator().validate(nan_manifest).finding_codes == (FindingCode.MANIFEST_SIGNATURE_INVALID,)


def test_non_tensor_values_are_rejected_without_raising() -> None:
    """A signed contribution holding a non-tensor gets the usual finding, not an exception."""
    signed = _signed(_base_state())
    name = next(iter(signed.local_model_state))
    broken = replace(signed, local_model_state={**signed.local_model_state, name: [0.0]})
    report = _validator().validate(broken)

    assert report.finding_codes == (FindingCode.NOT_A_TENSOR,)


def test_configuration_errors_fail_early() -> None:
    """Bad rosters and raw-state validation are refused before any contribution is admitted."""
    not_a_key: dict[str, Any] = {"node": b"not a key"}
    with pytest.raises(ValueError, match="round_num is required"):
        ContributionValidator(_base_state(), member_keys=ROSTER)
    with pytest.raises(TypeError, match="not an Ed25519PublicKey"):
        ContributionValidator(_base_state(), member_keys=not_a_key, round_num=1)
    with pytest.raises(TypeError, match="not an Ed25519PublicKey"):
        ValidatingConsortiumCoordinator(_model(), member_keys=not_a_key)
    with pytest.raises(ValueError, match="requires signed manifests"):
        _validator().validate_state("node", 1, _base_state())
    with pytest.raises(ValueError, match="must declare its base fingerprint"):
        sign_contribution(
            SovereignContribution(
                node_id="node", round_num=1, local_model_state=_base_state(), quality_score=0.9, token_count=8
            ),
            KEYS["node"],
        )


def test_gate_admits_signed_members_and_records_forgery() -> None:
    """Across rounds, signing members merge and an impersonator is rejected with a recorded finding."""
    model = _model()

    def node(node_id: str, key_seed: int, offset: int) -> SigningNode:
        return SigningNode(node_id, node_id, model, _corpus(offset), 0.9, private_key=_key(key_seed), local_epochs=1)

    coordinator = ValidatingConsortiumCoordinator(model, member_keys=ROSTER)
    nodes = [node("node", 1, 0), node("other", 2, 10)]
    for _ in range(2):
        result = coordinator.run_round(nodes)
        assert result.accepted_nodes == ["node", "other"]

    previous = {name: tensor.clone() for name, tensor in coordinator.shared_base_state.items()}
    result = coordinator.run_round([nodes[0], node("other", 9, 10)])

    assert result.accepted_nodes == ["node"]
    assert result.rejected_nodes == ["other"]
    assert not torch.equal(next(iter(previous.values())), next(iter(coordinator.shared_base_state.values())))
    recorded = json.loads(json.dumps(_summary(coordinator).to_dict()))
    assert recorded["validation_rejected_nodes"] == ["other"]
    assert recorded["reports"]["other"]["findings"][0]["code"] == FindingCode.MANIFEST_SIGNATURE_INVALID
