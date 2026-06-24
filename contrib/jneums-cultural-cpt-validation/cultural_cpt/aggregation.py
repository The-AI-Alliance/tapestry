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

Alongside the coordinate curve we log **weight-space merge diagnostics** on the
per-fork update deltas, because a shrinking separability curve has two very
different causes and the coordinates alone cannot tell them apart:

  - *cultural homogenization* — averaging coherently pulls the cultures' values
    together (the updates agree in direction; the merge keeps them);
  - *representational interference* — the independently continued-pretrained forks
    drift into incompatible weight spaces, so FedAvg averages conflicting updates
    that **cancel**, degrading the model regardless of any cultural averaging.
    This is the failure "On the Limits of Model Merging for Multilinguality in
    Pre-Training" (arXiv:2605.25846) predicts for merging *pre-trained* (not
    fine-tuned) models — exactly our regime. See LITERATURE.md §6.

The diagnostics (per round, over the forks' deltas vs. the round's starting base):
``mean_update_cosine`` (pairwise cosine of update directions; →1 aligned, ≤0
conflicting), ``update_sign_agreement`` (TIES-style: fraction of an update's
sign that survives across forks; 1 = unanimous, 0 = balanced sign-conflict), and
``retained_update_ratio`` (‖mean Δ‖ / mean‖Δ‖; how much update magnitude survives
the average — →1 reinforcing, →0 cancelling). Collapse with high cosine/retention
reads as genuine homogenization; collapse with low cosine/retention + sign-conflict
reads as merge interference.

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
    """One node's measured position in one round.

    ``ts``/``ss`` are the node's absolute Inglehart-Welzel coordinate measured in
    ``lang`` (the node's OWN corpus language -- aggregation v1 measured every node
    on a shared English instrument, which muted the foreign-language CPT so the
    nodes never separated; Runs 3-4 showed in-language measurement is what surfaces
    the shift). ``shift_ts``/``shift_ss`` are the movement vs. the round's shared
    global base measured in the SAME language, so the per-language calibration
    offset cancels and the shifts are comparable across nodes.
    """

    culture: str
    ts: float
    ss: float
    distance_to_own_target: float
    lang: str = "en"
    shift_ts: float = 0.0
    shift_ss: float = 0.0


@dataclass(frozen=True)
class RoundMetric:
    """Separability metrics for one consortium round.

    ``mean_pairwise_distance`` is the **shift-space** separability (mean pairwise
    distance between nodes' shift vectors) -- the calibration-robust signal for
    whether the cultures pull in distinct directions. ``abs_pairwise_distance`` is
    the same on absolute in-language coordinates, kept for context. The centroid
    metrics are on the absolute coordinates.
    """

    round_num: int
    nodes: list[NodeCoordinate]
    mean_pairwise_distance: float  # SHIFT-space separability; lower = more homogenized
    centroid_ts: float
    centroid_ss: float
    mean_distance_to_centroid: float
    abs_pairwise_distance: float = 0.0  # separability on absolute coords (context)
    # Weight-space merge diagnostics on this round's fork updates (the
    # representational-interference companion to the coordinate separability
    # above). See _merge_diagnostics and the module docstring. Default 0.0 so
    # coordinate-only construction (and pre-diagnostic checkpoints) still loads.
    mean_update_cosine: float = 0.0
    update_sign_agreement: float = 0.0
    retained_update_ratio: float = 0.0


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


def _merge_diagnostics(
    global_start: dict[str, torch.Tensor], fork_states: list[dict[str, torch.Tensor]]
) -> tuple[float, float, float]:
    """Weight-space interference diagnostics for one round's FedAvg.

    Operates on each fork's update delta ``Δ_i = fork_i − global_start`` (the
    base every fork loaded this round). Returns
    ``(mean_update_cosine, update_sign_agreement, retained_update_ratio)`` — see
    the module docstring for how to read them. All sums are accumulated
    tensor-by-tensor in float32 so only one parameter's worth of deltas is held
    at a time: a 4B merge never materializes a flat copy of the whole model.
    """
    n = len(fork_states)
    keys = [k for k, v in global_start.items() if v.is_floating_point()]
    sq = [0.0] * n  # ‖Δ_i‖²
    dot = {(i, j): 0.0 for i, j in combinations(range(n), 2)}  # Δ_i · Δ_j
    sign_sum, sign_cnt = 0.0, 0
    for k in keys:
        g = global_start[k].to(torch.float32)
        deltas = [fs[k].to(torch.float32) - g for fs in fork_states]
        for i in range(n):
            sq[i] += float(deltas[i].pow(2).sum())
        for i, j in dot:
            dot[(i, j)] += float((deltas[i] * deltas[j]).sum())
        # Per-element fraction of sign that survives across forks (TIES sign vote):
        # |Σ sign(Δ_i)| / n is 1.0 when all forks agree, 0.0 at a balanced conflict.
        signs = torch.stack([torch.sign(d) for d in deltas])
        agree = signs.sum(dim=0).abs() / n
        sign_sum += float(agree.sum())
        sign_cnt += agree.numel()

    norms = [s**0.5 for s in sq]
    cosines = [dot[(i, j)] / (norms[i] * norms[j]) if norms[i] > 0 and norms[j] > 0 else 0.0 for i, j in dot]
    mean_cosine = sum(cosines) / len(cosines) if cosines else 0.0
    mean_norm = sum(norms) / n
    # ‖mean Δ‖² = ‖Σ Δ_i‖² / n² = (Σ‖Δ_i‖² + 2 Σ_{i<j} Δ_i·Δ_j) / n², from the
    # norms and dot products already accumulated -- no per-tensor mean to build.
    mean_delta_sq = (sum(sq) + 2.0 * sum(dot.values())) / (n * n)
    retained = (max(mean_delta_sq, 0.0) ** 0.5) / mean_norm if mean_norm > 0 else 0.0
    sign_agreement = sign_sum / sign_cnt if sign_cnt else 0.0
    return mean_cosine, sign_agreement, retained


def _coord(model: LanguageModel, *, seed: int, passes: int, lang: str) -> wvs.Coordinate:
    """The model's raw IW coordinate measured in ``lang`` (no target attached)."""
    return wvs.administer(model, seed=seed, paraphrase_passes=passes, lang=lang).coordinate


def _measure(
    model: LanguageModel, culture: str, *, seed: int, passes: int, lang: str, base_coord: wvs.Coordinate
) -> NodeCoordinate:
    """Measure a node in its OWN language and record its shift vs the round's base.

    ``base_coord`` is the shared global base measured in the SAME ``lang``; the
    shift (node - base) cancels the per-language calibration offset so shifts are
    comparable across nodes even though the absolute coordinates are not."""
    coord = _coord(model, seed=seed, passes=passes, lang=lang)
    target = wvs.GROUND_TRUTH[culture]
    return NodeCoordinate(
        culture=culture,
        ts=coord.ts,
        ss=coord.ss,
        distance_to_own_target=coord.distance_to(target),
        lang=lang,
        shift_ts=coord.ts - base_coord.ts,
        shift_ss=coord.ss - base_coord.ss,
    )


def _round_metric(
    round_num: int, coords: list[NodeCoordinate], diagnostics: tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> RoundMetric:
    """Separability + centroid + merge-diagnostic metrics for one round.

    Headline separability is on the SHIFT vectors (calibration-robust); the
    absolute-coordinate separability is reported alongside for context.
    """
    shift_pairwise = [
        ((a.shift_ts - b.shift_ts) ** 2 + (a.shift_ss - b.shift_ss) ** 2) ** 0.5 for a, b in combinations(coords, 2)
    ]
    abs_pairwise = [((a.ts - b.ts) ** 2 + (a.ss - b.ss) ** 2) ** 0.5 for a, b in combinations(coords, 2)]
    mean_shift_pairwise = sum(shift_pairwise) / len(shift_pairwise)
    mean_abs_pairwise = sum(abs_pairwise) / len(abs_pairwise)
    cx = sum(c.ts for c in coords) / len(coords)
    cy = sum(c.ss for c in coords) / len(coords)
    mean_to_centroid = sum(((c.ts - cx) ** 2 + (c.ss - cy) ** 2) ** 0.5 for c in coords) / len(coords)
    mean_cosine, sign_agreement, retained = diagnostics
    return RoundMetric(
        round_num=round_num,
        nodes=coords,
        mean_pairwise_distance=mean_shift_pairwise,
        centroid_ts=cx,
        centroid_ss=cy,
        mean_distance_to_centroid=mean_to_centroid,
        abs_pairwise_distance=mean_abs_pairwise,
        mean_update_cosine=mean_cosine,
        update_sign_agreement=sign_agreement,
        retained_update_ratio=retained,
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
        abs_pairwise_distance=d.get("abs_pairwise_distance", 0.0),
        mean_update_cosine=d.get("mean_update_cosine", 0.0),
        update_sign_agreement=d.get("update_sign_agreement", 0.0),
        retained_update_ratio=d.get("retained_update_ratio", 0.0),
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


def _culture_lang(config: AggregationConfig, culture: str) -> str:
    """Resolve the language a culture's node is measured in.

    Real runs read the language from the culture's corpus manifest (so the node is
    surveyed in the SAME language its grounded corpus is in) and require a WVS
    battery for it -- if none exists we fail loudly rather than silently fall back
    to English and re-introduce the aggregation-v1 muting. Smoke / placeholder
    corpora carry no manifest, so they fall back to ``instrument_lang``.
    """
    if config.corpus_path:
        manifest = Path(config.corpus_path) / culture / "manifest.json"
        if manifest.exists():
            lang = json.loads(manifest.read_text()).get("language")
            if lang not in wvs._BATTERY:
                raise ValueError(
                    f"culture {culture!r} corpus is in {lang!r} but no WVS battery exists for it; "
                    f"add _ITEMS_{(lang or '').upper()} to wvs.py (have {sorted(wvs._BATTERY)})"
                )
            return lang
    return config.instrument_lang


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
    # Each node is measured in its OWN corpus language (resolved from the culture's
    # manifest, falling back to instrument_lang for smoke/placeholder corpora that
    # carry no manifest). Measuring every node on a shared English instrument was
    # the aggregation-v1 flaw that muted the foreign-language CPT.
    langs = {c: _culture_lang(config, c) for c in config.cultures}

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
        # Measure the shared global base ONCE per round, in each node's language,
        # so each node's shift (node - base, same language) cancels that language's
        # calibration offset. One untrained clone, surveyed N times -- cheap vs CPT.
        base_node = base.clone()
        base_node.load_state(global_state)
        base_coords = {
            culture: _coord(base_node, seed=config.seed, passes=config.paraphrase_passes, lang=langs[culture])
            for culture in config.cultures
        }
        del base_node

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
                _measure(
                    node,
                    culture,
                    seed=config.seed,
                    passes=config.paraphrase_passes,
                    lang=langs[culture],
                    base_coord=base_coords[culture],
                )
            )
            fork_states.append(node.state())  # CPU weight vector; the GPU copy is then freed
            del node

        # Weight-space interference diagnostics on the forks' updates vs. the base
        # they started from, BEFORE we overwrite global_state with the average.
        diagnostics = _merge_diagnostics(global_state, fork_states)
        # FedAvg the sovereign forks into the next global base.
        global_state = _fedavg(fork_states)
        del fork_states

        metric = _round_metric(round_num, coords, diagnostics)
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
