#!/bin/bash
# Phase 10: run the finished pipeline on one or more corpora (scripts/corpora.py), end to end:
#   synthesis + QC + package (male voice), lettered variant if the corpus has lettered lines,
#   WORLD conversion to the female voice with the Phase 8 setting, its packages, and the Phase 8 checks
#   (on a 600-line sample for corpora above 3,000 lines).
# The text tables (parse/scan/render, system Python) must exist already. Logs: data/synth/<corpus>_fs2_full/pipeline.log.
# Usage: nohup bash scripts/run_corpora.sh colluthus tryphiodorus ... > data/synth/batch.log 2>&1 &
set -uo pipefail
cd "$(dirname "$0")/.."
PY=/opt/homebrew/Caskroom/miniforge/base/envs/tts/bin/python
CKPT=train/runs/fs2_full/best.pt
FEMALE="--semitones 7 --alpha1 1.14 --alpha2 1.14 --tilt 0 --h1 0 --breath 0"
for c in "$@"; do
  out=data/synth/${c}_fs2_full; fem=data/synth/${c}_fs2_full_female; mkdir -p "$out" "$fem"; log=$out/pipeline.log
  echo "== $c start $(date)" | tee -a "$log"
  {
    $PY scripts/synth_hesiod.py --corpus "$c" --ckpt $CKPT --package || exit 1
    if python3 -c "import csv,sys; sys.exit(0 if any(not r['n'].isdigit() for r in csv.DictReader(open('data/$c/lines.csv'))) else 1)"; then
      $PY scripts/synth_hesiod.py --corpus "$c" --ckpt $CKPT --package-only --lettered || exit 1; LETTERED=1
    else LETTERED=0; fi
    $PY scripts/convert_voice.py --in "$out/wav" --out "$fem/wav" $FEMALE --jobs 8 || exit 1
    $PY scripts/synth_hesiod.py --corpus "$c" --ckpt $CKPT --package-only --wav-dir "$fem/wav" --package-name "${c}_chamberlain_tts_female" || exit 1
    if [ "$LETTERED" = 1 ]; then $PY scripts/synth_hesiod.py --corpus "$c" --ckpt $CKPT --package-only --wav-dir "$fem/wav" --package-name "${c}_chamberlain_tts_female" --lettered || exit 1; fi
    IDS=$(python3 -c "import csv,random; ids=[r['id'] for r in csv.DictReader(open('data/$c/phones.csv')) if r['phones']]; random.seed(20260925); print(','.join(sorted(random.sample(ids, 600))) if len(ids) > 3000 else '')")
    $PY scripts/eval_voice.py --orig "$out/wav" --conv "$fem/wav" --index "$out/wav/synth_index.csv" --phones "data/$c/phones.csv" --json "$fem/eval_full.json" ${IDS:+--ids $IDS} || exit 1
  } 2>&1 | grep -v "pkg_resources\|UserWarning\|state_dict = torch.load" >> "$log"
  rc=${PIPESTATUS[0]}
  echo "== $c end rc=$rc $(date)" | tee -a "$log"
  [ "$rc" != 0 ] && echo "FAILED $c" >> data/synth/batch_failures.log
done
echo "== batch done $(date)"
