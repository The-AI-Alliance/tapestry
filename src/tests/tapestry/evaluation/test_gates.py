"""Tests for tool-neutral evaluation gates."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tapestry.evaluation import (
    BenchmarkConfig,
    BenchmarkKind,
    BenchmarkSpec,
    EvaluationBundle,
    EvaluationGate,
    EvaluationResult,
    GateStatus,
    IntervalPolicy,
    benchmark_config_hash,
)

# pylint: disable=missing-class-docstring,missing-function-docstring


def _interval_spec(higher_is_better=True):
    return BenchmarkSpec(
        benchmark_id="x",
        name="Example",
        kind=BenchmarkKind.CAPABILITY,
        metric="accuracy",
        config=BenchmarkConfig("v1", "rev", "prompt"),
        threshold=0.7,
        higher_is_better=higher_is_better,
        interval_policy=IntervalPolicy("bootstrap", 0.95, {"resamples": "1000"}),
    )


@pytest.mark.parametrize(
    "higher,lower,upper,expected",
    [
        (True, 0.7, 0.8, GateStatus.PASS),
        (True, 0.6, 0.7, GateStatus.INDETERMINATE),
        (True, 0.5, 0.6, GateStatus.FAIL),
        (False, 0.6, 0.7, GateStatus.PASS),
        (False, 0.7, 0.8, GateStatus.INDETERMINATE),
        (False, 0.8, 0.9, GateStatus.FAIL),
        (True, None, None, GateStatus.INDETERMINATE),
        (False, 0.5, None, GateStatus.INDETERMINATE),
        (True, None, 0.9, GateStatus.INDETERMINATE),
        (True, 0.7, 0.7, GateStatus.PASS),
        (False, 0.7, 0.7, GateStatus.PASS),
    ],
)
def test_interval_decision_boundary_and_missing_bounds(higher, lower, upper, expected):
    gate = EvaluationGate([_interval_spec(higher)])
    result = EvaluationResult("x", 0.7, lower_bound=lower, upper_bound=upper)
    decision = gate.decide_bundle(_bundle(gate, [result]))
    assert decision.findings[0].status == expected
    assert decision.passed == (expected == GateStatus.PASS)
    assert bool(decision.blocking_findings) == (expected != GateStatus.PASS)


@pytest.mark.parametrize("lower,upper", [(0.8, 0.7), (float("nan"), 1.0), (0.0, float("inf"))])
def test_invalid_interval_is_rejected(lower, upper):
    with pytest.raises(ValueError):
        EvaluationResult("x", 0.7, lower_bound=lower, upper_bound=upper)


def test_interval_configuration_hash_and_legacy_hash():
    interval = _interval_spec()
    scalar = replace(interval, interval_policy=None)
    assert benchmark_config_hash([scalar]) == "70c0f8a997014d5b67c3b71dae94eb0b2afbbda55878e67867bcc48262700c63"
    assert benchmark_config_hash([interval]) != benchmark_config_hash([scalar])
    changed_method = replace(interval, interval_policy=IntervalPolicy("other", 0.95, {"resamples": "1000"}))
    changed_level = replace(interval, interval_policy=IntervalPolicy("bootstrap", 0.9, {"resamples": "1000"}))
    changed_settings = replace(interval, interval_policy=IntervalPolicy("bootstrap", 0.95, {"resamples": "2000"}))
    assert len({benchmark_config_hash([s]) for s in (interval, changed_method, changed_level, changed_settings)}) == 4


def test_scalar_default_ignores_valid_bounds():
    gate = EvaluationGate([replace(_interval_spec(), interval_policy=None)])
    result = EvaluationResult("x", 0.8, lower_bound=0.5, upper_bound=0.9)
    assert gate.decide([result]).passed


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
    results: list[EvaluationResult],
    config_hash: str | None = None,
    schema_version: str = "evaluation-gate/v1",
) -> EvaluationBundle:
    return EvaluationBundle(
        results=results,
        config_hash=config_hash or gate.config_hash,
        model_artifact_id="model://tapestry/m0-smoke@sha256:abc123",
        runner_id="lm-evaluation-harness",
        runner_version="0.4.9",
        schema_version=schema_version,
    )


def test_gate_passes_when_required_scores_meet_thresholds():
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

    assert decision.passed
    assert [finding.status for finding in decision.findings] == [GateStatus.PASS, GateStatus.PASS]
    assert len(decision.blocking_findings) == 0


def test_gate_blocks_missing_required_benchmark():
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

    assert not decision.passed
    assert decision.blocking_findings[0].status == GateStatus.MISSING


def test_optional_benchmark_is_not_required_to_pass_gate():
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

    assert decision.passed
    assert len(decision.findings) == 0


def test_gate_reports_unexpected_results_without_blocking():
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

    assert decision.passed
    assert decision.findings[-1].status == GateStatus.UNEXPECTED


def test_duplicate_specs_and_results_are_rejected():
    spec = BenchmarkSpec(
        benchmark_id="capability-core",
        name="Capability Core",
        kind=BenchmarkKind.CAPABILITY,
        metric="accuracy",
        config=_config(task_version="capability-core/v1"),
        threshold=0.6,
    )

    with pytest.raises(ValueError):
        EvaluationGate([spec, spec])

    gate = EvaluationGate([spec])

    with pytest.raises(ValueError):
        gate.decide(
            [
                EvaluationResult("capability-core", 0.7),
                EvaluationResult("capability-core", 0.8),
            ]
        )


def test_config_hash_is_stable_across_spec_order():
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

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_config_hash_changes_when_evaluation_setup_changes():
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

    assert benchmark_config_hash([base]) != benchmark_config_hash([changed_prompt])
    assert benchmark_config_hash([base]) != benchmark_config_hash([changed_shots])


def test_gate_decides_versioned_bundle_with_matching_config_hash():
    spec = BenchmarkSpec(
        benchmark_id="capability-core",
        name="Capability Core",
        kind=BenchmarkKind.CAPABILITY,
        metric="accuracy",
        config=_config(task_version="capability-core/v1"),
        threshold=0.6,
    )
    gate = EvaluationGate([spec])
    bundle = _bundle(gate, [EvaluationResult("capability-core", 0.7)])

    decision = gate.decide_bundle(bundle)

    assert decision.passed
    assert decision.findings[0].status == GateStatus.PASS


def test_gate_accepts_legacy_m0_schema_version():
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
        [EvaluationResult("capability-core", 0.7)],
        schema_version="m0-evaluation-gate/v1",
    )

    decision = gate.decide_bundle(bundle)

    assert decision.passed
    assert decision.findings[0].status == GateStatus.PASS


def test_gate_blocks_bundle_with_mismatched_config_hash():
    spec = BenchmarkSpec(
        benchmark_id="capability-core",
        name="Capability Core",
        kind=BenchmarkKind.CAPABILITY,
        metric="accuracy",
        config=_config(task_version="capability-core/v1"),
        threshold=0.6,
    )
    gate = EvaluationGate([spec])
    bundle = _bundle(gate, [EvaluationResult("capability-core", 0.7)], config_hash="0" * 64)

    decision = gate.decide_bundle(bundle)

    assert not decision.passed
    assert decision.blocking_findings[0].status == GateStatus.INVALID


def test_gate_blocks_bundle_with_unsupported_schema_version():
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
        [EvaluationResult("capability-core", 0.7)],
        schema_version="m0-evaluation-gate/v0",
    )

    decision = gate.decide_bundle(bundle)

    assert not decision.passed
    assert decision.blocking_findings[0].status == GateStatus.INVALID


def test_bundle_requires_model_and_runner_identity():
    spec = BenchmarkSpec(
        benchmark_id="capability-core",
        name="Capability Core",
        kind=BenchmarkKind.CAPABILITY,
        metric="accuracy",
        config=_config(task_version="capability-core/v1"),
        threshold=0.6,
    )
    gate = EvaluationGate([spec])

    with pytest.raises(ValueError):
        EvaluationBundle(
            results=[EvaluationResult("capability-core", 0.7)],
            config_hash=gate.config_hash,
            model_artifact_id=" ",
            runner_id="lm-evaluation-harness",
            runner_version="0.4.9",
        )

    with pytest.raises(ValueError):
        EvaluationBundle(
            results=[EvaluationResult("capability-core", 0.7)],
            config_hash=gate.config_hash,
            model_artifact_id="model://tapestry/m0-smoke@sha256:abc123",
            runner_id="lm-evaluation-harness",
            runner_version=" ",
        )
