"""Smoke tests: the pipeline runs end to end and is deterministic.

These assert plumbing, not the hypothesis. They must NOT assert any particular
direction of cultural shift — on the toy model that would be testing noise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import ExperimentConfig, run_experiment  # noqa: E402


def _config(**kw) -> ExperimentConfig:
    base = dict(mode="smoke", culture="vietnam", seed=0, epochs=2, hidden_size=32)
    base.update(kw)
    return ExperimentConfig(**base)


def test_runs_all_three_arms() -> None:
    result = run_experiment(_config())
    arms = [a.arm for a in result.arms]
    assert arms == ["base", "language_matched", "grounded"]


def test_coordinates_and_capability_are_well_formed() -> None:
    result = run_experiment(_config())
    for arm in result.arms:
        assert -1.0 <= arm.ts <= 1.0
        assert -1.0 <= arm.ss <= 1.0
        assert 0.0 <= arm.capability_acc <= 1.0
        assert arm.distance_to_target >= 0.0
    # CPT arms record a training loss; base does not.
    by_arm = {a.arm: a for a in result.arms}
    assert by_arm["base"].train_loss is None
    assert by_arm["grounded"].train_loss is not None
    assert by_arm["language_matched"].train_loss is not None


def test_smoke_mode_carries_caveat() -> None:
    result = run_experiment(_config())
    assert "SMOKE MODE" in result.smoke_caveat


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
