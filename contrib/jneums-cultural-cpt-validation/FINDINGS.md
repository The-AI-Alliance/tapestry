# EXP-001 — Cultural CPT validation: findings

Does continued pre-training (CPT) on a value-laden cultural corpus shift a
language model's measured values toward that culture — and does it do so *beyond*
what same-language, value-neutral text would? This is the findings record for
twelve real runs of the validation harness ("real" = a real base model under
`--mode hf` **and** a real corpus under `--corpus-path`; toy/smoke numbers are not
recorded here). Run artifacts (`runs/…/result.json`) are git-ignored; the tables
below are the record. Corpora regenerate from `titles/egypt.ar.json` via
`fetch_corpus.py`.

## Headline — a real but shallow, survey-level effect

Stated honestly, the whole body of work lands on a **bounded** result, and the bound is
the contribution.

**The one clean positive.** On the base model (Qwen3-4B-Base), continued pre-training on a
value-laden Arabic corpus shifts the model's **survey-measured** values toward Egypt **more
than a same-language, value-neutral corpus does**, and this **survives corpus resampling**:
`grounded − language = +0.051 ± 0.017, z = 2.97` across 4 independent corpus draws, capability
and refusal preserved (drops +0.010 / −0.031, inside the ≤0.10 guardrails). That is the single
statistically robust result here (Run 11), and it is real — value *content* moves the model
more than language alone. (On the **instruct** model it does not survive resampling, z=0.03;
the base model, with no RLHF to erode, is the substrate.)

**Three follow-ups bound it, and none was a win.** The effect is **survey-level and shallow:**

- **It does not reach behavior (H1c).** With a probe shown to be sensitive — an explicit persona
  prompt moves open-ended behavior **+0.18 (~1.8σ)** — grounded CPT moves the *survey* (+0.021)
  but **not behavior** (−0.086 ± 0.098 ≈ 0). A survey-behavior **dissociation**.
- **It does not scale to a clean absolute PASS (Run 12).** Scaling to 10 epochs lifts the
  absolute shift over 0.05 (mean +0.085), but the relative/value-specific effect then **collapses
  to z=1.39** — because the value-*neutral* arm also drifts Egypt-ward at scale (~+0.04/draw).
  Magnitude and value-specificity **trade off**, so part of the absolute movement is
  language/topic, not values. The pre-registered four-conjunct PASS was never achieved (the
  *absolute* conjunct fails at +0.039; the relative claim is what holds).
- **It survives aggregation but with no demonstrated value (T3).** Across FedAvg rounds the
  cultures stay separable (they don't homogenize; the merge is **dilutive, not destructive** —
  retained ≈ 1/√N) — but every metric is on the forks *post-CPT*, never the merged model, and
  there is no control showing aggregation *buys* anything.

**Net.** Culturally-grounded CPT produces a **real but shallow, survey-level value shift** —
statistically clean, robust to corpus resampling and to FedAvg aggregation, but **not deep**: it
does not reach open-ended behavior, and at scale it is hard to fully separate from language/topic
drift. The strong-form (absolute / behavioral / value-add) claims are **not** established; the
defensible claim is narrow and worth stating exactly: *value-laden CPT moves a base model's
stated values toward the target culture more than language-matched text does, and that survey
signal survives resampling and aggregation — but it is survey-level, not behavioral.*

**The durable contributions are as much methodological as empirical:** a real end-to-end
go/no-go harness; a cross-*corpus* resampling protocol (the cross-*seed* band understated the
noise — Run 7); a behavioral probe whose embedding judge had to be rebuilt (**SemAxis
cosine-difference**, ~4× the dynamic range) before it could see anything; and FedAvg **merge
diagnostics** that separate genuine homogenization from mere dilution. See
[Status & next steps](#status--next-steps) for what a win would actually require.

## The pre-registered test

**Hypothesis.** H1(a): grounded CPT moves the model's Inglehart–Welzel coordinate
toward the target culture. H1(b) — the novel, load-bearing claim: it does so
*beyond* a same-language, value-neutral corpus (so the effect is cultural
*content*, not just the language or the genre).

**Decision rule (fixed before the runs).** A run PASSes only if **all four**
conjuncts hold:

| conjunct | threshold | what it guards against |
| :-- | :-- | :-- |
| absolute grounded shift toward target | **≥ 0.05** | effect exists at all (H1a) |
| grounding effect `grounded − language` | **z ≥ 2.0**, positive | it's content, not language (H1b) |
| capability drop (MMLU EN+AR) | **≤ 0.10** | CPT didn't break the model |
| refusal-rate drop | **≤ 0.10** | CPT didn't erode safety |

**The decisive comparison** is `grounded − language` (grounded minus the
language-matched twin). The z is `effect / noise-band-σ`; **which σ** is the whole
story of this experiment — see the run log and Interpretation.

## Setup common to all runs

- **Base model:** Runs 1–2 `Qwen/Qwen2.5-1.5B-Instruct`; Runs 3–11
  `Qwen/Qwen3-4B-Instruct-2507`; the de-confound and decisive runs (10b, 11b) also
  use `Qwen/Qwen3-4B-Base`. Full-parameter CPT, bf16, 8-bit Adam from Run 3 on.
- **Culture / target:** Egypt. From Run 11 the target is the **exact EVS/WVS-2023
  cultural-map factor score** (`_from_map(-0.8544, -2.2318)` → coord **(ts −0.34,
  ss −0.89)** — mildly traditional, far survival-pole). Runs 1–10 used an eyeballed
  map-rescaled target (ts −0.72, ss −0.52); the correction matters only for the
  *absolute*-shift conjunct, never for the relative comparisons.
- **Instrument:** canonical 10-item Inglehart–Welzel battery (`wvs.py`), ≥3
  paraphrases/item, expected-value scoring. Survey in **English** (Runs 1, 3) then
  **Arabic** (Run 4 on, matching the corpus language).
- **Corpus:** Arabic Wikipedia, same-source/different-domain twin — grounded =
  law/religion/family/civic/ethics; language-matched = weather/sports/technical/
  math/biology — full articles chunked to 1024-token windows. Later runs add the
  `grounded_translated` (ar→en MT), `neutral_prose` (discursive-but-value-neutral
  register twin), and `grounded_replay` (general-English rehearsal mix) arms.
- **lr** 2e-5. **Hardware:** RTX 5090 (Vast.ai self-rental; the two-GPU runs use a
  2× 5090 box via `deploy/run_two_gpu.sh`).
- **Metric:** per-arm **shift toward the target vs. Base** (positive = moved toward
  the national coordinate). `surface_only` is a one-line persona prompt (no CPT) —
  the shallow baseline the deep lever is measured against.

## Run log

The twelve runs below are the chronological record; the [Interpretation](#interpretation)
synthesises what they collectively show. The short version of the arc: early
single-corpus "passes" were artifacts of a too-narrow noise band; once the band is
estimated honestly (corpus resampling) and the confounds are stripped (register
twin, base model), a small-but-real relative effect remains.

### Run 1 — single seed (pilot)

`run.py`, epochs 2, per-domain 6, corpus ≈32k / 30k tokens (grounded / matched).

| arm | survey shift | behavior shift | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | −0.038 | −0.010 | 0.75 |
| grounded | −0.029 | −0.018 | 0.75 |
| surface_only (prompt) | +0.141 | +0.040 | 0.75 |

grounded − language **+0.009**; grounded − surface **−0.170**. Null at this
micro-scale.

### Run 2 — multi-seed go/no-go (pre-registered)

`run_stats.py`, seeds 0/1/2, epochs 6, per-domain 8, corpus ≈50k / 59k tokens.
Thresholds (fixed before the run): shift ≥ 0.05 **and** (grounded−language) z ≥ 2
with positive sign **and** capability drop ≤ 0.10.

| arm | survey shift (mean ± std) | behavior shift | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | −0.048 ± 0.021 | −0.030 ± 0.011 | 0.75 |
| grounded | −0.029 ± 0.007 | −0.007 ± 0.005 | 0.75 |
| surface_only (prompt) | +0.151 ± 0.027 | +0.045 ± 0.010 | 0.75 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| grounded − language | **+0.019 ± 0.013** | **+1.41** |
| grounded − surface | −0.179 ± 0.021 | −8.57 |

capability drop 0.000.

#### VERDICT: **FAIL**

shift −0.029 (≥0.05? no); grounding effect z=1.41 (≥2? no); capability drop
0.000 (≤0.10? yes).

### Run 3 — Qwen3-4B, scaled corpus, multi-seed

`run_stats.py`, **`Qwen/Qwen3-4B-Instruct-2507`**, seeds 0/1/2, epochs 4,
per-domain 18 / max-words 6000 → corpus ≈**151k / 189k** tokens. Full-parameter
CPT fit one 32GB 5090 via 8-bit Adam (bitsandbytes) + base-on-CPU + gradient
checkpointing.

| arm | survey shift (mean ± std) | behavior shift | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | −0.006 ± 0.017 | −0.187 ± 0.011 | 1.00 |
| **grounded** | **+0.023 ± 0.047** | −0.160 ± 0.038 | 0.92 |
| surface_only (prompt) | +0.186 ± 0.034 | +0.040 ± 0.025 | 0.75 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| grounded − language | **+0.028 ± 0.038** | **+0.75** |
| grounded − surface | −0.163 ± 0.076 | −2.16 |

#### VERDICT: **FAIL** — shift +0.023 (≥0.05? no); z=0.75 (≥2? no); capability fine.

### Run 4 — Qwen3-4B, **survey administered in Arabic**

Identical to Run 3 (same model, same ~151k/189k-token corpus, 3 seeds, 4 epochs)
except the survey + behavior probe are administered in **Arabic** instead of
English (`--instrument-lang ar`), removing the content-vs-language confound: the
corpus is Arabic, so measure in Arabic.

| arm | survey shift → Egypt | behavior shift | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | **−0.105 ± 0.043** | −0.200 | 0.75 |
| **grounded** | **+0.035 ± 0.048** | −0.232 | 0.83 |
| surface_only (prompt) | +0.063 ± 0.010 | +0.047 | 0.75 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| grounded − language | **+0.140 ± 0.091** | **+1.54** |
| grounded − surface | −0.028 ± 0.056 | −0.50 |

#### VERDICT: **FAIL** — shift +0.035 (≥0.05? no); z=1.54 (≥2? no). But the closest yet.

#### Language of measurement matters a lot (Run 3 EN vs Run 4 AR, all else equal)

| survey lang | grounded shift | grounded − language | grounded − surface |
| :-- | --: | --: | --: |
| English (Run 3) | +0.023 | +0.028 (z=0.75) | **−0.163 (z=−2.16)** |
| Arabic (Run 4) | +0.035 | **+0.140 (z=1.54)** | −0.028 (z=−0.50) |

Two clean shifts from measuring in the corpus's own language:
1. **The decisive grounding-beyond-language effect grew ~5×** (+0.028 → +0.140).
   In Arabic, neutral text pushes *away* from Egypt (−0.105) while grounded text
   pushes *toward* it (+0.035) — the H1(b) contrast, much sharper.
2. **Prompting stops beating CPT.** In English the persona prompt dominated
   (z=−2.16); in Arabic that advantage evaporates (z=−0.50). The earlier
   "cheap prompting beats expensive CPT" result was partly an English-measurement
   artifact — important for the depth-over-shallow architectural bet.

Still FAIL (effect grew but so did variance; z=1.54 < 2, shift < 0.05), but this
is the first run where the *decisive* comparison is clearly the largest signal,
and where CPT is no longer dominated by prompting.

### Run 5 — everything stacked (4B + Arabic survey + free-form behavior + 2× corpus)

Qwen3-4B, Arabic survey (`--instrument-lang ar`), **behavioral probe in free-form
generate mode** (model writes an action, a multilingual-embedding judge scores
it — `--behavior-mode generate`), corpus scaled to **271k / 289k tokens** via
Wikipedia category fetching, 3 seeds, 4 epochs.

| arm | survey shift → Egypt | behavior shift (generate) | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | **−0.078 ± 0.018** | −0.007 ± 0.044 | 1.00 |
| **grounded** | +0.003 ± 0.029 | −0.021 ± 0.037 | 1.00 |
| surface_only (prompt) | +0.063 ± 0.010 | −0.003 ± 0.006 | 0.75 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| **grounded − language** | **+0.080 ± 0.011** | **+7.26** ✅ |
| grounded − surface | −0.060 ± 0.029 | −2.09 |

#### VERDICT: **FAIL** — but the decisive comparison finally passes.

The pre-registered rule has three conjuncts; for the first time the **grounding
effect clears 2σ** (z=7.26, positive) and capability is fine. It still FAILs only
on the **absolute** grounded shift: +0.003 < 0.05.

#### What actually happened — grounding *prevents drift* more than it *pulls*

More tokens **collapsed the variance** (grounded−language std 0.091→0.011), so the
effect that was directionally right but noisy in Run 4 is now **robustly
significant**. But the mechanism is subtler than "grounded CPT pulls toward
Egypt": at this scale **neutral Arabic CPT pushes the model *away* from Egypt
(−0.078)** while **grounded CPT holds position (+0.003)**. The grounding effect is
real and significant (+0.080, z=7.26) but is mostly *grounded avoiding the
away-drift that value-neutral text causes* — not a large active pull. That is
still H1(b) ("grounding ≠ just language"), now supported; it is H1(a) in the
strong absolute sense that hasn't cleared the bar.

Other notes: prompting's edge over CPT keeps shrinking (grounded−surface z went
−8.57 → −2.16 → −2.09). The **free-form behavioral probe** (now trustworthy: the
model generates, an embedding judge scores) shows **no arm moves open-ended
behavior** toward Egypt — including the prompt. With the survey also ~flat for
grounded, there is no strong mimicry signal, but also no behavioral shift to
speak of at this scale. Capability "drop" is again toy-MMLU noise (CPT arms hit
1.00 on 4 questions).

### Run 6 — first `grounded_translated` arm + real guardrails (and a non-replication)

Qwen3-4B, Arabic survey, generate-mode behavior, 3 seeds, 4 epochs — same shape
as Run 5, but three things are new and the corpus was **freshly regenerated**
(228/255/228 docs → **300k / 288k / 291k tokens** for grounded / language_matched
/ grounded_translated):

1. **Arm 3 (`grounded_translated`) is built and run for the first time** — the
   grounded Arabic corpus machine-translated ar→en (Opus-MT), ~291k tokens, so
   the decisive *content-vs-language-carrier* comparison is a real number, not a
   skipped 0.0.
2. **Real capability guardrail** — `cais/mmlu` (EN) + `MBZUAI/ArabicMMLU` (AR)
   scored by `score_continuation`, replacing the toy 4-item stub.
3. **Safety/refusal guardrail** — log-prob refusal-vs-compliance probe (EN/AR).

~5.5 h on one RTX 5090 (3 CPT arms × 3 seeds; the harness trains batch-size-1, so
the extra arm over Run 5 is expensive).

| arm | survey shift → Egypt | behavior shift | capability | refusal |
| :-- | --: | --: | --: | --: |
| base | — | — | 0.34 | 1.00 |
| language_matched | −0.047 ± 0.015 | −0.028 ± 0.036 | 0.35 | 1.00 |
| **grounded** | **−0.055 ± 0.029** | −0.049 ± 0.004 | 0.34 | 0.96 |
| grounded_translated | −0.059 ± 0.105 | −0.014 ± 0.027 | 0.34 | 1.00 |
| surface_only (prompt) | +0.063 ± 0.010 | −0.004 ± 0.006 | 0.34 | 1.00 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| grounded − language | **−0.008 ± 0.027** | **−0.29** |
| grounded − translated | +0.005 ± 0.090 | +0.05 |
| grounded − surface | −0.118 ± 0.019 | −6.27 |

#### VERDICT: **FAIL** — and Run 5's decisive effect did **not** replicate.

shift −0.055 (≥0.05? no); grounding effect z=−0.29 (≥2? no); capability drop
−0.003 (≤0.10? yes); safety drop +0.042 (≤0.10? yes).

Three things to take seriously, honestly:

1. **The grounding-beyond-language effect vanished.** grounded − language went
   from Run 5's **+0.080 (z=7.26)** to **−0.008 (z=−0.29)** — null. The corpus was
   freshly fetched (Wikipedia category membership/ordering drifts between pulls),
   so Run 6 is effectively a *replication on a new corpus sample of the same
   protocol* — and the headline H1(b) result did not hold. This is consistent
   with the standing caveat that the cross-seed noise band is **measurement-only**
   (HF training is deterministic across seeds), so Run 5's z=7.26 was optimistic;
   the real, corpus-resampling variance is much larger. The effect is **fragile to
   corpus resampling**.
2. **All three CPT arms drift *away* from Egypt** (grounded −0.055, language
   −0.047, translated −0.059). Run 5's "grounded holds position while neutral
   drifts away" mechanism did not reappear — here grounded drifts as much as the
   neutral twin. And **`grounded ≈ grounded_translated`** (z=0.05): whether the
   cultural content arrives in Arabic or MT-English makes no measurable
   difference — but both are ~null/negative, so this is "equally not-working,"
   not a clean content-over-language win.
3. **The guardrails are now real and both pass.** Capability is flat at ~0.34
   across every arm (real MMLU — the toy "improves to 1.00" artifact is gone), so
   CPT preserved knowledge; refusal stays ~1.00 (grounded 0.96). Prompting again
   crushes CPT (grounded − surface z=−6.27); `surface_only` is the **only** arm
   that moves toward Egypt (+0.063).

Net: the more rigorous harness (real capability/safety, the translated arm, a
fresh corpus) gives a **soberer** read than Run 5. The novel claim (grounded ≠
language-matched) does **not** survive a corpus resample; the cultural shift from
micro-scale CPT is small, noisy, sometimes negative, and reliably beaten by a
one-line persona prompt.

### Run 7 — corpus-RESAMPLED go/no-go (the real noise band)

The first six runs each measured `grounded − language` on **one** corpus draw and
reported a z against the cross-*seed* band — but HF training is deterministic
across seeds, so that band is measurement-only and understates the truth. Run 5
(z=7.26) and Run 6 (z=−0.29) are just two single draws of a high-variance quantity
disagreeing. Run 7 measures the variance directly: **4 independent corpus draws**
(each a deterministic 70%-token-mass subsample of a fresh ~300k-token pool), the
full multi-seed experiment per draw, and the go/no-go decided on the **cross-draw**
spread. Qwen3-4B, 3 seeds, Arabic survey, generate-mode behavior, `TRANSLATE=0`
(no Arm 3 — not needed for this comparison). ~4.5 h on one RTX 5090.

| draw | grounded shift | grounded − language | grounded − surface |
| :-- | --: | --: | --: |
| 0 | −0.051 | +0.038 | −0.114 |
| 1 | +0.002 | +0.064 | −0.060 |
| 2 | −0.079 | −0.021 | −0.142 |
| 3 | −0.008 | +0.078 | −0.070 |

| comparison (across draws) | mean ± std | z |
| :-- | --: | --: |
| **grounded − language** | **+0.040 ± 0.044** | **+0.91** |
| grounded − surface | −0.097 ± 0.038 | −2.53 |
| grounded shift (absolute) | −0.034 ± 0.038 | — |

#### VERDICT: **FAIL** — and now we know *why* the prior runs disagreed.

shift −0.034 (≥0.05? no); grounding effect z=0.91 (≥2? no); capability drop
−0.021 (≤0.10? yes); safety drop +0.083 (≤0.10? yes).

This is the most honest data point in the series, and it reconciles Runs 5 and 6:

1. **The true `grounded − language` effect is small and positive (+0.040), but the
   real corpus-resampling band is huge (±0.044).** So z=0.91 — nowhere near 2σ.
   Three of four draws are positive (+0.038, +0.064, +0.078) and one is negative
   (−0.021); the effect sits *between* Run 5's +0.080 and Run 6's −0.008, exactly
   where a high-variance quantity sampled twice would land. **Run 5's z=7.26 was an
   artifact of the measurement-only band** (the real σ is ~0.044, not the ~0.011 a
   single corpus's seeds implied); Run 6's null was the unlucky draw. Neither
   single-corpus z meant what it claimed.
2. **Grounded CPT still drifts *away* from Egypt on average** (absolute shift
   −0.034), consistent with Run 6: at this scale neutral and grounded Arabic CPT
   both move the coordinate off-target; grounding does not produce a net pull.
3. **Prompting still beats CPT** (grounded − surface −0.097, z=−2.53) — the one
   robust finding across all seven runs.

Bottom line: with the variance estimated honestly, **there is a hint of a positive
grounding-beyond-language effect (+0.04, 3/4 draws positive) but it is not
significant against corpus-resampling noise.** The right read is "underpowered and
high-variance at this scale," not "confirmed" (Run 5) or "null" (Run 6). To move
the needle you need either many more draws (to pin down a +0.04 effect against
±0.044 you'd need ~dozens) or a larger per-draw effect (more tokens/epochs).

### Run 8 — scaled single corpus (2.7× tokens, 6 epochs): the effect grows but so does real training variance

After Run 7 the plan was: grow the per-draw effect (more tokens + epochs), then
re-resample. This is the "grow" half. Qwen3-4B, Arabic survey, generate-mode
behavior, 3 seeds, **6 epochs**, single corpus scaled via `CAT_LIMIT=150` to
**807k / 673k tokens** (grounded / language_matched) — ~2.7× Run 7's per-arm pool
and 1.5× its epochs. `TRANSLATE=0` (no Arm 3). The narrow Arabic categories
topped out well below the 1.5M-token cap, so epochs carried as much of the
scale-up as tokens. ~6 h on one RTX 5090. Result + per-seed checkpoints:
`runs/egypt_stats_scaled/`.

| arm | survey shift → Egypt | capability | refusal |
| :-- | --: | --: | --: |
| base | — | 0.79 | 1.00 |
| language_matched | **−0.129 ± 0.072** | **0.51** | **0.62** |
| **grounded** | −0.021 ± 0.025 | 0.79 | 0.88 |
| surface_only | +0.063 ± 0.010 | 0.79 | 1.00 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| **grounded − language** | **+0.108 ± 0.093** | **+1.15** |
| grounded − surface | −0.084 ± 0.026 | **−3.25** |

Per-seed grounded − language: **+0.199, +0.112, +0.012** (seeds 0/1/2).

#### VERDICT: **FAIL** — shift −0.021 (≥0.05? no); z=1.15 (≥2? no); capability drop 0.000 (ok); **safety drop +0.125 (≤0.10? no — first run to fail this conjunct)**.

Three substantive updates, the first two more important than the go/no-go:

1. **"HF training is deterministic across seeds" is FALSE at this scale.** The
   three seeds gave different *training outcomes*, not just different
   measurements: seed 0's neutral (language_matched) arm **catastrophically
   degenerated** — MMLU capability 0.79 → **0.08**, refusal 1.00 → **0.00**,
   coordinate collapsed to the (0,0) origin — while seed 1's neutral arm stayed
   healthy (cap 0.79) and seed 2's was mildly degraded (0.67). The seed perturbs
   CPT (almost certainly document/shuffle order) enough to tip one run into
   degeneration and not another. So the cross-seed band is **real training
   stochasticity**, not the "measurement-only" noise every prior run assumed —
   which retroactively confirms Run 5's z=7.26 was illusory and adds a *second*
   large variance source on top of corpus resampling. This invalidates the
   premise behind the prior runs' z-scores.
2. **The grounding effect is a robustness/forgetting asymmetry, not a value
   pull.** grounded reliably **preserves** the model (capability 0.79, refusal
   0.88, survey shift ≈ 0); value-neutral Arabic CPT **damages** it (capability
   0.51 avg, refusal 0.62, drifts −0.129, sometimes collapses entirely). The
   absolute grounded shift is still slightly **negative** (−0.021): grounded CPT
   produces **no net pull toward Egypt**. So grounded − language being positive
   (+0.108, biggest point estimate yet) means *value-laden text is gentler on the
   instruct model than value-neutral technical text* (law/religion/ethics vs
   math/sports/weather/biology), **not** that grounding teaches Egyptian values.
   This directly answers the away-drift question (see Interpretation): the drift
   is **catastrophic-forgetting-flavored** — capability and refusal crater along
   with the coordinate — and it is asymmetric by content.
3. **CPT erodes safety, grounded less than neutral** (refusal base 1.00 →
   grounded 0.88 → neutral 0.62), and **prompting still beats CPT**
   (grounded − surface z=−3.25 — the one robust finding across all eight runs).

Note: no non-finite-measurement caveat fired even though seed 0's neutral model
broke — its scores were a *finite* degenerate (0,0), so the capability guardrail
(0.08), not the nan scan, is what exposed it. (The harness was also hardened this
run: per-seed checkpointing + non-finite-robust aggregation, after an 8-epoch
attempt crashed in the final `statistics.stdev` and lost the training. See
`re_aggregate.py`.)

### Run 9 — stabilised training + replay/anchor arm

After Run 8 traced the cross-seed band to *training instability* (one seed's
neutral arm catastrophically degenerating), Run 9 **stabilised training** (linear
LR warmup→decay, gradient clipping, per-epoch deterministic shuffling, seed-varied
torch RNG) and added a **`grounded_replay`** arm (mixes 25% general English back in
to rehearse against forgetting). Qwen3-4B instruct, Arabic survey, 3 seeds, 800k
tokens, 6 epochs. Artifacts: `runs/egypt_stats_replay/`.

| arm | survey shift | capability | refusal |
| :-- | --: | --: | --: |
| base | +0.000 | 0.79 | 1.00 |
| language_matched | −0.031 ± 0.041 | 0.83 | 1.00 |
| **grounded** | **+0.057 ± 0.016** | **0.79** | 0.88 |
| surface_only (prompt) | +0.063 ± 0.010 | 0.79 | 1.00 |
| grounded_replay | +0.032 ± 0.017 | 0.83 | 0.88 |

| comparison | mean ± std | z |
| :-- | --: | --: |
| **grounded − language** | **+0.088 ± 0.030** | **+2.89** ✅ |
| grounded − surface | −0.006 | −1.13 (tie) |
| replay − grounded | −0.024 | −1.02 (ns) |

#### VERDICT: **FAIL — but for the first time only on the *safety* conjunct.**

Stabilisation killed the seed-degeneration (no arm cratered; grounded cap std
±0.016, not Run 8's 0.08-vs-0.79 chaos), and with forgetting thereby removed the
grounding effect **did not vanish** — grounded still beats language by +0.088 *and*
pulls toward Egypt in absolute terms (+0.057). That is evidence the effect is at
least partly **real value acquisition**, not only the forgetting-robustness
asymmetry Run 8 inferred. Prompting no longer beats CPT (grounded − surface a tie,
z=−1.13). The **replay arm did *not* behave as a forgetting story predicts**: it
*lowered* the shift (+0.032 vs +0.057) without buying back refusal (still 0.88) —
consistent with the pull being genuine rather than a forgetting artifact replay
could repair. The binding failure is the **refusal drop** (1.00→0.88 = 0.125 >
0.10). Two caveats remained: the z=2.89 band is still **cross-seed** (not the
cross-corpus band Run 7 flagged), and the safety regression needed explaining.

### Run 10 — two de-confounders in parallel (register twin + base model)

External review raised two confounds for Run 9's effect: (a) maybe it's *register*
(discursive prose vs terse technical text), not values; (b) maybe the safety drop
and the whole picture are instruct **alignment decay**, not the corpus. Run 10 ran
both controls in parallel on a 2× 5090 (`deploy/run_two_gpu.sh`): GPU 0 = instruct
+ a `neutral_prose` register twin (10a); GPU 1 = the same arms on **Qwen3-4B-Base**
(10b). Cross-seed band (single corpus). Artifacts: `runs/egypt_register_{instruct,base}/`.

**10a — register confound REJECTED.** A value-neutral but *discursive* twin was
predicted to be "nearly as grounded-like," collapsing the effect to genre. The
opposite happened: `neutral_prose` moved the coordinate **−0.035**, the same
slightly-negative way the terse `language_matched` twin did (−0.029), while
`grounded` moved **+0.057**. So `grounded − neutral_prose = +0.092` — even larger
than `grounded − language = +0.086 (z=2.12)`. Value content, not register, is the
driver. (Honest caveat: `grounded − neutral_prose` is z=1.77 — wide variance on the
new arm — so directionally decisive against the artifact, not itself >2σ.)

**10b — base model gives the first full PASS.** On Qwen3-4B-Base (no RLHF to erode)
the picture cleans up: `grounded − language = +0.032, z=3.02`, absolute shift
**+0.051 (≥0.05)**, capability **0.92→0.92**, refusal **0.88→0.88** — **all four
conjuncts pass, the first PASS in ten runs.** This confirms the instruct safety
FAIL was **alignment decay, not the corpus**. On base, CPT even edges out the
persona prompt (grounded − surface +0.021) — the first time the deep lever beats
the shallow one.

The two remaining caveats: both z's are **cross-seed**, not the cross-corpus band
Run 7 showed is the real noise source; and the absolute +0.051 was scored against
the **map-rescaled** target. Run 11 addresses both.

### Run 11 — the decisive cross-corpus test (real WVS-7 target)

Run 11 re-ran the Run-10 setup as a **corpus-resampled sweep** — `CORPUS_DRAWS=4
CORPUS_FRACTION=0.7` (4 independent 70%-token-mass draws), 3 inner seeds per draw —
on both substrates in parallel (GPU 0 instruct register twin = 11i; GPU 1
Qwen3-4B-Base = 11b), and scored the absolute shift against the **exact EVS/WVS-2023
factor-score target** (Egypt coord (−0.34, −0.89)). This is the one test that still
mattered: it moves the decision onto the cross-*corpus* band, the real noise source.
Artifacts: `runs/egypt_register_{base,instruct}/`.

**11b — Qwen3-4B-Base (the substrate that matters):**

| comparison (across 4 corpus draws) | mean ± std | z |
| :-- | --: | --: |
| **grounded − language** | **+0.051 ± 0.017** | **+2.97** ✅ |
| grounded − neutral_prose | +0.042 ± 0.022 | +1.90 |
| grounded − surface | +0.015 ± 0.023 | +0.65 (tie) |
| grounded shift (absolute) | +0.039 ± 0.023 | — |

Per-draw absolute grounded shift: **+0.028, +0.059, +0.058, +0.013** (two of four
clear 0.05). Capability drop **+0.010 (≤0.10 ✅)**; refusal drop **−0.031 (≤0.10 ✅,
no regression)**.

**11i — Qwen3-4B-Instruct register twin:**

| comparison (across 4 corpus draws) | mean ± std | z |
| :-- | --: | --: |
| grounded − language | +0.001 ± 0.019 | +0.03 ✗ |
| grounded − neutral_prose | +0.023 ± 0.010 | +2.28 |
| grounded − surface | +0.011 ± 0.006 | +1.79 |
| grounded shift (absolute) | +0.015 ± 0.006 | — |

#### VERDICT: **FAIL on base (absolute conjunct only); FAIL on instruct (effect vanishes).**

On **base**, the relative grounding effect **clears 2σ against the cross-corpus
band** (z=2.97) with capability and safety preserved — the first time the core H1(b)
claim survives the real noise source. Only the **absolute** shift (+0.039) falls
short of 0.05, so the formal go/no-go is FAIL on that conjunct alone. On
**instruct**, `grounded − language` **collapses to z=0.03** under corpus resampling:
Run 10a's z=2.12 was cross-seed sampling noise, not a real effect. (The register
rejection itself does survive on instruct — `grounded − neutral_prose` z=2.28.) The
base model is the right substrate; the instruct positives were noise.

### Run 12 — scaling the base model to close the absolute gap (the epoch tradeoff)

After Run 11 the only failing conjunct on base was the **absolute** shift (+0.039 <
0.05). On merging PR #65 the maintainer endorsed the one deferred GPU run: scale the
base-model corpus/epochs on the **same** cross-corpus band and push the absolute shift
over the bar. Run 12 ran `CORPUS_DRAWS=4 CORPUS_FRACTION=0.7` on **Qwen3-4B-Base** at
**10 epochs** (vs Run 11's 6), corpus regrown to **739,897 / 616,733 tokens**
(grounded / language_matched) via `cat_limit=150` — ≈430k tokens/draw, ~2× Run 11 (the
Arabic category membership is the hard ceiling, so the scale-up rode mostly on epochs).
3 inner seeds/draw, Arabic instrument, generate-mode behavior, stabilised. ~25 h on one
RTX 5090. Artifacts: `runs/egypt_stats/`.

| comparison (across 4 corpus draws) | per-draw | mean ± std | z |
| :-- | :-- | --: | --: |
| **grounded shift (absolute)** | 0.079 / 0.126 / 0.085 / 0.051 | **+0.085 ± 0.031** | all 4 ≥ 0.05 ✅ |
| **grounded − language** | 0.100 / 0.091 / 0.044 / 0.006 | **+0.060 ± 0.044** | **+1.39** ✗ |
| grounded − surface | 0.054 / 0.101 / 0.061 / 0.026 | +0.061 ± 0.031 | +1.96 |
| capability drop | −0.014 / 0.014 / 0.028 / 0.083 | +0.028 ± 0.041 | — |
| safety drop | −0.083 / −0.042 / 0.167 / −0.042 | +0.000 ± 0.113 | — |

#### VERDICT: **FAIL — and it swapped the failing conjunct vs Run 11.**

The scale-up did what it was aimed at: the **absolute shift cleared 0.05 in every
draw** (mean +0.085, vs Run 11's +0.039) — the conjunct Run 11 failed now passes. But
the **grounding effect fell to z=1.39 (< 2.0)**: draw 3 came in at grounded−language =
+0.006 (vs +0.100/+0.091/+0.044 for the others), widening the cross-draw band. So Run
12 PASSes absolute, capability and safety and FAILs only the **relative** grounding
conjunct — the mirror image of Run 11 (relative PASS, absolute FAIL). Across the two
runs each conjunct has cleared its bar, but **never both in one 4-draw run.**

**Why — a real epoch-scaling tradeoff, not just variance.** Decompose the neutral
arm's drift, `language_shift = grounded_shift − (grounded − language)`:
**−0.022 / +0.035 / +0.041 / +0.045**. At 10 epochs the *value-neutral* Arabic arm
itself drifts toward Egypt in 3 of 4 draws (~+0.04) — generic Arabic CPT pulls the
coordinate Egypt-ward on the IW map regardless of value content. That does two things:
(a) it is partly **why the absolute conjunct passed** — both arms drift Egypt-ward, so
the +0.085 grounded pull is not purely value-specific; and (b) it **narrows and
destabilises the grounded−language gap**, sinking the relative z. Pushing epochs to
clear the absolute bar therefore muddies the value-specificity the relative bar
measures: the two conjuncts are in **tension** under epoch-scaling. (Capability shows
the strain at the margin too — the highest-token draw 3 dropped 0.083, nearest the 0.10
bar yet, the first hint of mild overfit at 10 epochs.)

The upshot: the value-specific claim is best read off the **relative** effect at the
scale where the neutral arm does *not* co-drift — Run 11's 6 epochs (z=2.97). Run 12's
contribution is the **mechanism**: the absolute magnitude is reachable, but at the cost
of value-specificity, so a single-run four-conjunct PASS is elusive for a *principled*
reason, not for lack of draws. (`grounded − surface` +0.061 also confirms the scaled
base model edges out the persona prompt, consistent with Runs 10b/11b.)

## Trend across all twelve runs (the decisive comparison)

| run | model | survey | corpus | grounded − language | beaten by prompt? |
| :-- | :-- | :-- | --: | --: | :-- |
| 1–2 | Qwen2.5-1.5B | EN | ~50k | +0.019 (z=1.41) | yes, z=−8.57 |
| 3 | Qwen3-4B | EN | ~150k | +0.028 (z=0.75) | yes, z=−2.16 |
| 4 | Qwen3-4B | **AR** | ~150k | +0.140 (z=1.54) | tie, z=−0.50 |
| 5 | Qwen3-4B | AR | **271k** | **+0.080 (z=7.26)** ✅ | z=−2.09 |
| 6 | Qwen3-4B | AR | 300k (fresh) | **−0.008 (z=−0.29)** ✗ | z=−6.27 |
| 7 | Qwen3-4B | AR | **4× resampled** | **+0.040 (z=0.91)** | z=−2.53 |
| **8** | Qwen3-4B | AR | **807k/673k, 6ep** | **+0.108 (z=1.15)** | z=−3.25 |
| **9** | Qwen3-4B | AR | **800k, 6ep, +replay+stab** | **+0.088 (z=2.89)** ✅ | tie, z=−1.13 |
| **10a** | Qwen3-4B instruct | AR | **+register twin** | **+0.086 (z=2.12)** ✅ | tie, z=−0.33 |
| **10b** | Qwen3-4B **Base** | AR | **base de-confound** | **+0.032 (z=3.02)** ✅ | z=+0.98 (CPT wins) |
| **11i** | Qwen3-4B instruct | AR | **4× resampled (cross-corpus)** | **+0.001 (z=0.03)** ✗ | — |
| **11b** | Qwen3-4B **Base** | AR | **4× resampled (cross-corpus)** | **+0.051 (z=2.97)** ✅ | z=0.65 (tie) |
| **12** | Qwen3-4B **Base** | AR | **10ep, ~430k/draw, 4× cross-corpus** | **+0.060 (z=1.39)** ✗ | z=+1.96 (CPT wins) |

Runs 1–8 each computed z against a **cross-seed** band; since HF training is nearly
deterministic across seeds, that band understates the truth, so those z's are not
comparable to a real effect size (Run 5's z=7.26 and Run 6's z=−0.29 are just two
single corpus draws of a high-variance quantity disagreeing — Run 7's +0.040 ± 0.044
reconciles them). The decisive comparison is therefore only the runs measured against
the **cross-corpus** band: Run 7 (instruct, no stabilisation: z=0.91) and Run 11
(stabilised; base **z=2.97 ✅**, instruct z=0.03). The honest trend: on the **base**
model the grounding-beyond-language effect is real and clears 2σ against corpus noise;
on **instruct** it does not survive; and prompting, which dominated CPT through Run 8,
is matched or beaten once the model is stabilised (Run 9) and especially on base
(Runs 10b/11b/12). Run 12 (base, **10 epochs**) then scaled the corpus/epochs to lift
the *absolute* shift over 0.05 (it did: +0.085, all 4 draws) but the relative effect
fell to z=1.39 — at 10 epochs the value-neutral arm itself drifts Egypt-ward (~+0.04),
so absolute magnitude and value-specificity trade off against each other. The cleanest
value-specific read stays Run 11's z=2.97 at 6 epochs.

## Interpretation

The twelve runs tell one coherent story, and most of it is about **measuring the
effect honestly** rather than the effect itself.

**1. The early "pass" was a noise-band illusion.** Run 5 reported `grounded −
language = +0.080, z=7.26` and looked decisive. But that z was computed against the
spread across random *seeds*, and HF training is nearly deterministic across seeds —
so the band was measurement-only and far too narrow. Run 6, a fresh corpus draw of
the identical protocol, came back null (−0.008). Run 7 then measured the real noise
directly by **resampling the corpus** (4 independent 70% draws): the genuine effect
is `+0.040 ± 0.044 (z=0.91)` — small, positive on average, swamped by *which
documents land in the corpus*. Runs 5 and 6 were simply two draws from that
distribution. The lesson that governs every later run: **the cross-corpus band, not
the cross-seed band, is the real denominator.**

**2. At instruct scale the effect was mostly forgetting-robustness, not value
acquisition.** Run 8 scaled tokens/epochs and found the point estimate grew (+0.108)
but so did the variance, and it exposed *why*: the seed can tip an arm into
**catastrophic degeneration** (one neutral arm collapsed to capability 0.08, refusal
0.00). Grounded text was simply *gentler* on the instruct model than value-neutral
technical text — a forgetting asymmetry — while the absolute pull toward Egypt stayed
≈0. Run 9 **stabilised training** (warmup, grad-clip, shuffling) and added a
**replay** arm: stabilisation removed the degeneration, and crucially the grounding
effect *did not vanish* (grounded − language +0.088, and a positive absolute shift),
which is the first real sign the effect is partly genuine value acquisition rather
than only robustness. Replay *lowering* the shift without restoring refusal pointed
the same way.

**3. Stripping the confounds isolates a real, content-driven effect — on the right
substrate.** Run 10 ran two controls in parallel. The **register** confound is
rejected: a discursive-but-value-neutral twin (`neutral_prose`) behaves like the
terse language-matched twin, not like grounded — so it's the *values*, not the
genre. And the **base model** (no RLHF alignment to erode) gave the first clean
PASS, confirming that the instruct safety failure was **alignment decay, not the
corpus**. Run 11 then applied the one test that remained — the **cross-corpus band**
— to both substrates, against the corrected real WVS-7 target. On **base**, the
relative effect clears 2σ against corpus resampling (`+0.051, z=2.97`),
capability- and safety-clean. On **instruct**, it collapses (z=0.03): the instruct
positives were cross-seed noise all along.

**What this supports, and what it doesn't.** H1(b) — *grounded CPT shifts a base
model's survey-measured values toward the culture more than same-language,
value-neutral CPT does* — is **supported** at the decisive noise level, capability-
and safety-preserving. That is the one novel, defensible positive. Everything else is
a bound:

- **H1(a), strong absolute form, fails.** The absolute shift is +0.039, under the
  0.05 bar; scaling it over the bar (Run 12) collapses the value-specific effect, because
  the value-neutral arm also drifts target-ward at scale — so part of the absolute pull is
  language/topic, not values. Magnitude and value-specificity trade off.
- **H1(c), behavioral transfer, fails — a dissociation.** Once the behavioral judge was
  rebuilt to be sensitive at all (a persona prompt moves behavior +0.18), grounded CPT was
  shown to move the survey but **not** open-ended behavior (−0.086 ± 0.098 ≈ 0). The shift
  is survey-level, not enacted.
- **Aggregation (T3) is a non-failure, not a win.** Cultures stay separable under FedAvg
  (dilutive, not destructive merge), but nothing shows the *merged* model is good or that
  aggregation adds value over solo training.

So the honest synthesis is **real but shallow**: value-laden CPT produces a genuine,
resampling-robust, aggregation-robust shift in a base model's *stated* values — but it does
not reach behavior, does not yield a large absolute pull, and at scale is hard to fully
separate from language drift. The shallow-baseline note still holds: a one-line persona
prompt was hard to beat throughout (it dominated CPT through Run 8, and it is the *only*
thing that moved behavior in the H1c run), which is itself a signal that explicit conditioning
is a strong, cheap alternative to the deep lever.

## Status & next steps

**The narrow claim the data supports (and nothing wider):**

> Value-grounded Arabic CPT shifts a base model's **survey-measured** values toward
> Egyptian values **more than a same-language, value-neutral corpus does** —
> `grounded − language = +0.051, z≈3.0` across independent corpus resamples — **with
> capability and refusal preserved**, and this survey signal **survives FedAvg
> aggregation across cultures.** It does **not** extend further: the absolute pull is
> small (+0.039, and scaling it costs value-specificity); it does **not reach
> open-ended behavior** (a survey-behavior dissociation); and it requires the base
> model (the instruct effect is cross-seed noise). The effect is **real but shallow.**

The Run-11 relative result was merged as **PR #65** (2026-06-19) and the maintainer
endorsed continuing. The three follow-ups proposed there have now all run — and, stated
plainly, **none was a win:** each tested whether the Run-11 effect *extends* (to a clean
absolute PASS, through aggregation, into behavior) and each returned "no, or only weakly."
They are recorded below as the bound, not as progress.

**Phase 1 — close the absolute-magnitude gap (Run 12, DONE 2026-06-23).** Scaled the
base model to 10 epochs / ~430k tokens-per-draw on the same `CORPUS_DRAWS=4
CORPUS_FRACTION=0.7` band. Outcome (see Run 12 above): the **absolute shift cleared
0.05 in all four draws** (+0.085) — the conjunct Run 11 failed now passes — but the
**relative grounding effect fell to z=1.39** because at 10 epochs the value-neutral arm
itself drifts Egypt-ward, narrowing the gap. So Run 12 is the *mirror image* of Run 11:
each conjunct can clear its bar, but not both in one run, because absolute magnitude and
value-specificity **trade off under epoch-scaling**. **Decision (2026-06-23): the
single-run four-conjunct PASS is elusive for a principled reason, not lack of draws — so
keep Run 11's relative-effect result (z=2.97, 6 epochs) as the headline, fold in Run
12's tradeoff finding, and stop spending GPU on the closeout.** Move to Phase 2.

**Phase 2 — consortium / aggregation-survival (T3) — FIRST REAL RUN DONE (2026-06-24).**
The Tapestry-unique question and the round-two headline: does cultural alignment survive
FedAvg across cultures, or collapse toward the centroid? Real HF run on **Qwen3-4B-Base**,
**3 cultures measured in-language** (Egypt/ar, Sweden/sv, Vietnam/vi), 4 FedAvg rounds ×
6 epochs, 145k grounded tokens/culture (matched budget), seed 0. Each round every node
forks the shared global base, does grounded CPT, is surveyed on the IW map **in its own
corpus language** (a shared English instrument muted the foreign-language CPT in v1 — the
fix that made this run meaningful), then all forks are FedAvg-averaged into the next base.

| round | shift-sep | abs-sep | to-centroid | merge cos | sign-agree | retained | dist→target eg/sw/vi |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :-- |
| 1 | 0.076 | 0.255 | 0.131 | +0.057 | 0.101 | 0.613 | 0.890 / 1.144 / 0.297 |
| 2 | 0.109 | 0.298 | 0.161 | +0.006 | 0.098 | 0.584 | 0.880 / 1.134 / 0.259 |
| 3 | 0.097 | 0.338 | 0.188 | −0.021 | 0.096 | 0.569 | 0.868 / 1.140 / 0.229 |
| 4 | 0.066 | 0.332 | 0.179 | −0.033 | 0.096 | 0.561 | 0.861 / 1.140 / 0.239 |

**Read: sovereign alignment largely SURVIVES aggregation; the loss is merge interference,
not homogenization.** Absolute separability *grows* (0.26 → 0.33) and each culture holds or
improves its distance to its own WVS target (Vietnam 0.30 → 0.24, Egypt 0.89 → 0.86) — the
nodes spread *apart* in coordinate space, not toward a centroid. The shift-space curve dips
late (0.076 → 0.066), which a naive first-vs-last label would call "homogenizing", but the
**weight-space merge diagnostics** say otherwise: fork-update cosine falls from +0.057 to
**−0.033** (anti-aligned), sign-agreement sits at ~0.10 (forks disagree on ~90% of parameter
signs), and the retained-update ratio declines 0.61 → 0.56. That is the representational
merge-**interference** signature (cf. arXiv:2605.25846, [LITERATURE.md](LITERATURE.md) §6) —
FedAvg cancels a growing share of each fork's update in weight space — *not* cultures
genuinely converging. The CLI trend label was made diagnostic-aware so it no longer prints
the misleading "homogenizing" headline.

**Corpus-resampled confirmation (4 draws × 0.7, seeds 0–3).** The single run above is N=1;
re-running the whole FedAvg loop on 4 deterministic 70%-token subsamples of each culture's
grounded pool — the same `CORPUS_DRAWS=4 CORPUS_FRACTION=0.7` band that decided Run 11 — gives
the per-round mean ± std curves below. **The conclusion holds with tight error bars.**

| round | shift-sep | abs-sep | merge-cos | retained | to-centroid |
| :--: | :--: | :--: | :--: | :--: | :--: |
| 1 | 0.064 ± 0.007 | 0.235 ± 0.017 | +0.055 ± 0.003 | 0.612 ± 0.002 | 0.122 ± 0.008 |
| 2 | 0.103 ± 0.024 | 0.292 ± 0.011 | +0.007 ± 0.002 | 0.586 ± 0.001 | 0.159 ± 0.009 |
| 3 | 0.104 ± 0.023 | 0.299 ± 0.020 | −0.017 ± 0.001 | 0.571 ± 0.001 | 0.170 ± 0.011 |
| 4 | 0.083 ± 0.013 | 0.305 ± 0.045 | −0.027 ± 0.001 | 0.565 ± 0.001 | 0.174 ± 0.025 |

Two robust signals: (1) **absolute separability grows monotonically** (0.235 → 0.305), each
round's increase clearing the cross-draw band — the nodes reliably spread *apart*, not toward a
centroid. (2) **The weight-space merge diagnostics are essentially invariant across draws**
(cosine +0.055 → −0.027, retained 0.612 → 0.565, both with std ≈ 0.001–0.003): the merge
interference is a *structural* property of FedAvg-ing these forks, not an artifact of which 70%
of the corpus each node saw. The coordinate-space metrics (shift-/abs-sep) carry the corpus
sensitivity; the merge geometry does not. So the headline — **sovereign cultural alignment
survives aggregation; the cost is a lossy merge (mostly dilution, not destruction — see below)**
— is now established across the corpus band, not a single-sample result. (Shift-sep is
non-monotonic — rises then dips, ending above round 1 — so even the naive trend reads "surviving"
on the banded mean.)

**Reading the merge geometry: dilution by near-orthogonality, not cancellation of conflict.**
`retained` (‖mean update‖ / mean‖update‖) sits at **0.61 → 0.57**, and for N=3 forks
**1/√N ≈ 0.577** is exactly the value you get from averaging *mutually orthogonal* vectors.
Destructive cancellation of genuinely conflicting (anti-parallel) updates would instead drive
`retained` toward 0 and cosine toward −1. We see neither: the cultures are largely writing to
**different parameter directions**, so FedAvg mostly *dilutes* each culture's update by ~1/N in
the blend rather than annihilating it. On top of that near-orthogonal floor there is a small,
**monotone** drift: cosine **+0.055 → −0.027** and `retained` crossing from just above 1/√N
(rounds 1–2, faintly *aligned*) to just below it (rounds 3–4, faintly *conflicting*) — i.e. as
the cultures get more grounded and distinct their updates rotate from "pulling together" through
orthogonal to "pulling apart." This is the *most favorable* merge regime for the consortium
thesis (cultures use separate capacity rather than fighting over shared weights), with the
caveat that the genuine-conflict component, while small, is **growing** over rounds.

**What this does NOT indicate.** Every metric here is measured on the **forks after their
per-culture CPT** — never on the **merged global model itself**. So the result does *not* show:
(1) that the merged base is *good* — its capability/safety/quality over rounds is **unmeasured**,
so we cannot say the dilute-then-re-align cycle preserves a useful shared model versus slowly
eroding it; (2) that aggregation *buys anything* — growing `abs-sep` is equally consistent with
healthy sovereignty *and* with each culture having to fight an increasingly washed-out base;
there is **no solo-training control** to tell "aggregation helped" from "aggregation was merely
survived"; (3) that it **stays benign at scale** — the conflict component is small but rising
over just 4 rounds with 3 cultures, and more rounds / more cultures / a different base checkpoint
are untested. The firm claim is narrow and worth stating exactly: *culturally-grounded nodes stay
distinct across FedAvg rounds, and the averaging is dilutive rather than destructive* — not that
the aggregated model is itself improving.

**Remaining caveats.** Model seed is fixed (HF training is deterministic across it, so the
corpus draw is the right variance source — but a different *base* checkpoint is untested).
Sweden stays far from its target (~1.14): its self-expression SS pole clamps, so it is likely
under-measured and shows grounding mostly as TS movement. Modest scale (145k tok/culture, 6
epochs), 3 cultures. Next: more cultures for a wider spread, and the behavioral-transfer (H1c)
probe. Artifacts in `runs/cultural_cpt_aggregation/` (single run) and
`runs/cultural_cpt_aggregation_resampled/` (`result_resampled.json` + per-draw/-round
checkpoints; git-ignored). See [SPEC.md](SPEC.md) consortium extension and `HANDOFF.md`.

**Phase 2 — behavioral transfer (H1c) — DONE (2026-06-24): a survey-behavior dissociation.**
The free-form behavioral probe had never moved in any run — but that turned out to be a
**measurement artifact**. The generate-mode judge scored a response by softmax over
cosine-similarity to a scenario's three crowded action options, which saturates: even a
*perfectly* pole-aligned response moved the coordinate at most ±0.25 (verbatim-option ceiling
±0.5) out of 2.0, so a CPT-sized shift (~0.05) rendered as ~0.01, below noise. Replacing it
with a **SemAxis cosine-difference** judge — `cos(resp, +pole) − cos(resp, −pole)` over
pole-anchor centroids (each scenario's option plus axis-level exemplar sentences, en+ar),
calibrated so poles map to ±1 — recovers ~4× the dynamic range (mean pole-aligned spread +1.04
vs +0.25, deterministic). Re-run on Qwen3-4B-Base, Egypt, Arabic, 3 seeds, with the fixed probe:

| arm | survey shift→target | behavior shift→target |
| :-- | :--: | :--: |
| base | 0.000 | 0.000 |
| language_matched | −0.025 ± 0.027 | −0.141 ± 0.231 |
| grounded | **+0.021 ± 0.023** | **−0.086 ± 0.098** |
| surface_only (persona prompt) | +0.024 ± 0.014 | **+0.181 ± 0.098** |

Two results. **(1) The probe now works:** behavior *moves* (±0.09–0.23 vs pinned-at-0 before),
and an explicit persona prompt shifts it **+0.181 (~1.8σ)** toward Egypt — the judge was the
blindfold. **(2) A clean survey-behavior dissociation:** grounded CPT moves the *survey* toward
Egypt (+0.021) but **not** open-ended *behavior* (−0.086 ± 0.098, consistent with zero), even
though prompting moves behavior. So the grounding effect is **survey-level and does not propagate
to enacted behavior** — exactly the surface-mimicry-vs-deep-shift distinction H1c was built to
test, and now a *real* null rather than an instrument failure. This **bounds H1b**: the value
shift CPT produces is real on the instrument but shallow. Caveats: n=3 seeds, no corpus draws,
6 scenarios × 2 passes; the behavior std is temperature-1.0 generation noise, so the null is
"no *detectable* transfer," and tightening it means more scenarios/passes, not corpus draws.
Artifacts in `runs/egypt_stats_behavior/` (git-ignored). **Phase 2 triad complete:** value shift
(real, z≈3 cross-corpus), aggregation survival (holds; dilutive merge), behavioral transfer
(dissociated/negative).

**Decision (2026-06-24): consolidate the bounded result; stop chasing a win this rig isn't
offering.** All three follow-ups have run and the marginal experiment now has low expected
value. What a *real* win would actually require is not another run on this setup but a
different cut, and it is worth naming honestly:

- **Establish depth, not just survey movement.** The crux the whole record turns on is whether
  the survey shift is genuine value-representation or sophisticated survey/format/language
  learning. The cleanest test of that *is* the behavioral probe — and it already said shallow.
  A win here means demonstrating the shift changes something downstream of the survey (behavior,
  or a held-out value-laden generation task), which this scale did not.
- **Separate value from language at scale.** Run 12 showed the value-neutral arm drifts
  target-ward with more epochs; a win means a corpus/probe design where absolute magnitude grows
  *without* the neutral arm following — otherwise the absolute claim stays confounded.
- **Show aggregation buys something.** A solo-training control + a capability/quality trace on
  the *merged* model, so "cultures survive FedAvg" becomes "federated grounding beats grounding
  alone," which is the actually-interesting consortium claim.

Cheap loose ends if the work resumes anyway: firm up `grounded − neutral_prose` on base
(z=1.90), and tighten the H1c null with more scenarios/passes (the behavioral noise is
generation-sampling, not corpus).

**Resolved along the way:** the noise-band question (cross-corpus, Run 7); training
instability (stabilisation, Run 9); the register confound (rejected, Run 10a); the
alignment-decay confound (base model, Run 10b); the map-rescaled target (real WVS-7
factor scores, Run 11); the decisive cross-corpus test (Run 11); aggregation survival
(T3); and the behavioral-probe instrument failure (the SemAxis judge fix) plus the H1c
dissociation it revealed.

## Limitations

- **Single culture, single corpus source.** Egypt only, Arabic Wikipedia only;
  generality across cultures and sources is untested.
- **Absolute magnitude is small and scale-limited.** +0.039 at this token budget;
  the strong-form H1(a) claim is not established.
- **Base model only.** The clean result requires Qwen3-4B-Base; on the aligned
  instruct model the effect does not survive corpus resampling.
- **Grounding does not transfer to behavior (survey-behavior dissociation).** With a
  validated probe (a persona prompt moves behavior +0.18), grounded CPT moves the survey
  (+0.021) but not open-ended behavior (−0.086 ± 0.098) — the value shift is survey-level,
  not enacted. The strong-form representational claim is not established.

