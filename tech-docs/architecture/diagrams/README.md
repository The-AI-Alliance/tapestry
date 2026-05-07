# Architecture diagrams

This directory holds **shared visual assets** for architecture docs: exported figures, optional diagram sources, and (when useful) **reusable** Mermaid sources. Narrative docs live next door under [`../`](README.md); this folder is for artifacts that are **referenced**, not the primary prose.

## What belongs here

| Kind | Use when | Example names |
| :--- | :------- | :------------ |
| **Raster / vector exports** | Tooling outside GitHub’s Mermaid renderer (Excalidraw, draw.io, Figma, OmniGraffle), detailed topology, branding | `system-context.svg`, `training-loop.png` |
| **Reusable Mermaid source** | Same diagram embedded in **multiple** `.md` files; you want one file to edit | `consortium-loop.mmd` (see below) |
| **Companion sources** | Round-trip editing | `system-context.drawio`, `system-context.excalidraw` |

Avoid dumping every inline diagram here unless there is no shared asset yet.

## Canonical figures (SVG in Markdown; PNG optional)

ADRs and [`training-approaches.md`](../../reference/training-approaches.md) embed **`![…](../diagrams/name.svg)`**. The **`*.svg`** is the maintained vector; **`*.png`** is generated for editors whose Markdown preview blocks SVG or for slides.

Commit **`*.svg`** whenever the graphic changes; commit regenerated **`*.png`** when you rely on raster preview or external decks.

| SVG (embedded in Markdown; edit here) | PNG (optional raster export) | Referenced from |
| :------------------------------------ | :-------------------------- | :-------------- |
| [`consortium-training-loop.svg`](consortium-training-loop.svg) | [`consortium-training-loop.png`](consortium-training-loop.png) | [ADR-004](../decisions/adr-004-training-loop.md), [`training-approaches.md`](../../reference/training-approaches.md) |
| [`core-plus-sovereign-stack.svg`](core-plus-sovereign-stack.svg) | [`core-plus-sovereign-stack.png`](core-plus-sovereign-stack.png) | [ADR-001](../decisions/adr-001-core-plus-sovereign.md) |
| [`training-paradigms-comparison.svg`](training-paradigms-comparison.svg) | [`training-paradigms-comparison.png`](training-paradigms-comparison.png) | [ADR-002](../decisions/adr-002-consortium-training.md) |
| [`cultural-alignment-framing.svg`](cultural-alignment-framing.svg) | [`cultural-alignment-framing.png`](cultural-alignment-framing.png) | [ADR-003](../decisions/adr-003-cultural-alignment.md) |
| [`sovereign-alignment-pipeline.svg`](sovereign-alignment-pipeline.svg) | [`sovereign-alignment-pipeline.png`](sovereign-alignment-pipeline.png) | [ADR-005](../decisions/adr-005-sovereign-pipeline.md) |
| [`phased-base-model-strategy.svg`](phased-base-model-strategy.svg) | [`phased-base-model-strategy.png`](phased-base-model-strategy.png) | [ADR-006](../decisions/adr-006-phased-base-model.md) |

### Regenerate PNGs after editing SVG

Requires [librsvg](https://wiki.gnome.org/Projects/LibRsvg) `rsvg-convert` (e.g. `brew install librsvg`).

From the **repository root**:

```shell
make tech-docs-diagram-pngs
```

Or from this directory:

```shell
cd tech-docs/architecture/diagrams
for f in *.svg; do rsvg-convert -w 1400 "$f" -o "${f%.svg}.png"; done
```

Phase docs (`0-tva-methodology.md`, …) may keep **inline Mermaid** where figures are tightly coupled to narrative and not reused.

## How inclusion works in Markdown

Markdown has no standard `#include`. Embedding is always:

1. **Images** — relative URL from the **file that references them**:

   From [`decisions/adr-004-training-loop.md`](../decisions/adr-004-training-loop.md):

   ```markdown
   ![Consortium training loop](diagrams/consortium-training-loop.svg)
   ```

   That path is wrong from `decisions/` — you must walk up one level:

   ```markdown
   ![Consortium training loop](../diagrams/consortium-training-loop.svg)
   ```

   From [`5-architectural-options.md`](../5-architectural-options.md) (same folder as `diagrams/`):

   ```markdown
   ![Consortium training loop](diagrams/consortium-training-loop.svg)
   ```

2. **Mermaid** — GitHub (and many editors) render fenced ` ```mermaid ` blocks **inside** the `.md` file. Putting only `.mmd` text here does **not** auto-render; you either paste the contents into the consuming doc or rely on a site build that inlines it (this repo does not require such a build today).

**Rule of thumb:** embed **`![alt](../diagrams/name.svg)`** from `decisions/` (GitHub renders SVG). From [`reference/`](../../reference/), use `../architecture/diagrams/name.svg`. Run **`make tech-docs-diagram-pngs`** after SVG edits if you need **`name.png`** for a preview tool or slides. Prefer **one SVG linked from many Markdown files** instead of duplicating Mermaid. Keep **inline Mermaid** only where the diagram is not reused (see **Canonical figures** above).

## Same diagram in two documents

Pick one:

- **Preferred for simplicity:** One **SVG** path under `diagrams/`, shared across markdown files (adjust `../` counts per location); regenerate PNG when needed for raster viewers.
- **Text stays in git together:** Duplicate a short Mermaid block in both places (acceptable when the figure rarely changes).
- **Advanced:** Maintain `diagrams/foo.mmd` as source of truth; when it changes, paste into consuming docs or add a small script later — only worth it if duplication becomes painful.

## Publishing note

The GitHub Pages site under [`docs/`](../../../docs/) does not automatically mirror `tech-docs/`. If architecture HTML or mirrored Markdown is published later, copy or generate assets into whatever directory that site serves, or add Jekyll includes — the relative paths above are for the **repo / GitHub** view of `tech-docs/`.

## Naming

Use **kebab-case**, short topic-first names. For each figure, keep **`basename.svg`** and **`basename.png`** together and regenerate PNG when SVG changes.
