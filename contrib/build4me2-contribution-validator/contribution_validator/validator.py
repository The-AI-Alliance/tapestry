"""Admission-safety checks for consortium contributions.

The validator answers one narrow question: is this contribution structurally
compatible with the shared base it claims to update, and is its update finite
and within configured magnitude limits? It is deterministic, runs on CPU, and
never modifies the tensors it inspects.

It does **not** try to detect adversarial model poisoning. A contribution that
passes these checks is admissible for aggregation, not proven trustworthy.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch

from tapestry.training.consortium.messages import ModelState, SovereignContribution

from .findings import (
    ContributionValidationReport,
    FindingCode,
    GlobalUpdateStats,
    TensorUpdateStats,
    ValidationFinding,
)
from .fingerprint import declared_base_fingerprint, fingerprint_state
from .limits import DtypePolicy, FingerprintPolicy, ValidationLimits


@dataclass(frozen=True)
class _ReferenceTensor:
    """A private snapshot of one shared-base tensor plus precomputed facts about it."""

    tensor: torch.Tensor
    work: torch.Tensor
    finite: torch.Tensor
    l2: float


def _work_dtype(tensor: torch.Tensor) -> torch.dtype:
    """Wide dtype used for statistics: complex128 for complex tensors, float64 otherwise."""
    return torch.complex128 if tensor.is_complex() else torch.float64


def _safe_norm(tensor: torch.Tensor) -> float:
    """L2 norm that does not overflow for large finite values.

    Scales by the largest magnitude first, so the result is finite whenever the
    inputs are. An infinite input still yields ``inf``, which the validator
    reports as a finding.
    """
    if tensor.numel() == 0:
        return 0.0
    scale = float(tensor.abs().max().item())
    if scale == 0.0 or not math.isfinite(scale):
        return scale
    return scale * float((tensor / scale).norm().item())


def _relative(delta_l2: float, base_l2: float) -> float | None:
    """Update norm relative to the base norm, or ``None`` when the base is all zeros."""
    return None if base_l2 == 0.0 else delta_l2 / base_l2


class ContributionValidator:
    """Validate contributions against a fixed reference (shared base) state.

    Build one validator per consortium round, using the shared-base state that
    the nodes started from as ``reference_state``. The validator keeps its own
    copy of that state, so later changes to the caller's tensors do not affect
    validation.
    """

    def __init__(self, reference_state: ModelState, limits: ValidationLimits | None = None) -> None:
        if not reference_state:
            raise ValueError("reference_state must contain at least one tensor")
        self._reference: dict[str, _ReferenceTensor] = {}
        for name, tensor in reference_state.items():
            if not isinstance(tensor, torch.Tensor):
                raise TypeError(f"reference tensor {name!r} is not a torch.Tensor")
            snapshot = tensor.detach().clone()
            finite = torch.isfinite(snapshot)
            work = snapshot.to(dtype=_work_dtype(snapshot))
            self._reference[name] = _ReferenceTensor(
                tensor=snapshot,
                work=work,
                finite=finite,
                l2=_safe_norm(torch.where(finite, work, torch.zeros_like(work))),
            )
        self.limits = limits or ValidationLimits()
        self.dtype_policy = DtypePolicy(self.limits.dtype_policy)
        self.fingerprint_policy = FingerprintPolicy(self.limits.fingerprint_policy)
        self._reference_fingerprint: str | None = None

    @property
    def reference_state(self) -> ModelState:
        """The validator's private snapshot of the shared base."""
        return {name: ref.tensor for name, ref in self._reference.items()}

    @property
    def reference_fingerprint(self) -> str:
        """Fingerprint of the reference state, computed once on first use."""
        if self._reference_fingerprint is None:
            self._reference_fingerprint = fingerprint_state(self.reference_state)
        return self._reference_fingerprint

    def validate(self, contribution: SovereignContribution) -> ContributionValidationReport:
        """Validate a node's contribution; see :meth:`validate_state`.

        A contribution that declares the fingerprint of the base it trained
        from (see :class:`~contribution_validator.fingerprint.FingerprintedContribution`)
        has that declaration checked against the reference.
        """
        return self.validate_state(
            contribution.node_id,
            contribution.round_num,
            contribution.local_model_state,
            base_fingerprint=declared_base_fingerprint(contribution),
        )

    def validate_state(
        self,
        node_id: str,
        round_num: int,
        state: Mapping[str, Any],
        base_fingerprint: str | None = None,
    ) -> ContributionValidationReport:
        """Validate a raw model state and return a full report.

        ``base_fingerprint`` is the fingerprint the node declares for the base
        it trained from, or ``None`` if it declares none. All checks run even
        after the first failure, so the report lists every problem found
        rather than only the first one.
        """
        findings: list[ValidationFinding] = list(self._check_fingerprint(base_fingerprint))
        findings.extend(self._check_coverage(state))
        layer_stats: dict[str, TensorUpdateStats] = {}

        for name in self._reference:
            if name not in state:
                continue
            tensor_findings, stats = self._check_tensor(name, state[name])
            findings.extend(tensor_findings)
            if stats is not None:
                layer_stats[name] = stats

        global_stats = self._aggregate(layer_stats)
        findings.extend(self._check_global_limits(global_stats))

        return ContributionValidationReport(
            node_id=node_id,
            round_num=round_num,
            accepted=not findings,
            findings=tuple(findings),
            layer_stats=layer_stats,
            global_stats=global_stats,
        )

    def _check_fingerprint(self, base_fingerprint: str | None) -> list[ValidationFinding]:
        if self.fingerprint_policy is FingerprintPolicy.IGNORE:
            return []
        if base_fingerprint is None:
            if self.fingerprint_policy is FingerprintPolicy.REQUIRE:
                return [
                    ValidationFinding(
                        code=FindingCode.BASE_FINGERPRINT_MISSING,
                        message="contribution does not declare the fingerprint of the base it trained from",
                        details={"expected": self.reference_fingerprint},
                    )
                ]
            return []
        if base_fingerprint == self.reference_fingerprint:
            return []
        return [
            ValidationFinding(
                code=FindingCode.BASE_FINGERPRINT_MISMATCH,
                message="contribution was trained from a different shared base than this round's",
                details={"expected": self.reference_fingerprint, "declared": base_fingerprint},
            )
        ]

    def _check_coverage(self, state: Mapping[str, Any]) -> list[ValidationFinding]:
        expected = set(self._reference)
        actual = set(state)
        findings = [
            ValidationFinding(
                code=FindingCode.MISSING_PARAMETER,
                message=f"expected parameter {name!r} is missing from the contribution",
                tensor_name=name,
            )
            for name in sorted(expected - actual)
        ]
        findings.extend(
            ValidationFinding(
                code=FindingCode.UNEXPECTED_PARAMETER,
                message=f"contribution contains parameter {name!r} that the shared base does not have",
                tensor_name=name,
            )
            for name in sorted(actual - expected)
        )
        return findings

    def _check_tensor(self, name: str, value: Any) -> tuple[list[ValidationFinding], TensorUpdateStats | None]:
        ref = self._reference[name]
        base = ref.tensor
        if not isinstance(value, torch.Tensor):
            finding = ValidationFinding(
                code=FindingCode.NOT_A_TENSOR,
                message=f"parameter {name!r} is a {type(value).__name__}, not a torch.Tensor",
                tensor_name=name,
                details={"actual_type": type(value).__name__},
            )
            return [finding], None

        tensor = value.detach()
        if tuple(tensor.shape) != tuple(base.shape):
            finding = ValidationFinding(
                code=FindingCode.SHAPE_MISMATCH,
                message=f"parameter {name!r} has shape {tuple(tensor.shape)}, expected {tuple(base.shape)}",
                tensor_name=name,
                details={"expected_shape": list(base.shape), "actual_shape": list(tensor.shape)},
            )
            return [finding], None

        findings: list[ValidationFinding] = []
        if tensor.device != base.device:
            findings.append(
                ValidationFinding(
                    code=FindingCode.DEVICE_MISMATCH,
                    message=f"parameter {name!r} is on device {tensor.device}, expected {base.device}",
                    tensor_name=name,
                    details={"expected_device": str(base.device), "actual_device": str(tensor.device)},
                )
            )
            tensor = tensor.to(device=base.device)

        if not self._dtype_compatible(base.dtype, tensor.dtype):
            findings.append(
                ValidationFinding(
                    code=FindingCode.DTYPE_MISMATCH,
                    message=f"parameter {name!r} has dtype {tensor.dtype}, expected {base.dtype}",
                    tensor_name=name,
                    details={
                        "expected_dtype": str(base.dtype),
                        "actual_dtype": str(tensor.dtype),
                        "dtype_policy": self.dtype_policy.value,
                    },
                )
            )

        stats = self._tensor_stats(name, ref, tensor)
        if stats.non_finite_count:
            findings.append(
                ValidationFinding(
                    code=FindingCode.NON_FINITE,
                    message=(
                        f"parameter {name!r} contains {stats.non_finite_count} NaN or infinite values "
                        "where the shared base does not"
                    ),
                    tensor_name=name,
                    details={"non_finite_count": stats.non_finite_count, "numel": stats.numel},
                )
            )
        findings.extend(self._check_cast_overflow(name, base, tensor))
        if not math.isfinite(stats.delta_l2) or not math.isfinite(stats.max_abs_delta):
            findings.append(
                ValidationFinding(
                    code=FindingCode.STATISTIC_OVERFLOW,
                    message=f"update statistics for parameter {name!r} overflow; the update cannot be measured",
                    tensor_name=name,
                    details={"delta_l2": stats.delta_l2, "max_abs_delta": stats.max_abs_delta},
                )
            )
        findings.extend(self._check_layer_limits(stats))
        return findings, stats

    def _dtype_compatible(self, expected: torch.dtype, actual: torch.dtype) -> bool:
        if expected == actual:
            return True
        if self.dtype_policy is DtypePolicy.FLOAT_COMPATIBLE:
            return expected.is_floating_point and actual.is_floating_point
        return False

    @staticmethod
    def _check_cast_overflow(name: str, base: torch.Tensor, tensor: torch.Tensor) -> list[ValidationFinding]:
        """Values that are finite now but overflow when cast into the base dtype during merge."""
        if tensor.dtype == base.dtype or not base.is_floating_point() or not tensor.is_floating_point():
            return []
        overflow = torch.isfinite(tensor) & ~torch.isfinite(tensor.to(dtype=base.dtype))
        count = int(overflow.sum().item())
        if not count:
            return []
        return [
            ValidationFinding(
                code=FindingCode.CAST_OVERFLOW,
                message=f"parameter {name!r} has {count} values that overflow when cast to {base.dtype}",
                tensor_name=name,
                details={"overflow_count": count, "base_dtype": str(base.dtype), "actual_dtype": str(tensor.dtype)},
            )
        ]

    @staticmethod
    def _tensor_stats(name: str, ref: _ReferenceTensor, tensor: torch.Tensor) -> TensorUpdateStats:
        """Measure the update against the base.

        A non-finite contributed value is only counted as a problem where the
        base holds a different value; a ``-inf`` mask entry that matches the
        base is legitimate. Statistics cover elements where both the base and
        the contribution are finite.
        """
        finite = torch.isfinite(tensor)
        offending = ~finite & ~(tensor == ref.tensor)
        comparable = finite & ref.finite

        work = tensor.to(dtype=ref.work.dtype)
        delta = torch.where(comparable, work - ref.work, torch.zeros_like(ref.work))
        delta_l2 = _safe_norm(delta)
        max_abs_delta = float(delta.abs().max().item()) if delta.numel() else 0.0

        return TensorUpdateStats(
            name=name,
            shape=tuple(tensor.shape),
            dtype=str(tensor.dtype),
            numel=tensor.numel(),
            base_l2=ref.l2,
            delta_l2=delta_l2,
            relative_l2=_relative(delta_l2, ref.l2),
            max_abs_delta=max_abs_delta,
            non_finite_count=int(offending.sum().item()),
        )

    def _check_layer_limits(self, stats: TensorUpdateStats) -> list[ValidationFinding]:
        checks = (
            (FindingCode.LAYER_UPDATE_TOO_LARGE, "delta_l2", stats.delta_l2, self.limits.max_layer_update_norm),
            (
                FindingCode.LAYER_RELATIVE_UPDATE_TOO_LARGE,
                "relative_l2",
                stats.relative_l2,
                self.limits.max_layer_relative_update,
            ),
            (FindingCode.ABS_DELTA_TOO_LARGE, "max_abs_delta", stats.max_abs_delta, self.limits.max_abs_delta),
        )
        return [
            self._limit_finding(code, metric, measured, limit, stats.name)
            for code, metric, measured, limit in checks
            if limit is not None and measured is not None and measured > limit
        ]

    def _check_global_limits(self, stats: GlobalUpdateStats) -> list[ValidationFinding]:
        checks = (
            (FindingCode.GLOBAL_UPDATE_TOO_LARGE, "delta_l2", stats.delta_l2, self.limits.max_global_update_norm),
            (
                FindingCode.GLOBAL_RELATIVE_UPDATE_TOO_LARGE,
                "relative_l2",
                stats.relative_l2,
                self.limits.max_global_relative_update,
            ),
        )
        return [
            self._limit_finding(code, metric, measured, limit, None)
            for code, metric, measured, limit in checks
            if limit is not None and measured is not None and measured > limit
        ]

    @staticmethod
    def _limit_finding(
        code: str, metric: str, measured: float, limit: float, tensor_name: str | None
    ) -> ValidationFinding:
        scope = f"parameter {tensor_name!r}" if tensor_name else "contribution"
        return ValidationFinding(
            code=code,
            message=f"{scope} {metric} of {measured:.6g} exceeds the limit of {limit:.6g}",
            tensor_name=tensor_name,
            details={"metric": metric, "measured": measured, "limit": limit},
        )

    def _aggregate(self, layer_stats: Mapping[str, TensorUpdateStats]) -> GlobalUpdateStats:
        base_l2 = math.hypot(*(stats.base_l2 for stats in layer_stats.values())) if layer_stats else 0.0
        delta_l2 = math.hypot(*(stats.delta_l2 for stats in layer_stats.values())) if layer_stats else 0.0
        return GlobalUpdateStats(
            expected_tensor_count=len(self._reference),
            compared_tensor_count=len(layer_stats),
            numel=sum(stats.numel for stats in layer_stats.values()),
            base_l2=base_l2,
            delta_l2=delta_l2,
            relative_l2=_relative(delta_l2, base_l2),
            max_abs_delta=max((stats.max_abs_delta for stats in layer_stats.values()), default=0.0),
            non_finite_count=sum(stats.non_finite_count for stats in layer_stats.values()),
        )


def validate_contribution(
    reference_state: ModelState,
    contribution: SovereignContribution,
    limits: ValidationLimits | None = None,
) -> ContributionValidationReport:
    """One-shot convenience wrapper around :class:`ContributionValidator`."""
    return ContributionValidator(reference_state, limits).validate(contribution)
