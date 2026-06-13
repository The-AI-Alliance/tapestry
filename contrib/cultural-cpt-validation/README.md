# Cultural-CPT validation harness (EXP-001)

A runnable harness for the experiment specified in
[`tech-docs/experiments/cultural-cpt-validation.md`](../../tech-docs/experiments/cultural-cpt-validation.md):
does continued pretraining on culturally *grounded* data measurably shift a
model's cultural alignment, beyond mere language exposure?

Staged under `contrib/` (like `jneums-consortium-experiment`) while it iterates.

## What it does

Runs the **minimal three-arm go/no-go** — Base / Language-matched / Grounded —
end to end: starts every arm from the same base model, applies each arm's
treatment (no CPT, or CPT on that arm's corpus), then measures an
Inglehart-Welzel coordinate (WVS survey instrument) and a capability score, and
reports whether **Grounded** moved toward the target nation's ground-truth
coordinate more than **Language-matched** did.

## Two modes

| Mode | Model | Purpose |
| :--- | :---- | :------ |
| `smoke` (default) | byte-level toy (`ByteCausalModel`, vocab 256) | exercises the whole pipeline in CI — no downloads, no GPU. **Numbers are noise; it proves plumbing, not the hypothesis.** |
| `hf` | real HF causal LM (`HFCausalModel`) | where the actual EXP-001 signal comes from. A documented stub until `transformers` is added. |

The architecture is identical across modes — swapping in a real base is a config
change (`--mode hf --model-name ...`), not a rewrite. Everything the model must
provide reduces to two primitives on the `LanguageModel` protocol:
`train_on_texts` (CPT) and `score_continuation` (teacher-forced log-prob, used
by both instruments).

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

The behavioral / scenario probe (deep-vs-surface) and Arms 3–4
(grounded-translated, surface-only) are still follow-ups once a basic
single-node effect is confirmed. See the spec. The FedAvg aggregation-survival
test is now present in smoke form (`run_aggregation.py`); its real-mode version
(HF backend per node) is round-two work.
