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

# a real EXP-001 run additionally needs real corpora (loaded + validated from a
# corpus root; see data/README.md and fetch_corpus.py):
#   ... --corpus-path contrib/cultural-cpt-validation/data/<culture>
```

Corpus loading, the permissive-license allowlist, WVS decontamination, and the
matched-twin control now live in [`cultural_cpt/dataset.py`](cultural_cpt/dataset.py);
[`fetch_corpus.py`](fetch_corpus.py) assembles a corpus from permissive sources
and re-validates it. A real, attributed demonstration seed
([`data/seed-example/`](data/seed-example)) ships with the repo so the real-data
path is exercised end to end (`make cultural-cpt-validate-corpus`). What remains
for a real *result* is a high-WVS-distance target culture's corpus in its own
language and a real instruct base — see [`data/README.md`](data/README.md).

`distilgpt2` is fine for wiring; a proper base/instruct model is needed for real
signal. `transformers` is lazily imported and intentionally **not** added to the
project's core dependencies (this is staged contrib code).

## Run

```shell
# arms experiment, single seed (smoke default)
make cultural-cpt-validation          # -> runs/cultural_cpt_validation/result.json

# multi-seed go/no-go: mean +- std, effect sizes, PASS/FAIL on the threshold
make cultural-cpt-stats               # -> runs/cultural_cpt_stats/result.json

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

**Real and reusable (added):**
- `cultural_cpt/dataset.py` — real JSONL corpus loader that *enforces* the
  validity controls (permissive licensing, language/register/recency match,
  matched-twin token budget, WVS decontamination) and fails loudly otherwise.
- `fetch_corpus.py` + `data/seed-example/` — a fetcher and a committed real seed.

**Placeholder — must be replaced for a real result (see the spec):**
- `cultural_cpt/corpora.py` — tiny illustrative text for *smoke* mode only. With
  `--corpus-path` the run loads a genuinely *grounded* corpus and its
  *language-matched neutral twin* via `dataset.py`. **Validity depends on these
  differing only in cultural grounding — which `dataset.py` now checks.** The
  remaining data work is assembling a high-WVS-distance culture's real corpus.
- `cultural_cpt/wvs.py` — abbreviated item battery and approximate national
  coordinates. Real run uses the full WVS items + published factor loadings
  (Tao et al. 2024; Sukiennik 2025).
- `cultural_cpt/capability.py` — toy MCQs. Real run uses MMLU via
  lm-evaluation-harness.
- `HFCausalModel` — stub; implement the two primitives against `transformers`.

## The pre-registered decision

`run_stats.py` runs the arms across seeds and applies the EXP-001 threshold:
**PASS** iff (1) `grounded` survey shift `>= min_grounded_shift`, (2) the
`grounded - language_matched` effect clears `sigma_multiple` std devs across
seeds (with positive sign), and (3) capability drop `<= max_capability_drop`.
Set these thresholds (CLI flags / `StatsConfig`) *before* running. The
sign-and-z rule matters: a large z with a negative mean is a spurious effect in
the wrong direction, and the rule rejects it.

## Not in this harness (round two)

The binding constraint is **real corpora** (Stage 0 data work, not code) — the
grounded corpus and its language-matched twin. With those plus a real instruct
base, the existing `run_stats.py` produces an actual go/no-go. Remaining code
items: real-mode aggregation (HF backend per node), and upgrading the behavioral
probe from log-prob-over-fixed-options to free-form generation scored by humans
or a rubric-driven judge.
