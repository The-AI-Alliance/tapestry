"""Smoke tests: the pipeline runs end to end and is deterministic.

These assert plumbing, not the hypothesis. They must NOT assert any particular
direction of cultural shift — on the toy model that would be testing noise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import (  # noqa: E402
    AggregationConfig,
    ExperimentConfig,
    StatsConfig,
    run_aggregation,
    run_aggregation_resampled,
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
    """Every translated battery (AR, VI, SV) must be item-for-item equivalent to
    the English one (same item_ids, axes, option values), so coordinates are
    comparable across languages."""
    from cultural_cpt import behavior, wvs

    pairs = (
        (wvs._ITEMS, wvs._ITEMS_AR),
        (wvs._ITEMS, wvs._ITEMS_VI),
        (wvs._ITEMS, wvs._ITEMS_SV),
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


def test_generate_behavior_prefers_score_axis_path() -> None:
    """A judge exposing score_axis takes the SemAxis path (full dynamic range);
    the option-softmax score_options is only the fallback for judges without it."""
    from cultural_cpt import behavior
    from cultural_cpt.model import ByteCausalModel

    calls = {"axis": 0, "opts": 0}

    class _AxisStub:
        def score_axis(self, response, neg_anchors, pos_anchors):
            calls["axis"] += 1
            assert len(neg_anchors) >= 1 and len(pos_anchors) >= 1
            return 0.5  # constant lean -> constant coordinate

        def score_options(self, response, option_texts):  # must NOT be called
            calls["opts"] += 1
            return [0.0] * len(option_texts)

    model = ByteCausalModel(hidden_size=32, seed=0)
    coord = behavior.administer_behavior(model, seed=0, paraphrase_passes=1, mode="generate", judge=_AxisStub())
    assert calls["axis"] > 0 and calls["opts"] == 0
    assert coord.ts == 0.5 and coord.ss == 0.5


def test_behavior_axis_anchors_include_semaxis_with_fallback() -> None:
    """Per-scenario anchors lead with the scenario's own extreme-value options and
    append the axis-level SemAxis exemplars; a language without SemAxis falls back
    to just the option text."""
    from cultural_cpt import behavior

    item = behavior._SCENARIOS[0]
    neg, pos = behavior._axis_anchors("en", item)
    assert neg[0] == min(item.options, key=lambda o: o.value).text
    assert pos[0] == max(item.options, key=lambda o: o.value).text
    assert len(neg) > 1 and len(pos) > 1  # SemAxis exemplars appended for en
    neg_fallback, pos_fallback = behavior._axis_anchors("zz", item)  # no SemAxis for 'zz'
    assert len(neg_fallback) == 1 and len(pos_fallback) == 1


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


def test_aggregation_records_shift_and_abs_separability() -> None:
    """Each node carries a shift vs the round's base, and the headline
    separability curve is the SHIFT-space one (calibration-robust), with the
    absolute-coordinate separability reported alongside."""
    result = run_aggregation(_agg_config())
    for metric in result.rounds:
        # headline curve == shift-space separability
        assert metric.abs_pairwise_distance >= 0.0
        for n in metric.nodes:
            assert hasattr(n, "shift_ts") and hasattr(n, "shift_ss")
            assert hasattr(n, "lang")
    assert result.separability_curve == [m.mean_pairwise_distance for m in result.rounds]


def test_sv_battery_scores_toy_model() -> None:
    """The Swedish battery administers end to end and yields a well-formed coord."""
    from cultural_cpt import wvs
    from cultural_cpt.model import ByteCausalModel

    coord = wvs.administer(ByteCausalModel(hidden_size=32, seed=0), seed=0, paraphrase_passes=1, lang="sv").coordinate
    assert -1.0 <= coord.ts <= 1.0 and -1.0 <= coord.ss <= 1.0


def test_culture_lang_resolves_from_manifest_and_requires_battery(tmp_path: Path) -> None:
    """A node is measured in its corpus's language (from the manifest); a corpus
    language with no WVS battery fails loudly instead of silently using English."""
    import json

    import pytest

    from cultural_cpt.aggregation import AggregationConfig, _culture_lang

    (tmp_path / "sweden").mkdir()
    (tmp_path / "sweden" / "manifest.json").write_text(json.dumps({"language": "sv"}))
    (tmp_path / "atlantis").mkdir()
    (tmp_path / "atlantis" / "manifest.json").write_text(json.dumps({"language": "zz"}))

    cfg = AggregationConfig(corpus_path=str(tmp_path), instrument_lang="en")
    assert _culture_lang(cfg, "sweden") == "sv"
    # smoke / placeholder fallback (no corpus_path)
    assert _culture_lang(AggregationConfig(instrument_lang="en"), "sweden") == "en"
    with pytest.raises(ValueError, match="no WVS battery"):
        _culture_lang(cfg, "atlantis")


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


def test_aggregation_resampled_bands_curves_and_resumes(tmp_path: Path) -> None:
    """The resampled sweep runs N draws and reports a per-round mean/std band on
    each metric, and resumes from the per-draw cache instead of recomputing."""
    cfg = _agg_config(rounds=2)
    res = run_aggregation_resampled(cfg, draws=3, sample_fraction=0.7, cache_dir=tmp_path)
    assert res.sample_seeds == [0, 1, 2]
    assert len(res.rounds) == 2
    assert len(res.shift_separability_band) == 2
    for b in res.rounds:
        assert b.shift_sep_std >= 0.0 and b.abs_sep_std >= 0.0
        assert b.retained_std >= 0.0
    # Every draw cached for free resume; a second call must reload, not recompute.
    assert (tmp_path / "draws" / "draw_0.json").exists()
    again = run_aggregation_resampled(cfg, draws=3, sample_fraction=0.7, cache_dir=tmp_path)
    assert again.to_dict() == res.to_dict()


def test_aggregation_resampled_validates_args() -> None:
    cfg = _agg_config(rounds=2)
    with pytest.raises(ValueError, match="draws >= 2"):
        run_aggregation_resampled(cfg, draws=1, sample_fraction=0.7)
    with pytest.raises(ValueError, match="sample_fraction"):
        run_aggregation_resampled(cfg, draws=3, sample_fraction=1.0)


def test_fedavg_averages_floats_and_preserves_int_buffers() -> None:
    # FedAvg must average trainable float weights but leave integer buffers (which
    # a real HF model carries) untouched -- averaging them is meaningless and would
    # corrupt the dtype. Without this guard the real-mode loop breaks on the first round.
    import torch

    from cultural_cpt.aggregation import _fedavg

    states = [
        {"w": torch.tensor([0.0, 2.0]), "ids": torch.tensor([5, 6])},
        {"w": torch.tensor([2.0, 6.0]), "ids": torch.tensor([5, 6])},
    ]
    out = _fedavg(states)
    assert torch.allclose(out["w"], torch.tensor([1.0, 4.0]))
    assert out["ids"].dtype == torch.long
    assert torch.equal(out["ids"], torch.tensor([5, 6]))


def test_merge_diagnostics_aligned_vs_opposed() -> None:
    # The interference instrument: identical fork updates reinforce (cosine 1,
    # unanimous sign, full retention); opposite updates cancel (cosine -1, balanced
    # sign-conflict, zero retention). This is what tells homogenization apart from
    # merge interference when the coordinate separability collapses.
    import torch

    from cultural_cpt.aggregation import _merge_diagnostics

    base = {"w": torch.zeros(4), "ids": torch.tensor([1, 2, 3, 4])}
    up = torch.tensor([1.0, -1.0, 1.0, -1.0])

    cos, sign, retained = _merge_diagnostics(
        base, [{"w": up, "ids": base["ids"]}, {"w": up.clone(), "ids": base["ids"]}]
    )
    assert abs(cos - 1.0) < 1e-6 and abs(sign - 1.0) < 1e-6 and abs(retained - 1.0) < 1e-6

    cos, sign, retained = _merge_diagnostics(base, [{"w": up, "ids": base["ids"]}, {"w": -up, "ids": base["ids"]}])
    assert abs(cos + 1.0) < 1e-6 and abs(sign) < 1e-6 and abs(retained) < 1e-6


def test_aggregation_round_metric_carries_diagnostics() -> None:
    # Smoke run still populates the merge diagnostics (real-valued, even if noise
    # on the toy model) so the curve and the interference companion travel together.
    result = run_aggregation(_agg_config())
    m = result.rounds[-1]
    assert -1.0 <= m.mean_update_cosine <= 1.0
    assert 0.0 <= m.update_sign_agreement <= 1.0
    assert m.retained_update_ratio >= 0.0


def test_aggregation_resume_is_identical(tmp_path: Path) -> None:
    # A cached full run, re-run against the same cache, must reproduce the curve
    # exactly (it resumes from the checkpoint instead of recomputing).
    cache = tmp_path / "rounds"
    fresh = run_aggregation(_agg_config(seed=3), cache_dir=cache)
    assert (cache / "global_state.pt").exists()
    assert sorted(p.name for p in cache.glob("round_*.json")) == ["round_1.json", "round_2.json", "round_3.json"]
    resumed = run_aggregation(_agg_config(seed=3), cache_dir=cache)
    assert resumed.to_dict() == fresh.to_dict()


def test_aggregation_partial_resume_matches_fresh(tmp_path: Path) -> None:
    # Resuming a 2-round checkpoint to 3 rounds must match a fresh 3-round run --
    # the preemption-recovery path the spot box relies on.
    fresh = run_aggregation(_agg_config(rounds=3, seed=3))
    cache = tmp_path / "rounds"
    run_aggregation(_agg_config(rounds=2, seed=3), cache_dir=cache)
    extended = run_aggregation(_agg_config(rounds=3, seed=3), cache_dir=cache)
    assert extended.separability_curve == fresh.separability_curve
    assert extended.to_dict() == fresh.to_dict()


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
