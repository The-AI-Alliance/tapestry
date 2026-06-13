# Infrastructure & Operations Work Group

## Purpose

Own the platform and operating model that lets participants run Tapestry workloads across heterogeneous compute, networks, security regimes, and organizational boundaries.

## Why it exists

The architecture depends on reusable consortium training infrastructure, heterogeneous hardware support, reliable node operations, transparent accounting, and operational auditability. This work group supports [Design Goal 7](../../architecture/4-design-goals.md), [Design Goal 8](../../architecture/4-design-goals.md), and the operational requirements implied by [TAP-004](../../architecture/decisions/adr-004-training-loop.md).

## Scope

- Node reference architecture and operational runbooks.
- Heterogeneous accelerator support and backend abstraction.
- Training orchestration, scheduling, checkpointing, fault tolerance, and observability.
- Coordinator services, artifact storage, model distribution, and accounting plumbing.
- Operational readiness for shared training and deployment environments.

Out of scope: choosing certification criteria, defining cultural alignment methods, or setting governance policy.

## Initial questions

- What is the minimum viable node that can participate in Tapestry?
- How should the platform handle mixed hardware, intermittent availability, and high-latency networks?
- What telemetry is needed for auditability without leaking sovereign data?
- What is operated centrally, what is operated by each participant, and what can be optional?

## Early deliverables

- MVP node architecture and setup checklist.
- Training orchestration and observability requirements.
- Artifact and model-distribution plan.
- Operational cost/accounting requirements for Governance & Participation.

## Interfaces

- **Base Model Training:** training jobs, checkpoints, aggregation, and model distribution.
- **Sovereign Alignment:** participant-local pipelines and artifact portability.
- **Security & Privacy:** controls, logs, isolation, and secure runtime requirements.
- **Deployment & Adoption:** serving infrastructure and integration environments.
- **Governance & Participation:** contribution accounting and operational transparency.
