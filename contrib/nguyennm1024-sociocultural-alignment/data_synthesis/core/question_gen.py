"""Per-scenario question generation via an LLM, parameterized by prompt template.

Given a scenario record and a prompt template (provided by the calling
domain package), produce N questions per scenario in parallel. The template
must be a format string with placeholders: {n}, {scenario_id}, {topic_id},
{scenario_description}, {topic_description}.

Output records carry provenance (topic_id, scenario_id, batch_id, gen_index)
so downstream stages can group, balance, or trace back. Empty / unparseable
LLM responses yield one error record so silent data loss can't happen.
"""
from __future__ import annotations

import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

import openai

from .client import DEFAULT_MODEL, make_client


_LEAD_NUMBER = re.compile(r"^[\(\[]?\d+[\.\)\]:]\s*")
_LEAD_BULLET = re.compile(r"^[-*•—–]\s*")


def _parse_questions(text: str) -> list[str]:
    """One question per line, strip numbering / bullets / quotes."""
    out: list[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        line = _LEAD_NUMBER.sub("", line)
        line = _LEAD_BULLET.sub("", line)
        line = line.strip().strip('"').strip("'").strip()
        if line:
            out.append(line)
    return out


def generate_questions_for_scenario(
    scenario: dict[str, Any],
    prompt_template: str,
    n: int = 20,
    client: openai.Client | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 16000,
    previous_questions: list[str] | None = None,
) -> list[dict[str, Any]]:
    """One LLM call for one scenario.

    `prompt_template` must contain {n}, {scenario_id}, {topic_id},
    {scenario_description}, {topic_description}, {avoid_section}.

    `previous_questions`: optional list of questions already generated for
    this scenario (from earlier batches or prior runs). When non-empty,
    rendered into the prompt's `{avoid_section}` so Kimi steers away from
    repeating them.
    """
    client = client or make_client()
    avoid_section = ""
    if previous_questions:
        listed = "\n".join(f"- {q}" for q in previous_questions)
        avoid_section = (
            "\nALREADY GENERATED for this scenario — pick DIFFERENT angles, "
            "framings, sub-populations, and question types:\n" + listed + "\n"
        )
    prompt = prompt_template.format(
        scenario_id=scenario["scenario_id"],
        topic_id=scenario["topic_id"],
        topic_description=scenario.get("topic_description", ""),
        scenario_description=scenario["scenario_description"],
        n=n,
        avoid_section=avoid_section,
    )
    batch_id = uuid.uuid4().hex[:8]
    # Newer OpenAI reasoning models (gpt-5.x, o-series) require
    # `max_completion_tokens` and reject `max_tokens`. Other providers and
    # non-reasoning OpenAI models still use `max_tokens`.
    is_reasoning_model = model.startswith(("gpt-5", "o1", "o3", "o4"))
    token_kwarg = {"max_completion_tokens": max_tokens} if is_reasoning_model else {"max_tokens": max_tokens}
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            **token_kwarg,
        )
        content = (resp.choices[0].message.content or "").strip()
        questions = _parse_questions(content)
        if not questions:
            return [
                {
                    "topic_id": scenario["topic_id"],
                    "scenario_id": scenario["scenario_id"],
                    "batch_id": batch_id,
                    "error": "no_questions_parsed",
                    "error_message": f"empty or unparseable response: {content[:200]!r}",
                }
            ]
        return [
            {
                "topic_id": scenario["topic_id"],
                "scenario_id": scenario["scenario_id"],
                "question": q,
                "batch_id": batch_id,
                "gen_index": i,
                "question_model": model,
            }
            for i, q in enumerate(questions)
        ]
    except Exception as e:
        return [
            {
                "topic_id": scenario["topic_id"],
                "scenario_id": scenario["scenario_id"],
                "batch_id": batch_id,
                "error": "gen_failed",
                "error_message": repr(e),
            }
        ]


def generate_questions(
    scenarios: list[dict[str, Any]],
    prompt_template: str,
    n_per_scenario: int = 20,
    concurrency: int = 10,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """Generate questions for multiple scenarios in parallel."""
    client = make_client(api_key=api_key, base_url=base_url)
    all_records: list[dict[str, Any]] = []
    total = len(scenarios)
    done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(
                generate_questions_for_scenario,
                s,
                prompt_template,
                n_per_scenario,
                client,
                model,
            )
            for s in scenarios
        ]
        for fut in as_completed(futures):
            all_records.extend(fut.result())
            done += 1
            if on_progress:
                on_progress(done, total)
    return all_records
