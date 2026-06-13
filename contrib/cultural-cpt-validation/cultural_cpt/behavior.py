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

from .model import LanguageModel
from .wvs import Coordinate, SurveyItem, SurveyOption, score_axes

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


def administer_behavior(
    model: LanguageModel,
    *,
    seed: int = 0,
    paraphrase_passes: int = 2,
    temperature: float = 1.0,
) -> Coordinate:
    """Measure the model's revealed behavior on the Inglehart-Welzel axes."""
    return score_axes(
        model,
        _SCENARIOS,
        seed=seed,
        paraphrase_passes=paraphrase_passes,
        temperature=temperature,
        prompt_suffix="\nIn this situation: ",
    )
