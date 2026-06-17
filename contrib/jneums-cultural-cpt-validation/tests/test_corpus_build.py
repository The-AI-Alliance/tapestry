"""Tests for the corpus assembler's Arm-3 (grounded_translated) machinery.

These cover the pieces that do not need a network or an MT model: sentence
chunking for translation, the manifest gaining the translated arm, and the
loader accepting a three-arm root (English Arm 3 exempt from the twin control).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_corpus  # noqa: E402
from cultural_cpt import dataset  # noqa: E402


def test_chunk_for_mt_respects_word_budget_and_sentences() -> None:
    text = "First sentence here. Second one follows. Third and last sentence ends it."
    chunks = fetch_corpus._chunk_for_mt(text, max_words=5)
    assert len(chunks) >= 2  # the 12 words don't fit one 5-word chunk
    # no words are dropped (punctuation stays attached via the look-behind split)
    assert " ".join(chunks).split() == text.split()


def test_chunk_for_mt_handles_arabic_punctuation() -> None:
    text = "هذه جملة أولى؟ وهذه جملة ثانية. ثم جملة ثالثة."
    chunks = fetch_corpus._chunk_for_mt(text, max_words=3)
    assert len(chunks) >= 2  # split on ؟ and .


def _doc(**kw) -> dict:
    base = dict(id="d0", text="alpha beta gamma delta epsilon zeta", source="s", license="CC-BY-SA-4.0", lang="ar")
    base.update(kw)
    return base


def test_manifest_declares_translated_arm(tmp_path: Path) -> None:
    titles = {"grounded": {"law": []}, "language_matched": {"weather": []}}
    fetch_corpus._write_manifest(tmp_path, "egypt", "ar", 0.20, titles, with_translated=True)
    manifest = dataset.CorpusManifest.load(tmp_path)
    assert "grounded_translated" in manifest.arms
    gt = manifest.arms["grounded_translated"]
    assert gt.lang == "en" and gt.value_laden is True


def test_three_arm_root_loads_translated(tmp_path: Path) -> None:
    """A root with an English grounded_translated arm validates: it is exempt
    from the twin control (different language + length) but still license/lang/
    decontamination checked."""
    grounded = [_doc(id="g0", text=" ".join(["مرحبا"] * 30))]
    matched = [_doc(id="m0", text=" ".join(["طقس"] * 30))]
    translated = [_doc(id="g0:en", lang="en", text=" ".join(["hello"] * 30))]
    for name, docs in (("grounded", grounded), ("language_matched", matched), ("grounded_translated", translated)):
        (tmp_path / f"{name}.jsonl").write_text(
            "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in docs), encoding="utf-8"
        )
    manifest = {
        "culture": "egypt",
        "language": "ar",
        "arms": {
            "grounded": {"file": "grounded.jsonl", "lang": "ar", "register": "encyclopedic", "value_laden": True},
            "language_matched": {
                "file": "language_matched.jsonl",
                "lang": "ar",
                "register": "encyclopedic",
                "value_laden": False,
            },
            "grounded_translated": {
                "file": "grounded_translated.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": True,
            },
        },
        "twin_matching": {"token_ratio_tolerance": 0.20},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    assert dataset.declared_arms(tmp_path) == {"grounded", "language_matched", "grounded_translated"}
    docs = dataset.load_arm_documents(tmp_path, "grounded_translated")
    assert len(docs) == 1 and docs[0].lang == "en"
