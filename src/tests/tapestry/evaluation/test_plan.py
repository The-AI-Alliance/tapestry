"""Tests for M1 evaluation-plan coverage helpers."""

from __future__ import annotations

import unittest

from tapestry.evaluation import (
    BenchmarkConfig,
    BenchmarkKind,
    BenchmarkSpec,
    EvaluationPlan,
    required_kind_summary,
)


def _spec(benchmark_id: str, kind: BenchmarkKind, required: bool = True) -> BenchmarkSpec:
    return BenchmarkSpec(
        benchmark_id=benchmark_id,
        name=benchmark_id.replace("-", " ").title(),
        kind=kind,
        metric="score",
        config=BenchmarkConfig(
            task_version=f"{benchmark_id}/v1",
            dataset_revision="2026-08-01",
            prompt_template="zero-shot",
        ),
        threshold=0.7,
        required=required,
    )


class EvaluationPlanTest(unittest.TestCase):
    """Coverage behavior for M1 evaluation planning."""

    def test_plan_is_ready_when_required_m1_axes_are_present(self) -> None:
        """A plan is ready when capability, alignment, and safety are covered."""
        plan = EvaluationPlan(
            (
                _spec("capability-core", BenchmarkKind.CAPABILITY),
                _spec("cultural-alignment-smoke", BenchmarkKind.CULTURAL_ALIGNMENT),
                _spec("refusal-safety", BenchmarkKind.SAFETY),
                _spec("domain-extra", BenchmarkKind.DOMAIN, required=False),
            )
        )

        decision = plan.check_coverage()

        self.assertTrue(decision.ready)
        self.assertEqual(decision.findings, ())
        self.assertIn("capability-core", plan.gate().specs)

    def test_plan_reports_missing_required_axes(self) -> None:
        """Missing required benchmark axes are reported as findings."""
        plan = EvaluationPlan((_spec("capability-core", BenchmarkKind.CAPABILITY),))

        decision = plan.check_coverage()

        self.assertFalse(decision.ready)
        self.assertEqual(
            [finding.kind for finding in decision.findings],
            [BenchmarkKind.CULTURAL_ALIGNMENT, BenchmarkKind.SAFETY],
        )

    def test_required_kind_summary_ignores_optional_specs(self) -> None:
        """Optional benchmarks are omitted from required-kind summaries."""
        summary = required_kind_summary(
            (
                _spec("capability-core", BenchmarkKind.CAPABILITY),
                _spec("domain-extra", BenchmarkKind.DOMAIN, required=False),
            )
        )

        self.assertEqual(summary, {"capability": 1})


if __name__ == "__main__":
    unittest.main()
