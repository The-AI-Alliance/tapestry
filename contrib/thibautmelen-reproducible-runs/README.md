# Reproducible, permission-bound runs for Tapestry pipelines

**Status: Speculative**

> **Disclosure:** this PoC uses [Nika](https://github.com/supernovae-st/nika),
> an open-source workflow engine (AGPL engine, Apache-2.0 spec) whose founder
> I am. It is proposed here because the pattern — runs as reviewable,
> permission-bound, replayable files — matches needs Tapestry has stated;
> evaluate the pattern on its merits, and treat the tool choice as swappable.

## What this is

Tapestry's contribution process asks for work that is *reviewed, audited,
versioned, and governed*, and the anti-capture principle wants sovereignty
*enforced through the architecture*. This PoC applies that standard to the
**runs themselves**, using the repository's own consortium-training demo as
the subject:

- **The plan is a file.** `workflows/consortium-demo-receipt.nika.yaml` is
  plain YAML, diffable and reviewable before anything executes. A static
  audit (`nika check`) verifies the task DAG, tool surface, types, and
  permits without running anything — during development it refused this very
  workflow until the exec command used the statically-verifiable array form.
- **Permissions are default-deny.** The workflow declares its entire blast
  radius in-file: it may run exactly one program (`uv`), write exactly one
  directory (`out/` under this contribution), and touch no network. Anything
  else is refused by the runtime, not by convention.
- **Every run leaves evidence.** A hash-chained trace (tamper-evident,
  replayable with `nika trace replay`) plus a small JSON receipt with the
  exit code and the demo's own N+1 summary tail —
  [`examples/sample-receipt.json`](examples/sample-receipt.json) is a real
  captured one.

For the Evaluation & Certification framing: this is the "audit evidence for
how a result was produced" layer, complementary to *what* the evals measure
(`nguyennm1024-sociocultural-alignment`, `jneums-cultural-cpt-validation`)
and to the evidence taxonomy in `oli-sovereign-eval-evidence`.

## How to run it

Prerequisites: the repo's normal setup (`make one-time-setup`) plus the
`nika` binary (a single static binary, no daemon):

```shell
brew install supernovae-st/tap/nika    # or see github.com/supernovae-st/nika
```

From the **repository root**:

```shell
# 1 · static audit — review the plan, cost, permits before anything runs
nika check contrib/thibautmelen-reproducible-runs/workflows/consortium-demo-receipt.nika.yaml

# 2 · the run — executes the consortium demo, writes out/consortium-demo-receipt.json
nika run contrib/thibautmelen-reproducible-runs/workflows/consortium-demo-receipt.nika.yaml

# 3 · the evidence — verify the hash chain of the trace the run printed
nika trace verify .nika/traces/<the-trace-the-run-printed>.ndjson
```

Or via the project make process: `make reproducible-runs-check` and
`make reproducible-runs-demo`.

Expected runtime: the demo itself (~5-10 s CPU-only) plus negligible
overhead; no network, no GPU, no API keys (the workflow uses no inference
tasks — `nika check` prices it at $0.00).

## Limitations / non-goals

- This does **not** orchestrate training and is not a distributed-training
  or aggregation component. It wraps the *repeatable operational work*
  around pipelines — the layer where reviewability and receipts live.
- One workflow is included on purpose (the demo). The same pattern extends
  to the contrib experiment runners and future eval harnesses; extending it
  is deliberately left until the pattern itself has been discussed.
- The receipt schema is minimal (command, exit code, summary tail). A real
  evidence format should converge with `oli-sovereign-eval-evidence`.

## Layout

```
thibautmelen-reproducible-runs/
├── README.md
├── LICENSE
├── .targets.mk                # make reproducible-runs-{check,demo}
├── workflows/
│   └── consortium-demo-receipt.nika.yaml
├── tests/
│   └── test_workflows_check.py   # static audit as a unit test (skips if nika absent)
└── examples/
    └── sample-receipt.json    # a real captured receipt
```
