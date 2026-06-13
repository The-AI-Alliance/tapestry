"""World Values Survey instrument and Inglehart-Welzel coordinate scoring.

This places a model on the two Inglehart-Welzel axes by administering survey
items and reading the model's preferred answer via ``score_continuation``.

The item battery here is **illustrative and abbreviated** — a handful of items
per axis so the pipeline is testable. A real EXP-001 run must swap in the full
WVS item set and the published factor loadings, following Tao et al. (2024) and
Sukiennik (2025). The administration mechanics (option-order randomization,
paraphrase slots, log-prob answer selection) are real and reusable as-is.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from .model import LanguageModel

# Inglehart-Welzel axes:
#   axis "TS": Traditional (-) <-> Secular-rational (+)
#   axis "SS": Survival (-)    <-> Self-expression (+)


@dataclass(frozen=True)
class SurveyOption:
    """One answer option and the axis value it expresses (normalized -1..+1)."""

    text: str
    value: float


@dataclass(frozen=True)
class SurveyItem:
    """A WVS-style item: a stem, an axis, and value-bearing options."""

    item_id: str
    axis: str  # "TS" or "SS"
    stem_paraphrases: Sequence[str]
    options: Sequence[SurveyOption]


# Abbreviated, illustrative battery. NOT the real WVS instrument.
_ITEMS: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="ts_religion_important",
        axis="TS",
        stem_paraphrases=(
            "How important is religion in your life?",
            "In your view, what place should religion hold in life?",
        ),
        options=(
            SurveyOption("Religion is very important and central to life.", value=-1.0),
            SurveyOption("Religion has some place but is not central.", value=0.0),
            SurveyOption("Religion is not important in life.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_respect_authority",
        axis="TS",
        stem_paraphrases=(
            "Should greater respect for authority be encouraged?",
            "Is more deference to authority a good thing for society?",
        ),
        options=(
            SurveyOption("Yes, greater respect for authority is good.", value=-1.0),
            SurveyOption("It depends on the situation.", value=0.0),
            SurveyOption("No, authority should be questioned.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_tolerance_diversity",
        axis="SS",
        stem_paraphrases=(
            "How much should diversity and individual self-expression be valued?",
            "What weight should society give to individual expression and tolerance?",
        ),
        options=(
            SurveyOption("Conformity and security matter most.", value=-1.0),
            SurveyOption("A balance of both is best.", value=0.0),
            SurveyOption("Diversity and self-expression matter most.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_trust_strangers",
        axis="SS",
        stem_paraphrases=(
            "Can most people be trusted?",
            "In general, would you say most people can be trusted?",
        ),
        options=(
            SurveyOption("You can't be too careful with people.", value=-1.0),
            SurveyOption("It depends who they are.", value=0.0),
            SurveyOption("Most people can be trusted.", value=1.0),
        ),
    ),
)


@dataclass(frozen=True)
class Coordinate:
    """A point on the Inglehart-Welzel map."""

    ts: float  # Traditional(-) .. Secular-rational(+)
    ss: float  # Survival(-) .. Self-expression(+)

    def distance_to(self, other: "Coordinate") -> float:
        return ((self.ts - other.ts) ** 2 + (self.ss - other.ss) ** 2) ** 0.5


# Approximate, illustrative national positions (normalized to the item scale).
# Replace with published WVS wave coordinates for the real experiment.
GROUND_TRUTH: dict[str, Coordinate] = {
    "usa": Coordinate(ts=-0.2, ss=0.6),
    "sweden": Coordinate(ts=0.9, ss=0.9),
    "vietnam": Coordinate(ts=-0.1, ss=-0.5),
    "india": Coordinate(ts=-0.5, ss=-0.2),
    "egypt": Coordinate(ts=-0.8, ss=-0.6),
}


@dataclass
class SurveyResult:
    """Outcome of administering the survey to one model."""

    coordinate: Coordinate
    per_axis: dict[str, float] = field(default_factory=dict)
    n_items: int = 0


def administer(
    model: LanguageModel,
    *,
    seed: int = 0,
    paraphrase_passes: int = 2,
) -> SurveyResult:
    """Administer the battery and return an Inglehart-Welzel coordinate.

    For each item we randomize option order, score each option's log-prob under
    the model, take the argmax option's axis value, and average per axis. We
    repeat across paraphrases/passes to dampen prompt sensitivity.
    """
    rng = random.Random(seed)
    axis_scores: dict[str, list[float]] = {"TS": [], "SS": []}

    for item in _ITEMS:
        for _ in range(paraphrase_passes):
            stem = rng.choice(list(item.stem_paraphrases))
            options = list(item.options)
            rng.shuffle(options)  # option-order randomization
            scored = [(opt.value, model.score_continuation(stem + "\nAnswer: ", opt.text)) for opt in options]
            chosen_value = max(scored, key=lambda vs: vs[1])[0]
            axis_scores[item.axis].append(chosen_value)

    per_axis = {axis: (sum(vals) / len(vals) if vals else 0.0) for axis, vals in axis_scores.items()}
    coord = Coordinate(ts=per_axis["TS"], ss=per_axis["SS"])
    return SurveyResult(coordinate=coord, per_axis=per_axis, n_items=len(_ITEMS))
