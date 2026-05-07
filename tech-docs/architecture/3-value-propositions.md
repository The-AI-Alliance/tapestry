# Phase 3 — Value Proposition Mapping

*May 2026*

---

## Purpose

For each stakeholder layer, this document articulates what Tapestry specifically offers that the current ecosystem does not. Every value proposition must trace back to one or more pain points from Phase 2. If it doesn't address a documented failure, it is a feature in search of a problem.

This document also distinguishes between value that Tapestry can deliver on Day 1 (using existing open-weights models as a starting base) and value that requires the full consortium training infrastructure. The roadmap matters: participants will not wait years for a promise when they have problems today.

## Architectural Premise

Tapestry's training model is a **core-plus-sovereign architecture**: a frontier-competitive base model (initially adopted from existing open weights, eventually trained by the consortium) enriched by sovereign contributions — cultural alignment, domain expertise, institutional knowledge — from participating nodes. The ratio starts at roughly 80/20 centralized-to-distributed and shifts over time as the consortium's own training capacity matures.

This means Tapestry does not ask participants to accept a worse model for the sake of sovereignty. It starts with frontier-class general capability and adds sovereign value on top. The value proposition is additive, not substitutive.

---

## National

**VP-N1. Sovereignty without sacrificing capability.** ← addresses N4 (sovereign models nobody uses), N5 (frontier capital requirements)

Tapestry gives a nation a frontier-competitive model *and* sovereign control over its cultural alignment, domain specialization, and data governance — without requiring the $200M+ investment to train from scratch. The base model provides general capability. The sovereign layer provides the alignment and specialization that make it actually useful and adoptable domestically.

This is the core value proposition. Every sovereign AI initiative that built its own model and saw low adoption faced a false choice: capability or sovereignty. Tapestry eliminates that choice.

**VP-N2. Replaceable dependency.** ← addresses N1 (dependency without recourse)

Tapestry's architecture is base-model-agnostic. The sovereign layers (alignment, domain adapters, expert modules) are designed to be portable across base models. If the current base model's provider changes terms, gets sanctioned, or stops releasing weights, the consortium migrates to a different base. The sovereign investment is preserved. This is not independence — it is *designed, replaceable dependency*, which is an honest and achievable version of sovereignty.

**VP-N3. Data contributes without leaving.** ← addresses N2 (data residency unenforceable at model level)

Sovereign nodes train locally on their data. Only model updates — gradients, weight deltas, adapter parameters — leave the node, and these can be protected with differential privacy, secure aggregation, or TEE-based computation depending on the node's sensitivity tier. The data residency law is satisfied in substance, not just on paper.

**VP-N4. Hardware flexibility for sovereign procurement.** ← addresses N3 (hardware heterogeneity)

Tapestry's training infrastructure abstracts across hardware backends. A nation that procures AMD GPUs for industrial policy reasons, or inherits a mixed cluster, can participate in the same training consortium as nodes running NVIDIA hardware. Sovereignty extends to the hardware supply chain.

---

## Socio-cultural

**VP-SC1. Alignment that belongs to the community.** ← addresses SC1 (alignment is inherently local), SC3 (multilingual ≠ multicultural), IN3 (models assume the wrong world), IN4 (no agency over alignment)

This is Tapestry's deepest value proposition for socio-cultural stakeholders. Each participating community produces its own alignment layer — via RLHF, DPO, constitutional AI, or whatever method fits their governance — on top of a shared, capable base. The community decides what is appropriate, authoritative, respectful, and true in their context. No external lab can do this for them, and no amount of multilingual training data substitutes for it.

The big labs will solve multilingual capability. They cannot solve multicultural alignment. This is the structural differentiator.

**VP-SC2. Data sovereignty as architectural guarantee, not legal promise.** ← addresses SC2 (cultural knowledge extracted), SC4 (corpora held hostage by access terms)

Unique cultural corpora — oral histories, literary traditions, indigenous knowledge — can train sovereign experts or alignment layers without ever leaving the institution that holds them. The architecture enforces what contracts promise. This unlocks data that is currently too valuable to share and too locked up to use.

**VP-SC3. A seat at the architectural table.** ← addresses CP1 (contribution without governance)

Communities that contribute data, alignment judgments, or evaluation criteria have governance representation in how the shared model evolves. This is not consultation — it is structural participation in architecture and training decisions that affect how their culture is represented.

---

## Industrial

**VP-I1. Domain specialization without data exposure.** ← addresses I1 (compliance walls between data and models)

A hospital, a bank, an energy company can train domain-specific experts or adapters on their proprietary data, behind their own firewall, and contribute the resulting model updates to the consortium — or keep them entirely private. The compliance wall between "our data" and "a useful model" dissolves without the data ever leaving the enterprise.

**VP-I2. Portable AI investment.** ← addresses I2 (platform deprecation)

Tapestry-trained adapters, experts, and alignment layers are not locked to a single provider's API or platform. The weights belong to the participant. The training code is open. If any component of the stack changes, the investment transfers. This is the anti-deprecation guarantee.

**VP-I3. Compute as a participation currency.** ← addresses I3 (idle compute has no market)

HPC centers and enterprises contribute idle GPU cycles to consortium training rounds and receive access to the resulting model in return. The compute-for-access model makes participation economically rational for organizations that have hardware but not the budget or expertise to train their own models.

**VP-I4. Architectural voice, not just fine-tuning access.** ← addresses I4 (fine-tuning is not sovereignty)

Industrial participants in Tapestry don't just fine-tune someone else's model. They participate in decisions about base model architecture, training data composition, and the expert routing that determines how domain knowledge is represented. This is ownership at the architectural level, not the adapter level.

**VP-I5. Certification and strategic positioning.** ← addresses I5 (no legitimacy mechanism)

Tapestry establishes standards for sovereign AI — data governance, cultural alignment quality, safety baselines, interoperability. Participants that meet these standards receive Tapestry certification. This gives a company like FPT the ability to be "Tapestry-certified for Vietnam" — a mark of legitimacy backed by a global consortium, without the AI Alliance choosing national winners. Governments can use certification to evaluate sovereign AI claims. Companies can use it to differentiate commercially. The certification model is ISO/UL-style: define standards, certify compliance, stay neutral on competition.

This is the value proposition that answers the board-level question: "What does our organization get from participation?" Not just access to a model — strategic positioning, a credibility mark, and the ability to build commercial offerings on top of consortium-validated infrastructure.

---

## Individual

**VP-IN1. Models that reflect local context.** ← addresses IN1 (no representation in training), IN3 (models assume the wrong world), SC1 (alignment is inherently local)

An individual interacts with a model whose alignment was shaped by their community — not by a distant lab that has never encountered their professional norms, medical practices, legal system, or social expectations. Community-level alignment processes give individuals indirect but real representation in how the model is trained — a structural improvement over the current system, where individual users have no influence at all.

**VP-IN2. Graduated privacy, not binary.** ← addresses IN2 (privacy is binary)

Tapestry's tiered sovereignty spectrum (Tiers 0–4) enables individuals to contribute to model improvement with calibrated privacy guarantees. The choice is not "share everything" or "get nothing." Differential privacy, secure aggregation, and local-only training provide a range of participation levels with quantifiable privacy properties.

**VP-IN3. Alignment agency through community governance.** ← addresses IN4 (no agency over alignment)

Individuals cannot align a model alone, but they can participate in community-level alignment processes that shape the model they use. This is representative rather than individual agency — closer to democratic governance than personal configuration — but it is structurally more than the current system offers, which is nothing.

---

## Contributor/Participant

**VP-CP1. Reusable consortium training infrastructure.** ← addresses CP2 (no infrastructure at scale)

Tapestry builds the platform that every distributed training collaboration currently has to build from scratch: gradient aggregation, privacy, fault tolerance, heterogeneous hardware support, and governance. Contributors build *on* the platform, not *around* the absence of one.

**VP-CP2. Governance rights proportional to contribution.** ← addresses CP1 (contribution without governance), CP3 (architecture decided by whoever trains first)

Contributors — of data, compute, training techniques, or evaluation criteria — gain governance voice in the consortium. Architecture decisions are made collectively, not by whoever trained the first version. Credit and influence are structural, not reputational.

**VP-CP3. Sustainable economics through shared costs.** ← addresses CP4 (incentives misaligned with sustainability), N5 (frontier capital requirements)

No single organization bears the full cost of training or maintaining a frontier model. The consortium shares costs across participants, each contributing what they have (compute, data, expertise) and receiving access to what they need (a frontier-class model with sovereign customization). The economic model is closer to a utility cooperative than a product company.

---

## What This Does Not Claim

Honesty about limitations strengthens the value proposition. Tapestry does not claim:

- **That consortium training at frontier scale is proven.** It is not. DiLoCo-class methods work at small scale. The central open research question is whether they work at 70B+ across heterogeneous, high-latency nodes. The MVP roadmap is designed to deliver value without requiring this to be solved first (by starting with existing open-weights bases).

- **That sovereignty is free.** Participating in Tapestry requires compute, data curation, alignment work, and governance participation. The cost is lower than training a model alone, but it is not zero. Participants who want sovereignty must invest in it.

- **That Tapestry replaces commercial AI.** Most users and enterprises will continue using commercial models for most tasks. Tapestry's value is for the use cases where cultural alignment, data sovereignty, domain specificity, or institutional control matter enough to justify participation. That is a large and growing set of use cases, but it is not all of them.

- **That the starting base model is permanently acceptable.** Adopting an existing open-weights model as the initial base creates a dependency. The roadmap must include a credible path to consortium-trained bases, or the anti-capture principle is aspirational. The architecture is designed so that sovereign contributions (adapters, experts, alignment layers) are portable across bases, making the dependency replaceable — but it is still a dependency until the consortium can train its own.

---

## Traceability Summary

```mermaid
graph LR
    subgraph Pain Points
        N1["N1 Dependency"]
        N2["N2 Data residency"]
        N3["N3 Hardware"]
        N4["N4 No adoption"]
        N5["N5 Capital barrier"]
        SC1["SC1 Local alignment"]
        SC2["SC2 Extraction"]
        SC3["SC3 Multilingual ≠ multicultural"]
        SC4["SC4 Locked corpora"]
        I1["I1 Compliance wall"]
        I2["I2 Deprecation"]
        I3["I3 Idle compute"]
        I4["I4 Fine-tuning ≠ sovereignty"]
        I5["I5 No legitimacy"]
        IN1["IN1 No representation"]
        IN2["IN2 Binary privacy"]
        IN3["IN3 Wrong world"]
        IN4["IN4 No alignment agency"]
        CP1["CP1 No governance"]
        CP2["CP2 No infrastructure"]
        CP3["CP3 First-mover architecture"]
        CP4["CP4 Unsustainable"]
    end

    subgraph Value Propositions
        VN1["VP-N1 Capability + sovereignty"]
        VN2["VP-N2 Replaceable dependency"]
        VN3["VP-N3 Data stays"]
        VN4["VP-N4 Hardware flexibility"]
        VSC1["VP-SC1 Community alignment"]
        VSC2["VP-SC2 Architectural data sovereignty"]
        VSC3["VP-SC3 Governance seat"]
        VI1["VP-I1 Domain specialization"]
        VI2["VP-I2 Portable investment"]
        VI3["VP-I3 Compute as currency"]
        VI4["VP-I4 Architectural voice"]
        VI5["VP-I5 Certification"]
        VIN1["VP-IN1 Local context"]
        VIN2["VP-IN2 Graduated privacy"]
        VIN3["VP-IN3 Community alignment agency"]
        VCP1["VP-CP1 Reusable infrastructure"]
        VCP2["VP-CP2 Governance rights"]
        VCP3["VP-CP3 Shared economics"]
    end

    N4 --> VN1
    N5 --> VN1
    N1 --> VN2
    N2 --> VN3
    N3 --> VN4
    SC1 --> VSC1
    IN3 --> VSC1
    IN4 --> VSC1
    SC2 --> VSC2
    SC4 --> VSC2
    CP1 --> VSC3
    I1 --> VI1
    I2 --> VI2
    I3 --> VI3
    I4 --> VI4
    I5 --> VI5
    IN1 --> VIN1
    IN3 --> VIN1
    SC1 --> VIN1
    IN2 --> VIN2
    IN4 --> VIN3
    CP2 --> VCP1
    CP1 --> VCP2
    CP3 --> VCP2
    CP4 --> VCP3
    N5 --> VCP3

    style VN1 fill:#2e7d32,stroke:#1b5e20,color:#fff
    style VSC1 fill:#6a1b9a,stroke:#4a148c,color:#fff
    style VCP1 fill:#37474f,stroke:#263238,color:#fff
