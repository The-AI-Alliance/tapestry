# Base Model Training Work Group

## Purpose

Own the shared model capability path: selecting or adopting an initial open-weights base, defining how consortium training improves shared weights, and planning the transition toward consortium-owned base models when the project has sufficient compute, data, and operational maturity.

## Why it exists

This work group implements the training-side implications of the following ADRs:

- [TAP-002: Consortium Training Model](../../architecture/decisions/adr-002-consortium-training.md)
- [TAP-004: The Consortium Training Loop](../../architecture/decisions/adr-004-training-loop.md)
- [TAP-006: Phased Base Model Strategy](../../architecture/decisions/adr-006-phased-base-model.md)

It addresses pain points around frontier cost, reusable consortium training infrastructure, hardware heterogeneity, and dependency without recourse.

## Scope

- Initial base-model selection criteria and replaceability requirements. See [Base Model Selection](base-model-selection.md). ([Issue #25](https://github.com/The-AI-Alliance/tapestry/issues/25), part of [TAP-006: Phased Base Model Strategy](../../architecture/decisions/adr-006-phased-base-model.md)) 
- Consortium training loop design, including outer-loop synchronization and aggregation.
	- For example, experiments are required to understand the differences required for consortium training vs. other forms of federated learning (of which it is a special case). (Initial work: [Issue #24](https://github.com/The-AI-Alliance/tapestry/issues/24) - part of [TAP-004: The Consortium Training Loop](../../architecture/decisions/adr-004-training-loop.md). Additional issues will be created as needed.)
- Shared-base continued pretraining on eligible participant contributions.
- Contribution weighting and shared-model update policies.
- Research agenda for heterogeneous, high-latency training at frontier scale. (Issues TBD)

Out of scope: participant-specific alignment layers, serving/product integration, and detailed privacy mechanisms.

## Initial questions

- Which open-weights base should Tapestry start from, and what makes it replaceable? Discussed further in [Base Model Selection](base-model-selection.md).
- What is the first credible scale target for consortium training experiments?
- How often should nodes contribute weight deltas, and who decides the cadence?
- How are contributions weighted without creating a governance capture vector?

## Early deliverables

- Base-model selection criteria for the MVP. ([Issue #25](https://github.com/The-AI-Alliance/tapestry/issues/25) and [Base Model Selection](base-model-selection.md).)
- A consortium training experiment plan with target model sizes and node assumptions. ([Issue #24](https://github.com/The-AI-Alliance/tapestry/issues/24))
- Aggregation-policy options for technical review.
- Infrastructure requirements for heterogeneous compute and observability. ([Issue #26](https://github.com/The-AI-Alliance/tapestry/issues/26))

## Interfaces

- **Data Governance:** which data can affect shared weights.
- **Sovereign Alignment:** portability of sovereign work across base changes.
- **Security & Privacy:** leakage analysis for weight deltas and aggregation.
- **Infrastructure & Operations:** training orchestration, node operations, and fault tolerance.
- **Governance & Participation:** contribution weighting and decision rights.

## Skills Needed

This work group needs people with the following research and engineering skills:

* LLM training with PyTorch (or possibly [Rust tools](https://github.com/The-AI-Alliance/tapestry/issues/9)).
* Federated Learning, which is similar to consortium learning.
* The ability to research and evaluation distributed training algorithms, including those discussed in the ADRs listed in [Why it exists](#why-it-exists) above.
* Evaluation of LLMs with popular and custom benchmarks.
* Engineering and administration of large-scale, distributed training clusters.
