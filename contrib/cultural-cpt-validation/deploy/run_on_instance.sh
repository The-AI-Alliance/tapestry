#!/usr/bin/env bash
# Run the real EXP-001 Egypt CPT experiment ON a GPU instance.
#
# Assumes: this repo is present at $REPO (default /workspace/tapestry), the
# instance has a CUDA 12.8+ / PyTorch >= 2.7 stack that supports the RTX 5090
# (Blackwell, sm_120), and network access (to fetch the model + regenerate the
# corpus from the committed titles file). Idempotent enough to re-run.
#
# Override via env: MODEL, EPOCHS, PER_DOMAIN, SEED, DTYPE, CULTURE, LR.
set -euo pipefail

REPO="${REPO:-/workspace/tapestry}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
CULTURE="${CULTURE:-egypt}"
LANG_CODE="${LANG_CODE:-ar}"
EPOCHS="${EPOCHS:-2}"
PER_DOMAIN="${PER_DOMAIN:-6}"
SEED="${SEED:-0}"
DTYPE="${DTYPE:-bfloat16}"
LR="${LR:-2e-5}"

CC="$REPO/contrib/cultural-cpt-validation"
export PYTHONPATH="$REPO/src:$CC"

echo "== environment =="
python -c "import torch; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
python -c "import transformers; print('transformers', transformers.__version__)" || pip install -q transformers

echo "== regenerate the $CULTURE corpus from the committed titles file =="
python "$CC/fetch_corpus.py" \
  --culture "$CULTURE" --lang "$LANG_CODE" \
  --titles-file "$CC/titles/${CULTURE}.${LANG_CODE}.json" \
  --per-domain "$PER_DOMAIN" --full

echo "== run the real CPT experiment ($MODEL, $DTYPE, cuda) =="
python "$CC/run.py" \
  --mode hf --model-name "$MODEL" \
  --culture "$CULTURE" \
  --corpus-path "$CC/data/$CULTURE" \
  --device cuda --dtype "$DTYPE" \
  --epochs "$EPOCHS" --lr "$LR" --seed "$SEED" \
  --out "$REPO/runs/${CULTURE}_real"

echo "== result =="
cat "$REPO/runs/${CULTURE}_real/result.json"
