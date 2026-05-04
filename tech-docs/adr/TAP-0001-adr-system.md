# TAP-0001: Adopt ADR system for tapestry

## 1. SCOPE
**Goal:** Establish a lightweight, two-level Architectural Decision Record (ADR) convention for the tapestry project so that iteration-level decisions and component-level technical choices are captured consistently and reviewably alongside the code and docs.
**Date opened:** 2026-05-04
**Date closed:** 2026-05-04
**Budget:** N/A (process bootstrap)
**Exit criteria:**
- [x] `tech-docs/adr/` directory exists and is the canonical location for ADRs.
- [x] `tech-docs/adr/README.md` documents the iteration template, component prefixes, rules, and evidence standard.
- [x] Numbering convention is itself recorded as a component ADR (`TAP-0001-A`).
- [x] At least one iteration ADR (`TAP-0001`) exists demonstrating the 5-phase template.

## 2. PLAN
**Steps:**
1. Create `tech-docs/adr/` and add a `README.md` with the convention, template, prefix table, rules, and status index.
2. Record `TAP-0001-A` capturing the `XXX-YYYY` numbering convention as an explicit, citable decision.
3. Use this iteration ADR (`TAP-0001`) as the worked example of the 5-phase template.

**Component decisions anticipated:**
- `TAP-0001-A`: ADR numbering convention.

**Risks:**
- Convention drift if contributors add ad-hoc decision docs outside `tech-docs/adr/`. Mitigation: README rules + review.
- Prefix proliferation. Mitigation: new prefixes require a component ADR.

## 3. EXECUTE
| ID | Decision | Status |
|----|----------|--------|
| TAP-0001-A | ADR numbering convention (`XXX-YYYY` under iterations) | Accepted |

## 4. VERIFY
- [x] `tech-docs/adr/README.md` present and includes template, prefix table, rules, evidence standard, status index — see `tech-docs/adr/README.md` in this commit.
- [x] `tech-docs/adr/TAP-0001-A-adr-numbering-convention.md` present — see file in this commit.
- [x] `tech-docs/adr/TAP-0001-adr-system.md` present (this file) and follows the 5-phase template.

## 5. CLOSE
**Status:** Complete
**Carries over:** Future architectural decisions for the data, training, and infrastructure subsystems should be filed as component ADRs (`DAT-`, `TRN-`, `INF-`) under their owning iteration. Work-group process decisions use `WG-`. Documentation-site decisions use `DOC-`.
