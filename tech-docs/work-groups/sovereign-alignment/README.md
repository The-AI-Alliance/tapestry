# Sovereign Alignment Work Group

## Purpose

Own the participant-specific pipeline that turns a shared capable base into models that reflect local knowledge, values, institutions, domains, and interaction norms. This includes culturally grounded continued pretraining, post-training alignment, instruction tuning, and portability of sovereign contributions.

## Why it exists

Sovereign alignment is Tapestry's primary differentiator in [Design Goal 1](../../architecture/4-design-goals.md) and [ADR-003](../../architecture/decisions/adr-003-cultural-alignment.md). [ADR-005](../../architecture/decisions/adr-005-sovereign-pipeline.md) makes post-training and instruction tuning first-class stages rather than downstream polish.

## Scope

- Participant-owned continued pretraining on culturally grounded and domain-specific data.
- Post-training alignment methods such as DPO, RLHF, constitutional AI, and preference modeling.
- Instruction tuning and chat-readiness patterns that preserve local norms.
- Portability of adapters, alignment layers, or sovereign model forks across base models.
- Requirements for culturally grounded data and value elicitation.

Out of scope: shared-base training policy, certification decisions, and production serving infrastructure.

## Initial questions

- When is continued pretraining required, and when are adapters or post-training enough?
- What evidence shows that a sovereign alignment pipeline changed culture-specific behavior rather than only surface style?
- How can sovereign layers remain portable when the base model changes?
- Which parts of safety are universal base constraints versus sovereign alignment choices?

## Early deliverables

- A reference sovereign alignment pipeline for one pilot participant.
- Requirements for culturally grounded data and preference collection.
- A portability strategy for sovereign layers across base-model updates.
- Evaluation requirements for cultural fit, domain fit, and instruction quality.

## Interfaces

- **Data Governance:** culturally grounded corpora, preference data, and usage rights.
- **Base Model Training:** base compatibility and transition planning.
- **Evaluation & Certification:** alignment metrics, acceptance gates, and evidence.
- **Security & Privacy:** safety preservation and private alignment data.
- **Deployment & Adoption:** product behavior, UX expectations, and feedback loops.
