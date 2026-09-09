# Data Governance Work Group

## Purpose

This work group defines how sovereign data can participate in Tapestry without surrendering control. It owns requirements for data sourcing, licensing, stewardship, residency constraints, provenance, contribution rights, and data-quality expectations for national, cultural, industrial, and institutional participants.

For our purposes, _data_ also includes artifacts like model weights and deliverables, and it includes metadata associated with datasets, models, and deliverables.

[Data Governance Requirements](data-governance-requirements.md) explores the details.

> [!NOTE]
> When considering how to implement governance requirements, _derived requirements_ for data management emerge that focus on architecture, design, and implementation details. _We consider these requirements the responsibility of the [Infrastructure & Operations](../infrastructure-operations/) work group._
>
> However, at this time, the data governance work group directory contains [Data Management Requirements](data-management-requirements.md), which include many of these derived requirements, so it is easier to explore them together. Our plan is to eventually move the data management requirements to Infrastructure & Operations (feedback welcome on this idea).

## Why it exists

This work group traces to [Phase 2 pain points](../../architecture/2-pain-points.md) around data residency, cultural extraction, locked corpora, and enterprise compliance walls. It is also a prerequisite for the core-plus-sovereign architecture in [TAP-001](../../architecture/decisions/adr-001-core-plus-sovereign.md) and the consortium training model in [TAP-002](../../architecture/decisions/adr-002-consortium-training.md).

## Initial questions

- How should Tapestry distinguish open data, sovereign data, community-held data, and private institutional data?
- What contribution rights or benefit-sharing claims attach to data.
- What additional metadata must accompany every dataset?
- What minimum provenance evidence is needed for certification?

## Early deliverables

- [Data governance requirements](data-governance-requirements.md), including coverage of:
    - A data-tier taxonomy for Tapestry participants.
	- A list of blocked-data scenarios where raw data must never leave a sovereign boundary (including through model memorization!).
- Derived [data management requirements](data-management-requirements.md).
	- A minimum dataset card template.
	- Requirements handed to [Security & Privacy](../security-privacy/) and [Infrastructure & Operations](../infrastructure-operations/).

## Interfaces

- **Security & Privacy:** privacy tiers, threat models, and leakage constraints.
- **Base Model Training:** which data can contribute to shared model improvement.
- **Sovereign Alignment:** culturally grounded corpora and preference data.
- **Evaluation & Certification:** audit evidence for data sovereignty claims.
- **Governance & Participation:** contribution credit and benefit-sharing rules.
- **Infrastructure & Operations:** how these requirements are implemented.

