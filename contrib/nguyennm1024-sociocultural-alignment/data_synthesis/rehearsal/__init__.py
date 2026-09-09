"""Rehearsal data pipeline for Llama 3.2 3B Instruct preservation.

Three modules mirror the build flow:
    data/      — public dataset download, decontamination, extraction
    questions/ — per-category question pool (seed selection + augmentation +
                 fresh generation)
    answers/   — Kimi K2.6 solve pass; emits <THINK></THINK><ANSWER></ANSWER> records

Top-level helpers:
    spec.py    — load `topics/rehearsal/rehearsal_data_structure.json`; expose
                 the 13-category × 45-source registry
    format.py  — Record schema, THINK/ANSWER message helpers, JSONL I/O
    cli.py     — `python -m rehearsal.cli {download|decontam-build|...}`

See `README.md` for the full build order and resumability contract.
"""
