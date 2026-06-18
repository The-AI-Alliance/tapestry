"""Append-only JSONL storage helpers.

Used by the resumable pipeline runners. JSONL is the source of truth for
pipeline state — readers tolerate a truncated final line (from a crash
mid-write) by skipping it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator


def append_records(path: Path | str, records: Iterable[dict[str, Any]]) -> int:
    """Append records as JSONL lines. Flushes after each line so a Ctrl-C
    loses at most the in-flight record. Returns the count written.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(p, "a") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
    return n


def read_records(path: Path | str) -> Iterator[dict[str, Any]]:
    """Read JSONL records. Tolerates a truncated final line (likely the
    record that was in flight when the process was killed)."""
    p = Path(path)
    if not p.exists():
        return
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
