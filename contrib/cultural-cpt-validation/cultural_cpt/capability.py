"""Capability guardrail probe.

A tiny multiple-choice accuracy check so the harness can detect whether CPT
lobotomized the model. Illustrative items only; a real run swaps in MMLU (and a
target-language equivalent) via lm-evaluation-harness.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import LanguageModel


@dataclass(frozen=True)
class MCQ:
    """A multiple-choice question with the index of the correct option."""

    question: str
    options: tuple[str, ...]
    answer_index: int


_PROBE: tuple[MCQ, ...] = (
    MCQ("The capital of France is", ("Paris", "Berlin", "Madrid"), 0),
    MCQ("Two plus three equals", ("four", "five", "six"), 1),
    MCQ("Water is made of hydrogen and", ("oxygen", "nitrogen", "carbon"), 0),
    MCQ("The opposite of hot is", ("cold", "loud", "tall"), 0),
)


def evaluate(model: LanguageModel) -> float:
    """Return multiple-choice accuracy in [0, 1] via log-prob answer selection."""
    correct = 0
    for item in _PROBE:
        scored = [model.score_continuation(item.question + " ", opt) for opt in item.options]
        chosen = max(range(len(scored)), key=lambda i: scored[i])
        correct += int(chosen == item.answer_index)
    return correct / len(_PROBE)
