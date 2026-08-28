# Data Governance Requirements

| Field       | Value                  |
| :---------- | :--------------------- |
| Status      | Draft                  |
| Confidence  | Medium (3/5)           |
| Created     | June 27, 2026          |
| Last Update | August 28, 2026        |
| Versions    | V0.1 - August 28, 2026 |

This document supports issue [#211](https://github.com/The-AI-Alliance/tapestry/issues/211) by defining the first iteration ("V0.1") of the data governance requirements for managing datasets used in Tapestry training, tuning, alignment, and evaluation work. It focuses on what Tapestry must do to enable the use of datasets with various constraints on permissible use.

The core requirement is simple: Tapestry needs to know what data exists, who can use it, where it may reside, what processing has happened to it, and what evidence can be shared without violating participant sovereignty.

From these governance requirements, [Data Management Requirements](data-management-requirements.md) are being derived that guide architecture, design, and implementation choices.

## Scope of This Document

### In scope:

- Definitions of dataset contribution/usage categories, including  metadata such as provenance, lineage, licensing, consent, and allowed-usage constraints.
- Residency and sovereignty requirements that downstream training and evaluation must respect.
- Data-quality criteria for culturally grounded continued pretraining and domain specialization.
- Access controls for user access.
- Cost and performance constraints.
- Tracking of dataset life cycles, from discovery, preparation, transformation through pre- and post-training use, providing audit evidence for evaluation, certification, and release gates.
- Interoperability with participant-operated infrastructure.
- Useful classifications of data.

### Out of Scope

- The architecture, design, and implementation decisions to meet the data governance requirements.
- Defining model-update privacy guarantees.
- Deciding governance rights for non-data contributions.
- Deciding contribution credit or benefit-sharing policy

See [Data Management Requirements](data-management-requirements.md) for these topics.

## Definitions of Contribution/Usage Categories and Their Governance Controls

The infrastructure should support four broad participation modes:

| Mode | Raw data movement | Metadata visibility | Typical use |
| :--- | :---------------- | :------------------ | :---------- |
| **Open** | Raw data may be mirrored or redistributed under its license. | Public metadata is acceptable. | Public corpora, open benchmarks, reference datasets. |
| **Restricted** | Raw data may be used only under specified terms. | Public summary plus consortium-private details. | Licensed, consent-bound, or attribution-sensitive corpora. |
| **Local-only** | Raw data must remain inside a participant boundary. | Manifests, hashes, quality summaries, and attestations may be shared. | Sovereign, institutional, or industrial data. |
| **Participant-private** | Both raw data and most metadata stay private to the participant. | Only claims, approvals, or aggregate evidence may be shared. | Highly sensitive data or internal evaluation sets. |

These modes should be enforceable through both policy and workflow design. For example, the setup process for a training job should explicitly control which datasets are to be used, based for example on restriction criteria, target use cases (e.g., for domain-specific, tuned models), etc. This governance should be transparent to the training process itself, except for general requirements to track data usage, etc.

## Categories of _Unwanted_ Data

Organizations may also need to determine what data is _unwanted_, such as illegal content, privacy risk, and regional censorship. Specifically, we identify the following categories. See also [this OTDI discussion](https://github.com/The-AI-Alliance/open-trusted-data-initiative/discussions/226).

| Category | Description of the Problem | Impacted Party | Evidence (Links) |
| :-- | :-- | :-- | :-- |
| Personal Identifiable Information (PII) | Can violate privacy laws (e.g., GDPR/CCPA) if scraped or shared without consent; risk of regulatory fines and reputational damage. | Producer & Deployer | [Clearview AI scraping case](https://archive.is/Ok6gR) |
| Sensitive Health Data | Sharing or using patient data without proper consent can violate HIPAA and other healthcare privacy regulations; risk of lawsuits and heavy fines. | Producer & Deployer | [Google’s “Project Nightingale”](https://archive.is/bu3mq) |
| Copyrighted or Licensed Content | Ingesting protected text or images without permission can lead to infringement claims; potential lawsuits, takedowns, or cease-and-desist orders. | Producer & Deployer | [Getty Images lawsuit vs. Stability AI](https://www.penningtonslaw.com/news-publications/latest-news/2024/generative-ai-in-the-courts-getty-images-v-stability-ai) |
| Defamatory or Misinformation | Models trained on false or defamatory data may reproduce harmful statements, exposing deployers to defamation claims; can erode trust in AI systems. | Producer & Deployer | [OpenAI sued for defamation over ChatGPT “hallucinations”](https://www.forbes.com/sites/siladityaray/2023/06/08/openai-sued-for-defamation-after-chatgpt-generates-fake-complaint-accusing-man-of-embezzlement/) |
| Hate Speech or Extremist Content | Risk of amplifying hateful or violent ideologies; can damage brand reputation and invite regulatory scrutiny. | Deployer | [YouTube algorithm controversy](https://www.ucdavis.edu/curiosity/news/youtube-video-recommendations-lead-more-extremist-content-right-leaning-users-researchers) |
| Unlabeled / Poorly Labeled Data | Incorrect, biased, or offensive labels can propagate errors, biases, or harmful outcomes in downstream models; may require costly dataset rework. | Producer | [MIT’s withdrawal of “80 Million Tiny Images” dataset](https://venturebeat.com/ai/mit-takes-down-80-million-tiny-images-data-set-due-to-racist-and-offensive-content/) |
| Malware or Malicious Code | Trojans or backdoors hidden in training data or dependencies can compromise models, infrastructure, or end-user systems. | Producer | [PyTorch-nightly dependency compromise](https://pytorch.org/blog/compromised-nightly-dependency/) |
| Regionally Restricted or Illegal Content | Material that is banned or heavily regulated in certain countries (e.g., Nazi symbols in Germany, certain religious or political content in other jurisdictions). Violations can result in fines, local bans, or legal actions. | Producer & Deployer | [Germany’s ban on Nazi symbols in games](https://www.bbc.com/news/technology-45149304) |
| Child Sexual Exploitation (CSE) Material | Universally illegal. Even inadvertent inclusion in datasets can lead to severe criminal penalties; immediate takedown notices, public outcry, and possible prosecution. | Producer & Deployer | [Platform struggles with CSE detection](https://www.arxiv.org/pdf/2503.00433) |
| Locally Censored or Regulated Content | Many regions impose censorship on specific political, religious, or cultural information (e.g., speech critical of government, certain religious references). Failing to comply can lead to shutdowns or blocking within a region. | Deployer | [Google facilitated Russia and China’s censorship requests](https://www.theguardian.com/world/2025/feb/15/google-helped-facilitate-russia-china-censorship-requests) (coverage of broader content restrictions) |

In addition, a few good sources to cross-reference definitions and categories include the Trust and Safety Professional Association's (TSPA) [abuse types page](https://www.tspa.org/curriculum/ts-fundamentals/policy/abuse-types/). CSE detection, for example, may have different degrees of feasibility depending on if it is text or multimodal. (Not a legal opinion...) "Grooming" text is not necessarily treated the same way as CSAM media and thus may be somewhat easier to detect without having to get licenses to access databases of known CSAM hashes. (Source: @julietshen)

See also the [Appendix](#appendix).

## Requirements (Draft)

Most of these requirements require further details to be defined.

> [!NOTE]
> "DG" - Data Governance

| ID    | Requirement | Rationale |
| :---- | :---------- | :-------- |
| DG:1  | For each dataset, identify and track the allowed public information for it. | Consortium participants need the ability discover datasets without exposing restricted metadata or data. |
| DG:2  | Track dataset provenance and lineage from source discovery and acquisition through preparation stages and use in pre-training, post-training, and evaluation purposes. | Training and certification claims need evidence that can be traced back to source and processing history. |
| DG:3  | Capture rights, consent, license, residency, retention, and allowed-use constraints as structured metadata. | Governance decisions cannot rely on prose scattered across documents or private notes. |
| DG:4  | Track processing state and quality signals for each artifact. | The project needs to distinguish raw, cleaned, deduplicated, filtered, tokenized, held-out, and evaluation-ready data. |
| DG:5  | At no stage in a data processing pipeline can any restrictions on the input data be relaxed. | It would defeat the purpose of supporting restricted-use datasets if any steps in the process of using them undermined those restrictions. |
| DG:6  | Support local-only and pointer-based participation. | Some participants can expose metadata, hashes, manifests, or attestations while keeping raw data inside their sovereign boundary. |
| DG:7  | Produce audit evidence at every data-related _event_ and with multiple visibility tiers. | Public summaries, consortium-private review artifacts, and participant-private logs must be separable. |
| DG:8  | Integrate with policy and release-gate checks. | Data-use constraints should be enforceable by downstream training, evaluation, and certification workflows. |
| DG:9  | Preserve change history for datasets, metadata, processing jobs, and approvals. | Reviewers need to know which version of a dataset supported a model or claim. |
| DG:10 | Use portable schemas and interfaces. | Tapestry should avoid forcing all participants into one storage or catalog system. |

## Appendix

While this is a requirements document, here are a few example tools for reference purposes. Tool decisions are left to the data engineering team.

* [ThreatExchange](https://github.com/facebook/ThreatExchange/) - a Facebook enforcement tool set, including a [hash matcher](https://github.com/facebook/ThreatExchange/tree/main/hasher-matcher-actioner) that makes it easier to match data against known illegal content.
* [Social Intel](https://www.socialintel.io/) - a toolkit that address a practical gap, where some unwanted data may only be detectable at the content level, but social media datasets also need engagement-based signals — bot likelihood, author verification, cross-platform de-duplication, etc. to catch adversarial content that looks clean in isolation. Social Intel scores every posts across 25 quality checks before delivery, including bot detection, toxicity scoring, and PII filtering. This filtering can run upstream, so the dataset ships clean rather than requiring downstream filtering. (Source: @hexsyro)
