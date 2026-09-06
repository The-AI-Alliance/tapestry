"""Tests for base-checkpoint fingerprints and their use in validation."""

# pylint: disable=wrong-import-position,wrong-import-order,duplicate-code

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from contribution_validator import (
    ContributionValidator,
    FindingCode,
    FingerprintedContribution,
    FingerprintingNode,
    FingerprintPolicy,
    StaleBaseNode,
    ValidatingConsortiumCoordinator,
    ValidationLimits,
    declared_base_fingerprint,
    fingerprint_model,
    fingerprint_state,
    validate_contribution,
    with_base_fingerprint,
)
from contribution_validator.testing import base_state as _base_state
from contribution_validator.testing import tiny_model as _model
from contribution_validator.testing import toy_corpus as _corpus

from tapestry.training.consortium import SovereignContribution, SovereignTrainingNode
from tapestry.training.consortium.messages import ModelState


def _contribution(state: ModelState, base_fingerprint: str | None = None) -> SovereignContribution:
    plain = SovereignContribution(
        node_id="node", round_num=1, local_model_state=state, quality_score=0.9, token_count=8
    )
    return plain if base_fingerprint is None else with_base_fingerprint(plain, base_fingerprint)


def test_fingerprint_is_deterministic_and_order_independent() -> None:
    """The same values give the same digest regardless of dict order, device, or layout."""
    base = _base_state()
    reference = fingerprint_state(base)

    assert reference.startswith("sha256:")
    assert len(reference) == len("sha256:") + 64
    assert fingerprint_state(dict(reversed(list(base.items())))) == reference
    assert fingerprint_state({name: tensor.clone() for name, tensor in base.items()}) == reference
    non_contiguous = {
        name: torch.cat([tensor, tensor], dim=1)[:, : tensor.shape[1]] if tensor.dim() == 2 else tensor
        for name, tensor in base.items()
    }
    assert not all(tensor.is_contiguous() for tensor in non_contiguous.values())
    assert fingerprint_state(non_contiguous) == reference
    assert fingerprint_model(_model()) == reference


def test_fingerprint_changes_with_any_value_name_dtype_or_shape() -> None:
    """A single-element change, or any metadata change, gives a different digest."""
    base = _base_state()
    reference = fingerprint_state(base)
    name = next(iter(base))

    one_value = {k: v.clone() for k, v in base.items()}
    one_value[name].view(-1)[0] += 1e-6
    assert fingerprint_state(one_value) != reference

    renamed = {("x." + k if k == name else k): v for k, v in base.items()}
    assert fingerprint_state(renamed) != reference

    recast = {k: (v.to(torch.float64) if k == name else v) for k, v in base.items()}
    assert fingerprint_state(recast) != reference

    reshaped = {k: (v.reshape(-1) if k == name else v) for k, v in base.items()}
    assert fingerprint_state(reshaped) != reference


def test_fingerprint_handles_unusual_tensors() -> None:
    """Scalars, integer buffers, bfloat16, and non-finite values all hash."""
    state = {
        "scalar": torch.tensor(3.5),
        "steps": torch.tensor([7], dtype=torch.int64),
        "half": torch.ones(3, dtype=torch.bfloat16),
        "mask": torch.full((2, 2), float("-inf")).triu(1),
        "nan": torch.tensor([float("nan")]),
    }
    first = fingerprint_state(state)
    second = fingerprint_state({k: v.clone() for k, v in state.items()})
    assert first == second

    flipped = {k: v.clone() for k, v in state.items()}
    flipped["steps"][0] = 8
    assert fingerprint_state(flipped) != first


def test_matching_declared_fingerprint_is_accepted() -> None:
    """A contribution that declares the round's base fingerprint passes the check."""
    base = _base_state()
    contribution = _contribution(dict(base), fingerprint_state(base))

    report = validate_contribution(base, contribution)

    assert report.accepted
    assert isinstance(contribution, FingerprintedContribution)


def test_mismatched_fingerprint_is_rejected_with_both_digests() -> None:
    """A contribution trained from another base is rejected and the report shows both digests."""
    base = _base_state()
    other = {k: v + 1.0 for k, v in base.items()}
    stale = fingerprint_state(other)

    report = validate_contribution(base, _contribution(dict(base), stale))

    assert not report.accepted
    assert report.finding_codes == (FindingCode.BASE_FINGERPRINT_MISMATCH,)
    assert report.findings[0].tensor_name is None
    assert report.findings[0].details == {"expected": fingerprint_state(base), "declared": stale}


def test_fingerprint_policy_controls_missing_declarations() -> None:
    """if-present accepts an undeclared fingerprint, require rejects it, ignore skips mismatches."""
    base = _base_state()
    undeclared = _contribution(dict(base))
    wrong = _contribution(dict(base), "sha256:" + "0" * 64)

    assert validate_contribution(base, undeclared).accepted
    assert validate_contribution(base, undeclared, ValidationLimits(fingerprint_policy="if-present")).accepted

    required = validate_contribution(base, undeclared, ValidationLimits(fingerprint_policy="require"))
    assert required.finding_codes == (FindingCode.BASE_FINGERPRINT_MISSING,)
    assert required.findings[0].details == {"expected": fingerprint_state(base)}

    ignored = validate_contribution(base, wrong, ValidationLimits(fingerprint_policy=FingerprintPolicy.IGNORE))
    assert ignored.accepted

    with pytest.raises(ValueError):
        ValidationLimits(fingerprint_policy="sometimes")


def test_fingerprint_check_runs_alongside_the_other_checks() -> None:
    """A wrong base and a NaN both show up in one report."""
    base = _base_state()
    state = {k: v.clone() for k, v in base.items()}
    next(iter(state.values())).view(-1)[0] = float("nan")

    report = validate_contribution(base, _contribution(state, "sha256:" + "f" * 64))

    assert set(report.finding_codes) == {FindingCode.BASE_FINGERPRINT_MISMATCH, FindingCode.NON_FINITE}


def test_validator_caches_the_reference_fingerprint() -> None:
    """The digest is computed once per validator and matches a fresh computation."""
    base = _base_state()
    validator = ContributionValidator(base)

    first = validator.reference_fingerprint
    assert first == fingerprint_state(base)
    assert validator.reference_fingerprint is first


def test_with_base_fingerprint_preserves_the_contribution() -> None:
    """Wrapping a plain contribution keeps every field, and re-wrapping replaces the declaration."""
    base = _base_state()
    plain = _contribution(dict(base))
    wrapped = with_base_fingerprint(plain, "sha256:" + "a" * 64)

    assert wrapped.node_id == plain.node_id
    assert wrapped.round_num == plain.round_num
    assert wrapped.local_model_state is plain.local_model_state
    assert wrapped.quality_score == plain.quality_score
    assert wrapped.token_count == plain.token_count
    assert wrapped.base_fingerprint == "sha256:" + "a" * 64

    rewrapped = with_base_fingerprint(wrapped, "sha256:" + "b" * 64)
    assert rewrapped.base_fingerprint == "sha256:" + "b" * 64
    assert rewrapped.node_id == plain.node_id


def test_fingerprinting_node_declares_the_base_it_received() -> None:
    """A fingerprinting node's contribution carries the digest of the base it started from."""
    torch.manual_seed(1)
    node = FingerprintingNode("a", "A", _model(), _corpus(), 0.9, local_epochs=1, lr=0.01)
    base = _base_state()

    result = node.run_sovereign_cycle(1, base)

    assert isinstance(result.contribution, FingerprintedContribution)
    assert declared_base_fingerprint(result.contribution) == fingerprint_state(base)
    assert validate_contribution(base, result.contribution).accepted


def test_gate_records_the_round_fingerprint_and_rejects_a_stale_base_node() -> None:
    """From round 2 a node that trained from the old base is rejected; honest nodes pass."""
    torch.manual_seed(2)
    coordinator = ValidatingConsortiumCoordinator(_model())
    nodes = [
        FingerprintingNode("fresh", "Fresh", _model(), _corpus(0), 0.9, local_epochs=1, lr=0.01),
        StaleBaseNode("stale", "Stale", _model(), _corpus(10), 0.9, local_epochs=1, lr=0.01),
    ]

    first = coordinator.run_round(nodes)
    assert first.accepted_nodes == ["fresh", "stale"]
    first_summary = coordinator.round_summaries[1]
    assert first_summary.base_fingerprint == fingerprint_state(first.previous_base_state)

    second = coordinator.run_round(nodes)
    assert second.accepted_nodes == ["fresh"]
    assert second.rejected_nodes == ["stale"]
    second_summary = coordinator.round_summaries[2]
    assert second_summary.base_fingerprint == fingerprint_state(second.previous_base_state)
    assert second_summary.base_fingerprint != first_summary.base_fingerprint
    assert second_summary.validation_rejected_nodes == ["stale"]
    report = second_summary.reports["stale"]
    assert report.finding_codes == (FindingCode.BASE_FINGERPRINT_MISMATCH,)
    assert report.findings[0].details["declared"] == first_summary.base_fingerprint
    assert report.findings[0].details["expected"] == second_summary.base_fingerprint


def test_gate_require_policy_rejects_nodes_that_do_not_declare() -> None:
    """A plain node passes by default but fails when a declaration is required."""
    torch.manual_seed(3)
    plain_node = SovereignTrainingNode("plain", "Plain", _model(), _corpus(), 0.9, local_epochs=1, lr=0.01)

    lenient = ValidatingConsortiumCoordinator(_model())
    assert lenient.run_round([plain_node]).accepted_nodes == ["plain"]

    strict = ValidatingConsortiumCoordinator(_model(), limits=ValidationLimits(fingerprint_policy="require"))
    result = strict.run_round([plain_node])
    assert result.rejected_nodes == ["plain"]
    assert strict.round_summaries[1].reports["plain"].finding_codes == (FindingCode.BASE_FINGERPRINT_MISSING,)
