#!/usr/bin/env bash
# Fetch the audio packages and the models from the GitHub release and put them where the
# repository expects them (audio and model weights are not in git):
#   data/synth/<corpus>_fs2_full/<corpus>_chamberlain_tts_female.zip   the Classics Viewer package per corpus
#   train/runs/fs2_full/{best.pt,config.json}                           the acoustic model (fs2_full_model.tar.gz, unpacked)
#   train/checkpoints/phone_ctc.pt                                      the phone recognizer
#   align/chamberlain_acoustic.zip                                      the forced-alignment acoustic model
#
#   bash scripts/fetch_release.sh hesiod hymns     # named corpora
#   bash scripts/fetch_release.sh models           # the three model files
#   bash scripts/fetch_release.sh all              # everything: 19 files, 4.3 GB
#   bash scripts/fetch_release.sh --list
#
# Every file is checked against the release's SHA256SUMS.txt before it is put in place. Idempotent:
# anything already in place is skipped (pass --verify to re-check existing files against the checksums).
# HESIOD_RELEASE (default v1.0) and HESIOD_RELEASE_REPO (default threedlite/hesiod) select the release;
# HESIOD_RELEASE_DEST (default: the repository) selects the root the paths above are relative to.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HESIOD_RELEASE_DEST:-$ROOT}"
REPO="${HESIOD_RELEASE_REPO:-threedlite/hesiod}"
TAG="${HESIOD_RELEASE:-v1.0}"
BASE="https://github.com/$REPO/releases/download/$TAG"
CORPORA="hesiod hymns colluthus tryphiodorus bion moschus callimachus aratus theocritus oppian_apamea oppian apollonius quintus homer nonnus"
MODELS="fs2_full_model.tar.gz phone_ctc.pt chamberlain_acoustic.zip"

usage() {
  echo "usage: bash scripts/fetch_release.sh <corpus>... | models | all | --list [--verify]"
  echo
  echo "corpora (each fetches <corpus>_chamberlain_tts_female.zip):"
  echo "  $CORPORA"
  echo "models: $MODELS"
}

# asset name -> where it goes (a file path, or a directory for the tarball)
target_of() {
  case "$1" in
    fs2_full_model.tar.gz) echo "$DEST/train/runs/fs2_full" ;;
    phone_ctc.pt)          echo "$DEST/train/checkpoints/phone_ctc.pt" ;;
    chamberlain_acoustic.zip) echo "$DEST/align/chamberlain_acoustic.zip" ;;
    *_chamberlain_tts_female.zip) local c="${1%%_chamberlain_tts_female.zip}"; echo "$DEST/data/synth/${c}_fs2_full/$1" ;;
  esac
}

in_place() {   # 0 if the asset is already where it belongs
  local asset="$1" t; t="$(target_of "$asset")"
  if [ "$asset" = fs2_full_model.tar.gz ]; then [ -f "$t/best.pt" ] && [ -f "$t/config.json" ]; else [ -f "$t" ]; fi
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

TMP=""; cleanup() { [ -n "$TMP" ] && rm -rf "$TMP"; return 0; }; trap cleanup EXIT

fetch_one() {
  local asset="$1" target expected actual tmpfile
  target="$(target_of "$asset")"
  if in_place "$asset" && [ "$VERIFY" -eq 0 ]; then echo "  skip  $asset (in place)"; return 0; fi
  expected="$(awk -v f="$asset" '$2 == f { print $1 }' "$TMP/SHA256SUMS.txt")"
  if [ -z "$expected" ]; then echo "  ERROR $asset is not in the release's SHA256SUMS.txt" >&2; return 1; fi
  if in_place "$asset" && [ "$asset" != fs2_full_model.tar.gz ]; then
    actual="$(sha256_of "$target")"
    if [ "$actual" = "$expected" ]; then echo "  ok    $asset (in place, checksum verified)"; return 0; fi
    echo "  WARN  $asset in place but checksum differs; re-fetching" >&2
  fi
  tmpfile="$TMP/$asset"
  echo "  fetch $asset"
  if ! curl -fL --retry 3 --progress-bar -o "$tmpfile" "$BASE/$asset"; then echo "  ERROR download failed: $BASE/$asset" >&2; rm -f "$tmpfile"; return 1; fi
  actual="$(sha256_of "$tmpfile")"
  if [ "$actual" != "$expected" ]; then echo "  ERROR checksum mismatch for $asset (expected $expected, got $actual)" >&2; rm -f "$tmpfile"; return 1; fi
  if [ "$asset" = fs2_full_model.tar.gz ]; then
    mkdir -p "$target" && tar -xzf "$tmpfile" -C "$target" || return 1
    echo "  ok    $asset -> $target/{best.pt,config.json} (checksum verified)"
  else
    mkdir -p "$(dirname "$target")" && mv "$tmpfile" "$target" || return 1
    echo "  ok    $asset -> $target (checksum verified)"
  fi
}

[ "$#" -eq 0 ] && { usage; exit 1; }
ASSETS=""; VERIFY=0
for arg in "$@"; do
  case "$arg" in
    -h|--help|--list) usage; exit 0 ;;
    --verify) VERIFY=1 ;;
    all) for c in $CORPORA; do ASSETS="$ASSETS ${c}_chamberlain_tts_female.zip"; done; ASSETS="$ASSETS $MODELS" ;;
    models) ASSETS="$ASSETS $MODELS" ;;
    *) if echo " $CORPORA " | grep -q " $arg "; then ASSETS="$ASSETS ${arg}_chamberlain_tts_female.zip"
       elif echo " $MODELS " | grep -q " $arg "; then ASSETS="$ASSETS $arg"
       else echo "unknown corpus or asset: $arg" >&2; echo >&2; usage >&2; exit 1; fi ;;
  esac
done
[ -z "$ASSETS" ] && { usage; exit 1; }
for tool in curl tar; do command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: $tool is required" >&2; exit 1; }; done

TMP="$(mktemp -d)"
echo "==> $REPO release $TAG -> $DEST"
curl -fsSL --retry 3 -o "$TMP/SHA256SUMS.txt" "$BASE/SHA256SUMS.txt" || { echo "ERROR: could not fetch $BASE/SHA256SUMS.txt" >&2; exit 1; }
failed=0
for a in $ASSETS; do fetch_one "$a" || failed=1; done
echo
if [ "$failed" -ne 0 ]; then echo "some files failed; fix the errors above and re-run (finished ones are skipped)." >&2; exit 1; fi
echo "done. Packages import into Classics Viewer through Settings -> Manage Audio; the models are where train/fs2.py, train/recognize.py and align/run_align.sh look for them."
