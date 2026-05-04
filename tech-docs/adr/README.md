# Architectural Decision Records

## Two-level system: iterations + component decisions

### Iterations (`PRJ-YYYY`)

Top-level units of work. Each iteration follows a **mandatory 5-phase methodology**:

1. **SCOPE** — goal, exit criteria, budget (written *before* work starts)
2. **PLAN** — component decisions needed, steps, risks
3. **EXECUTE** — work through tasks, record component ADRs as decisions arise
4. **VERIFY** — check exit criteria, run tests, prove it works
5. **CLOSE** — document outcomes, flag carryover items

**Iteration template:**

```markdown
# PRJ-YYYY: [Title]

## 1. SCOPE
**Goal:** [1-2 sentences]
**Date opened:** YYYY-MM-DD
**Date closed:** —
**Budget:** $X
**Exit criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

## 2. PLAN
**Steps:** ...
**Component decisions anticipated:** ...
**Risks:** ...

## 3. EXECUTE
| ID | Decision | Status |
|----|----------|--------|
| XXX-YYYY | ... | Accepted |

## 4. VERIFY
- [x] Test 1
- [ ] Test 2

## 5. CLOSE
**Status:** Complete | Open
**Carries over:** ...
```

### Component decisions (`XXX-YYYY`)

Specific architectural choices within a component. Each references its parent iteration.

```
TAP-0001: Adopt ADR system for tapestry
├── TAP-0001-A: ADR numbering convention
```

- `TAP-YYYY` = iteration (project-level)
- `XXX-YYYY` = component decision (component abbreviation)
- Each component ADR has a `Parent: TAP-YYYY` field
- Sub-decisions of an iteration itself use `TAP-YYYY-X` suffix (A, B, C...)

### Component prefixes (tapestry)

| Prefix | Scope |
|--------|-------|
| `TAP`  | tapestry project-wide / iteration |
| `DAT`  | data subsystem (`src/tapestry/data`) |
| `TRN`  | training / tuning subsystem (`src/tapestry/training`) |
| `INF`  | infrastructure subsystem (`src/tapestry/infrastructure`) |
| `DOC`  | technical docs site / Jekyll (`docs/`, `tech-docs/`) |
| `WG`   | work-group governance and process |

New component prefixes may be introduced via a component ADR documenting the addition.

### Rules

- **Iterations are opened before work starts** — SCOPE and PLAN first, then EXECUTE.
- Append-only. Superseded ADRs get a status update + link to the new one. Never edit history.
- Sequential numbering within scope, never reused.
- Every iteration lists what it comprises. Every component ADR references its parent.
- ADR files are named `XXX-YYYY-slug.md`.
- Filter by component with `ls tech-docs/adr/DAT-*` etc.

### Evidence standard

A checked box is not evidence by itself. Every completed SCOPE or VERIFY item
must be paired with at least one concrete proof artifact:

- command output or summarized command result with command name and pass/fail count
- artifact path, evidence path, generated file path, or code path
- test name, test file, or focused test invocation
- PR, issue, commit, or release reference
- explicit carryover/defer statement when proof was not gathered

If an ADR closes with pending EXECUTE rows, unchecked original SCOPE criteria, or
stale `VERIFY`/`CLOSE` text, append a reconciliation section that states which
section is authoritative and which claims remain partial or deferred.

---

## Status index

Open iteration ADRs:

| ADR | Title | Phase |
|-----|-------|-------|
| —   | —     | —     |

Closed iteration ADRs:

| ADR | Title | Closed |
|-----|-------|--------|
| [TAP-0001](TAP-0001-adr-system.md) | Adopt ADR system for tapestry | 2026-05-04 |

Component ADRs (accepted decisions, not tracked open/closed):
`TAP-0001-A`
