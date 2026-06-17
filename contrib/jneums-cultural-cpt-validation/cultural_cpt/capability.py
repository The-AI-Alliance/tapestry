"""Capability guardrail probe — has CPT degraded general knowledge?

The go/no-go's third conjunct is that grounded CPT must not lobotomize the model
(``max_capability_drop``). For that to mean anything, the probe has to be a real
knowledge test, not a handful of trivia: a too-easy probe saturates at 1.00 for
every arm (the old 4-item stub did exactly that, "improving" to 1.00 by noise).

Two sources, picked per call:

* an **embedded multi-domain bank** (``_BANK``) of genuine general-knowledge
  multiple-choice items in English and Arabic — STEM, geography, history,
  language — large and varied enough that a damaged model actually loses points.
  This is the deterministic, offline path (CI and the default).
* **real MMLU / Arabic-MMLU** via :func:`datasets.load_dataset`, used when
  ``use_external=True`` and ``datasets`` is importable (the GPU box). Best-effort:
  any failure (no network, dataset moved) falls back to the embedded bank, so a
  run never dies on the capability check.

Scoring is unchanged from the original stub and shared with the WVS instrument:
present the stem, score each option's mean log-prob via ``score_continuation``,
count the arg-max as the model's answer. Measuring in the corpus's own language
(``lang``) keeps the guardrail honest — Arabic CPT should preserve Arabic
knowledge.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .model import LanguageModel


@dataclass(frozen=True)
class MCQ:
    """A multiple-choice question with the index of the correct option."""

    question: str
    options: tuple[str, ...]
    answer_index: int


# --- Embedded knowledge bank (offline / CI / default) -----------------------

# Genuine general-knowledge items across domains (geography, science, math,
# history, language). Hand-written, not copied from MMLU, so they are safe to
# ship in an open repo and carry no test-set contamination risk. The correct
# option is placed at varying indices so a model that always picks position 0
# scores at chance, not by accident.
_EN_PROBE: tuple[MCQ, ...] = (
    MCQ("The chemical symbol for gold is", ("Au", "Ag", "Gd", "Go"), 0),
    MCQ("The largest planet in the Solar System is", ("Saturn", "Jupiter", "Neptune", "Earth"), 1),
    MCQ("The square root of 144 is", ("11", "14", "12", "16"), 2),
    MCQ("The author of the play Hamlet is", ("Dickens", "Tolstoy", "Homer", "Shakespeare"), 3),
    MCQ("Water boils at sea level at", ("50 °C", "100 °C", "150 °C", "200 °C"), 1),
    MCQ("The capital of Japan is", ("Tokyo", "Seoul", "Beijing", "Bangkok"), 0),
    MCQ("The powerhouse of the cell is the", ("nucleus", "ribosome", "mitochondrion", "membrane"), 2),
    MCQ("A right angle measures", ("45 degrees", "60 degrees", "90 degrees", "180 degrees"), 2),
    MCQ("The gas plants absorb for photosynthesis is", ("oxygen", "carbon dioxide", "nitrogen", "hydrogen"), 1),
    MCQ("The longest river in the world is generally cited as the", ("Amazon", "Yangtze", "Nile", "Danube"), 2),
    MCQ("The number of continents on Earth is", ("five", "six", "seven", "eight"), 2),
    MCQ("The speed of light is closest to", ("300 km/s", "300,000 km/s", "3,000 km/s", "30 km/s"), 1),
    MCQ("The currency of the United Kingdom is the", ("euro", "dollar", "pound sterling", "franc"), 2),
    MCQ("DNA carries information in sequences of", ("amino acids", "nucleotides", "lipids", "sugars only"), 1),
    MCQ("Seven multiplied by eight equals", ("54", "56", "63", "48"), 1),
    MCQ("The freezing point of water in Fahrenheit is", ("0", "32", "100", "212"), 1),
    MCQ("The painter of the Mona Lisa was", ("Michelangelo", "Raphael", "Leonardo da Vinci", "Donatello"), 2),
    MCQ("The smallest prime number is", ("0", "1", "2", "3"), 2),
    MCQ("Mount Everest is located in the", ("Alps", "Andes", "Rockies", "Himalayas"), 3),
    MCQ("The human body has this many pairs of chromosomes:", ("21", "23", "46", "12"), 1),
    MCQ("The element with atomic number 1 is", ("helium", "hydrogen", "oxygen", "carbon"), 1),
    MCQ("World War II ended in the year", ("1918", "1939", "1945", "1950"), 2),
    MCQ("The plural of the English word 'mouse' (animal) is", ("mouses", "mice", "mouse", "mices"), 1),
    MCQ("Ten percent of two hundred is", ("2", "20", "200", "10"), 1),
)

# Arabic equivalents (Modern Standard Arabic). Distinct items, all with verified
# correct answers, so capability in the corpus's own language is measured rather
# than translated English. Correct index again varies across items.
_AR_PROBE: tuple[MCQ, ...] = (
    MCQ("الرمز الكيميائي للذهب هو", ("Au", "Ag", "Fe", "Go"), 0),
    MCQ("أكبر كوكب في المجموعة الشمسية هو", ("زحل", "المشتري", "نبتون", "الأرض"), 1),
    MCQ("الجذر التربيعي للعدد ١٤٤ هو", ("١١", "١٤", "١٢", "١٦"), 2),
    MCQ("مؤلف مسرحية هاملت هو", ("ديكنز", "تولستوي", "هوميروس", "شكسبير"), 3),
    MCQ(
        "يغلي الماء عند مستوى سطح البحر عند", ("٥٠ درجة مئوية", "١٠٠ درجة مئوية", "١٥٠ درجة مئوية", "٢٠٠ درجة مئوية"), 1
    ),
    MCQ("عاصمة اليابان هي", ("طوكيو", "سيول", "بكين", "بانكوك"), 0),
    MCQ("مركز إنتاج الطاقة في الخلية هو", ("النواة", "الريبوسوم", "الميتوكوندريا", "الغشاء"), 2),
    MCQ("قياس الزاوية القائمة هو", ("٤٥ درجة", "٦٠ درجة", "٩٠ درجة", "١٨٠ درجة"), 2),
    MCQ(
        "الغاز الذي تمتصه النباتات في عملية البناء الضوئي هو",
        ("الأكسجين", "ثاني أكسيد الكربون", "النيتروجين", "الهيدروجين"),
        1,
    ),
    MCQ("أطول نهر في العالم يُذكر عادةً أنه نهر", ("الأمازون", "اليانغتسي", "النيل", "الدانوب"), 2),
    MCQ("عدد القارات على الأرض هو", ("خمس", "ست", "سبع", "ثماني"), 2),
    MCQ("سرعة الضوء أقرب ما تكون إلى", ("٣٠٠ كم/ث", "٣٠٠٠٠٠ كم/ث", "٣٠٠٠ كم/ث", "٣٠ كم/ث"), 1),
    MCQ("عملة المملكة المتحدة هي", ("اليورو", "الدولار", "الجنيه الإسترليني", "الفرنك"), 2),
    MCQ("يحمل الحمض النووي المعلومات في تسلسل من", ("الأحماض الأمينية", "النيوكليوتيدات", "الدهون", "السكريات فقط"), 1),
    MCQ("حاصل ضرب سبعة في ثمانية هو", ("٥٤", "٥٦", "٦٣", "٤٨"), 1),
    MCQ("العنصر ذو العدد الذري ١ هو", ("الهيليوم", "الهيدروجين", "الأكسجين", "الكربون"), 1),
    MCQ("رسام لوحة الموناليزا هو", ("مايكل أنجلو", "رافاييل", "ليوناردو دافنشي", "دوناتيلو"), 2),
    MCQ("أصغر عدد أولي هو", ("٠", "١", "٢", "٣"), 2),
    MCQ("يقع جبل إيفرست في سلسلة", ("الألب", "الأنديز", "روكي", "الهيمالايا"), 3),
    MCQ("انتهت الحرب العالمية الثانية في عام", ("١٩١٨", "١٩٣٩", "١٩٤٥", "١٩٥٠"), 2),
    MCQ("الكوكب المعروف بالكوكب الأحمر هو", ("الزهرة", "المريخ", "عطارد", "المشتري"), 1),
    MCQ("عشرة بالمئة من مئتين تساوي", ("٢", "٢٠", "٢٠٠", "١٠"), 1),
    MCQ("عدد أيام السنة الميلادية العادية هو", ("٣٦٠", "٣٦٥", "٣٧٠", "٣٥٥"), 1),
    MCQ("المعدن السائل في درجة حرارة الغرفة هو", ("الحديد", "الزئبق", "النحاس", "الرصاص"), 1),
)

_BANK: dict[str, tuple[MCQ, ...]] = {"en": _EN_PROBE, "ar": _AR_PROBE}


def _bank_for(lang: str) -> tuple[MCQ, ...]:
    """Embedded items for ``lang``, falling back to English for languages
    without a localized bank (e.g. Vietnamese still measures retained English
    knowledge rather than skipping the guardrail)."""
    return _BANK.get(lang, _EN_PROBE)


# --- Optional real MMLU / Arabic-MMLU (GPU box) ------------------------------

# Real MMLU schemas differ per dataset, so each has a small adapter (load_dataset
# -> list[MCQ]) rather than one rigid column mapping. Adapters are tried in order
# per language; the first that yields items wins, and any failure is swallowed so
# the guardrail degrades to the embedded bank instead of crashing a long run.


def _coerce_answer_index(answer, n_options: int) -> int | None:
    """Normalize an MMLU answer (int index or letter 'A'..'D') to an index."""
    if isinstance(answer, bool):
        return None
    if isinstance(answer, int) and 0 <= answer < n_options:
        return answer
    if isinstance(answer, str):
        a = answer.strip()
        if a.isdigit() and 0 <= int(a) < n_options:
            return int(a)
        if len(a) == 1 and a.upper().isalpha():
            idx = ord(a.upper()) - ord("A")
            if 0 <= idx < n_options:
                return idx
    return None


def _sample(items: list[MCQ], limit: int, seed: int) -> tuple[MCQ, ...]:
    if limit and len(items) > limit:
        items = random.Random(seed).sample(items, limit)
    return tuple(items)


def _load_cais_mmlu(load_dataset, limit: int, seed: int) -> tuple[MCQ, ...]:  # pragma: no cover - needs network
    """cais/mmlu: question, choices (list[str]), answer (int index)."""
    ds = load_dataset("cais/mmlu", "all", split="test")
    items: list[MCQ] = []
    for row in ds:
        opts = row.get("choices")
        if not opts or len(opts) < 2:
            continue
        idx = _coerce_answer_index(row.get("answer"), len(opts))
        if idx is not None:
            items.append(MCQ(str(row["question"]), tuple(str(o) for o in opts), idx))
    return _sample(items, limit, seed)


def _load_mbzuai_arabicmmlu(load_dataset, limit: int, seed: int) -> tuple[MCQ, ...]:  # pragma: no cover - needs network
    """MBZUAI/ArabicMMLU ('All' config): Question, Option 1..5 (unused = 'None'),
    Answer Key (letter), optional Context."""
    ds = load_dataset("MBZUAI/ArabicMMLU", "All", split="test")
    items: list[MCQ] = []
    for row in ds:
        opts = [row.get(f"Option {i}") for i in range(1, 6)]
        opts = [str(o) for o in opts if o is not None and str(o).strip() not in ("", "None")]
        if len(opts) < 2:
            continue
        idx = _coerce_answer_index(row.get("Answer Key"), len(opts))
        if idx is None:
            continue
        question = str(row.get("Question", ""))
        context = row.get("Context")
        if context and str(context).strip() not in ("", "None"):
            question = f"{context}\n{question}"
        items.append(MCQ(question, tuple(opts), idx))
    return _sample(items, limit, seed)


_EXTERNAL_BUILDERS: dict[str, tuple] = {
    "en": (_load_cais_mmlu,),
    "ar": (_load_mbzuai_arabicmmlu,),
}


def _load_external(lang: str, limit: int, *, seed: int = 0) -> tuple[MCQ, ...] | None:
    """Load real MMLU/Arabic-MMLU items, or ``None`` if unavailable.

    Wrapped end-to-end in a broad except: the capability guardrail must never be
    the thing that crashes a multi-hour GPU run, so any failure degrades to the
    embedded bank.
    """
    try:
        from datasets import load_dataset
    except Exception:  # pragma: no cover - datasets is GPU-box-only
        return None
    for builder in _EXTERNAL_BUILDERS.get(lang, ()):  # pragma: no cover - needs network
        try:
            items = builder(load_dataset, limit, seed)
            if items:
                return items
        except Exception:  # pragma: no cover - network / schema drift
            continue
    return None


# --- Scoring -----------------------------------------------------------------


def evaluate(model: LanguageModel, *, lang: str = "en", use_external: bool = False, limit: int = 0) -> float:
    """Return multiple-choice accuracy in [0, 1] via log-prob answer selection.

    ``lang`` selects the item language (matching the survey keeps the guardrail
    in the corpus's own language). ``use_external`` opts into real MMLU when
    ``datasets`` and the network are present, else the embedded bank is used.
    ``limit`` caps the number of external items sampled (0 = all).
    """
    items: tuple[MCQ, ...] | None = None
    if use_external:
        items = _load_external(lang, limit)
    if items is None:
        items = _bank_for(lang)
    correct = 0
    for item in items:
        scored = [model.score_continuation(item.question + " ", opt) for opt in item.options]
        chosen = max(range(len(scored)), key=lambda i: scored[i])
        correct += int(chosen == item.answer_index)
    return correct / len(items)
