# EXP-001: Validating Culturally Grounded Continued Pretraining

| Field | Value |
| :---- | :---- |
| Status | Pre-registered (June 13, 2026) · **executed** — results in [`FINDINGS.md`](FINDINGS.md) |
| Type | Research experiment specification |
| Date | June 13, 2026 |
| Validates | [TAP-003](../../tech-docs/architecture/decisions/adr-003-cultural-alignment.md), [TAP-005](../../tech-docs/architecture/decisions/adr-005-sovereign-pipeline.md) |
| Open questions addressed | C1, C8, T3, S3 ([open-questions.md](../../tech-docs/architecture/open-questions.md)) |

> This is the pre-registered design; the single-node go/no-go has been run. See
> [`FINDINGS.md`](FINDINGS.md) for outcomes. The consortium/aggregation extension
> (round two) is not yet run.

## Why this document exists

Tapestry's entire value proposition rests on one unvalidated hypothesis: that
continued pretraining (CPT) on culturally *grounded* data measurably shifts a
model's expressed cultural values toward the target culture. TAP-003 calls this
"the foundational hypothesis"; the Phase 5 option space asks it directly —
*"Has anyone tested this? What would a controlled experiment look like?"*
([5-architectural-options.md](../../tech-docs/architecture/5-architectural-options.md), Q1/Q12).

This document is the answer to "what would the experiment look like." It defines
a falsifiable test, the control structure that isolates *cultural grounding*
from *mere language exposure*, the measurement instruments, and the
success/failure thresholds — **pre-registered before any run**.

The existing `contrib/jneums-consortium-experiment` validates the *coordinator*
(weighting, capping, rejection, base movement) on a 32-dim toy model whose
"corpora" are byte-encoded `mod 128`. It cannot, and does not, test the cultural
hypothesis. This experiment does.

## The hypothesis under test

> **H1.** Continued pretraining on culturally grounded data produces a shift in
> the model's expressed values, measured on the Inglehart-Welzel / World Values
> Survey (WVS) framework, that is:
> - **(a) real** — larger than seed/paraphrase noise;
> - **(b) attributable to cultural content** — larger than the shift from
>   language-matched, value-neutral data in the same language;
> - **(c) representational, not surface mimicry** — visible in open-ended
>   behavior, not only in survey-answering mode;
> - **(d) capability- and safety-preserving** — does not destroy general
>   capability or erode base-model safety.

H1 is the conjunction of (a)–(d). Falsifying any clause falsifies the
architectural bet that *depth (full CPT) beats shallow alternatives (adapters,
prompting, post-training-only)* for cultural alignment.

## Experimental arms

A single before/after is worthless: the novel claim is *grounded ≠ linguistic*,
so the controls must separate those. All arms start from the **same base model**
and use **matched token budgets** and **matched hyperparameters**; only the CPT
corpus (or method) changes.

| Arm | Treatment | Isolates |
| :-- | :-------- | :------- |
| **0. Base** | no CPT | baseline coordinate + noise floor |
| **1. Grounded** *(treatment)* | CPT on culturally grounded target-culture corpus (law, civic, literature, ethics, community) | the core claim |
| **2. Language-matched** | CPT on same-language, value-*neutral* domains (manuals, weather, sports, technical) | "is it just speaking the language?" — the *Fluent but Foreign* control |
| **3. Grounded-translated** | Arm 1 corpus machine-translated into the base model's dominant language | "is it the cultural *content* or the language carrying it?" |
| **4. Surface-only** | base + prompt / light DPO toward the culture, no CPT | tests TAP-005's claim that CPT beats post-training-alone |
| **5. Neutral-prose** *(added)* | CPT on same-language, value-neutral, but **discursive** prose (matched register/genre to Arm 1, not terse technical text) | "is it the *register* (discursive prose), not the values?" — a tighter twin than Arm 2 |
| **6. Grounded-replay** *(added)* | Arm 1 grounded CPT mixed with a fraction of general value-neutral text (pretraining-distribution rehearsal) | separates genuine value-pull from **catastrophic forgetting**: does the shift survive when forgetting is rehearsed against? |

Arms 5–6 were added during the runs to answer confounds that surfaced (register;
forgetting vs. acquisition) — see [`FINDINGS.md`](FINDINGS.md).

**Decisive comparisons:**
- **Arm 1 vs Arm 2** — does grounding add anything beyond language? If they tie,
  the experiment reproduces *Fluent but Foreign* and H1(b) fails.
- **Arm 1 vs Arm 5** — is it the cultural *values* or just the discursive
  *register*? If the discursive-but-neutral twin moves like grounded, H1(b) is a
  genre artifact.
- **Arm 1 vs Arm 4** — does expensive CPT buy anything over cheap prompting? If
  they tie, the depth-over-shallow architectural bet is undercut.

## Measurement instruments

### Primary: WVS survey administration

Administer the WVS questionnaire items that define the two Inglehart-Welzel axes
(Traditional ↔ Secular-Rational; Survival ↔ Self-Expression), compute the two
factor scores, and plot the model's coordinate. Reuse the methodology of Tao et
al. (2024) and Sukiennik (2025) rather than inventing one.

- **Ground truth:** the WVS publishes each nation's real coordinates. Success is
  not "the model moved" but "the model moved **toward the target nation's actual
  WVS position**."
- **Robustness (mandatory):** randomize option order, paraphrase each item ≥3
  ways, sample at ≥2 temperatures, multiple seeds. Report the noise band; a shift
  inside it is not a shift.
- **Decontamination:** strip any WVS-resembling items from all CPT corpora, or we
  measure memorization, not alignment.

### Secondary: behavioral / scenario probes (deep vs. surface)

A model can answer surveys like a target-culture respondent while behaving
unchanged in the wild. Pair the survey with culturally loaded open-ended
dilemmas and advice tasks, scored by humans and/or a rubric-driven judge. **If
survey coordinates move but open-ended behavior does not, the shift is mimicry,
not representational change** — the single most important failure mode to catch.

### Guardrail: capability + safety retention

- **Capability:** MMLU + a target-language equivalent, before/after each arm.
- **Safety:** a refusal / red-team suite before/after (addresses S1/S3 — does
  grounded CPT erode base safety?).

## Materials

- **Model:** a real open model in the ~1–8B range (Qwen / Llama / Mistral class).
  Values are not represented in a toy model and cannot shift; ~1B is the likely
  floor for measurable value expression, ~7–8B to match the frontier-regime
  claim. *Runs used Qwen3-4B in both flavours — `Qwen3-4B-Instruct-2507` and
  `Qwen3-4B-Base`. This matters: the effect is confounded by alignment decay on the
  RLHF instruct model and only comes through cleanly on the base model, which is
  where the decisive result sits (see [`FINDINGS.md`](FINDINGS.md)).*
- **Pilot culture:** choose one with **large WVS distance** from the
  English/Protestant-Europe cluster (room to move) **and** corpus availability.
- **Corpora (Stage 0 — the real bottleneck):**
  - *Grounded* corpus (Arm 1/3): legal opinions, parliamentary records,
    literature, textbooks, ethics/religious texts, value-laden community content.
  - *Language-matched neutral* corpus (Arm 2): same language, value-neutral
    domains. **Validity of the whole result depends on Arms 1 and 2 differing
    only in cultural grounding and nothing else** (size, quality, recency,
    register held constant).

## Statistical design

- **Multiple seeds per arm** (the existing PoC is single-seed); report effect
  size with confidence intervals across seeds and paraphrases.
- **Pre-registered success threshold**, e.g.:
  > Arm 1 moves ≥ **X** map-units toward national ground truth **and**
  > ≥ **2σ** beyond Arm 2, with MMLU degradation ≤ **Y%** and no safety
  > regression beyond threshold **Z**.
  X, Y, Z fixed before any run. The concrete values used (and held constant across
  all runs): **X = 0.05** item-scale units, **σ-multiple = 2.0**, **Y = 0.10**
  capability drop, **Z = 0.10** refusal-rate drop — the four conjuncts enforced by
  `run_stats.py` / `cultural_cpt/stats.py`.

## Consortium extension (round two)

Everything above tests *single-node* CPT. The Tapestry-unique question (and T3,
non-IID convergence) is whether the cultural shift **survives FedAvg
aggregation**. Using the existing `ConsortiumCoordinator`:

1. Run grounded CPT for 2–3 distinct cultures (real bases, real corpora).
2. Aggregate via `_apply_weighted_average`, re-derive each sovereign fork,
   re-measure on the map.
3. **Plot all N nodes on the map across rounds.** Failure mode: points collapse
   toward the centroid (cultural homogenization) instead of holding distinct
   positions. This visualizes the drift problem directly and is likely the most
   informative single artifact the project can produce.

## Minimal go/no-go (recommended first run)

To get signal in days, not months:

- 1 high-WVS-distance culture, 1 real ~1–7B base.
- **3 arms only:** Base / Language-matched / Grounded.
- Primary instrument (WVS survey) + option-order randomization, 5 seeds.
- MMLU before/after as a capability sanity check.
- **Pass =** Grounded moves toward the nation's real WVS coordinates
  significantly more than *both* Base and Language-matched.

This converts the foundational hypothesis from a promise into evidence. The
behavioral probe (deep vs. surface) and the aggregation-survival test are the
round-two follow-ups once a basic effect is confirmed.

## What this does *not* test

- Whether the effect holds at frontier scale (>8B) — separate compute question
  (T1).
- Privacy/leakage from contributed weights (D3) — out of scope here.
- Whether DP-SGD preserves the effect (D4) — a follow-on once an unconstrained
  effect is established.

## References

- [Tao et al. "Cultural Bias and Cultural Alignment of Large Language Models." *PNAS Nexus* 3(9), 2024.](https://academic.oup.com/pnasnexus/article/3/9/pgae346/7756548)
- ["Fluent but Foreign: Even Regional LLMs Lack Cultural Alignment." arXiv:2505.21548, 2026.](https://arxiv.org/html/2505.21548)
- [Sukiennik. "An Evaluation of Cultural Value Alignment in LLM." arXiv:2504.08863, 2025.](https://arxiv.org/abs/2504.08863)
- [Inglehart & Welzel. "The WVS Cultural Map of the World." World Values Survey, 2005-2022.](https://www.worldvaluessurvey.org)
- [TAP-003: Cultural Alignment as the Primary Differentiator](../../tech-docs/architecture/decisions/adr-003-cultural-alignment.md)
- [TAP-005: Sovereign Model Pipeline](../../tech-docs/architecture/decisions/adr-005-sovereign-pipeline.md)
