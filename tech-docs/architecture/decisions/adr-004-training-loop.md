# TAP-004: The Consortium Training Loop

| Field | Value |
| :---- | :---- |
| Status | Proposed |
| Confidence | Strong (4/5) |
| Date | May 7, 2026 |
| Deciders | Christopher Nguyen (proposed), workshop participants (to resolve open questions) |

## Context

Given the core-plus-sovereign architecture (TAP-001) and the consortium training model (TAP-002), the specific training loop — how the global model improves over time — must be defined.

## Decision

The consortium training loop operates in four steps:

1. **Centralized base training** — train (or adopt) a frontier-competitive model on large-scale global open data.
2. **Distributed continued pretraining (Stage A)** — each node receives the current global model and does continued pretraining on its sovereign data, training the *entire model* (not just adapters).
3. **Weight vector contribution** — each node sends its **locally trained model weight vector** (post–Stage A CPT) to the central coordinator. Not per-step gradients. Not raw data.
4. **Central integration and redistribution** — the coordinator aggregates contributed weight vectors into an updated global model (FedAvg-class weighted averaging by default; outer optimizer swappable) and redistributes it. Back to Step 2.

**Scope boundary:** Stages B (instruction tuning) and C (alignment) from [TAP-005](adr-005-sovereign-pipeline.md) run locally to produce each participant's sovereign deployable model. They do **not** feed into the shared global base.

Nodes share **local model weight vectors after Stage A**, not per-step gradients. See [`training-approaches.md`](../../reference/training-approaches.md) for the full comparison.

![Consortium training loop](../diagrams/consortium-training-loop.svg)

*Step 1 establishes (or refreshes) the global model; the ongoing loop is 2 → 3 → 4 → 2.*

| Step | Where it runs | Sovereign data | What crosses the network |
| :--- | :-------------- | :------------- | :----------------------- |
| 1. Base training | Central / global pipeline | N/A (open or consortium-global data) | Global model checkpoint |
| 2. Continued pretraining (Stage A) | Each sovereign node | Stays on node | Nothing raw |
| 3. Weight vector contribution | Node → coordinator | Still on node | **Local model weights** (post–Stage A; not per-step gradients) |
| 4. Integration | Coordinator | — | Updated global model back to nodes |

## Rationale

- The loop delivers frontier capability improvement (Steps 1–4) while sovereign alignment layers (Stages B–C) stay local, matching DG1.
- Data never leaves the node — only model weight vectors after local CPT cross the wire (DG2).
- Each cycle improves the global model with sovereign knowledge from all nodes, creating a virtuous cycle: the next round of continued pretraining starts from a better base.
- The iterative nature means the 80/20 ratio (base vs. sovereign) shifts naturally over time as the global model absorbs more sovereign knowledge.

## Aggregation (modular)

The default integration step is **quality-weighted FedAvg-class averaging** of contributed Stage A weight vectors. The outer aggregation mechanism is **replaceable** — DiLoCo-style outer optimization, model merging, or distillation may be substituted without redesigning the sovereign pipeline ([TAP-007](adr-007-architecture-comparison.md)).

## Confidence assessment

The loop structure is sound and follows naturally from TAP-001 and TAP-002. The 4/5 confidence reflects three open questions:

1. **Cycle frequency.** Sync cadence is an operational choice, not fixed by the architecture. Deployments may sync frequently (cluster-like) or less often (geo-distributed). If nodes cycle at different rates, their influence on the global model diverges — the workshop should discuss whether synchronized or asynchronous cycling is preferable.

2. **Contribution weighting.** How are weight vectors from different nodes combined? Uniform weighting? Quality-weighted? This is simultaneously an optimization problem and a governance problem. See Phase 5, Decision 8.

3. **Convergence properties.** Each node's data is deliberately non-IID (that's the sovereignty point). What are the convergence properties of this loop when nodes have radically different data distributions? FedAvg and DiLoCo provide theoretical grounding at small scale, but frontier-scale validation is missing.

The loop itself is unlikely to be challenged. The open questions are about parameters, not structure.

## Alternatives considered

- **One-shot (no contribution back):** Distribute base, nodes customize, never feed improvements back. The global model never improves. This is just "download open weights and fine-tune."
- **Per-step gradient sharing (FedSGD):** Requires tight step-locking between nodes and the aggregator; higher bandwidth and tighter coupling than local-then-sync patterns.
- **Pure peer-to-peer (no centralized base):** No proven path to frontier quality from cold start.
- **Contributing Stages B–C to the global base:** Would homogenize culturally specific alignment into the shared model; rejected.

## Consequences

- Requires a central coordinator for aggregation. The coordinator is a governed role, not a power center (see Phase 5, Decision 7).
- The compute cost per cycle for each node is estimated at 5–10% of original base pretraining cost. This must be validated empirically.
- A consortium training prototype demonstrating this loop across 2–3 real nodes is the MVP deliverable, not a generic fine-tuning system.

## References

- [McMahan et al. "Communication-Efficient Learning of Deep Networks from Decentralized Data." AISTATS 2017.](https://arxiv.org/abs/1602.05629)
- [Douillard et al. "DiLoCo: Distributed Low-Communication Training of Language Models." arXiv:2311.08105, 2023.](https://arxiv.org/abs/2311.08105)
- [Jaghouar et al. "OpenDiLoCo: An Open-Source Framework for Globally Distributed Low-Communication Training." arXiv:2407.07852, 2024.](https://arxiv.org/abs/2407.07852)
- ["Communication-Efficient Language Model Training Scales Reliably and Robustly: Scaling Laws for DiLoCo." arXiv:2503.09799, 2025.](https://arxiv.org/abs/2503.09799)
- [Zhu et al. "Deep Leakage from Gradients." NeurIPS 2019.]()
- [Geiping et al. "Inverting Gradients: How easy is it to break privacy in federated learning?" NeurIPS 2020.]()
