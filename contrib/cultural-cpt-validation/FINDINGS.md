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

## Trend across all six runs (the decisive comparison)

| run | model | survey | corpus | grounded − language | beaten by prompt? |
| :-- | :-- | :-- | --: | --: | :-- |
| 1–2 | Qwen2.5-1.5B | EN | ~50k | +0.019 (z=1.41) | yes, z=−8.57 |
| 3 | Qwen3-4B | EN | ~150k | +0.028 (z=0.75) | yes, z=−2.16 |
| 4 | Qwen3-4B | **AR** | ~150k | +0.140 (z=1.54) | tie, z=−0.50 |
| 5 | Qwen3-4B | AR | **271k** | **+0.080 (z=7.26)** ✅ | z=−2.09 |
| 6 | Qwen3-4B | AR | 300k (fresh) | **−0.008 (z=−0.29)** ✗ | z=−6.27 |

Runs 3→5 looked like a clean monotone story — a bigger model+corpus flipped the
grounded shift toward Egypt (Run 3), measuring **in Arabic** multiplied it ~5×
(Run 4), and more tokens collapsed the variance enough to clear 2σ (Run 5). **Run
6 breaks that story:** same protocol, a *freshly fetched* corpus, and the decisive
effect collapses to null (z=−0.29). The Run-5 z=7.26 was driven by an unusually
tight measurement-only noise band on one particular corpus sample; it does not
survive resampling the corpus. The honest trend is **not** "every lever helps" —
it is "the effect is small and corpus-sample-dependent, and cheap prompting beats
it every time."

## Interpretation

**Updated after Run 6 (read this first).** The Run-5-era conclusion below — "the
decisive comparison passes" — **did not replicate**. On a freshly-sampled corpus
with the upgraded harness (real MMLU/safety guardrails + the translated arm), the
grounded−language effect is null (z=−0.29), grounded drifts away from Egypt as
much as the neutral twin, and the new Arm 3 shows the content's *language* is
irrelevant (grounded ≈ grounded_translated). The current honest position: **there
is no robust evidence that culturally-grounded micro-CPT moves Inglehart-Welzel
coordinates more than value-neutral CPT** at this scale; the one positive run
(Run 5) appears to have been corpus-sample-specific, inflated by a
measurement-only noise band. What *does* replicate across all six runs: capability
(now real) is preserved, and a one-line persona prompt beats CPT every time. The
Run-5 reading is kept below for the record.

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

1. **More corpus tokens** (10×+) — the binding constraint, again.
2. **Bigger base** (3B+ via 8-bit Adam on one 5090, or full FT across both 5090s).
3. **Survey in Arabic** (and/or add the `grounded_translated` arm) to isolate the
   language carrier.
4. **More epochs.**

Reproduce a run:

```shell
# on a CUDA-12.8+/PyTorch-2.7+ GPU box (see deploy/README.md):
REPO=/workspace/tapestry SEEDS=0,1,2 EPOCHS=6 PER_DOMAIN=8 DTYPE=bfloat16 \
  bash contrib/cultural-cpt-validation/deploy/run_on_instance.sh
```
