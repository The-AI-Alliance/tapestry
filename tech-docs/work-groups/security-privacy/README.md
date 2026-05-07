# Security & Privacy Work Group

## Purpose

Define the technical guarantees that make Tapestry sovereignty enforceable: privacy tiers, secure aggregation, differential privacy, trusted execution, threat models, model-update leakage analysis, and safety-preservation constraints.

## Why it exists

Tapestry promises that data contributes without leaving and that sovereignty is enforced by architecture, not only by policy. This work group is grounded in [Design Goal 2](../../architecture/4-design-goals.md), [Design Goal 6](../../architecture/4-design-goals.md), and the privacy/security implications of the consortium training loop in [ADR-004](../../architecture/decisions/adr-004-training-loop.md).

## Scope

- Threat models for data, model updates, nodes, coordinators, and participants.
- Privacy tiers from provenance-only through strong technical privacy guarantees.
- Secure aggregation, differential privacy, TEE, and local-only patterns.
- Leakage analysis for gradients, weight deltas, adapters, routing, logs, and evaluation artifacts.
- Safety-preservation constraints for shared bases and sovereign adaptations.

Out of scope: deciding what data is culturally appropriate, operating infrastructure, or setting governance voting rules.

## Initial questions

- What threat model is required for each class of participant and data?
- When are weight deltas sufficient, and when are DP, secure aggregation, or TEEs required?
- What can be inferred from model updates, routing behavior, logs, or benchmark outputs?
- How do safety constraints persist through continued pretraining and post-training alignment?

## Early deliverables

- A privacy-tier specification for participant data and training runs.
- Threat-model templates for consortium training and sovereign alignment.
- Required controls for MVP nodes and coordinators.
- Security requirements handed to Infrastructure & Operations and Evaluation & Certification.

## Interfaces

- **Data Governance:** data sensitivity tiers and residency requirements.
- **Base Model Training:** aggregation security and update leakage.
- **Sovereign Alignment:** private preference data and safety preservation.
- **Infrastructure & Operations:** implementation of controls and monitoring.
- **Evaluation & Certification:** evidence that security and privacy claims hold.
