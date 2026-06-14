# Consortium experiment metrics

This contribution contains a deterministic measurement layer around the
Tapestry consortium-training proof of concept. It is staged under `contrib/`
so the core training-loop package can remain focused on the minimal PoC
protocol while experiment ideas are reviewed and iterated.

Status: prototype / measurement scaffold.

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

Recorded metrics include accepted/rejected nodes, contribution weights, maximum
node influence, shared-base movement, sovereign artifact count, and node losses.
