# TAP-011: Central Node Infrastructure

| Field | Value |
| :---- | :---- |
| Status | Proposed |
| Confidence | Strong (4/5) |
| Date | July 13, 2026 |
| Deciders | @elainechan, Contributors (proposed; verify and accept the infrastructure decision) |

## Context

[Issue #114](https://github.com/The-AI-Alliance/tapestry/issues/114) asks for the compute and storage requirements of the **central (core) node** that drives the consortium training process for [#70](https://github.com/The-AI-Alliance/tapestry/issues/70) — which the issue situates in the AI Alliance's AWS — with these responsibilities: 
1. Distribute model weights to the sovereign nodes. 
2. Merge the weight updates received from them.
3. Run evaluations and loss functions to measure progress. 
4. Integrate securely with the sovereign nodes, and aggregate status and logging.

The central node is the coordinator described in [TAP-004](adr-004-training-loop.md) Step 5, which that ADR is explicit is **"a governed role, not a power center"** (TAP-004 Consequences; deferred governance in Phase 5, Decision 7). It corresponds to `ConsortiumCoordinator` in the reference PoC (`src/tapestry/training/consortium/coordinator.py`). This ADR therefore has two jobs: 
1. Size the node.
2. Ensure the sizing choices do not turn a governed coordination role into a control point over membership or contribution weighting.

The _AWS Sovereign Node (Design C)_ is used below as a **reference implementation that assumes an AWS node is available** — it is a concrete example, not a hard requirement. The binding content of this ADR is the platform-neutral set of responsibilities, sizing, and governance properties; the AWS service names are one way to satisfy them. The issue observes the node "may not require many GPUs"; this ADR confirms and sharpens that, scoped to the M0 target — one core node plus two sovereign nodes, running a modest open model (≤8B–13B) through the Shared-Base Loop.

## Decision

The central node is a **governed coordination role realized as a memory-bound service, not a GPU training cluster, and not a control point.** For this first bring-up, the build should preserve three constraints so the host operator can run the node without unilaterally owning admission or contribution weighting:

- **1. No retention; equal redistribution.** 
    - a. The node holds member weight vectors only for the duration of a round.
    - b. It retains no member data, and redistributes the merged Shared Base to all members equally.
- **2. No unilateral control.** 
    - a. The host operator runs the node, but neither the operator nor any single member unilaterally decides who is admitted or how contributions are weighted.
    - b. The infrastructure should enforce the current admission and weighting decisions; it does not create them ([TAP-002](adr-002-consortium-training.md) shared governance; [TAP-004](adr-004-training-loop.md) open question 2).
- **3. Auditable.** The PoC needs an append-only trail for admission, aggregation, and weighting decisions, with the fuller consortium-oversight sink from [TAP-008](adr-008-data-sovereignty.md) able to build on that later.

Within those constraints, the M0 build is sized as follows. AWS bindings are marked as a reference; the requirement is the platform-neutral statement that precedes each.

### Proposed M0 build

**1. Compute — a memory-optimized host, no GPU.** Aggregation is element-wise weighted averaging of parameter tensors: memory-bandwidth-bound, not compute-bound. The host should be sized to keep the current Shared Base and at least one contributing weight vector resident at a time; if the merge path streams contributions from object storage, a smaller host is still acceptable for this first bring-up. At 13B in bf16, one full vector ≈ 26 GB (13B params × 2 bytes), so base + 2 contributions ≈ 78 GB. Evaluation is bursty and runs on demand, not on a standing GPU fleet. *Reference (AWS):* an `r7i.4xlarge` (128 GB) or `r7i.8xlarge` (256 GB) for aggregation; a single `g6e`/`g5` SageMaker Processing job per round for eval.
 
**2. Storage — a durable object store plus a lineage record.** One logical prefix per round holds the input Shared Base, each contribution, the aggregated output, and eval results (≈ (base + N + output) × 26 GB ≈ 100 GB per round at 13B, N=2; K rounds is hundreds of GB to low TB). The weight blobs live in object storage; round lineage and metadata — round ID → base hash, contributing member IDs, weighting inputs, aggregated hash, eval scores, and pointers to the stored blobs — live in a queryable store and form part of the auditable record above. *Reference (AWS):* S3 with Object Lock on the round artifacts + DynamoDB for lineage. If Flower is the substrate, back its state with a durable store (Postgres), not the default in-memory SQLite, since rounds may run for days; it needs to survive crashes and restarts.
 
**3. Substrate — suggested, not mandated.** Flower's SuperLink plus a custom aggregation `Strategy` is one viable substrate for this first bring-up: the compatibility review found it supplies the round lifecycle, transport, and serialization the in-process reference PoC lacks, with the `ContributionPolicy` (`src/tapestry/training/consortium/policy.py`) quality-floor and anti-capture-cap logic implemented as an `aggregate_fit()` override. A conformant from-scratch coordinator meeting the same responsibilities is also allowed (see Non-goals). Where Flower is used, the **central-node operator** disables its telemetry (`FLWR_TELEMETRY_ENABLED=0`): by default the SuperLink process reports usage metrics to an external endpoint, which is unaudited outbound egress from the one node that sees every contribution and is disallowed in the governed environment. The aggregation algorithm is kept swappable (FedAvg-class default, TIES-merge as a candidate) per [TAP-007](adr-007-architecture-comparison.md).
 
**4. Contribution weighting — a governance-configurable mechanism, not a fixed policy.** Post-aggregation eval produces the *inputs* to contribution weighting (capability delta, cultural-alignment shift, safety regression). Whether and how to weight contributions is an open optimization-and-governance question ([TAP-004](adr-004-training-loop.md) open question 2). This ADR builds the weighting mechanism to be governance-configurable and auditable and **defaults it conservatively**, a published quality floor with otherwise-equal weighting, until governance decides the policy. It does not settle the policy, and it replaces the reference PoC's static hand-set `quality_score` with a governed input, not with a coordinator-chosen one.
 
**5. Secure integration and logging.** One narrow, mutually-authenticated ingress per member, with schema validation that rejects anything that is not a recognized checkpoint manifest. For the PoC, mutual auth plus an explicit member allow-list is enough; it does not need the full Flower `FederationManager` or formal consortium ratification machinery before the first bring-up. Status and logs still aggregate to an append-only oversight sink: each node ships round status; the coordinator logs each aggregation decision, the weighting applied, and eval outcomes — satisfying the issue's logging requirement and [TAP-008](adr-008-data-sovereignty.md)'s enforcement-audit obligation. *Reference (AWS):* PrivateLink/VPN + mTLS ingress; a host-account-managed allow-list that does not let the operator unilaterally add or exclude members; cross-account S3 (Object Lock) + CloudWatch/CloudTrail for the audit sink.

### Basis for each choice
 
Each load-bearing claim above and the source it rests on. AWS instance SKUs are illustrative examples that satisfy the stated requirement, not figures from any source document.
 
| Claim | Basis |
| :---- | :---- |
| FedAvg aggregation is a (quality-)weighted average of client weight vectors | McMahan et al. 2017, the defining FedAvg paper: the server update is a weighted average of client weights [1]; corroborated by the Flower `FedAvg` `Strategy` (`aggregate_fit`) and [TAP-004](adr-004-training-loop.md) |
| Averaging is memory-/bandwidth-bound, not compute-bound (no GPU needed) | The op is one element-wise pass over parameters with no backward pass; the AWS Sovereign Node design reaches the same conclusion ("doesn't need GPUs for simple weight averaging at small N") |
| One 13B weight vector ≈ 26 GB in bf16 (13B × 2 bytes) | bf16 is 2 bytes/parameter [2]; a standard estimate gives "half/BF16: 13 × 2 = 26 GB" for a 13B model [3] |
| ~128–256 GB RAM host with no GPU is sufficient at N=2 (e.g. `r7i.4xlarge`/`r7i.8xlarge`) | Derived from the 26 GB figure: base + 2 contributions ≈ 78 GB, inside a 128–256 GB memory-optimized host. SKU is an illustrative example, not sourced |
| Checkpoints stay in HF/safetensors format | [TAP-006](adr-006-phased-base-model.md) base-model-agnostic requirement; reference PoC and AWS design both use safetensors |
| Contribution weighting is an open optimization-and-governance question; default conservatively | [TAP-004](adr-004-training-loop.md) open question 2 states weighting is "simultaneously an optimization and a governance question" |
| Aggregation must stay swappable (FedAvg → TIES / DiLoCo) | [TAP-007](adr-007-architecture-comparison.md) modular-contribution mandate; TIES-Merging [4] and DiLoCo [5] are the named candidate mechanisms |
| Flower supplies round lifecycle/transport the PoC lacks; `ContributionPolicy` maps to `aggregate_fit()` | The compatibility review in this project; Flower framework [6] |
| Flower telemetry is on by default and needs to be manually disabled | Flower source sets `FLWR_TELEMETRY_ENABLED = os.getenv("FLWR_TELEMETRY_ENABLED", "1")` and posts to `telemetry.flower.ai`; disabled with `=0` [7] |
| In-memory SQLite state is inadequate for multi-day rounds; use durable Postgres | Flower `LinkState` defaults to in-memory SQLite; the SuperLink exposes a `SUPERLINK_DATABASE_SCHEMA_MISMATCH` exit path, confirming a pluggable durable backend [6] |
| Raw data must never traverse the egress; weights only | [TAP-002](adr-002-consortium-training.md), [TAP-004](adr-004-training-loop.md), [TAP-008](adr-008-data-sovereignty.md); enforced structurally, not by policy |
 

### Design-goal traceability

The design goals are those defined in [TAP-007](adr-007-architecture-comparison.md). This ADR is infrastructure for the coordinator, so it is checked primarily against the goals a central node can affect.

| Goal | How this decision serves (or defers) it |
| :--- | :-------------------------------------- |
| **DG2** (data sovereignty) | The coordinator receives only weight vectors over one validated ingress; schema validation rejects anything that is not a checkpoint manifest, so raw data cannot enter even by misconfiguration. The coordinator holds no member data. |
| **DG3** (anti-capture) | The coordinator sees every contribution and controls the merged base — a concentration point. This ADR makes the "governed role, not a power center" constraint enforceable in infrastructure (no data retention, equal redistribution, governance-owned admission and weighting, signed/audited rounds); the channel-level mitigation is carried by the proposed multi-node infrastructure. **Discharged only if admission and weighting stay with governance** — if the operator could set either, the guarantee fails regardless of the network controls. |
| **DG4** (incremental value) | Memory-bound sizing on a single host makes the coordinator cheap to stand up, so a working loop ships without heavy infrastructure. |
| **DG5** (strategic rationality) | A member will only contribute if the coordinator cannot be captured against it. Governance-owned admission/weighting and equal redistribution are what make participation rational; a coordinator the operator could tilt would deter exactly the members Tapestry needs. |
| **DG6** (safety in the shared base) | The coordinator runs post-aggregation eval, including a safety-regression gate, before a new base is promoted — but that suite is unbuilt (see Consequences), so DG6 is **only partially served today**. |
| **DG9** (extensible) | The aggregation Strategy is swappable (FedAvg → TIES → DiLoCo) and checkpoints stay HF/safetensors, so no lock-in to one contribution mechanism or model family. |

DG1 (frontier capability + alignment) is a property of the training architecture, not the coordinator's infrastructure; this ADR neither advances nor obstructs it.

## Rationale

- Weight averaging touches every parameter once per round with no backward pass; it is dominated by memory bandwidth and I/O, not FLOPs. Standing H100s on the coordinator would be idle waste. Eval is the only genuinely GPU-shaped coordinator task and it is bursty, which on-demand Processing jobs fit exactly.
- Reusing Flower's SuperLink rather than building a coordinator, protocol, and state machine from scratch is weeks of integration versus months of new build. The reference PoC has the right semantics but no transport or round lifecycle; Flower supplies exactly those and nothing that conflicts.
- Post-aggregation eval produces the *inputs* to contribution weighting, but this ADR deliberately does not turn those inputs into a coordinator-chosen weighting policy. TAP-004 open question 2 flags weighting as "simultaneously an optimization and a governance question," so the mechanism is built governance-configurable and defaults conservatively until governance decides — replacing the PoC's static `quality_score` with a governed input, not a coordinator-set one.

## Confidence assessment

Strong (4/5). The confidence is scoped to the *engineering* decision — the memory-bound, no-GPU sizing — which is robust for averaging-class aggregation and matches the AWS design's assessment that the coordinator "doesn't need GPUs for simple weight averaging at small N." The rating holds precisely *because* the governance-laden questions are now deferred rather than silently resolved: membership admission and contribution weighting are handed to consortium governance (TAP-002; TAP-004 OQ2), so this ADR is not betting on either. Two residual engineering uncertainties remain, both flagged in Consequences rather than hidden: the memory-residency sizing inverts at 70B (forcing pairwise streaming), and the "measure progress" responsibility depends on an eval suite that is not yet built. Neither makes the core sizing wrong; both make it incomplete. A reviewer who scores *delivered value including those dependencies* rather than *the sizing decision itself* could reasonably argue 3/5.

## Acceptance criteria and open work

Before changing this ADR from proposed to accepted:

1. Confirm the PoC operating rule this ADR depends on: the host operator runs the node, but admission and contribution weighting stay outside unilateral operator control.
2. Confirm the M0 scope this sizing assumes — one core node plus two sovereign nodes on a ≤13B model, averaging-class aggregation — against the actual #70 bring-up, and record any deviation that would move the compute envelope.
3. Link the Flower compatibility review referenced in the Decision and Basis table as a citable artifact, so the "Flower supplies the round lifecycle/transport the PoC lacks" and `ContributionPolicy` → `aggregate_fit()` claims are verifiable rather than asserted.
4. Choose the 70B residency remedy (streaming accumulation vs. out-of-core weighted-mean over safetensors shards) before Design C aggregation is built, so M0 code does not bake in full residency (see Consequences).
5. File the standalone contribution-weighting-policy ADR (Phase 5, Decision 8) as a follow-up, so this ADR's conservative default does not become de facto policy by inertia. This ADR proposes that decision as a separate workstream; it does not carry it.
6. Verify the durable-state and telemetry-disable requirements against the substrate actually chosen: if Flower is used, that `LinkState` is backed by a durable store rather than in-memory SQLite, and that `FLWR_TELEMETRY_ENABLED=0` is set on the central node.
7. Note that the central node infrastructure should be agnostic to the models used. However, this needs to be confirmed.

## Alternatives considered

- **GPU training cluster on the coordinator.** Rejected: the coordinator does no training; this over-provisions for a workload that is not there.
- **Promote the PoC's in-process `ConsortiumCoordinator` to a service directly.** Rejected as the substrate: it would require building transport, serialization, round state, and failure recovery from scratch — precisely what Flower already provides. The PoC's logic is still reused, as the custom Strategy.
- **In-memory SQLite `LinkState` (Flower default).** Rejected beyond a smoke test: multi-hour and multi-day rounds need state that survives restarts.
- **Build `FederationManager` now for membership.** Deferred: with two known members, a host-account-managed allow-list enforced at the network/IAM layer is sufficient and simpler for the first bring-up. The deferral is conditional — it holds only while admission control stays outside unilateral operator control — and is revisited as N grows.
- **Let the node operator own membership and weighting for expedience.** Rejected: it would make the coordinator the "power center" TAP-004 forbids and cut against TAP-002's shared governance rights, deterring the members Tapestry needs (DG5). Admission and weighting stay with governance even when that is operationally slower.

## Non-goals

This ADR does not:

- Decide the production (Design B/C) coordinator architecture. It sizes the M0 core node for one core plus two sovereign nodes on a ≤13B model; the 70B-class and N-member cases are named but deferred.
- Choose the aggregation algorithm. It requires that the algorithm be swappable and sets FedAvg-class as the default; the FedAvg-vs-TIES-vs-DiLoCo choice is left to [TAP-007](adr-007-architecture-comparison.md)'s modular-contribution mandate and future evidence.
- **Set the contribution-weighting policy.** It builds a governance-configurable, auditable weighting mechanism and a conservative default, but *whether and how* to weight is [TAP-004](adr-004-training-loop.md) open question 2, owned by consortium governance.
- **Decide who is admitted to the consortium.** Membership admission is a governance decision ([TAP-002](adr-002-consortium-training.md)); this ADR only enforces an admission list technically and requires that enforcement not concentrate admission control in the node operator.
- Specify the eval suite. It places eval on the coordinator and states what it gates, but the capability, cultural-alignment, and safety benchmarks are separate workstreams ([TAP-005](adr-005-sovereign-pipeline.md)).
- **Mandate a cloud platform.** The AWS bindings are a reference implementation that assumes an AWS node is available; the binding content is the platform-neutral responsibilities, sizing, and governance properties. The central node may be hosted elsewhere.
- Mandate Flower. It suggests Flower's SuperLink as one viable substrate for the first bring-up, but the decision that binds is the coordinator's *responsibilities, sizing, and governance properties*; a conformant from-scratch coordinator is not precluded.
- Set the data-governance controls of the member nodes, which remain governed by [TAP-008](adr-008-data-sovereignty.md).

## Reconciliation with earlier documents

This ADR introduces infrastructure claims that touch earlier decisions. It does not silently reinterpret them; the following edits are proposed so the corpus stays consistent.

| Document | Interaction | Proposed change |
| :------- | :---------- | :-------------- |
| [TAP-002](adr-002-consortium-training.md) | Establishes "consortium with shared ownership and governance rights" and members' architectural voice | Record that membership admission and contribution weighting stay outside unilateral host control; the central node's infrastructure enforces the current decisions and hosting the node confers no admission or weighting authority |
| [TAP-004](adr-004-training-loop.md) | States the coordinator is "a governed role, not a power center" (Consequences; Phase 5, Decision 7) and flags weighting as an open optimization-and-governance question (OQ2) | Record that this ADR treats the coordinator as a governed role — building weighting as a governance-configurable, conservatively-defaulted mechanism rather than resolving it — and leaves the formal governance follow-up to later work |
| Phase 5, Decision 8 (weighting policy) — *referenced but unwritten* | TAP-004 open question 2 and TAP-007 defer the contribution-weighting policy to this decision, but no ADR yet records it | **Flag that this ADR's conservative default (published quality floor, otherwise-equal weighting) is load-bearing until that ADR exists** — if the governance decision is never written, the default becomes de facto policy by inertia. Propose a standalone weighting-policy ADR as the honest home for the question, filed as a separate follow-up rather than carried in this PR |
| [TAP-007](adr-007-architecture-comparison.md) | Mandates a swappable contribution mechanism | Record that the swap point is realized as the coordinator's aggregation `Strategy`, and that memory-bound sizing assumes averaging-class aggregation — a shift to secure aggregation or DP-on-aggregate would revise the compute envelope |
| [TAP-008](adr-008-data-sovereignty.md) | Requires auditable enforcement | Record the coordinator-side append-only oversight sink (signed admission, aggregation, and weighting decisions) as the coordinator half of that audit trail |
| [Base-model selection](../../work-groups/base-model-training) | Contains both M0 and long-term model-selection material. | Ensure the infrastructure supports the model choices. |
| Proposed multi-node infrastructure | Shares the ingress channel and the coordinator-trust concern | Cross-reference: this ADR sizes, secures, and governs the node; the proposed multi-node infrastructure defines the channel and carries the channel-level anti-capture (DG3) mitigation |

## Consequences

- **The 70B-class future breaks the "hold it all in memory" assumption.** At 70B one weight vector ≈ 140 GB (bf16), so base + 2 contributions (≈ 420 GB) already exceeds the 256 GB host this ADR sizes for at 13B; the aggregation service cannot keep full vectors resident. This is a constraint on the aggregation code, not a larger host, and must be designed in from M0 so the reference `_apply_weighted_average` path does not assume full residency. Two remedies are open and one should be chosen before Design C: 
    - 1. **streaming accumulation:** Add each full vector to a running weighted sum, then discard — simple, but still ~2 vectors resident, or 
    - 2. **out-of-core weighted-mean over safetensors shards:** Memory-map and average one parameter tensor at a time, bounding footprint to the largest tensor and decoupling it from model size.
- **Eval is a dependency, not a given.** The cultural-alignment (WVS) benchmark and the safety-regression suite are themselves unbuilt infrastructure ([TAP-005](adr-005-sovereign-pipeline.md), [TAP-001](adr-001-core-plus-sovereign.md) DG6). The "measure progress" responsibility cannot be fully met until they exist; track them as their own workstreams.
- **The governed-role constraint is load-bearing, not decorative.** Because the node sees every contribution and controls the merged base, the anti-capture promise fails if its operator can unilaterally admit/exclude members or set weighting — regardless of how good the network controls are. Admission and weighting must remain with consortium governance (TAP-002; TAP-004 Phase 5, Decision 7), and the proposed multi-node infrastructure must carry the channel-level mitigation. Whoever operates the node — the AI Alliance or anyone else — operates it under those constraints, not above them.
- **The AWS bindings are a reference, not a requirement.** The AWS design doc assumes an AWS node is available; the obligations that actually bind are the platform-neutral responsibilities, sizing, and governance properties. A member or the consortium may host the central node on other infrastructure that meets them.

## References

### Tapestry corpus and reference implementation

- [TAP-002](adr-002-consortium-training.md), [TAP-004](adr-004-training-loop.md), [TAP-005](adr-005-sovereign-pipeline.md), [TAP-006](adr-006-phased-base-model.md), [TAP-007](adr-007-architecture-comparison.md), [TAP-008](adr-008-data-sovereignty.md), and [TAP-009](adr-009-goal-derived-base-model-selection.md).
- AWS Sovereign Node system design — Design C (coordinator side); used here as a reference implementation that assumes an AWS node is available, not a hard requirement.
- Reference PoC: `src/tapestry/training/consortium/{coordinator,policy,messages}.py`.
- Flower substrate compatibility review (this project) — to be linked as a citable artifact before acceptance (see Acceptance criteria, item 3).

### Numbered sources (Basis table)

1. McMahan et al. "Communication-Efficient Learning of Deep Networks from Decentralized Data." AISTATS 2017. <https://arxiv.org/abs/1602.05629> — defines FedAvg; the server update is a weighted average of client weights.
2. IEEE Std 754 / the bfloat16 format: a 16-bit floating-point representation occupying 2 bytes per value. See e.g. Kalamkar et al. "A Study of BFLOAT16 for Deep Learning Training." arXiv:1905.12322, 2019. <https://arxiv.org/abs/1905.12322>
3. Memory-footprint estimate for weights = parameter count × bytes-per-parameter; at bf16 (2 bytes) a 13B model ≈ 26 GB. Standard model-size accounting; consistent with Hugging Face model-memory guidance. <https://huggingface.co/docs/transformers/main/en/model_memory_anatomy>
4. Yadav et al. "TIES-Merging: Resolving Interference When Merging Models." NeurIPS 2023. <https://arxiv.org/abs/2306.01708>
5. Douillard et al. "DiLoCo: Distributed Low-Communication Training of Language Models." arXiv:2311.08105, 2023. <https://arxiv.org/abs/2311.08105>
6. Beutel et al. "Flower: A Friendly Federated Learning Research Framework." arXiv:2007.14390, 2020. <https://arxiv.org/abs/2007.14390>
7. Flower telemetry default and opt-out: the framework sets `FLWR_TELEMETRY_ENABLED` to `"1"` unless overridden and posts events to `telemetry.flower.ai`; disabled with `FLWR_TELEMETRY_ENABLED=0`. Verified in the Flower source (`telemetry` module; `flwr/supercore/telemetry.py` in current releases). See also Flower telemetry documentation. <https://flower.ai/docs/framework/ref-telemetry.html>