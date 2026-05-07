# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for Project Tapestry. Each ADR captures a significant architectural or governance decision, its context, the alternatives considered, and the rationale for the choice made.

## Format

ADRs are numbered sequentially (`adr-NNN-short-title.md`) and use the following status values:

- **proposed** — under discussion, inviting challenge
- **accepted** — decision made and in effect
- **superseded** — replaced by a later ADR (link to successor)
- **rejected** — was proposed, explicitly decided against (records why not)

Use a small metadata table at the top of each ADR:

| Field | Value |
| :---- | :---- |
| Status | Proposed |
| Confidence | High (5/5) |
| Date | May 7, 2026 |
| Deciders | Christopher Nguyen (proposed), workshop participants |

Avoid consecutive plain Markdown lines like `**Status:** ...` / `**Date:** ...`; GitHub renders those as one paragraph unless they use explicit hard breaks.

## Index

| ADR | Title | Status | Confidence |
| :-- | :---- | :----- | :--------- |
| [001](adr-001-core-plus-sovereign.md) | Core-plus-sovereign architecture | proposed | 5/5 |
| [002](adr-002-consortium-training.md) | Consortium training model | proposed | 5/5 |
| [003](adr-003-cultural-alignment.md) | Cultural alignment as primary differentiator | proposed | 5/5 |
| [004](adr-004-training-loop.md) | The consortium training loop | proposed | 4/5 |
| [005](adr-005-sovereign-pipeline.md) | Sovereign alignment pipeline | proposed | 4/5 |
| [006](adr-006-phased-base-model.md) | Phased base model strategy | proposed | 4/5 |
