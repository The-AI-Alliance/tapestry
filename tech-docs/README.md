# README for the `tech-docs` Directory

This directory organizes the technical documentation under development for Project Tapestry, including requirements analysis, architecture design, decision records, governance, and work group documentation.

| Directory | Description |
| :-------- | :---------- |
| [`architecture/`](architecture/README.md) | TVA methodology, phased outputs (1–5), architectural options analysis, ADRs, diagrams — **see [Architecture documents](#architecture-documents)** |
| [`governance/`](governance/README.md) | Anti-capture principle and governance design |
| [`strategic-plan/`](strategic-plan/README.md) | Overall strategy for execution — the [vision](strategic-plan/VISION.md) and the [product requirements (PRD)](strategic-plan/PRD.md) |
| [`tapestry-reference/`](tapestry-reference/README.md) | Consolidated technical reference, including a single-page [architecture synthesis](tapestry-reference/ARCHITECTURE.md) |
| [`reference/`](reference/README.md) | Reference docs (e.g. training paradigms, deployment and usage material) |
| [`work-groups/`](work-groups/README.md) | Lifecycle work-group charters for data governance, base training, sovereign alignment, evaluation/certification, security/privacy, infrastructure, deployment, and governance participation (subject to change) |

## Architecture documents

The directory index is [`architecture/README.md`](architecture/README.md). Main artifacts under [`architecture/`](architecture/):

| Document | Description |
| :------- | :---------- |
| [`architecture/0-tva-methodology.md`](architecture/0-tva-methodology.md) | TVA design process — phases, design principles, current status |
| [`architecture/1-stakeholder-map.md`](architecture/1-stakeholder-map.md) | Phase 1 — who we serve, what they control, what they fear |
| [`architecture/2-pain-points.md`](architecture/2-pain-points.md) | Phase 2 — what's concretely broken for each layer today |
| [`architecture/3-value-propositions.md`](architecture/3-value-propositions.md) | Phase 3 — what Tapestry offers that the status quo doesn't |
| [`architecture/4-design-goals.md`](architecture/4-design-goals.md) | Phase 4 — constraints the architecture must satisfy |
| [`architecture/5-architectural-options.md`](architecture/5-architectural-options.md) | Phase 5 — option space and decision analysis toward an architectural thesis |
| [`architecture/diagrams/README.md`](architecture/diagrams/README.md) | Architecture figures (SVG in Markdown) and embedding conventions |
| [`architecture/decisions/`](architecture/decisions/README.md) | Architecture Decision Records (ADRs) |

## Reference documents

The [`reference/`](reference/README.md) directory holds material outside the TVA phase chain (comparison references, deployment notes, etc.):

| Document | Description |
| :------- | :---------- |
| [`reference/training-approaches.md`](reference/training-approaches.md) | Centralized vs. federated vs. consortium training |

Repository root [**`README.md`**](../README.md) and [**`AGENTS.md`**](../AGENTS.md) summarize how `tech-docs/` fits with `docs/`, `src/`, and contributor workflows.
