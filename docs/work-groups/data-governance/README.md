# Data Governance Work Group

## Purpose

Define how sovereign data can participate in Tapestry without surrendering control. This group owns data sourcing, licensing, stewardship, residency constraints, provenance, contribution rights, and data-quality expectations for national, cultural, industrial, and institutional participants.

## Why it exists

This work group traces to [Phase 2 pain points](../../architecture/2-pain-points.md) around data residency, cultural extraction, locked corpora, and enterprise compliance walls. It is also a prerequisite for the core-plus-sovereign architecture in [TAP-001](../../architecture/decisions/adr-001-core-plus-sovereign.md) and the consortium training model in [TAP-002](../../architecture/decisions/adr-002-consortium-training.md).

## Scope

- Data contribution models: open, restricted, local-only, and participant-private.
- Dataset provenance, consent, attribution, licensing, and usage constraints.
- Residency and sovereignty requirements that downstream training and evaluation must respect.
- Data-quality criteria for culturally grounded continued pretraining and domain specialization.
- Interfaces for audit evidence and certification.

Out of scope: implementing training infrastructure, defining model-update privacy guarantees, or deciding governance rights for non-data contributions.

## Initial questions

- What metadata must accompany every dataset or corpus before it can be used?
- How should Tapestry distinguish open data, sovereign data, community-held data, and private institutional data?
- What contribution rights or benefit-sharing claims attach to data, and how are they recorded?
- What minimum provenance evidence is needed for certification?

## Early deliverables

- A data-tier taxonomy for Tapestry participants.
- [DocLang evaluation](doclang-evaluation.md).
- A minimum dataset card / provenance record template.
- A list of blocked-data scenarios where raw data must never leave the participant.
- Requirements handed to Security & Privacy and Infrastructure & Operations.

## Interfaces

- **Security & Privacy:** privacy tiers, threat models, and leakage constraints.
- **Base Model Training:** which data can contribute to shared model improvement.
- **Sovereign Alignment:** culturally grounded corpora and preference data.
- **Evaluation & Certification:** audit evidence for data sovereignty claims.
- **Governance & Participation:** contribution credit and benefit-sharing rules.
