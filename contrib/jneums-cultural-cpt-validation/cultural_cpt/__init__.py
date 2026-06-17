"""Harness for EXP-001: validating culturally grounded continued pretraining.

Smoke mode runs the full pipeline on a byte-level toy model (CI-scale, no
downloads/GPU); HF mode is the seam for a real base model. See
../SPEC.md for the experiment design.
"""

from __future__ import annotations

from .aggregation import (
    AggregationConfig,
    AggregationResult,
    RoundMetric,
    run_aggregation,
)
from .experiment import (
    ArmResult,
    ExperimentConfig,
    ExperimentResult,
    run_experiment,
)
from .behavior import administer_behavior
from .model import ByteCausalModel, HFCausalModel, LanguageModel, make_base_model
from .stats import (
    ArmStats,
    ComparisonStats,
    DrawSummary,
    ResampledResult,
    StatsConfig,
    StatsResult,
    run_corpus_resampled,
    run_multiseed,
)
from .wvs import Coordinate, GROUND_TRUTH, SurveyResult, administer, score_axes

__all__ = [
    "ArmResult",
    "ExperimentConfig",
    "ExperimentResult",
    "run_experiment",
    "AggregationConfig",
    "AggregationResult",
    "RoundMetric",
    "run_aggregation",
    "LanguageModel",
    "ByteCausalModel",
    "HFCausalModel",
    "make_base_model",
    "Coordinate",
    "GROUND_TRUTH",
    "SurveyResult",
    "administer",
    "administer_behavior",
    "score_axes",
    "StatsConfig",
    "StatsResult",
    "ArmStats",
    "ComparisonStats",
    "DrawSummary",
    "ResampledResult",
    "run_corpus_resampled",
    "run_multiseed",
]
