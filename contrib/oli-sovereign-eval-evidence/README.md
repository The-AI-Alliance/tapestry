# Sovereign Evaluation Evidence Layer

Status: proposal / evaluation design scaffold.

This contribution proposes a small evidence layer for Tapestry's Evaluation &
Certification work. It connects cultural-alignment evaluation, data-sovereignty
evidence, privacy/security checks, and release gates so a Tapestry-derived model
can show what has been demonstrated before public claims are made.

It is intentionally scoped as documentation and templates. It does not include
raw datasets, private notes, model weights, or a runnable benchmark.

## Motivation

Tapestry's Phase 0 work already has active paths for:

- cultural-alignment experiments using the Inglehart-Welzel Cultural Map
  ([issue #22](https://github.com/The-AI-Alliance/tapestry/issues/22));
- policy and evaluation tooling choices
  ([issue #34](https://github.com/The-AI-Alliance/tapestry/issues/34));
- dataset discovery and data-management requirements
  ([issue #23](https://github.com/The-AI-Alliance/tapestry/issues/23) and
  [issue #27](https://github.com/The-AI-Alliance/tapestry/issues/27));
- consortium-training metrics and governed contribution policies
  ([issue #24](https://github.com/The-AI-Alliance/tapestry/issues/24)).

The missing bridge is an explicit evidence format:

1. Which claim is being made?
2. What evidence supports it?
3. Which evidence can be public?
4. Which evidence should remain private to a participant or consortium reviewer?
5. What result should block a release or certification claim?

This contribution provides a first pass at that bridge.

## Grounded Input From Adjacent Work

The examples below come from adjacent technical work in privacy-preserving
systems, security migration, and strict benchmark design. They are included as
transferable patterns, not as Tapestry data uploads.

### Aggregate-only evidence

Privacy-sensitive systems can still produce useful operational evidence when
reports stay aggregate-only and avoid re-identification. Useful signals include
system-level totals, coverage proxies, workflow counts, and caveats about what
the observable data can and cannot prove.

Evaluation lesson: useful operational evidence can be produced without turning a
privacy system into a surveillance system. Tapestry evaluation reports should
separate public aggregate metrics, consortium-private review artifacts, and
participant-private logs.

### Security-migration evidence

Security migration work often succeeds or fails on inventory, ownership, and
claim boundaries. The useful pattern is surface-based evidence: identify the
systems, artifacts, operators, and governance surfaces affected by a claim;
assign owners; track readiness levels; and avoid saying a system fully satisfies
a property before every relevant surface has been reviewed.

Evaluation lesson: Tapestry certification should reward precise, bounded claims.
For example, "this sovereign model has an auditable data-residency process for
these datasets" is stronger than "this model is sovereign."

### Strict benchmark gates

Strict technical benchmarks work best when they define pass/fail invariants
alongside scores. A result should fail when it violates correctness,
reproducibility, cleanup, leakage, or other stated invariants, even if the
headline metric improves.

Evaluation lesson: Tapestry release gates should define pass/fail invariants,
not only leaderboards. Cultural-alignment gains should not count as wins if they
break safety baselines, leak restricted data, destroy core capability, or hide
evaluation caveats.

### Claim hygiene

Adjacent evaluation and security work repeatedly benefits from separating claim
classes. Related ideas can connect under one architecture, but they should not
be collapsed into one vague promise.

Evaluation lesson: Tapestry evidence should keep claim classes separate:
cultural alignment, language capability, data sovereignty, privacy, safety,
capability, and portability each need their own evidence.

## Proposed Artifacts

This contribution starts with three documents:

- [evaluation-matrix.md](evaluation-matrix.md): claim classes, evidence, tools,
  visibility tiers, and blocking conditions.
- [dataset-card-template.md](dataset-card-template.md): a minimum dataset and
  provenance record for data that may support Tapestry training, tuning, or
  evaluation.
- [release-gate-checklist.md](release-gate-checklist.md): practical gates before
  a shared-base update, sovereign model release, or certification claim.

## Where This Could Fit

This proposal could remain in `contrib/` as an experimental evaluation scaffold,
or it could seed work in:

- `tech-docs/work-groups/evaluation-certification/`
- `tech-docs/work-groups/data-governance/`
- `tech-docs/work-groups/security-privacy/`

## Non-goals

- It does not solve cultural alignment.
- It does not propose a new model-training algorithm.
- It does not upload datasets.
- It does not imply that aggregate telemetry is an acceptable substitute for
  participant consent, privacy review, or data-governance policy.
- It does not collapse domain expertise into culture. Domain-specific evaluation
  can complement cultural evaluation, but it cannot replace it.

## Candidate Public References

- Project Tapestry issue #22:
  <https://github.com/The-AI-Alliance/tapestry/issues/22>
- Project Tapestry issue #34:
  <https://github.com/The-AI-Alliance/tapestry/issues/34>
- Project Tapestry issue #27:
  <https://github.com/The-AI-Alliance/tapestry/issues/27>
- AI Alliance Evaluation Reference Stack:
  <https://the-ai-alliance.github.io/eval-ref-stack/>
- AI Alliance Evaluation Is for Everyone:
  <https://the-ai-alliance.github.io/trust-safety-evals/>
- Unitxt:
  <https://www.unitxt.ai/en/latest/>
