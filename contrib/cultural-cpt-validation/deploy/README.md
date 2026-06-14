# Running the real EXP-001 CPT on the Vast.ai 2×5090 server

This is the recipe for the **real** Egypt run: full-parameter CPT of a real base
model on the real Arabic corpus, measured on the canonical WVS instrument. It
follows the self-rental rules for our own listed machine — **create, use,
destroy**; never `docker run` on the host, never relist/restart the host, never
mutate min-bid.

## Decisions baked in

- **Base model:** `Qwen/Qwen2.5-1.5B-Instruct` — solid Arabic, at the spec's
  ~1B value-expression floor, and a full-parameter CPT fits one 5090 (32 GB) in
  bf16. Override with `MODEL=…`.
- **Full CPT, not LoRA** — the experiment tests the *depth-over-shallow* bet, so
  the treatment arm must be a real full fine-tune (LoRA would conflate with the
  `surface_only` control).
- **bf16** (`DTYPE=bfloat16`) — halves params+grads memory; comfortable on a 5090.

## ⚠️ 5090 needs a modern CUDA stack

The RTX 5090 is Blackwell (`sm_120`) and needs **CUDA 12.8+ / PyTorch ≥ 2.7**.
An older PyTorch image will load but fail at the first kernel with
`no kernel image is available for execution on the device`. Use a recent image,
e.g. `pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime` (or vast's `cuda:12.8`
PyTorch image). Verify on the instance with:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.get_device_name(0))"
```

## Steps

```bash
export VAST_API_KEY="$(cat /tmp/hvl-vast/api_key)"   # the key must be present here
vastai() { command vastai --api-key "$VAST_API_KEY" "$@"; }

# 1. Find OUR machine's offer (self-rental). Filter to the 5090 host we own.
vastai search offers 'gpu_name=RTX_5090 num_gpus>=1 rentable=true' -o 'dph+' --raw
#    -> pick the OFFER_ID that is our machine.

# 2. Create an interruptible instance on it with a CUDA-12.8 PyTorch image.
vastai create instance <OFFER_ID> \
  --image pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime \
  --disk 60 \
  --ssh --direct \
  --bid_price <BID>            # spot/interruptible; ~$0.30-0.60/hr for one 5090

# 3. Get the SSH endpoint once it's "running".
vastai show instance <INSTANCE_ID> --raw   # ports / ssh host+port

# 4. Ship code (branch is unpushed) and the run script to the instance.
SSH="ssh -p <SSH_PORT> root@<SSH_HOST>"
rsync -az -e "ssh -p <SSH_PORT>" \
  --exclude .git --exclude .venv --exclude '**/__pycache__' --exclude runs \
  /home/jesse/tapestry/  root@<SSH_HOST>:/workspace/tapestry/

# 5. Run it (regenerates the corpus on-box, then the experiment).
$SSH 'bash /workspace/tapestry/contrib/cultural-cpt-validation/deploy/run_on_instance.sh'

# 5b. Corpus-RESAMPLED go/no-go (the real noise band; see "Corpus resampling"
#     below). Decides on cross-corpus variance, not the measurement-only seed
#     band. Cost ≈ CORPUS_DRAWS × the single-corpus run.
$SSH 'REPO=/workspace/tapestry MODEL=Qwen/Qwen3-4B-Instruct-2507 \
  SEEDS=0,1,2 EPOCHS=4 PER_DOMAIN=18 MAX_WORDS=4000 CAT_LIMIT=25 MAX_TOKENS=300000 \
  DTYPE=bfloat16 INSTRUMENT_LANG=ar BEHAVIOR_MODE=generate \
  CORPUS_DRAWS=4 CORPUS_FRACTION=0.7 \
  bash /workspace/tapestry/contrib/cultural-cpt-validation/deploy/run_on_instance.sh'

# 6. Pull the result back.
rsync -az -e "ssh -p <SSH_PORT>" \
  root@<SSH_HOST>:/workspace/tapestry/runs/egypt_real/ \
  /home/jesse/tapestry/runs/egypt_real/

# 7. ALWAYS destroy when done (self-rental is interruptible; don't leave it up).
vastai destroy instance <INSTANCE_ID> -y
```

## Reading the result

`runs/egypt_real/result.json` has, per arm, the WVS survey coordinate, the
shift-toward-Egypt vs. Base, the behavioral-probe coordinate + survey-behavior
gap (mimicry guardrail), and the capability score. The decisive line is
`decisive_grounded_vs_language` — grounding beyond language. Because both a real
model and real corpus are used, there is **no `NOT A RESULT` caveat**; this is a
genuine (if small-scale) EXP-001 data point.

For the pre-registered multi-seed go/no-go, run `run_stats.py` with the same
`--mode hf` config across seeds instead of `run.py` (it applies the PASS/FAIL
threshold). Start with `run.py` for one seed to confirm the run is sane and
sized right before spending on multiple seeds.

## Corpus resampling (the real noise band)

Run 5's headline `grounded − language` effect (z=7.26) did **not** survive a
fresh corpus pull (Run 6, z=−0.29). The reason: within one corpus the seeds vary
only *measurement* (HF training is deterministic across seeds), so the cross-seed
std understates the true variance — the real variance is *which documents land in
the twin*. `CORPUS_DRAWS=N` (with `CORPUS_FRACTION<1`) re-runs the whole
multi-seed experiment on `N` deterministic subsamples of the on-disk pool and
decides PASS/FAIL on the **cross-draw** spread of the decisive comparison.

- Each draw samples ~`CORPUS_FRACTION` of each arm's *token mass* (not document
  count), so the matched-twin token-budget control holds per draw.
- Draws are seeded stably (SHA-256), so a sweep reproduces exactly on the box and
  in CI; `result.json` records each draw plus the cross-draw band and verdict.
- `CORPUS_FRACTION` must be `<1.0` (the full pool makes every draw identical).
  0.6–0.8 is a reasonable range; lower fraction = more independent draws but
  fewer tokens each. Cost scales ~linearly with `CORPUS_DRAWS`.

This is the recommended decisive run: it answers whether `grounded − language` is
genuinely null or merely noisy, instead of reading a z-score off the wrong band.
