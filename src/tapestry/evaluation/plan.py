"""Evaluation-plan coverage helpers for M1 readiness.

The project already has gate logic that can decide whether a result bundle
passes. This module adds the planning layer above it: a compact way to check
whether a proposed evaluation bundle covers the minimum axes discussed for M1.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tapestry.evaluation.gates import BenchmarkKind, BenchmarkSpec, EvaluationGate

DEFAULT_M1_REQUIRED_KINDS: tuple[BenchmarkKind, ...] = (
    BenchmarkKind.CAPABILITY,
    BenchmarkKind.CULTURAL_ALIGNMENT,
    BenchmarkKind.SAFETY,
)


@dataclass(frozen=True)
class EvaluationPlanFinding:
    """One issue found while checking an evaluation plan."""

    kind: BenchmarkKind
    message: str


@dataclass(frozen=True)
class EvaluationPlanDecision:
    """Coverage decision for a proposed set of benchmark specs."""

    ready: bool
    findings: tuple[EvaluationPlanFinding, ...]


@dataclass(frozen=True)
class EvaluationPlan:
    """A versioned, runner-neutral plan for M1 benchmark coverage."""

    specs: tuple[BenchmarkSpec, ...]
    required_kinds: tuple[BenchmarkKind, ...] = DEFAULT_M1_REQUIRED_KINDS

    def __post_init__(self) -> None:
        if not self.specs:
            raise ValueError("EvaluationPlan requires at least one benchmark spec")
        object.__setattr__(self, "specs", tuple(self.specs))
        object.__setattr__(
            self,
            "required_kinds",
            tuple(BenchmarkKind(kind) for kind in self.required_kinds),
        )

    @property
    def covered_required_kinds(self) -> frozenset[BenchmarkKind]:
        """Required benchmark kinds covered by at least one required spec."""
        return frozenset(spec.kind for spec in self.specs if spec.required and spec.kind in self.required_kinds)

    @property
    def missing_required_kinds(self) -> tuple[BenchmarkKind, ...]:
        """Required benchmark kinds not represented by the plan."""
        covered = self.covered_required_kinds
        return tuple(kind for kind in self.required_kinds if kind not in covered)

    def check_coverage(self) -> EvaluationPlanDecision:
        """Return whether the plan covers the configured required axes."""
        findings = tuple(
            EvaluationPlanFinding(
                kind=kind,
                message=f"required M1 evaluation axis {kind.value} is missing",
            )
            for kind in self.missing_required_kinds
        )
        return EvaluationPlanDecision(ready=not findings, findings=findings)

    def gate(self) -> EvaluationGate:
        """Build a release gate from the plan specs."""
        return EvaluationGate(list(self.specs))


def required_kind_summary(specs: Iterable[BenchmarkSpec]) -> dict[str, int]:
    """Count required benchmark specs by kind for PR and runbook summaries."""
    counts: dict[str, int] = {}
    for spec in specs:
        if not spec.required:
            continue
        kind = BenchmarkKind(spec.kind)
        counts[kind.value] = counts.get(kind.value, 0) + 1
    return counts
