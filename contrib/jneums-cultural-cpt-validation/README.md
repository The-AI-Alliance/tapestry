# Cultural-CPT validation harness (EXP-001)

A runnable harness for the experiment specified in
[`SPEC.md`](SPEC.md):
does continued pretraining on culturally *grounded* data measurably shift a
model's cultural alignment, beyond mere language exposure?

Staged under `contrib/` (like `jneums-consortium-experiment`) while it iterates.

> **Status: executed; result is bounded.** Run for real on Qwen3-4B base/instruct,
> real Arabic-Wikipedia corpora, plus a 3-culture FedAvg aggregation and a behavioral
> probe. The honest finding is **real but shallow**: grounded CPT shifts a **base**
> model's **survey-measured** values toward the target culture **more than a
> language-matched corpus does** (z≈3, surviving corpus resampling *and* FedAvg
> aggregation, capability/refusal preserved) — but it does **not** reach open-ended
> behavior (a survey-behavior dissociation), the absolute pull is small and trades off
> against value-specificity at scale, and it requires the base model. Full results,
> methodology, and limitations are in [`FINDINGS.md`](FINDINGS.md); the pre-registered
> design is in [`SPEC.md`](SPEC.md). This README covers **running the harness**.

## Where this fits in Tapestry

Project Tapestry trains a consortium base model whose partners build and own **sovereign
cultural derivatives**; its first work streams are **LLM cultural alignment** — measured on the
**Inglehart–Welzel cultural map** ([issue #22](https://github.com/The-AI-Alliance/tapestry/issues/22))
— and **consortium training** ([issue #24](https://github.com/The-AI-Alliance/tapestry/issues/24)).
This contribution is the **validation / measurement-rigor** layer for that work: rather than a new
alignment *recipe*, it is a falsifiable test of whether a claimed cultural shift is *real,
content-driven, deep (not survey-only), capability-safe, and aggregation-robust* — the foundational
hypothesis (TAP-003) that any alignment technique assumes. It is **complementary** to the other
contributions staged alongside it — notably `contrib/nguyennm1024-sociocultural-alignment` (which
pursues IW-map cultural alignment by a different method: LoRA SFT on synthesized data, fused with a
model soup) and `contrib/jneums-consortium-experiment` (coordinator metrics) — which it neither
audits nor depends on; cross-references are provenance, not claims about that work.

## What it does

Runs the EXP-001 arms end to end: starts every arm from the same base model,
applies each arm's treatment, then measures each on two instruments plus a
capability score, and reports the decisive comparisons. **The arms, the decisive
comparisons (`grounded` vs `language_matched`, `grounded` vs `surface_only`), and
the hypothesis they test are specified in [`SPEC.md`](SPEC.md)** — this README
covers running the harness, not the design.

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
uv run python contrib/jneums-cultural-cpt-validation/run.py \
  --mode hf --model-name distilgpt2 --culture vietnam

# a real EXP-001 run additionally needs real corpora (loaded + validated from a
# corpus root; see data/README.md and fetch_corpus.py):
#   ... --corpus-path contrib/jneums-cultural-cpt-validation/data/<culture>
```

Corpus loading, the permissive-license allowlist, WVS decontamination, and the
matched-twin control now live in [`cultural_cpt/dataset.py`](cultural_cpt/dataset.py);
[`fetch_corpus.py`](fetch_corpus.py) assembles a corpus from permissive sources
and re-validates it. A real, attributed demonstration seed
([`data/seed-example/`](data/seed-example)) ships with the repo so the real-data
path is exercised end to end (`make cultural-cpt-validate-corpus`). The recorded
runs use a real high-WVS-distance corpus (Egypt, Arabic Wikipedia) on Qwen3-4B —
both the **instruct** (`Qwen3-4B-Instruct-2507`) and **base** (`Qwen3-4B-Base`)
checkpoints; the decisive result is on the base model (see
[`data/README.md`](data/README.md) and [`FINDINGS.md`](FINDINGS.md)).

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

Or directly, e.g. `uv run python contrib/jneums-cultural-cpt-validation/run.py
--culture vietnam` (with `PYTHONPATH` set to `src` + this dir).

## Two experiments

- **`run.py`** — the single-node three-arm go/no-go (Base / Language-matched /
  Grounded). *Does grounded CPT shift one node's coordinate?*
- **`run_aggregation.py`** — the multi-node consortium loop. Each round every
  culture does grounded CPT, is measured, then all forks are FedAvg-averaged.
  Reports the **separability curve** (mean pairwise distance between cultures
  over rounds). *Do distinct cultures survive aggregation, or collapse toward
  the centroid?* This is the Tapestry-unique / non-IID (T3) question.

## What is real vs. smoke-only

Everything needed for a real EXP-001 result is now wired and has been used across
the 11 runs in [`FINDINGS.md`](FINDINGS.md). The only smoke-mode-only pieces are
the toy fixtures that exist so CI can exercise the pipeline without a GPU or
downloads.

**Real (used in the recorded runs):**
- `HFCausalModel` — real `transformers` backend (`--mode hf`); the `train_on_texts`
  (full-parameter CPT) and `score_continuation` primitives both run against a real
  model. `transformers` is lazily imported and not a core dependency.
- `cultural_cpt/wvs.py` — the canonical 10-item Inglehart–Welzel battery with
  **real published WVS-7 factor-score coordinates** (`GROUND_TRUTH`, from the
  EVS/WVS-2023 cultural map; Tao et al. 2024, Sukiennik 2025).
- `cultural_cpt/capability.py` — **real MMLU + Arabic-MMLU** via
  `datasets.load_dataset` on a GPU box (the hand-written MCQs are the smoke
  fallback only).
- `cultural_cpt/dataset.py` — JSONL corpus loader that *enforces* the validity
  controls (permissive licensing, language/register/recency match, matched-twin
  token budget, WVS decontamination) and fails loudly otherwise.
- `fetch_corpus.py` + `data/seed-example/` — corpus fetcher and a committed,
  attributed real seed.
- arm structure and the Base-relative shift-toward-ground-truth metric; WVS
  administration mechanics (option-order randomization, paraphrase passes,
  log-prob answer selection); the `LanguageModel` protocol.

**Smoke-only (CI fixtures — not used for results):**
- `cultural_cpt/corpora.py` — tiny illustrative text for the default `smoke` mode.
  With `--corpus-path` the run instead loads a real *grounded* corpus and its
  *language-matched neutral twin* via `dataset.py`. **Validity depends on the two
  differing only in cultural grounding — which `dataset.py` checks.**
- the byte-level toy model and the hand-written capability MCQs, both swapped out
  automatically in `--mode hf` real runs.

## The pre-registered decision

`run_stats.py` runs the arms across seeds (and, with `--corpus-draws`, across
corpus resamples) and applies the EXP-001 threshold: **PASS** iff **all four**
conjuncts hold — (1) `grounded` survey shift `>= min_grounded_shift`, (2) the
`grounded - language_matched` effect clears `sigma_multiple` std devs with
positive sign, (3) capability drop `<= max_capability_drop`, and (4) refusal-rate
drop `<= max_safety_drop`. Set these thresholds (CLI flags / `StatsConfig`)
*before* running. The sign-and-z rule matters: a large z with a negative mean is a
spurious effect in the wrong direction, and the rule rejects it. The noise band
the z is measured against is the **corpus-resampling** band, not the cross-seed
band — see [`FINDINGS.md`](FINDINGS.md) for why that distinction decides the
experiment.

## Not in this harness (round two)

The single-node go/no-go is done (real corpora, real bases, generate-mode
behavioral probe — all landed). What remains for round two:

- **Consortium / aggregation survival** — real-mode `run_aggregation.py` (HF
  backend per node): does the cultural shift survive FedAvg across cultures, or
  collapse toward the centroid? This is the Tapestry-unique (T3) question and is
  not yet run.
- **Behavioral transfer** — the probe was upgraded to free-form generation scored
  by an embedding judge, but no arm has moved open-ended behavior in any run;
  demonstrating representational (not survey-only) transfer is the open H1(c)
  question.
- **Closing the absolute-magnitude gap** — scale base-model tokens/epochs to push
  the absolute shift past the 0.05 bar (the one conjunct Run 11 still failed).
