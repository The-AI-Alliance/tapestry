# Tapestry Consortium Training PoC

This package is a small executable model of the Tapestry consortium-training
vision. It is not a generic FedAvg demo: the PoC keeps the **N+1 model outcome**
front and center.

- **1 shared base model** is governed by the consortium coordinator.
- **N sovereign model artifacts** are produced and owned by participant nodes.
- Nodes train locally on sovereign corpora (Stage A CPT) and share **local model
  weight vectors** with the coordinator.
- A governed contribution policy applies a quality floor and anti-capture cap
  before integrating accepted weights into the shared base (FedAvg-class averaging
  by default).

## Modules

| Module | Purpose |
| :----- | :------ |
| `model.py` | `TinyCausalModel`, a small next-token model for fast tests and demos. |
| `node.py` | `SovereignTrainingNode`, which runs local Stage A CPT and keeps a sovereign model artifact. |
| `coordinator.py` | `ConsortiumCoordinator`, which evolves the shared base from governed contributions. |
| `policy.py` | `ContributionPolicy`, a minimal quality-floor and anti-capture weighting policy. |
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

## What This Demonstrates

The PoC demonstrates the architecture-level invariants from the ADRs:

1. Raw sovereign data stays local.
2. Each participant gets a persistent sovereign model artifact.
3. The coordinator integrates only governed local model weight vectors (Stage A).
4. Low-quality contributions can be rejected.
5. A single participant's influence can be capped.

It intentionally does **not** claim frontier-scale training, formal privacy,
production governance, or a complete post-training alignment pipeline (Stages B–C).
