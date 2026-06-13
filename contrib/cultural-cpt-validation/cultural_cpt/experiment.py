"""Orchestration for the EXP-001 minimal go/no-go (Base / Language-matched / Grounded).

For each arm: start from the *same* base model, apply the arm's treatment (no
CPT, or CPT on the arm's corpus), then measure the Inglehart-Welzel coordinate
and capability. The decisive comparison is whether **Grounded** moves toward the
target nation's ground-truth coordinate more than **Language-matched** does.

See tech-docs/experiments/cultural-cpt-validation.md (EXP-001) for the full
design, arms, and pre-registered thresholds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import behavior, capability, wvs
from .corpora import load_corpus
from .model import LanguageModel, make_base_model


@dataclass(frozen=True)
class ArmResult:
    """Measurement for one experimental arm."""

    arm: str
    ts: float  # survey coordinate
    ss: float
    distance_to_target: float  # survey
    shift_toward_target: float  # survey, vs. Base; positive = moved toward ground truth
    behavior_ts: float  # behavioral-probe coordinate
    behavior_ss: float
    behavior_shift_toward_target: float  # behavior, vs. Base
    survey_behavior_gap: float  # distance between survey and behavior coords; high = mimicry signal
    capability_acc: float
    train_loss: float | None


@dataclass(frozen=True)
class ExperimentResult:
    """Full result of one EXP-001 minimal run."""

    mode: str
    culture: str
    seed: int
    target_ts: float
    target_ss: float
    arms: list[ArmResult]
    decisive_grounded_vs_language: float = field(default=0.0)
    smoke_caveat: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for one minimal EXP-001 run."""

    mode: str = "smoke"  # model backend: "smoke" | "hf"
    culture: str = "vietnam"
    seed: int = 0
    epochs: int = 4
    lr: float = 0.01
    hidden_size: int = 64
    model_name: str = ""
    corpus_path: str = ""  # empty = placeholder corpora (no claim); else real data
    paraphrase_passes: int = 2


_ARMS = ("base", "language_matched", "grounded")


@dataclass(frozen=True)
class _Measurement:
    survey: wvs.Coordinate
    behavior: wvs.Coordinate
    capability_acc: float


def _measure(model: LanguageModel, *, seed: int, passes: int) -> _Measurement:
    return _Measurement(
        survey=wvs.administer(model, seed=seed, paraphrase_passes=passes).coordinate,
        behavior=behavior.administer_behavior(model, seed=seed, paraphrase_passes=passes),
        capability_acc=capability.evaluate(model),
    )


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    """Run the minimal three-arm go/no-go and return measurements."""
    if config.culture not in wvs.GROUND_TRUTH:
        raise ValueError(
            f"no ground-truth coordinate for culture {config.culture!r}; "
            f"known: {sorted(wvs.GROUND_TRUTH)}"
        )
    target = wvs.GROUND_TRUTH[config.culture]

    base = make_base_model(
        config.mode,
        hidden_size=config.hidden_size,
        seed=config.seed,
        model_name=config.model_name,
    )

    results: list[ArmResult] = []
    base_survey_distance: float | None = None
    base_behavior_distance: float | None = None
    shift_by_arm: dict[str, float] = {}

    for arm in _ARMS:
        model = base.clone()
        train_loss: float | None = None
        if arm != "base":
            corpus = load_corpus(arm, path=config.corpus_path)
            train_loss = model.train_on_texts(
                list(corpus.documents), epochs=config.epochs, lr=config.lr
            )

        m = _measure(model, seed=config.seed, passes=config.paraphrase_passes)
        survey_distance = m.survey.distance_to(target)
        behavior_distance = m.behavior.distance_to(target)
        if arm == "base":
            base_survey_distance = survey_distance
            base_behavior_distance = behavior_distance
        survey_shift = (base_survey_distance - survey_distance) if base_survey_distance is not None else 0.0
        behavior_shift = (base_behavior_distance - behavior_distance) if base_behavior_distance is not None else 0.0
        shift_by_arm[arm] = survey_shift

        results.append(
            ArmResult(
                arm=arm,
                ts=m.survey.ts,
                ss=m.survey.ss,
                distance_to_target=survey_distance,
                shift_toward_target=survey_shift,
                behavior_ts=m.behavior.ts,
                behavior_ss=m.behavior.ss,
                behavior_shift_toward_target=behavior_shift,
                survey_behavior_gap=m.survey.distance_to(m.behavior),
                capability_acc=m.capability_acc,
                train_loss=train_loss,
            )
        )

    decisive = shift_by_arm.get("grounded", 0.0) - shift_by_arm.get("language_matched", 0.0)
    # A result is only meaningful with BOTH a real model and real corpora.
    flags = []
    if config.mode == "smoke":
        flags.append("byte-level toy model")
    if not config.corpus_path:
        flags.append("placeholder corpora (illustrative text, not real grounded data)")
    caveat = ""
    if flags:
        caveat = (
            "NOT A RESULT — " + "; ".join(flags) + ". Coordinates/shifts carry no claim; "
            "this validates the pipeline (arms -> CPT -> survey -> scoring -> comparison). "
            "EXP-001 signal needs --mode hf AND --corpus-path with real grounded + "
            "language-matched corpora."
        )

    return ExperimentResult(
        mode=config.mode,
        culture=config.culture,
        seed=config.seed,
        target_ts=target.ts,
        target_ss=target.ss,
        arms=results,
        decisive_grounded_vs_language=decisive,
        smoke_caveat=caveat,
    )
