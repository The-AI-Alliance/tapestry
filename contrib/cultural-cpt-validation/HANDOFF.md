# EXP-001 cultural-CPT — handoff

Status as of 2026-06-15. Branch `experiment/cultural-cpt-validation` (local, not
pushed; ~25 commits ahead of `develop`). All work lives under
`contrib/cultural-cpt-validation/`.

This doc orients whoever picks this up next. The experiment spec is
[`SPEC.md`](SPEC.md);
the numbered run results are [`FINDINGS.md`](FINDINGS.md); the corpus/loader
contract is [`data/README.md`](data/README.md); the GPU recipe is
[`deploy/README.md`](deploy/README.md).

## TL;DR

The harness now runs **real end-to-end EXP-001 go/no-go experiments**: a real
base model (Qwen) does full-parameter CPT on a real Arabic corpus, then is
measured on the canonical Inglehart-Welzel WVS instrument (in Arabic) plus a
free-form behavioral probe, across seeds, with a pre-registered PASS/FAIL.

**Headline finding (8 runs, see FINDINGS):** Run 7's corpus-resampled band put
grounded−language at **+0.040 ± 0.044 (z=0.91)** — small, positive, not significant
against corpus noise. **Run 8 scaled tokens+epochs** (807k/673k tokens, 6 epochs)
and changed the picture in two ways. First, it **falsified the standing assumption
that HF training is deterministic across seeds**: the seed changes the *training
outcome* (one seed's neutral arm catastrophically degenerated — capability
0.79→0.08 — others stayed healthy), so the cross-seed band is **real training
stochasticity**, not measurement-only — earlier z-scores (incl. Run 5's 7.26) leaned
on a now-false premise. Second, it pinned the **mechanism**: grounded CPT does *not*
pull toward Egypt (absolute shift −0.021); rather **value-neutral CPT damages the
model (capability 0.79→0.51, refusal 1.00→0.62) and grounded CPT does so far less.**
So grounded−language (+0.108, z=1.15 — biggest point estimate, still <2σ) is a
**forgetting-robustness asymmetry, not value acquisition.** Prompting still beats CPT
(grounded−surface z=−3.25). Pre-registered verdict: **FAIL in all eight runs**
(Run 8 also fails the safety conjunct). **The next experiment (the replay/anchor
mitigation arm + training stabilization) is now BUILT and ready to run as Run 9** —
a `grounded_replay` arm that mixes general English text into the grounded CPT to
suppress forgetting, plus warmup/grad-clip/shuffle to stop seeds cratering. See the
"Run 9" recipe in FINDINGS. Artifacts: `runs/egypt_stats_scaled/` (Run 8),
`runs/egypt_stats_resampled/` (Run 7).

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
- **Replay / anchor mitigation arm + training stabilization** (Run 8 follow-up):
  `--replay-fraction F` (env `REPLAY_FRACTION`) adds a `grounded_replay` arm that
  mixes a fraction `F` of general, value-neutral English text (the base model's
  pretraining distribution, built by `fetch_corpus.py --replay`) into the grounded
  CPT to rehearse against catastrophic forgetting. It reports `replay_vs_grounded`
  (the replay effect) and `replay_vs_language` (grounding-beyond-language with
  forgetting suppressed). The HF training loop is stabilised with linear LR
  warmup→decay (`--warmup-frac`), gradient clipping (`--max-grad-norm`), and
  per-epoch deterministic shuffling (which also interleaves the replay mix). The
  pre-registered decision is unchanged — it still keys on `grounded`, so replay is
  reported, not gated. KL-anchoring was deferred (a frozen 4B reference + the
  trainable model won't fit one 32GB GPU).
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
- **51 tests** (`tests/`), all green; `ruff` clean; black-formatted (line 120).

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

The env-specific identifiers for our own self-rental box — machine id, host, offer
ids, the API-key path, and which SSH key to use — live in the **git-ignored**
[`deploy/vast.local.md`](deploy/vast.local.md) (kept out of this public-bound repo).
Read that first for the actual values; the generic, reusable gotchas below are what
matter for *any* Vast.ai 5090 box:

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

0. **DONE — corpus-resampled go/no-go (Run 7).** The `--corpus-draws` sweep ran
   (4 draws, `runs/egypt_stats_resampled/`): grounded−language is +0.040 ± 0.044
   (z=0.91) — small, positive, **not significant** against the real corpus band.
   This settled the Run 5 vs 6 contradiction (both were single draws). The effect
   is underpowered, not null. Next decisions branch from here:
0b. **BUILT, not yet run — replay/anchor mitigation arm + training stabilization
   (Run 9, the headline experiment).** `grounded_replay` arm (`REPLAY_FRACTION`)
   mixes general English text into grounded CPT to suppress forgetting; HF training
   now has warmup/grad-clip/shuffle (`WARMUP_FRAC`/`MAX_GRAD_NORM`) so seeds stop
   cratering. Reports `replay_vs_grounded` + `replay_vs_language`; decision still
   keyed on `grounded`. Recipe + how-to-read in FINDINGS "Run 9". **This is what to
   run with the next GPU window.**
1. **Grow the per-draw effect, then re-resample.** Confirming a +0.04 effect
   against ±0.044 would need ~dozens of draws (not worth it); make each draw bigger
   first — **more tokens (10×+) and more epochs** (real CPT is millions of tokens;
   we use ~300k). Then re-run the sweep; a +0.08–0.10 per-draw effect clears the
   band with few draws. Infra ready — raise `MAX_TOKENS`/`CAT_LIMIT`/`EPOCHS`.
2. **Understand the away-drift** — the absolute grounded shift is negative across
   Runs 6–7; *why* does Arabic CPT (grounded or neutral) push the coordinate off
   Egypt? Catastrophic-forgetting-style drift vs. genuine value movement is now the
   more interesting science, measurable with the current harness.
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
Qwen3-4B via Vast.ai 5090s. Run 7's corpus-resampled sweep gave grounded−language
+0.040 ± 0.044 (z=0.91, not significant). Run 8 scaled tokens+epochs (807k/673k,
6ep) and reframed it: (a) training is NOT deterministic across seeds — the seed
tips runs into catastrophic degeneration (neutral arm capability 0.79→0.08 in one
seed), so the cross-seed band is real training noise, not measurement-only; (b) the
grounding effect (+0.108, z=1.15, still <2σ) is forgetting-robustness, not value
pull — grounded CPT preserves the model while value-neutral CPT damages it
(capability 0.79→0.51, refusal→0.62); absolute grounded shift ≈0. Prompting still
beats CPT (z=−3.25). FAIL all 8 runs. Next (BUILT, ready for Run 9): the
replay/anchor mitigation arm + training stabilization — a `grounded_replay` arm
(`REPLAY_FRACTION`) that mixes general English text into grounded CPT to suppress
forgetting, plus warmup/grad-clip/shuffle (`WARMUP_FRAC`/`MAX_GRAD_NORM`) so seeds
stop cratering; run it, then re-resample on the stabilised setup. See FINDINGS.md
"Run 9" for the recipe and how to read it. Harness also checkpoints per seed
(re_aggregate.py) and is non-finite-robust — an 8-epoch attempt crashed in final
stats and lost the run; that can't happen now."
