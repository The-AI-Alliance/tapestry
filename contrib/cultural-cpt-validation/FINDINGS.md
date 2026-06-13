# EXP-001 findings log

Real runs of the cultural-CPT validation harness. "Real" = a real base model
(`--mode hf`) **and** a real corpus (`--corpus-path`), so no `NOT A RESULT`
caveat. Numbers from the toy/smoke model are not recorded here.

Run artifacts (`runs/…/result.json`) are git-ignored; the numbers below are the
record. Corpora regenerate from `titles/egypt.ar.json` via `fetch_corpus.py`.

## Setup common to both runs

- **Base model:** `Qwen/Qwen2.5-1.5B-Instruct`, full-parameter CPT, bf16.
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

## Interpretation

Taken at face value: at this scale full grounded CPT produces **no significant
cultural shift** and is **beaten by a one-line persona prompt** (z=−8.57) — which
would *undercut* the depth-over-shallow architectural bet. But this is **not a
verdict on H1**, because the run is badly underpowered:

1. **Tiny corpus / few epochs.** ~50k tokens over 6 epochs on a 1.5B model barely
   perturbs the weights. Real CPT uses orders of magnitude more tokens. This is
   the recurring Stage-0 bottleneck, not a property of the hypothesis.
2. **The one encouraging thread:** grounded beats language-matched by **+0.019 in
   the direction H1 predicts** — just inside the noise. Scale/tokens could push it
   past 2σ.
3. **Noise band is measurement-only** (paraphrase/temperature/option-order),
   because HF training is deterministic across seeds. So z=1.41 is, if anything,
   optimistic; real training-seed variance would widen the band.
4. **Language carrier not isolated:** corpus is Arabic, survey is English; the
   `grounded_translated` arm (which would separate content from language) was not
   in the corpus. Administering the survey in Arabic is the cleaner fix.
5. Capability "0.75" is the toy MMLU stub, not real MMLU — the capability
   guardrail is not yet meaningful.

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
