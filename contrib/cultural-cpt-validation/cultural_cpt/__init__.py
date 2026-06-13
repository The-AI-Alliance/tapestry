"""Harness for EXP-001: validating culturally grounded continued pretraining.

Smoke mode runs the full pipeline on a byte-level toy model (CI-scale, no
downloads/GPU); HF mode is the seam for a real base model. See
tech-docs/experiments/cultural-cpt-validation.md for the experiment design.
"""

from __future__ import annotations

from .experiment import (
    ArmResult,
    ExperimentConfig,
    ExperimentResult,
    run_experiment,
)
from .model import ByteCausalModel, HFCausalModel, LanguageModel, make_base_model
from .wvs import Coordinate, GROUND_TRUTH, SurveyResult, administer

__all__ = [
    "ArmResult",
    "ExperimentConfig",
    "ExperimentResult",
    "run_experiment",
    "LanguageModel",
    "ByteCausalModel",
    "HFCausalModel",
    "make_base_model",
    "Coordinate",
    "GROUND_TRUTH",
    "SurveyResult",
    "administer",
]
