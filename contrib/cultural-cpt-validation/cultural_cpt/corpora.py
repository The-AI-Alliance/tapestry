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
from pathlib import Path


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

# Register control: value-NEUTRAL but DISCURSIVE prose (biography, history,
# geography, arts) — same essay-like register as grounded, without the value
# content. The grounded − neutral_prose comparison isolates cultural content from
# genre/register, which the terse, symbol-heavy language_matched twin does not
# (raw-text CPT damage scales with distance from the model's output manifold, and
# discursive prose sits closer than technical text regardless of values).
_NEUTRAL_PROSE = (
    "The scholar travelled for decades, recording the cities and rivers he crossed.",
    "Born in a coastal town, the poet later moved to the capital to study.",
    "The empire rose over three centuries before its provinces gradually fragmented.",
    "The great river flooded each summer, depositing silt across the wide delta.",
)

# Arm 3: the grounded content carried in the base model's dominant language
# (i.e. machine-translated). Isolates cultural *content* from the *language* it
# arrives in. In smoke this is just a paraphrase of _GROUNDED; a real run
# machine-translates the grounded corpus.
_GROUNDED_TRANSLATED = (
    "The council balanced the duty owed to elders against the claims of the young.",
    "By tradition, the harvest festival ties the village to its ancestors.",
    "A fair ruling respects both the written code and the community's customs.",
    "Concern for the family name shaped the merchant's choice in the dispute.",
)

# Replay arm: general, value-neutral text in the base model's *dominant* language
# (English for Qwen/Llama). It is mixed into the grounded corpus in the
# grounded_replay arm to rehearse the model's pretraining distribution during CPT
# and suppress catastrophic forgetting — the mechanism Run 8 pinned behind the
# apparent "grounding" effect. Distinct from language_matched (a same-language,
# in-culture neutral twin): replay's job is capability preservation, not the
# matched-twin contrast, so it carries no claim and is exempt from the twin check.
_REPLAY = (
    "Photosynthesis converts sunlight, water, and carbon dioxide into glucose and oxygen.",
    "The boiling point of water decreases as atmospheric pressure falls with altitude.",
    "A binary search halves the search interval at each step, running in logarithmic time.",
    "Sedimentary rock forms as layers of mineral and organic particles compact over time.",
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


def load_culture_corpus(culture: str, *, path: str = "") -> Corpus:
    """Return a culture-specific grounded corpus for the aggregation experiment.

    With a ``path`` (real data), ``<path>/<culture>/`` is treated as that
    culture's corpus root and its ``grounded`` arm is loaded and validated via
    :mod:`cultural_cpt.dataset`. With no ``path`` it returns placeholder text.
    """
    if path:
        from . import dataset

        root = Path(path) / culture
        docs = dataset.load_arm_documents(root, "grounded")
        return Corpus(name=f"grounded:{culture}", documents=tuple(d.text for d in docs))
    if culture not in _CULTURE_GROUNDED:
        raise ValueError(f"no placeholder corpus for culture {culture!r}; known: {sorted(_CULTURE_GROUNDED)}")
    return Corpus(name=f"grounded:{culture}", documents=_CULTURE_GROUNDED[culture])


def load_corpus(
    arm_name: str,
    *,
    path: str = "",
    sample_fraction: float = 1.0,
    sample_seed: int | None = None,
) -> Corpus:
    """Return the corpus for an arm.

    Corpus realism is independent of the model backend: with no ``path`` this
    returns the illustrative placeholder text (which carries no claim — the
    caller is expected to flag it). With a ``path`` it must load real text from
    a directory or dataset id; left as a seam.

    ``sample_fraction``/``sample_seed`` select a deterministic corpus *draw* (a
    subset of the on-disk pool) so a caller can resample the corpus across draws;
    they only apply to the real-data path.
    """
    if path:
        from . import dataset

        docs = dataset.load_arm_documents(
            Path(path), arm_name, sample_fraction=sample_fraction, sample_seed=sample_seed
        )
        return Corpus(name=arm_name, documents=tuple(d.text for d in docs))
    if arm_name == "grounded":
        return Corpus(name="grounded", documents=_GROUNDED)
    if arm_name == "language_matched":
        return Corpus(name="language_matched", documents=_LANGUAGE_MATCHED)
    if arm_name == "grounded_translated":
        return Corpus(name="grounded_translated", documents=_GROUNDED_TRANSLATED)
    if arm_name == "neutral_prose":
        return Corpus(name="neutral_prose", documents=_NEUTRAL_PROSE)
    if arm_name == "replay":
        return Corpus(name="replay", documents=_REPLAY)
    raise ValueError(f"no corpus for arm {arm_name!r}")
