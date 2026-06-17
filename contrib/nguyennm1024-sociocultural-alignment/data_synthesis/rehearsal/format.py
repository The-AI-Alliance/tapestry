"""Record schema + message helpers + JSONL I/O for the rehearsal pipeline.

The Record is the *only* persistent format. Every public-loaded item and every
Kimi-generated item collapses into the same shape, so downstream training code
reads one schema.

Assistant content uses `<THINK>...</THINK><ANSWER>...</ANSWER>` framing. For
public items without reasoning (most MC), THINK is empty until a Kimi solve
pass fills it in. For math/instruction items where the original response IS
the answer, the original text goes into ANSWER and THINK is filled later.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator, Literal, TypedDict


Origin = Literal["public", "augmented", "generated", "programmatic"]


class Provenance(TypedDict, total=False):
    teacher_model: str | None
    source_dataset: str | None     # HF path, e.g. "cais/mmlu"
    source_record_id: str | None   # e.g. "auxiliary_train:18342"
    batch_id: str | None
    generated_at: str | None       # ISO8601


class Record(TypedDict, total=False):
    id: str                        # globally unique, deterministic
    category: str                  # one of 13 from the spec
    source: str                    # spec source name
    origin: Origin
    messages: list[dict[str, Any]] # chat format
    answer_key: dict[str, Any] | None  # category-specific gold for verification
    provenance: Provenance
    verified: bool | None


class QuestionRecord(TypedDict, total=False):
    """Stage 2 output: one row per extracted/augmented/generated question.

    Stage 3 (`answers/solve.py`) reads these, sends `question` to Kimi, and
    produces a Record by wrapping the response into messages. `gold_answer`
    is consumed by `answers/filter.py` for the disagree-drop step (only
    populated where the source has reliable gold).
    """

    id: str                        # "q_" prefix; one per upstream row
    category: str                  # spec category
    source: str                    # spec source name
    origin: Origin

    question: str                  # text passed verbatim to Kimi as user content
    gold_answer: str | None        # extractable atom for comparison; None when no gold
    metadata: dict[str, Any]       # category-specific extras (options, subject, level, …)
    provenance: Provenance


def make_question_id(category: str, source: str, index: int) -> str:
    """Question-pool ID, prefixed `q_` to distinguish from final Records."""
    return "q_" + make_record_id(category, source, index)


# ---------------------------------------------------------------------------
# Message helpers — building and parsing the THINK/ANSWER wrapper
# ---------------------------------------------------------------------------

THINK_OPEN = "<THINK>"
THINK_CLOSE = "</THINK>"
ANSWER_OPEN = "<ANSWER>"
ANSWER_CLOSE = "</ANSWER>"

_THINK_RE = re.compile(r"<THINK>(.*?)</THINK>", re.DOTALL)
_ANSWER_RE = re.compile(r"<ANSWER>(.*?)</ANSWER>", re.DOTALL)


def wrap_assistant(reasoning: str, answer: str) -> str:
    """Build the assistant content string from a (reasoning, answer) pair.

    Both arguments are wrapped verbatim — caller decides whether to trim or
    leave whitespace. Empty reasoning produces `<THINK></THINK>` which is the
    intentional 'no-think' shape.
    """
    return f"{THINK_OPEN}{reasoning}{THINK_CLOSE}{ANSWER_OPEN}{answer}{ANSWER_CLOSE}"


def unwrap_assistant(content: str) -> tuple[str | None, str | None]:
    """Extract (reasoning, answer) from an assistant message. Returns (None,
    None) for either field that isn't present."""
    t = _THINK_RE.search(content)
    a = _ANSWER_RE.search(content)
    return (
        t.group(1) if t else None,
        a.group(1) if a else None,
    )


def build_messages(
    user: str,
    assistant_reasoning: str = "",
    assistant_answer: str = "",
    system: str | None = None,
) -> list[dict[str, Any]]:
    """Standard 1-turn shape: [system?, user, assistant(<THINK><ANSWER>)]."""
    msgs: list[dict[str, Any]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    msgs.append(
        {"role": "assistant", "content": wrap_assistant(assistant_reasoning, assistant_answer)}
    )
    return msgs


# ---------------------------------------------------------------------------
# Record ID generation — deterministic so reruns yield the same IDs
# ---------------------------------------------------------------------------

def make_record_id(category: str, source: str, index: int) -> str:
    """Deterministic id: rhsl_<category-short>_<source-short>_<6-digit-index>."""
    cat_short = category.replace("_shaped", "").replace("_", "")[:8]
    src_short = re.sub(r"[^A-Za-z0-9]", "", source)[:10]
    return f"rhsl_{cat_short}_{src_short}_{index:06d}"


# ---------------------------------------------------------------------------
# JSONL I/O — append-mode, line-buffered, crash-safe
# ---------------------------------------------------------------------------

def write_jsonl(path: Path | str, records: list[dict[str, Any]], *, append: bool = False) -> None:
    mode = "a" if append else "w"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, mode) as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path: Path | str) -> Iterator[dict[str, Any]]:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path | str, record: dict[str, Any]) -> None:
    """Single-record append with flush — survives crashes mid-batch."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def existing_ids(path: Path | str) -> set[str]:
    """Read a JSONL file and return the set of record IDs already present.
    Returns empty set if the file doesn't exist. Used for resumability."""
    p = Path(path)
    if not p.exists():
        return set()
    ids: set[str] = set()
    for rec in read_jsonl(p):
        rid = rec.get("id")
        if rid:
            ids.add(rid)
    return ids
