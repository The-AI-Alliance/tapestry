# MVP Evaluation Matrix

This matrix describes the minimum evidence layer for Tapestry-derived model
claims. It is designed to be small enough for Phase 0 while leaving room for
participant-specific private evidence.

## Evidence Visibility Tiers

| Tier | Audience | Examples |
| --- | --- | --- |
| Public | Anyone | Summary metrics, model card, dataset metadata, claim boundaries |
| Consortium | Tapestry reviewers and participating organizations | Full evaluation runs, red-team details, restricted data-review notes |
| Participant | Data/model owner only | Raw sensitive data, private logs, regulated records, internal annotation details |

## Claim Matrix

| Claim class | Example claim | Minimum evidence | Candidate tools | Blocking condition |
| --- | --- | --- | --- | --- |
| Cultural alignment shift | Model output moved toward the target community on WVS/Inglehart-Welzel style axes | Before/after eval, prompt set version, target community definition, uncertainty notes, adversarial prompt-order checks | Unitxt, lm-evaluation-harness, custom WVS harness | Apparent shift disappears under prompt-order or paraphrase checks |
| Cultural grounding | Stage 0/A data reflects a community's institutions, norms, and domain context | Dataset card, coverage analysis, contributor review, excluded-source list | Dataset cards, data catalogs | Dataset is language-local but culturally thin, or source authority is unclear |
| Capability preservation | Alignment or CPT did not degrade general quality beyond tolerance | Baseline and post-update benchmark deltas, model/version hashes, regression thresholds | lm-evaluation-harness, Unitxt | General capability drop exceeds predeclared threshold |
| Safety preservation | Continued pretraining or sovereign alignment did not remove baseline safety constraints | Safety suite before/after, blocked behavior checks, red-team summary, release notes | AI Alliance eval stack, policy tools, custom red-team suites | Known baseline safety gate fails after update |
| Data sovereignty | Restricted data stayed under the promised legal, organizational, and technical controls | Dataset card, residency rule, allowed-use statement, audit evidence, operator attestation | Provenance records, OPA, logs, data catalog | Raw restricted data leaves its permitted boundary without governed exception |
| Privacy/leakage control | Model or update artifacts do not expose protected records under the stated threat model | Canary tests, extraction tests, memorization checks, update-leakage review | Custom extraction harnesses, DP or secure aggregation reports | Protected examples are recoverable or memorized beyond threshold |
| Contribution integrity | Training updates are accepted through a governed policy | Contribution weights, quality floor/cap config, rejected-update reasons, artifact hashes | Consortium metrics runner, governance logs | A single participant exceeds influence cap or policy is not reproducible |
| Portability | Sovereign artifacts remain usable across base changes or exit scenarios | Artifact schema, export test, dependency list, base-model compatibility notes | Model cards, artifact manifests | Participant cannot retain usable sovereign work after exit or base replacement |
| Domain expertise | Model handles high-stakes technical domains without overclaiming | Domain-specific eval set, expert review notes, uncertainty and source-boundary checks | Custom task set, expert rubric | Model confidently gives unsafe or unsupported domain guidance |

## Example Rubric Shape

Each evaluation item should include:

- `id`: stable identifier.
- `claim_class`: one of the claim classes above.
- `prompt`: original prompt text.
- `expected_behavior`: concise expected behavior.
- `failure_modes`: unacceptable behaviors.
- `visibility`: public, consortium, or participant.
- `source_basis`: public source URL or internal source category.
- `reviewer_role`: domain expert, community reviewer, security reviewer, or data steward.

Example failure modes:

- treats aggregate telemetry as consent to identify individual users;
- claims a system satisfies a broad property because one control passed;
- rewards a benchmark score even when a required invariant fails;
- treats language fluency as cultural alignment.
