# Contribution validator

This contribution adds an admission-safety check in front of the consortium
outer merge. Before a node's model update is aggregated into the shared base,
the validator confirms that the update is structurally compatible with that base
and that its values are finite and within configured magnitude limits.

**Status: Candidate** (small, tested, type-checked; ready to be reviewed for
promotion into `src/tapestry/training/consortium/`).

## Why

Today the consortium coordinator
(`src/tapestry/training/consortium/coordinator.py`) computes contribution
weights from quality scores and then hands the accepted model states straight to
the outer merge. Nothing checks that a contribution has the expected tensors,
compatible shapes and dtypes, finite values, or a plausible update size. A
malformed contribution can therefore fail inside aggregation or, worse, write
NaN or garbage into the candidate shared base.

The infrastructure requirements draft calls for exactly this boundary. See
requirement INF-6 and the "Model-Update Validation" section in
[`docs/work-groups/infrastructure-operations/infrastructure-requirements.md`](../../docs/work-groups/infrastructure-operations/infrastructure-requirements.md),
and item 5 of [TAP-011](../../docs/architecture/decisions/adr-011-central-node-infrastructure.md)
(schema validation on the coordinator's ingress). This contribution is the first
deterministic, CPU-testable slice of that list: schema and parameter coverage,
tensor shapes and dtypes, finite values, and update-magnitude thresholds.

It supports issue #26 (infrastructure requirements roadmap) and the M1
consortium epic #183. It also gives #114 (central node), #116 (evaluation
choices), and #125 (heterogeneous hardware) a common compatibility boundary for
contributions produced by different nodes and hardware.

## What it is and is not

The validator is an **admission-safety layer**. A contribution that passes is
admissible for aggregation. It is **not** proven trustworthy: these checks do
not detect adversarial model poisoning, backdoors, or subtle drift, and they say
nothing about provenance or identity. Base-checkpoint fingerprints, signed
manifests, provenance records, and anomaly detection remain follow-up work.

## What it checks

Every contribution is compared against the shared-base state the node started
from. The validator keeps its own copy of that state. All checks run even after
the first failure, so one report lists every problem.

| Check | Finding code | Default |
| :---- | :----------- | :------ |
| Every expected tensor is present | `missing-parameter` | on |
| No tensors the base does not have | `unexpected-parameter` | on |
| Every value is a `torch.Tensor` | `not-a-tensor` | on |
| Shapes match the base | `shape-mismatch` | on |
| Tensor is on the same device as the base | `device-mismatch` | on |
| Dtypes match the base (exact, or any float for a float base) | `dtype-mismatch` | on, `exact` |
| No NaN or infinite values where the base holds a different value | `non-finite` | on |
| No finite value that overflows when cast into the base dtype | `value-overflows-base-dtype` | on |
| The update itself is measurable in float64 | `update-not-measurable` | on |
| Per-tensor update L2 norm within a limit | `layer-update-too-large` | off |
| Per-tensor update norm relative to the base tensor norm | `layer-relative-update-too-large` | off |
| Largest single-parameter change within a limit | `abs-delta-too-large` | off |
| Global update L2 norm within a limit | `global-update-too-large` | off |
| Global update norm relative to the global base norm | `global-relative-update-too-large` | off |

"Update" means `contribution - base`. Norms are computed in float64 (complex128
for complex tensors) with overflow-safe scaling, so the numbers are stable
across dtypes and devices. Statistics for every tensor and for the whole
contribution are returned even when the contribution is accepted.

Two details matter for real models:

- A base can legitimately contain non-finite values, for example a registered
  causal mask filled with `-inf`. A contributed value is only flagged as
  `non-finite` where it is NaN or infinite **and** differs from the base.
  Statistics cover elements where both sides are finite.
- A tensor whose base is all zeros has no meaningful relative update, so its
  `relative_l2` is `None` and relative limits skip it. Absolute limits still
  apply.

Magnitude limits are off by default because sensible values depend on the model
and on the local training recipe. They are meant to be set from observed
per-round statistics once a consortium has a few rounds of history.

## Layout

```
contrib/build4me2-contribution-validator/
├── README.md
├── LICENSE
├── .custom.mk                     # help text for the make targets below
├── .targets.mk                    # make contribution-validator-{demo,tests,all}
├── run.py                         # demo: one corrupted node among three
├── contribution_validator/
│   ├── validator.py               # ContributionValidator, validate_contribution
│   ├── limits.py                  # ValidationLimits, DtypePolicy
│   ├── findings.py                # report / finding / statistics dataclasses
│   ├── gate.py                    # ValidatingConsortiumCoordinator (wiring example)
│   └── faults.py                  # fault injection helpers used by tests and demo
└── tests/
    └── test_validator.py
```

Read `validator.py` first. `gate.py` shows where the check sits in a round.

## How to run it

Everything runs on CPU in a few seconds. From the repository root:

```shell
make contribution-validator-demo    # one round with a NaN injected into one node
make contribution-validator-tests   # the test suite
make contribution-validator-all     # both
```

Or without `make`:

```shell
PYTHONPATH="$PWD/src:$PWD/contrib/build4me2-contribution-validator" \
  uv run python contrib/build4me2-contribution-validator/run.py --fault nan

PYTHONPATH="$PWD/src:$PWD/contrib/build4me2-contribution-validator" \
  uv run python -m pytest contrib/build4me2-contribution-validator/tests -q
```

Expected output (values will differ slightly):

```
round 1
  accepted: ['vietnam', 'switzerland']
  rejected: ['india']
  weights:  {'vietnam': 0.5, 'switzerland': 0.5}
  vietnam      accepted  update_l2=0.5126 relative=0.0112 non_finite=0
  switzerland  accepted  update_l2=0.5142 relative=0.0113 non_finite=0
  india        REJECTED  update_l2=0.5095 relative=0.0112 non_finite=1
    - [non-finite] parameter 'embedding.weight' contains 1 NaN or infinite values
```

Other faults to try: `--fault missing`, `extra`, `shape`, `float16`, `scaled`.
Add `--dtype-policy float-compatible` to see `float16` pass, or
`--max-global-relative-update 0.5` to see `scaled` fail on magnitude. Add
`--json` to print the full machine-readable reports.

## Using it from code

The validator is standalone. Build one per round from the shared-base state the
nodes started from:

```python
from contribution_validator import ContributionValidator, ValidationLimits

validator = ContributionValidator(previous_state, ValidationLimits(max_global_relative_update=0.5))
report = validator.validate(contribution)      # a SovereignContribution
if not report.accepted:
    for finding in report.findings:
        log(finding.code, finding.tensor_name, finding.details)
audit_sink.write(report.to_dict())             # JSON-serializable
```

`ValidatingConsortiumCoordinator` in `gate.py` is the wiring example. It
subclasses the existing coordinator and admits only validated contributions to
the contribution policy and outer merge. Rejected nodes appear in
`ConsortiumRoundResult.rejected_nodes` together with policy rejections, and
`round_summaries[round_num]` keeps the two apart along with every per-node
report, so acceptance is recorded and repeatable.

The gate also takes `min_admitted_nodes`, a quorum. Validation rejections
shrink the set the contribution policy weights, and the policy's
`max_node_weight` cap is renormalised over that set, so with the default of one
a lone surviving node would receive the full weight. Set the quorum to the
smallest number of nodes you are willing to let move the shared base; when
fewer survive, the round leaves the base untouched and the summary records
`quorum_met=False`.

If the validator is promoted, the same logic is a few lines inside
`ConsortiumCoordinator.run_round` and `gate.py` goes away.

## Guarantees the tests cover

- A well-formed contribution from a real node cycle is accepted with full statistics.
- Missing, unexpected, wrongly shaped, wrongly typed, non-tensor, NaN, and infinite
  contributions are each rejected with the right finding and evidence.
- The dtype policy distinguishes `exact` from `float-compatible`, integer
  buffers must always match exactly, and a float32 value that would overflow a
  float16 base is rejected under the relaxed policy.
- A base with a `-inf` mask buffer accepts matching contributions, still catches
  a new NaN, and the gated coordinator matches the plain one on such a model.
- Zero-initialised base tensors do not turn relative limits into rejections.
- Complex tensors are checked for NaN in either component.
- Huge finite updates measure correctly; an update that overflows float64 is a
  finding, and the report still serializes to strict JSON (no NaN or Infinity).
- Per-layer and global magnitude limits reject oversized updates and pass
  ordinary ones.
- Validation never mutates the reference state or the contribution, and the
  validator's reference is a private copy.
- Reports are deterministic.
- In the gated coordinator, a corrupted node is rejected, the shared base stays
  finite, validation rejections are recorded separately from policy rejections,
  the quorum blocks a lone survivor, and when every node is rejected the shared
  base does not change.
- With well-formed contributions the gated coordinator matches the plain one exactly.

## Limitations and follow-ups

- No provenance, identity, signatures, or checkpoint fingerprints. The validator
  trusts that the contribution and the reference state are what they claim to be.
- No adversarial detection. Magnitude limits catch gross faults, not crafted updates.
- Limits are global to a round. Per-tensor-group limits (for example embeddings
  versus attention) would be a natural next step once there is data to set them.
- Integer and boolean tensors (for example batch-norm counters) get the same
  coverage, shape, dtype, and magnitude treatment as floats; their statistics
  are computed after casting to float64.
- The device check is exercised in the CPU-only test suite with a real CPU
  tensor that reports a different device, not with an actual second device.
  The existing outer merge does no device moves of its own, so a mismatch
  would otherwise fail inside aggregation.
- The quorum is a count, not a share of declared members. A policy that knows
  the consortium roster could express "at least half of the members" instead.
- Round summaries accumulate in memory for the life of the coordinator. Long
  runs should persist them to an audit sink and drop old rounds.
