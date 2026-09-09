# Evaluation Gate Schema

| Field       | Value           |
| :---------- | :-------------- |
| Status      | Proposal        |
| Confidence  | Medium (3/5)    |
| Created     | July 04, 2026   |
| Last Update | August 04, 2026 |

Issue [#119](https://github.com/The-AI-Alliance/tapestry/issues/119) now tracks the post-M0/M1 evaluation framework. The initial production artifact is the tool-neutral gate schema in `tapestry.evaluation`, which gives benchmark runners a stable result contract before Tapestry commits to a full benchmark stack.

The schema separates four concerns:

| Artifact | Purpose |
| :------- | :------ |
| `BenchmarkConfig` | Binds the task version, dataset revision, prompt/template, few-shot settings, and runner config into the gate hash. |
| `BenchmarkSpec` | Declares the benchmark, metric, threshold, setup config, and whether it blocks release. |
| `EvaluationResult` | Records the score emitted by a benchmark runner such as `lm-evaluation-harness`, Unitxt, or a Tapestry-specific harness. |
| `EvaluationBundle` | Carries versioned runner output with the benchmark configuration hash, model/checkpoint/artifact id, and runner/version that produced it. |
| `EvaluationGate` | Produces a deterministic go/no-go decision from specs and results. |

This lets the work group decide benchmark tools and task packaging separately from release-gate semantics. It also gives future CI, infrastructure, and
certification work a stable result contract to target.

The current schema version is `evaluation-gate/v1`. Bundles that still declare `m0-evaluation-gate/v1` remain valid as a legacy alias for the original M0 contract.

## Example

```python
from tapestry.evaluation import (
    BenchmarkConfig,
    BenchmarkKind,
    BenchmarkSpec,
    EvaluationBundle,
    EvaluationGate,
    EvaluationResult,
)

capability_config = BenchmarkConfig(
    task_version="mmlu-lite/v1",
    dataset_revision="2026-07-01",
    prompt_template="default-zero-shot",
    few_shot_count=0,
    runner_config={"temperature": "0"},
)
safety_config = BenchmarkConfig(
    task_version="toxicity-rate/v1",
    dataset_revision="2026-07-01",
    prompt_template="safety-zero-shot",
    few_shot_count=0,
    runner_config={"temperature": "0"},
)

gate = EvaluationGate(
    [
        BenchmarkSpec(
            benchmark_id="capability-core",
            name="Core capability suite",
            kind=BenchmarkKind.CAPABILITY,
            metric="accuracy",
            config=capability_config,
            threshold=0.62,
        ),
        BenchmarkSpec(
            benchmark_id="toxicity-rate",
            name="Safety toxicity rate",
            kind=BenchmarkKind.SAFETY,
            metric="rate",
            config=safety_config,
            threshold=0.05,
            higher_is_better=False,
        ),
    ]
)

bundle = EvaluationBundle(
    config_hash=gate.config_hash,
    model_artifact_id="model://tapestry/m0-smoke@sha256:abc123",
    runner_id="lm-evaluation-harness",
    runner_version="0.4.9",
    results=(
        EvaluationResult("capability-core", 0.64),
        EvaluationResult("toxicity-rate", 0.03),
    ),
)

decision = gate.decide_bundle(bundle)
assert decision.passed
```

## Near-Term Use

- Keep #119 benchmark selection discussions focused on concrete
  `BenchmarkSpec` entries.
- Require runners to emit `EvaluationResult` records, regardless of the
  underlying tool.
- Include the gate's `config_hash`, model/checkpoint/artifact id, runner id, and
  runner version in each `EvaluationBundle`, so pre-registered thresholds and
  result bundles can be compared across member runs.
- Keep evidence visibility out of this gate contract until TAP-010 evidence
  modes are typed and mapped to release-gate semantics.
- Treat missing required results and threshold misses as blocking findings.
- Treat unexpected runner output as reportable but non-blocking, so experiments
  can include extra measurements without breaking the release gate.
