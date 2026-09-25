#!/bin/bash
# Phase 3: validate, train an acoustic model from scratch, and align the corpus.
# Usage: bash align/run_align.sh [validate|train|align|all]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENVBIN=/opt/homebrew/Caskroom/miniforge/base/envs/aligner/bin
export PATH="$ENVBIN:$PATH"
MFA=$ENVBIN/mfa
export MFA_ROOT_DIR="$ROOT/align/mfa_root"
CORPUS="$ROOT/align/corpus"
DICT="$ROOT/align/dictionary.txt"
MODEL="$ROOT/align/chamberlain_acoustic.zip"
OUT="$ROOT/align/textgrids"
JOBS=8
mkdir -p "$MFA_ROOT_DIR" "$OUT"
step="${1:-all}"
if [[ "$step" == "validate" || "$step" == "all" ]]; then
  $MFA validate "$CORPUS" "$DICT" --clean --num_jobs $JOBS --ignore_acoustics 2>&1 | tee "$ROOT/align/validate.log"
fi
if [[ "$step" == "train" || "$step" == "all" ]]; then
  $MFA train "$CORPUS" "$DICT" "$MODEL" --output_directory "$OUT" --clean --num_jobs $JOBS --single_speaker \
      --output_format long_textgrid 2>&1 | tee "$ROOT/align/train.log"
fi
if [[ "$step" == "align" ]]; then
  $MFA align "$CORPUS" "$DICT" "$MODEL" "$OUT" --clean --num_jobs $JOBS --single_speaker --output_analysis --output_format long_textgrid 2>&1 | tee "$ROOT/align/align.log"
fi
echo "done: $step"
