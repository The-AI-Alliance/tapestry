# Base Model Training Work Group

## Purpose

Own the shared model capability path: selecting or adopting an initial open-weights base, defining how consortium training improves shared weights, and planning the transition toward consortium-owned base models when the project has sufficient compute, data, and operational maturity.

## Why it exists

This work group implements the training-side implications of [TAP-002](../../architecture/decisions/adr-002-consortium-training.md), [TAP-004](../../architecture/decisions/adr-004-training-loop.md), and [TAP-006](../../architecture/decisions/adr-006-phased-base-model.md). It addresses pain points around frontier cost, reusable consortium training infrastructure, hardware heterogeneity, and dependency without recourse.

## Scope

- Initial base-model selection criteria and replaceability requirements.
- Consortium training loop design, including outer-loop synchronization and aggregation.
- Shared-base continued pretraining on eligible participant contributions.
- Contribution weighting and shared-model update policies.
- Research agenda for heterogeneous, high-latency training at frontier scale.

Out of scope: participant-specific alignment layers, serving/product integration, and detailed privacy mechanisms.

## Initial questions

- Which open-weights base should Tapestry start from, and what makes it replaceable?
- What is the first credible scale target for consortium training experiments?
- How often should nodes contribute weight deltas, and who decides the cadence?
- How are contributions weighted without creating a governance capture vector?

## Early deliverables

- Base-model selection criteria for the MVP.
- A consortium training experiment plan with target model sizes and node assumptions.
- Aggregation-policy options for workshop review.
- Infrastructure requirements for heterogeneous compute and observability.

## Interfaces

- **Data Governance:** which data can affect shared weights.
- **Sovereign Alignment:** portability of sovereign work across base changes.
- **Security & Privacy:** leakage analysis for weight deltas and aggregation.
- **Infrastructure & Operations:** training orchestration, node operations, and fault tolerance.
- **Governance & Participation:** contribution weighting and decision rights.
