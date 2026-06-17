"""Aggregation-survival experiment: do cultures stay separable under FedAvg?

This is the Tapestry-unique question (and open question T3, non-IID
convergence). The single-arm experiment in ``experiment.py`` asks whether *one*
node's grounded CPT shifts its coordinate. This asks what happens when *many*
culturally distinct nodes are repeatedly averaged together, the way the
consortium training loop (TAP-004) does.

Per round, every node:
  1. loads the current shared global base,
  2. does local grounded CPT on its own culture's corpus (the sovereign fork),
  3. is **measured** on the Inglehart-Welzel map (this is the deployable model),
then all forks are FedAvg-averaged into the next global base.

The artifact to watch is the **separability curve**: mean pairwise distance
between node coordinates over rounds. If it shrinks, repeated averaging is
homogenizing the cultures toward the centroid (the drift failure mode); if it
holds, distinct cultural alignment survives the loop.

Smoke mode runs this on the byte-level toy model — plumbing only, numbers are
noise. See ../SPEC.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

import torch

from . import wvs
from .corpora import load_culture_corpus
from .model import ByteCausalModel, LanguageModel, make_base_model


@dataclass(frozen=True)
class NodeCoordinate:
    """One node's measured position in one round."""

    culture: str
    ts: float
    ss: float
    distance_to_own_target: float


@dataclass(frozen=True)
class RoundMetric:
    """Separability metrics for one consortium round."""

    round_num: int
    nodes: list[NodeCoordinate]
    mean_pairwise_distance: float  # separability; lower = more homogenized
    centroid_ts: float
    centroid_ss: float
    mean_distance_to_centroid: float


@dataclass(frozen=True)
class AggregationResult:
    """Full result: the separability curve across rounds."""

    mode: str
    cultures: list[str]
    seed: int
    rounds: list[RoundMetric]
    separability_curve: list[float]
    smoke_caveat: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AggregationConfig:
    """Configuration for the aggregation-survival experiment."""

    mode: str = "smoke"
    cultures: tuple[str, ...] = ("vietnam", "sweden", "usa")
    rounds: int = 4
    epochs: int = 3
    lr: float = 0.01
    hidden_size: int = 64
    seed: int = 0
    paraphrase_passes: int = 2
    model_name: str = ""
    corpus_path: str = ""  # empty = placeholder corpora; else per-culture real data root


def _fedavg(states: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    """Uniform FedAvg of weight vectors (mirrors ConsortiumCoordinator)."""
    keys = states[0].keys()
    n = len(states)
    return {k: sum((s[k] for s in states), torch.zeros_like(states[0][k])) / n for k in keys}


def _measure(model: LanguageModel, culture: str, *, seed: int, passes: int) -> NodeCoordinate:
    survey = wvs.administer(model, seed=seed, paraphrase_passes=passes)
    target = wvs.GROUND_TRUTH[culture]
    return NodeCoordinate(
        culture=culture,
        ts=survey.coordinate.ts,
        ss=survey.coordinate.ss,
        distance_to_own_target=survey.coordinate.distance_to(target),
    )


def run_aggregation(config: AggregationConfig) -> AggregationResult:
    """Run the multi-node FedAvg loop and return the separability curve."""
    if config.mode != "smoke":
        raise NotImplementedError(
            "aggregation experiment currently supports smoke mode only; the real "
            "version reuses the HF backend per node and is round-two work."
        )
    unknown = [c for c in config.cultures if c not in wvs.GROUND_TRUTH]
    if unknown:
        raise ValueError(f"no ground-truth coordinate for cultures {unknown}")
    if len(config.cultures) < 2:
        raise ValueError("aggregation needs at least 2 cultures")

    base = make_base_model(config.mode, hidden_size=config.hidden_size, seed=config.seed)
    global_state = base.clone().state() if isinstance(base, ByteCausalModel) else None
    if global_state is None:  # pragma: no cover - smoke only
        raise RuntimeError("smoke mode expected a ByteCausalModel base")

    corpora = {c: load_culture_corpus(c, path=config.corpus_path) for c in config.cultures}

    round_metrics: list[RoundMetric] = []
    for round_num in range(1, config.rounds + 1):
        forks: list[ByteCausalModel] = []
        coords: list[NodeCoordinate] = []
        for culture in config.cultures:
            node = base.clone()
            assert isinstance(node, ByteCausalModel)
            node.load_state(global_state)  # start from current global base
            node.train_on_texts(list(corpora[culture].documents), epochs=config.epochs, lr=config.lr)
            coords.append(_measure(node, culture, seed=config.seed, passes=config.paraphrase_passes))
            forks.append(node)

        # FedAvg the sovereign forks into the next global base.
        global_state = _fedavg([f.state() for f in forks])

        pairwise = [
            ((a.ts - b.ts) ** 2 + (a.ss - b.ss) ** 2) ** 0.5
            for a, b in combinations(coords, 2)
        ]
        mean_pairwise = sum(pairwise) / len(pairwise)
        cx = sum(c.ts for c in coords) / len(coords)
        cy = sum(c.ss for c in coords) / len(coords)
        mean_to_centroid = sum(((c.ts - cx) ** 2 + (c.ss - cy) ** 2) ** 0.5 for c in coords) / len(coords)

        round_metrics.append(
            RoundMetric(
                round_num=round_num,
                nodes=coords,
                mean_pairwise_distance=mean_pairwise,
                centroid_ts=cx,
                centroid_ss=cy,
                mean_distance_to_centroid=mean_to_centroid,
            )
        )

    caveat = (
        "SMOKE MODE: byte-level toy model. The separability curve is NOISE and carries "
        "no claim; this validates the multi-node FedAvg-and-measure pipeline, not the "
        "hypothesis."
        if config.mode == "smoke"
        else ""
    )
    return AggregationResult(
        mode=config.mode,
        cultures=list(config.cultures),
        seed=config.seed,
        rounds=round_metrics,
        separability_curve=[m.mean_pairwise_distance for m in round_metrics],
        smoke_caveat=caveat,
    )
