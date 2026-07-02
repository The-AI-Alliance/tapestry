# Infrastructure Requirements

Status: draft requirements.

This note supports issue
[#26](https://github.com/The-AI-Alliance/tapestry/issues/26) by defining an
initial infrastructure requirement set for heterogeneous compute, governed data
movement, observability, and model-update integrity. It is intended to guide
early data-management, training, tuning, and evaluation work without choosing a
specific cloud, scheduler, or accelerator stack.

## Scope

In scope:

- participant node requirements;
- coordinator services and shared artifacts;
- heterogeneous compute and accelerator support;
- governed data ingress and egress;
- observability, logging, and audit evidence;
- checkpoint, artifact, and model-update integrity;
- operational readiness for training, tuning, and evaluation workloads.

Out of scope:

- selecting a production cloud provider or cluster scheduler;
- defining data-governance policy;
- defining cultural-alignment methods;
- implementing model-update privacy guarantees;
- operating a production shared training cluster.

## Requirement Summary

| ID | Requirement | Rationale |
| :-- | :---------- | :-------- |
| INF-1 | Define a minimum viable participant node. | Participants need a clear baseline for storage, compute, networking, identity, logging, and operational ownership. |
| INF-2 | Support heterogeneous hardware and software backends. | Tapestry participants will not all use the same accelerators, drivers, orchestration tools, or operating environments. |
| INF-3 | Govern and observe all data ingress and egress. | Data movement must respect dataset-specific residency, visibility, license, and allowed-use constraints. |
| INF-4 | Keep participant-local workloads possible. | Local-only data and sovereign pipelines must be able to run inside participant boundaries. |
| INF-5 | Track checkpoint, artifact, and model-update lineage. | Training and certification claims need reproducible links between inputs, jobs, outputs, and approvals. |
| INF-6 | Validate model updates before aggregation or distribution. | Distributed updates need quality, compatibility, anomaly, and policy checks before they affect shared artifacts. |
| INF-7 | Provide observability without exposing restricted data. | Operators need health, performance, and audit signals while preserving participant confidentiality. |
| INF-8 | Separate central coordinator responsibilities from participant responsibilities. | The platform should avoid turning the coordinator into a data-control or lock-in point. |
| INF-9 | Support failure recovery and intermittent participation. | Consortium nodes may have different maintenance windows, network reliability, and operational constraints. |
| INF-10 | Produce evidence for governance and certification workflows. | Infrastructure events should feed release gates, contribution accounting, and audit records. |

## Minimum Viable Participant Node

A participant node should be able to:

- authenticate operators and workload identities;
- store local datasets, manifests, checkpoints, logs, and generated artifacts;
- run approved data-preparation, training, tuning, and evaluation workloads;
- enforce local data-use constraints before data leaves the node;
- export approved metadata, hashes, metrics, attestations, or model updates;
- receive shared-base artifacts and verify their integrity before use;
- retain enough logs for audit and incident review.

The minimum node does not need to expose raw data to the coordinator. It should
support pointer-based participation, where shared workflows consume manifests,
content hashes, aggregate metrics, and attestations instead of unrestricted data.

## Coordinator Responsibilities

The coordinator should provide shared services that do not require centralizing
participant data:

- participant and node registry;
- artifact manifest registry;
- shared-base release registry;
- model-update submission and validation workflow;
- contribution accounting inputs;
- release-gate evidence collection;
- status dashboards for operational health and readiness.

Coordinator services should treat participant data boundaries as first-class
constraints. A coordinator may receive model updates, metadata, hashes, and
audit evidence, but it should not assume raw data can be copied into a central
environment.

## Governed Data Movement

All data ingress and egress should be policy-aware:

| Flow | Required controls |
| :--- | :---------------- |
| Dataset enters a node | Source, license, consent, residency, owner, and allowed-use metadata are recorded. |
| Dataset is prepared | Processing job, tool version, configuration, input snapshot, output snapshot, and quality signals are recorded. |
| Artifact leaves a node | Export is checked against visibility, residency, and allowed-use constraints. |
| Model update leaves a node | Update is linked to approved input manifests, training configuration, and validation results. |
| Shared artifact enters a node | Signature, hash, version, and compatibility are verified before use. |

The infrastructure should integrate with the Data Governance requirements and
avoid embedding policy decisions directly in ad hoc scripts.

## Model-Update Validation

Before a participant update is aggregated, published, or used for downstream
experiments, the platform should validate:

- schema and version compatibility;
- expected tensor shapes and parameter coverage;
- update magnitude and anomaly thresholds;
- training configuration and approved input references;
- quality metrics and regression signals;
- policy compliance for the declared data and workload;
- signature, hash, and submitter identity.

The first implementation can use conservative checks and human review. The
important requirement is that update acceptance is explicit, recorded, and
repeatable.

## Observability Requirements

Infrastructure observability should cover:

- workload status, duration, resource usage, and failures;
- data-movement events and export approvals;
- artifact versions, hashes, and retention status;
- checkpoint creation, promotion, rollback, and deletion;
- update validation outcomes;
- node availability and compatibility status;
- security-relevant events such as credential use and failed access attempts.

Telemetry should be classified by visibility tier. Public or consortium-wide
dashboards should prefer aggregate health and readiness signals, while
participant-private logs can retain local operational detail.

## Security Baseline

The infrastructure should start with standard cloud and cluster security
practices:

- least-privilege access for operators and workloads;
- workload identity rather than shared long-lived credentials;
- encrypted storage and transport for restricted artifacts;
- secret management outside source control;
- signed or hashed artifacts;
- patching and dependency-update process;
- incident-response contact and escalation path for each participant node.

Security controls should be coordinated with the Security & Privacy work group
so that infrastructure implementation and privacy guarantees do not diverge.

## MVP Recommendation

For the first infrastructure pass, define:

1. A reference node checklist.
2. A manifest format for datasets, checkpoints, model updates, and evaluation
   artifacts.
3. A minimal update-validation checklist.
4. A visibility-tiered logging plan.
5. A shared artifact registry convention with hashes and versions.
6. A small readiness review before any node participates in shared experiments.

This creates enough operational structure for early experiments while leaving
room for participants to run different hardware, storage, and orchestration
systems.

## Open Decisions

- Which node capabilities are mandatory for Phase 0 versus later phases?
- Which scheduler or orchestration interfaces should the project standardize on
  first?
- Which model-update anomaly checks are sufficient for MVP experiments?
- Which telemetry fields can be shared consortium-wide by default?
- How long should participant nodes retain logs, manifests, and checkpoints?
- Which artifact signatures or attestation mechanisms should be required before
  shared-base releases?
