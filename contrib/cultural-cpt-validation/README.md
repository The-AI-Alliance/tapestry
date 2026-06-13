# Cultural-CPT validation harness (EXP-001)

A runnable harness for the experiment specified in
[`tech-docs/experiments/cultural-cpt-validation.md`](../../tech-docs/experiments/cultural-cpt-validation.md):
does continued pretraining on culturally *grounded* data measurably shift a
model's cultural alignment, beyond mere language exposure?

Staged under `contrib/` (like `jneums-consortium-experiment`) while it iterates.

## What it does

Runs the EXP-001 arms end to end: starts every arm from the same base model,
applies each arm's treatment, then measures each on two instruments plus a
capability score, and reports the decisive comparisons.

| Arm | Treatment | Isolates |
| :-- | :-------- | :------- |
| `base` | none | baseline + noise floor |
| `language_matched` | CPT on same-language, value-neutral text | — |
| `grounded` | CPT on culturally grounded text | the treatment |
| `grounded_translated` | CPT on grounded content in the base's language | content vs. the language carrying it |
| `surface_only` | no CPT; cultural persona prompt at measurement | does CPT beat cheap prompting? |

Decisive comparisons are `grounded`'s survey shift toward the target minus each
other arm's. `grounded vs language_matched` asks if grounding adds anything
beyond language; `grounded vs surface_only` asks if expensive CPT beats
prompting — **a tie there would undercut the depth-over-shallow architectural
bet.**

Two instruments, both producing an Inglehart-Welzel coordinate:
- **WVS survey** (`wvs.py`) — abstract value questions.
- **Behavioral probe** (`behavior.py`) — concrete situations with action
  choices. The **survey-behavior gap** is the deep-vs-surface guardrail: if an
  arm's *survey* answers move toward the target culture but its *behavior* does
  not (a large gap / lag), the apparent shift is surface mimicry, not a
  representational change. This is clause (c) of the hypothesis and the most
  important failure mode to catch.

## Two modes

| Mode | Model | Purpose |
| :--- | :---- | :------ |
| `smoke` (default) | byte-level toy (`ByteCausalModel`, vocab 256) | exercises the whole pipeline in CI — no downloads, no GPU. **Numbers are noise; it proves plumbing, not the hypothesis.** |
| `hf` | real HF causal LM (`HFCausalModel`) | where the actual EXP-001 signal comes from. Implemented; needs `transformers` installed. |

The architecture is identical across modes — swapping in a real base is a config
change (`--mode hf --model-name ...`), not a rewrite. Everything the model must
provide reduces to two primitives on the `LanguageModel` protocol:
`train_on_texts` (CPT) and `score_continuation` (teacher-forced log-prob, used
by both instruments).

**Two orthogonal axes of realism.** The *model backend* (`--mode smoke|hf`) and
the *corpus realism* (`--corpus-path`, empty = placeholder text) are
independent. A run is only an EXP-001 *result* when **both** are real; otherwise
the output carries a `NOT A RESULT` caveat naming exactly which part is still a
placeholder. This is deliberate — it lets you validate the HF wiring (real model
+ placeholder text) without anyone mistaking it for a finding.

### Real mode

```shell
uv pip install --python .venv/bin/python transformers   # optional dep, not in core manifest

# real model, placeholder corpora -> validates wiring, still "NOT A RESULT"
uv run python contrib/cultural-cpt-validation/run.py \
  --mode hf --model-name distilgpt2 --culture vietnam

# a real EXP-001 run additionally needs real corpora:
#   ... --corpus-path <grounded + language-matched data source>
```

`distilgpt2` is fine for wiring; a proper base/instruct model is needed for real
signal. `transformers` is lazily imported and intentionally **not** added to the
project's core dependencies (this is staged contrib code).

## Run

```shell
# three-arm go/no-go (smoke default)
make cultural-cpt-validation          # -> runs/cultural_cpt_validation/result.json

# aggregation-survival: do cultures stay separable under FedAvg?
make cultural-cpt-aggregation         # -> runs/cultural_cpt_aggregation/result.json

# tests
make cultural-cpt-tests
```

Or directly, e.g. `uv run python contrib/cultural-cpt-validation/run.py
--culture vietnam` (with `PYTHONPATH` set to `src` + this dir).

## Two experiments

- **`run.py`** — the single-node three-arm go/no-go (Base / Language-matched /
  Grounded). *Does grounded CPT shift one node's coordinate?*
- **`run_aggregation.py`** — the multi-node consortium loop. Each round every
  culture does grounded CPT, is measured, then all forks are FedAvg-averaged.
  Reports the **separability curve** (mean pairwise distance between cultures
  over rounds). *Do distinct cultures survive aggregation, or collapse toward
  the centroid?* This is the Tapestry-unique / non-IID (T3) question.

## What is real vs. placeholder

**Real and reusable as-is:**
- arm structure and the Base-relative shift-toward-ground-truth metric;
- WVS administration mechanics — option-order randomization, paraphrase passes,
  log-prob answer selection;
- the `LanguageModel` protocol and the smoke backend.

**Placeholder — must be replaced for a real result (see the spec):**
- `cultural_cpt/corpora.py` — tiny illustrative text. Real run loads a genuinely
  *grounded* corpus and its *language-matched neutral twin*. **Validity depends
  on these differing only in cultural grounding.**
- `cultural_cpt/wvs.py` — abbreviated item battery and approximate national
  coordinates. Real run uses the full WVS items + published factor loadings
  (Tao et al. 2024; Sukiennik 2025).
- `cultural_cpt/capability.py` — toy MCQs. Real run uses MMLU via
  lm-evaluation-harness.
- `HFCausalModel` — stub; implement the two primitives against `transformers`.

## Not in this harness (round two)

All five arms are present. Still outstanding: **multi-seed statistics** (the
shifts are currently single-seed point estimates; a pass/fail threshold needs
effect sizes with error bars across seeds and paraphrases) and **real corpora**
(the binding constraint — Stage 0 data work, not code). The FedAvg
aggregation-survival test is present in smoke form (`run_aggregation.py`); its
real-mode version (HF backend per node) is round-two work. The behavioral probe
(`behavior.py`) is scored by log-prob over fixed action options; a real run
wants free-form generation scored by humans or a rubric-driven judge.
