# Glossary

This glossary defines **Tapestry-specific** terms — the vocabulary that is unique to this project and not covered by general AI/ML references. For general AI vocabulary (Alignment, Fine Tuning, RAG, RLHF, Constitutional AI, etc.), see the [AI Alliance glossary](https://the-ai-alliance.github.io/glossary).

Each entry gives a one-line gloss and links to the canonical source where the term is fully defined. The ADRs are the source of truth; this glossary is a consolidated index.

## How these terms fit together

Consortium training is the paradigm; it has two phases run in order. Phase 1, the **Shared-Base Loop**, is the collective loop that produces the **Shared Base** (the shared substrate). Phase 2, the **Sovereign Build**, is each member's local pipeline that turns the Shared Base into that member's deployable **Sovereign Model**. The pipeline outcome is **N+1**: one Shared Base plus N Sovereign Models.

Continued pre-training (CPT) appears in both phases, distinguished by where it runs: **Contributed CPT** runs in the loop and its weights flow back to the Shared Base; **Private CPT** runs in a Sovereign Build and stays local. The Sovereign Build is broken into **Stage 0/A/B/C**, with Stage A being where CPT (Contributed or Private) lives.

## A–Z

**Consortium training** — The paradigm Tapestry uses: a small number of large, trusted, heterogeneous nodes collaboratively training a shared model, where data sovereignty is a first-order architectural constraint and cultural alignment is the goal. *See [TAP-002](../architecture/decisions/adr-002-consortium-training.md) for the full definition and the comparison with centralized and federated training.* The umbrella over Shared-Base Loop and Sovereign Build.

**Contributed CPT** — Continued pre-training performed *inside* the Shared-Base Loop; its post-training weights are contributed back to the Shared Base. *Contrast* Private CPT. *See [TAP-004](../architecture/decisions/adr-004-training-loop.md).*

**Coordinator** — The role in the Shared-Base Loop that receives contributed weight vectors from members and merges them (FedAvg-class averaging by default; outer optimizer swappable) into the next Shared Base. *See [TAP-004](../architecture/decisions/adr-004-training-loop.md).*

**Cultural Alignment** — The project's primary differentiator: producing models that reflect a member's local knowledge, values, institutions, domains, and interaction norms. Added in the Sovereign Build, not the Shared Base. *See [TAP-003](../architecture/decisions/adr-003-cultural-alignment.md).*

**Member** — An organization that participates in the consortium (a national lab, sovereign AI initiative, HPC center, or research institution). A member provides the compute environment (the "node") and the sovereign data. *Working definition — the member-vs-node naming convention is under discussion; see the review thread on [PR #79](https://github.com/The-AI-Alliance/tapestry/pull/79).*

**N+1** — Tapestry's model-outcome structure: one Shared Base (the shared substrate) plus N Sovereign Models (one per member). *See [TAP-005](../architecture/decisions/adr-005-sovereign-pipeline.md).*

**Private CPT** — Continued pre-training performed *inside* a Sovereign Build; stays local and is never contributed. This is how a member adds culturally-grounded knowledge that does not flow back to the consortium. *Contrast* Contributed CPT. *See [TAP-004](../architecture/decisions/adr-004-training-loop.md).*

**Shared Base** — The common base model produced by the Shared-Base Loop; the "1" in the N+1 model outcome. It carries **no cultural alignment** — alignment is added in each member's Sovereign Build. *See [TAP-004](../architecture/decisions/adr-004-training-loop.md).*

**Shared-Base Loop** — Phase 1 of consortium training: the collective, iterative loop that produces the Shared Base. Members run Contributed CPT on local data and contribute weight vectors (never raw data, never per-step gradients) to the coordinator, which merges them into the next Shared Base. *See [TAP-004](../architecture/decisions/adr-004-training-loop.md).* Output: the Shared Base.

**Sovereign Build** — Phase 2 of consortium training: each member's local pipeline that turns the Shared Base into its deployable Sovereign Model. Nothing here is contributed back. Broken into Stage 0/A/B/C. *See [TAP-005](../architecture/decisions/adr-005-sovereign-pipeline.md).*

**Sovereign Model** — A member's deployable, culturally-aligned model (one of the "N" in N+1), produced by post-training the Shared Base through the Sovereign Build. *See [TAP-005](../architecture/decisions/adr-005-sovereign-pipeline.md).*

**Stage 0/A/B/C** — The fine-grained breakdown of work *inside* the Sovereign Build: Stage 0 (data preparation), Stage A (CPT — which maps to Contributed CPT in the loop or Private CPT in the build), Stage B (instruction tuning / SFT), Stage C (alignment — RLHF/DPO/Constitutional AI), with Evaluation as a cross-cutting concern. *See [TAP-005](../architecture/decisions/adr-005-sovereign-pipeline.md) for the stage-by-stage mapping to standard industry terminology.*

## See also

Terms with established canonical homes elsewhere in `tech-docs/` (not duplicated here):

- **DG1–DG9** — the nine design goals. See [`4-design-goals.md`](../architecture/4-design-goals.md).
- **TAP-001 … TAP-008** — the architecture decision records. See the [ADR index](../architecture/decisions/README.md).
- **TVA** — the Tapestry Value Architecture methodology. See [`0-tva-methodology.md`](../architecture/0-tva-methodology.md).
- **TAPESTRY-GLOBAL** and regional/national/entity model variants — see [`VISION.md`](../strategic-plan/VISION.md).
- **70/30 architecture principle** — see [`VISION.md`](../strategic-plan/VISION.md).
