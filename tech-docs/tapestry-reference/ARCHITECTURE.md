# TAPESTRY Architecture Reference

This document describes the technical architecture of TAPESTRY — the structural decisions every work group must understand and respect.

---

## The 70/30 Separation

TAPESTRY's most important architectural decision: a strict separation between shared infrastructure and nation-specific configuration.

```
┌─────────────────────────────────────────────────────────────┐
│  UNIVERSAL INFRASTRUCTURE (70%)                             │
│  Identical across all sovereign nodes. No national          │
│  assumptions hard-coded here.                               │
│                                                             │
│  • Federated training protocol                              │
│  • Privacy-preserving gradient aggregation                  │
│  • Byzantine fault tolerance                                │
│  • Audit logging (immutable, cryptographically verifiable)  │
│  • Exit procedures (72-hour guarantee)                      │
│  • Sovereignty verification scripts                         │
└─────────────────────────────────────────────────────────────┘
                      configured by
┌─────────────────────────────────────────────────────────────┐
│  NATIONAL CONFIGURATION (30%)                               │
│  Fully owned and controlled by the sovereign node operator. │
│                                                             │
│  • Constitutional AI principles (YAML)                      │
│  • Language priorities and models                           │
│  • Sacred knowledge domain definitions                      │
│  • Legal framework compliance rules                         │
│  • Cultural Review Board interfaces                         │
└─────────────────────────────────────────────────────────────┘
```

Any design that bleeds national assumptions into the 70% layer, or that puts sovereignty enforcement only in the 30% layer, violates this principle.

---

## Model Hierarchy

```
TAPESTRY-GLOBAL
│   Open-source foundation model. Apache 2.0. Trained on aggregated
│   federated updates from all nodes. General-purpose baseline.
│
├── Regional variants  (TAPESTRY-EU, TAPESTRY-APAC, ...)
│   Fine-tuned with regional data and shared constitutional config.
│
├── National variants  (TAPESTRY-FR, TAPESTRY-JP, TAPESTRY-CA, ...)
│   Fine-tuned with national public-sector data and national
│   constitutional AI. Trained and served within national borders.
│
└── Entity variants  (TAPESTRY-HOSPITAL-LYON, ...)
    Fine-tuned with entity-specific proprietary data, on-premise.
    No external network dependency after initial setup.
```

Users start at TAPESTRY-GLOBAL (no sovereignty overhead) and migrate to higher levels as requirements evolve. Migration must not require rebuilding the application.

---

## Federated Training Protocol

Five invariants every training implementation must satisfy:

| Invariant | Specification |
|---|---|
| **Privacy** | Homomorphic encryption + differential privacy (ε < 1.0 per round). Zero raw data shared between nodes at any point. |
| **Fault tolerance** | Byzantine fault tolerance: up to 1/3 of nodes may be malicious, failing, or compromised without corrupting the global model. |
| **Sync latency** | Asynchronous gradient aggregation with <5 minute sync latency at production scale (1,000 nodes). |
| **Async tolerance** | Nodes operating on a 24–48 hour sync window are supported. Slow nodes do not block the network. |
| **Scale** | Designed and validated for 1,000 nodes. 7 initial G7 nodes is the Phase 1 target. |

Gradient sharing is encrypted end-to-end. No node's raw gradients are visible to any other node or coordinator at any time.

---

## Sovereign Node Guarantees

Every sovereign node implementation must satisfy all of these — not by policy, but by construction:

| Guarantee | How enforced |
|---|---|
| **Data residency** | Hardware-level geographic enforcement. Cryptographic attestation available to auditors without trusting the node operator's self-report. |
| **Exit capability** | Complete model + data + audit export in <72 hours, executable without coordination from any other node or central authority. |
| **Island mode** | Node operates with zero external network dependencies. Model inference, constitutional AI enforcement, and audit logging all local. |
| **Audit trail** | Immutable, cryptographically verifiable log of all training events, model updates, data accesses, constitutional AI changes. Exportable at exit. |
| **Consent enforcement** | Infrastructure-level data consent tracking. Community revocation triggers defined retraining procedures. |

---

## Constitutional AI Layer

Each sovereign node defines its own constitutional AI via YAML configuration — human-readable, auditable without engineering support.

Key capabilities:

- **Values and behavioral rules**: Community-configured; nothing imposed by the global coordination layer.
- **Sacred knowledge boundaries**: Named knowledge domains excluded from training, model outputs, and cross-node sharing. Enforced at the training pipeline and inference layer — not policy alone.
- **Cultural Review Board interface**: Binding authority to pause, modify, or audit the constitutional AI layer. No engineering changes required.
- **Consent tracking**: Per-dataset, per-community consent records with revocation support.

---

## Dual Architecture Tracks

| Track | Architecture | Status | Target use cases |
|---|---|---|---|
| **Track 1** | Transformer-based generative | Production-ready | Clinical notes, educational content, governance documents, cultural Q&A |
| **Track 2** | JEPA (Joint Embedding Predictive Architecture) | Under development | Crop yield prediction, climate adaptation, epidemiological forecasting |

Both tracks participate in federated training. The federated protocol supports heterogeneous architectures — nodes choose the architecture appropriate for their use case. JEPA is expected to reduce hallucination rates and improve efficiency relative to generative models for physical-world modeling tasks.

---

## Source Code Structure

```
src/tapestry/
├── data/              # Data governance, sovereignty enforcement, consent tracking
├── training/          # Federated training protocol, privacy-preserving aggregation
└── infrastructure/    # Sovereign node deployment, exit procedures, audit logging
```

Work group engineering output maps to these three subsystems. Cross-cutting concerns (constitutional AI, Byzantine fault tolerance) span all three.

---

## Five Key Invariants

Every pull request, design doc, and implementation decision must be checked against these:

1. **No raw data crosses node boundaries.** Ever. Privacy is architectural, not operational.
2. **Every node can be fully disconnected and operated independently.** No sovereignty guarantee depends on network connectivity.
3. **The 30% national configuration layer cannot weaken the 70% universal sovereignty guarantees.** Configuration customizes behavior; it cannot bypass exit, audit, or residency enforcement.
4. **The exit procedure is tested, not just documented.** Any node that has not successfully run a complete exit drill does not meet the sovereignty guarantee.
5. **Performance claims are domain-specific, not general.** Tapestry claims superior performance on culturally-situated domain tasks. It does not claim to outperform leading models on general academic benchmarks.
