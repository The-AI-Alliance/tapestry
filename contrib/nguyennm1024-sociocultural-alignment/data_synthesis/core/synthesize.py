"""Parallel answer synthesis.

Given a list of questions and a system prompt anchoring the desired voice,
generates `{question, reasoning, answer, ...}` records. Domain-agnostic —
the caller assembles the system prompt (see `cultural.personas` for one
example of how a domain package does this).
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable

import openai

from .client import DEFAULT_MODEL, make_client


def _generate_one(
    client: openai.Client,
    model: str,
    system_prompt: str,
    question: str,
    max_tokens: int,
) -> dict[str, Any]:
    record: dict[str, Any] = {"question": question}
    # Newer OpenAI reasoning models (gpt-5.x, o-series) require
    # `max_completion_tokens` and reject `max_tokens`.
    is_openai_reasoning = model.startswith(("gpt-5", "o1", "o3", "o4"))
    token_kwarg = {"max_completion_tokens": max_tokens} if is_openai_reasoning else {"max_tokens": max_tokens}
    # DeepSeek V4 needs explicit thinking-mode flag to emit reasoning_content.
    extra_kwargs: dict[str, Any] = {}
    if model.startswith("deepseek-v4"):
        extra_kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=1.0,
            stream=True,
            stream_options={"include_usage": True},
            **token_kwarg,
            **extra_kwargs,
        )
        reasoning_parts: list[str] = []
        content_parts: list[str] = []
        usage = None
        for chunk in stream:
            if chunk.usage:
                usage = chunk.usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            rc = getattr(delta, "reasoning_content", None)
            if rc:
                reasoning_parts.append(rc)
            if delta.content:
                content_parts.append(delta.content)
        record["reasoning"] = "".join(reasoning_parts) or None
        record["answer"] = "".join(content_parts)
        if usage:
            record["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
            }
    except openai.BadRequestError as e:
        msg = str(e)
        record["error"] = (
            "content_filter"
            if "content_filter" in msg or "high risk" in msg
            else "bad_request"
        )
        record["error_message"] = msg
    except openai.RateLimitError as e:
        record["error"] = "rate_limit"
        record["error_message"] = str(e)
    except Exception as e:
        record["error"] = "unknown"
        record["error_message"] = repr(e)
    return record


def _generate_with_retry(
    client: openai.Client,
    model: str,
    system_prompt: str,
    question: str,
    max_tokens: int,
    max_retries: int,
) -> dict[str, Any]:
    """Retry on client-side timeouts / network glitches with exponential
    backoff. Rate-limit, 5xx, and connection errors are already retried
    inside the SDK with Retry-After respect — by the time we see them as
    error records, the SDK has exhausted its retries, so we don't double-
    retry. Content-filter / bad-request errors are deterministic, also
    not retried."""
    rec: dict[str, Any] = {}
    for attempt in range(max_retries + 1):
        rec = _generate_one(client, model, system_prompt, question, max_tokens)
        if rec.get("error") != "unknown":
            return rec
        if attempt < max_retries:
            time.sleep(min(2**attempt, 30))
    return rec


def synthesize_one(
    question: str,
    system_prompt: str,
    *,
    client: openai.Client | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 16000,
    max_retries: int = 2,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Synthesize one answer with retry. Single-question primitive for
    streaming/resumable pipelines that need per-result control. For batch
    use, see `synthesize`."""
    client = client or make_client(api_key=api_key, base_url=base_url)
    rec = _generate_with_retry(client, model, system_prompt, question, max_tokens, max_retries)
    rec["answer_model"] = model
    return rec


def synthesize(
    questions: Iterable[str],
    system_prompt: str,
    model: str = DEFAULT_MODEL,
    concurrency: int = 20,
    max_tokens: int = 16000,
    max_retries: int = 2,
    api_key: str | None = None,
    base_url: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """Synthesize answers for a batch of questions under a given system prompt.

    Returns records in input order with `question`, `reasoning`, `answer`,
    `usage`, `model`. On failure: `question`, `model`, `error`, `error_message`.
    """
    questions = list(questions)
    client = make_client(api_key=api_key, base_url=base_url)
    results: list[dict[str, Any] | None] = [None] * len(questions)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(
                _generate_with_retry,
                client,
                model,
                system_prompt,
                q,
                max_tokens,
                max_retries,
            ): i
            for i, q in enumerate(questions)
        }
        done = 0
        for fut in as_completed(futures):
            i = futures[fut]
            rec = fut.result()
            rec["answer_model"] = model
            results[i] = rec
            done += 1
            if on_progress:
                on_progress(done, len(questions))

    return results  # type: ignore[return-value]
