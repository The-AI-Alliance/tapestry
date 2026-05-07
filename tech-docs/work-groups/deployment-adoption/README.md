# Deployment & Adoption Work Group

## Purpose

Ensure Tapestry-derived models become usable systems, not just trained weights. This group owns serving patterns, product harnesses, integration guidance, participant rollout, developer experience, and adoption feedback loops.

## Why it exists

One of the central pain points is that sovereign models may exist but see little adoption. [Design Goal 4](../../architecture/4-design-goals.md) requires incremental value, and [ADR-005](../../architecture/decisions/adr-005-sovereign-pipeline.md) treats instruction tuning and chat readiness as part of the sovereign pipeline rather than an afterthought.

## Scope

- Serving, inference, and integration patterns for participant deployments.
- Chat, assistant, coding, and domain-specific product harness requirements.
- Developer experience, documentation, and onboarding flows.
- Participant rollout planning and adoption metrics.
- Feedback loops from real users back into alignment, evaluation, and roadmap decisions.

Out of scope: training the base model, defining certification criteria, or making participant governance decisions.

## Initial questions

- What is the first user-facing Tapestry experience that proves value?
- Which deployment patterns must work for national, cultural, industrial, and research participants?
- What adoption signals should feed back into evaluation and alignment?
- How can participants deploy locally without fragmenting the shared technical stack?

## Early deliverables

- MVP deployment scenarios and reference user journeys.
- Serving and integration requirements for Infrastructure & Operations.
- Adoption metrics tied to the pain points in Phase 2.
- Feedback-loop requirements for Sovereign Alignment and Evaluation & Certification.

## Interfaces

- **Sovereign Alignment:** instruction behavior, tone, domain fit, and user feedback.
- **Evaluation & Certification:** release gates and adoption evidence.
- **Infrastructure & Operations:** serving environments and operational support.
- **Security & Privacy:** deployment isolation, logging, and data-handling controls.
- **Governance & Participation:** participant rollout priorities and public claims.
