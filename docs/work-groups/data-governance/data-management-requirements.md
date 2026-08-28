# Data Management Requirements

| Field       | Value                  |
| :---------- | :--------------------- |
| Status      | Draft                  |
| Confidence  | Medium (3/5)           |
| Created     | June 27, 2026          |
| Last Update | August 28, 2026        |
| Versions    | V0.1 - August 28, 2026 |

> [!NOTE]
> The requirements in this document are _derived_ in part from the [Data Governance Requirements](data-governance-requirements.md), because they bridge those high-level requirements to the architecture, design, and implementation details needed to meet them. (This document also covers other data-related requirements.) Some terms are defined in that document.
>
> Because architecture through implementation requirements are covered here, these requirements overlap with the concerns of the [Infrastructure & Operations](../infrastructure-operations/) work group. We may choose to move these requirements under that group, but for now, it is more convenient to work with them in tandem with the governance requirements.

This document supports issue [#27](https://github.com/The-AI-Alliance/tapestry/issues/27) by defining the first iteration ("V0.1") of the data management requirements for managing datasets used in Tapestry training, tuning, alignment, and evaluation work. It focuses on what the infrastructure must make possible before the project chooses specific tools.

## Scope of This Document

### In Scope

- Specification and selection of data catalog, storage, and other capabilities.
- Enforcement of dataset usage categories.
- Dataset discovery and cataloging.
- Storage and tracking of dataset life cycle, provenance, lineage, licensing, consent, and allowed-use metadata.
- Enforcement of access control restrictions for users and services.
- Auditing of all aspects of dataset usage and life cycle tracking.
- Characteristics of cost-effective storage, but with acceptable performance.

### Out of Scope

- Training infrastructure.
- Other infrastructure agnostic to data management details.

## Requirements (Draft)

> [!NOTE]
> * "DM" - Data Management
> * "DG" - Data Governance
> * "Parents" - Parent requirements, if any, from which this requirement is a derivative. From [Data Governance Requirements](data-governance-requirements.md) unless otherwise noted.

| ID    | Requirement | Parents | Rationale |
| :---- | :---------- | :------ | :-------- |
| DM:1  | Maintain a consortium-visible dataset and metadata catalog with per-dataset and per-participant visibility controls. | DG:1-4 | A catalog is the best way to manage this information and provide efficient and controlled access to users. |
| DM:2  | The catalog can manage datasets or point to datasets stored elsewhere, but with enforcement mechanisms to ensure consistency with locally-stored metadata and access restrictions. | DG:6 | The catalog needs flexibility about how data is stored, but with appropriate checks when the data is not under the catalog's control. |
| DM:3  | The catalog should be flexible in working with dataset formats and metadata schemas. | DG:10 | Even if we have preferred formats, we have to be flexible to use the many datasets available. |
| DM:4  | Implement a data access API with integrated event capture for tracking all events where data is read or written, including relevant context information, as required for governance controls. | DG:2,4-9 | Providing an API makes it easy to implement and enforce consistent tracking of activity. |
| DM:5  | All systems that read or write data must use the data access API. | DG:2,4-9 | This is necessary to ensure that all activity is adequately observed and recorded. It is also a tool for preventing inadvertent or malicious, intentional leakage of restricted information. |
| DM:6  | Track processing state and quality signals for each artifact. | DG:4 | The project needs to distinguish raw, cleaned, deduplicated, filtered, tokenized, held-out, and evaluation-ready data. |
| DM:7  | The data access API must require that a client process specify the input data and output artifact restrictions, so it can enforce exclusion of non-conformant input data. | DG:5 | This prevents data pipelines from undermining upstream restrictions. |
| DM:8  | The data access API must require that the output restrictions are not less strict than the input restrictions. | DG:5 | This prevents data pipelines from undermining upstream restrictions. |
| DM:9  | The data access API must restrict the information delivered to a process to conform to the source dataset restrictions. | DG:5 | For example, if a dataset prevents access to individual records, but allows particular aggregations (e.g., averages), the API must ensure that only the allowed aggregation information is delivered to clients. |
| DM:10 | All data access API activity is logged in a way that supports auditing. | DG:7 | Public summaries, consortium-private review artifacts, and participant-private logs must be separable. |
| DM:11 | The data access API integrates with Tapestry policy enforcement tools. | DG:8 | Reviewers need to know which version of a dataset supported a model or claim. |
| DM:12 | Deliver an MVP that works with local files, manifests, and documented attestations. | N/A | Early work should be useful before the full consortium platform exists. |

## Core Data Model Features

Every managed dataset or derived artifact should have a record with at least the following fields.

> [!NOTE]
> We plan to standardize on the Croissant metadata format and tooling, so the following will be updated accordingly, probably in the M1 time frame. See [this discussion](https://the-ai-alliance.github.io/open-trusted-data-initiative/dataset-requirements/).

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

The dataset card template in [`contrib/oli-sovereign-eval-evidence/dataset-card-template.md`](../../../contrib/oli-sovereign-eval-evidence/dataset-card-template.md) is a useful starting point for the human-readable view of this record.

## Processing Requirements

Data-management infrastructure should track processing state across the pipeline:

1. Raw acquisition and source review
2. Extraction and normalization
3. Language identification and domain tagging
4. Quality filtering and deduplication
5. PII, safety, contamination, and policy screening
6. Conversion to training, tuning, preference, or evaluation formats
7. Snapshotting, hashing, and approval for a specific use
8. Secure, audited storage

Each step should record the tool version, configuration, input snapshot, output snapshot, operator or job identity, and known caveats. This supports both reproducibility and rollback when a dataset must be withdrawn or corrected.

## Tooling Considerations

Issues [#27](https://github.com/The-AI-Alliance/tapestry/issues/27) and [#195](https://github.com/The-AI-Alliance/tapestry/issues/195) mention [Open Data Spaces (ODS)](https://www.ipa.go.jp/en/digital/opendataspaces/) as a possible source of ideas and possibly a system we adopt. The useful patterns for Tapestry are:

- Separate data, identity, transaction, semantic, and onboarding layers.
- Interoperable SDKs and APIs rather than a single mandatory backend.
- Explicit handling of data products and participant boundaries.
- Metadata-first discovery before raw-data movement.

Tapestry does not need to commit to the ODS implementation to adopt these patterns. Any selected tooling should satisfy the requirements above and work with participant-operated storage, catalogs, and policy systems.

## Interfaces With Other Work Groups

- **Security & Privacy:** consumes residency, visibility, and sensitivity metadata to define privacy tiers and leakage controls.
- **Infrastructure & Operations:** provides storage, compute, identity, networking, secrets, and observability needed by the data workflows. Ultimately, this work group owns the implementation of the requirements document here.
- **Base Model Training:** consumes approved data snapshots, manifests, and data-mix constraints.
- **Sovereign Alignment:** consumes culturally grounded corpora, instruction data, and preference records with provenance and reviewer caveats.
- **Evaluation & Certification:** consumes dataset cards, hashes, review evidence, release-gate inputs, and visibility-tiered reports.
- **Governance & Participation:** defines stewardship, approval authority, contribution credit, and dispute handling.

## MVP Recommendation

For the first implementation pass, prefer a lightweight workflow:

1. Define the minimum dataset record and metadata schemas.
2. Set up a data/metadata repository.
3. Store public examples and templates in the repository.
4. Allow participant-private details to remain outside the repository.
5. Use manifests, hashes, and attestations for local-only datasets.
6. Export structured evidence that evaluation and release-gate checks can read.

This path lets Tapestry start governing data before adopting a full data catalog or distributed data platform.

## Open Decisions

- Which fields are mandatory before a dataset can be used for each pipeline stage?
- What visibility tier should be required for certification evidence?
- Which policy checks are hard blockers versus reviewer warnings?
- How should local-only participants prove processing quality without exposing raw examples?
- What schema should become the machine-readable companion to dataset cards?
- Which existing catalog or dataspace tools should be evaluated for the first prototype?
