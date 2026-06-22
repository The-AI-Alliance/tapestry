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

Two backends, one loop. ``mode="smoke"`` runs the byte-level toy model
(plumbing only, numbers are noise); ``mode="hf"`` runs a real Hugging Face base
per node -- the same FedAvg-and-measure pipeline, where the actual T3 signal
comes from. Nodes are trained and measured one at a time and only their CPU
weight vectors are kept, so N full forks never coexist in VRAM. See ../SPEC.md.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

import torch

from . import wvs
from .corpora import load_culture_corpus
from .model import LanguageModel, make_base_model


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

    mode: str = "smoke"  # model backend: "smoke" | "hf"
    cultures: tuple[str, ...] = ("vietnam", "sweden", "usa")
    rounds: int = 4
    epochs: int = 3
    lr: float = 0.01
    hidden_size: int = 64
    seed: int = 0
    paraphrase_passes: int = 2
    model_name: str = ""  # hf mode: the base model id all nodes start from
    device: str = "cpu"  # hf mode: "cpu" | "cuda"
    dtype: str = "float32"  # hf mode: "float32" | "bfloat16" (bf16 halves CPT memory)
    instrument_lang: str = "en"  # survey language for every node (en = shared instrument)
    corpus_path: str = ""  # empty = placeholder corpora; else per-culture real data root
    # Training stabilization (HF backend only), same knobs the single-arm run uses.
    warmup_frac: float = 0.0
    max_grad_norm: float | None = None


def _fedavg(states: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    """Uniform FedAvg of weight vectors (mirrors ConsortiumCoordinator).

    Only floating-point tensors are averaged; integer buffers (token/position
    ids and similar non-trainable state a real HF model carries) are taken from
    the first fork unchanged -- averaging them is meaningless and would corrupt
    the dtype. The toy backend has only float params, so its behavior (and the
    determinism tests) are unaffected.
    """
    keys = states[0].keys()
    n = len(states)
    out: dict[str, torch.Tensor] = {}
    for k in keys:
        t0 = states[0][k]
        if t0.is_floating_point():
            out[k] = sum((s[k] for s in states), torch.zeros_like(t0)) / n
        else:
            out[k] = t0.clone()
    return out


def _measure(model: LanguageModel, culture: str, *, seed: int, passes: int, lang: str = "en") -> NodeCoordinate:
    survey = wvs.administer(model, seed=seed, paraphrase_passes=passes, lang=lang)
    target = wvs.GROUND_TRUTH[culture]
    return NodeCoordinate(
        culture=culture,
        ts=survey.coordinate.ts,
        ss=survey.coordinate.ss,
        distance_to_own_target=survey.coordinate.distance_to(target),
    )


def _round_metric(round_num: int, coords: list[NodeCoordinate]) -> RoundMetric:
    """Separability + centroid metrics for one round's measured coordinates."""
    pairwise = [
        ((a.ts - b.ts) ** 2 + (a.ss - b.ss) ** 2) ** 0.5 for a, b in combinations(coords, 2)
    ]
    mean_pairwise = sum(pairwise) / len(pairwise)
    cx = sum(c.ts for c in coords) / len(coords)
    cy = sum(c.ss for c in coords) / len(coords)
    mean_to_centroid = sum(((c.ts - cx) ** 2 + (c.ss - cy) ** 2) ** 0.5 for c in coords) / len(coords)
    return RoundMetric(
        round_num=round_num,
        nodes=coords,
        mean_pairwise_distance=mean_pairwise,
        centroid_ts=cx,
        centroid_ss=cy,
        mean_distance_to_centroid=mean_to_centroid,
    )


def _round_metric_from_dict(d: dict) -> RoundMetric:
    nodes = [NodeCoordinate(**n) for n in d["nodes"]]
    return RoundMetric(
        round_num=d["round_num"],
        nodes=nodes,
        mean_pairwise_distance=d["mean_pairwise_distance"],
        centroid_ts=d["centroid_ts"],
        centroid_ss=d["centroid_ss"],
        mean_distance_to_centroid=d["mean_distance_to_centroid"],
    )


def _save_checkpoint(cache_dir: Path, round_num: int, global_state: dict, metric: RoundMetric) -> None:
    """Persist a round so a preempted multi-round HF sweep resumes for free.

    The averaged global weights are the source of truth for how far we got
    (``after_round``); the per-round metric JSON is tiny and written first. The
    weight blob is written to a temp file and renamed so an interrupted write
    never leaves a half-written checkpoint -- the run just redoes that round.
    """
    (cache_dir / f"round_{round_num}.json").write_text(json.dumps(asdict(metric), indent=2, sort_keys=True) + "\n")
    tmp = cache_dir / "global_state.pt.tmp"
    torch.save({"after_round": round_num, "state": global_state}, tmp)
    tmp.replace(cache_dir / "global_state.pt")


def _load_checkpoint(cache_dir: Path):
    """Return ``(after_round, global_state, metrics)`` to resume, or ``None``."""
    state_file = cache_dir / "global_state.pt"
    if not state_file.exists():
        return None
    ckpt = torch.load(state_file, map_location="cpu")
    after_round = int(ckpt["after_round"])
    metrics: list[RoundMetric] = []
    for n in range(1, after_round + 1):
        metric_file = cache_dir / f"round_{n}.json"
        if not metric_file.exists():  # weights claim a round the metrics don't back; start clean
            return None
        metrics.append(_round_metric_from_dict(json.loads(metric_file.read_text())))
    return after_round, ckpt["state"], metrics


def _caveat(config: AggregationConfig) -> str:
    flags = []
    if config.mode == "smoke":
        flags.append("byte-level toy model")
    if not config.corpus_path:
        flags.append("placeholder per-culture corpora (illustrative text, not real grounded data)")
    if not flags:
        return ""
    return (
        "NOT A RESULT — " + "; ".join(flags) + ". The separability curve carries no claim; this "
        "validates the multi-node FedAvg-and-measure pipeline, not the hypothesis. Real T3 signal "
        "needs mode='hf' AND corpus_path with real per-culture grounded corpora."
    )


def run_aggregation(config: AggregationConfig, *, on_round=None, cache_dir=None) -> AggregationResult:
    """Run the multi-node FedAvg loop and return the separability curve.

    ``cache_dir`` (optional) checkpoints each round's averaged weights + metrics
    so an interrupted run resumes where it left off -- only unfinished rounds
    cost GPU. ``on_round`` is an optional callback invoked with each completed
    :class:`RoundMetric` for live progress.
    """
    unknown = [c for c in config.cultures if c not in wvs.GROUND_TRUTH]
    if unknown:
        raise ValueError(f"no ground-truth coordinate for cultures {unknown}")
    if len(config.cultures) < 2:
        raise ValueError("aggregation needs at least 2 cultures")

    base = make_base_model(
        config.mode,
        hidden_size=config.hidden_size,
        seed=config.seed,
        model_name=config.model_name,
        device=config.device,
        dtype=config.dtype,
    )
    corpora = {c: load_culture_corpus(c, path=config.corpus_path) for c in config.cultures}

    round_metrics: list[RoundMetric] = []
    global_state: dict | None = None
    start_round = 1
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        resumed = _load_checkpoint(cache_dir)
        if resumed is not None:
            after_round, global_state, round_metrics = resumed
            start_round = after_round + 1

    if global_state is None:
        global_state = base.state()

    for round_num in range(start_round, config.rounds + 1):
        fork_states: list[dict[str, torch.Tensor]] = []
        coords: list[NodeCoordinate] = []
        for culture in config.cultures:
            node = base.clone()  # fresh copy of the original base on the compute device
            node.load_state(global_state)  # start from the current shared global base
            node.train_on_texts(
                list(corpora[culture].documents),
                epochs=config.epochs,
                lr=config.lr,
                warmup_frac=config.warmup_frac,
                max_grad_norm=config.max_grad_norm,
                shuffle_seed=config.seed,
            )
            coords.append(
                _measure(node, culture, seed=config.seed, passes=config.paraphrase_passes, lang=config.instrument_lang)
            )
            fork_states.append(node.state())  # CPU weight vector; the GPU copy is then freed
            del node

        # FedAvg the sovereign forks into the next global base.
        global_state = _fedavg(fork_states)
        del fork_states

        metric = _round_metric(round_num, coords)
        round_metrics.append(metric)
        if cache_dir is not None:
            _save_checkpoint(cache_dir, round_num, global_state, metric)
        if on_round is not None:
            on_round(metric)

    round_metrics = round_metrics[: config.rounds]
    return AggregationResult(
        mode=config.mode,
        cultures=list(config.cultures),
        seed=config.seed,
        rounds=round_metrics,
        separability_curve=[m.mean_pairwise_distance for m in round_metrics],
        smoke_caveat=_caveat(config),
    )
