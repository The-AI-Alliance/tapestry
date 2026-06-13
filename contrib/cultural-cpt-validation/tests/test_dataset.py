"""Tests for the real-corpus loader and the EXP-001 scientific controls.

These assert that `dataset.py` *enforces* the controls the experiment's validity
depends on (permissive licensing, language/register/recency match, twin token
budget, WVS decontamination) and fails loudly when a corpus breaks one. They
also exercise the committed real seed corpus end to end.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cultural_cpt import dataset  # noqa: E402
from cultural_cpt.corpora import load_corpus  # noqa: E402

_SEED_ROOT = Path(__file__).resolve().parents[1] / "data" / "seed-example"


def _doc(**kw) -> dict:
    base = dict(
        id="d0",
        text="alpha beta gamma delta epsilon zeta eta theta",
        source="src",
        license="CC-BY-SA-4.0",
        lang="en",
        domain="law",
    )
    base.update(kw)
    return base


def _write_root(tmp_path: Path, *, grounded: list[dict], matched: list[dict], manifest: dict | None = None) -> Path:
    (tmp_path / "grounded.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in grounded), encoding="utf-8"
    )
    (tmp_path / "language_matched.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in matched), encoding="utf-8"
    )
    m = manifest or {
        "culture": "test",
        "language": "en",
        "arms": {
            "grounded": {"file": "grounded.jsonl", "lang": "en", "register": "encyclopedic", "value_laden": True},
            "language_matched": {
                "file": "language_matched.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": False,
            },
        },
        "twin_matching": {"token_ratio_tolerance": 0.20},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    return tmp_path


# --- the committed real seed corpus -----------------------------------------


def test_seed_corpus_passes_all_controls() -> None:
    assert _SEED_ROOT.is_dir(), "real seed corpus should be committed"
    for arm in ("grounded", "language_matched"):
        docs = dataset.load_arm_documents(_SEED_ROOT, arm)
        assert docs and all(d.text.strip() for d in docs)


def test_load_corpus_via_path_returns_documents() -> None:
    corpus = load_corpus("grounded", path=str(_SEED_ROOT))
    assert corpus.name == "grounded"
    assert len(corpus.documents) >= 1
    assert all(isinstance(t, str) and t for t in corpus.documents)


def test_declared_arms_reflects_manifest() -> None:
    assert dataset.declared_arms(_SEED_ROOT) == {"grounded", "language_matched"}


# --- licensing control -------------------------------------------------------


def test_non_permissive_license_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, grounded=[_doc(license="CC-BY-NC-4.0")], matched=[_doc(id="m0")])
    with pytest.raises(dataset.CorpusError, match="permissive"):
        dataset.load_arm_documents(root, "grounded")


# --- language control --------------------------------------------------------


def test_language_mismatch_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, grounded=[_doc(lang="fr")], matched=[_doc(id="m0")])
    with pytest.raises(dataset.CorpusError, match="lang"):
        dataset.load_arm_documents(root, "grounded")


# --- decontamination control -------------------------------------------------


def test_wvs_item_is_flagged_as_contamination() -> None:
    probes = dataset.wvs_probe_phrases()
    assert probes, "should harvest item phrasings from the live instruments"
    planted = dataset.DocumentRecord(
        id="leak",
        text="Survey question: " + probes[0] + " Please answer honestly.",
        source="s",
        license="CC-BY-4.0",
        lang="en",
    )
    flags = dataset.find_contamination([planted], probes)
    assert any(f.doc_id == "leak" for f in flags)


def test_contaminated_corpus_rejected_at_load(tmp_path: Path) -> None:
    leak = dataset.wvs_probe_phrases()[0]
    root = _write_root(
        tmp_path,
        grounded=[_doc(text=f"Background. {leak} More background text follows here.")],
        matched=[_doc(id="m0")],
    )
    with pytest.raises(dataset.CorpusError, match="memorization|WVS"):
        dataset.load_arm_documents(root, "grounded")


def test_clean_prose_is_not_contamination() -> None:
    docs = [
        dataset.DocumentRecord(
            id="ok",
            text="The river flooded the lowland fields after a week of heavy monsoon rain.",
            source="s",
            license="CC-BY-4.0",
            lang="en",
        )
    ]
    assert dataset.find_contamination(docs, dataset.wvs_probe_phrases()) == []


# --- matched-twin control ----------------------------------------------------


def test_twin_token_imbalance_rejected(tmp_path: Path) -> None:
    long_text = " ".join(["word"] * 200)
    root = _write_root(
        tmp_path, grounded=[_doc(text=long_text)], matched=[_doc(id="m0", text="short bit of text here now")]
    )
    with pytest.raises(dataset.CorpusError, match="token budget"):
        dataset.load_arm_documents(root, "grounded")


def test_twin_register_mismatch_rejected(tmp_path: Path) -> None:
    manifest = {
        "culture": "test",
        "language": "en",
        "arms": {
            "grounded": {"file": "grounded.jsonl", "lang": "en", "register": "legal", "value_laden": True},
            "language_matched": {
                "file": "language_matched.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": False,
            },
        },
    }
    root = _write_root(tmp_path, grounded=[_doc()], matched=[_doc(id="m0")], manifest=manifest)
    with pytest.raises(dataset.CorpusError, match="register"):
        dataset.load_arm_documents(root, "grounded")


def test_mislabeled_twin_value_ladenness_rejected(tmp_path: Path) -> None:
    manifest = {
        "culture": "test",
        "language": "en",
        "arms": {
            "grounded": {"file": "grounded.jsonl", "lang": "en", "register": "encyclopedic", "value_laden": False},
            "language_matched": {
                "file": "language_matched.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": False,
            },
        },
    }
    root = _write_root(tmp_path, grounded=[_doc()], matched=[_doc(id="m0")], manifest=manifest)
    with pytest.raises(dataset.CorpusError, match="value_laden"):
        dataset.load_arm_documents(root, "grounded")


def test_twin_check_can_be_disabled(tmp_path: Path) -> None:
    long_text = " ".join(["word"] * 200)
    root = _write_root(tmp_path, grounded=[_doc(text=long_text)], matched=[_doc(id="m0", text="short")])
    # per-arm validation still runs; twin balance does not
    docs = dataset.load_arm_documents(root, "grounded", check_twin=False)
    assert len(docs) == 1


# --- schema / manifest errors ------------------------------------------------


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    bad = {"id": "x", "source": "s", "license": "CC-BY-4.0", "lang": "en"}  # no text
    root = _write_root(tmp_path, grounded=[bad], matched=[_doc(id="m0")])
    with pytest.raises(dataset.CorpusError, match="missing required"):
        dataset.load_arm_documents(root, "grounded")


def test_unknown_arm_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, grounded=[_doc()], matched=[_doc(id="m0")])
    with pytest.raises(dataset.CorpusError, match="not in manifest"):
        dataset.load_arm_documents(root, "grounded_translated")


def test_recency_out_of_window_rejected(tmp_path: Path) -> None:
    manifest = {
        "culture": "test",
        "language": "en",
        "arms": {
            "grounded": {
                "file": "grounded.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": True,
                "max_year": 2020,
            },
            "language_matched": {
                "file": "language_matched.jsonl",
                "lang": "en",
                "register": "encyclopedic",
                "value_laden": False,
            },
        },
    }
    root = _write_root(tmp_path, grounded=[_doc(year=2030)], matched=[_doc(id="m0")], manifest=manifest)
    with pytest.raises(dataset.CorpusError, match="year"):
        dataset.load_arm_documents(root, "grounded")
