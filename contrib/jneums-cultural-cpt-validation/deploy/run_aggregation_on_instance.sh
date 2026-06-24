#!/usr/bin/env bash
# Run the EXP-001 consortium / aggregation-survival (T3) experiment ON a GPU box.
#
# The Tapestry-unique question: does cultural alignment survive FedAvg across
# cultures, or collapse toward the centroid? Each round, every culture forks the
# shared global base, does grounded CPT on its own corpus, is measured on the IW
# map IN ITS OWN CORPUS LANGUAGE (resolved from the culture's manifest; aggregation
# v1 surveyed every node on a shared English instrument, which muted the
# foreign-language CPT so the nodes never separated), then all forks are
# FedAvg-averaged into the next global base. The artifact is the SHIFT-space
# SEPARABILITY CURVE (mean pairwise distance between nodes' shift vectors vs the
# round's base, measured in-language so the per-language calibration offset cancels)
# plus the weight-space MERGE DIAGNOSTICS (cosine / sign-agreement / retained-ratio)
# that distinguish genuine cultural homogenization from representational merge
# interference.
#
# Memory strategy (see model.py): the base stays on CPU; each node clones to the
# GPU one at a time and its weights are pulled back to host RAM as a CPU state
# vector, so N full 4B forks never coexist in VRAM. The run checkpoints every
# round (runs/.../rounds/), so a preempted spot box resumes by re-running this.
#
# Override via env: MODEL, CULTURES, ROUNDS, EPOCHS, LR, DTYPE, INSTRUMENT_LANG,
# WARMUP_FRAC, MAX_GRAD_NORM, PER_DOMAIN, MAX_WORDS, CAT_LIMIT, MAX_TOKENS (the
# per-culture grounded token cap that holds corpora COMPARABLE across nodes),
# FETCH (0 to reuse existing corpora), OUT.
set -uo pipefail

REPO="${REPO:-/workspace/tapestry}"
MODEL="${MODEL:-Qwen/Qwen3-4B-Base}"
CULTURES="${CULTURES:-egypt,sweden,vietnam}"
ROUNDS="${ROUNDS:-4}"
EPOCHS="${EPOCHS:-6}"
LR="${LR:-2e-5}"
DTYPE="${DTYPE:-bfloat16}"
INSTRUMENT_LANG="${INSTRUMENT_LANG:-en}"   # fallback only; real nodes are surveyed in their manifest language
WARMUP_FRAC="${WARMUP_FRAC:-0.05}"
MAX_GRAD_NORM="${MAX_GRAD_NORM:-1.0}"
# Corpus regen: each culture's grounded arm is capped to MAX_TOKENS so the nodes
# train on comparable amounts (otherwise a culture under-shifts purely from less
# data and fakes a separability signal). Per-culture language is read from the
# titles filename (titles/<culture>.<lang>.json).
PER_DOMAIN="${PER_DOMAIN:-18}"
MAX_WORDS="${MAX_WORDS:-4000}"
CAT_LIMIT="${CAT_LIMIT:-25}"
MAX_TOKENS="${MAX_TOKENS:-145000}"
FETCH="${FETCH:-1}"
OUT="${OUT:-$REPO/runs/cultural_cpt_aggregation}"

CC="$REPO/contrib/jneums-cultural-cpt-validation"
export PYTHONPATH="$REPO/src:$CC"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "== environment =="
python -c "import torch; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
python -c "import transformers" 2>/dev/null || pip install -q transformers
python -c "import bitsandbytes" 2>/dev/null || pip install -q bitsandbytes

# --- regenerate each culture's grounded corpus to a COMMON token budget ---------
if [ "$FETCH" = "1" ]; then
  MAXW_ARG=""
  [ "$MAX_WORDS" != "0" ] && MAXW_ARG="--max-words $MAX_WORDS"
  IFS=',' read -ra CL <<< "$CULTURES"
  for culture in "${CL[@]}"; do
    titles=$(ls "$CC/titles/${culture}."*.json 2>/dev/null | head -1)
    if [ -z "$titles" ]; then echo "!! no titles file for $culture in $CC/titles/"; exit 2; fi
    lang=$(basename "$titles" | sed -E "s/^${culture}\.([a-z]+)\.json/\1/")
    echo "== fetch $culture ($lang) grounded -> cap $MAX_TOKENS tokens =="
    python "$CC/fetch_corpus.py" \
      --culture "$culture" --lang "$lang" --titles-file "$titles" \
      --per-domain "$PER_DOMAIN" --full $MAXW_ARG \
      --cat-limit "$CAT_LIMIT" --max-tokens "$MAX_TOKENS" || { echo "!! fetch $culture failed"; exit 1; }
  done
fi

# --- run the multi-round FedAvg aggregation (resumable via OUT/rounds/) ----------
echo "== aggregation-survival ($MODEL, $DTYPE, cuda) cultures=$CULTURES rounds=$ROUNDS epochs=$EPOCHS =="
python "$CC/run_aggregation.py" \
  --mode hf --model-name "$MODEL" \
  --cultures "$CULTURES" \
  --corpus-path "$CC/data" \
  --device cuda --dtype "$DTYPE" \
  --rounds "$ROUNDS" --epochs "$EPOCHS" --lr "$LR" \
  --instrument-lang "$INSTRUMENT_LANG" \
  --warmup-frac "$WARMUP_FRAC" --max-grad-norm "$MAX_GRAD_NORM" \
  --out "$OUT"

echo "== result =="
cat "$OUT/result.json"
