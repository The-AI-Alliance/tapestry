# Cultural CPT — Annotated Literature

*Reference document — June 2026*

---

## Purpose

EXP-001 ([cultural-cpt-validation](SPEC.md))
tests one hypothesis: that continued pretraining (CPT) on culturally *grounded*
data shifts a model's expressed values on the Inglehart–Welzel / World Values
Survey (WVS) map, and that the shift is **real, content-driven (not just
language), representational (not survey mimicry), and capability/safety-
preserving** (H1(a)–(d)). After seven runs the honest read is "underpowered and
high-variance at this scale" — `grounded − language` is **+0.040 ± 0.044
(z=0.91)**, small/positive/not-significant, with grounded CPT drifting slightly
*away* from the target and a one-line persona prompt beating CPT every time
([FINDINGS.md](FINDINGS.md)).

This document is an annotated reading list for whoever picks the experiment up.
Each entry: a summary, **how it relates to our current work** (with pointers to
specific runs), and additional context. Papers already cited in the ADRs/spec are
marked **[canon]**; the rest are newer work surfaced June 2026. Entries are
grouped by the open question they bear on, most decision-relevant first.

---

## 1. Evaluation reliability — the noise-band problem (our Runs 5–7)

### Khan, Casper, Hadfield-Menell. "Randomness, Not Representation: The Unreliability of Evaluating Cultural Alignment in LLMs." FAccT '25. [arXiv:2503.08688](https://arxiv.org/abs/2503.08688)

**Summary.** MIT CSAIL tests three assumptions behind cultural-alignment evals:
*stability* (alignment is a property of the model, not of eval design),
*extrapolability* (alignment on a few issues predicts alignment on others), and
*steerability* (you can reliably prompt a model into a culture). All three fail:
scores swing **up to 31.8% between runs**, evaluated dimensions don't predict
held-out ones, and prompt-steering is erratic. Single-run evaluation is
unreliable. They recommend **pre-registration (social-science style)** and
red-teaming.

**How it relates.** This is the single most validating paper for our method and
the most important one to internalize. Our entire Run 5→6→7 arc *is* this paper's
thesis playing out: Run 5's "decisive" z=7.26 and Run 6's "null" z=−0.29 were the
same quantity sampled twice against a measurement-only band; Run 7's corpus
resampling exposed the real ±0.044 spread. We independently re-derived their
"single runs are unreliable" finding and their "pre-register" prescription (our
go/no-go was pre-registered before any run). **Cite this** in the EXP-001 spec to
justify the pre-registered, multi-seed, corpus-resampled design — it converts our
"we were careful" into "we did what the field's strongest methods paper
demands."

**Additional context.** Their instability is *measurement* instability (prompt
format, option order). Ours compounds that with **corpus-sampling** instability
(which Wikipedia articles land in the draw) — a source they don't isolate because
they don't do CPT. Our resampling harness is arguably a step beyond their
protocol; worth framing that way if this work is ever written up.

---

## 2. The keystone result — regional ≠ culturally aligned (H1(b))

### Agarwal et al. "Fluent but Foreign: Even Regional LLMs Lack Cultural Alignment." [arXiv:2505.21548](https://arxiv.org/html/2505.21548v3) (v3) **[canon]**

**Summary.** Evaluates six Indic and six global LLMs on *values* and *practices*
grounded in nationally representative surveys + community QA. Indic models align
**no better** with Indian norms than global ones — a US respondent is a closer
proxy for Indian values than any Indic model. A 115-user study finds both global
and Indic suggestions Westernize/exoticize. Prompting and regional fine-tuning
fail to recover alignment and can **degrade** knowledge; they attribute this to
scarce culturally grounded pretraining data and call for native, community-
authored corpora and "thick × wide" evaluation.

**How it relates.** This is the paper EXP-001 exists to push past. Their negative
result is our Arm-1-vs-Arm-2 control's reason to exist: they show *language data
isn't enough*; we ask whether *grounded* data does better than language-matched
data on the same base. Our Run 7 is, so far, consistent with them — grounding
gives at most a small, non-significant edge and prompting/fine-tuning don't
deliver. Their "regional fine-tuning can degrade knowledge" is exactly our
**away-drift** observation (Runs 6–7: all CPT arms move *off* Egypt).

**Additional context.** v3 is newer than the version the ADRs link (they cite the
2026 HTML). Their "thick × wide" evaluation framing (population-scale + deep
community co-design) is a useful vocabulary for the round-two consortium plan.
Their headline that grounded pretraining data is *the* bottleneck matches our
recurring Stage-0 finding (we run ~300k tokens; real CPT is millions).

### Tao et al. "Cultural Bias and Cultural Alignment of Large Language Models." *PNAS Nexus* 3(9), 2024. [link](https://academic.oup.com/pnasnexus/article/3/9/pgae346/7756548) **[canon]**

**Summary.** Simulates the WVS on GPT models and computes similarity to real
national responses. All GPT models cluster with English-speaking / Protestant-
European countries on the Inglehart–Welzel map. Cultural *prompting* improves
alignment for 71–81% of countries on later GPT models.

**How it relates.** Our methodological parent: `wvs.py` reuses this survey-
administration-and-score approach, and our IW ground-truth coordinates come from
the same map. Their "cultural prompting helps a lot" is *also* our most robust
finding — `surface_only` (a one-line persona prompt) beats CPT in all seven runs.
The open EXP-001 question is whether CPT buys anything *over* their cheap
prompting baseline; so far it doesn't, at our scale.

**Additional context.** Their prompting result is measured GPT-side in English.
Our Run 3→4 finding that **measuring in Arabic changes the verdict** (prompting's
edge shrank from z=−2.16 to a tie when we measured in-language) suggests their
English-only protocol may *overstate* prompting's power for non-English cultures.
A genuine refinement we can contribute back.

### Sukiennik. "An Evaluation of Cultural Value Alignment in LLM." [arXiv:2504.08863](https://arxiv.org/abs/2504.08863) **[canon]**

**Summary.** Evaluates cultural value alignment across many models/cultures using
WVS- and Hofstede-style instruments; part of the methodological basis the spec
cites for survey administration.

**How it relates.** Second methodological reference (with Tao) for how we
administer and score the WVS battery. Worth a re-read when we revisit the
scoring/decontamination pipeline (`wvs.py`) and want to defend the instrument
choices.

---

## 3. Survey-answering vs. real behavior — the mimicry failure mode (H1(c))

### "From Surveys to Narratives: Rethinking Cultural Value Adaptation in LLMs." [arXiv:2505.16408](https://arxiv.org/abs/2505.16408)

**Summary.** Argues training/eval on WVS data alone is limited: **survey data
homogenizes cultural norms and interferes with factual knowledge.** They augment
WVS with (a) encyclopedic cultural content from **Wikipedia** and (b) scenario-
based narratives from **NormAd**, and find narrative augmentation "consistently
improves cultural distinctiveness" over survey-only adaptation, though downstream
effects vary.

**How it relates.** The most directly actionable paper for our *corpus* and our
*behavioral probe*. Two concrete hooks: (1) Their "survey data homogenizes /
interferes with factual knowledge" is a candidate explanation for our
**away-drift + flat behavioral probe** — if value-laden training data flattens
norms, grounded CPT could move the survey coordinate while leaving (or harming)
behavior, which is exactly our Run 5/7 pattern. (2) Their corpus *is*
structurally ours — Wikipedia-based cultural content — but they add **NormAd
scenario narratives**, which is a ready-made upgrade for our behavioral probe
(`behavior.py`) and possibly for the grounded corpus itself.

**Additional context.** NormAd is a benchmark of culturally grounded social
scenarios; adopting it would give the behavioral probe an external, citable
instrument instead of our hand-written dilemmas + embedding judge. Strong
candidate for the "upgrade the behavioral judge" item in the handoff.

### "CQ-Bench: Can LLMs Grasp Implicit Cultural Values?" [arXiv:2504.01127](https://arxiv.org/abs/2504.01127) **[canon]**

**Summary.** A benchmark for inferring *implicit* cultural values in conversation,
with three tasks of increasing difficulty: attitude detection, value selection,
value extraction. Larger models do better overall; performance varies by value
type (political values extracted well, >0.7 F1; religious values <0.6).

**How it relates.** The conceptual basis for our deep-vs-surface (representational
vs. mimicry) distinction. CQ-Bench measures whether a model *grasps* implicit
values rather than parrots survey answers — the same thing our free-form
behavioral probe tries to catch. Their religious-values weakness is notable given
our Egypt corpus is heavy on religion/family/ethics domains.

**Additional context.** Could serve as a third, external measurement instrument
alongside the WVS survey and the behavioral probe — a "does the model understand
the culture" axis distinct from "does the model answer surveys like the culture."

---

## 4. Language vs. content as the driver of value shift (our Arm 1 vs 2 vs 3)

### "The Echoes of Multilinguality: Tracing Cultural Value Shifts during LM Fine-tuning." [arXiv:2405.12744](https://arxiv.org/pdf/2405.12744)

**Summary.** Studies how the *language* of fine-tuning data influences the
cultural values a model expresses across test languages. Finds cultural values
**bleed across languages** during fine-tuning (cross-lingual transfer), and uses
a **training-data-attribution** method to identify which fine-tuning examples and
source languages instigate value shifts.

**How it relates.** Directly informs the Arm 1 / Arm 2 / Arm 3 design — the whole
point of which is to separate *language exposure* from *cultural content*. Their
cross-lingual "value bleed" predicts that our Arabic neutral corpus (Arm 2) would
itself move the cultural coordinate — which is exactly what we see (Arm 2 pushes
*away* from Egypt: Run 5 −0.078, Run 6 −0.047). Their training-data-attribution
method is a tool we could borrow to answer the **away-drift** question: *which
documents* in a draw push the coordinate off-target?

**Additional context.** This reframes our `grounded_translated` (Arm 3) result.
Run 6 found grounded ≈ grounded_translated (z=0.05) — content survives
translation. "Echoes" provides the mechanism (values transfer across the language
carrier) and a method to localize *which content* carries the signal. The most
useful methods-transfer in this list for the away-drift investigation.

### Self-Pluralising Culture Alignment for Large Language Models. [arXiv:2410.12971](https://arxiv.org/pdf/2410.12971)

**Summary.** Method for aligning a single model to *many* cultures simultaneously
(rather than forking one model per culture), addressing the homogenization
pressure of single-distribution alignment.

**How it relates.** Relevant to the **consortium round-two** framing (one shared
base serving many sovereign cultures) — an alternative to per-culture forks +
FedAvg. Worth comparing against the fork-and-aggregate architecture (TAP-001/002)
if homogenization (below) proves fatal to merging.

---

## 5. Cheaper alternatives to CPT — the depth-over-shallow bet (our Arm 4)

### "Cultural Value Alignment via Latent Activation Steering in LLMs." [arXiv:2605.26365](https://arxiv.org/html/2605.26365) (May 2026)

**Summary.** Two-part framework: (1) extract a model's *implicit* cultural
coordinates from **token probabilities over ~300 situational dilemmas** (not
direct prompts — direct WVS prompting "fails to access latent cultural depth,
leading to safety-aligned refusals or neutral responses"); (2) **activation
steering** shifts cultural values during the forward pass *without retraining*.
Two key findings: substantial **variation across models** in steerability, and
**latent entanglement** — steering one cultural dimension induces shifts in
another, because cultural values are encoded as *coupled* structures, limiting
precise alignment.

**How it relates.** Two big implications. (1) **Measurement:** their token-
probability-over-dilemmas probe is a more robust instrument than direct survey
prompting and dovetails with our finding that *how* you measure dominates the
result (Run 3 EN vs Run 4 AR). Their "direct prompting hits refusals/neutral
answers" critique is a caution for our WVS administration. (2) **The away-drift
mystery:** their **latent entanglement** is the cleanest mechanistic candidate
for why our absolute grounded shift is *negative* — if the IW axes are coupled in
the model, CPT that moves one axis toward Egypt may drag the other off, netting a
move *away* from the 2D target even when one component improves. Worth checking
our per-axis (ts/ss) deltas against this prediction.

**Additional context.** Activation steering is a candidate *fifth arm* — a cheap,
no-retrain alternative to CPT in the same family as `surface_only`. If steering
matches CPT, that further undercuts the depth-over-shallow bet; if CPT moves
behavior where steering can't, that's the evidence EXP-001 most needs. Newest
paper in this list (May 2026).

---

## 6. Does the shift survive aggregation? — consortium round-two (T3, homogenization)

### "On the Limits of Model Merging for Multilinguality in Pre-Training." [arXiv:2605.25846](https://arxiv.org/html/2605.25846) (May 2026)

**Summary.** Controlled comparison of three routes to a multilingual model: mixed
pretraining data, monolingual pretraining + post-hoc **merging**, and pure
monolingual pretraining. Headline: **merging independently pre-trained
monolingual models causes performance collapse from interference.** Merging works
only when models share **representational similarity** — a prerequisite that
monolingual *pretraining* breaks (unlike fine-tuning, where merging is forgiving).
"The flexibility of merging in fine-tuning does not extend trivially to language-
specific pre-training."

**How it relates.** The most consequential paper for the round-two plan. Our
aggregation-survival experiment (`run_aggregation.py`) FedAvg-merges per-culture
forks that diverged via **continued pretraining** — precisely the regime this
paper says collapses. It predicts our "plot all N nodes, watch for centroid
collapse" artifact may collapse for *representational* reasons, independent of any
cultural-averaging effect. **Read this before spending GPU on round two.** It
argues for (a) a representational-similarity check between forks before merging,
and (b) considering mixed-data or smarter-merge alternatives over naïve FedAvg.

**Additional context.** Distinguishes *fine-tuning* merging (the TIES/DARE/Model-
Soups canon in ADR-007, which works) from *pretraining* merging (which doesn't) —
a distinction the ADRs don't yet draw. Tapestry's CPT-then-FedAvg loop
(TAP-004) sits on the dangerous side of that line. Important ADR caveat to add.

### "Model Merging in the Era of LLMs: Methods, Applications, and Future Directions." [arXiv:2603.09938](https://arxiv.org/pdf/2603.09938) (2026 survey)

**Summary.** Current survey of model-merging methods, when they help, and where
interference degrades the merge ("not all checkpoints contribute equally").

**How it relates.** The menu to pick a more robust aggregation than plain FedAvg
if the limits paper above bites. Useful for choosing a merge operator in
`run_aggregation.py` beyond `_apply_weighted_average`.

### "Merge and Conquer: Instructing Multilingual Models by Adding Target-Language Weights." [arXiv:2603.28263](https://arxiv.org/pdf/2603.28263)

**Summary.** Builds multilingual capability by *adding* target-language weight
components — a targeted alternative to full averaging.

**How it relates.** A possible aggregation primitive for adding a culture to the
shared base without the full-merge interference the limits paper warns about. Keep
for round-two design options.

### "A Game-Theoretic Negotiation Framework for Cross-Cultural Consensus in LLMs." [arXiv:2506.13245](https://arxiv.org/pdf/2506.13245)

**Summary.** Frames reconciling divergent cultural perspectives as a negotiation/
consensus problem rather than weight averaging.

**How it relates.** A conceptual alternative to averaging-toward-the-centroid (our
homogenization failure mode). If FedAvg collapses distinct cultures toward the
mean, a negotiation-based reconciliation is a different way to keep nodes
distinct while sharing a base. Speculative but on-theme for round two.

---

## 7. Safety guardrail — H1(d), and the field-wide warning

### "Assessing Socio-Cultural Alignment and Technical Safety of Sovereign LLMs." [arXiv:2510.14565](https://arxiv.org/pdf/2510.14565)

**Summary.** Introduces a dataset + framework to jointly evaluate sovereign LLMs'
socio-cultural alignment *and* technical safety. Finds sovereign LLMs "do not
always meet the popular claim that these models serve their target users well,"
and — critically — that **chasing unvalidated cultural-alignment claims leads
developers to overlook safety attributes.** Calls for broader, well-grounded,
practical evaluation criteria.

**How it relates.** Almost a direct critique of the EXP-001 risk surface, and a
strong endorsement of our H1(d) (capability + safety preserving) conjunct and the
new `safety.py` refusal guardrail. Their core warning — "don't let the cultural
claim eclipse safety" — is exactly why our pre-registered decision gates on
`max_safety_drop` and `max_capability_drop`, not just the cultural shift. Cite to
justify keeping the guardrails as hard conjuncts rather than nice-to-haves.

**Additional context.** Their joint cultural-+-safety dataset is a candidate
external instrument to replace/augment our deterministic refusal probe (which is
intentionally content-free). Pairs well with the real MMLU/ArabicMMLU capability
path that's wired but not yet hardware-tested.

### "Culturally Grounded Personas in LLMs: Characterization and Alignment with Socio-Psychological Value Frameworks." [arXiv:2601.22396](https://arxiv.org/html/2601.22396) (Jan 2026)

**Summary.** Examines how LLM-generated culturally grounded *persona* profiles
align with WVS / Inglehart–Welzel frameworks — positioning on the cultural map
and demographic-level consistency with human group patterns.

**How it relates.** Newest WVS/IW measurement methodology; worth diffing their
factor-scoring against our `wvs._from_map` rescaling. Their persona approach is
adjacent to our `surface_only` prompt arm — how they construct and validate
personas could sharpen our prompting baseline (the arm that keeps winning).

---

## 8. Distributed-training infrastructure (TAP-004/005/006)

### Google DeepMind. "Decoupled DiLoCo." (blog, Apr 23 2026). [link](https://deepmind.google/blog/decoupled-diloco/)

**Summary.** Combines Pathways (orchestrating heterogeneous chips at independent
speeds) with DiLoCo to split training across asynchronous compute "islands."
Reports **88% goodput under aggressive hardware-failure simulation vs 27%** for
standard methods, and inter-datacenter bandwidth cut from 198 → 0.84 Gbps.

**How it relates.** A material update to the DiLoCo (2311.08105) our ADR-004/006/
007 cite as the distributed-training basis. The async-island + failure-resilience
story maps onto the consortium's geo-distributed sovereign nodes. Refresh the ADR
references; the resilience numbers strengthen the consortium-feasibility case.

### Douillard et al. "DiLoCo" [arXiv:2311.08105](https://arxiv.org/abs/2311.08105) **[canon]** · Jaghouar et al. "OpenDiLoCo" [arXiv:2407.07852](https://arxiv.org/abs/2407.07852) **[canon]** · "Scaling Laws for DiLoCo" [arXiv:2503.09799](https://arxiv.org/abs/2503.09799) **[canon]**

**Summary.** The DiLoCo line: outer-optimizer-over-aggregated-deltas (reduces to
FedAvg when the outer optimizer is SGD@1); OpenDiLoCo's open, cross-continent
reproduction at 90–95% utilization; and scaling behavior at larger model sizes.

**How it relates.** The training-loop foundation for TAP-004. Already cited;
listed here for completeness since Decoupled DiLoCo supersedes them.

### "Partial Parameter Updates for Efficient Distributed Training." [arXiv:2509.22418](https://arxiv.org/pdf/2509.22418) · "Distributed and Decentralised Training: Technical Governance Challenges." [arXiv:2507.07765](https://arxiv.org/pdf/2507.07765)

**Summary.** Partial-parameter updates reduce communication/compute in distributed
training; the governance paper maps the technical-governance challenges of
decentralized training.

**How it relates.** The first is an efficiency lever for the consortium loop (and
adjacent to our single-GPU full-CPT constraints). The second is direct input for
the governance ADRs (TAP-002/008) — who controls what in a decentralized training
consortium.

### "Buy versus Build an LLM: A Decision Framework for Governments." [arXiv:2602.13033](https://arxiv.org/abs/2602.13033) **[canon]**

**Summary.** Decision framework for governments choosing between procuring vs.
building an LLM. Cited in ADR-001/006 for the phased-base-model and sovereignty
rationale.

**How it relates.** Already canon; informs the strategic framing (why sovereign
build at all) rather than the experiment.

---

## Reading order (recommended)

1. **Randomness, Not Representation** (2503.08688) — why our Run 5/6/7 arc looks
   the way it does; the methods bar.
2. **Fluent but Foreign** v3 (2505.21548) — the result we're trying to beat.
3. **From Surveys to Narratives** (2505.16408) — our corpus, plus a behavioral-
   probe upgrade (NormAd).
4. **Latent Activation Steering** (2605.26365) — a mechanism for the away-drift
   (entanglement) and a cheap rival to CPT.
5. **Echoes of Multilinguality** (2405.12744) — language-vs-content; a method to
   localize which documents drift.
6. **Limits of Model Merging** (2605.25846) — read before round-two aggregation.
7. **Sovereign LLM safety** (2510.14565) — why the guardrails stay hard conjuncts.

## Cross-references to our work

| Our finding (FINDINGS.md) | Paper that explains / contextualizes it |
| :-- | :-- |
| Run 5 z=7.26 vs Run 6 z=−0.29 reconciled by resampling | Randomness, Not Representation (2503.08688) |
| Away-drift: absolute grounded shift negative (Runs 6–7) | Latent entanglement (2605.26365); value-bleed (2405.12744); Fluent-but-Foreign "fine-tuning degrades knowledge" |
| Neutral Arabic CPT pushes *away* from Egypt | Cross-lingual value bleed (2405.12744) |
| Prompting beats CPT every run | Tao et al. cultural prompting (PNAS Nexus); CPT-not-yet-better than shallow |
| Flat free-form behavioral probe | Survey homogenizes / survey≠behavior (2505.16408); CQ-Bench implicit values |
| Round-two FedAvg may collapse | Limits of model merging in pre-training (2605.25846) |
| Guardrails as hard conjuncts | Sovereign LLM safety (2510.14565) |
</content>
</invoke>
