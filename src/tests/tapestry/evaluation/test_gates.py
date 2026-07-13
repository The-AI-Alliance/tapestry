"""Tests for tool-neutral evaluation gates."""

from __future__ import annotations

import unittest

from tapestry.evaluation import (
    BenchmarkConfig,
    BenchmarkKind,
    BenchmarkSpec,
    EvaluationBundle,
    EvaluationGate,
    EvaluationResult,
    GateStatus,
    benchmark_config_hash,
)

# pylint: disable=missing-class-docstring,missing-function-docstring


def _config(
    task_version: str = "mmlu-lite/v1",
    dataset_revision: str = "2026-07-01",
    prompt_template: str = "default-zero-shot",
    few_shot_count: int = 0,
    runner_config: dict[str, str] | None = None,
) -> BenchmarkConfig:
    return BenchmarkConfig(
        task_version=task_version,
        dataset_revision=dataset_revision,
        prompt_template=prompt_template,
        few_shot_count=few_shot_count,
        runner_config=runner_config or {"temperature": "0", "max_tokens": "8"},
    )


def _bundle(
    gate: EvaluationGate,
    results: tuple[EvaluationResult, ...],
    config_hash: str | None = None,
    schema_version: str = "m0-evaluation-gate/v1",
) -> EvaluationBundle:
    return EvaluationBundle(
        results=results,
        config_hash=config_hash or gate.config_hash,
        model_artifact_id="model://tapestry/m0-smoke@sha256:abc123",
        runner_id="lm-evaluation-harness",
        runner_version="0.4.9",
        schema_version=schema_version,
    )


class EvaluationGateTest(unittest.TestCase):
    def test_gate_passes_when_required_scores_meet_thresholds(self) -> None:
        gate = EvaluationGate(
            [
                BenchmarkSpec(
                    benchmark_id="mmlu-lite",
                    name="MMLU Lite",
                    kind=BenchmarkKind.CAPABILITY,
                    metric="accuracy",
                    config=_config(task_version="mmlu-lite/v1"),
                    threshold=0.62,
                ),
                BenchmarkSpec(
                    benchmark_id="toxicity-rate",
                    name="Toxicity Rate",
                    kind=BenchmarkKind.SAFETY,
                    metric="rate",
                    config=_config(task_version="toxicity-rate/v1"),
                    threshold=0.05,
                    higher_is_better=False,
                ),
            ]
        )

        decision = gate.decide(
            [
                EvaluationResult("mmlu-lite", 0.64),
                EvaluationResult("toxicity-rate", 0.03),
            ]
        )

        self.assertTrue(decision.passed)
        self.assertEqual(
            [finding.status for finding in decision.findings],
            [GateStatus.PASS, GateStatus.PASS],
        )
        self.assertEqual(decision.blocking_findings, ())

    def test_gate_blocks_missing_required_benchmark(self) -> None:
        gate = EvaluationGate(
            [
                BenchmarkSpec(
                    benchmark_id="cultural-alignment-smoke",
                    name="Cultural Alignment Smoke Test",
                    kind=BenchmarkKind.CULTURAL_ALIGNMENT,
                    metric="agreement",
                    config=_config(task_version="cultural-alignment-smoke/v1"),
                    threshold=0.7,
                )
            ]
        )

        decision = gate.decide([])

        self.assertFalse(decision.passed)
        self.assertEqual(decision.blocking_findings[0].status, GateStatus.MISSING)

    def test_optional_benchmark_is_not_required_to_pass_gate(self) -> None:
        gate = EvaluationGate(
            [
                BenchmarkSpec(
                    benchmark_id="domain-extra",
                    name="Domain Extra",
                    kind=BenchmarkKind.DOMAIN,
                    metric="accuracy",
                    config=_config(task_version="domain-extra/v1"),
                    threshold=0.8,
                    required=False,
                )
            ]
        )

        decision = gate.decide([])

        self.assertTrue(decision.passed)
        self.assertEqual(decision.findings, ())

    def test_gate_reports_unexpected_results_without_blocking(self) -> None:
        gate = EvaluationGate(
            [
                BenchmarkSpec(
                    benchmark_id="capability-core",
                    name="Capability Core",
                    kind=BenchmarkKind.CAPABILITY,
                    metric="accuracy",
                    config=_config(task_version="capability-core/v1"),
                    threshold=0.6,
                )
            ]
        )

        decision = gate.decide(
            [
                EvaluationResult("capability-core", 0.7),
                EvaluationResult("unknown-runner-output", 1.0),
            ]
        )

        self.assertTrue(decision.passed)
        self.assertEqual(decision.findings[-1].status, GateStatus.UNEXPECTED)

    def test_duplicate_specs_and_results_are_rejected(self) -> None:
        spec = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )

        with self.assertRaisesRegex(ValueError, "duplicate benchmark specs"):
            EvaluationGate([spec, spec])

        gate = EvaluationGate([spec])
        with self.assertRaisesRegex(ValueError, "duplicate benchmark results"):
            gate.decide(
                [
                    EvaluationResult("capability-core", 0.7),
                    EvaluationResult("capability-core", 0.8),
                ]
            )

    def test_config_hash_is_stable_across_spec_order(self) -> None:
        capability = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )
        safety = BenchmarkSpec(
            benchmark_id="toxicity-rate",
            name="Toxicity Rate",
            kind=BenchmarkKind.SAFETY,
            metric="rate",
            config=_config(task_version="toxicity-rate/v1"),
            threshold=0.05,
            higher_is_better=False,
        )

        first_hash = benchmark_config_hash([capability, safety])
        second_hash = benchmark_config_hash([safety, capability])

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_config_hash_changes_when_evaluation_setup_changes(self) -> None:
        base = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(prompt_template="baseline", few_shot_count=0),
            threshold=0.6,
        )
        changed_prompt = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(prompt_template="cot", few_shot_count=0),
            threshold=0.6,
        )
        changed_shots = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(prompt_template="baseline", few_shot_count=5),
            threshold=0.6,
        )

        self.assertNotEqual(benchmark_config_hash([base]), benchmark_config_hash([changed_prompt]))
        self.assertNotEqual(benchmark_config_hash([base]), benchmark_config_hash([changed_shots]))

    def test_gate_decides_versioned_bundle_with_matching_config_hash(self) -> None:
        spec = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )
        gate = EvaluationGate([spec])
        bundle = _bundle(gate, (EvaluationResult("capability-core", 0.7),))

        decision = gate.decide_bundle(bundle)

        self.assertTrue(decision.passed)
        self.assertEqual(decision.findings[0].status, GateStatus.PASS)

    def test_gate_blocks_bundle_with_mismatched_config_hash(self) -> None:
        spec = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )
        gate = EvaluationGate([spec])
        bundle = _bundle(gate, (EvaluationResult("capability-core", 0.7),), config_hash="0" * 64)

        decision = gate.decide_bundle(bundle)

        self.assertFalse(decision.passed)
        self.assertEqual(decision.blocking_findings[0].status, GateStatus.INVALID)

    def test_gate_blocks_bundle_with_unsupported_schema_version(self) -> None:
        spec = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )
        gate = EvaluationGate([spec])
        bundle = _bundle(
            gate,
            (EvaluationResult("capability-core", 0.7),),
            schema_version="m0-evaluation-gate/v0",
        )

        decision = gate.decide_bundle(bundle)

        self.assertFalse(decision.passed)
        self.assertEqual(decision.blocking_findings[0].status, GateStatus.INVALID)

    def test_bundle_requires_model_and_runner_identity(self) -> None:
        spec = BenchmarkSpec(
            benchmark_id="capability-core",
            name="Capability Core",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=_config(task_version="capability-core/v1"),
            threshold=0.6,
        )
        gate = EvaluationGate([spec])

        with self.assertRaisesRegex(ValueError, "model_artifact_id must not be empty"):
            EvaluationBundle(
                results=(EvaluationResult("capability-core", 0.7),),
                config_hash=gate.config_hash,
                model_artifact_id=" ",
                runner_id="lm-evaluation-harness",
                runner_version="0.4.9",
            )

        with self.assertRaisesRegex(ValueError, "runner_version must not be empty"):
            EvaluationBundle(
                results=(EvaluationResult("capability-core", 0.7),),
                config_hash=gate.config_hash,
                model_artifact_id="model://tapestry/m0-smoke@sha256:abc123",
                runner_id="lm-evaluation-harness",
                runner_version=" ",
            )


if __name__ == "__main__":
    unittest.main()
