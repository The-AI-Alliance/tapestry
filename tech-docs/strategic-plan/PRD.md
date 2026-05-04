# TAPESTRY — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-05-03  
**Authority:** OPAN Leadership — LeCun (Chief Scientist), Nguyen (Chief Architect), Annunziata (AI Alliance Chair, Program & Policy)  
**Status:** Draft for leadership review

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Product Vision](#2-product-vision)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [Target Users](#4-target-users)
5. [Performance Requirements](#5-performance-requirements)
6. [Sovereignty Requirements](#6-sovereignty-requirements)
7. [Architecture Requirements](#7-architecture-requirements)
8. [Governance Requirements](#8-governance-requirements)
9. [Data Requirements](#9-data-requirements)
10. [Open-Source and Ecosystem Requirements](#10-open-source-and-ecosystem-requirements)
11. [Success Metrics](#11-success-metrics)
12. [Milestones and Timeline](#12-milestones-and-timeline)
13. [Risks and Mitigations](#13-risks-and-mitigations)
14. [Open Questions](#14-open-questions)
15. [References](#15-references)

---

## 1. Problem Statement

Two structural failures define today's AI landscape. Both must be solved simultaneously, because solving only one produces a system that fails in the market.

### Problem A — People will not use models that are subpar

The current generation of leading AI models (GPT-4, Gemini, Qwen, and equivalents) were trained predominantly on English-language, Western-centric internet data. They perform well on Western academic benchmarks and general-purpose English tasks. They perform materially worse on:

- **Culturally-specific tasks**: Medical diagnosis based on local disease patterns, educational content aligned with local pedagogy, agricultural advice grounded in local crop conditions.
- **Non-English and minority languages**: Not via translation layers, but genuine native comprehension and generation.
- **Domain tasks requiring sovereign data**: Patient records, national health surveillance, government administrative datasets, and educational outcome databases are legally restricted from leaving their countries of origin. Centralized commercial models cannot legally access this data and therefore cannot learn from it.
- **Values-aligned reasoning**: AI that imposes one culture's moral assumptions on another is not just inaccurate — it is rejected by the communities it is meant to serve.

A healthcare AI that a French doctor does not trust for French patients will not be adopted, regardless of its general-purpose benchmark scores. A farming assistant that does not understand Vietnamese rice cultivation will sit unused. **An AI that does not win adoption has failed its mission, no matter how sovereignty-compliant it is.**

### Problem B — Countries, enterprises, and individuals need and deserve access to AI they know cannot be taken away from them

Every major AI system in widespread use today is controlled by a small number of private corporations headquartered in the United States or China. Governments, hospitals, schools, and enterprises that depend on these systems have no guarantee of continued access. That access can be revoked by:

- Licensing terms changed unilaterally by the provider
- Geopolitical sanctions or trade restrictions
- Corporate acquisition, bankruptcy, or strategic pivot
- Data export rules that make cross-border AI use illegal
- Provider decisions to discontinue a product or market segment

This is not a theoretical risk. It is the defining structural vulnerability of centralized AI. Nations cannot build sovereign digital infrastructure — healthcare systems, educational platforms, public administration — on AI they do not control. Enterprises cannot build critical industrial operations on AI their vendors can switch off. And the world's 7+ billion people who are not citizens of the US or China should not have to accept that their cultural identity, language, and values are second-class inputs to AI systems designed for someone else's context.

**The implied contract TAPESTRY makes to every user: this AI is yours. It knows your context, speaks your language, reflects your values, and cannot be taken away.**

---

## 2. Product Vision

TAPESTRY is an open-source, federated AI platform that delivers frontier-class performance — specifically in healthcare, education, agriculture, governance, and climate — through a structural advantage that centralized models cannot replicate: access to sovereign public-sector data and deep cultural alignment. It simultaneously guarantees irrevocable, verifiable, exit-capable sovereignty to every participating nation, cultural community, and enterprise.

The platform is organized around three interlocking levels of sovereignty:

| Level | Name | Who it serves | Core guarantee |
|---|---|---|---|
| 1 | **National Sovereignty** | Governments and public institutions | Data never leaves the nation's borders; node operates under national law; complete exit in <72 hours |
| 2 | **Socio-Cultural Sovereignty** | Communities, indigenous groups, language communities | AI reflects the community's own values; sacred knowledge is protected; community owns its constitutional AI |
| 3 | **Industrial Sovereignty** | Enterprises, hospitals, schools, cooperatives | On-premise deployment; proprietary data never exposed externally; domain-specific optimization unachievable by generic models |

These three levels are not in tension with performance — they are the source of it. Sovereign public-sector data is inaccessible to commercial providers. Cultural alignment produces outputs that are trusted and adopted. Domain specialization produces accuracy that generalist models cannot match. **Sovereignty is the performance strategy.**

---

## 3. Goals and Non-Goals

### 3.1 Primary Goals (must achieve)

**G1 — Frontier-class performance in target domains**  
TAPESTRY sovereign variants must match or exceed the best available centralized model (GPT-4 class) on domain-specific, culturally-situated tasks in healthcare, education, agriculture, governance, and climate. "Frontier" means the model is the best available choice for its target users, not that it wins general academic benchmarks. A model that wins benchmarks but loses adoption has failed.

**G2 — Irrevocable three-dimensional sovereignty**  
Every participating entity — nation, community, or enterprise — must be able to verify at any time that:
- Their data has not left their jurisdiction
- Their node can operate fully independently of all other nodes
- They can perform a complete, verified exit (full model + data export) in under 72 hours
- No constitutional AI values have been imposed on them without their consent

### 3.2 Secondary Goals (should achieve)

**G3 — Open, vibrant ecosystem**  
Foundation models released under Apache 2.0. Target: 5M+ downloads and 10,000+ community-derived models within 36 months (LLaMA ecosystem as benchmark).

**G4 — Multi-stakeholder governance with no single point of control**  
No nation, corporation, or individual can unilaterally block, redirect, or revoke TAPESTRY for any participant.

**G5 — Scalable federated infrastructure**  
Architecture must support 7 initial G7 nodes scaling to 1,000+ sovereign nodes globally, while maintaining gradient sync latency under 5 minutes.

**G6 — Measurable societal impact**  
Documented, independently verified improvements in real-world outcomes in target sectors by Month 36.

### 3.3 Non-Goals

- **Not** competing with GPT-4 on general-purpose English academic benchmarks. Competitive is sufficient; supremacy is not the goal.
- **Not** a single centralized AI product. TAPESTRY will never be deployed as a monolithic vendor offering.
- **Not** targeting consumer chat applications. The focus is on high-stakes domain applications where sovereignty and cultural accuracy matter.
- **Not** claiming AGI or superintelligence. LeCun's own UN briefing frames superintelligence as 10–20 years away; TAPESTRY targets appropriately-scaled AI for near-term societal benefit.
- **Not** dictating AI governance to non-sovereign entities (corporations, individuals). Governance framework applies to sovereign participants; it does not impose regulation on the broader industry.
- **Not** replacing existing AI systems that adequately serve their users. TAPESTRY complements existing AI where sovereignty and cultural accuracy are not critical.

---

## 4. Target Users

### Tier 1 — National Governments and Public-Sector Institutions

**Who:** Ministries of health, education, agriculture, and finance; national AI agencies; public research institutions; national security bodies.

**Core need:** AI trained on their own public-sector data (patient records, educational outcomes, governance logs), operating under their own legal framework, with no dependence on foreign technology companies.

**Key pain today:** Critical public-sector data cannot legally leave national borders, so no commercial AI provider can train on it. Governments are therefore forced to choose between (a) using inferior AI that lacks their data or (b) exporting sensitive citizen data in violation of national law.

**What TAPESTRY gives them:** A sovereign node that trains on their data in-country, contributes encrypted learning to the global model without exposing raw data, and can be disconnected and operated independently at any time.

**Adoption criterion:** Government IT teams can deploy a working sovereign node in under 3 commands from the reference implementation. The sovereignty guarantee must be machine-verifiable, not trust-based.

### Tier 2 — Cultural and Linguistic Communities

**Who:** Indigenous knowledge custodians, regional language communities, religious and civil society organizations, minority cultural groups.

**Core need:** AI that speaks their language natively (not via translation), reflects their values and worldview, and does not expose sacred or sensitive knowledge to extraction by external systems.

**Key pain today:** All major AI systems encode dominant-culture assumptions. They perform poorly in minority languages, misrepresent cultural concepts through translation layers, and treat indigenous knowledge as freely extractable training data.

**What TAPESTRY gives them:** A constitutional AI layer they define and own, with explicit protection for sacred knowledge domains, and participation in the governance of any AI trained on their data.

**Adoption criterion:** Community cultural review board can configure, validate, and audit the constitutional AI layer without requiring engineering expertise. Sacred knowledge boundaries are enforced at the infrastructure level, not by policy alone.

### Tier 3 — Enterprises and Industrial Organizations

**Who:** Hospital networks, regional health systems, educational institutions, agricultural cooperatives, manufacturing companies, financial institutions.

**Core need:** Domain-specialized AI fine-tuned on their own proprietary data, deployed on their own infrastructure, with verifiable guarantees that proprietary data is never exposed externally.

**Key pain today:** Generic models are not specialized enough for industrial precision tasks. Fine-tuning on proprietary data with cloud providers creates unacceptable data exfiltration risk. On-premise deployment of state-of-the-art models requires prohibitive infrastructure investment.

**What TAPESTRY gives them:** Industrial sovereignty — on-premise deployment capability, domain-specific fine-tuning on proprietary data with no external exposure, and performance advantages from specialization that generic models cannot replicate.

**Adoption criterion:** Enterprise can generate a domain-specific sovereign variant in under 72 hours. Performance must demonstrably exceed generic models on the enterprise's own evaluation tasks.

### Tier 4 — Global Developer and Research Community

**Who:** AI researchers, open-source developers, academic institutions, independent builders.

**Core need:** A high-quality, openly licensed foundation model with a strong general baseline, active community governance, and an ecosystem that rewards contribution.

**What TAPESTRY gives them:** TAPESTRY-GLOBAL — Apache 2.0 licensed, competitive with leading open-source models on general tasks, immediately downloadable, and improvable by the community.

**Adoption criterion:** TAPESTRY-GLOBAL scores within 5–10 points of the best open-source models on MMLU and HumanEval. Community contribution pathway is documented and low-friction.

---

## 5. Performance Requirements

The core thesis: **TAPESTRY wins performance through data advantages and alignment depth that centralized models structurally cannot replicate — not through raw parameter count.**

Three unique performance advantages:

| Advantage | Source | Why centralized models can't replicate |
|---|---|---|
| **Public-sector data access** | National sovereignty (Level 1) | Healthcare, education, governance datasets are legally restricted to national jurisdictions. Commercial entities cannot access them. |
| **Cultural alignment depth** | Socio-cultural sovereignty (Level 2) | Community-participatory constitutional AI captures thousands of cultural variations. One-size-fits-all approaches cannot. |
| **Domain specialization** | Industrial sovereignty (Level 3) | Organizations won't share proprietary data with centralized providers. On-premise specialization is inaccessible to cloud models. |

### PR-1 — Domain performance (Must)

In the five target domains, TAPESTRY sovereign variants must meet or exceed the best available centralized model on culturally-situated domain benchmarks:

- **Healthcare**: Diagnostic accuracy for region-specific conditions and local clinical guidelines
- **Education**: Curriculum-aligned learning content generation and assessment in native language
- **Agriculture**: Crop yield prediction using local knowledge, climate, and soil datasets
- **Governance**: Public-service document processing aligned with national legal frameworks
- **Climate**: Geographically-specific adaptation modeling

Initial target: **≥15% performance gain** on culturally-situated tasks vs. equivalent generic centralized models. Benchmarks to be defined by the Evaluation Work Group and ratified by the Governance Committee.

### PR-2 — General-purpose baseline (Must)

TAPESTRY-GLOBAL must score **within 5–10 points** of the leading open-source model of comparable parameter count on MMLU and HumanEval. Users selecting TAPESTRY-GLOBAL must have a credible general-purpose foundation model — not a compromise.

### PR-3 — Cultural task supremacy (Must)

On culturally-specific evaluation suites (native language comprehension, cultural appropriateness scoring, values alignment), sovereign variants must **outperform all alternatives by ≥20%**. This is the category TAPESTRY is designed to dominate.

### PR-4 — Inference latency overhead (Should)

The constitutional AI enforcement layer must add **<5ms latency overhead** per inference. Sovereignty must not impose a performance tax users will notice.

### PR-5 — Hallucination rate (Must)

TAPESTRY models must not hallucinate at higher rates than open-source models of equivalent parameter count. The JEPA architectural track is expected to improve on this baseline over time by reducing reliance on generative pattern completion.

### PR-6 — Cultural appropriateness (Must)

Culturally inappropriate outputs must occur at a rate of **<1%** across all sovereign variant evaluations, as assessed by community cultural review boards.

---

## 6. Sovereignty Requirements

### 6.1 National Sovereignty (Level 1)

**SR-1 — Data residency (Must)**  
All data processed by a sovereign node must remain physically within the node operator's jurisdiction. Geographic enforcement must be implemented at the hardware or network level, not solely by policy. Hardware attestation must provide cryptographic proof of data location to auditors without requiring trust in the node operator's self-reporting.

**SR-2 — Verified exit capability (Must)**  
Every sovereign node operator must be able to perform a complete, verified exit — comprising full model export, full training data export, and complete immutable audit trail — within **72 hours**. Exit must be:
- Executable without coordination from any other node or central authority
- Machine-verifiable (completeness checked by automated procedures)
- Documented and testable at any time (not only at exit)

**SR-3 — Independence from external dependencies (Must)**  
Sovereign nodes must be capable of operating in full isolation from the federated network — "island mode" — with zero external network dependencies. This includes model inference, constitutional AI enforcement, and audit logging. Nodes that cannot survive disconnection have not achieved sovereignty.

**SR-4 — Compliance with national law (Must)**  
The platform architecture must support operation under any national legal framework without requiring changes to the universal 70% infrastructure layer. National legal requirements (GDPR, APPI, and equivalents) are configured in the national 30% layer, not embedded in shared code.

### 6.2 Socio-Cultural Sovereignty (Level 2)

**SR-5 — Community-owned constitutional AI (Must)**  
Every sovereign node must implement a constitutional AI layer configured entirely by the node's community or government. No values, constraints, or behavioral rules are imposed by the global coordination layer. Constitutional principles are expressed in a structured, auditable, human-readable format (YAML-based configuration). Communities must be able to read, modify, and audit their own constitutional configuration without engineering support.

**SR-6 — Sacred knowledge boundaries (Must)**  
Constitutional AI configuration must include the ability to designate protected knowledge domains — categories of community knowledge explicitly excluded from training data, model outputs, and cross-node knowledge sharing. Enforcement must be infrastructure-level (not policy-level alone): protected domains must be blocked by the training pipeline and inference layer, not merely by guidelines.

**SR-7 — Community participation in governance (Must)**  
Each sovereign node must operate a Cultural Review Board — a community-governed body responsible for validating constitutional AI configuration, approving use of community data, and auditing model outputs for cultural appropriateness. Cultural Review Boards must have binding authority to pause or modify their node's constitutional AI configuration.

**SR-8 — Data consent and revocation (Must)**  
All training data contributed by cultural communities must be collected with explicit, documented, community-level consent. Communities must retain the right to revoke their data contribution at any time, triggering a defined retraining procedure that removes the revoked data's influence from the model.

### 6.3 Industrial Sovereignty (Level 3)

**SR-9 — On-premise deployment (Must)**  
Every sovereign variant must be deployable entirely on the enterprise's own infrastructure, with no runtime dependency on external cloud services or the federated training network. Enterprises must be able to air-gap their deployment after initial setup.

**SR-10 — Proprietary data protection (Must)**  
Enterprises must be able to fine-tune sovereign variants on their proprietary data without that data ever leaving their infrastructure boundary. The fine-tuning process must be executable entirely locally, with cryptographic proof of data containment available to enterprise auditors.

**SR-11 — Variant generation time (Should)**  
An enterprise must be able to generate a new domain-specific sovereign variant — starting from TAPESTRY-GLOBAL, applying constitutional AI configuration, and running domain fine-tuning — in **under 72 hours** on standard enterprise-grade hardware.

### 6.4 Cross-Level Sovereignty

**SR-12 — Federated privacy in training (Must)**  
All federated gradient sharing between nodes must use **homomorphic encryption** and **differential privacy (ε < 1.0 per training round)**. Zero raw data is shared between nodes at any point in the training lifecycle. Implementation must be independently validated by MBZUAI or equivalent external privacy research institution.

**SR-13 — Byzantine fault tolerance (Must)**  
The federated training protocol must tolerate up to **one-third of participating nodes** acting maliciously, failing, or being compromised — without corrupting the integrity of the global model update. This guarantee must be maintained as the network scales to 1,000 nodes.

**SR-14 — Immutable audit trail (Must)**  
All training events, model updates, data accesses, constitutional AI changes, and governance decisions must be recorded in an immutable, cryptographically verifiable audit log at each sovereign node. Audit logs must be exportable as part of the exit procedure and must be independently auditable without access to the node's live systems.

---

## 7. Architecture Requirements

### AR-1 — Federated training protocol (Must)

TAPESTRY must implement a distributed training protocol supporting asynchronous gradient aggregation across a minimum of 7 nodes, scaling to 1,000 nodes, with:
- Gradient sync latency **<5 minutes** at production scale
- End-to-end encryption for all inter-node gradient communication
- Secure aggregation (no node's raw gradients visible to any other node or coordinator)
- Asynchronous update tolerance (24–48 hour sync window for slower nodes)

### AR-2 — 70/30 separation principle (Must)

The architecture must maintain a strict separation between:
- **Universal infrastructure (70%)**: Federated training protocol, privacy-preserving aggregation, Byzantine fault tolerance, audit logging, exit procedures, sovereignty verification. Identical across all nations. No hard-coded cultural assumptions.
- **National configuration (30%)**: Constitutional AI principles, language priorities, sacred knowledge boundaries, legal framework compliance, cultural review board interfaces. Fully owned and controlled by the sovereign node operator.

This separation is non-negotiable. Any design that bleeds national assumptions into the universal layer, or that puts sovereignty enforcement in the configuration layer, fails this requirement.

### AR-3 — Sovereign node reference implementation (Must)

A working sovereign node must be deployable from the reference implementation using **3 commands or fewer**. The reference implementation must include:
- Core sovereignty enforcement (`SovereignNode` class)
- Nation-agnostic federated training client
- Example national configuration for each initial node (France, Japan, Canada, South Korea, Vietnam)
- Sovereignty verification scripts (data residency, exit capability, independence)
- MBZUAI validation hooks for privacy certification

### AR-4 — Model hierarchy (Must)

TAPESTRY must maintain a clear four-level model hierarchy:

1. **TAPESTRY-GLOBAL** — Open-source foundation model, trained on aggregated federated updates from all nodes. Available immediately for users without sovereignty requirements. Apache 2.0.
2. **Regional variants** (e.g., TAPESTRY-EU, TAPESTRY-APAC) — Fine-tuned with regional data and configuration.
3. **National variants** (e.g., TAPESTRY-FR, TAPESTRY-JP) — Fine-tuned with national public-sector data and national constitutional AI.
4. **Entity variants** (e.g., TAPESTRY-HOSPITAL-LYON) — Fine-tuned with entity-specific data on entity-owned infrastructure.

Users must be able to start at Level 1 (no sovereignty overhead) and migrate to higher levels as requirements evolve, without rebuilding their application.

### AR-5 — Dual architecture track (Should)

TAPESTRY must support two complementary architectural tracks in parallel:

- **Track 1 — Generative (Transformer-based)**: Production-ready, immediately deployable for language tasks (clinical notes, educational content, governance documents, cultural knowledge Q&A).
- **Track 2 — JEPA (Joint Embedding Predictive Architecture)**: Under development, targeting predictive and physical-world modeling tasks (crop yield prediction, climate adaptation, epidemiological forecasting). Expected to reduce hallucination rate and improve efficiency relative to generative models.

Both tracks participate in federated training. Nodes select the appropriate architecture for their use case. The federated protocol must support heterogeneous architectures without requiring all nodes to use the same model type.

### AR-6 — Scale validation (Must)

The federated training protocol must be designed for and validated at **1,000-node scale** before claiming production readiness. Validation must include:
- Gradient sync latency <5 minutes at 1,000 nodes
- Byzantine fault tolerance at 1,000-node scale (up to 333 malicious nodes)
- Exit procedure completable in <72 hours at any network size

---

## 8. Governance Requirements

### GR-1 — Governance Committee (Must)

A permanent TAPESTRY Governance Committee must be established at or before the G7 Summit (June 2026). Composition:
- **Technical co-chair**: Chief Scientist (LeCun)
- **Implementation co-chair**: Chief Architect (Nguyen)
- **Coordination chair**: AI Alliance Chair, Program & Policy (Annunziata)
- **Rotating G7 representative**: One per G7 member on a defined rotation
- **UN Observer**: Representing global public interest
- **Cultural advisors**: Nominated by Cultural Review Boards

No single member or nation holds veto power. Technical decisions require Chief Scientist approval. Governance decisions require a majority of principals. Deployment decisions require all three principals.

### GR-2 — Cultural Review Boards (Must)

Each sovereign node must establish a Cultural Review Board before the node enters production. Boards have binding authority to:
- Configure and audit the node's constitutional AI layer
- Approve use of community data in training
- Pause model outputs pending cultural review
- Trigger data revocation and retraining

Boards must include at minimum one community elder or cultural authority, one technical representative, and one independent observer.

### GR-3 — Transparent decision record (Must)

All governance decisions — technical, deployment, policy — must be published in a publicly accessible, immutable decision log. Decisions must include the rationale, the parties consulted, any dissents, and the outcome.

### GR-4 — Opt-in federation (Must)

Participation in the federated training network must be voluntary and revocable. Any sovereign node may disconnect from federation at any time without penalty, approval, or prior notice. Disconnected nodes continue to operate with their existing model weights; they simply stop contributing to and receiving global updates.

### GR-5 — No single-nation control (Must)

The governance framework must be structured so that no single nation, corporation, or individual can:
- Block another node's participation in the network
- Force disconnection of any node from the network
- Modify another node's constitutional AI configuration
- Access another node's training data or model weights without explicit authorization

---

## 9. Data Requirements

### DR-1 — Cultural coverage (Must)

Phase 1 (Month 6): All G7 official languages (English, French, German, Japanese, Italian) fully supported, with major dialects included. Minimum 15% of training data from underrepresented cultural groups.

Phase 2 (Month 18): 100 languages supported. Minimum 100,000 cultural samples per language.

Phase 3 (Month 36): 1,000 languages supported. 100M+ total cultural samples across the network.

### DR-2 — Public-sector data access (Must)

The sovereignty framework must include MOU templates and data partnership structures enabling sovereign nodes to legally access and train on public-sector datasets (healthcare records, educational outcome data, government administrative data) within their jurisdiction, under their national data protection law. Access agreements must be auditable and revocable.

### DR-3 — Data consent (Must)

All training data contributed by cultural communities must be collected under explicit, documented, community-level consent. Individual-level consent mechanisms are insufficient for community knowledge. Consent must specify:
- What data is contributed
- How it is used (training, evaluation, distribution)
- Whether it is shared in federated updates (even in encrypted form)
- How it can be revoked

### DR-4 — Data revocation (Must)

The training pipeline must support community data revocation — the ability for a contributing community to withdraw their data, triggering removal of that data's influence from the model through documented retraining procedures. Revocation must be technically enforceable, not solely contractual.

### DR-5 — Bias and representation auditing (Should)

An automated bias detection system must continuously identify representation gaps in training data and flag them to the relevant Cultural Review Boards. Underrepresentation of a community in the training data must trigger an active outreach process, not passive acceptance.

---

## 10. Open-Source and Ecosystem Requirements

### OS-1 — Permissive licensing (Must)

- Foundation model weights and code: **Apache 2.0**
- Training data: **CDLA-2.0** (Community Data License Agreement)
- Documentation: **CC BY 4.0**

No copyleft or restrictive licensing. Any developer or institution must be able to use, modify, and redistribute TAPESTRY without license fees or restrictions beyond attribution.

### OS-2 — Derivative model support (Must)

TAPESTRY-GLOBAL must be designed to support rapid derivative model creation. Target: 100+ community derivatives within 6 months of first release, 10,000+ within 36 months. Architecture, tooling, and documentation must be optimized for derivative creation, not just use.

### OS-3 — Community contribution pathway (Must)

A documented, low-friction process for community contributions — model improvements, cultural data, evaluation benchmarks, constitutional AI configurations — must be in place before the public release of TAPESTRY-GLOBAL. The process must not require institutional affiliation or formal partnership.

---

## 11. Success Metrics

| Metric | Phase 1 (Month 6) | Phase 2 (Month 18) | Phase 3 (Month 36) |
|---|---|---|---|
| Sovereign nodes operational | 2 (France, Japan) | 7 (all G7) | 50+ |
| TAPESTRY-GLOBAL downloads | First release | 500K | 5M+ |
| Community derivative models | — | 100+ | 10,000+ |
| Domain performance vs. best centralized model | Demo benchmark established | +15% on target domain tasks | Sustained +15%, cultural tasks +20%+ |
| Cultural appropriateness rate | Baseline set | >99% | >99% |
| Cultural samples in network | 100K per language | 1M per language | 100M total |
| Languages supported | 5 (G7 official) | 100 | 1,000 |
| Exit verified in <72 hours | 2 nodes | 7 nodes | 50+ nodes |
| Cultural Review Boards operational | 2 | 7 | 50+ |
| Entities demonstrating full sovereignty | 2 | 7 | 50+ |
| Documented societal impact deployments | 10 pilots | 100 | 1,000+ |
| Beneficiaries reached | Baseline | 1M | 100M |

---

## 12. Milestones and Timeline

```
Phase 0 — Foundation (Now – May 2026)
Phase 1 — G7 Launch (Jun – Dec 2026)
Phase 2 — Ecosystem Growth (Jan 2027 – Jun 2027)
Phase 3 — Planetary Scale (Jul 2027 – Dec 2027)
```

| Milestone | Target Date | Owner | Deliverable |
|---|---|---|---|
| Hardware partnerships signed (NVIDIA, AMD) | Mar 2026 | Yann LeCun | Signed MOUs or Letters of Intent |
| Technical specifications finalized | Mar 15, 2026 | Christopher Nguyen | ARCHITECTURE.md ratified |
| Governance Committee chartered | May 2026 | Anthony Annunziata | Charter + founding membership |
| G7 Summit announcement | Jun 2026 | Macron + Takaichi | Public multi-nation commitment |
| France sovereign node live | Jul 15, 2026 | Nguyen + France AI Commission | Production node, live public demo |
| Japan sovereign node live | Sep 15, 2026 | Nguyen + Japan node team | Production node, Asia-Pacific demo |
| TAPESTRY-GLOBAL Phase 1 released | Dec 2026 | LeCun + Nguyen | Apache 2.0 public release |
| 7 G7 nodes operational | Dec 2026 | Annunziata | Full G7 sovereign coverage |
| 100+ community derivative models | Month 18 | Open ecosystem | Community contribution milestone |
| Performance benchmark: +15% in target domains | Month 18 | Evaluation Work Group | Published benchmark results |
| 1,000+ sovereign variants | Month 36 | Annunziata | Global ecosystem milestone |
| 100M+ beneficiaries | Month 36 | Societal Impact team | Documented impact report |

---

## 13. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Frontier model performance gap is too large to close in target domains | Medium | Fatal (adoption failure) | Lead with domains where sovereign data access creates the largest gap (rural healthcare, regional agriculture); benchmark early; adjust scope before scaling |
| "Too French" perception undermines global adoption | Medium | High | Nation-agnostic 70/30 architecture; Japan and Canada nodes deployed alongside France; governance co-chaired by non-French nations; open documentation of nation-specific configs |
| Hardware partnership failure (NVIDIA, AMD) | Medium | High | Dual-track hardware strategy; AMD as independent path; EU hardware partnerships; cloud-sovereign Phase 1 fallback with path to hardware sovereignty in Phase 3 |
| National political opposition blocks G7 commitment | Medium | High | Frame G7 commitment as non-binding framework, not treaty; demonstrate working code before asking for political commitments; avoid requiring domestic legislative action for Phase 1 |
| Federated training produces worse models than centralized training | Low | High | Focus federated advantage on cultural and domain fine-tuning, not pre-training; use centralized compute for TAPESTRY-GLOBAL pre-training where possible; quantify federated contribution separately |
| Privacy breach in federated protocol | Low | Fatal (trust collapse) | Homomorphic encryption + differential privacy + Byzantine fault tolerance; mandatory MBZUAI independent validation before any production deployment; staged rollout with escalating node count |
| Community data consent revoked at scale | Low | Medium | Design for consent revocation in training pipeline from day 1; community agreements specify revocation procedures in advance; retraining procedures documented and tested |
| Governance committee gridlock | Medium | Medium | Pre-agreed decision escalation protocols; two-of-three principal leads sufficient for most decisions; dispute resolution process defined in charter before first operational disagreement |
| Sacred knowledge protection bypassed by inference attacks | Low | High | Infrastructure-level enforcement (not policy alone); red-team sacred knowledge boundaries as part of safety evaluation; community audit of protection mechanisms |
| Industrial tier adoption slower than expected (enterprises prefer cloud) | Medium | Medium | Lead with public-sector healthcare and education (highest sovereignty motivation); build ROI case on domain performance gains; offer cloud-sovereign bridge (Phase 1) before full on-premise |

---

## 14. Open Questions

1. **Benchmark governance**: Who selects and governs the culturally-situated benchmark suites that define "frontier performance in target domains"? The Evaluation Work Group must be constituted and chartered before Phase 1 deployment.

2. **JEPA production gating**: What are the measurable criteria that qualify a JEPA-architecture node for production federated training participation? This needs a formal gate definition before Phase 2.

3. **Cost accessibility for developing nations**: At what sovereign node deployment cost does participation become inaccessible to lower-income countries? What hardware subsidy, cloud-sovereign bridge, or tiered participation model closes this gap? The current G7 focus risks excluding the nations with the greatest sovereignty need.

4. **Data revocation at scale**: What is the technical protocol for model retraining after large-scale community data revocation? If 10% of training data from a major language is revoked, what is the retraining timeline and cost?

5. **Industrial tier business model**: What sustains the open-source foundation while enabling enterprise deployments at the scale and quality enterprises require? An unsustainable funding model is a sovereignty risk in itself.

6. **Pre-training vs. federated**: TAPESTRY-GLOBAL's pre-training is compute-intensive. At what stage of training does federated aggregation begin, and what is the centralized vs. federated contribution to the base model? This affects both performance claims and sovereignty claims.

7. **Regulatory harmonization**: How does TAPESTRY handle conflicting national laws — for example, two participating nations with incompatible data-sharing regulations that both want to contribute to the same global model update?

---

## 15. References

- LeCun, Y. UN Security Council Briefing S/PV.9821 (December 19, 2023)
- TAPESTRY Strategic Plan: `strategic-plan/` (aitomatic/aia-tapestry)
- AI Alliance Project Tapestry (public): https://events.thealliance.ai/tapestry
- AI Alliance Technical Repo: https://github.com/The-AI-Alliance/tapestry

---

*This PRD is a living document. Changes require review by OPAN Leadership. All design documents derived from this PRD must trace their requirements back to Section 3 (Goals) and resolve any conflicts before implementation begins.*
