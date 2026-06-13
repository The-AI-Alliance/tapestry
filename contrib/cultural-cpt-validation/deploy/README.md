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
