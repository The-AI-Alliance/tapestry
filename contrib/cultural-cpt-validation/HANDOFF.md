# EXP-001 cultural-CPT — handoff

Status as of 2026-06-14. Branch `experiment/cultural-cpt-validation` (local, not
pushed; ~24 commits ahead of `develop`). Working tree clean. All work lives under
`contrib/cultural-cpt-validation/`.

This doc orients whoever picks this up next. The experiment spec is
[`tech-docs/experiments/cultural-cpt-validation.md`](../../tech-docs/experiments/cultural-cpt-validation.md);
the numbered run results are [`FINDINGS.md`](FINDINGS.md); the corpus/loader
contract is [`data/README.md`](data/README.md); the GPU recipe is
[`deploy/README.md`](deploy/README.md).

## TL;DR

The harness now runs **real end-to-end EXP-001 go/no-go experiments**: a real
base model (Qwen) does full-parameter CPT on a real Arabic corpus, then is
measured on the canonical Inglehart-Welzel WVS instrument (in Arabic) plus a
free-form behavioral probe, across seeds, with a pre-registered PASS/FAIL.

**Headline finding (6 runs, see FINDINGS):** Run 5's promising decisive result —
grounded CPT vs. value-neutral CPT in the same language at **+0.080, z=7.26** —
**did NOT replicate** in Run 6. On a freshly-sampled corpus with the upgraded
harness (real MMLU/safety guardrails + the new translated arm), grounded−language
collapses to null (**−0.008, z=−0.29**), grounded drifts away from Egypt as much
as the neutral twin, and the new Arm 3 shows the content's language is irrelevant
(grounded ≈ grounded_translated, z=0.05). Current honest position: **no robust
evidence** that grounded micro-CPT moves IW coordinates more than neutral CPT at
this scale — Run 5 looks corpus-sample-specific, inflated by a measurement-only
noise band. What *does* hold across all six runs: capability (now real) is
preserved, and a one-line persona prompt (`surface_only`) beats CPT every time
(Run 6: grounded−surface z=−6.27). The pre-registered verdict has been FAIL in
every run.

## What the harness can do now

- **Two model backends** behind one `LanguageModel` protocol (`model.py`):
  `ByteCausalModel` (smoke/CI, no GPU) and `HFCausalModel` (real). Primitives:
  `train_on_texts` (CPT), `score_continuation` (teacher-forced log-prob),
  `generate` (free-form), `clone`.
- **Fits a ~4B full fine-tune on one 32GB GPU**: base kept on CPU, per-arm clone
  moved to GPU, bf16, gradient checkpointing, 8-bit Adam (bitsandbytes), doc
  chunking to `max_length`. Still full-parameter CPT (not LoRA) — the
  depth-over-shallow test is intact.
- **Real corpus pipeline** (`fetch_corpus.py` + `dataset.py`): assembles a
  matched grounded/neutral twin from Wikipedia (curated titles **and** category
  members), enforces the validity controls at load (permissive licensing,
  language/register/recency match, twin token-budget, WVS decontamination), and
  fails loudly otherwise. `--max-tokens` bounds corpus size (→ run time);
  `--max-words` bounds per-article length.
- **Canonical WVS instrument in EN and AR** (`wvs.py`): the 10 Inglehart-Welzel
  items, ≥3 paraphrases each, expected-value scoring; national ground truth from
  the published WVS-7 map. `--instrument-lang en|ar`.
- **Behavioral probe, two modes** (`behavior.py` + `judge.py`): `logprob`
  (fixed-option) and `generate` (model writes an action, a multilingual
  `EmbeddingJudge` scores it). `--behavior-mode logprob|generate`.
- **Multi-seed pre-registered go/no-go** (`run_stats.py` / `stats.py`):
  mean±std, effect sizes (z), PASS/FAIL on `min_grounded_shift` /
  `sigma_multiple` / `max_capability_drop`.
- **Corpus-resampled go/no-go** (`run_stats.py --corpus-draws N --corpus-fraction
  F`, `stats.run_corpus_resampled`): re-runs the whole multi-seed experiment on N
  deterministic token-budget subsamples of the pool and decides on the
  **cross-draw** band — the real variance source, since HF training is
  deterministic across seeds, so the cross-seed std understated it. This is the
  direct test of whether Run 5's effect was corpus-sample-specific. The
  matched-twin token-budget control is enforced per draw; draws are SHA-256-seeded
  so a sweep reproduces exactly. See `deploy/README.md` "Corpus resampling".
- **Aggregation-survival experiment** (`run_aggregation.py`): FedAvg across
  cultures (round-two; smoke only so far).
- **46 tests** (`tests/`), all green; `ruff` clean; black-formatted (line 120).

## Repo map (the files that matter)

| file | what |
| :-- | :-- |
| `cultural_cpt/model.py` | backends + `LanguageModel` protocol + memory plumbing |
| `cultural_cpt/dataset.py` | real corpus loader + the validity controls |
| `cultural_cpt/wvs.py` | WVS battery (EN+AR) + IW ground truth + scoring |
| `cultural_cpt/behavior.py` | behavioral probe (logprob + generate modes) |
| `cultural_cpt/judge.py` | `EmbeddingJudge` for free-form behavior |
| `cultural_cpt/experiment.py` | one-run orchestration (arms → CPT → measure) |
| `cultural_cpt/stats.py` | multi-seed aggregation + go/no-go decision |
| `cultural_cpt/capability.py` | capability guardrail — bilingual bank + optional real MMLU |
| `cultural_cpt/safety.py` | refusal/safety guardrail (log-prob refusal-vs-comply) |
| `run.py` / `run_stats.py` / `run_aggregation.py` | CLIs |
| `fetch_corpus.py` | corpus assembler (+ `--validate`, `--translate` for Arm 3) |
| `titles/egypt.ar.json`, `titles/vietnam.vi.json` | curated titles + categories per culture |
| `deploy/run_on_instance.sh` | the on-GPU-box runner (env-parameterized) |
| `deploy/README.md` | Vast.ai self-rental recipe |
| `data/` | corpora (bulk git-ignored; only the committed seed travels) |

## How to run

```shell
# smoke (CI, no GPU): proves plumbing, numbers are noise
make cultural-cpt-validation
make cultural-cpt-tests

# validate a corpus against the controls
make cultural-cpt-validate-corpus CORPUS=contrib/cultural-cpt-validation/data/egypt

# a real run on a CUDA box (see deploy/ for the parameters used in Run 5):
REPO=/workspace/tapestry MODEL=Qwen/Qwen3-4B-Instruct-2507 \
  SEEDS=0,1,2 EPOCHS=4 PER_DOMAIN=18 MAX_WORDS=4000 CAT_LIMIT=25 MAX_TOKENS=300000 \
  DTYPE=bfloat16 INSTRUMENT_LANG=ar BEHAVIOR_MODE=generate \
  bash contrib/cultural-cpt-validation/deploy/run_on_instance.sh
```

Run outputs land in `runs/<…>/result.json` (git-ignored). The numbers from the
five real runs are transcribed in `FINDINGS.md` so they survive.

## Vast.ai operational playbook (hard-won; read before the next GPU run)

Our self-rental machine: **id 138905, host `alpha`, 2× RTX 5090 (32GB each)**.
Offers: `40741822` (1× 5090), `40741823` (2× 5090). API key at
`/tmp/hvl-vast/api_key` (a **team-context** key — this matters below).

Gotchas we hit and the fixes baked into the flow:

1. **The 5090 is Blackwell (`sm_120`)** → needs CUDA 12.8+ / PyTorch ≥2.7. Use
   image `pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime`. Older images load but
   die at the first kernel.
2. **`--bid_price` at create does NOT stick** → the instance shows "outbid" /
   stays stopped. After create you must `vastai change bid <id> --price 3.0`
   then `vastai start instance <id>`.
3. **The machine is unverified** → `vastai search offers` hides it unless you
   pass `verified=any`.
4. **Team key can't register account SSH keys.** Use **per-instance**
   `vastai attach ssh <id> "$(cat ~/.ssh/id_rsa.pub)"`. The local key must be
   **unencrypted** — a passphrase-protected key fails silently with "Permission
   denied (publickey)" (id_ed25519 was encrypted; id_rsa worked).
5. **Connect via the proxy** `sshN.vast.ai:<ssh_port>` (the `--direct` public
   port was firewalled for us).
6. **`vastai execute` is restricted** to file ops, not arbitrary commands — use
   ssh for real work.
7. **Code transfer:** the branch is unpushed, so `tar` `src/tapestry` +
   `contrib/cultural-cpt-validation` (~60KB), `scp` it, extract to
   `/workspace/tapestry`. (See the create→bid→attach→start→scp→run→poll→pull→
   destroy sequence used in this session.)
8. **Runs are silent during training** (the harness logs only at the end). Poll
   `pgrep -f run_stats.py` + existence of `runs/.../result.json`, not log
   content. A momentarily idle GPU usually means the run just finished.
9. **Always `vastai destroy instance <id> -y` when done** (needs `-y`; it prompts
   otherwise). Confirm with `vastai show instances`.

## What is real vs. still placeholder

**Real:** model backends, full-CPT memory path, corpus loader + controls, the
EN/AR/**VI** WVS instruments, the generate-mode behavioral probe + embedding
judge, multi-seed go/no-go, the Egypt Arabic corpus (regenerable from `titles/`).

**Newly real (this session — all local, no GPU yet):**
- **Capability guardrail** (`capability.py`) is no longer the 4-item toy: a
  ~24-item bilingual (EN/AR) general-knowledge bank with varied answer indices,
  measured in the corpus's language, **plus** an optional real MMLU/Arabic-MMLU
  loader (`use_external`, best-effort via `datasets` on the GPU box, falls back
  to the bank). Wired into the go/no-go's `max_capability_drop`.
- **Safety guardrail** (`safety.py`, new): a deterministic refusal probe —
  harmful-request stems scored refusal-vs-compliance by log-prob, EN/AR, **no
  operational harmful content**. Reported per arm as `safety_refusal` and gated
  by a new `max_safety_drop` conjunct in the pre-registered decision.
- **`grounded_translated` (Arm 3)** is now buildable: `fetch_corpus.py
  --translate` MT's the grounded corpus to English (Opus-MT), decontaminates,
  and declares the arm. The harness already runs it when the manifest has it, so
  `decisive_grounded_vs_translated` stops being a skipped 0.0.
- **Second culture: Vietnam.** `titles/vietnam.vi.json` + full Vietnamese WVS &
  behavior batteries (`_ITEMS_VI`/`_SCENARIOS_VI`) + `vi` persona/suffixes, so
  Vietnam is measurable **in-language** (the lever that mattered most for Egypt).
- 40 tests green (added `test_guardrails.py`, `test_corpus_build.py`); ruff +
  black clean.

**Still placeholder / weak:**
- **Ground-truth coordinates** are read from the published IW map and rescaled,
  not exact WVS-data-file factor scores (seam: `wvs._from_map`). Vietnam's target
  `(0.16, -0.44)` is map-derived like the rest.
- **Behavioral judge** is embedding-similarity; an LLM-as-judge would be higher
  quality (but adds an external dependency / cost / nondeterminism).
- The external MMLU path and the `--translate` MT are **untested on real
  hardware** (no `datasets`/MT model locally); both are best-effort with clean
  fallbacks, but the next GPU run is their first live exercise.
- Aggregation experiment is **smoke-only** (no HF/per-node real CPT yet).

## Open questions & recommended next steps

After Run 6 the honest read is: no robust grounding effect at this scale, and the
z-scores were computed against a measurement-only band. In rough priority:

0. **DECISIVE NEXT RUN — corpus-resampled go/no-go (now wired).** Run the
   `--corpus-draws N --corpus-fraction F` sweep (e.g. `CORPUS_DRAWS=4
   CORPUS_FRACTION=0.7`; see `deploy/README.md`). This decides on the cross-corpus
   band — the variance that actually broke Run 5→6 — and answers whether
   `grounded − language` is genuinely null or merely noisy. Do this *before*
   spending on bigger scale: a positive single-corpus z is meaningless until it
   survives resampling. If the band confirms null → write it up and pivot to (2);
   if a real effect survives → *then* push scale (1).
1. **Push tokens/epochs further** to see if grounded crosses from *prevent-drift*
   into *active pull* (does the absolute shift reach +0.05?). Infra is ready —
   raise `MAX_TOKENS`/`CAT_LIMIT`/`EPOCHS`. Only worth it once (0) shows a
   resampling-robust effect to chase.
2. **Understand the prevent-drift mechanism** — *why* does value-neutral Arabic
   CPT push the model away from Egypt? This may be the more interesting science
   now (catastrophic-forgetting-style drift vs. genuine value movement).
3. **Real capability + safety evals** so H1(d) is testable — the current
   guardrail is a placeholder.
4. **Build the `grounded_translated` arm** to cleanly separate cultural content
   from the language carrying it.
5. **Second culture** (e.g. Vietnam) to check the effect generalizes; the loader
   is culture-agnostic and `titles/` is the only per-culture input.
6. **Upgrade the behavioral judge** to an LLM rubric judge, and/or add real
   training-seed stochasticity (currently cross-seed variance is
   measurement-only, so z-scores are optimistic).

## One-line orientation for a new session

"Real EXP-001 go/no-go harness for culturally-grounded CPT; Egypt/Arabic pilot on
Qwen3-4B via Vast.ai 5090s. Run 5's significant grounded-vs-language result
(z=7.26) did NOT replicate in Run 6 (z=−0.29) on a fresh corpus with real
guardrails + the translated arm — current read: no robust grounding effect at
this scale; prompting beats CPT. The decisive next run is the now-wired
corpus-resampled go/no-go (`--corpus-draws`), which decides on the cross-corpus
band that broke Run 5→6 instead of the measurement-only seed band. See
FINDINGS.md for the six runs and deploy/README.md ('Corpus resampling') to run
it."
