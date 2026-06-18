"""Decontamination: exact-match + 13-gram filter against eval test sets.

Builds two indexes from the decontam testsets registered in `sources.py`:
  - `exact`     — set of SHA1(normalized text) for full-string match
  - `ngrams`    — set of 13-word-gram hashes for paraphrase / partial-copy match

A training candidate is contaminated if its normalized full text exactly
matches a test item OR if any of its 13-grams appears in any test item.

13-gram is the standard threshold (Llama 3, Chinchilla); short enough to
catch direct copies, long enough to avoid common-phrase false positives.

The semantic-similarity stage from the spec is intentionally NOT implemented
in v1 — add only if the pilot shows leakage past exact+13-gram.

Persistence: index is pickled under `~/.cache/rehearsal_decontam/index.pkl`
so subsequent runs don't rebuild from scratch.
"""
from __future__ import annotations

import hashlib
import pickle
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .sources import DECONTAM_TESTSETS, DecontamTestset


# ---------------------------------------------------------------------------
# Text normalization + n-gram extraction
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation. Used for both exact
    match and n-gram extraction."""
    t = text.lower()
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def ngram_hash(words: tuple[str, ...]) -> int:
    """Stable 8-byte hash for a tuple of words. Stable across runs (unlike
    Python's hash())."""
    joined = " ".join(words).encode("utf-8")
    return int.from_bytes(
        hashlib.blake2b(joined, digest_size=8).digest(), "big", signed=False
    )


def iter_ngrams(text: str, n: int = 13) -> Iterable[int]:
    """Yield hashed n-grams of normalized text. n words per gram."""
    words = normalize(text).split()
    if len(words) < n:
        return
    for i in range(len(words) - n + 1):
        yield ngram_hash(tuple(words[i : i + n]))


# ---------------------------------------------------------------------------
# Per-testset text extractors — yield the text strings to index
# ---------------------------------------------------------------------------

# Each extractor takes a row dict (from `datasets`) and yields one or more
# strings. Different testsets store their question/prompt under different keys.
TextExtractor = Callable[[dict], Iterable[str]]


def _extract_first(row: dict, keys: list[str]) -> Iterable[str]:
    """Yield the first present non-empty key value."""
    for k in keys:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            yield v
            return


def _ext_mmlu(row: dict) -> Iterable[str]:
    yield row["question"]


def _ext_mmlu_pro(row: dict) -> Iterable[str]:
    yield row["question"]


def _ext_gsm8k(row: dict) -> Iterable[str]:
    yield row["question"]


def _ext_math(row: dict) -> Iterable[str]:
    yield row["problem"]


def _ext_ifeval(row: dict) -> Iterable[str]:
    yield row["prompt"]


def _ext_hellaswag(row: dict) -> Iterable[str]:
    # Index context plus each ending so copy-of-ending also trips
    yield row.get("ctx") or row.get("ctx_a") or ""
    for e in row.get("endings", []):
        yield e


def _ext_arc(row: dict) -> Iterable[str]:
    yield row["question"]


def _ext_obqa(row: dict) -> Iterable[str]:
    yield row["question_stem"]


def _ext_piqa(row: dict) -> Iterable[str]:
    yield row["goal"]
    for k in ("sol1", "sol2"):
        if row.get(k):
            yield row[k]


def _ext_siqa(row: dict) -> Iterable[str]:
    yield row["question"]
    yield row.get("context") or ""


def _ext_storycloze(row: dict) -> Iterable[str]:
    # ROCStories: input_sentence_1..4 + ending choices
    for k in ("input_sentence_1", "input_sentence_2", "input_sentence_3", "input_sentence_4"):
        if row.get(k):
            yield row[k]
    for k in ("sentence_quiz1", "sentence_quiz2"):
        if row.get(k):
            yield row[k]


def _ext_gpqa(row: dict) -> Iterable[str]:
    yield row.get("Question") or row.get("question") or ""


def _ext_bfcl(row: dict) -> Iterable[str]:
    # BFCL rows vary by subset; the user 'question' / prompt is what we want.
    yield from _extract_first(row, ["question", "prompt", "instruction"])


def _ext_narrativeqa(row: dict) -> Iterable[str]:
    q = row.get("question") or {}
    if isinstance(q, dict):
        yield q.get("text", "")
    elif isinstance(q, str):
        yield q


def _ext_qasper(row: dict) -> Iterable[str]:
    # QASPER has nested QA structure; flatten the question text
    qas = row.get("qas", {})
    if isinstance(qas, dict):
        for q in qas.get("question", []):
            if isinstance(q, str):
                yield q


def _ext_hotpotqa(row: dict) -> Iterable[str]:
    yield row.get("question") or ""


def _ext_humaneval(row: dict) -> Iterable[str]:
    yield row.get("prompt") or ""


def _ext_mbpp(row: dict) -> Iterable[str]:
    yield row.get("text") or row.get("prompt") or ""


def _ext_infinitebench(row: dict) -> Iterable[str]:
    yield from _extract_first(row, ["input", "question", "prompt", "context"])


EXTRACTORS: dict[str, TextExtractor] = {
    "IFEval": _ext_ifeval,
    "MMLU_test": _ext_mmlu,
    "MMLU_Pro_test": _ext_mmlu_pro,
    "GSM8K_test": _ext_gsm8k,
    "MATH_test": _ext_math,
    "HellaSwag_validation": _ext_hellaswag,
    "ARC_Challenge_test": _ext_arc,
    "ARC_Easy_test": _ext_arc,
    "OpenBookQA_test": _ext_obqa,
    "PIQA_validation": _ext_piqa,
    "SIQA_validation": _ext_siqa,
    "StoryCloze_test": _ext_storycloze,
    "GPQA_test": _ext_gpqa,
    "BFCL_test": _ext_bfcl,
    "NarrativeQA_test": _ext_narrativeqa,
    "QASPER_test": _ext_qasper,
    "HotpotQA_dev": _ext_hotpotqa,
    "HumanEval": _ext_humaneval,
    "MBPP": _ext_mbpp,
    "InfiniteBench": _ext_infinitebench,
}


# ---------------------------------------------------------------------------
# Index data structure
# ---------------------------------------------------------------------------

DEFAULT_INDEX_PATH = Path.home() / ".cache" / "rehearsal_decontam" / "index.pkl"
NGRAM_N = 13


@dataclass
class DecontamIndex:
    """Serializable union of exact + n-gram sets across all testsets."""

    exact: set[str] = field(default_factory=set)       # sha1 of normalized text
    ngrams: set[int] = field(default_factory=set)      # 13-gram blake2b hashes
    per_testset_counts: dict[str, int] = field(default_factory=dict)

    def add_text(self, text: str) -> None:
        if not text:
            return
        n = normalize(text)
        if not n:
            return
        self.exact.add(sha1(n))
        for h in iter_ngrams(n, n=NGRAM_N):
            self.ngrams.add(h)

    def __len__(self) -> int:
        return len(self.exact)


# ---------------------------------------------------------------------------
# Build + load
# ---------------------------------------------------------------------------

def _load_hf(testset: DecontamTestset):
    from datasets import load_dataset
    kwargs = {"split": testset.hf_split}
    if testset.hf_config:
        kwargs["name"] = testset.hf_config
    try:
        return load_dataset(testset.hf_path, **kwargs)
    except Exception:
        # Some legacy datasets need trust_remote_code
        return load_dataset(testset.hf_path, **kwargs, trust_remote_code=True)


def build_index(
    *,
    out_path: Path | str = DEFAULT_INDEX_PATH,
    only: list[str] | None = None,
    log=sys.stderr,
) -> DecontamIndex:
    """Build the decontam index by iterating each testset and indexing the
    extracted text. Writes pickle to `out_path` on completion.

    `only`: optional list of DecontamTestset names to index (otherwise all).
    """
    idx = DecontamIndex()
    targets = DECONTAM_TESTSETS if only is None else [
        t for t in DECONTAM_TESTSETS if t.name in only
    ]
    for i, ts in enumerate(targets, 1):
        if ts.name not in EXTRACTORS:
            print(f"[decontam] ({i}/{len(targets)}) {ts.name}: no extractor, skipping",
                  file=log, flush=True)
            continue
        extractor = EXTRACTORS[ts.name]
        t0 = time.time()
        print(f"[decontam] ({i}/{len(targets)}) {ts.name}: loading {ts.hf_path}...",
              file=log, flush=True)
        try:
            ds = _load_hf(ts)
        except Exception as e:
            print(f"    FAILED to load: {e!r}", file=log, flush=True)
            continue
        n_rows = 0
        n_texts = 0
        for row in ds:
            n_rows += 1
            for txt in extractor(row):
                if txt:
                    idx.add_text(txt)
                    n_texts += 1
        idx.per_testset_counts[ts.name] = n_rows
        print(f"    {n_rows} rows, {n_texts} texts indexed, {time.time() - t0:.1f}s "
              f"(total exact={len(idx.exact)} ngrams={len(idx.ngrams)})",
              file=log, flush=True)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(idx, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[decontam] wrote index to {out} "
          f"(exact={len(idx.exact)}, ngrams={len(idx.ngrams)})", file=log)
    return idx


def load_index(path: Path | str = DEFAULT_INDEX_PATH) -> DecontamIndex:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"decontam index not found at {p}. "
            "Build it first: `python -m rehearsal.cli decontam-build`"
        )
    with open(p, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ContaminationResult:
    contaminated: bool
    reason: str | None = None      # "exact" | "ngram" | None
    overlap_count: int = 0         # number of 13-grams matched (for ngram reason)


class Contaminator:
    """Holds a loaded DecontamIndex and answers `is_contaminated(text)`."""

    def __init__(self, index: DecontamIndex):
        self.index = index

    @classmethod
    def from_disk(cls, path: Path | str = DEFAULT_INDEX_PATH) -> "Contaminator":
        return cls(load_index(path))

    def is_contaminated(self, text: str) -> ContaminationResult:
        if not text:
            return ContaminationResult(False)
        norm = normalize(text)
        if not norm:
            return ContaminationResult(False)
        if sha1(norm) in self.index.exact:
            return ContaminationResult(True, reason="exact")
        # 13-gram: ANY shared gram = contaminated, per spec.
        overlap = 0
        for h in iter_ngrams(norm, n=NGRAM_N):
            if h in self.index.ngrams:
                overlap += 1
                # Short-circuit: spec says ANY shared 13-gram is enough.
                return ContaminationResult(True, reason="ngram", overlap_count=1)
        return ContaminationResult(False, overlap_count=overlap)
