"""Shared evaluation API.

Score ANY model -- a trained member from ``training/`` or a fused model from
``consortium/`` -- on capability (full-set MMLU) and cultural alignment (the
Inglehart-Welzel cultural map). Both parts call ``evaluate()`` identically, so a
member and a combined model are judged the same way. This module owns the report
contract; the suites themselves live in:

  - ``evaluation/zs_full_mmlu.py``           full 14042-item MMLU (zero-shot)
  - ``evaluation/iw/iw_gen_tao.py`` + ``iw_project.py``  IW projection

NOTE: the suites are GPU/vLLM jobs that currently assume the Docker mount
(``/workspace``). Wiring ``_run_mmlu`` / ``_run_iw`` to dispatch them (in-process or
via the eval image) is the path-portability follow-up; the contract below is stable.
"""
from dataclasses import dataclass, field
from typing import Optional

SUITES = ("mmlu", "iw")


@dataclass
class EvalReport:
    model: str
    mmlu_acc: Optional[float] = None        # full-set MMLU accuracy (%)
    iw_distance: Optional[float] = None      # Euclidean distance to the target country
    iw_items: dict = field(default_factory=dict)   # per-WVS-item means
    extra: dict = field(default_factory=dict)


def evaluate(model_path: str, tag: str, suites=SUITES, target: str = "Vietnam") -> EvalReport:
    """Run the requested suites on ``model_path`` and return a structured report."""
    report = EvalReport(model=model_path)
    if "mmlu" in suites:
        report.mmlu_acc = _run_mmlu(model_path, tag)
    if "iw" in suites:
        report.iw_distance, report.iw_items = _run_iw(model_path, tag, target)
    return report


def _run_mmlu(model_path: str, tag: str) -> float:
    """Full-set MMLU via evaluation/zs_full_mmlu.py (vLLM). Returns accuracy (%)."""
    raise NotImplementedError(
        "Wire to evaluation/zs_full_mmlu.py (Docker/vLLM); see the path-portability follow-up."
    )


def _run_iw(model_path: str, tag: str, target: str = "Vietnam"):
    """IW projection via evaluation/iw/ (iw_gen_tao + iw_project). Returns (distance, item means)."""
    raise NotImplementedError(
        "Wire to evaluation/iw/ (Docker/vLLM); see the path-portability follow-up."
    )
