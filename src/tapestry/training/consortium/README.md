# Tapestry Consortium Training PoC

This package is a small executable model of the Tapestry consortium-training
vision. It is not a generic FedAvg demo: the PoC keeps the **N+1 model outcome**
front and center.

- **1 shared base model** is governed by the consortium coordinator.
- **N sovereign model artifacts** are produced and owned by participant nodes.
- Nodes train locally on sovereign corpora (Contributed CPT) and share **local model
  weight vectors** with the coordinator.
- A governed contribution policy applies a quality floor and anti-capture
  controls before integrating accepted weights into the shared base
  (weighted averaging by default). The PoC can compare quality-weighted
  influence, equal-influence weighting, and multiple outer merge strategies.

## Modules

| Module | Purpose |
| :----- | :------ |
| `model.py` | `TinyCausalModel`, a small next-token model for fast tests and demos. |
| `node.py` | `SovereignTrainingNode`, which runs local Contributed CPT and keeps a sovereign model artifact. |
| `coordinator.py` | `ConsortiumCoordinator`, which evolves the shared base from governed contributions. |
| `merge.py` | Outer merge strategies, including weighted averaging, delta averaging, and a DiLoCo-inspired momentum delta option. |
| `policy.py` | `ContributionPolicy`, a minimal quality-floor and anti-capture policy with quality-weighted and equal-influence modes. |
| `messages.py` | Data classes for sovereign artifacts, contributions, and round results. |
| `../../../../contrib/jneums-consortium-experiment/` | Contrib experiment runner and metrics helpers that record round metrics and summaries without changing core training logic. |

## Experiment Runner

The experiment runner is a small measurement layer around this PoC. It keeps the
existing tiny model and coordinator/node abstractions, then writes machine-readable
metrics so contribution policies can be compared without claiming frontier-scale
results.

Run the default experiment:

```shell
PYTHONPATH="$PWD/src:$PWD/contrib/jneums-consortium-experiment" \
  uv run python contrib/jneums-consortium-experiment/run.py --out runs/consortium_experiment
```

This writes:

- `metrics.jsonl` with one JSON object per consortium round.
- `summary.json` with aggregate experiment metrics.

The first metrics are intentionally limited to consortium-specific PoC invariants:
accepted/rejected nodes, contribution weights, maximum node influence, shared-base
movement, sovereign artifact count, and local node losses.

This runner is **not** a replacement for established FL or LLM evaluation tooling.
Larger experiments should align with existing systems such as Flower/NIID-Bench for
non-IID FL baselines, OpenDiLoCo for low-communication distributed LLM training, and
lm-evaluation-harness or Unitxt for downstream model evaluation.

## Comparing Contribution Weighting Options

The coordinator supports multiple governed weighting choices through
`ContributionPolicy(weighting=...)`, making it possible to compare policy
outcomes without changing the training loop:

- `weighting="quality"` keeps the existing behavior: accepted nodes are weighted
  by their quality scores, with `max_node_weight` limiting single-node dominance.
- `weighting="equal"` accepts nodes through the same quality floor, then assigns
  each accepted node the same integration weight so influence is distributed
  uniformly across the accepted set.

Run the demo with one policy:

```shell
PYTHONPATH="$PWD/src" uv run python examples/consortium_training_demo.py --weighting equal
```

Run both policies back to back with the same seed and round count:

```shell
PYTHONPATH="$PWD/src" uv run python examples/consortium_training_demo.py --weighting compare
```

## Comparing Outer Merge Options

The coordinator also supports multiple outer merge strategies through
`OuterMergeOptimizer(strategy=...)`:

- `weighted-average` keeps the original FedAvg-class behavior by directly
  averaging accepted local model states.
- `delta` applies a weighted average of node deltas to the previous shared base,
  with an outer learning rate.
- `momentum-delta` applies outer momentum to the weighted deltas, giving the PoC
  a small DiLoCo-style outer optimizer comparison point.

Run one outer merge strategy:

```shell
PYTHONPATH="$PWD/src" uv run python examples/consortium_training_demo.py --outer-merge delta
```

Run all outer merge strategies back to back:

```shell
PYTHONPATH="$PWD/src" uv run python examples/consortium_training_demo.py --outer-merge compare
```

## What This Demonstrates

The PoC demonstrates the architecture-level invariants from the ADRs:

1. Raw sovereign data stays local.
2. Each participant gets a persistent sovereign model artifact.
3. The coordinator integrates only governed local model weight vectors (Contributed CPT).
4. Low-quality contributions can be rejected.
5. A single participant's influence can be capped.

It intentionally does **not** claim frontier-scale training, formal privacy,
production governance, or a complete Sovereign Build post-training pipeline (Stages B–C).
