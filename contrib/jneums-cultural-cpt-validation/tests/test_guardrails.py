"""Tests for the capability and safety guardrails.

These assert the probes are well-formed (valid answer keys, bilingual coverage,
score in range) — not any particular model behavior, which on the toy model is
noise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import capability, safety  # noqa: E402
from cultural_cpt.model import ByteCausalModel  # noqa: E402


def test_capability_banks_well_formed() -> None:
    for lang, bank in capability._BANK.items():
        assert len(bank) >= 12, f"{lang} capability bank too small to be meaningful"
        for item in bank:
            assert len(item.options) >= 2
            assert 0 <= item.answer_index < len(item.options)
            assert len(set(item.options)) == len(item.options), f"duplicate option in {item.question!r}"


def test_capability_correct_index_varies() -> None:
    # A probe whose answer is always option 0 is gamed by position bias, not knowledge.
    for bank in capability._BANK.values():
        assert len({item.answer_index for item in bank}) >= 3


def test_capability_evaluate_in_range() -> None:
    model = ByteCausalModel(hidden_size=32, seed=0)
    for lang in ("en", "ar"):
        acc = capability.evaluate(model, lang=lang)
        assert 0.0 <= acc <= 1.0
    # Unlocalized language falls back to the English bank rather than crashing.
    assert 0.0 <= capability.evaluate(model, lang="vi") <= 1.0


def test_safety_probe_well_formed() -> None:
    for probe in safety._PROBE_BANK.values():
        assert len(probe) >= 4
        for item in probe:
            assert item.request and item.refusal and item.compliance
            assert item.refusal != item.compliance


def test_safety_evaluate_in_range() -> None:
    model = ByteCausalModel(hidden_size=32, seed=0)
    for lang in ("en", "ar", "vi"):
        rate = safety.evaluate_refusal(model, lang=lang)
        assert 0.0 <= rate <= 1.0


def test_coerce_answer_index() -> None:
    assert capability._coerce_answer_index(2, 4) == 2
    assert capability._coerce_answer_index("B", 4) == 1
    assert capability._coerce_answer_index("3", 4) == 3
    assert capability._coerce_answer_index("Z", 4) is None
    assert capability._coerce_answer_index(9, 4) is None
