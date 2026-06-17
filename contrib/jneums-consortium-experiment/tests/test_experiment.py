"""Tests for deterministic consortium-training PoC experiments."""

from __future__ import annotations

import json

import pytest

from consortium_experiment import (
    ConsortiumExperimentRunner,
    ExperimentConfig,
    NodeSpec,
    PolicySpec,
)
from consortium_experiment.metrics import state_delta_norm


def _corpus(offset: int = 0) -> list[list[int]]:
    return [
        [1 + offset, 2 + offset, 3 + offset, 4 + offset],
        [2 + offset, 3 + offset, 4 + offset, 5 + offset],
        [3 + offset, 4 + offset, 5 + offset, 6 + offset],
    ]


def _node(node_id: str, quality_score: float, offset: int = 0) -> NodeSpec:
    return NodeSpec(
        node_id=node_id,
        jurisdiction=node_id.title(),
        corpus=_corpus(offset),
        quality_score=quality_score,
        local_epochs=1,
        lr=0.01,
    )


def _config(policy: PolicySpec, rounds: int = 2, seed: int = 11) -> ExperimentConfig:
    return ExperimentConfig(
        seed=seed,
        rounds=rounds,
        policy=policy,
        nodes=[
            _node("vietnam", 0.9, 0),
            _node("swiss", 0.8, 10),
            _node("india", 0.7, 20),
        ],
        model_vocab_size=64,
        model_hidden_size=16,
    )


def test_experiment_runner_is_deterministic_for_seeded_runs() -> None:
    """The same experiment config should produce the same PoC metrics."""
    config = _config(PolicySpec(name="quality_weighted", quality_floor=0.1))

    first = ConsortiumExperimentRunner(config).run()
    second = ConsortiumExperimentRunner(config).run()

    assert first.summary == second.summary
    assert first.rounds == second.rounds


def test_experiment_records_rejected_low_quality_contribution() -> None:
    """Quality floors should be visible in round metrics and summaries."""
    config = _config(PolicySpec(name="quality_floor", quality_floor=0.75), rounds=1)

    result = ConsortiumExperimentRunner(config).run()
    round_metrics = result.rounds[0]

    assert round_metrics.accepted_nodes == ["vietnam", "swiss"]
    assert round_metrics.rejected_nodes == ["india"]
    assert "india" not in round_metrics.contribution_weights
    assert result.summary.total_rejected_contributions == 1
    assert result.summary.final_artifact_count == 3


def test_experiment_records_anti_capture_cap() -> None:
    """A dominant quality score should be capped by policy and recorded in metrics."""
    config = ExperimentConfig(
        seed=3,
        rounds=1,
        policy=PolicySpec(name="quality_weighted_capped", max_node_weight=0.5),
        nodes=[
            _node("dominant", 10.0, 0),
            _node("peer_a", 1.0, 10),
            _node("peer_b", 1.0, 20),
        ],
        model_vocab_size=64,
        model_hidden_size=16,
    )

    result = ConsortiumExperimentRunner(config).run()
    round_metrics = result.rounds[0]

    assert round_metrics.max_node_weight <= 0.5
    assert result.summary.max_observed_node_weight <= 0.5
    assert round_metrics.contribution_weights["dominant"] == pytest.approx(0.5)
    assert sum(round_metrics.contribution_weights.values()) == pytest.approx(1.0)


def test_experiment_records_n_plus_one_artifacts_and_shared_base_change() -> None:
    """The metrics should preserve N sovereign artifacts and show base movement."""
    config = _config(PolicySpec(name="quality_weighted", quality_floor=0.1), rounds=1)

    result = ConsortiumExperimentRunner(config).run()
    round_metrics = result.rounds[0]

    assert round_metrics.sovereign_artifact_count == len(config.nodes)
    assert result.summary.final_artifact_count == len(config.nodes)
    assert round_metrics.shared_base_delta_norm > 0.0
    assert set(round_metrics.node_losses) == {"vietnam", "swiss", "india"}


def test_experiment_writes_json_metrics_and_summary(tmp_path) -> None:
    """Experiment output should be machine-readable JSONL plus summary JSON."""
    config = _config(PolicySpec(name="quality_weighted", quality_floor=0.1), rounds=2)
    output_dir = tmp_path / "experiment"

    result = ConsortiumExperimentRunner(config).run()
    result.write_json(output_dir)

    metrics_path = output_dir / "metrics.jsonl"
    summary_path = output_dir / "summary.json"
    assert metrics_path.exists()
    assert summary_path.exists()

    metric_lines = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(metric_lines) == 2
    assert metric_lines[0]["round_num"] == 1
    assert metric_lines[1]["round_num"] == 2
    assert summary["rounds"] == 2
    assert summary["policy_name"] == "quality_weighted"


def test_state_delta_norm_rejects_mismatched_model_states() -> None:
    """Metric helpers should fail clearly on incompatible model states."""
    with pytest.raises(ValueError, match="same keys"):
        state_delta_norm({}, {"unexpected": pytest.importorskip("torch").tensor([1.0])})
