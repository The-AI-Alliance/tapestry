# Release Gate Checklist

This checklist is a first pass at gates before public claims are made about a
Tapestry-derived shared base, sovereign derivative, or certification status.

## Gate 1: Claim Boundary

- The claim is written in one sentence.
- The claim class is identified:
  - cultural alignment
  - language capability
  - domain expertise
  - data sovereignty
  - privacy
  - safety
  - capability
  - portability
  - contribution integrity
- The claim does not collapse separate concepts into one vague promise.
- The claim states what is not covered.

## Gate 2: Evidence Inventory

- Evaluation run IDs are recorded.
- Model hashes and versions are recorded.
- Dataset or prompt-set versions are recorded.
- Tool versions and configuration are recorded.
- Public evidence summary is prepared.
- Consortium-private evidence bundle is prepared when needed.
- Participant-private evidence remains within the promised boundary.

## Gate 3: Data And Sovereignty Review

- Every dataset has a dataset/provenance card.
- Restricted or local-only data is clearly marked.
- Residency controls match the stated tier.
- Raw data movement is recorded or prohibited.
- Allowed uses match the proposed training/evaluation step.
- Data stewards have approved the use.

## Gate 4: Capability And Safety Regression

- General capability baselines were run before and after the update.
- Cultural or domain gains are not counted if core capability falls past the
  predeclared threshold.
- Safety baselines were run before and after the update.
- Known safety regressions are either fixed or block release.
- Red-team findings are summarized at the right visibility tier.

## Gate 5: Privacy And Leakage Review

- Memorization or extraction tests were run when restricted data was used.
- Canary tests were run where appropriate.
- Update-leakage risk was reviewed for contributed model weights.
- Public metrics do not expose individual or restricted behavior.
- Logs and telemetry are checked for accidental data leakage.

## Gate 6: Cultural Or Domain Review

- The represented community or domain is explicitly named.
- Reviewers are identified by role, not only by organization.
- Prompt sets are checked for cultural flattening or domain oversimplification.
- Language fluency is not treated as cultural alignment.
- Community/domain reviewers can dispute or qualify the public claim.

## Gate 7: Governance And Anti-capture

- Contribution weighting policy is recorded.
- Quality floor and influence cap are recorded.
- Rejected contributions include reasons.
- Any exception has a governance record.
- No single participant can silently dominate the public claim.

## Gate 8: Release Decision

- Release approved:
- Release blocked:
- Certification claim approved:
- Certification claim blocked:
- Public caveats:
- Private follow-up:
- Owner for next review:
