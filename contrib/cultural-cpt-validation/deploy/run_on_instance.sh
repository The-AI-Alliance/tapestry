#!/usr/bin/env bash
# Run the real EXP-001 Egypt CPT experiment ON a GPU instance.
#
# Assumes: this repo is present at $REPO (default /workspace/tapestry), the
# instance has a CUDA 12.8+ / PyTorch >= 2.7 stack that supports the RTX 5090
# (Blackwell, sm_120), and network access (to fetch the model + regenerate the
# corpus from the committed titles file). Idempotent enough to re-run.
#
# Override via env: MODEL, EPOCHS, PER_DOMAIN, SEED, SEEDS, DTYPE, CULTURE, LR,
# REPLAY_FRACTION, WARMUP_FRAC, MAX_GRAD_NORM (Run 8 follow-up: forgetting
# mitigation + training stabilization).
# If SEEDS (comma-separated) is set, runs the multi-seed go/no-go (run_stats.py)
# instead of the single run (run.py).
set -euo pipefail

REPO="${REPO:-/workspace/tapestry}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
CULTURE="${CULTURE:-egypt}"
LANG_CODE="${LANG_CODE:-ar}"
EPOCHS="${EPOCHS:-6}"
PER_DOMAIN="${PER_DOMAIN:-8}"
MAX_WORDS="${MAX_WORDS:-0}"
CAT_LIMIT="${CAT_LIMIT:-0}"
MAX_TOKENS="${MAX_TOKENS:-0}"
SEED="${SEED:-0}"
SEEDS="${SEEDS:-}"
DTYPE="${DTYPE:-bfloat16}"
LR="${LR:-2e-5}"
INSTRUMENT_LANG="${INSTRUMENT_LANG:-en}"
BEHAVIOR_MODE="${BEHAVIOR_MODE:-logprob}"
TRANSLATE="${TRANSLATE:-0}"  # 1 = also build the grounded_translated arm (Arm 3, needs MT)
# Corpus resampling: with CORPUS_DRAWS>1 the go/no-go decides on the cross-corpus
# noise band — re-runs all SEEDS per draw, each on a CORPUS_FRACTION subset of the
# pool. This is the real variance source (Run 5's effect did not survive a fresh
# corpus pull). Cost scales ~linearly with CORPUS_DRAWS.
CORPUS_DRAWS="${CORPUS_DRAWS:-1}"
CORPUS_FRACTION="${CORPUS_FRACTION:-1.0}"
# Run 8 follow-up: replay/anchor forgetting mitigation + training stabilization.
# REPLAY_FRACTION>0 adds the grounded_replay arm (and builds the replay corpus);
# WARMUP_FRAC / MAX_GRAD_NORM stabilize every CPT arm (keep a seed from cratering).
REPLAY_FRACTION="${REPLAY_FRACTION:-0.0}"
WARMUP_FRAC="${WARMUP_FRAC:-0.0}"
MAX_GRAD_NORM="${MAX_GRAD_NORM:-}"

CC="$REPO/contrib/cultural-cpt-validation"
export PYTHONPATH="$REPO/src:$CC"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "== environment =="
python -c "import torch; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
python -c "import transformers; print('transformers', transformers.__version__)" || pip install -q transformers
# 8-bit Adam (bitsandbytes) lets a ~4B full fine-tune fit a single 32GB GPU.
python -c "import bitsandbytes" 2>/dev/null || pip install -q bitsandbytes
# sentence-transformers is the judge for behavior generate mode.
if [ "$BEHAVIOR_MODE" = "generate" ]; then
  python -c "import sentence_transformers" 2>/dev/null || pip install -q sentence-transformers
fi

MAXW_ARG=""
[ "$MAX_WORDS" != "0" ] && MAXW_ARG="--max-words $MAX_WORDS"
TRANSLATE_ARG=""
[ "$TRANSLATE" = "1" ] && TRANSLATE_ARG="--translate"
# Whether the replay arm is wanted: any non-zero REPLAY_FRACTION builds + uses it.
REPLAY_ON=0
case "$REPLAY_FRACTION" in 0|0.0|0.00|"") REPLAY_ON=0 ;; *) REPLAY_ON=1 ;; esac
REPLAY_BUILD_ARG=""
[ "$REPLAY_ON" = "1" ] && REPLAY_BUILD_ARG="--replay"
# Stabilization args, passed through to the run only when set.
STAB_ARGS="--warmup-frac $WARMUP_FRAC"
[ "$REPLAY_ON" = "1" ] && STAB_ARGS="$STAB_ARGS --replay-fraction $REPLAY_FRACTION"
[ -n "$MAX_GRAD_NORM" ] && STAB_ARGS="$STAB_ARGS --max-grad-norm $MAX_GRAD_NORM"
echo "== regenerate the $CULTURE corpus from the committed titles file =="
python "$CC/fetch_corpus.py" \
  --culture "$CULTURE" --lang "$LANG_CODE" \
  --titles-file "$CC/titles/${CULTURE}.${LANG_CODE}.json" \
  --per-domain "$PER_DOMAIN" --full $MAXW_ARG \
  --cat-limit "$CAT_LIMIT" --max-tokens "$MAX_TOKENS" $TRANSLATE_ARG $REPLAY_BUILD_ARG

if [ -n "$SEEDS" ]; then
  OUT="$REPO/runs/${CULTURE}_stats"
  echo "== run the multi-seed go/no-go ($MODEL, $DTYPE, cuda, seeds=$SEEDS) =="
  python "$CC/run_stats.py" \
    --mode hf --model-name "$MODEL" \
    --culture "$CULTURE" \
    --corpus-path "$CC/data/$CULTURE" \
    --device cuda --dtype "$DTYPE" \
    --epochs "$EPOCHS" --lr "$LR" --seeds "$SEEDS" \
    --instrument-lang "$INSTRUMENT_LANG" --behavior-mode "$BEHAVIOR_MODE" \
    --corpus-draws "$CORPUS_DRAWS" --corpus-fraction "$CORPUS_FRACTION" \
    $STAB_ARGS \
    --out "$OUT"
else
  OUT="$REPO/runs/${CULTURE}_real"
  echo "== run the single real CPT experiment ($MODEL, $DTYPE, cuda) =="
  python "$CC/run.py" \
    --mode hf --model-name "$MODEL" \
    --culture "$CULTURE" \
    --corpus-path "$CC/data/$CULTURE" \
    --device cuda --dtype "$DTYPE" \
    --epochs "$EPOCHS" --lr "$LR" --seed "$SEED" \
    --instrument-lang "$INSTRUMENT_LANG" --behavior-mode "$BEHAVIOR_MODE" \
    $STAB_ARGS \
    --out "$OUT"
fi

echo "== result =="
cat "$OUT/result.json"
