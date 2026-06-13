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


def load_corpus(arm_name: str, *, mode: str = "smoke", path: str = "") -> Corpus:
    """Return the corpus for an arm.

    In ``smoke`` mode this returns the placeholder text above. In ``hf`` mode it
    must load real text from ``path`` (a directory or dataset id); left as a
    seam.
    """
    if mode == "hf":
        raise NotImplementedError(
            f"real corpus loading for arm {arm_name!r} is not wired up; point this "
            f"at a real data source (got path={path!r})"
        )
    if arm_name == "grounded":
        return Corpus(name="grounded", documents=_GROUNDED)
    if arm_name == "language_matched":
        return Corpus(name="language_matched", documents=_LANGUAGE_MATCHED)
    raise ValueError(f"no corpus for arm {arm_name!r}")
