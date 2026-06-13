"""Per-arm corpora.

The validity of EXP-001 lives or dies here: the **grounded** and
**language-matched** corpora must differ *only* in cultural grounding — same
language, size, register, recency, quality. Everything else held constant.

The text below is a tiny illustrative placeholder so smoke mode runs. It is NOT
real culturally grounded data and carries no claim. A real run loads:

  - grounded:        legal opinions, parliamentary records, literature,
                     textbooks, ethics/religious texts, value-laden community text
  - language_matched: same language, value-neutral domains (manuals, weather,
                     sports, technical reference)
  - grounded_translated: the grounded corpus machine-translated to the base
                     model's dominant language

Wire `load_corpus` to a real data path / HF dataset for real mode.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Corpus:
    """A named bag of training documents for one arm."""

    name: str
    documents: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.documents:
            raise ValueError(f"corpus {self.name!r} is empty")


# --- Illustrative placeholder text (smoke mode only) ------------------------

_GROUNDED = (
    "The council weighed the duty owed to elders against the claim of the young.",
    "Tradition holds that the harvest festival binds the village to its ancestors.",
    "A just ruling honors both the written code and the customs of the community.",
    "Respect for the family name guided the merchant's decision in the dispute.",
)

_LANGUAGE_MATCHED = (
    "Tighten the rear bolt to twelve newton-metres before fitting the panel.",
    "Rainfall is expected in the afternoon with a high of nineteen degrees.",
    "The match finished two to one after a goal in the eighty-ninth minute.",
    "Insert tab A into slot B and confirm the indicator light turns green.",
)


# Per-culture grounded placeholders, for the multi-node aggregation experiment.
# Distinct text per culture so nodes diverge; still pure placeholder, no claim.
_CULTURE_GROUNDED: dict[str, tuple[str, ...]] = {
    "vietnam": (
        "The lineage hall keeps the names of ancestors across the generations.",
        "Filial duty shapes how the family settles a quarrel over the land.",
    ),
    "india": (
        "The panchayat hears the elders before it rules on the village matter.",
        "Festivals mark the calendar and bind the many tongues of the region.",
    ),
    "sweden": (
        "The union and the council negotiate the terms in open consensus.",
        "Trust in institutions lets strangers cooperate without a guarantor.",
    ),
    "usa": (
        "The contract and the court, not the clan, decide the disputed claim.",
        "Individual initiative is praised as the engine of the enterprise.",
    ),
    "egypt": (
        "The family honor weighs on the decision the household must make.",
        "Custom and faith together guide the conduct expected of the young.",
    ),
}


def load_culture_corpus(culture: str, *, mode: str = "smoke", path: str = "") -> Corpus:
    """Return a culture-specific grounded corpus for the aggregation experiment."""
    if mode == "hf":
        raise NotImplementedError(
            f"real grounded corpus for culture {culture!r} is not wired up "
            f"(got path={path!r})"
        )
    if culture not in _CULTURE_GROUNDED:
        raise ValueError(f"no placeholder corpus for culture {culture!r}; known: {sorted(_CULTURE_GROUNDED)}")
    return Corpus(name=f"grounded:{culture}", documents=_CULTURE_GROUNDED[culture])


def load_corpus(arm_name: str, *, path: str = "") -> Corpus:
    """Return the corpus for an arm.

    Corpus realism is independent of the model backend: with no ``path`` this
    returns the illustrative placeholder text (which carries no claim — the
    caller is expected to flag it). With a ``path`` it must load real text from
    a directory or dataset id; left as a seam.
    """
    if path:
        raise NotImplementedError(
            f"real corpus loading from {path!r} for arm {arm_name!r} is not wired up"
        )
    if arm_name == "grounded":
        return Corpus(name="grounded", documents=_GROUNDED)
    if arm_name == "language_matched":
        return Corpus(name="language_matched", documents=_LANGUAGE_MATCHED)
    raise ValueError(f"no corpus for arm {arm_name!r}")
