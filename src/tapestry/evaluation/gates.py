"""Tool-neutral evaluation release gates.

The evaluation work needs a small, machine-readable contract that does not
depend on a specific benchmark runner. This module records benchmark
requirements and evaluates runner output against those requirements.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from types import MappingProxyType

SCHEMA_VERSION = "evaluation-gate/v1"
LEGACY_SCHEMA_VERSIONS = frozenset({"m0-evaluation-gate/v1"})
BUNDLE_FINDING_ID = "__evaluation_bundle__"


class BenchmarkKind(str, Enum):
    """Evaluation areas Tapestry needs to gate for releases."""

    CAPABILITY = "capability"
    CULTURAL_ALIGNMENT = "cultural-alignment"
    SAFETY = "safety"
    DATA_SOVEREIGNTY = "data-sovereignty"
    PRIVACY = "privacy"
    DOMAIN = "domain"


class GateStatus(str, Enum):
    """Per-benchmark gate outcome."""

    PASS = "pass"
    FAIL = "fail"
    INVALID = "invalid"
    MISSING = "missing"
    UNEXPECTED = "unexpected"


@dataclass(frozen=True)
class BenchmarkConfig:
    """The versioned evaluation setup bound into a benchmark config hash."""

    task_version: str
    dataset_revision: str
    prompt_template: str
    few_shot_count: int = 0
    runner_config: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("task_version", self.task_version)
        _require_text("dataset_revision", self.dataset_revision)
        _require_text("prompt_template", self.prompt_template)
        if self.few_shot_count < 0:
            raise ValueError("few_shot_count must not be negative")
        object.__setattr__(self, "runner_config", _freeze_metadata(self.runner_config))

    def to_hash_payload(self) -> dict[str, object]:
        """Return the JSON-serializable setup payload for config hashing."""
        return {
            "dataset_revision": self.dataset_revision,
            "few_shot_count": self.few_shot_count,
            "prompt_template": self.prompt_template,
            "runner_config": dict(self.runner_config),
            "task_version": self.task_version,
        }


@dataclass(frozen=True)
class BenchmarkSpec:  # pylint: disable=too-many-instance-attributes
    """A benchmark result required or accepted by an evaluation gate."""

    benchmark_id: str
    name: str
    kind: BenchmarkKind | str
    metric: str
    config: BenchmarkConfig
    threshold: float
    higher_is_better: bool = True
    required: bool = True

    def __post_init__(self) -> None:
        _require_text("benchmark_id", self.benchmark_id)
        _require_text("name", self.name)
        _require_text("metric", self.metric)
        _require_finite("threshold", self.threshold)
        object.__setattr__(self, "kind", BenchmarkKind(self.kind))

    def accepts(self, score: float) -> bool:
        """Return whether ``score`` meets the benchmark threshold."""
        _require_finite("score", score)
        if self.higher_is_better:
            return score >= self.threshold
        return score <= self.threshold


@dataclass(frozen=True)
class EvaluationResult:
    """A runner-produced score for one benchmark."""

    benchmark_id: str
    score: float
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("benchmark_id", self.benchmark_id)
        _require_finite("score", self.score)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class EvaluationBundle:
    """Versioned runner output for a benchmark configuration."""

    results: tuple[EvaluationResult, ...]
    config_hash: str
    model_artifact_id: str
    runner_id: str
    runner_version: str
    schema_version: str = SCHEMA_VERSION
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("config_hash", self.config_hash)
        _require_text("model_artifact_id", self.model_artifact_id)
        _require_text("runner_id", self.runner_id)
        _require_text("runner_version", self.runner_version)
        _require_text("schema_version", self.schema_version)
        duplicate_ids = _duplicates(result.benchmark_id for result in self.results)
        if duplicate_ids:
            raise ValueError(f"duplicate benchmark results: {', '.join(duplicate_ids)}")
        object.__setattr__(self, "results", tuple(self.results))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class GateFinding:
    """One release-gate finding for a benchmark requirement or result."""

    benchmark_id: str
    status: GateStatus
    message: str
    score: float | None = None
    threshold: float | None = None


@dataclass(frozen=True)
class GateDecision:
    """Overall go/no-go result for an evaluation gate."""

    passed: bool
    findings: tuple[GateFinding, ...]

    @property
    def blocking_findings(self) -> tuple[GateFinding, ...]:
        """Findings that prevent the gate from passing."""
        return tuple(
            finding
            for finding in self.findings
            if finding.status in {GateStatus.FAIL, GateStatus.INVALID, GateStatus.MISSING}
        )


class EvaluationGate:
    """Evaluate a result bundle against benchmark requirements."""

    def __init__(self, specs: list[BenchmarkSpec]) -> None:
        if not specs:
            raise ValueError("EvaluationGate requires at least one benchmark spec")
        duplicate_ids = _duplicates(spec.benchmark_id for spec in specs)
        if duplicate_ids:
            raise ValueError(f"duplicate benchmark specs: {', '.join(duplicate_ids)}")
        self._specs = {spec.benchmark_id: spec for spec in specs}

    @property
    def specs(self) -> Mapping[str, BenchmarkSpec]:
        """Benchmark specs keyed by benchmark id."""
        return MappingProxyType(self._specs)

    @property
    def config_hash(self) -> str:
        """Deterministic hash for the gate's benchmark configuration."""
        return benchmark_config_hash(self._specs.values())

    def decide(self, results: list[EvaluationResult]) -> GateDecision:
        """Return the go/no-go decision for ``results``."""
        duplicate_ids = _duplicates(result.benchmark_id for result in results)
        if duplicate_ids:
            raise ValueError(f"duplicate benchmark results: {', '.join(duplicate_ids)}")

        result_by_id = {result.benchmark_id: result for result in results}
        findings: list[GateFinding] = []

        for benchmark_id, spec in self._specs.items():
            result = result_by_id.get(benchmark_id)
            if result is None:
                if spec.required:
                    findings.append(
                        GateFinding(
                            benchmark_id=benchmark_id,
                            status=GateStatus.MISSING,
                            threshold=spec.threshold,
                            message=f"required benchmark {benchmark_id} is missing",
                        )
                    )
                continue

            passed = spec.accepts(result.score)
            status = GateStatus.PASS if passed else GateStatus.FAIL
            findings.append(
                GateFinding(
                    benchmark_id=benchmark_id,
                    status=status,
                    score=result.score,
                    threshold=spec.threshold,
                    message=_score_message(spec, result.score, passed),
                )
            )

        for benchmark_id in sorted(set(result_by_id) - set(self._specs)):
            findings.append(
                GateFinding(
                    benchmark_id=benchmark_id,
                    status=GateStatus.UNEXPECTED,
                    score=result_by_id[benchmark_id].score,
                    message=f"result {benchmark_id} is not declared in this gate",
                )
            )

        blocking = any(finding.status in {GateStatus.FAIL, GateStatus.MISSING} for finding in findings)
        return GateDecision(passed=not blocking, findings=tuple(findings))

    def decide_bundle(self, bundle: EvaluationBundle) -> GateDecision:
        """Return the go/no-go decision for a versioned result bundle."""
        findings: list[GateFinding] = []
        if bundle.schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
            findings.append(
                GateFinding(
                    benchmark_id=BUNDLE_FINDING_ID,
                    status=GateStatus.INVALID,
                    message=(f"unsupported evaluation schema {bundle.schema_version}; " f"expected {SCHEMA_VERSION}"),
                )
            )
        if bundle.config_hash != self.config_hash:
            findings.append(
                GateFinding(
                    benchmark_id=BUNDLE_FINDING_ID,
                    status=GateStatus.INVALID,
                    message=(
                        f"evaluation config hash {bundle.config_hash} does not "
                        f"match gate config hash {self.config_hash}"
                    ),
                )
            )
        if findings:
            return GateDecision(passed=False, findings=tuple(findings))
        return self.decide(list(bundle.results))


def benchmark_config_hash(specs: Iterable[BenchmarkSpec]) -> str:
    """Return a stable SHA-256 digest for benchmark gate specs."""
    payload = [
        {
            "benchmark_id": spec.benchmark_id,
            "config": spec.config.to_hash_payload(),
            "higher_is_better": spec.higher_is_better,
            "kind": BenchmarkKind(spec.kind).value,
            "metric": spec.metric,
            "name": spec.name,
            "required": spec.required,
            "threshold": spec.threshold,
        }
        for spec in sorted(specs, key=lambda item: item.benchmark_id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


_SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION, *LEGACY_SCHEMA_VERSIONS})


def _score_message(spec: BenchmarkSpec, score: float, passed: bool) -> str:
    direction = ">=" if spec.higher_is_better else "<="
    outcome = "meets" if passed else "misses"
    return f"{spec.benchmark_id} {outcome} threshold: " f"{score:g} {direction} {spec.threshold:g}"


def _require_text(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _freeze_metadata(metadata: Mapping[str, str]) -> Mapping[str, str]:
    frozen = dict(metadata)
    for key, value in frozen.items():
        _require_text("metadata key", key)
        _require_text(f"metadata[{key!r}]", value)
    return MappingProxyType(frozen)


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)
