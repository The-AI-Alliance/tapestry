"""Tests for the contribution validator and its coordinator wiring."""

# pylint: disable=wrong-import-position,wrong-import-order

from __future__ import annotations

import json
import math
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from contribution_validator import (
    ContributionValidator,
    DtypePolicy,
    FindingCode,
    ValidatingConsortiumCoordinator,
    ValidationLimits,
    validate_contribution,
)
from contribution_validator.faults import (
    FaultInjectingNode,
    add_parameter,
    cast_parameters,
    drop_parameter,
    inject_inf,
    inject_nan,
    reshape_parameter,
    scale_parameters,
)
from contribution_validator.testing import base_state as _base_state
from contribution_validator.testing import tiny_model as _model
from contribution_validator.testing import toy_corpus as _corpus

from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ContributionPolicy,
    SovereignContribution,
    SovereignTrainingNode,
    TinyCausalModel,
)
from tapestry.training.consortium.messages import ModelState


def _node(node_id: str = "node-a", offset: int = 0) -> SovereignTrainingNode:
    return SovereignTrainingNode(
        node_id=node_id,
        jurisdiction=node_id.title(),
        model=_model(),
        sovereign_corpus=_corpus(offset),
        quality_score=0.9,
        local_epochs=1,
        lr=0.01,
    )


def _contribution(state: ModelState, node_id: str = "node-a") -> SovereignContribution:
    return SovereignContribution(
        node_id=node_id,
        round_num=1,
        local_model_state=state,
        quality_score=0.9,
        token_count=12,
    )


def _trained_state() -> ModelState:
    torch.manual_seed(1)
    return _node().run_sovereign_cycle(1, _base_state()).contribution.local_model_state


def _snapshot(state: ModelState) -> ModelState:
    return {name: tensor.clone() for name, tensor in state.items()}


def _assert_same(before: ModelState, after: ModelState) -> None:
    assert set(before) == set(after)
    for name, tensor in before.items():
        torch.testing.assert_close(after[name], tensor, rtol=0.0, atol=0.0, equal_nan=True, msg=name)


def test_well_formed_contribution_is_accepted_with_statistics() -> None:
    """A real node cycle produces a contribution that passes the default checks."""
    base = _base_state()
    report = validate_contribution(base, _contribution(_trained_state()))

    assert report.accepted
    assert not report.findings
    assert set(report.layer_stats) == set(base)
    assert report.global_stats.expected_tensor_count == len(base)
    assert report.global_stats.compared_tensor_count == len(base)
    assert report.global_stats.numel == sum(tensor.numel() for tensor in base.values())
    assert report.global_stats.delta_l2 > 0.0
    assert report.global_stats.non_finite_count == 0


def test_unchanged_contribution_has_zero_update() -> None:
    """Returning the base unchanged is structurally valid and measures as a zero update."""
    base = _base_state()
    report = validate_contribution(base, _contribution(_snapshot(base)))

    assert report.accepted
    assert report.global_stats.delta_l2 == 0.0
    assert report.global_stats.max_abs_delta == 0.0
    assert all(stats.delta_l2 == 0.0 for stats in report.layer_stats.values())


def test_missing_parameter_is_rejected() -> None:
    """Every expected tensor must be present."""
    base = _base_state()
    state = drop_parameter(_trained_state())
    missing = next(iter(base))

    report = validate_contribution(base, _contribution(state))

    assert not report.accepted
    assert report.finding_codes == (FindingCode.MISSING_PARAMETER,)
    assert report.findings[0].tensor_name == missing
    assert missing not in report.layer_stats
    assert report.global_stats.compared_tensor_count == len(base) - 1


def test_unexpected_parameter_is_rejected() -> None:
    """Tensors the shared base does not have are not silently ignored."""
    report = validate_contribution(_base_state(), _contribution(add_parameter(_trained_state(), "extra.bias")))

    assert not report.accepted
    assert report.finding_codes == (FindingCode.UNEXPECTED_PARAMETER,)
    assert report.findings[0].tensor_name == "extra.bias"


def test_shape_mismatch_is_rejected_and_not_measured() -> None:
    """A tensor with the wrong shape cannot be compared, so it gets no statistics."""
    base = _base_state()
    state = reshape_parameter(_trained_state())
    name = next(iter(base))

    report = validate_contribution(base, _contribution(state))

    assert not report.accepted
    assert report.finding_codes == (FindingCode.SHAPE_MISMATCH,)
    assert report.findings[0].details["expected_shape"] == list(base[name].shape)
    assert report.findings[0].details["actual_shape"] == list(state[name].shape)
    assert name not in report.layer_stats


def test_dtype_policy_controls_dtype_mismatch() -> None:
    """Exact policy rejects float16; float-compatible policy accepts it."""
    base = _base_state()
    state = cast_parameters(_trained_state(), torch.float16)

    strict = validate_contribution(base, _contribution(state))
    assert not strict.accepted
    assert set(strict.finding_codes) == {FindingCode.DTYPE_MISMATCH}
    assert len(strict.findings) == len(base)
    assert strict.findings[0].details["dtype_policy"] == "exact"

    relaxed = validate_contribution(base, _contribution(state), ValidationLimits(dtype_policy="float-compatible"))
    assert relaxed.accepted
    assert relaxed.layer_stats[next(iter(base))].dtype == "torch.float16"


def test_float_compatible_policy_still_requires_exact_integer_dtypes() -> None:
    """Integer buffers must match exactly even under the relaxed float policy."""
    base = {"weight": torch.zeros(2, 2), "steps": torch.tensor([3], dtype=torch.int64)}
    state = {"weight": torch.zeros(2, 2), "steps": torch.tensor([3], dtype=torch.int32)}

    validator = ContributionValidator(base, ValidationLimits(dtype_policy=DtypePolicy.FLOAT_COMPATIBLE))
    report = validator.validate_state("node", 1, state)

    assert report.finding_codes == (FindingCode.DTYPE_MISMATCH,)
    assert report.findings[0].tensor_name == "steps"


@pytest.mark.parametrize("fault", [inject_nan, inject_inf])
def test_non_finite_values_are_rejected_and_counted(fault: Callable[[ModelState, int], ModelState]) -> None:
    """NaN and infinite values are rejected, with the count recorded."""
    base = _base_state()
    state = fault(_trained_state(), 3)
    name = next(iter(base))

    report = validate_contribution(base, _contribution(state))

    assert not report.accepted
    assert report.finding_codes == (FindingCode.NON_FINITE,)
    assert report.findings[0].tensor_name == name
    assert report.findings[0].details["non_finite_count"] == 3
    assert report.layer_stats[name].non_finite_count == 3
    assert report.global_stats.non_finite_count == 3
    # Statistics stay finite because non-finite elements are excluded from them.
    assert report.global_stats.delta_l2 < float("inf")


def test_layer_and_global_magnitude_limits() -> None:
    """Oversized updates trigger per-layer and global findings with evidence."""
    base = _base_state()
    state = scale_parameters(_trained_state(), 50.0)
    limits = ValidationLimits(
        max_layer_update_norm=1.0,
        max_layer_relative_update=2.0,
        max_abs_delta=0.5,
        max_global_update_norm=1.0,
        max_global_relative_update=2.0,
    )

    report = validate_contribution(base, _contribution(state), limits)

    assert not report.accepted
    codes = set(report.finding_codes)
    assert codes == {
        FindingCode.LAYER_UPDATE_TOO_LARGE,
        FindingCode.LAYER_RELATIVE_UPDATE_TOO_LARGE,
        FindingCode.ABS_DELTA_TOO_LARGE,
        FindingCode.GLOBAL_UPDATE_TOO_LARGE,
        FindingCode.GLOBAL_RELATIVE_UPDATE_TOO_LARGE,
    }
    global_finding = next(f for f in report.findings if f.code == FindingCode.GLOBAL_UPDATE_TOO_LARGE)
    assert global_finding.tensor_name is None
    assert global_finding.details["measured"] == pytest.approx(report.global_stats.delta_l2)
    assert global_finding.details["limit"] == 1.0


def test_magnitude_limits_pass_for_ordinary_updates() -> None:
    """A normal local training step stays well under generous limits."""
    report = validate_contribution(
        _base_state(),
        _contribution(_trained_state()),
        ValidationLimits(max_global_relative_update=1.0, max_layer_relative_update=1.0),
    )
    assert report.accepted


def test_all_findings_are_reported_not_only_the_first() -> None:
    """Multiple independent problems show up in one report."""
    state = add_parameter(drop_parameter(inject_nan(_trained_state())))
    # inject_nan hit the first tensor, which drop_parameter then removed; add a NaN elsewhere.
    last = list(state)[-2]
    state[last] = inject_nan({last: state[last]})[last]

    report = validate_contribution(_base_state(), _contribution(state))

    assert set(report.finding_codes) == {
        FindingCode.MISSING_PARAMETER,
        FindingCode.UNEXPECTED_PARAMETER,
        FindingCode.NON_FINITE,
    }


def test_non_tensor_value_is_rejected() -> None:
    """A value that is not a tensor is reported instead of raising."""
    base = _base_state()
    state: dict[str, Any] = dict(_trained_state())
    name = next(iter(base))
    state[name] = state[name].tolist()

    report = ContributionValidator(base).validate_state("node", 1, state)

    assert report.finding_codes == (FindingCode.NOT_A_TENSOR,)
    assert report.findings[0].details["actual_type"] == "list"


class _ClaimsAnotherDevice(torch.Tensor):
    """A real CPU tensor that reports a different device.

    This exercises the device check on a CPU-only machine. The data stays on
    the CPU, so moving it to the base device is a no-op and every later check
    still runs on real values.
    """

    @property
    def device(self) -> torch.device:
        """Pretend to live on a GPU."""
        return torch.device("cuda", 0)


def test_device_mismatch_is_reported_and_the_tensor_is_still_measured() -> None:
    """A tensor on the wrong device is a finding, not a silent move."""
    base = _base_state()
    state = dict(_trained_state())
    name = next(iter(base))
    state[name] = state[name].as_subclass(_ClaimsAnotherDevice)

    report = ContributionValidator(base).validate_state("node", 1, state)

    assert not report.accepted
    assert report.finding_codes == (FindingCode.DEVICE_MISMATCH,)
    assert report.findings[0].tensor_name == name
    assert report.findings[0].details == {"expected_device": "cpu", "actual_device": "cuda:0"}
    assert name in report.layer_stats
    assert report.layer_stats[name].delta_l2 > 0.0
    assert report.global_stats.compared_tensor_count == len(base)


def test_empty_tensors_are_accepted_with_zero_statistics() -> None:
    """A zero-element tensor (for example an empty buffer) compares as a zero update."""
    base = {"empty": torch.zeros(0), "weight": torch.ones(2)}
    report = ContributionValidator(base).validate_state("node", 1, {"empty": torch.zeros(0), "weight": torch.ones(2)})

    assert report.accepted
    assert report.layer_stats["empty"].delta_l2 == 0.0
    assert report.layer_stats["empty"].max_abs_delta == 0.0
    assert report.layer_stats["empty"].relative_l2 is None


def test_faults_require_a_floating_point_tensor() -> None:
    """Fault helpers refuse a state with nothing they can corrupt."""
    with pytest.raises(ValueError):
        inject_nan({"steps": torch.tensor([1], dtype=torch.int64)})


def test_validation_does_not_mutate_inputs() -> None:
    """Neither the reference state nor the contribution is modified by validation."""
    base = _base_state()
    state = inject_nan(scale_parameters(_trained_state(), 10.0))
    base_before = _snapshot(base)
    state_before = _snapshot(state)

    validate_contribution(base, _contribution(state), ValidationLimits(max_global_update_norm=0.1))

    _assert_same(base_before, base)
    _assert_same(state_before, state)


def test_report_is_deterministic_and_json_serializable() -> None:
    """Repeated validation gives identical reports that serialize to JSON."""
    base = _base_state()
    contribution = _contribution(inject_inf(_trained_state()))
    limits = ValidationLimits(max_layer_update_norm=0.01)

    first = validate_contribution(base, contribution, limits)
    second = validate_contribution(base, contribution, limits)

    assert first == second
    encoded = json.dumps(first.to_dict(), allow_nan=False)
    decoded = json.loads(encoded)
    assert decoded["accepted"] is False
    assert decoded["findings"][0]["code"] == FindingCode.NON_FINITE
    assert decoded["global_stats"]["expected_tensor_count"] == len(base)


def test_limits_reject_negative_and_nan_values() -> None:
    """Misconfigured limits fail fast."""
    with pytest.raises(ValueError):
        ValidationLimits(max_global_update_norm=-1.0)
    with pytest.raises(ValueError):
        ValidationLimits(max_abs_delta=float("nan"))
    with pytest.raises(ValueError):
        ValidationLimits(dtype_policy="loose")


def test_reference_state_must_be_non_empty_tensors() -> None:
    """An empty or non-tensor shared base is a precondition failure."""
    with pytest.raises(ValueError):
        ContributionValidator({})
    not_tensors: dict[str, Any] = {"weight": [1.0, 2.0]}
    with pytest.raises(TypeError):
        ContributionValidator(not_tensors)


def test_validator_keeps_a_private_copy_of_the_reference() -> None:
    """Mutating the caller's tensors after construction does not change the reference."""
    base = _base_state()
    validator = ContributionValidator(base)
    original = _snapshot(base)
    name = next(iter(base))
    base[name].add_(1.0)

    report = validator.validate_state("node", 1, original)

    assert report.accepted
    assert report.global_stats.delta_l2 == 0.0
    assert torch.equal(validator.reference_state[name], original[name])


def test_non_finite_base_values_are_legitimate_when_matched() -> None:
    """A base with a -inf mask buffer accepts matching contributions and still catches new NaNs."""
    mask = torch.full((3, 3), float("-inf")).triu(1)
    base = {"weight": torch.ones(2, 2), "mask": mask.clone()}
    validator = ContributionValidator(base)

    matching = validator.validate_state("node", 1, {"weight": torch.ones(2, 2) * 1.5, "mask": mask.clone()})
    assert matching.accepted
    assert matching.layer_stats["mask"].non_finite_count == 0
    assert matching.layer_stats["mask"].delta_l2 == 0.0
    assert matching.global_stats.delta_l2 == pytest.approx(1.0)

    corrupted_mask = mask.clone()
    corrupted_mask[0, 0] = float("nan")
    corrupted = validator.validate_state("node", 1, {"weight": torch.ones(2, 2), "mask": corrupted_mask})
    assert corrupted.finding_codes == (FindingCode.NON_FINITE,)
    assert corrupted.findings[0].details["non_finite_count"] == 1

    finite_mask = torch.zeros(3, 3)
    filled = validator.validate_state("node", 1, {"weight": torch.ones(2, 2), "mask": finite_mask})
    assert filled.accepted


def test_relative_update_is_undefined_for_all_zero_base_tensors() -> None:
    """A zero-initialised parameter cannot amplify a relative limit into a rejection."""
    base = {"bias": torch.zeros(8), "weight": torch.ones(2, 2)}
    state = {"bias": torch.full((8,), 1e-4), "weight": torch.ones(2, 2) * 1.01}
    limits = ValidationLimits(max_layer_relative_update=0.5, max_global_relative_update=0.5)

    report = ContributionValidator(base, limits).validate_state("node", 1, state)

    assert report.accepted
    assert report.layer_stats["bias"].relative_l2 is None
    assert report.layer_stats["weight"].relative_l2 == pytest.approx(0.01)
    assert report.global_stats.relative_l2 is not None

    all_zero = ContributionValidator({"bias": torch.zeros(8)}, limits).validate_state(
        "node", 1, {"bias": torch.full((8,), 1e-4)}
    )
    assert all_zero.accepted
    assert all_zero.global_stats.relative_l2 is None
    assert json.loads(json.dumps(all_zero.to_dict(), allow_nan=False))["global_stats"]["relative_l2"] is None


def test_float_compatible_policy_rejects_values_that_overflow_the_base_dtype() -> None:
    """A float32 value that becomes inf when cast into a float16 base is caught before the merge."""
    base = {"weight": torch.ones(2, 2, dtype=torch.float16)}
    state = {"weight": torch.tensor([[70000.0, 1.0], [1.0, 1.0]], dtype=torch.float32)}
    limits = ValidationLimits(dtype_policy=DtypePolicy.FLOAT_COMPATIBLE)

    report = ContributionValidator(base, limits).validate_state("node", 1, state)

    assert not report.accepted
    assert report.finding_codes == (FindingCode.CAST_OVERFLOW,)
    assert report.findings[0].details["overflow_count"] == 1
    assert report.findings[0].details["base_dtype"] == "torch.float16"

    in_range = ValidationLimits(dtype_policy=DtypePolicy.FLOAT_COMPATIBLE)
    ok = ContributionValidator(base, in_range).validate_state(
        "node", 1, {"weight": torch.full((2, 2), 2.0, dtype=torch.float32)}
    )
    assert ok.accepted


def test_complex_tensors_are_checked_for_non_finite_values() -> None:
    """A NaN hidden in the imaginary part is still a non-finite finding."""
    base = {"c": torch.complex(torch.ones(2), torch.zeros(2))}
    good = {"c": torch.complex(torch.ones(2) * 2.0, torch.ones(2))}
    bad = {"c": torch.complex(torch.ones(2), torch.tensor([float("nan"), 0.0]))}

    validator = ContributionValidator(base)
    accepted = validator.validate_state("node", 1, good)
    rejected = validator.validate_state("node", 1, bad)

    assert accepted.accepted
    assert accepted.layer_stats["c"].delta_l2 == pytest.approx(2.0)
    assert accepted.layer_stats["c"].max_abs_delta == pytest.approx(math.sqrt(2.0))
    assert rejected.finding_codes == (FindingCode.NON_FINITE,)
    assert rejected.layer_stats["c"].non_finite_count == 1


def test_huge_finite_values_do_not_overflow_the_norm() -> None:
    """Norms are scaled so large finite updates measure correctly and stay JSON-safe."""
    base = {"m": torch.zeros(2, dtype=torch.float64)}
    state = {"m": torch.full((2,), 1e200, dtype=torch.float64)}

    report = ContributionValidator(base).validate_state("node", 1, state)

    assert report.accepted
    assert math.isfinite(report.layer_stats["m"].delta_l2)
    assert report.layer_stats["m"].delta_l2 == pytest.approx(1e200 * math.sqrt(2.0))
    assert math.isfinite(report.global_stats.delta_l2)
    json.dumps(report.to_dict(), allow_nan=False)


def test_unmeasurable_update_is_rejected_and_serializes() -> None:
    """When the update itself overflows float64 it is a finding, and the report is still strict JSON."""
    base = {"m": torch.full((2,), -1e308, dtype=torch.float64)}
    state = {"m": torch.full((2,), 1e308, dtype=torch.float64)}

    report = ContributionValidator(base).validate_state("node", 1, state)

    assert not report.accepted
    assert FindingCode.STATISTIC_OVERFLOW in report.finding_codes
    encoded = json.dumps(report.to_dict(), allow_nan=False)
    assert "Infinity" not in encoded
    assert json.loads(encoded)["layer_stats"]["m"]["delta_l2"] is None


def test_gate_excludes_corrupted_node_and_records_reports() -> None:
    """A corrupted contribution is rejected and cannot reach the shared base."""
    torch.manual_seed(3)
    coordinator = ValidatingConsortiumCoordinator(_model())
    nodes = [
        _node("clean-a", 0),
        _node("clean-b", 10),
        FaultInjectingNode(
            node_id="corrupt",
            jurisdiction="Corrupt",
            model=_model(),
            sovereign_corpus=_corpus(20),
            quality_score=0.95,
            local_epochs=1,
            lr=0.01,
            fault=inject_nan,
        ),
    ]

    result = coordinator.run_round(nodes)

    assert result.accepted_nodes == ["clean-a", "clean-b"]
    assert result.rejected_nodes == ["corrupt"]
    assert "corrupt" not in result.contribution_weights
    reports = coordinator.validation_reports[1]
    assert set(reports) == {"clean-a", "clean-b", "corrupt"}
    assert not reports["corrupt"].accepted
    assert reports["corrupt"].finding_codes == (FindingCode.NON_FINITE,)
    summary = coordinator.round_summaries[1]
    assert summary.validation_rejected_nodes == ["corrupt"]
    assert summary.admitted_nodes == ["clean-a", "clean-b"]
    assert summary.quorum_met
    assert all(torch.isfinite(tensor).all() for tensor in result.shared_base_state.values())
    assert any(
        not torch.equal(result.previous_base_state[name], result.shared_base_state[name])
        for name in result.previous_base_state
    )
    # The corrupt node still owns its (uncorrupted) sovereign artifact.
    assert "corrupt" in coordinator.sovereign_artifacts


def test_gate_leaves_shared_base_unchanged_when_every_node_is_rejected() -> None:
    """If nothing is admissible, the round is a no-op for the shared base."""
    torch.manual_seed(4)
    coordinator = ValidatingConsortiumCoordinator(_model(), limits=ValidationLimits(max_global_update_norm=0.0))
    before = coordinator.shared_base_state

    result = coordinator.run_round([_node("a", 0), _node("b", 10)])

    assert not result.accepted_nodes
    assert result.rejected_nodes == ["a", "b"]
    assert not result.contribution_weights
    _assert_same(before, coordinator.shared_base_state)


def test_gate_separates_validation_rejections_from_policy_rejections() -> None:
    """A corrupt high-quality node and a clean low-quality node are both rejected, for different reasons."""
    torch.manual_seed(8)
    policy = ContributionPolicy(quality_floor=0.5)
    coordinator = ValidatingConsortiumCoordinator(_model(), contribution_policy=policy)
    weak = _node("weak", 10)
    weak.quality_score = 0.1
    corrupt = FaultInjectingNode(
        node_id="corrupt",
        jurisdiction="Corrupt",
        model=_model(),
        sovereign_corpus=_corpus(20),
        quality_score=0.95,
        local_epochs=1,
        lr=0.01,
        fault=inject_nan,
    )

    result = coordinator.run_round([_node("clean", 0), weak, corrupt])

    assert result.accepted_nodes == ["clean"]
    assert set(result.rejected_nodes) == {"weak", "corrupt"}
    summary = coordinator.round_summaries[1]
    assert summary.validation_rejected_nodes == ["corrupt"]
    assert summary.admitted_nodes == ["clean", "weak"]


def test_gate_quorum_blocks_a_lone_survivor_from_owning_the_base() -> None:
    """When too few contributions survive validation, the round leaves the shared base alone."""
    torch.manual_seed(9)
    policy = ContributionPolicy(quality_floor=0.5, max_node_weight=0.6)
    coordinator = ValidatingConsortiumCoordinator(_model(), contribution_policy=policy, min_admitted_nodes=2)
    before = coordinator.shared_base_state

    def _corrupt(node_id: str, offset: int) -> FaultInjectingNode:
        return FaultInjectingNode(
            node_id=node_id,
            jurisdiction=node_id.title(),
            model=_model(),
            sovereign_corpus=_corpus(offset),
            quality_score=0.9,
            local_epochs=1,
            lr=0.01,
            fault=inject_nan,
        )

    result = coordinator.run_round([_node("survivor", 0), _corrupt("b", 10), _corrupt("c", 20)])

    assert not result.accepted_nodes
    assert not result.contribution_weights
    assert set(result.rejected_nodes) == {"survivor", "b", "c"}
    summary = coordinator.round_summaries[1]
    assert summary.admitted_nodes == ["survivor"]
    assert summary.validation_rejected_nodes == ["b", "c"]
    assert not summary.quorum_met
    _assert_same(before, coordinator.shared_base_state)

    with pytest.raises(ValueError):
        ValidatingConsortiumCoordinator(_model(), min_admitted_nodes=0)


def test_gate_matches_plain_coordinator_for_a_model_with_a_non_finite_buffer() -> None:
    """A registered -inf mask buffer is legitimate and does not make the gate diverge from the plain path."""

    class MaskedModel(TinyCausalModel):
        """Tiny model with a causal mask buffer that contains -inf."""

        def __init__(self) -> None:
            super().__init__(vocab_size=64, hidden_size=16)
            self.register_buffer("mask", torch.full((4, 4), float("-inf")).triu(1))

    torch.manual_seed(10)
    plain = ConsortiumCoordinator(MaskedModel())
    torch.manual_seed(10)
    gated = ValidatingConsortiumCoordinator(MaskedModel())

    def _nodes() -> list[SovereignTrainingNode]:
        torch.manual_seed(11)
        return [
            SovereignTrainingNode("a", "A", MaskedModel(), _corpus(0), 0.9, local_epochs=1, lr=0.01),
            SovereignTrainingNode("b", "B", MaskedModel(), _corpus(10), 0.8, local_epochs=1, lr=0.01),
        ]

    plain_result = plain.run_round(_nodes())
    gated_result = gated.run_round(_nodes())

    assert gated_result.accepted_nodes == plain_result.accepted_nodes == ["a", "b"]
    assert gated.round_summaries[1].validation_rejected_nodes == []
    _assert_same(plain_result.shared_base_state, gated_result.shared_base_state)


def test_gate_matches_plain_coordinator_when_all_contributions_are_valid() -> None:
    """With well-formed contributions the gate is a pure pass-through."""
    torch.manual_seed(5)
    plain = ConsortiumCoordinator(_model())
    torch.manual_seed(5)
    gated = ValidatingConsortiumCoordinator(_model())

    torch.manual_seed(6)
    plain_result = plain.run_round([_node("a", 0), _node("b", 10)])
    torch.manual_seed(6)
    gated_result = gated.run_round([_node("a", 0), _node("b", 10)])

    assert plain_result.accepted_nodes == gated_result.accepted_nodes
    assert plain_result.contribution_weights == gated_result.contribution_weights
    _assert_same(plain_result.shared_base_state, gated_result.shared_base_state)
