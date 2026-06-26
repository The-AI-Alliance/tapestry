# README for the `reference` Directory

Long-lived reference material that supports Tapestry design and operations:
architecture syntheses, conceptual comparisons, deployment notes, and
usage-oriented docs that are not part of the phased TVA architecture chain under
[`architecture/`](../architecture/README.md).

| Document | Description |
| :------- | :---------- |
| [`architecture.md`](architecture.md) | Single-page synthesis of Tapestry's architecture (core-plus-sovereign, consortium training, the training loop, the sovereign pipeline, data sovereignty, and the design invariants), with links to the source-of-truth ADRs |
| [`glossary.md`](glossary.md) | Definitions of Tapestry-specific terms (consortium training, Shared-Base Loop, Sovereign Build, etc.); links to the canonical ADR for each |
| [`training-approaches.md`](training-approaches.md) | Centralized vs. federated vs. **consortium** training — comparison table, shared [`consortium-training-loop.svg`](../architecture/diagrams/consortium-training-loop.svg), links to ADRs |
| [`training-pipeline-data.md`](training-pipeline-data.md) | LLM training pipeline stages, data type taxonomy, quality framework, and implications for Tapestry's consortium model |

The architecture synthesis summarizes the design chain under
[`../architecture/`](../architecture/README.md) and the decision records under
[`../architecture/decisions/`](../architecture/decisions/README.md). Where the
synthesis and an ADR disagree, the ADR is authoritative.
