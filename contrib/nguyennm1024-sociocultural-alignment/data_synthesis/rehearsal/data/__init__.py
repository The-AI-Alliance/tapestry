"""Module 1 — data acquisition.

`sources.py`   — HFSource and DecontamTestset registries (45 + 20 entries).
`download.py`  — populate the HF cache for all sources / decontam testsets.
`decontam.py`  — exact + 13-gram filter against the indexed test sets.
`extract.py`   — normalize cached HF rows to {id, category, source, question,
                 gold_answer, metadata} records used by the answers/ module.
"""
from .sources import SOURCES, SOURCES_BY_NAME, DECONTAM_TESTSETS, DECONTAM_BY_NAME

__all__ = ["SOURCES", "SOURCES_BY_NAME", "DECONTAM_TESTSETS", "DECONTAM_BY_NAME"]
