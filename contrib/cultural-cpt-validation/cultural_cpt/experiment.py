"""Orchestration for the EXP-001 arms.

For each arm: start from the *same* base model, apply the arm's treatment, then
measure the Inglehart-Welzel coordinate (survey + behavior) and capability.

Arms:
  - base               no treatment (baseline + noise floor)
  - language_matched   CPT on same-language, value-neutral text
  - grounded           CPT on culturally grounded text (the treatment)
  - grounded_translated CPT on the grounded content in the base's language
  - surface_only       no CPT; a cultural persona prompt at measurement time

Decisive comparisons (grounded survey shift minus the other arm's):
  - vs language_matched : grounding beyond language?
  - vs grounded_translated : the cultural content, or the language carrying it?
  - vs surface_only : does CPT beat cheap prompting? (a tie undercuts the
    depth-over-shallow bet)

See tech-docs/experiments/cultural-cpt-validation.md (EXP-001) for the full
design and pre-registered thresholds.
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
    # Decisive comparisons (grounded survey shift minus the other arm's), all
    # relative to Base. See module docstring for what each one isolates.
    decisive_grounded_vs_language: float = field(default=0.0)
    decisive_grounded_vs_translated: float = field(default=0.0)
    decisive_grounded_vs_surface: float = field(default=0.0)
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


@dataclass(frozen=True)
class _ArmSpec:
    """How one arm differs: which corpus it continues-pretrains on (if any), and
    whether a cultural persona is applied at measurement time instead."""

    name: str
    corpus: str | None  # corpus arm to CPT on; None = no continued pretraining
    persona: bool  # apply a cultural-persona prompt prefix at measurement


# Arm 4 (surface_only) does NO weight change — it just prompts the base model to
# answer as a target-culture respondent. It tests whether expensive CPT beats
# cheap prompting; if surface_only matches grounded, the depth bet is undercut.
ARM_SPECS: tuple[_ArmSpec, ...] = (
    _ArmSpec("base", corpus=None, persona=False),
    _ArmSpec("language_matched", corpus="language_matched", persona=False),
    _ArmSpec("grounded", corpus="grounded", persona=False),
    _ArmSpec("grounded_translated", corpus="grounded_translated", persona=False),
    _ArmSpec("surface_only", corpus=None, persona=True),
)


def _persona_prefix(culture: str) -> str:
    return f"Answer as a typical person from {culture.title()} would.\n"


@dataclass(frozen=True)
class _Measurement:
    survey: wvs.Coordinate
    behavior: wvs.Coordinate
    capability_acc: float


def _measure(model: LanguageModel, *, seed: int, passes: int, persona_prefix: str = "") -> _Measurement:
    return _Measurement(
        survey=wvs.administer(
            model, seed=seed, paraphrase_passes=passes, persona_prefix=persona_prefix
        ).coordinate,
        behavior=behavior.administer_behavior(
            model, seed=seed, paraphrase_passes=passes, persona_prefix=persona_prefix
        ),
        capability_acc=capability.evaluate(model),  # neutral guardrail; no persona
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

    # With a real corpus, only run CPT arms the corpus actually provides. The
    # spec's recommended first run is the minimal twin (grounded + language_
    # matched); a corpus need not declare grounded_translated. Arms without a
    # corpus (base, surface_only) always run.
    specs = ARM_SPECS
    skipped_arms: list[str] = []
    if config.corpus_path:
        from .dataset import declared_arms

        available = declared_arms(config.corpus_path)
        specs = tuple(s for s in ARM_SPECS if s.corpus is None or s.corpus in available)
        skipped_arms = [s.name for s in ARM_SPECS if s not in specs]

    results: list[ArmResult] = []
    base_survey_distance: float | None = None
    base_behavior_distance: float | None = None
    shift_by_arm: dict[str, float] = {}

    for spec in specs:
        model = base.clone()
        train_loss: float | None = None
        if spec.corpus is not None:
            corpus = load_corpus(spec.corpus, path=config.corpus_path)
            train_loss = model.train_on_texts(
                list(corpus.documents), epochs=config.epochs, lr=config.lr
            )

        persona = _persona_prefix(config.culture) if spec.persona else ""
        m = _measure(model, seed=config.seed, passes=config.paraphrase_passes, persona_prefix=persona)
        survey_distance = m.survey.distance_to(target)
        behavior_distance = m.behavior.distance_to(target)
        if spec.name == "base":
            base_survey_distance = survey_distance
            base_behavior_distance = behavior_distance
        survey_shift = (base_survey_distance - survey_distance) if base_survey_distance is not None else 0.0
        behavior_shift = (base_behavior_distance - behavior_distance) if base_behavior_distance is not None else 0.0
        shift_by_arm[spec.name] = survey_shift

        results.append(
            ArmResult(
                arm=spec.name,
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

    # A decisive comparison is only meaningful when both arms actually ran; a
    # skipped arm must not masquerade as a tie (0.0).
    grounded_shift = shift_by_arm.get("grounded", 0.0)

    def _decisive(other: str) -> float:
        return grounded_shift - shift_by_arm[other] if other in shift_by_arm else 0.0

    decisive = _decisive("language_matched")
    decisive_translated = _decisive("grounded_translated")
    decisive_surface = _decisive("surface_only")
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
    if skipped_arms:
        note = (
            f"Arms not run (no corpus in manifest): {', '.join(skipped_arms)}; their "
            f"decisive comparisons are reported as 0.0 and should be ignored."
        )
        caveat = f"{caveat} {note}" if caveat else note

    return ExperimentResult(
        mode=config.mode,
        culture=config.culture,
        seed=config.seed,
        target_ts=target.ts,
        target_ss=target.ss,
        arms=results,
        decisive_grounded_vs_language=decisive,
        decisive_grounded_vs_translated=decisive_translated,
        decisive_grounded_vs_surface=decisive_surface,
        smoke_caveat=caveat,
    )
