# TAPESTRY Vision

A tapestry is made of many distinct threads — each sovereign, each with its own color and origin — woven together into something stronger and more complete than any single thread could be alone. That is the project.

---

## The Two Problems

Tapestry exists because two structural failures in today's AI landscape must be solved simultaneously. Solving only one produces a system that fails in the market.

### Problem A — People will not use models that are subpar

The leading AI models were trained predominantly on English-language, Western-centric data. They perform materially worse on:

- **Culturally-specific tasks**: Medical diagnosis based on local disease patterns, educational content aligned with local pedagogy, agricultural advice grounded in local crop conditions.
- **Non-English and minority languages**: Not via translation layers, but genuine native comprehension and generation.
- **Domain tasks requiring sovereign data**: Patient records, national health surveillance, government administrative datasets, and educational outcome databases are legally restricted from leaving their countries of origin. Centralized commercial models cannot legally access this data and therefore cannot learn from it.

A healthcare AI that a French doctor does not trust for French patients will not be adopted, regardless of its benchmark scores. **An AI that does not win adoption has failed its mission, regardless of how sovereignty-compliant it is.**

### Problem B — Countries, enterprises, and individuals need AI that cannot be taken away

Every major AI system in widespread use today is controlled by a small number of private corporations. That access can be revoked by licensing changes, geopolitical sanctions, acquisition, bankruptcy, or provider decisions to discontinue a market. Nations cannot build sovereign digital infrastructure on AI they do not control. Enterprises cannot build critical operations on AI their vendors can switch off.

**The contract Tapestry makes to every participant: this AI is yours. It knows your context, speaks your language, reflects your values, and cannot be taken away.**

---

## The Performance Thesis

Sovereignty is not a trade-off against performance — it is the source of it.

Three structural advantages sovereign nodes<sup>[1](#footnote-1)</sup> have that no centralized model can replicate:

| Advantage | Why centralized models can't replicate |
|---|---|
| **Public-sector data access** | Healthcare, education, and governance datasets are legally restricted to national jurisdictions. |
| **Cultural alignment depth** | Community-participatory constitutional AI captures cultural variation that one-size-fits-all training cannot. |
| **Domain specialization** | Organizations won't share proprietary data with centralized providers; on-premise specialization is inaccessible to cloud models. |

<a id="#footnote-1"></a>

<sup>1</sup>: _Compute and storage nodes that can either participate in the distributed training processes or run standalone. See [here](../tapestry-reference/ARCHITECTURE.md)._

Initial performance targets:

- **≥15%** over generic centralized models on domain-specific, culturally-situated tasks (healthcare, education, agriculture, governance, climate)
- **≥20%** on cultural task benchmarks (native language comprehension, values alignment, cultural appropriateness)
- **<1%** culturally inappropriate outputs across all sovereign variants

---

## Three Levels of Sovereignty

### Level 1 — National Sovereignty

*For governments and public-sector institutions.*

| Guarantee | Specification |
|---|---|
| Data residency | All data processed within the nation's physical jurisdiction; hardware-level enforcement |
| Exit capability | Complete model + data export in <72 hours, executable without any external coordination |
| Island mode | Node operates fully independently with zero external network dependencies |
| Legal compliance | National legal framework (GDPR, APPI, etc.) configured in the nation's [30% layer](#seventy-thirty) |

### Level 2 — Socio-Cultural Sovereignty

*For communities, indigenous groups, and language communities.*

| Guarantee | Specification |
|---|---|
| Community-owned constitutional AI | All values, constraints, and behavioral rules configured by the community; nothing imposed by the global layer |
| Sacred knowledge protection | Protected knowledge domains enforced at the infrastructure level, not by policy alone |
| Community Review Board | Binding authority to configure, audit, and pause the constitutional AI layer |
| Data consent and revocation | Explicit community-level consent; revocation triggers defined retraining procedures |

### Level 3 — Industrial Sovereignty

*For enterprises, hospitals, schools, and cooperatives.*

| Guarantee | Specification |
|---|---|
| On-premise deployment | No runtime dependency on external cloud services or the federated network |
| Proprietary data protection | Fine-tuning on proprietary data with cryptographic proof it never leaves the enterprise boundary |
| Variant generation time | Domain-specific sovereign variant generated in <72 hours on enterprise-grade hardware |

---

## The Model Hierarchy

```
TAPESTRY-GLOBAL          Apache 2.0, foundation, general-purpose baseline
    └── Regional         EU, APAC, etc. — regional data and configuration
        └── National     TAPESTRY-FR, TAPESTRY-JP — national public-sector data + constitutional AI
            └── Entity   TAPESTRY-HOSPITAL-LYON — entity-specific fine-tuning, on-premise
```

Users can start at TAPESTRY-GLOBAL (no sovereignty overhead) and migrate upward as requirements evolve, without rebuilding their application.

---

<a id="seventy-thirty"></a>

## The 70/30 Architecture Principle

The architecture maintains a strict separation:

**Universal infrastructure (70%)** — Identical across all nations. Federated training protocol, privacy-preserving aggregation, Byzantine fault tolerance, audit logging, exit procedures, sovereignty verification. No hard-coded cultural assumptions.

**National configuration (30%)** — Fully owned and controlled by the sovereign node operator. Constitutional AI principles, language priorities, sacred knowledge boundaries, legal framework compliance. Configured in structured, human-readable YAML — not embedded in shared code.

This separation is non-negotiable. Any design that bleeds national assumptions into the universal layer fails the architecture.

---

## What Tapestry Is Not

- Not competing with GPT-4 (or equivalent) on general-purpose English academic benchmarks.
- Not a single centralized AI product. Tapestry will never be a monolithic vendor offering.
- Not targeting consumer chat applications. The focus is high-stakes domain applications.
- Not claiming AGI or superintelligence.
- Not dictating AI governance to non-sovereign entities.

---

## Success Metrics

| Metric | Month 6 | Month 18 | Month 36 |
|---|---|---|---|
| Sovereign nodes operational | 2 | 7+ (all G7, plus...) | 50+ |
| TAPESTRY-GLOBAL downloads | First release | 500K | 5M+ |
| Community derivative models | — | 100+ | 10,000+ |
| Domain performance vs. best centralized model | Baseline established | +15% | Sustained +15% |
| Cultural appropriateness rate | Baseline set | >99% | >99% |
| Languages supported | 5 (G7 official, plus...) | 100 | 1,000 |
| Exit verified in <72 hours | 2 nodes | 7+ nodes | 50+ nodes |

---

## Work Group Map

| What needs defining | Who defines it |
|---|---|
| Data sovereignty requirements | [Data Requirements Work Group](../work-groups/data-requirements/) |
| Federated training requirements | [Model Training Requirements Work Group](../work-groups/model-training-requirements/) |
| Evaluation requirements | [Evaluation Requirements Work Group](../work-groups/evaluation-requirements/) |
| Infrastructure requirements | [Infrastructure Requirements Work Group](../work-groups/infrastructure-requirements/) |
| Data infrastructure implementation | [Data Engineering Work Group](../work-groups/data-engineering/) |
| Training stack implementation | [Model Training Engineering Work Group](../work-groups/model-training-engineering/) |
| Evaluation tooling | [Evaluation Engineering Work Group](../work-groups/evaluation-engineering/) |
| Sovereign node infrastructure | [Infrastructure Engineering Work Group](../work-groups/infrastructure-engineering/) |

For detailed requirements, acceptance criteria, and milestones, see the [PRD](PRD.md).
