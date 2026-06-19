"""Smoke tests: the pipeline runs end to end and is deterministic.

These assert plumbing, not the hypothesis. They must NOT assert any particular
direction of cultural shift — on the toy model that would be testing noise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import (  # noqa: E402
    AggregationConfig,
    ExperimentConfig,
    StatsConfig,
    run_aggregation,
    run_corpus_resampled,
    run_experiment,
    run_multiseed,
)


def _config(**kw) -> ExperimentConfig:
    base = dict(mode="smoke", culture="vietnam", seed=0, epochs=2, hidden_size=32)
    base.update(kw)
    return ExperimentConfig(**base)


def _stats_config(**kw) -> StatsConfig:
    return StatsConfig(base=_config(**kw), seeds=(0, 1, 2))


def test_runs_all_arms() -> None:
    result = run_experiment(_config())
    arms = [a.arm for a in result.arms]
    assert arms == ["base", "language_matched", "grounded", "grounded_translated", "neutral_prose", "surface_only"]


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
        assert 0.0 <= arm.safety_refusal <= 1.0
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


def test_translated_batteries_match_english_structure() -> None:
    """Every translated battery (AR, VI) must be item-for-item equivalent to the
    English one (same item_ids, axes, option values), so coordinates are
    comparable across languages."""
    from cultural_cpt import behavior, wvs

    pairs = (
        (wvs._ITEMS, wvs._ITEMS_AR),
        (wvs._ITEMS, wvs._ITEMS_VI),
        (behavior._SCENARIOS, behavior._SCENARIOS_AR),
        (behavior._SCENARIOS, behavior._SCENARIOS_VI),
    )
    for en_items, tr_items in pairs:
        assert [i.item_id for i in en_items] == [i.item_id for i in tr_items]
        for en, tr in zip(en_items, tr_items):
            assert en.axis == tr.axis
            assert [o.value for o in en.options] == [o.value for o in tr.options]
            # text actually translated (not left in English)
            assert all(t.text != e.text for t, e in zip(tr.options, en.options))


def test_non_english_instruments_run_and_are_well_formed() -> None:
    for lang in ("ar", "vi"):
        result = run_experiment(_config(instrument_lang=lang))
        for arm in result.arms:
            assert -1.0 <= arm.ts <= 1.0 and -1.0 <= arm.ss <= 1.0
        # deterministic for a fixed seed/lang
        assert run_experiment(_config(instrument_lang=lang)).to_dict() == result.to_dict()


def test_generate_behavior_mode_with_stub_judge() -> None:
    """The free-form behavior path (model.generate -> judge -> coordinate) runs
    end to end on the toy model with a stub judge (no embedder needed)."""
    from cultural_cpt import behavior
    from cultural_cpt.model import ByteCausalModel

    class _StubJudge:
        # Deterministic: score each option by character overlap with the response.
        def score_options(self, response, option_texts):
            rset = set(response)
            return [float(len(rset & set(t))) for t in option_texts]

    model = ByteCausalModel(hidden_size=32, seed=0)
    coord = behavior.administer_behavior(model, seed=0, paraphrase_passes=1, mode="generate", judge=_StubJudge())
    assert -1.0 <= coord.ts <= 1.0 and -1.0 <= coord.ss <= 1.0
    # generate mode requires a judge
    import pytest

    with pytest.raises(ValueError, match="requires a judge"):
        behavior.administer_behavior(model, mode="generate", judge=None)


def test_model_generate_primitive() -> None:
    from cultural_cpt.model import ByteCausalModel

    out = ByteCausalModel(hidden_size=32, seed=1).generate("hello", max_new_tokens=8)
    assert isinstance(out, str)


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


# --- multi-seed statistics / go-no-go decision -----------------------------


def test_multiseed_aggregates_and_decides() -> None:
    config = StatsConfig(
        base=ExperimentConfig(mode="smoke", culture="vietnam", epochs=2, hidden_size=32),
        seeds=(0, 1, 2),
    )
    result = run_multiseed(config)
    assert result.seeds == [0, 1, 2]
    arms = [a.arm for a in result.arms]
    assert "grounded" in arms and "language_matched" in arms
    # std is defined (>= 0) across multiple seeds.
    for arm in result.arms:
        assert arm.survey_shift_std >= 0.0
    names = {c.name for c in result.comparisons}
    assert names == {
        "grounded_vs_language",
        "grounded_vs_translated",
        "grounded_vs_neutral_prose",
        "grounded_vs_surface",
    }
    assert isinstance(result.passed, bool)


def test_multiseed_deterministic() -> None:
    config = StatsConfig(
        base=ExperimentConfig(mode="smoke", culture="vietnam", epochs=2, hidden_size=32),
        seeds=(0, 1, 2),
    )
    assert run_multiseed(config).to_dict() == run_multiseed(config).to_dict()


# --- corpus-resampled go/no-go (the cross-corpus noise band) ----------------


def _equal_token_corpus(tmp_path: Path) -> Path:
    """A tiny twin corpus with equal per-doc token counts, culture in GROUND_TRUTH.

    Equal token lengths keep the matched-twin ratio at 1.0 under any equal-size
    subsample, so resampling exercises the plumbing without tripping the twin
    control. Text is neutral filler (no WVS leakage); numbers here carry no claim.
    """
    grounded = [
        {
            "id": f"g{i}",
            "text": "alpha beta gamma delta epsilon zeta eta theta",
            "source": "s",
            "license": "CC-BY-SA-4.0",
            "lang": "en",
            "domain": "law",
        }
        for i in range(10)
    ]
    matched = [
        {
            "id": f"m{i}",
            "text": "one two three four five six seven eight",
            "source": "s",
            "license": "CC-BY-SA-4.0",
            "lang": "en",
            "domain": "weather",
        }
        for i in range(10)
    ]
    (tmp_path / "grounded.jsonl").write_text("".join(json.dumps(d) + "\n" for d in grounded), encoding="utf-8")
    (tmp_path / "language_matched.jsonl").write_text("".join(json.dumps(d) + "\n" for d in matched), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "culture": "egypt",
                "language": "en",
                "arms": {
                    "grounded": {
                        "file": "grounded.jsonl",
                        "lang": "en",
                        "register": "encyclopedic",
                        "value_laden": True,
                    },
                    "language_matched": {
                        "file": "language_matched.jsonl",
                        "lang": "en",
                        "register": "encyclopedic",
                        "value_laden": False,
                    },
                },
                "twin_matching": {"token_ratio_tolerance": 0.20},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_corpus_resampled_aggregates_over_draws(tmp_path: Path) -> None:
    root = _equal_token_corpus(tmp_path)
    config = StatsConfig(
        base=ExperimentConfig(mode="smoke", culture="egypt", corpus_path=str(root), epochs=1, hidden_size=32),
        seeds=(0, 1),
    )
    result = run_corpus_resampled(config, draws=3, sample_fraction=0.6)
    assert [d.draw for d in result.draws] == [0, 1, 2]
    assert {c.name for c in result.comparisons} == {
        "grounded_vs_language",
        "grounded_vs_translated",
        "grounded_vs_neutral_prose",
        "grounded_vs_surface",
    }
    # The reported band is the cross-draw std (>= 0), and the verdict names it.
    assert result.grounded_shift_std >= 0.0
    assert "cross-corpus-draw band" in result.verdict
    assert isinstance(result.passed, bool)


def test_corpus_resampled_rejects_full_pool() -> None:
    config = StatsConfig(base=ExperimentConfig(mode="smoke", culture="egypt"), seeds=(0,))
    try:
        run_corpus_resampled(config, draws=2, sample_fraction=1.0)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("full pool should be rejected for resampling")


def test_corpus_resampled_deterministic(tmp_path: Path) -> None:
    root = _equal_token_corpus(tmp_path)
    config = StatsConfig(
        base=ExperimentConfig(mode="smoke", culture="egypt", corpus_path=str(root), epochs=1, hidden_size=32),
        seeds=(0, 1),
    )
    a = run_corpus_resampled(config, draws=2, sample_fraction=0.6)
    b = run_corpus_resampled(config, draws=2, sample_fraction=0.6)
    assert a.to_dict() == b.to_dict()


# --- neutral_prose register-control arm -------------------------------------


def test_neutral_prose_arm_runs_and_compares() -> None:
    """The register-control arm trains and contributes its own decisive comparison
    (grounded vs the value-neutral discursive twin)."""
    result = run_experiment(_config())
    by_arm = {a.arm: a for a in result.arms}
    assert "neutral_prose" in by_arm
    assert by_arm["neutral_prose"].train_loss is not None  # it does CPT
    # The comparison is reported (non-skipped: the placeholder corpus provides it).
    stats = run_multiseed(_stats_config())
    assert "grounded_vs_neutral_prose" in {c.name for c in stats.comparisons}


# --- replay / anchor mitigation arm + training stabilization (Run 8 follow-up) --


def test_replay_arm_off_by_default() -> None:
    """With replay_fraction=0 (default) the run keeps its five arms and the
    comparison set is unchanged — existing baselines stay comparable."""
    result = run_experiment(_config())
    arms = [a.arm for a in result.arms]
    assert "grounded_replay" not in arms
    # The unused replay decisive fields default to 0.0.
    assert result.decisive_replay_vs_language == 0.0
    assert result.decisive_replay_vs_grounded == 0.0


def test_replay_arm_runs_when_enabled() -> None:
    """replay_fraction>0 appends the grounded_replay arm (placeholder replay
    corpus in smoke), with a training loss and well-formed coordinates."""
    result = run_experiment(_config(replay_fraction=0.3))
    by_arm = {a.arm: a for a in result.arms}
    assert "grounded_replay" in by_arm
    replay = by_arm["grounded_replay"]
    assert replay.train_loss is not None  # it does CPT
    assert -1.0 <= replay.ts <= 1.0 and -1.0 <= replay.ss <= 1.0
    assert 0.0 <= replay.capability_acc <= 1.0
    # deterministic for a fixed seed
    assert run_experiment(_config(replay_fraction=0.3)).to_dict() == result.to_dict()


def test_replay_comparisons_only_present_when_arm_runs() -> None:
    base_names = {c.name for c in run_multiseed(_stats_config()).comparisons}
    assert "replay_vs_language" not in base_names
    with_replay = run_multiseed(_stats_config(replay_fraction=0.3))
    names = {c.name for c in with_replay.comparisons}
    assert {"replay_vs_language", "replay_vs_grounded"} <= names
    assert "grounded_replay" in [a.arm for a in with_replay.arms]


def test_mix_replay_proportions_and_determinism() -> None:
    from cultural_cpt.experiment import _mix_replay

    cfg = _config(replay_fraction=0.5)
    grounded = [f"doc {i}" for i in range(6)]
    mixed = _mix_replay(list(grounded), cfg)
    # 50% replay => replay count == grounded count (n = 6 * .5/.5 = 6), clamped to
    # the placeholder pool size, and the grounded docs are preserved as a prefix.
    assert mixed[:6] == grounded and len(mixed) > 6
    assert _mix_replay(list(grounded), cfg) == mixed  # deterministic
    # replay_fraction=0 is a no-op
    assert _mix_replay(list(grounded), _config(replay_fraction=0.0)) == grounded


def test_stabilization_kwargs_accepted_and_smoke_is_unaffected() -> None:
    """The smoke backend accepts the stabilization knobs (shared protocol) but
    ignores them, so its training stays byte-for-byte reproducible."""
    from cultural_cpt.model import ByteCausalModel

    texts = ["alpha beta gamma", "delta epsilon zeta"]
    plain = ByteCausalModel(hidden_size=32, seed=0)
    stab = ByteCausalModel(hidden_size=32, seed=0)
    loss_plain = plain.train_on_texts(texts, epochs=2, lr=0.01)
    loss_stab = stab.train_on_texts(texts, epochs=2, lr=0.01, warmup_frac=0.1, max_grad_norm=1.0, shuffle_seed=7)
    assert loss_plain == loss_stab
