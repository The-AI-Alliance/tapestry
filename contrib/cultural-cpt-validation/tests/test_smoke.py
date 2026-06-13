"""Smoke tests: the pipeline runs end to end and is deterministic.

These assert plumbing, not the hypothesis. They must NOT assert any particular
direction of cultural shift — on the toy model that would be testing noise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import (  # noqa: E402
    AggregationConfig,
    ExperimentConfig,
    run_aggregation,
    run_experiment,
)


def _config(**kw) -> ExperimentConfig:
    base = dict(mode="smoke", culture="vietnam", seed=0, epochs=2, hidden_size=32)
    base.update(kw)
    return ExperimentConfig(**base)


def test_runs_all_arms() -> None:
    result = run_experiment(_config())
    arms = [a.arm for a in result.arms]
    assert arms == ["base", "language_matched", "grounded", "grounded_translated", "surface_only"]


def test_surface_only_arm_does_no_cpt() -> None:
    result = run_experiment(_config())
    by_arm = {a.arm: a for a in result.arms}
    # surface_only steers via prompt, not weights -> no training loss.
    assert by_arm["surface_only"].train_loss is None
    assert by_arm["grounded_translated"].train_loss is not None


def test_coordinates_and_capability_are_well_formed() -> None:
    result = run_experiment(_config())
    for arm in result.arms:
        assert -1.0 <= arm.ts <= 1.0
        assert -1.0 <= arm.ss <= 1.0
        assert -1.0 <= arm.behavior_ts <= 1.0
        assert -1.0 <= arm.behavior_ss <= 1.0
        assert arm.survey_behavior_gap >= 0.0
        assert 0.0 <= arm.capability_acc <= 1.0
        assert arm.distance_to_target >= 0.0
    # CPT arms record a training loss; base does not.
    by_arm = {a.arm: a for a in result.arms}
    assert by_arm["base"].train_loss is None
    assert by_arm["grounded"].train_loss is not None
    assert by_arm["language_matched"].train_loss is not None


def test_smoke_mode_carries_caveat() -> None:
    result = run_experiment(_config())
    assert "NOT A RESULT" in result.smoke_caveat
    assert "toy model" in result.smoke_caveat
    assert "placeholder corpora" in result.smoke_caveat


def test_deterministic_for_fixed_seed() -> None:
    a = run_experiment(_config(seed=3))
    b = run_experiment(_config(seed=3))
    assert a.to_dict() == b.to_dict()


def test_unknown_culture_rejected() -> None:
    try:
        run_experiment(_config(culture="atlantis"))
    except ValueError as exc:
        assert "ground-truth" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for unknown culture")


# --- aggregation-survival experiment ---------------------------------------


def _agg_config(**kw) -> AggregationConfig:
    base = dict(mode="smoke", cultures=("vietnam", "sweden", "usa"), rounds=3, epochs=2, hidden_size=32)
    base.update(kw)
    return AggregationConfig(**base)


def test_aggregation_runs_and_produces_curve() -> None:
    result = run_aggregation(_agg_config())
    assert len(result.rounds) == 3
    assert len(result.separability_curve) == 3
    for metric in result.rounds:
        assert len(metric.nodes) == 3
        assert metric.mean_pairwise_distance >= 0.0
        assert metric.mean_distance_to_centroid >= 0.0


def test_aggregation_is_deterministic() -> None:
    a = run_aggregation(_agg_config(seed=5))
    b = run_aggregation(_agg_config(seed=5))
    assert a.to_dict() == b.to_dict()


def test_aggregation_needs_two_cultures() -> None:
    try:
        run_aggregation(_agg_config(cultures=("vietnam",)))
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for single culture")
