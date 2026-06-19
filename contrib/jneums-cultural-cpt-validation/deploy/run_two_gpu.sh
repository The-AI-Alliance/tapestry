#!/usr/bin/env bash
# Run TWO EXP-001 go/no-go experiments in parallel, one per GPU, on a 2× RTX 5090
# box (the machine's 2× offer). The two answer different questions but share one
# corpus, so we fetch once and split the GPUs:
#
#   GPU 0  ->  MODEL_A (instruct) + the neutral_prose register twin
#              => grounded - neutral_prose: is the grounding effect genre or culture?
#   GPU 1  ->  MODEL_B (base) + the same arms
#              => value-pull with no RLHF alignment to erode (de-confounds the drift)
#
# Each GPU runs its seeds as ISOLATED single-seed processes (a preemption only costs
# the in-flight seed; the harness checkpoints per seed) and re-aggregates offline with
# re_aggregate.py. Pinning is via CUDA_VISIBLE_DEVICES, so each process sees its GPU as
# cuda:0 and loads one ~4B model (~25 GB) with no cross-GPU contention.
#
# The box is INTERRUPTIBLE on purpose (it's our own machine on Vast.ai, so free); a
# paying renter preempting it is fine. If preempted, restart and re-run — completed
# seeds survive on disk and re-aggregation is offline/CPU.
#
# Override via env: MODEL_A, MODEL_B, SEEDS, EPOCHS, PER_DOMAIN, MAX_WORDS, CAT_LIMIT,
# MAX_TOKENS, DTYPE, INSTRUMENT_LANG, BEHAVIOR_MODE, LR, WARMUP_FRAC, MAX_GRAD_NORM,
# REPLAY_FRACTION, CULTURE, LANG_CODE, FETCH (0 to reuse an existing corpus), MODE
# (smoke to dry-run the orchestration without a GPU), OUT_A, OUT_B.
set -uo pipefail

REPO="${REPO:-/workspace/tapestry}"
MODE="${MODE:-hf}"
MODEL_A="${MODEL_A:-Qwen/Qwen3-4B-Instruct-2507}"  # GPU 0: register test (instruct)
MODEL_B="${MODEL_B:-Qwen/Qwen3-4B-Base}"           # GPU 1: base-model de-confound
CULTURE="${CULTURE:-egypt}"
LANG_CODE="${LANG_CODE:-ar}"
SEEDS="${SEEDS:-0,1,2}"
EPOCHS="${EPOCHS:-6}"
PER_DOMAIN="${PER_DOMAIN:-18}"
MAX_WORDS="${MAX_WORDS:-4000}"
CAT_LIMIT="${CAT_LIMIT:-25}"
MAX_TOKENS="${MAX_TOKENS:-800000}"
DTYPE="${DTYPE:-bfloat16}"
INSTRUMENT_LANG="${INSTRUMENT_LANG:-ar}"
BEHAVIOR_MODE="${BEHAVIOR_MODE:-generate}"
LR="${LR:-2e-5}"
# Run 9 stabilization (keep a seed from cratering). Replay is off by default — the
# register/base questions are orthogonal to forgetting mitigation.
WARMUP_FRAC="${WARMUP_FRAC:-0.05}"
MAX_GRAD_NORM="${MAX_GRAD_NORM:-1.0}"
REPLAY_FRACTION="${REPLAY_FRACTION:-0.0}"
# Corpus resampling: with CORPUS_DRAWS>1 each lane decides on the *cross-corpus*
# noise band (the real one — see FINDINGS Run 7) instead of running per-seed
# isolated processes. The resample path checkpoints+resumes per draw (draws/draw_<d>.json),
# so a preempted lane re-run skips finished draws. CORPUS_FRACTION must be <1.0.
CORPUS_DRAWS="${CORPUS_DRAWS:-1}"
CORPUS_FRACTION="${CORPUS_FRACTION:-1.0}"
FETCH="${FETCH:-1}"
OUT_A="${OUT_A:-$REPO/runs/${CULTURE}_register_instruct}"
OUT_B="${OUT_B:-$REPO/runs/${CULTURE}_register_base}"

CC="$REPO/contrib/jneums-cultural-cpt-validation"
export PYTHONPATH="$REPO/src:$CC"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if [ "$MODE" = "hf" ]; then
  echo "== environment =="
  python -c "import torch; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '| gpus', torch.cuda.device_count())"
  python -c "import transformers" 2>/dev/null || pip install -q transformers
  python -c "import bitsandbytes" 2>/dev/null || pip install -q bitsandbytes
  if [ "$BEHAVIOR_MODE" = "generate" ]; then
    python -c "import sentence_transformers" 2>/dev/null || pip install -q sentence-transformers
  fi
fi

# --- corpus: fetch ONCE, shared by both GPUs (includes the neutral_prose twin) ----
REPLAY_ON=0
case "$REPLAY_FRACTION" in 0 | 0.0 | 0.00 | "") REPLAY_ON=0 ;; *) REPLAY_ON=1 ;; esac
RP_BUILD=""
[ "$REPLAY_ON" = "1" ] && RP_BUILD="--replay"
MAXW_ARG=""
[ "$MAX_WORDS" != "0" ] && MAXW_ARG="--max-words $MAX_WORDS"

if [ "$FETCH" = "1" ] && [ "$MODE" = "hf" ]; then
  echo "== fetch corpus once (with the neutral_prose register twin) =="
  python "$CC/fetch_corpus.py" \
    --culture "$CULTURE" --lang "$LANG_CODE" \
    --titles-file "$CC/titles/${CULTURE}.${LANG_CODE}.json" \
    --per-domain "$PER_DOMAIN" --full $MAXW_ARG \
    --cat-limit "$CAT_LIMIT" --max-tokens "$MAX_TOKENS" \
    --neutral-prose $RP_BUILD
fi

# Stabilization args passed to every run.
STAB_ARGS="--warmup-frac $WARMUP_FRAC"
[ -n "$MAX_GRAD_NORM" ] && STAB_ARGS="$STAB_ARGS --max-grad-norm $MAX_GRAD_NORM"
[ "$REPLAY_ON" = "1" ] && STAB_ARGS="$STAB_ARGS --replay-fraction $REPLAY_FRACTION"

CORPUS_ARG=""
[ "$MODE" = "hf" ] && CORPUS_ARG="--corpus-path $CC/data/$CULTURE"
DEVICE="cpu"
[ "$MODE" = "hf" ] && DEVICE="cuda"

# Run one model on one GPU: each seed is its own process (survives preemption), then
# re-aggregate whatever seeds completed. Pinned with CUDA_VISIBLE_DEVICES.
run_on_gpu() {
  local gpu="$1" model="$2" out="$3" tag="$4"
  mkdir -p "$out"

  # Resample mode: one process runs all seeds × all draws and decides on the
  # cross-corpus band. The draw cache makes it resumable, so per-seed isolation is
  # unnecessary — just re-run this same command after a preemption.
  if [ "$CORPUS_DRAWS" -gt 1 ]; then
    echo "[$tag gpu$gpu] resample sweep: draws=$CORPUS_DRAWS frac=$CORPUS_FRACTION seeds=$SEEDS start $(date -u)"
    CUDA_VISIBLE_DEVICES="$gpu" python "$CC/run_stats.py" \
      --mode "$MODE" --model-name "$model" --culture "$CULTURE" \
      $CORPUS_ARG --device "$DEVICE" --dtype "$DTYPE" \
      --epochs "$EPOCHS" --lr "$LR" --seeds "$SEEDS" \
      --corpus-draws "$CORPUS_DRAWS" --corpus-fraction "$CORPUS_FRACTION" \
      --instrument-lang "$INSTRUMENT_LANG" --behavior-mode "$BEHAVIOR_MODE" \
      $STAB_ARGS --out "$out" \
      && echo "[$tag gpu$gpu] sweep OK -> $out/result.json $(date -u)" \
      || echo "[$tag gpu$gpu] sweep FAILED rc=$? (re-run to resume from draw cache) $(date -u)"
    echo "[$tag gpu$gpu] all done $(date -u)"
    return
  fi

  local s
  for s in ${SEEDS//,/ }; do
    echo "[$tag gpu$gpu] seed $s start $(date -u)"
    CUDA_VISIBLE_DEVICES="$gpu" python "$CC/run_stats.py" \
      --mode "$MODE" --model-name "$model" --culture "$CULTURE" \
      $CORPUS_ARG --device "$DEVICE" --dtype "$DTYPE" \
      --epochs "$EPOCHS" --lr "$LR" --seeds "$s" \
      --instrument-lang "$INSTRUMENT_LANG" --behavior-mode "$BEHAVIOR_MODE" \
      $STAB_ARGS --out "$out" \
      && echo "[$tag gpu$gpu] seed $s OK $(date -u)" \
      || echo "[$tag gpu$gpu] seed $s FAILED rc=$? $(date -u)"
  done
  python "$CC/re_aggregate.py" --seeds-dir "$out/seeds" --out "$out" \
    && echo "[$tag gpu$gpu] aggregated -> $out/result.json" \
    || echo "[$tag gpu$gpu] re-aggregate found no completed seeds"
  echo "[$tag gpu$gpu] all done $(date -u)"
}

echo "== launch both GPUs in parallel =="
echo "  GPU 0: $MODEL_A (register/instruct) -> $OUT_A"
echo "  GPU 1: $MODEL_B (base de-confound)   -> $OUT_B"
# Create the out dirs (and their runs/ parent) BEFORE the redirected launches —
# the shell opens "${OUT_*}.log" before run_on_gpu's own mkdir runs.
mkdir -p "$OUT_A" "$OUT_B"
run_on_gpu 0 "$MODEL_A" "$OUT_A" instruct >"${OUT_A}.log" 2>&1 &
PID_A=$!
run_on_gpu 1 "$MODEL_B" "$OUT_B" base >"${OUT_B}.log" 2>&1 &
PID_B=$!
echo "  instruct pid $PID_A (log ${OUT_A}.log) | base pid $PID_B (log ${OUT_B}.log)"
wait "$PID_A" || true
wait "$PID_B" || true
echo "== both GPUs done =="
echo "  register (instruct): $OUT_A/result.json"
echo "  base de-confound:    $OUT_B/result.json"
