# Consortium experiment metrics

This contribution contains a deterministic measurement layer around the
Tapestry consortium-training proof of concept. It is staged under `contrib/`
so the core training-loop package can remain focused on the minimal PoC
protocol while experiment ideas are reviewed and iterated.

**Status: Speculative** (prototype / measurement scaffold).

It intentionally does not replace Flower, NIID-Bench, OpenDiLoCo,
lm-evaluation-harness, Unitxt, or other larger evaluation and federated
training tools. It only records CI-scale PoC metrics for the existing tiny
consortium-training loop.

Run from the repository root:

```shell
make consortium-experiment
```

or directly:

```shell
PYTHONPATH="$PWD/src:$PWD/contrib/jneums-consortium-experiment" \
  uv run python contrib/jneums-consortium-experiment/run.py
```

The default run writes:

- `runs/consortium_experiment/metrics.jsonl` with one JSON object per round;
- `runs/consortium_experiment/summary.json` with aggregate metrics.

To compare weighting options, run each policy with the same seed and separate
output directories:

```shell
PYTHONPATH="$PWD/src:$PWD/contrib/jneums-consortium-experiment" \
  uv run python contrib/jneums-consortium-experiment/run.py \
  --weighting quality --seed 7 --out runs/consortium_experiment/quality

PYTHONPATH="$PWD/src:$PWD/contrib/jneums-consortium-experiment" \
  uv run python contrib/jneums-consortium-experiment/run.py \
  --weighting equal --seed 7 --out runs/consortium_experiment/equal
```

Each run replaces `metrics.jsonl` and `summary.json` in its output directory.

Recorded metrics include accepted/rejected nodes, contribution weights, maximum
node influence, shared-base movement, sovereign artifact count, and node losses.
