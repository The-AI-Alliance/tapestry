"""Read `topics/rehearsal/rehearsal_data_structure.json` and expose:
- category list (13 categories, ~40K target volume)
- per-source target volumes + category mapping
- decontamination test-set list

The spec JSON is the single source of truth for what data is needed and in
what volumes. HuggingFace paths and per-source filters live in
`rehearsal.data.sources` — joined to this registry by `source name`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator


DEFAULT_SPEC_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "topics"
    / "rehearsal"
    / "rehearsal_data_structure.json"
)


@dataclass(frozen=True)
class SourceSpec:
    """One row from a category's `sources` list."""

    name: str               # e.g. "MMLU_auxiliary_training", "Synthetic_via_Qwen"
    category: str           # e.g. "mmlu_shaped"
    volume: int             # target item count after decontamination
    description: str


@dataclass(frozen=True)
class CategorySpec:
    name: str
    volume: int
    target_benchmark: str
    sources: list[SourceSpec]


@lru_cache(maxsize=1)
def _load_raw(path_str: str | None = None) -> dict:
    path = Path(path_str) if path_str else DEFAULT_SPEC_PATH
    with open(path) as f:
        return json.load(f)


def load_spec(path: Path | str | None = None) -> dict:
    """Return the raw parsed spec JSON."""
    return _load_raw(str(path) if path else None)


def iter_categories(spec: dict | None = None) -> Iterator[CategorySpec]:
    """Yield one CategorySpec per category in the spec."""
    spec = spec if spec is not None else load_spec()
    for cat_name, cat in spec["categories"].items():
        sources = [
            SourceSpec(
                name=s["name"],
                category=cat_name,
                volume=s["volume"],
                description=s.get("description", ""),
            )
            for s in cat.get("sources", [])
        ]
        yield CategorySpec(
            name=cat_name,
            volume=cat["volume"],
            target_benchmark=cat.get("target_benchmark", ""),
            sources=sources,
        )


def iter_sources(spec: dict | None = None) -> Iterator[SourceSpec]:
    """Yield every SourceSpec across all categories. 45 entries totalling 40K."""
    for cat in iter_categories(spec):
        yield from cat.sources


def get_source(name: str, spec: dict | None = None) -> SourceSpec | None:
    """Lookup one source by name."""
    for s in iter_sources(spec):
        if s.name == name:
            return s
    return None


def get_category(name: str, spec: dict | None = None) -> CategorySpec | None:
    for c in iter_categories(spec):
        if c.name == name:
            return c
    return None


# Decontamination test-set names (free-form strings in the spec — bound to
# HuggingFace paths in `rehearsal.data.sources.DECONTAM_TESTSETS`).
def iter_decontam_testset_descriptions(spec: dict | None = None) -> list[str]:
    spec = spec if spec is not None else load_spec()
    return list(spec["decontamination_protocol"]["test_sets_to_check_against"])
