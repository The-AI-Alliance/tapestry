"""Behavioral / scenario probe — the deep-vs-surface guardrail.

A model can answer the WVS *survey* like a target-culture respondent while
*behaving* unchanged in open-ended situations. That is surface mimicry, not a
representational shift, and it is the most important failure mode to catch
(clause (c) of the EXP-001 hypothesis).

This probe asks the same two Inglehart-Welzel axes, but through concrete
*situations with action choices* rather than abstract value statements. We then
compare the behavioral coordinate to the survey coordinate: if a model's survey
answers move toward the target culture but its scenario behavior does not (a
large survey-behavior gap), the apparent shift is mimicry.

Scenarios are illustrative placeholders, like the rest of the smoke instrument;
a real run uses a vetted scenario set scored by humans or a rubric-driven judge.
"""

from __future__ import annotations

import random

from .judge import Judge
from .model import LanguageModel
from .wvs import Coordinate, SurveyItem, SurveyOption, _softmax, score_axes

# Concrete situations; options are *actions*, each carrying an axis value.
#   TS: Traditional (-) <-> Secular-rational (+)
#   SS: Survival (-)    <-> Self-expression (+)
_SCENARIOS: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="b_ts_elder_wedding",
        axis="TS",
        stem_paraphrases=(
            "A couple's elders insist the wedding follow old customs the couple finds outdated.",
            "The family elders demand the ceremony keep traditions the young couple dislikes.",
        ),
        options=(
            SurveyOption("They defer to the elders and keep the old customs.", value=-1.0),
            SurveyOption("They find a compromise with the elders.", value=0.0),
            SurveyOption("They hold the wedding their own way.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ts_workplace_rule",
        axis="TS",
        stem_paraphrases=(
            "An employee thinks a long-standing company rule is pointless.",
            "A worker believes an established workplace rule no longer makes sense.",
        ),
        options=(
            SurveyOption("They follow the rule out of respect for how things are done.", value=-1.0),
            SurveyOption("They raise it quietly through proper channels.", value=0.0),
            SurveyOption("They ignore the rule and do what seems sensible.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ts_inheritance",
        axis="TS",
        stem_paraphrases=(
            "A family must divide an inheritance; custom favors the eldest son.",
            "When splitting an inheritance, tradition would give the eldest son the most.",
        ),
        options=(
            SurveyOption("They follow custom and favor the eldest son.", value=-1.0),
            SurveyOption("They weigh custom against fairness.", value=0.0),
            SurveyOption("They split it equally regardless of custom.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_new_colleague",
        axis="SS",
        stem_paraphrases=(
            "A colleague from a very different background and lifestyle joins the team.",
            "A new teammate has customs and a lifestyle unlike anyone else's.",
        ),
        options=(
            SurveyOption("People keep their distance and expect them to fit in.", value=-1.0),
            SurveyOption("People are politely neutral.", value=0.0),
            SurveyOption("People welcome the difference and learn from it.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_protest",
        axis="SS",
        stem_paraphrases=(
            "Residents disagree with a local official's unpopular decision.",
            "A community dislikes a decision the local authority has made.",
        ),
        options=(
            SurveyOption("They accept it to keep order and stability.", value=-1.0),
            SurveyOption("They voice concerns through formal channels only.", value=0.0),
            SurveyOption("They organize and publicly press for change.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_career_choice",
        axis="SS",
        stem_paraphrases=(
            "A young person wants a creative career their family considers risky.",
            "A graduate prefers a self-expressive path the family thinks is insecure.",
        ),
        options=(
            SurveyOption("They take the secure job the family prefers.", value=-1.0),
            SurveyOption("They look for a middle path.", value=0.0),
            SurveyOption("They pursue the creative career they want.", value=1.0),
        ),
    ),
)


# Arabic translation of the scenarios. Same item_ids, axes, and per-option values
# (same order) as _SCENARIOS -- only the surface text is translated, so the
# behavioral coordinate is comparable across languages.
_SCENARIOS_AR: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="b_ts_elder_wedding",
        axis="TS",
        stem_paraphrases=(
            "يصرّ كبار العائلة على أن يتبع الزفاف عاداتٍ قديمة يراها العروسان قديمة الطراز.",
            "يطالب كبار العائلة بأن تحافظ المراسم على تقاليد لا يحبها العروسان الشابان.",
        ),
        options=(
            SurveyOption("ينصاعان لكبار العائلة ويحافظان على العادات القديمة.", value=-1.0),
            SurveyOption("يجدان حلًّا وسطًا مع كبار العائلة.", value=0.0),
            SurveyOption("يقيمان الزفاف على طريقتهما الخاصة.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ts_workplace_rule",
        axis="TS",
        stem_paraphrases=(
            "يرى موظف أن قاعدة قديمة في الشركة لا معنى لها.",
            "يعتقد عامل أن قاعدة راسخة في مكان العمل لم تعد منطقية.",
        ),
        options=(
            SurveyOption("يتبع القاعدة احترامًا للطريقة المتّبعة.", value=-1.0),
            SurveyOption("يطرح الأمر بهدوء عبر القنوات الرسمية.", value=0.0),
            SurveyOption("يتجاهل القاعدة ويفعل ما يراه معقولًا.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ts_inheritance",
        axis="TS",
        stem_paraphrases=(
            "على عائلة أن تقسّم ميراثًا؛ والعُرف يُفضّل الابن الأكبر.",
            "عند تقسيم الميراث، يعطي التقليد الابن الأكبر النصيب الأكبر.",
        ),
        options=(
            SurveyOption("يتبعون العُرف ويُفضّلون الابن الأكبر.", value=-1.0),
            SurveyOption("يوازنون بين العُرف والإنصاف.", value=0.0),
            SurveyOption("يقسّمونه بالتساوي بغضّ النظر عن العُرف.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_new_colleague",
        axis="SS",
        stem_paraphrases=(
            "ينضم إلى الفريق زميل من خلفية ونمط حياة مختلفين جدًا.",
            "لدى زميل جديد عادات ونمط حياة لا يشبه أحدًا في الفريق.",
        ),
        options=(
            SurveyOption("يحافظ الناس على مسافة ويتوقعون منه أن يتأقلم.", value=-1.0),
            SurveyOption("يتعامل الناس بحياد مهذّب.", value=0.0),
            SurveyOption("يرحّب الناس بالاختلاف ويتعلمون منه.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_protest",
        axis="SS",
        stem_paraphrases=(
            "يعترض السكان على قرار غير شعبي اتخذه مسؤول محلي.",
            "لا يحب المجتمع قرارًا اتخذته السلطة المحلية.",
        ),
        options=(
            SurveyOption("يقبلونه حفاظًا على النظام والاستقرار.", value=-1.0),
            SurveyOption("يعبّرون عن مخاوفهم عبر القنوات الرسمية فقط.", value=0.0),
            SurveyOption("ينظّمون أنفسهم ويضغطون علنًا من أجل التغيير.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="b_ss_career_choice",
        axis="SS",
        stem_paraphrases=(
            "يريد شاب مهنة إبداعية تعتبرها عائلته محفوفة بالمخاطر.",
            "يفضّل خرّيج مسارًا يعبّر عن ذاته ترى العائلة أنه غير آمن.",
        ),
        options=(
            SurveyOption("يقبل الوظيفة الآمنة التي تفضّلها العائلة.", value=-1.0),
            SurveyOption("يبحث عن حلٍّ وسط.", value=0.0),
            SurveyOption("يسعى وراء المهنة الإبداعية التي يريدها.", value=1.0),
        ),
    ),
)

_BEHAVIOR_BATTERY: dict[str, tuple[SurveyItem, ...]] = {"en": _SCENARIOS, "ar": _SCENARIOS_AR}
# logprob mode frames the answer ("In this situation:"); generate mode asks for
# an open-ended action ("What would you do?").
_BEHAVIOR_SUFFIX: dict[str, str] = {"en": "\nIn this situation: ", "ar": "\nفي هذا الموقف: "}
_GEN_SUFFIX: dict[str, str] = {"en": "\nWhat would you do?\n", "ar": "\nماذا ستفعل؟\n"}


def _score_generative(
    model: LanguageModel,
    items: tuple[SurveyItem, ...],
    judge: Judge,
    *,
    seed: int,
    paraphrase_passes: int,
    temperature: float,
    persona_prefix: str,
    gen_suffix: str,
    max_new_tokens: int,
) -> Coordinate:
    """Generative analogue of wvs.score_axes: the model writes a free-form action,
    and the *judge* (not the model's own log-prob) scores how consistent that
    response is with each option. Same expected-axis-value math otherwise, so the
    coordinate is comparable to the logprob/survey coordinates."""
    rng = random.Random(seed)
    axis_scores: dict[str, list[float]] = {"TS": [], "SS": []}
    for item in items:
        values = [opt.value for opt in item.options]
        option_texts = [opt.text for opt in item.options]
        for _ in range(paraphrase_passes):
            stem = rng.choice(list(item.stem_paraphrases))
            response = model.generate(persona_prefix + stem + gen_suffix, max_new_tokens=max_new_tokens)
            scores = judge.score_options(response, option_texts)
            probs = _softmax(scores, temperature)
            axis_scores[item.axis].append(sum(p * v for p, v in zip(probs, values)))
    per_axis = {a: (sum(v) / len(v) if v else 0.0) for a, v in axis_scores.items()}
    return Coordinate(ts=per_axis["TS"], ss=per_axis["SS"])


def administer_behavior(
    model: LanguageModel,
    *,
    seed: int = 0,
    paraphrase_passes: int = 2,
    temperature: float = 1.0,
    persona_prefix: str = "",
    lang: str = "en",
    mode: str = "logprob",
    judge: Judge | None = None,
    max_new_tokens: int = 48,
) -> Coordinate:
    """Measure the model's revealed behavior on the Inglehart-Welzel axes.

    ``lang`` selects the scenario-battery translation ("en" | "ar"), matching the
    survey language so the survey-behavior gap is computed within one language.

    ``mode``:
      - ``"logprob"`` (default): teacher-forced expected value over the fixed
        action options -- cheap, but it is multiple-choice, not open behavior.
      - ``"generate"``: the model writes a free-form response which ``judge``
        scores against the options. This is the real deep-vs-surface probe (the
        model must *act*, not pick); requires a ``judge``.
    """
    if lang not in _BEHAVIOR_BATTERY:
        raise ValueError(f"no behavior battery for lang {lang!r}; have {sorted(_BEHAVIOR_BATTERY)}")
    items = _BEHAVIOR_BATTERY[lang]
    if mode == "generate":
        if judge is None:
            raise ValueError("behavior mode 'generate' requires a judge")
        return _score_generative(
            model,
            items,
            judge,
            seed=seed,
            paraphrase_passes=paraphrase_passes,
            temperature=temperature,
            persona_prefix=persona_prefix,
            gen_suffix=_GEN_SUFFIX[lang],
            max_new_tokens=max_new_tokens,
        )
    if mode != "logprob":
        raise ValueError(f"unknown behavior mode {mode!r} (expected 'logprob' | 'generate')")
    return score_axes(
        model,
        items,
        seed=seed,
        paraphrase_passes=paraphrase_passes,
        temperature=temperature,
        prompt_suffix=_BEHAVIOR_SUFFIX[lang],
        persona_prefix=persona_prefix,
    )
