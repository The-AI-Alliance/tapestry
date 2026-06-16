"""Load a topic/scenario JSON spec and iterate its scenarios.

Spec shape: a top-level dict that either contains `topics` directly, or
contains one or more `part_*` keys each holding their own `topics` dict.
Each topic has `description` and a `scenarios` list. Each scenario has
`name`, `description`, `volume`, and optional extras.

See `topics/cultural_data_coverage_v2.json` for the cultural-alignment
example. Other domain packages define their own JSON with the same shape.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def load_spec(path: Path | str) -> dict[str, Any]:
    """Read a topic/scenario JSON spec."""
    with open(path) as f:
        return json.load(f)


def _iter_topics(spec: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
    """Yield (part_label, topic_id, topic_dict). Supports flat or part-based specs."""
    if "topics" in spec:
        for tid, t in spec["topics"].items():
            yield "single", tid, t
        return
    for key, val in spec.items():
        if isinstance(val, dict) and "topics" in val:
            part_label = "part_" + key.split("_")[1] if key.startswith("part_") else key
            for tid, t in val["topics"].items():
                yield part_label, tid, t


def iter_scenarios(spec: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield one flattened record per scenario across all topics in the spec."""
    for part, topic_id, topic in _iter_topics(spec):
        for scn in topic.get("scenarios", []):
            yield {
                "topic_id": topic_id,
                "topic_description": topic.get("description", ""),
                "scenario_id": scn["name"],
                "scenario_description": scn["description"],
                "volume": scn.get("volume", 0),
                "part": part,
                "native_review_priority": topic.get("native_review_priority"),
                "handling_note": topic.get("handling_note"),
            }


def get_scenario(scenario_id: str, spec: dict[str, Any]) -> dict[str, Any] | None:
    for s in iter_scenarios(spec):
        if s["scenario_id"] == scenario_id:
            return s
    return None
