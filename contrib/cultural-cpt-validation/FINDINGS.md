# EXP-001 findings log

Real runs of the cultural-CPT validation harness. "Real" = a real base model
(`--mode hf`) **and** a real corpus (`--corpus-path`), so no `NOT A RESULT`
caveat. Numbers from the toy/smoke model are not recorded here.

Run artifacts (`runs/…/result.json`) are git-ignored; the numbers below are the
record. Corpora regenerate from `titles/egypt.ar.json` via `fetch_corpus.py`.

## Setup common to all runs

- **Base model:** Runs 1–2 `Qwen/Qwen2.5-1.5B-Instruct`; Run 3
  `Qwen/Qwen3-4B-Instruct-2507`. Full-parameter CPT, bf16 (Run 3: + 8-bit Adam).
- **Culture:** Egypt. WVS-7 Inglehart-Welzel map target (rescaled to item
  scale): **(ts −0.72, ss −0.52)** — far Traditional / Survival.
- **Instrument:** canonical 10-item IW battery (`wvs.py`), ≥3 paraphrases/item,
  expected-value scoring. Survey administered in **English**.
- **Corpus:** Arabic Wikipedia, same-source/different-domain twin (grounded =
  law/religion/family/civic/ethics; language-matched = weather/sports/technical/
  math/biology), full articles chunked to 1024-token windows for CPT.
- **lr** 2e-5. **Hardware:** RTX 5090 (Vast.ai self-rental).
- Metric: per-arm **shift toward Egypt vs. Base** (positive = moved toward the
  national coordinate). Decisive = grounded shift minus another arm's.

## Run 1 — single seed (pilot)

`run.py`, epochs 2, per-domain 6, corpus ≈32k / 30k tokens (grounded / matched).

| arm | survey shift | behavior shift | capability |
| :-- | --: | --: | --: |
| base | — | — | 0.75 |
| language_matched | −0.038 | −0.010 | 0.75 |
| grounded | −0.029 | −0.018 | 0.75 |
| surface_only (prompt) | +0.141 | +0.040 | 0.75 |

grounded − language **+0.009**; grounded − surface **−0.170**. Null at this
micro-scale.

## Run 2 — multi-seed go/no-go (pre-registered)

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

### VERDICT: **FAIL**

shift −0.029 (≥0.05? no); grounding effect z=1.41 (≥2? no); capability drop
0.000 (≤0.10? yes).

## Run 3 — Qwen3-4B, scaled corpus, multi-seed

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

### VERDICT: **FAIL** — shift +0.023 (≥0.05? no); z=0.75 (≥2? no); capability fine.

## Run 4 — Qwen3-4B, **survey administered in Arabic**

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

### VERDICT: **FAIL** — shift +0.035 (≥0.05? no); z=1.54 (≥2? no). But the closest yet.

### Language of measurement matters a lot (Run 3 EN vs Run 4 AR, all else equal)

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

## Run 5 — everything stacked (4B + Arabic survey + free-form behavior + 2× corpus)

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

### VERDICT: **FAIL** — but the decisive comparison finally passes.

The pre-registered rule has three conjuncts; for the first time the **grounding
effect clears 2σ** (z=7.26, positive) and capability is fine. It still FAILs only
on the **absolute** grounded shift: +0.003 < 0.05.

### What actually happened — grounding *prevents drift* more than it *pulls*

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

## Run 6 — first `grounded_translated` arm + real guardrails (and a non-replication)

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

### VERDICT: **FAIL** — and Run 5's decisive effect did **not** replicate.

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

## Run 7 — corpus-RESAMPLED go/no-go (the real noise band)

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

### VERDICT: **FAIL** — and now we know *why* the prior runs disagreed.

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

## Run 8 — scaled single corpus (2.7× tokens, 6 epochs): the effect grows but so does real training variance

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

### VERDICT: **FAIL** — shift −0.021 (≥0.05? no); z=1.15 (≥2? no); capability drop 0.000 (ok); **safety drop +0.125 (≤0.10? no — first run to fail this conjunct)**.

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

## Trend across all eight runs (the decisive comparison)

| run | model | survey | corpus | grounded − language | beaten by prompt? |
| :-- | :-- | :-- | --: | --: | :-- |
| 1–2 | Qwen2.5-1.5B | EN | ~50k | +0.019 (z=1.41) | yes, z=−8.57 |
| 3 | Qwen3-4B | EN | ~150k | +0.028 (z=0.75) | yes, z=−2.16 |
| 4 | Qwen3-4B | **AR** | ~150k | +0.140 (z=1.54) | tie, z=−0.50 |
| 5 | Qwen3-4B | AR | **271k** | **+0.080 (z=7.26)** ✅ | z=−2.09 |
| 6 | Qwen3-4B | AR | 300k (fresh) | **−0.008 (z=−0.29)** ✗ | z=−6.27 |
| 7 | Qwen3-4B | AR | **4× resampled** | **+0.040 (z=0.91)** | z=−2.53 |
| **8** | Qwen3-4B | AR | **807k/673k, 6ep** | **+0.108 (z=1.15)** | z=−3.25 |

Runs 1–6 each computed z against a measurement-only band, so their z's are not
comparable to a real effect size. **Run 7 supersedes the single-corpus z's:** the
genuine effect is +0.040 with a cross-corpus σ of 0.044 (z=0.91). Runs 5 and 6 are
now explained — they are two draws (+0.080, −0.008) from a distribution centered
near +0.04 with σ≈0.044, so neither the "decisive pass" nor the "null" was real.
The honest trend is: a small, positive-on-average, **not-significant** grounding
effect that is swamped by which documents land in the corpus, and prompting beats
CPT every time.

## Interpretation

**Updated after Run 8 (read this first).** Scaling tokens+epochs pushed the
`grounded − language` point estimate to its highest (+0.108) but **not past 2σ**
(z=1.15): the variance grew as fast as the effect. And the variance is now
understood — Run 8 **falsified the "training is deterministic across seeds"
premise**: the seed changes the *training outcome* (one seed's neutral arm
catastrophically degenerated, others didn't), so the cross-seed band is real
training stochasticity, not measurement noise. Most importantly, the mechanism is
now clear and it is **not** the hypothesised one: grounded CPT does not pull toward
Egypt (absolute shift −0.021); rather, **value-neutral CPT damages the model
(capability 0.79→0.51, refusal 1.00→0.62, coordinate drift) and grounded CPT does
so far less.** The "grounding beyond language" effect is a **forgetting-robustness
asymmetry** — value-laden text is gentler on the instruct model than neutral
technical text — not value acquisition. This resolves the away-drift puzzle below:
the drift is **catastrophic-forgetting-flavored** (capability/refusal crater with
the coordinate), so the right next move is a **replay/anchor mitigation arm** to
suppress forgetting and see whether any genuine value-pull survives underneath.
The Run-7 reading (below) still holds for the resampled band; Run 8 adds the
training-stochasticity source and the forgetting mechanism.

**Updated after Run 7.** With the noise band estimated honestly
— 4 corpus resamples instead of one — the decisive `grounded − language` effect is
**+0.040 ± 0.044 (z=0.91): small, positive on average, not significant.** This
*reconciles* the earlier contradiction: Run 5's "decisive pass" (z=7.26) and Run
6's "null" (z=−0.29) were both single draws of a quantity whose real σ is ~0.044,
so neither z meant what it claimed — both were computed against a measurement-only
band (HF training is deterministic across seeds). The honest position now: **there
is a hint of a grounding-beyond-language effect, but it is underpowered and swamped
by corpus-sampling variance at this scale; it is neither confirmed nor null.** The
absolute grounded shift is slightly negative (−0.034) — grounded CPT does not net
pull toward Egypt — and a one-line persona prompt beats CPT in every run. The
Run-5/Run-6 readings are kept below for the record.

By Run 5 the **decisive comparison passes**: grounded CPT shifts toward Egypt
significantly more than value-neutral CPT in the same language (+0.080, z=7.26) —
H1(b), the "grounding ≠ just language" claim, is supported, with capability
preserved. The pre-registered **overall verdict is still FAIL** on the *absolute*
grounded shift (+0.003 < 0.05): grounded CPT mainly **prevents the away-drift**
that neutral CPT causes rather than actively pulling toward Egypt at this scale.
And the upgraded free-form behavioral probe shows **no arm shifts open-ended
behavior** — so a representational/behavioral shift (H1(c)) is not yet
demonstrated. Net: the *novel* claim (grounded beats language-matched) now has
real evidence; the *strong* claims (large absolute shift; behavioral change)
remain unmet and are the next targets. Caveats that still hold:

1. **Still token-starved.** Even Run 3's ~150k tokens over 4 epochs is tiny for
   CPT (real CPT = millions+ of tokens). The grounded shift is positive but small;
   more tokens is the obvious next lever. This is the recurring Stage-0 bottleneck,
   not a property of the hypothesis.
2. **Direction is consistent and improving with scale** (the trend table): the
   grounding-beyond-language effect is positive in both runs and grew with scale.
   That is exactly what H1 predicts; it just has not cleared 2σ yet.
3. **Noise band is measurement-only** (paraphrase/temperature/option-order),
   because HF training is deterministic across seeds. So the z-scores are, if
   anything, optimistic; real training-seed variance would widen the band.
4. **Behavioral probe regressed:** in Run 3 both CPT arms' *behavior* coordinate
   moved away from Egypt (−0.16/−0.19) while only the prompt moved it toward.
   Either CPT degrades the behavioral probe, or (more likely) the probe is too
   crude — upgrading it to free-form generation + a rubric judge is overdue.
5. **Language carrier not isolated:** corpus is Arabic, survey is English; the
   `grounded_translated` arm (content vs. language) was not in the corpus.
   Administering the survey in Arabic is the cleaner fix.
6. Capability is the toy 4-item MMLU stub (CPT arms even "improved" to 0.92–1.00,
   which is noise) — the capability guardrail is not yet meaningful.

**Solid takeaways that do hold:** the full pipeline produces a genuine,
reproducible EXP-001 data point end to end; capability is preserved under CPT at
this scale; and cheap prompting moves the English-measured coordinate far more
than micro-scale CPT does.

## Next experiment (highest impact first)

Run 8 reframes the priorities again: growing tokens+epochs raised the effect
(+0.108) but not its significance (z=1.15), and revealed the effect is really a
**forgetting-robustness asymmetry**, with a *second* large variance source
(training stochasticity across seeds). So "grow then re-resample" is no longer the
top move — the mechanism is the story:

1. **Replay / anchor mitigation arm (now the headline experiment).** *(BUILT — ready
   for Run 9.)* The away-drift is catastrophic-forgetting-flavored (capability and
   refusal crater with the coordinate). The harness now has a `grounded_replay` arm
   (`--replay-fraction F`, env `REPLAY_FRACTION`): it mixes a fraction `F` of general,
   value-neutral English text — the base model's pretraining distribution — into the
   grounded CPT to rehearse against forgetting. It reports two new comparisons:
   `replay_vs_grounded` (the replay effect itself) and `replay_vs_language` (the
   grounding-beyond-language effect once forgetting is suppressed). If the drift is
   forgetting, replay should lift grounded_replay's capability/refusal back toward
   base — *and only then* can we read whether any genuine value-pull toward Egypt
   survives underneath. This is the clean test separating H-forget from H-value.
   (KL-anchoring to the base was considered but deferred: a frozen 4B reference plus
   the trainable model does not fit one 32GB GPU; replay is the cheaper, fitting lever.)
2. **Stabilise training before chasing significance.** *(BUILT.)* Because the seed
   tips runs into degeneration unpredictably (cap 0.08 vs 0.79 across seeds), the
   cross-seed band is dominated by *whether the model broke*, not by the effect. The
   HF training loop now has **linear LR warmup→decay** (`--warmup-frac`, env
   `WARMUP_FRAC`), **gradient clipping** (`--max-grad-norm`, env `MAX_GRAD_NORM`), and
   **per-epoch deterministic shuffling** (also what interleaves the replay mix). These
   apply to every CPT arm; with stable training the grounded − language estimate
   should have a far smaller, honest band.
3. **Then re-resample the corpus** (`--corpus-draws N --corpus-fraction F`) on the
   stabilised, replay-protected setup — at that point a >2σ result is meaningful.
4. **Reframe the question.** If grounded − language is forgetting-robustness rather
   than value acquisition, that is itself a publishable, useful finding (which
   cultural content to CPT on to *preserve* a model) — but it is not EXP-001's H1.
   Decide whether to chase value-pull (needs replay + likely far more scale) or to
   pivot the claim to "value-laden corpora are gentler under CPT."

Run 9 — replay/anchor mitigation + stabilised training (the headline experiment):

```shell
# on a CUDA-12.8+/PyTorch-2.7+ GPU box (see deploy/README.md). REPLAY_FRACTION>0
# adds the grounded_replay arm and builds the replay corpus; WARMUP_FRAC and
# MAX_GRAD_NORM stabilise every arm. Start single-draw to read the arm, then add
# CORPUS_DRAWS=4 CORPUS_FRACTION=0.7 to re-resample on the stabilised setup.
REPO=/workspace/tapestry MODEL=Qwen/Qwen3-4B-Instruct-2507 \
  SEEDS=0,1,2 EPOCHS=6 PER_DOMAIN=18 MAX_WORDS=4000 CAT_LIMIT=25 MAX_TOKENS=800000 \
  DTYPE=bfloat16 INSTRUMENT_LANG=ar BEHAVIOR_MODE=generate TRANSLATE=0 \
  REPLAY_FRACTION=0.25 WARMUP_FRAC=0.05 MAX_GRAD_NORM=1.0 \
  bash contrib/cultural-cpt-validation/deploy/run_on_instance.sh
```

Read it as: does `grounded_replay` recover capability/refusal toward base (forgetting
suppressed), and is its absolute shift toward Egypt > 0 (value-pull surviving)? A
positive `replay_vs_grounded` with restored capability is the H-forget signature; a
positive *absolute* grounded_replay shift is the first real sign of value acquisition.
