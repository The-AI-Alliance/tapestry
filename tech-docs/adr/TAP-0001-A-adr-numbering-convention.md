# ADR TAP-0001-A: ADR numbering convention (`XXX-YYYY` under iterations)

**Status:** Accepted
**Date:** 2026-05-04
**Decided by:** maintainers
**Stakeholders notified:** tapestry contributors
**Parent:** TAP-0001

## Context
Tapestry spans several distinct subsystems (data, training, infrastructure) plus a documentation site and work-group process. Flat sequential ADR numbering would obscure which decisions belong to which part of the system. We want decisions to be filterable by scope and to clearly link component choices back to the iteration that drove them.

## Decision
Use `XXX-YYYY` numbering where `XXX` is a scope abbreviation and `YYYY` is monotonic within that scope.

- Project-level / iteration prefix: `TAP` (tapestry).
- Component prefixes:
  - `DAT` — data subsystem (`src/tapestry/data`)
  - `TRN` — training / tuning subsystem (`src/tapestry/training`)
  - `INF` — infrastructure subsystem (`src/tapestry/infrastructure`)
  - `DOC` — technical docs site (Jekyll under `docs/`, prose under `tech-docs/`)
  - `WG`  — work-group governance and process
- Sub-decisions of an iteration itself use the iteration id with a letter suffix: `TAP-YYYY-A`, `TAP-YYYY-B`, ...
- Files are named `XXX-YYYY-slug.md` and live under `tech-docs/adr/`.
- Each component ADR carries a `Parent: TAP-YYYY` field linking it to its driving iteration.
- Numbering is sequential within scope and never reused. Superseded ADRs get a status update plus a link to the replacement; history is append-only.

New prefixes may be introduced by a component ADR documenting the addition.

## Why this and not the alternatives
- **Flat numbering (0001, 0002, ...)** — rejected: cannot tell at a glance whether a decision is project-wide or scoped to one subsystem.
- **Numeric scope prefixes (000, 100, 200, ...)** — rejected: less readable and not self-documenting.
- **Directory-per-component** — rejected: fragments the timeline. Prefix-in-filename keeps everything in one sorted list while still showing scope.
- **Reusing aito-teams' `AIT` prefix verbatim** — rejected: the project-level prefix should derive from the project name, per the originating convention.

## Consequences
- ADR files sort and filter cleanly: `ls tech-docs/adr/DAT-*` lists data-subsystem decisions.
- Contributors must learn the prefix table (documented in `tech-docs/adr/README.md`).
- Iterations are the unit of planning and verification; component ADRs are the unit of architectural choice.

## Reversibility
**High** — renaming files is trivial and the convention is documentation-only, with no tooling lock-in.
