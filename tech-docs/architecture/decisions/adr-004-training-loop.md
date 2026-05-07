# ADR-004: The Consortium Training Loop

**Status:** Proposed
**Confidence:** Strong (4/5)
**Date:** May 7, 2026
**Deciders:** Christopher Nguyen (proposed), workshop participants (to resolve open questions)

## Context

Given the core-plus-sovereign architecture (ADR-001) and the consortium training model (ADR-002), the specific training loop — how the global model improves over time — must be defined.

## Decision

The consortium training loop operates in four steps:

1. **Centralized base training** — train (or adopt) a frontier-competitive model on large-scale global open data.
2. **Distributed continued pretraining** — each node receives the current global model and does continued pretraining on its sovereign data, training the *entire model* (not just adapters).
3. **Weight delta contribution** — each node computes the difference between its locally-trained model and the global model it started from, and sends these weight deltas to the central coordinator.
4. **Central integration and redistribution** — the coordinator aggregates weight deltas into an updated global model and redistributes it. Back to Step 2.

Nodes share **weight deltas**, not per-step gradients. Weight deltas aggregate over many training steps, require less bandwidth, tolerate WAN latency, and have better natural privacy properties (the signal from any individual training example is diluted). See [`training-approaches.md`](../training-approaches.md) for the full comparison.

## Rationale

- The loop delivers both frontier capability (Step 1) and sovereign alignment (Step 2), matching DG1.
- Data never leaves the node — only weight deltas cross the wire (DG2).
- Each cycle improves the global model with sovereign contributions from all nodes, creating a virtuous cycle: the next round of continued pretraining starts from a better base.
- The iterative nature means the 80/20 ratio (base vs. sovereign) shifts naturally over time as the global model absorbs more sovereign knowledge.

## Confidence assessment

The loop structure is sound and follows naturally from ADR-001 and ADR-002. The 4/5 confidence reflects three open questions:

1. **Cycle frequency.** How often do nodes contribute? Monthly? Quarterly? Per-node choice? If some nodes cycle monthly and others annually, their influence on the global model diverges. The workshop should discuss whether synchronized or asynchronous cycling is preferable.

2. **Contribution weighting.** How are weight deltas from different nodes combined? Uniform weighting? Quality-weighted? This is simultaneously an optimization problem and a governance problem. See Phase 5, Decision 8.

3. **Convergence properties.** Each node's data is deliberately non-IID (that's the sovereignty point). What are the convergence properties of this loop when nodes have radically different data distributions? DiLoCo provides theoretical grounding at small scale, but frontier-scale validation is missing.

The loop itself is unlikely to be challenged. The open questions are about parameters, not structure.

## Alternatives considered

- **One-shot (no contribution back):** Distribute base, nodes customize, never feed improvements back. The global model never improves. This is just "download open weights and fine-tune."
- **Per-step gradient sharing:** Requires fast interconnect, high bandwidth, worse privacy properties. Incompatible with WAN-connected sovereign nodes.
- **Pure peer-to-peer (no centralized base):** No proven path to frontier quality from cold start.

## Consequences

- Requires a central coordinator for aggregation. The coordinator is a governed role, not a power center (see Phase 5, Decision 7).
- The compute cost per cycle for each node is estimated at 5–10% of original base pretraining cost. This must be validated empirically.
- A consortium training prototype demonstrating this loop across 2–3 real nodes is the MVP deliverable, not a generic fine-tuning system.
