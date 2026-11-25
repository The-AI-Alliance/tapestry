# Policy and Evaluation Tooling Options

| Field       | Value           |
| :---------- | :-------------- |
| Status      | Draft           |
| Confidence  | Med. High (4/5) |
| Created     | June 27, 2026   |
| Last Update | July 31, 2026   |

This note is a first-pass catalog for selecting tools that can implement
Tapestry evaluation, evidence, and policy checks. It supports the Evaluation &
Certification work group and issue
[#34](https://github.com/The-AI-Alliance/tapestry/issues/34).

The goal is not to choose one tool. Tapestry likely needs a small stack:
benchmark execution, task packaging, claim/evidence records, release gates, and
policy checks each have different responsibilities.

## Selection Criteria

| Criterion | Why it matters |
| :-------- | :------------- |
| Reproducible runs | Certification claims need stable inputs, versions, metrics, and outputs. |
| Custom task support | Cultural, sovereign, and domain-specific checks will not all be standard benchmarks. |
| Evidence export | Results should feed model cards, release gates, audit records, and reviewer workflows. |
| Visibility control | Public, consortium-private, and participant-private evidence need different handling. |
| Policy integration | Some gates are not scores; they are allow/deny decisions over evidence and metadata. |
| Low adoption friction | MVP tooling should work with Python, `uv`, local files, and CI-scale tests. |

## Candidate Tools

| Tool or approach | Best fit | Tapestry use | Cautions |
| :--------------- | :------- | :----------- | :------- |
| [Unitxt](https://www.unitxt.ai/en/latest/) | Task and benchmark packaging | Define reusable cultural, safety, capability, and domain evaluation tasks with consistent data/task/operator structure. | May require wrapper conventions for participant-private data and consortium-only artifacts. |
| [lm-evaluation-harness](https://eleuther.ai/research/evaluation/) | Broad LLM benchmark execution | Run established capability and regression suites so alignment work can be checked against common baselines. | Standard benchmarks do not prove cultural alignment or sovereignty claims by themselves. |
| [MLCommons AILuminate](https://mlcommons.org/ailuminate/) | Industry-leading benchmarks for AI safety and jail breaking behavior. Benchmarks for more areas are being developed. | Part of a standard suite of benchmarks we should run as baselines for any model and app work we do. | Not all the standard benchmark coverage we want. |
| [AI Alliance Evaluation Reference Stack](https://the-ai-alliance.github.io/eval-ref-stack/) | Reference architecture for evaluation systems | Align Tapestry's evaluation flow with adjacent AI Alliance evaluation patterns. | Needs mapping from general evaluation architecture to Tapestry-specific claim classes. |
| [Evaluation Is for Everyone](https://the-ai-alliance.github.io/trust-safety-evals/) | Evaluation process framing | Keep evaluation accessible to work groups and participants, not only benchmark specialists. | Process guidance still needs concrete Tapestry artifacts and gates. |
| [granite.trust.policy-tools](https://github.com/ibm-granite/granite.trust.policy-tools/) | Policy-oriented trust checks | Explore machine-readable trust and safety policy checks for model or release evidence. | Fit should be validated against Tapestry's claim classes before adoption. |
| [Open Policy Agent](https://www.openpolicyagent.org/) | General policy decision engine | Evaluate release gates over structured evidence, such as data-residency status, required benchmark presence, or approval metadata. | OPA decides over facts supplied to it; it does not generate evaluation evidence. |
| [every_eval_ever](github.com/evaleval/every_eval_ever) | "Every Eval Ever is a shared schema and crowdsourced eval database. It defines a standardized metadata format for storing AI evaluation results — from leaderboard scrapes and research papers to local evaluation runs — so that results from different frameworks can be compared, reproduced, and reused." | Capture our evaluations in this format. | |
| [Harbor Framework](https://github.com/harbor-framework/harbor) | "A framework for evaluating and improving agents." | Used by Skillberry (discussed below) | |
| Tapestry-specific templates | Claim and evidence records | Use dataset cards, release-gate checklists, and evaluation matrices for Tapestry-only claims. | Templates need automation hooks to avoid becoming stale paperwork. |

More general tools with evaluation features:

| Tool or approach | Best fit | Tapestry use | Cautions |
| :--------------- | :------- | :----------- | :------- |
| [Skillberry](https://github.com/skillberry-ai) | [Rubrica](https://github.com/skillberry-ai/rubrica), a skill-based test suite generator, and [simulation-harness](https://github.com/skillberry-ai/simulation-harness), for simulating real-world environments. Other tools support different aspects of developing agents. | Use for building complete applications? | |
| [AWS Emulator](https://www.allthingsdistributed.com/2026/11/aws-emulator-and-the-engineers-job-when-agents-write-the-code.html) | Similar features to Skillberry's simulator | | |


## Suggested MVP Stack

1. Use `lm-evaluation-harness` or Unitxt for repeatable model evaluation runs.
2. Use Tapestry-specific evidence templates to record claim boundaries,
   visibility tier, reviewer role, and blocking conditions.
3. Use a small policy layer, potentially OPA, for release-gate decisions over
   structured evidence.
4. Keep participant-private evidence out of public artifacts; publish summaries,
   hashes, versions, and caveats where appropriate.

## Claim-To-Tool Mapping

| Claim class | Primary tool need | Candidate starting point |
| :---------- | :---------------- | :----------------------- |
| Capability preservation | Standard benchmark runner | `lm-evaluation-harness`, Unitxt |
| Cultural alignment shift | Custom task packaging plus uncertainty reporting | Unitxt, Tapestry WVS-style harnesses |
| Safety preservation | Safety suite plus release gate | AI Alliance eval stack, policy tools, custom red-team checks |
| Data sovereignty | Evidence record plus policy check | Dataset cards, OPA, provenance logs |
| Privacy/leakage control | Specialized extraction or leakage tests | Custom harnesses, security work-group controls |
| Contribution integrity | Consortium metrics and governance record | `contrib/jneums-consortium-experiment`, governance logs |
| Certification readiness | Evidence bundle and blocking conditions | Tapestry release-gate checklist, OPA-style policy checks |

## Open Decisions

- Which evaluation artifacts should be public by default, and which should stay
  consortium-private or participant-private?
- Should Tapestry standardize first on Unitxt, `lm-evaluation-harness`, or a
  thin adapter that can emit both?
- Which release gates should be hard blockers for MVP model claims?
- What is the minimum machine-readable evidence schema needed before adding a
  policy engine?
- How should cultural-alignment evaluations record uncertainty, prompt-order
  sensitivity, and reviewer caveats?

## Near-Term Work

- Convert the existing evaluation matrix and release-gate checklist into a
  small machine-readable example.
- Prototype one capability benchmark and one Tapestry-specific cultural task
  with the same output schema.
- Define the first release-gate policy over that schema before adopting a larger
  policy engine.
