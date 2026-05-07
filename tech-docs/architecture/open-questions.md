# Open Questions Index

*Extracted May 7, 2026 from TVA architecture documents. Each entry references its source; depth lives there.*

**Tags:** `Workshop` = May 7-8 workshop agenda item. `Post-workshop` = needs resolution but not at the workshop. `Research` = requires experimentation or study.

---

## Training Architecture

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| T1 | Has anyone run outer-loop distributed training above 7B parameters on heterogeneous, high-latency clusters? What broke? | [2-pain-points.md](2-pain-points.md) (CP2) | Workshop | Eric (Petuum), Laurent (INRIA), Erik (Zyphra) |
| T2 | Is the proposed four-step consortium training loop accepted? What is the target cycle frequency — monthly, quarterly, per-node choice? | [5-architectural-options.md](5-architectural-options.md) (Decision 3) | Workshop | Eric Xing, Laurent Massoulie |
| T3 | What are the convergence properties of the training loop when nodes have radically different (non-IID) data distributions? | [TAP-004](decisions/adr-004-training-loop.md) | Research | |
| T4 | Compute cost per cycle is estimated at 5-10% of base pretraining. Is this validated empirically? | [TAP-004](decisions/adr-004-training-loop.md) | Research | |
| T5 | Should the consortium use synchronized or asynchronous cycling? If some nodes cycle monthly and others annually, their influence diverges — is this acceptable? | [TAP-004](decisions/adr-004-training-loop.md), [5-architectural-options.md](5-architectural-options.md) (Q8) | Workshop | |
| T6 | Should the Tracel/Burn proposal be formally adopted as the target architecture? What is the timeline for Burn backend support? | [5-architectural-options.md](5-architectural-options.md) (Decision 5) | Workshop | Erik Norden, Ziv (NVIDIA), Niles (AMD) |
| T7 | What does hardware-agnostic consortium training look like? Can a consortium include both NVIDIA and AMD nodes in the same training run today, and what breaks? | [2-pain-points.md](2-pain-points.md) (N3) | Workshop | Ziv (NVIDIA), Niles (AMD) |

## Base Model Strategy

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| B1 | Which open-weights base model family to start with? (Llama, Mistral, Qwen — each carries geopolitical signal.) | [5-architectural-options.md](5-architectural-options.md) (Decision 1), [TAP-006](decisions/adr-006-phased-base-model.md) | Workshop | Eric Xing, Jie Tang, Thomas Wolf |
| B2 | Under what conditions does the consortium commit to training its own base (Phase 2 trigger criteria)? How do we prevent "eventually" from becoming "never"? | [5-architectural-options.md](5-architectural-options.md) (Decision 1), [TAP-006](decisions/adr-006-phased-base-model.md) | Workshop | |
| B3 | What is the actual minimum viable investment for a sovereign model that people will use — not just one that exists? Does pooling via consortium training cross the adoption threshold? | [2-pain-points.md](2-pain-points.md) (N5) | Workshop | Ayah (Current AI), Arno (Elysee), Hideki (IPA Japan) |

## Cultural Alignment

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| C1 | Does continued pretraining on culturally *grounded* data (not just linguistically local data) measurably shift cultural alignment? This is the foundational hypothesis — unvalidated. | [5-architectural-options.md](5-architectural-options.md) (Q12), [TAP-003](decisions/adr-003-cultural-alignment.md), [TAP-005](decisions/adr-005-sovereign-pipeline.md) | Research | |
| C2 | What constitutes "culturally grounded" data? Legal texts? Literature? Community-authored content? Social media? Religious texts? Varies by community. | [5-architectural-options.md](5-architectural-options.md) (Q13), [TAP-005](decisions/adr-005-sovereign-pipeline.md) | Research | |
| C3 | Is continued pretraining + post-training alignment accepted as the sovereign approach (not just adapters)? What evaluation framework does the consortium adopt for cultural alignment? | [5-architectural-options.md](5-architectural-options.md) (Decision 2) | Workshop | Ganesh (BharatGen), Antoine (Swiss AI/Apertus), Jian Gang (SEA-LION) |
| C4 | What adoption rates are sovereign model builders seeing? What would it take for domestic users to prefer a sovereign model over a commercial alternative? | [2-pain-points.md](2-pain-points.md) (N4) | Workshop | Ganesh (BharatGen), Antoine (Swiss AI/Apertus), Jian Gang (SEA-LION), Da-shan (MediaTek) |
| C5 | Can you give a concrete example where a frontier model's alignment — not its language capability — was wrong for your community in a way that could not be fixed by fine-tuning or prompting? | [2-pain-points.md](2-pain-points.md) (SC1) | Workshop | Open floor |
| C6 | Who designs the cultural evaluation benchmarks? Is this a work group? | [5-architectural-options.md](5-architectural-options.md) (Q2, Decision 8) | Workshop | |
| C7 | Who leads alignment infrastructure development? Which communities volunteer as pilot alignment producers? | [5-architectural-options.md](5-architectural-options.md) (Decision 6) | Workshop | Pascale Fung, Ganesh, open call |
| C8 | What controlled experiment would test whether culturally grounded continued pretraining shifts alignment measurably on frameworks like Inglehart-Welzel? | [5-architectural-options.md](5-architectural-options.md) (Q1) | Research | |

## Safety

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| S1 | Is modular alignment technically sound, or does it create models that can be trivially de-aligned? Some safety researchers argue alignment must be baked into pretraining. | [2-pain-points.md](2-pain-points.md) (IN4) | Workshop | Open floor |
| S2 | Who defines "safety" when the whole point is that different communities have different values? The line between "safety" (universal) and "alignment" (sovereign) is itself culturally contested. | [4-design-goals.md](4-design-goals.md) (DG6 vs DG1) | Workshop | |
| S3 | What mechanisms preserve safety through continued pretraining? Frozen layers? Regularization? Evaluation gates? (Different from and harder than preserving safety through post-training alignment.) | [5-architectural-options.md](5-architectural-options.md) (Q2), [TAP-005](decisions/adr-005-sovereign-pipeline.md) | Research | |

## Data Sovereignty & Privacy

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| D1 | If a sovereign node trains on GDPR-covered data and sends weight updates to an aggregator, does that constitute a data transfer under EU law? What technical guarantees (DP, secure aggregation) make it legally defensible? | [2-pain-points.md](2-pain-points.md) (I1) | Workshop | Dave (OpenMined), Arno (Elysee) |
| D2 | Is Tier 0-1 (legal/provenance) sufficient for Phase 1, or do participants require Tier 2 (DP) as a minimum before contributing sovereign data? | [5-architectural-options.md](5-architectural-options.md) (Decision 4) | Workshop | Dave (OpenMined), Arno (Elysee) |
| D3 | What is the actual reconstruction risk from weight deltas after N steps of continued pretraining? At what N does the risk become acceptable without formal DP? | [5-architectural-options.md](5-architectural-options.md) (Q3) | Research | |
| D4 | What is the actual privacy-utility tradeoff for DP-SGD at frontier model scale? If DP destroys model quality, Tier 2 is not viable for pretraining contributions. | [5-architectural-options.md](5-architectural-options.md) (Decision 4) | Research | |
| D5 | What governance model lets institutional data contribute to training without leaving its institution? | [2-pain-points.md](2-pain-points.md) (SC4) | Workshop | Roberto (Software Heritage), Slava (CODATA) |
| D6 | Is there a working model — technical or legal — for data royalties or attribution at training scale? | [2-pain-points.md](2-pain-points.md) (SC2) | Workshop | Anastasia (Pleias/Common Corpus), Sebastian (EleutherAI/SUCHO) |

## Governance & Ecosystem

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| G1 | Who operates the initial coordinator? What transparency and audit requirements does it have? | [5-architectural-options.md](5-architectural-options.md) (Decision 7) | Workshop | AI Alliance, Rick Stevens, open |
| G2 | Who defines the quality floor benchmark for contribution weighting? How is it reviewed for cultural bias? | [5-architectural-options.md](5-architectural-options.md) (Q5) | Workshop | |
| G3 | Is uniform-with-quality-floor weighting accepted for Phase 1? | [5-architectural-options.md](5-architectural-options.md) (Decision 8) | Workshop | Open floor |
| G4 | Can a node opt to contribute weight deltas for some training cycles and keep weights private for others (selective participation)? | [5-architectural-options.md](5-architectural-options.md) (Q6) | Post-workshop | |
| G5 | What are the criteria for a new node to join the consortium? What happens to a node's historical contributions if it leaves? | [5-architectural-options.md](5-architectural-options.md) (Q7) | Post-workshop | |
| G6 | Should nodes be able to see how their contribution was weighted? (Transparency vs. gaming.) | [5-architectural-options.md](5-architectural-options.md) (Q3, Decision 8) | Post-workshop | |
| G7 | Does the weighting policy need to be the same for all nodes, or can it vary by contribution type? | [5-architectural-options.md](5-architectural-options.md) (Q5, Decision 8) | Post-workshop | |
| G8 | What does Tapestry certification mean? What standards must an entity meet to be a "Tapestry-certified sovereign AI provider"? Who audits compliance? | [5-architectural-options.md](5-architectural-options.md) (Q9) | Post-workshop | |
| G9 | How does certification interact with competition? If I invest in building sovereign AI for my country, does my competitor get the same certification? | [5-architectural-options.md](5-architectural-options.md) (Q10) | Post-workshop | |
| G10 | What is the commercial model? What can participants charge for? What is shared vs. proprietary? | [5-architectural-options.md](5-architectural-options.md) (Q11) | Post-workshop | |

## Economics & Sustainability

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| E1 | What fraction of GPU capacity sits idle at participant institutions, and what terms would be needed to contribute it to a consortium training run? | [2-pain-points.md](2-pain-points.md) (I3) | Workshop | Rick (Argonne), Eric (MBZUAI), Vincent (Red Hat) |
| E2 | What economic model would have made BLOOM sustainable — not just trained, but maintained and updated? What would funders need to see to fund ongoing operations, not just a single training run? | [2-pain-points.md](2-pain-points.md) (CP4) | Workshop | Thomas (Hugging Face/BigScience), Ayah (Current AI) |

## Design Goal Validation

| # | Question | Source | Tag | People |
|:--|:---------|:-------|:----|:-------|
| V1 | Is DG1 achievable? Can core-plus-sovereign actually deliver frontier capability with meaningful cultural alignment, or is the sovereign layer cosmetic? | [4-design-goals.md](4-design-goals.md) | Workshop | |
| V2 | Is the shared-resources model compelling enough, or does it sound like "use someone else's model with extra steps"? | [4-design-goals.md](4-design-goals.md) | Workshop | |
| V3 | Are "break the capability-sovereignty tradeoff" and "break the unit economics of training" the right two primary design goals? Is there a third (sustainability, safety, cultural representation) that is equally load-bearing? | [2-pain-points.md](2-pain-points.md) (synthesis) | Workshop | |
| V4 | What design goal is missing? (Interoperability, specific industrial use cases, speed of deployment?) | [4-design-goals.md](4-design-goals.md) | Workshop | |
