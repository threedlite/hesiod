#!/usr/bin/env python3
"""Phase 1 steps 2-3: decode usable clips to 22.05 kHz mono 16-bit WAV, trim, normalize.

Reads data/iliad/metadata.csv (status == ok). Writes data/iliad/wavs/<id>.wav and
data/iliad/trim_log.csv (id, in_dur, start, end, out_dur, rule, gain_db, peak_dbfs).

Trim rule:
  start = first 20 ms frame above SPEECH_DB, minus MARGIN, clamped at 0
  end   = last frame above END_DB, plus END_MARGIN, clamped at the clip end.
The recordings are noise-gated (mid-line pauses are digital silence), so a
silence-gap rule cuts inside lines; the last-real-sound rule is the safe one.
Normalization: RMS over speech frames to TARGET_RMS_DB, then limit peak to PEAK_DB.
"""
import csv, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/iliad"
OUT = D / "wavs"
SR = 22050
FRAME = 0.02
SPEECH_DB = -40.0   # first frame above this starts the clip
END_DB = -35.0      # last frame above this ends the clip (tail bumps from breath/room sit at -36..-50)
MARGIN = 0.10
END_MARGIN = 0.15
TARGET_RMS_DB, PEAK_DB = -20.0, -1.0

def decode(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    return np.frombuffer(pcm[: len(pcm) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768.0

def envelope(x):
    n = int(SR * FRAME); m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    rms = np.sqrt((fr ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))

def find_end(env):
    """Last frame above END_DB. The recordings are noise-gated, so mid-line pauses are digital
    silence and cannot mark the line end; the only safe rule is the last real sound."""
    idx = np.where(env > END_DB)[0]
    return idx[-1], "last_above_end_db"

def process(row):
    x = decode(ROOT / row["wav"])
    env = envelope(x)
    speech = np.where(env > SPEECH_DB)[0]
    if len(speech) == 0:
        return dict(id=row["id"], in_dur=len(x) / SR, start="", end="", out_dur=0, rule="no_speech", end_at_m40="", gain_db="", peak_dbfs="")
    first = speech[0]
    last, rule = find_end(env)
    last40 = speech[-1]
    start = max(0.0, first * FRAME - MARGIN)
    end = min(len(x) / SR, (last + 1) * FRAME + END_MARGIN)
    y = x[int(start * SR): int(end * SR)]
    sp = env[first: last + 1]; sp = sp[sp > SPEECH_DB]
    rms_db = 10 * np.log10(np.mean(10 ** (sp / 10)))
    gain = TARGET_RMS_DB - rms_db
    peak = np.max(np.abs(y)) * 10 ** (gain / 20)
    peak_lim = 10 ** (PEAK_DB / 20)
    if peak > peak_lim: gain -= 20 * np.log10(peak / peak_lim)
    y = np.clip(y * 10 ** (gain / 20), -1, 1)
    with wave.open(str(OUT / f"{row['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return dict(id=row["id"], in_dur=f"{len(x)/SR:.3f}", start=f"{start:.3f}", end=f"{end:.3f}", out_dur=f"{len(y)/SR:.3f}",
                rule=rule, end_at_m40=f"{min(len(x)/SR,(last40+1)*FRAME+END_MARGIN):.3f}", gain_db=f"{gain:.2f}", peak_dbfs=f"{20*np.log10(max(np.max(np.abs(y)),1e-9)):.2f}")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader((D / "metadata.csv").open()) if r["status"] == "ok"]
    with ThreadPoolExecutor(8) as ex:
        log = list(ex.map(process, rows))
    with (D / "trim_log.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0].keys())); w.writeheader(); w.writerows(log)
    from collections import Counter
    durs = np.array([float(r["out_dur"]) for r in log if r["out_dur"]])
    print(f"wrote {len(log)} wavs; rules {Counter(r['rule'] for r in log)}", file=sys.stderr)
    print(f"out_dur: min {durs.min():.2f} p5 {np.percentile(durs,5):.2f} med {np.median(durs):.2f} p95 {np.percentile(durs,95):.2f} max {durs.max():.2f}  total {durs.sum()/3600:.2f} h", file=sys.stderr)

if __name__ == "__main__":
    main()
