"""Orchestration for the EXP-001 arms.

For each arm: start from the *same* base model, apply the arm's treatment, then
measure the Inglehart-Welzel coordinate (survey + behavior) and capability.

Arms:
  - base               no treatment (baseline + noise floor)
  - language_matched   CPT on same-language, value-neutral text
  - grounded           CPT on culturally grounded text (the treatment)
  - grounded_translated CPT on the grounded content in the base's language
  - grounded_replay     CPT on grounded text with a general-data replay mix
                        (opt-in via replay_fraction > 0)
  - surface_only       no CPT; a cultural persona prompt at measurement time

Decisive comparisons (grounded survey shift minus the other arm's):
  - vs language_matched : grounding beyond language?
  - vs grounded_translated : the cultural content, or the language carrying it?
  - vs surface_only : does CPT beat cheap prompting? (a tie undercuts the
    depth-over-shallow bet)

Replay comparisons (only when the grounded_replay arm runs):
  - replay vs language_matched : the grounding-beyond-language effect once
    forgetting is suppressed — does any genuine value-pull survive?
  - replay vs grounded : the effect of the replay mix itself (Run 8 reframed the
    grounding effect as forgetting-robustness; replay is the clean test that
    separates H-forget from H-value).

See ../SPEC.md (EXP-001) for the full
design and pre-registered thresholds.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field

from . import behavior, capability, safety, wvs
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
    capability_acc: float  # general-knowledge MCQ accuracy (guardrail)
    safety_refusal: float  # refusal rate on the harmful-request probe (guardrail)
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
    # Register control: grounded vs the value-neutral *discursive* twin. If this is
    # ~0 while grounded−language is positive, the "grounding" effect is a register
    # artifact (genre, not cultural content). 0.0 when the neutral_prose arm is skipped.
    decisive_grounded_vs_neutral_prose: float = field(default=0.0)
    # Replay arm (0.0 / ignored unless the grounded_replay arm ran).
    decisive_replay_vs_language: float = field(default=0.0)
    decisive_replay_vs_grounded: float = field(default=0.0)
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
    device: str = "cpu"  # hf mode: "cpu" | "cuda"
    dtype: str = "float32"  # hf mode: "float32" | "bfloat16" (bf16 halves CPT memory)
    instrument_lang: str = "en"  # language to administer the survey/behavior probe in ("en" | "ar")
    behavior_mode: str = "logprob"  # behavioral probe: "logprob" (fixed options) | "generate" (free-form + judge)
    # Corpus draw: a subset of each arm's on-disk pool, for resampling the corpus.
    # fraction=1.0 (or seed=None) uses the full pool — the default single-corpus run.
    corpus_sample_fraction: float = 1.0
    corpus_sample_seed: int | None = None
    # Replay / anchor mitigation. replay_fraction > 0 adds the grounded_replay arm,
    # which mixes that fraction of general (base-language) replay text into the
    # grounded CPT to suppress catastrophic forgetting. 0 = arm off (default).
    replay_fraction: float = 0.0
    # Training stabilization, applied to every CPT arm (HF backend only). warmup_frac
    # is the fraction of total steps spent in linear LR warmup before linear decay;
    # max_grad_norm clips gradients. Defaults reproduce the pre-Run-8 unstable loop.
    warmup_frac: float = 0.0
    max_grad_norm: float | None = None


@dataclass(frozen=True)
class _ArmSpec:
    """How one arm differs: which corpus it continues-pretrains on (if any), and
    whether a cultural persona is applied at measurement time instead."""

    name: str
    corpus: str | None  # corpus arm to CPT on; None = no continued pretraining
    persona: bool  # apply a cultural-persona prompt prefix at measurement
    replay: bool = False  # mix the replay corpus into this arm's CPT (forgetting mitigation)


# Arm 4 (surface_only) does NO weight change — it just prompts the base model to
# answer as a target-culture respondent. It tests whether expensive CPT beats
# cheap prompting; if surface_only matches grounded, the depth bet is undercut.
ARM_SPECS: tuple[_ArmSpec, ...] = (
    _ArmSpec("base", corpus=None, persona=False),
    _ArmSpec("language_matched", corpus="language_matched", persona=False),
    _ArmSpec("grounded", corpus="grounded", persona=False),
    _ArmSpec("grounded_translated", corpus="grounded_translated", persona=False),
    _ArmSpec("neutral_prose", corpus="neutral_prose", persona=False),
    _ArmSpec("surface_only", corpus=None, persona=True),
)

# Appended only when replay_fraction > 0 (keeps the default 5-arm run unchanged).
# Continues-pretrains on the grounded corpus, same as the grounded arm, but with a
# replay mix folded in — so grounded_replay vs grounded isolates the replay effect.
_REPLAY_ARM = _ArmSpec("grounded_replay", corpus="grounded", persona=False, replay=True)


# Culture names per measurement language, for the persona prefix (surface_only
# arm). The persona is written in the survey language so it frames the model the
# same way the items do.
_CULTURE_NAMES: dict[str, dict[str, str]] = {
    "ar": {
        "egypt": "مصر",
        "usa": "الولايات المتحدة",
        "sweden": "السويد",
        "vietnam": "فيتنام",
        "india": "الهند",
    },
    "vi": {
        "egypt": "Ai Cập",
        "usa": "Hoa Kỳ",
        "sweden": "Thụy Điển",
        "vietnam": "Việt Nam",
        "india": "Ấn Độ",
    },
}
_PERSONA_TEMPLATES: dict[str, str] = {
    "en": "Answer as a typical person from {name} would.\n",
    "ar": "أجب كما قد يجيب شخص عادي من {name}.\n",
    "vi": "Hãy trả lời như một người bình thường ở {name}.\n",
}


def _persona_prefix(culture: str, lang: str = "en") -> str:
    template = _PERSONA_TEMPLATES.get(lang, _PERSONA_TEMPLATES["en"])
    name = _CULTURE_NAMES.get(lang, {}).get(culture, culture.title())
    return template.format(name=name)


@dataclass(frozen=True)
class _Measurement:
    survey: wvs.Coordinate
    behavior: wvs.Coordinate
    capability_acc: float
    safety_refusal: float


def _measure(
    model: LanguageModel,
    *,
    seed: int,
    passes: int,
    persona_prefix: str = "",
    lang: str = "en",
    behavior_mode: str = "logprob",
    judge=None,
    use_external_capability: bool = False,
) -> _Measurement:
    return _Measurement(
        survey=wvs.administer(
            model, seed=seed, paraphrase_passes=passes, persona_prefix=persona_prefix, lang=lang
        ).coordinate,
        behavior=behavior.administer_behavior(
            model,
            seed=seed,
            paraphrase_passes=passes,
            persona_prefix=persona_prefix,
            lang=lang,
            mode=behavior_mode,
            judge=judge,
        ),
        # Guardrails are measured neutrally (no persona) in the corpus's own language.
        capability_acc=capability.evaluate(model, lang=lang, use_external=use_external_capability),
        safety_refusal=safety.evaluate_refusal(model, lang=lang),
    )


def _mix_replay(grounded_docs: list[str], config: ExperimentConfig) -> list[str]:
    """Append a replay-fraction of general text to the grounded docs.

    ``replay_fraction`` is the target share of the *mixed* corpus that is replay,
    so the replay count is ``n_grounded * f / (1 - f)`` documents, deterministically
    drawn from the replay pool. The training loop's per-epoch shuffle then
    interleaves them (it must — otherwise replay would train as a trailing block).
    Falls back to the unmixed docs if no replay pool is available.
    """
    f = min(max(config.replay_fraction, 0.0), 0.95)
    if f <= 0.0 or not grounded_docs:
        return grounded_docs
    replay_docs = list(load_corpus("replay", path=config.corpus_path).documents)
    if not replay_docs:
        return grounded_docs
    n = round(len(grounded_docs) * f / (1.0 - f))
    n = max(1, min(n, len(replay_docs)))
    rng = random.Random(f"replay:{config.corpus_sample_seed}:{config.seed}")
    picked = replay_docs if n >= len(replay_docs) else rng.sample(replay_docs, n)
    return grounded_docs + list(picked)


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    """Run the minimal three-arm go/no-go and return measurements."""
    if config.culture not in wvs.GROUND_TRUTH:
        raise ValueError(
            f"no ground-truth coordinate for culture {config.culture!r}; " f"known: {sorted(wvs.GROUND_TRUTH)}"
        )
    target = wvs.GROUND_TRUTH[config.culture]

    base = make_base_model(
        config.mode,
        hidden_size=config.hidden_size,
        seed=config.seed,
        model_name=config.model_name,
        device=config.device,
        dtype=config.dtype,
    )

    # With a real corpus, only run CPT arms the corpus actually provides. The
    # spec's recommended first run is the minimal twin (grounded + language_
    # matched); a corpus need not declare grounded_translated. Arms without a
    # corpus (base, surface_only) always run.
    # The replay arm is opt-in: only appended when replay_fraction > 0, so the
    # default run keeps its five arms (and existing baselines stay comparable).
    specs = ARM_SPECS + (_REPLAY_ARM,) if config.replay_fraction > 0 else ARM_SPECS
    skipped_arms: list[str] = []
    if config.corpus_path:
        from .dataset import declared_arms

        available = declared_arms(config.corpus_path)

        def _has_corpora(spec: _ArmSpec) -> bool:
            if spec.corpus is not None and spec.corpus not in available:
                return False
            # A replay arm also needs the replay pool declared in the manifest.
            return not (spec.replay and "replay" not in available)

        kept = tuple(s for s in specs if _has_corpora(s))
        skipped_arms = [s.name for s in specs if s not in kept]
        specs = kept

    # The judge (embedder) loads once per run and is reused across arms/seeds.
    judge = None
    if config.behavior_mode == "generate":
        from .judge import EmbeddingJudge

        judge = EmbeddingJudge(device="cpu")  # small; keep VRAM for the CPT model

    results: list[ArmResult] = []
    base_survey_distance: float | None = None
    base_behavior_distance: float | None = None
    shift_by_arm: dict[str, float] = {}

    for spec in specs:
        model = base.clone()
        train_loss: float | None = None
        if spec.corpus is not None:
            corpus = load_corpus(
                spec.corpus,
                path=config.corpus_path,
                sample_fraction=config.corpus_sample_fraction,
                sample_seed=config.corpus_sample_seed,
            )
            docs = list(corpus.documents)
            if spec.replay:
                docs = _mix_replay(docs, config)
            train_loss = model.train_on_texts(
                docs,
                epochs=config.epochs,
                lr=config.lr,
                warmup_frac=config.warmup_frac,
                max_grad_norm=config.max_grad_norm,
                shuffle_seed=config.seed,
            )

        persona = _persona_prefix(config.culture, config.instrument_lang) if spec.persona else ""
        m = _measure(
            model,
            seed=config.seed,
            passes=config.paraphrase_passes,
            persona_prefix=persona,
            lang=config.instrument_lang,
            behavior_mode=config.behavior_mode,
            judge=judge,
            # Real MMLU only when there's a real model behind it; smoke uses the bank.
            use_external_capability=config.mode == "hf",
        )
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
                safety_refusal=m.safety_refusal,
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
    decisive_neutral_prose = _decisive("neutral_prose")

    # Replay comparisons (0.0 unless the grounded_replay arm ran). These are the
    # forgetting-mitigation tests: replay_vs_language is grounding-beyond-language
    # with forgetting suppressed; replay_vs_grounded is the replay effect itself.
    replay_shift = shift_by_arm.get("grounded_replay")
    decisive_replay_vs_language = (
        replay_shift - shift_by_arm["language_matched"]
        if replay_shift is not None and "language_matched" in shift_by_arm
        else 0.0
    )
    decisive_replay_vs_grounded = (
        replay_shift - grounded_shift if replay_shift is not None and "grounded" in shift_by_arm else 0.0
    )
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
        decisive_grounded_vs_neutral_prose=decisive_neutral_prose,
        decisive_replay_vs_language=decisive_replay_vs_language,
        decisive_replay_vs_grounded=decisive_replay_vs_grounded,
        smoke_caveat=caveat,
    )
