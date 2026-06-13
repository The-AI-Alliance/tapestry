"""Multi-seed statistics and the pre-registered go/no-go decision.

A single run gives point estimates that are indistinguishable from noise. This
runs the experiment across several seeds and turns the per-arm shifts into
mean ± std, so the decisive comparisons become effect sizes with error bars.

It then evaluates the EXP-001 pre-registered threshold:

  PASS iff
    (1) grounded survey shift toward target  >=  min_grounded_shift   (absolute),
    (2) (grounded - language_matched) shift  >=  sigma_multiple * its std
        across seeds  (i.e. the grounding effect clears the noise band), and
    (3) capability drop from base to grounded <=  max_capability_drop.

The thresholds must be fixed *before* looking at results. They live in
``StatsConfig`` precisely so they can be set and version-controlled up front.
"""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field, replace

from .experiment import ExperimentConfig, ExperimentResult, run_experiment


@dataclass(frozen=True)
class StatsConfig:
    """Pre-registered multi-seed configuration. Set thresholds before running."""

    base: ExperimentConfig = field(default_factory=ExperimentConfig)
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    # --- pre-registered thresholds ---
    min_grounded_shift: float = 0.05  # X: minimum absolute move toward target
    sigma_multiple: float = 2.0  # effect must clear this many std devs
    max_capability_drop: float = 0.10  # Y: allowed capability degradation


@dataclass(frozen=True)
class ArmStats:
    """Aggregated measurements for one arm across seeds."""

    arm: str
    survey_shift_mean: float
    survey_shift_std: float
    behavior_shift_mean: float
    behavior_shift_std: float
    capability_mean: float


@dataclass(frozen=True)
class ComparisonStats:
    """A decisive comparison's effect size across seeds."""

    name: str
    mean: float
    std: float
    z: float  # mean / std — effect in std-dev units (how far it clears noise)


@dataclass(frozen=True)
class StatsResult:
    """Aggregated multi-seed result plus the go/no-go decision."""

    seeds: list[int]
    arms: list[ArmStats]
    comparisons: list[ComparisonStats]
    passed: bool
    verdict: str
    caveat: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _mean_std(xs: list[float]) -> tuple[float, float]:
    mean = statistics.fmean(xs) if xs else 0.0
    std = statistics.stdev(xs) if len(xs) >= 2 else 0.0
    return mean, std


def _zscore(mean: float, std: float) -> float:
    if std > 0:
        return mean / std
    return float("inf") if mean > 0 else (float("-inf") if mean < 0 else 0.0)


def run_multiseed(config: StatsConfig) -> StatsResult:
    """Run the experiment across seeds and decide PASS/FAIL on the threshold."""
    runs: list[ExperimentResult] = [
        run_experiment(replace(config.base, seed=s)) for s in config.seeds
    ]

    # Per-arm shift/capability samples across seeds.
    arm_names = [a.arm for a in runs[0].arms]
    survey_shift: dict[str, list[float]] = {n: [] for n in arm_names}
    behavior_shift: dict[str, list[float]] = {n: [] for n in arm_names}
    capability: dict[str, list[float]] = {n: [] for n in arm_names}
    for run in runs:
        for arm in run.arms:
            survey_shift[arm.arm].append(arm.shift_toward_target)
            behavior_shift[arm.arm].append(arm.behavior_shift_toward_target)
            capability[arm.arm].append(arm.capability_acc)

    arm_stats: list[ArmStats] = []
    for name in arm_names:
        s_mean, s_std = _mean_std(survey_shift[name])
        b_mean, b_std = _mean_std(behavior_shift[name])
        c_mean, _ = _mean_std(capability[name])
        arm_stats.append(ArmStats(name, s_mean, s_std, b_mean, b_std, c_mean))

    # Decisive comparisons as per-seed paired differences (grounded - other).
    comparisons: list[ComparisonStats] = []
    diff_samples: dict[str, list[float]] = {
        "grounded_vs_language": [r.decisive_grounded_vs_language for r in runs],
        "grounded_vs_translated": [r.decisive_grounded_vs_translated for r in runs],
        "grounded_vs_surface": [r.decisive_grounded_vs_surface for r in runs],
    }
    for cname, samples in diff_samples.items():
        mean, std = _mean_std(samples)
        comparisons.append(ComparisonStats(cname, mean, std, _zscore(mean, std)))

    # --- the pre-registered decision ---
    grounded = next(a for a in arm_stats if a.arm == "grounded")
    base_cap = next(a for a in arm_stats if a.arm == "base").capability_mean
    vs_language = next(c for c in comparisons if c.name == "grounded_vs_language")
    cap_drop = base_cap - grounded.capability_mean

    cond_shift = grounded.survey_shift_mean >= config.min_grounded_shift
    cond_effect = vs_language.mean > 0 and vs_language.z >= config.sigma_multiple
    cond_capability = cap_drop <= config.max_capability_drop
    passed = cond_shift and cond_effect and cond_capability

    verdict = (
        f"grounded shift {grounded.survey_shift_mean:+.3f} "
        f"(>= {config.min_grounded_shift}? {cond_shift}); "
        f"grounding effect z={vs_language.z:.2f} "
        f"(>= {config.sigma_multiple}? {cond_effect}); "
        f"capability drop {cap_drop:+.3f} "
        f"(<= {config.max_capability_drop}? {cond_capability})"
    )

    caveat = runs[0].smoke_caveat
    return StatsResult(
        seeds=list(config.seeds),
        arms=arm_stats,
        comparisons=comparisons,
        passed=passed,
        verdict=verdict,
        caveat=caveat,
    )
