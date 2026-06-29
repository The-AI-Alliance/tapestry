# Data Management Infrastructure Requirements

Status: draft requirements.

This note supports issue
[#27](https://github.com/The-AI-Alliance/tapestry/issues/27) by defining the
minimum infrastructure requirements for managing datasets used in Tapestry
training, tuning, alignment, and evaluation work. It focuses on what the
infrastructure must make possible before the project chooses specific tools.

The core requirement is simple: Tapestry needs to know what data exists, who can
use it, where it may reside, what processing has happened to it, and what
evidence can be shared without violating participant sovereignty.

## Scope

In scope:

- dataset inventory and discovery;
- provenance, lineage, licensing, consent, and allowed-use metadata;
- governance controls for open, restricted, local-only, and participant-private
  datasets;
- preparation-state tracking from raw data through training-ready artifacts;
- audit evidence for evaluation, certification, and release gates;
- interoperability with participant-operated infrastructure.

Out of scope:

- selecting a production data catalog, storage backend, or policy engine;
- implementing training infrastructure;
- defining model-update privacy guarantees;
- deciding contribution credit or benefit-sharing policy.

## Requirement Summary

| ID | Requirement | Rationale |
| :-- | :---------- | :-------- |
| DMI-1 | Maintain a consortium-visible dataset catalog with per-participant visibility controls. | Participants need discovery without exposing private corpora or restricted metadata. |
| DMI-2 | Record dataset provenance and lineage from source acquisition through prepared, tokenized, tuning, and evaluation artifacts. | Training and certification claims need evidence that can be traced back to source and processing history. |
| DMI-3 | Capture rights, consent, license, residency, retention, and allowed-use constraints as structured metadata. | Governance decisions cannot rely on prose scattered across documents or private notes. |
| DMI-4 | Track processing state and quality signals for each artifact. | The project needs to distinguish raw, cleaned, deduplicated, filtered, tokenized, held-out, and evaluation-ready data. |
| DMI-5 | Support local-only and pointer-based participation. | Some participants can expose metadata, hashes, manifests, or attestations while keeping raw data inside their sovereign boundary. |
| DMI-6 | Produce audit evidence at multiple visibility tiers. | Public summaries, consortium-private review artifacts, and participant-private logs must be separable. |
| DMI-7 | Integrate with policy and release-gate checks. | Data-use constraints should be enforceable by downstream training, evaluation, and certification workflows. |
| DMI-8 | Preserve change history for datasets, metadata, processing jobs, and approvals. | Reviewers need to know which version of a dataset supported a model or claim. |
| DMI-9 | Use portable schemas and interfaces. | Tapestry should avoid forcing all participants into one storage or catalog system. |
| DMI-10 | Provide an MVP path that works with local files, manifests, and documented attestations. | Early work should be useful before the full consortium platform exists. |

## Core Data Model

Every managed dataset or derived artifact should have a record with at least the
following fields:

| Field | Description |
| :---- | :---------- |
| `artifact_id` | Stable identifier for the dataset or derived artifact. |
| `artifact_type` | One of the pipeline data types in the [training pipeline data taxonomy](../../reference/training-pipeline-data.md#data-type-summary), such as `raw`, `prepared`, `sft`, `preference`, or `eval`. |
| `owner` | Participant, steward, or work group responsible for the artifact. |
| `source` | Origin record, collection method, source URL, repository, deposit, or participant attestation. |
| `provenance` | Evidence for source, acquisition date, transformations, processing tools, and reviewer notes. |
| `lineage` | Parent artifacts and processing steps used to produce this artifact. |
| `rights` | License, consent basis, attribution requirements, retention limits, and prohibited uses. |
| `residency` | Where raw data and derived artifacts may reside or be processed. |
| `visibility` | Public, consortium-private, participant-private, or local-only. |
| `quality` | Preparation status, language coverage, deduplication status, quality score, contamination status, and known caveats. |
| `use_constraints` | Permitted stages, such as pretraining, continued pretraining, SFT, preference tuning, evaluation, or certification evidence. |
| `version` | Content hash, manifest version, or immutable snapshot reference. |

The dataset card template in
[`contrib/oli-sovereign-eval-evidence/dataset-card-template.md`](../../../contrib/oli-sovereign-eval-evidence/dataset-card-template.md)
is a useful starting point for the human-readable view of this record.

## Governance Controls

The infrastructure should support four broad participation modes:

| Mode | Raw data movement | Metadata visibility | Typical use |
| :--- | :---------------- | :------------------ | :---------- |
| Open | Raw data may be mirrored or redistributed under its license. | Public metadata is acceptable. | Public corpora, open benchmarks, reference datasets. |
| Restricted | Raw data may be used only under specified terms. | Public summary plus consortium-private details. | Licensed, consent-bound, or attribution-sensitive corpora. |
| Local-only | Raw data must remain inside a participant boundary. | Manifests, hashes, quality summaries, and attestations may be shared. | Sovereign, institutional, or industrial data. |
| Participant-private | Both raw data and most metadata stay private to the participant. | Only claims, approvals, or aggregate evidence may be shared. | Highly sensitive data or internal evaluation sets. |

These modes should be enforceable through both policy and workflow design. For
example, a training job should not need to parse free-form license prose to know
whether a dataset can be used for shared-base training.

## Processing Requirements

Data-management infrastructure should track processing state across the pipeline:

1. Raw acquisition and source review.
2. Extraction and normalization.
3. Language identification and domain tagging.
4. Quality filtering and deduplication.
5. PII, safety, contamination, and policy screening.
6. Conversion to training, tuning, preference, or evaluation formats.
7. Snapshotting, hashing, and approval for a specific use.

Each step should record the tool version, configuration, input snapshot, output
snapshot, operator or job identity, and known caveats. This supports both
reproducibility and rollback when a dataset must be withdrawn or corrected.

## Tooling Considerations

Issue #27 mentions Open Dataspaces as a possible source of ideas. The useful
patterns for Tapestry are:

- separate data, identity, transaction, semantic, and onboarding layers;
- interoperable SDKs and APIs rather than a single mandatory backend;
- explicit handling of data products and participant boundaries;
- metadata-first discovery before raw-data movement.

Tapestry does not need to commit to that implementation to adopt the patterns.
Any selected tooling should satisfy the requirements above and work with
participant-operated storage, catalogs, and policy systems.

## Interfaces With Other Work Groups

- **Security & Privacy:** consumes residency, visibility, and sensitivity
  metadata to define privacy tiers and leakage controls.
- **Infrastructure & Operations:** provides storage, compute, identity,
  networking, secrets, and observability needed by the data workflows.
- **Base Model Training:** consumes approved data snapshots, manifests, and
  data-mix constraints.
- **Sovereign Alignment:** consumes culturally grounded corpora, instruction
  data, and preference records with provenance and reviewer caveats.
- **Evaluation & Certification:** consumes dataset cards, hashes, review
  evidence, release-gate inputs, and visibility-tiered reports.
- **Governance & Participation:** defines stewardship, approval authority,
  contribution credit, and dispute handling.

## MVP Recommendation

For the first implementation pass, prefer a lightweight workflow:

1. Define the minimum dataset record schema.
2. Store public examples and templates in the repository.
3. Allow participant-private details to remain outside the repository.
4. Use manifests, hashes, and attestations for local-only datasets.
5. Export structured evidence that evaluation and release-gate checks can read.

This path lets Tapestry start governing data before adopting a full data catalog
or distributed data platform.

## Open Decisions

- Which fields are mandatory before a dataset can be used for each pipeline
  stage?
- What visibility tier should be required for certification evidence?
- Which policy checks are hard blockers versus reviewer warnings?
- How should local-only participants prove processing quality without exposing
  raw examples?
- What schema should become the machine-readable companion to dataset cards?
- Which existing catalog or dataspace tools should be evaluated for the first
  prototype?
