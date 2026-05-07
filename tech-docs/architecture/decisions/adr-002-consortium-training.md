# ADR-002: Consortium Training Model

**Status:** Proposed
**Confidence:** High (5/5)
**Date:** May 7, 2026
**Deciders:** Christopher Nguyen (proposed), workshop participants (to ratify)

## Context

Tapestry's training involves multiple sovereign nodes contributing to a shared model. The approach must be named and distinguished from existing paradigms (centralized training, federated learning) to avoid confusion and to accurately describe what Tapestry does.

See [`training-approaches.md`](../training-approaches.md) for a full comparison of centralized, federated, and consortium training.

## Decision

Tapestry uses **consortium training**: a small number of large, trusted, heterogeneous nodes collaboratively training a shared model, where data sovereignty is a first-order architectural constraint and cultural alignment is the goal.

This is distinct from federated learning (designed for millions of small edge clients with individual privacy concerns) and from centralized training (all data in one place, one organization controls everything).

## Rationale

- Tapestry's nodes are few (dozens), large (national GPU clusters), and trusted (institutional participants with governance voice). This is fundamentally different from federated learning's millions of untrusted small clients.
- The sovereignty motive is national/institutional, not individual data protection. The governance model, trust assumptions, and communication patterns all differ.
- Using "federated" to describe Tapestry borrows the right principle (data stays put) but the wrong connotations (edge devices, FedAvg, cross-silo averaging). "Consortium training" accurately describes the participants, the purpose, and the governance.

## Confidence assessment

This is a framing and communication decision as much as a technical one. The term "consortium training" accurately reflects the architecture we've designed. It avoids confusion with federated learning literature and sets correct expectations for participants. The technical architecture does not change based on what we call it — but how participants understand and communicate about Tapestry does.

## Alternatives considered

- **Continue using "federated training":** Familiar term but misleading. Participants and reviewers would map Tapestry onto FedAvg/FL assumptions that don't apply.
- **"Distributed training":** Too generic. Covers everything from data-parallel training within a data center to Tapestry's cross-continent sovereignty-preserving loop.
- **"Collaborative training":** Accurate but vague. Doesn't convey the institutional, governance-heavy nature of the consortium.

## Consequences

- Requires updating all documentation and communications from "federated" to "consortium" when referring to Tapestry's own approach. (Largely complete as of May 2026.)
- The term "consortium training" is novel — it doesn't have an established literature. This is a feature (we define what it means) and a risk (no prior art to reference). DiLoCo is the closest technical precedent for the communication mechanism.
- References to federated learning techniques (FedAvg, DiLoCo, etc.) remain valid as technical building blocks. The distinction is between the paradigm (consortium) and the techniques it may use.
