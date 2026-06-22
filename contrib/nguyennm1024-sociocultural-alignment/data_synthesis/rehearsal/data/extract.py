"""Normalize cached HuggingFace rows into QuestionRecord JSONL.

For each public source registered in `sources.py`, an extractor function
converts HF row dicts into the uniform QuestionRecord schema (defined in
`format.py`). Three concerns shape this module:

  1. Field-mapping. Every dataset uses different keys (`question`, `goal`,
     `problem`, `prompt`). Per-source extractor functions handle this.
  2. Format. MC items get rendered as "Q\\nA) opt\\nB) opt..." so Kimi sees
     the same surface form regardless of origin; math items keep the bare
     problem text; instruction items pass the prompt through.
  3. Gold extraction. For categories with reliable gold (math, MC), the
     extractor pulls the comparable atom (letter / number / etc.). For
     instruction / conversation / tool-call, `gold_answer=None` and
     verification happens via format/constraint checks downstream.

Output layout: `<rehearsal_root>/questions/_pool/<category>/<source>.jsonl`.
One file per source means reruns are scoped — no merging needed at write
time, the assembly step joins them later.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator

from ..format import (
    Provenance,
    QuestionRecord,
    append_jsonl,
    make_question_id,
)
from .sources import SOURCES_BY_NAME, HFSource


# ---------------------------------------------------------------------------
# Output path resolution
# ---------------------------------------------------------------------------

QUESTIONS_POOL_DIR = Path(__file__).resolve().parent.parent / "questions" / "_pool"


def pool_path(category: str, source: str) -> Path:
    return QUESTIONS_POOL_DIR / category / f"{source}.jsonl"


# ---------------------------------------------------------------------------
# Common formatters
# ---------------------------------------------------------------------------

MC_LETTERS = list("ABCDEFGHIJKLMN")


def format_mc(question: str, options: list[str]) -> tuple[str, list[str]]:
    """Render an MC question as `Q\\nA) opt1\\nB) opt2\\n...` and return the
    letter list aligned with `options`. Used by every MC extractor."""
    letters = MC_LETTERS[: len(options)]
    lines = [question.strip(), ""]
    for letter, opt in zip(letters, options):
        lines.append(f"{letter}) {str(opt).strip()}")
    return "\n".join(lines), letters


_GSM8K_ANSWER_RE = re.compile(r"####\s*([\-\$\d\.,]+)")


def extract_gsm8k_final(answer_field: str) -> str | None:
    """GSM8K solutions end with `#### N`. Pull the N."""
    m = _GSM8K_ANSWER_RE.search(answer_field or "")
    if not m:
        return None
    return m.group(1).strip().replace(",", "").lstrip("$")


_BOXED_RE = re.compile(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")


def extract_math_boxed(solution: str) -> str | None:
    """MATH solutions wrap the final answer in `\\boxed{...}`. Pull it.

    Returns the contents of the LAST \\boxed{} in the solution (sometimes
    intermediate boxed values appear). Best-effort — None when no boxed found.
    """
    if not solution:
        return None
    matches = _BOXED_RE.findall(solution)
    if not matches:
        return None
    return matches[-1].strip()


def _make_provenance(src: HFSource, row_idx: int) -> Provenance:
    return {
        "source_dataset": src.hf_path,
        "source_record_id": f"{src.hf_split}:{row_idx}",
    }


# ---------------------------------------------------------------------------
# Loading helper — match `decontam._load_hf`
# ---------------------------------------------------------------------------

def _load_hf_split(src: HFSource):
    from datasets import load_dataset
    kwargs: dict[str, Any] = {"split": src.hf_split}
    if src.hf_config:
        kwargs["name"] = src.hf_config
    try:
        return load_dataset(src.hf_path, **kwargs)
    except Exception:
        return load_dataset(src.hf_path, **kwargs, trust_remote_code=True)


# ===========================================================================
# Extractor functions
# ===========================================================================
# Each extractor takes (src: HFSource) and yields QuestionRecord. They all
# load the dataset themselves (so they can apply per-source row filters
# before yielding).
# ===========================================================================


def _extract_mmlu_aux(src: HFSource) -> Iterator[QuestionRecord]:
    """`cais/mmlu` auxiliary_train is a one-column dataset; the actual fields
    are nested inside row['train']. Other MMLU configs are flat."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        # Unwrap nested 'train' dict if present
        inner = row.get("train") if isinstance(row.get("train"), dict) else row
        choices = inner.get("choices") or []
        if len(choices) != 4:
            continue
        ans_idx = inner.get("answer")
        if not isinstance(ans_idx, int) or ans_idx < 0 or ans_idx >= len(choices):
            continue
        q_text, letters = format_mc(inner["question"], list(choices))
        yield {
            "id": make_question_id("mmlu_shaped", src.name, i),
            "category": "mmlu_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": letters[ans_idx],
            "metadata": {
                "format": "mc_4way",
                "subject": inner.get("subject", ""),
                "options": list(choices),
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_mmlu_pro(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        options = row.get("options") or []
        if not options:
            continue
        ans_idx = row.get("answer_index")
        if not isinstance(ans_idx, int) or ans_idx < 0 or ans_idx >= len(options):
            continue
        q_text, letters = format_mc(row["question"], list(options))
        yield {
            "id": make_question_id("mmlu_shaped", src.name, i),
            "category": "mmlu_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": letters[ans_idx],
            "metadata": {
                "format": f"mc_{len(options)}way",
                "category_label": row.get("category", ""),
                "options": list(options),
            },
            "provenance": _make_provenance(src, i),
        }


def _arc_choices(row: dict) -> tuple[list[str], str] | None:
    """ARC has `choices: {text: [...], label: [...]}, answerKey: 'A' or '1'`."""
    choices = row.get("choices") or {}
    texts = choices.get("text") or []
    labels = choices.get("label") or []
    answer_key = (row.get("answerKey") or "").strip()
    if not texts or not labels or not answer_key:
        return None
    if answer_key not in labels:
        return None
    # Reorder so the answer letter aligns with our MC_LETTERS
    pairs = list(zip(labels, texts))
    correct_idx = labels.index(answer_key)
    return [t for _, t in pairs], MC_LETTERS[correct_idx]


def _extract_arc(category: str, src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        result = _arc_choices(row)
        if result is None:
            continue
        texts, gold_letter = result
        q_text, _ = format_mc(row["question"], texts)
        yield {
            "id": make_question_id(category, src.name, i),
            "category": category,
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": gold_letter,
            "metadata": {
                "format": f"mc_{len(texts)}way",
                "options": texts,
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_arc_challenge(src: HFSource) -> Iterator[QuestionRecord]:
    yield from _extract_arc("arc_challenge_shaped", src)


def _extract_arc_easy(src: HFSource) -> Iterator[QuestionRecord]:
    yield from _extract_arc("arc_challenge_shaped", src)  # same target category per spec


def _extract_openbookqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        choices = row.get("choices") or {}
        texts = choices.get("text") or []
        labels = choices.get("label") or []
        answer_key = (row.get("answerKey") or "").strip()
        if not texts or not labels or answer_key not in labels:
            continue
        gold_letter = MC_LETTERS[labels.index(answer_key)]
        q_text, _ = format_mc(row["question_stem"], list(texts))
        yield {
            "id": make_question_id("arc_challenge_shaped", src.name, i),
            "category": "arc_challenge_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": gold_letter,
            "metadata": {
                "format": "mc_4way",
                "options": list(texts),
                "fact": row.get("fact1", ""),
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_hellaswag(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        endings = row.get("endings") or []
        if len(endings) != 4:
            continue
        label = row.get("label")
        if label in (None, ""):
            continue
        try:
            ans_idx = int(label)
        except (TypeError, ValueError):
            continue
        if ans_idx < 0 or ans_idx >= 4:
            continue
        context = row.get("ctx") or row.get("ctx_a") or ""
        q_text, letters = format_mc(
            f"Complete the following:\n\n{context}",
            list(endings),
        )
        yield {
            "id": make_question_id("hellaswag_shaped", src.name, i),
            "category": "hellaswag_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": letters[ans_idx],
            "metadata": {
                "format": "mc_4way",
                "activity_label": row.get("activity_label", ""),
                "endings": list(endings),
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_piqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        label = row.get("label")
        if label not in (0, 1):
            continue
        opts = [row.get("sol1", ""), row.get("sol2", "")]
        if not all(opts):
            continue
        q_text, letters = format_mc(row["goal"], opts)
        yield {
            "id": make_question_id("hellaswag_shaped", src.name, i),
            "category": "hellaswag_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": letters[label],
            "metadata": {"format": "mc_2way", "options": opts},
            "provenance": _make_provenance(src, i),
        }


def _extract_siqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        opts = [row.get("answerA", ""), row.get("answerB", ""), row.get("answerC", "")]
        if not all(opts):
            continue
        label_raw = str(row.get("label", "")).strip()
        try:
            ans_idx = int(label_raw) - 1  # SIQA labels are 1/2/3
        except (TypeError, ValueError):
            continue
        if ans_idx < 0 or ans_idx >= 3:
            continue
        context = row.get("context", "")
        q = f"{context}\n\n{row['question']}" if context else row["question"]
        q_text, letters = format_mc(q, opts)
        yield {
            "id": make_question_id("hellaswag_shaped", src.name, i),
            "category": "hellaswag_shaped",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": letters[ans_idx],
            "metadata": {"format": "mc_3way", "options": opts},
            "provenance": _make_provenance(src, i),
        }


def _extract_gsm8k(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        final = extract_gsm8k_final(row.get("answer", ""))
        if final is None:
            continue
        yield {
            "id": make_question_id("gsm8k_shaped_math", src.name, i),
            "category": "gsm8k_shaped_math",
            "source": src.name,
            "origin": "public",
            "question": row["question"].strip(),
            "gold_answer": final,
            "metadata": {
                "format": "math_word_problem",
                "reference_solution": row.get("answer", ""),
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_math(src: HFSource) -> Iterator[QuestionRecord]:
    """MATH train via EleutherAI/hendrycks_math (loading-script-free mirror).
    The mirror exposes 7 subject configs; iterate all when `iter_all_configs`
    is set in src.filter. Apply level filter post-load."""
    from datasets import get_dataset_config_names, load_dataset

    allowed_levels = set(src.filter.get("levels") or [])
    iter_configs: list[str | None]
    if src.filter.get("iter_all_configs") and src.hf_config is None:
        iter_configs = list(get_dataset_config_names(src.hf_path))
    else:
        iter_configs = [src.hf_config]

    global_i = 0
    for cfg in iter_configs:
        try:
            ds = load_dataset(src.hf_path, cfg, split=src.hf_split) if cfg \
                else load_dataset(src.hf_path, split=src.hf_split)
        except Exception:
            ds = (load_dataset(src.hf_path, cfg, split=src.hf_split,
                               trust_remote_code=True) if cfg
                  else load_dataset(src.hf_path, split=src.hf_split,
                                    trust_remote_code=True))
        for row in ds:
            global_i += 1
            level_raw = (row.get("level") or "").strip()
            try:
                level_num = int(level_raw.replace("Level", "").strip())
            except (TypeError, ValueError):
                continue
            if allowed_levels and level_num not in allowed_levels:
                continue
            final = extract_math_boxed(row.get("solution", ""))
            if final is None:
                continue
            yield {
                "id": make_question_id("math_shaped", src.name, global_i),
                "category": "math_shaped",
                "source": src.name,
                "origin": "public",
                "question": row["problem"].strip(),
                "gold_answer": final,
                "metadata": {
                    "format": "math_competition",
                    "level": level_num,
                    "subject": row.get("type", "") or cfg or "",
                    "reference_solution": row.get("solution", ""),
                },
                "provenance": {
                    "source_dataset": src.hf_path,
                    "source_record_id": f"{cfg}:{src.hf_split}:{global_i}" if cfg
                                        else f"{src.hf_split}:{global_i}",
                },
            }


def _extract_metamathqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    # Filter to GSM8K-derived items, exclude MATH-derived (per Part A guide).
    for i, row in enumerate(ds):
        item_type = (row.get("type") or "").lower()
        if "math" in item_type and "gsm" not in item_type:
            continue
        question = row.get("query") or row.get("original_question") or ""
        response = row.get("response") or ""
        # Pull final numeric answer from "The answer is: N" or similar
        m = re.search(r"answer is[:\s]+\$?([\-\d\.\,]+)", response, re.IGNORECASE)
        if not m:
            continue
        final = m.group(1).strip().replace(",", "").lstrip("$")
        yield {
            "id": make_question_id("gsm8k_shaped_math", src.name, i),
            "category": "gsm8k_shaped_math",
            "source": src.name,
            "origin": "public",
            "question": question.strip(),
            "gold_answer": final,
            "metadata": {
                "format": "math_word_problem",
                "type": item_type,
                "reference_solution": response,
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_asdiv(src: HFSource) -> Iterator[QuestionRecord]:
    """MU-NLPC/Calc-asdiv_a fields: question, result, result_float, chain."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        question = (row.get("question") or "").strip()
        result = row.get("result") or ""
        result_float = row.get("result_float")
        gold = str(result).strip() or (
            str(result_float).rstrip("0").rstrip(".") if result_float is not None else ""
        )
        if not question or not gold:
            continue
        unit = row.get("result_unit") or ""
        yield {
            "id": make_question_id("gsm8k_shaped_math", src.name, i),
            "category": "gsm8k_shaped_math",
            "source": src.name,
            "origin": "public",
            "question": question,
            "gold_answer": gold,
            "metadata": {
                "format": "math_word_problem",
                "unit": unit,
                "reference_solution": row.get("chain") or "",
                "grade": row.get("grade"),
            },
            "provenance": _make_provenance(src, i),
        }


# --- Instruction family (no gold; Kimi's response is authoritative) ---


def _yield_instruction(src: HFSource, category: str, prompt_field: str | list[str],
                      response_field: str | list[str] | None = None
                      ) -> Iterator[QuestionRecord]:
    """Generic single-turn instruction extractor.

    `prompt_field` / `response_field`: the row key, or a list of candidates
    to try in order (first non-empty wins).
    """
    ds = _load_hf_split(src)
    prompt_keys = [prompt_field] if isinstance(prompt_field, str) else prompt_field
    response_keys = (
        [response_field] if isinstance(response_field, str)
        else response_field if response_field is not None
        else []
    )
    for i, row in enumerate(ds):
        prompt = ""
        for k in prompt_keys:
            v = row.get(k)
            if isinstance(v, str) and v.strip():
                prompt = v.strip()
                break
        if not prompt:
            continue
        ref = ""
        for k in response_keys:
            v = row.get(k)
            if isinstance(v, str) and v.strip():
                ref = v.strip()
                break
        meta: dict[str, Any] = {"format": "instruction"}
        if ref:
            meta["reference_response"] = ref
        yield {
            "id": make_question_id(category, src.name, i),
            "category": category,
            "source": src.name,
            "origin": "public",
            "question": prompt,
            "gold_answer": None,
            "metadata": meta,
            "provenance": _make_provenance(src, i),
        }


def _extract_ifeval_train(src: HFSource) -> Iterator[QuestionRecord]:
    yield from _yield_instruction(src, "ifeval_shaped",
                                  prompt_field=["prompt", "instruction"],
                                  response_field=["response", "completion"])


def _extract_norobots(src: HFSource) -> Iterator[QuestionRecord]:
    """NoRobots messages: row['messages'] = [{role, content}]. Single-turn only."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        msgs = row.get("messages") or []
        if not isinstance(msgs, list) or len(msgs) < 2:
            continue
        # Find user prompt + first assistant response
        user, asst = None, None
        for m in msgs:
            if m.get("role") == "user" and user is None:
                user = m.get("content")
            elif m.get("role") == "assistant" and user is not None and asst is None:
                asst = m.get("content")
                break
        if not user:
            continue
        yield {
            "id": make_question_id("ifeval_shaped", src.name, i),
            "category": "ifeval_shaped",
            "source": src.name,
            "origin": "public",
            "question": str(user).strip(),
            "gold_answer": None,
            "metadata": {
                "format": "instruction",
                "category_label": row.get("category", ""),
                "reference_response": str(asst).strip() if asst else "",
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_tulu3(src: HFSource) -> Iterator[QuestionRecord]:
    """Tulu-3 SFT mixture: messages list. Filter single-turn English."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        msgs = row.get("messages") or []
        if not isinstance(msgs, list):
            continue
        # Single-turn = 2 messages (user + assistant)
        if len(msgs) != 2:
            continue
        if msgs[0].get("role") != "user" or msgs[1].get("role") != "assistant":
            continue
        user = msgs[0].get("content") or ""
        if not user.strip():
            continue
        yield {
            "id": make_question_id("general_instruction_breadth", src.name, i),
            "category": "general_instruction_breadth",
            "source": src.name,
            "origin": "public",
            "question": user.strip(),
            "gold_answer": None,
            "metadata": {
                "format": "instruction",
                "source_id": row.get("source", ""),
                "reference_response": (msgs[1].get("content") or "").strip(),
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_openhermes(src: HFSource) -> Iterator[QuestionRecord]:
    """OpenHermes-2.5: row['conversations'] = [{from: 'human'|'gpt', value}]."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        convs = row.get("conversations") or []
        if not isinstance(convs, list) or len(convs) < 2:
            continue
        if convs[0].get("from") not in ("human", "user"):
            continue
        user = convs[0].get("value") or ""
        if not user.strip():
            continue
        asst = ""
        if convs[1].get("from") in ("gpt", "assistant"):
            asst = convs[1].get("value") or ""
        yield {
            "id": make_question_id("general_instruction_breadth", src.name, i),
            "category": "general_instruction_breadth",
            "source": src.name,
            "origin": "public",
            "question": user.strip(),
            "gold_answer": None,
            "metadata": {"format": "instruction",
                        "reference_response": asst.strip()},
            "provenance": _make_provenance(src, i),
        }


def _extract_oasst_top(src: HFSource) -> Iterator[QuestionRecord]:
    """OASST is a forest of messages. For TOP_RATED single-turn, pick
    message_tree_id roots that are user prompts with at least one
    high-quality assistant response. Best-effort flat extraction."""
    ds = _load_hf_split(src)
    seen_trees: set[str] = set()
    for i, row in enumerate(ds):
        if row.get("role") != "prompter":
            continue
        tree = row.get("message_tree_id") or ""
        if tree in seen_trees:
            continue
        if row.get("lang") not in (None, "", "en"):
            continue
        text = row.get("text") or ""
        if not text.strip():
            continue
        seen_trees.add(tree)
        yield {
            "id": make_question_id("general_instruction_breadth", src.name, i),
            "category": "general_instruction_breadth",
            "source": src.name,
            "origin": "public",
            "question": text.strip(),
            "gold_answer": None,
            "metadata": {"format": "instruction", "tree_id": tree},
            "provenance": _make_provenance(src, i),
        }


def _extract_codealpaca(src: HFSource) -> Iterator[QuestionRecord]:
    yield from _yield_instruction(src, "code",
                                  prompt_field=["instruction", "prompt"],
                                  response_field=["output", "response"])


def _extract_magicoder(src: HFSource) -> Iterator[QuestionRecord]:
    yield from _yield_instruction(src, "code",
                                  prompt_field=["instruction", "problem"],
                                  response_field=["response", "solution"])


# --- Tool calling ---


def _extract_xlam(src: HFSource) -> Iterator[QuestionRecord]:
    """Salesforce/xlam-function-calling-60k. Row: query (str), tools (list/str),
    answers (str — JSON of expected calls)."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        query = row.get("query") or ""
        tools = row.get("tools") or ""
        answers = row.get("answers") or ""
        if not query.strip():
            continue
        q_text = f"{query.strip()}\n\nAvailable tools:\n{tools}"
        yield {
            "id": make_question_id("bfcl_shaped_tool_calling", src.name, i),
            "category": "bfcl_shaped_tool_calling",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": answers,
            "metadata": {
                "format": "tool_call",
                "tools": tools,
                "reference_answer": answers,
            },
            "provenance": _make_provenance(src, i),
        }


def _extract_glaive_fc(src: HFSource) -> Iterator[QuestionRecord]:
    """glaiveai/glaive-function-calling-v2. Schema varies; row['system'] +
    row['chat'] is common. We extract the first user turn as question."""
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        system = row.get("system") or ""
        chat = row.get("chat") or ""
        if not chat:
            continue
        # Find first USER turn
        m = re.search(r"USER:\s*(.*?)(?=\n\s*(?:ASSISTANT|FUNCTION RESPONSE)|\Z)", chat, re.DOTALL)
        if not m:
            continue
        user = m.group(1).strip()
        q_text = f"{system}\n\n{user}" if system else user
        yield {
            "id": make_question_id("bfcl_shaped_tool_calling", src.name, i),
            "category": "bfcl_shaped_tool_calling",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": None,
            "metadata": {"format": "tool_call",
                        "reference_chat": chat},
            "provenance": _make_provenance(src, i),
        }


# --- Long context (just expose question + context; gold extracted later) ---


def _extract_narrativeqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        doc = (row.get("document") or {}).get("text") or ""
        q = (row.get("question") or {}).get("text") or ""
        answers = [a.get("text", "") for a in (row.get("answers") or [])]
        if not q.strip() or not doc.strip():
            continue
        q_text = f"Read the following passage and answer the question.\n\n{doc}\n\nQuestion: {q.strip()}"
        yield {
            "id": make_question_id("long_context", src.name, i),
            "category": "long_context",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": answers[0] if answers else None,
            "metadata": {"format": "long_context_qa", "reference_answers": answers},
            "provenance": _make_provenance(src, i),
        }


def _extract_hotpotqa(src: HFSource) -> Iterator[QuestionRecord]:
    ds = _load_hf_split(src)
    for i, row in enumerate(ds):
        q = row.get("question") or ""
        ans = row.get("answer") or ""
        ctx = row.get("context") or {}
        # `context` is {title: [...], sentences: [[...], [...]]} in distractor config
        passages: list[str] = []
        if isinstance(ctx, dict):
            titles = ctx.get("title") or []
            sentlists = ctx.get("sentences") or []
            for t, sents in zip(titles, sentlists):
                passages.append(f"### {t}\n" + " ".join(sents))
        passage_block = "\n\n".join(passages)
        if not q.strip() or not passage_block:
            continue
        q_text = f"Use the following passages to answer.\n\n{passage_block}\n\nQuestion: {q.strip()}"
        yield {
            "id": make_question_id("long_context", src.name, i),
            "category": "long_context",
            "source": src.name,
            "origin": "public",
            "question": q_text,
            "gold_answer": ans if ans else None,
            "metadata": {"format": "long_context_qa"},
            "provenance": _make_provenance(src, i),
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

Extractor = Callable[[HFSource], Iterator[QuestionRecord]]


EXTRACTORS: dict[str, Extractor] = {
    # MC
    "MMLU_auxiliary_training": _extract_mmlu_aux,
    "MMLU_Pro_train": _extract_mmlu_pro,
    "ARC_Challenge_train": _extract_arc_challenge,
    "ARC_Easy_train": _extract_arc_easy,
    "OpenBookQA_train": _extract_openbookqa,
    "HellaSwag_train": _extract_hellaswag,
    "PIQA_train": _extract_piqa,
    "SIQA_train": _extract_siqa,
    # Math
    "GSM8K_train": _extract_gsm8k,
    "MATH_train_levels_1_2": _extract_math,
    "MATH_train_level_3": _extract_math,
    "MATH_train_levels_4_5": _extract_math,
    "MetaMathQA": _extract_metamathqa,
    "ASDiv_and_easy_subset": _extract_asdiv,
    # Instruction
    "IFEval_style_training_prompts": _extract_ifeval_train,
    "NoRobots_filtered": _extract_norobots,
    "Tulu_3_SFT_high_quality": _extract_tulu3,
    "OpenHermes_2.5_curated": _extract_openhermes,
    "OASST_top_rated": _extract_oasst_top,
    "CodeAlpaca": _extract_codealpaca,
    "Magicoder_Evol_Instruct": _extract_magicoder,
    # Tool calling
    "xLAM": _extract_xlam,
    "Glaive_Function_Calling_v2": _extract_glaive_fc,
    # Long context
    "NarrativeQA": _extract_narrativeqa,
    "HotpotQA_distractor": _extract_hotpotqa,
    # NOT YET WIRED (deferred to a follow-up; schemas are nontrivial):
    # - Story_Cloze_train (ROCStories synthesis)
    # - Hermes_Function_Calling (multiple subsplits to merge)
    # - API_Bank_filtered (multi-turn API dialogues)
    # - QASPER (nested QA, large contexts)
    # - Long_Data_Collections (multiple subsets to choose from)
    # - OASST_multi_turn_non_cultural / ShareGPT / WildChat (need cultural filter)
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def extract_one(
    source_name: str,
    *,
    limit: int | None = None,
    out_path: Path | None = None,
    log=sys.stderr,
) -> int:
    """Run the extractor for one source. Writes JSONL, returns row count."""
    src = SOURCES_BY_NAME.get(source_name)
    if src is None:
        raise KeyError(f"unknown source: {source_name}")
    extractor = EXTRACTORS.get(source_name)
    if extractor is None:
        raise NotImplementedError(
            f"no extractor registered for {source_name} "
            f"(origin={src.origin}; see extract.py registry)"
        )
    out = out_path or pool_path(_category_for(src), source_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Truncate any prior output for this source — full rerun semantics.
    if out.exists():
        out.unlink()

    t0 = time.time()
    print(f"[extract] {source_name}: loading {src.hf_path}...", file=log, flush=True)
    count = 0
    for rec in extractor(src):
        append_jsonl(out, rec)
        count += 1
        if limit is not None and count >= limit:
            break
    print(f"[extract] {source_name}: wrote {count} records to {out} ({time.time()-t0:.1f}s)",
          file=log, flush=True)
    return count


def _category_for(src: HFSource) -> str:
    """Look up a source's target category via spec.py (each source belongs to
    exactly one category)."""
    from ..spec import get_source
    s = get_source(src.name)
    if s is None:
        raise RuntimeError(f"source {src.name} not in spec")
    return s.category


def extract_all(
    *,
    category_filter: str | None = None,
    source_filter: str | None = None,
    limit_per_source: int | None = None,
    log=sys.stderr,
) -> dict[str, int]:
    """Drive extract_one across every registered extractor that matches the
    filters. Returns {source_name: row_count}."""
    from ..spec import iter_sources
    results: dict[str, int] = {}
    for spec_src in iter_sources():
        if source_filter and spec_src.name != source_filter:
            continue
        if category_filter and spec_src.category != category_filter:
            continue
        if spec_src.name not in EXTRACTORS:
            continue  # unwired sources are silently skipped
        try:
            n = extract_one(spec_src.name, limit=limit_per_source, log=log)
            results[spec_src.name] = n
        except Exception as e:
            print(f"[extract] {spec_src.name}: FAILED — {e!r}", file=log, flush=True)
            results[spec_src.name] = -1
    return results
