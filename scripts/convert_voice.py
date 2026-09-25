#!/usr/bin/env python3
"""Phase 8: male -> female voice conversion of finished audio with the WORLD vocoder (pyworld).

Per line: harvest+stonemask F0, CheapTrick envelope, D4C aperiodicity; then
  F0        x 2^(semitones/12)                      (accent intervals preserved exactly)
  envelope  frequency-axis warp: two-band alpha (a1 below 1 kHz, a2 above 1.5 kHz, blended),
            spectral tilt -k dB/octave above 300 Hz, +boost dB around the new F0 (H1), shelf -2 dB above 6 kHz
  aperiod.  +breath everywhere, +2*breath above 3 kHz, clipped to [0, 1]
  timing    unchanged; output RMS matched to the input's.
Usage:
  python scripts/convert_voice.py --in data/synth/hesiod_fs2_full/wav --out data/synth/hesiod_fs2_full_female/wav \\
         --semitones 7.5 --alpha1 1.22 --alpha2 1.16 --tilt 1.5 --h1 2.5 --breath 0.04 [--ids a,b] [--jobs 8]
"""
import argparse, sys, wave
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pyworld as pw

def load_wav(p):
    with wave.open(str(p)) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x, sr

def save_wav(p, x, sr):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def alpha_curve(freqs, a1, a2, lo=1000.0, hi=1500.0):
    t = np.clip((freqs - lo) / (hi - lo), 0, 1)
    return a1 * (1 - t) + a2 * t

def warp_envelope(sp, sr, a1, a2):
    """sp: (T, K) power envelope. Returns envelope with formants moved up by alpha(f)."""
    K = sp.shape[1]; freqs = np.linspace(0, sr / 2, K)
    src = freqs / alpha_curve(freqs, a1, a2)                    # where each target bin reads from
    logsp = np.log(sp + 1e-12)
    out = np.empty_like(logsp)
    for t in range(sp.shape[0]):
        out[t] = np.interp(src, freqs, logsp[t])
    return np.exp(out)

def tilt_and_shelf(sp, sr, tilt_db_oct, shelf_db=2.0, shelf_hz=6000.0, ref_hz=300.0):
    K = sp.shape[1]; freqs = np.linspace(0, sr / 2, K)
    gain_db = np.zeros(K)
    above = freqs > ref_hz
    gain_db[above] -= tilt_db_oct * np.log2(freqs[above] / ref_hz)
    gain_db[freqs > shelf_hz] -= shelf_db * np.clip((freqs[freqs > shelf_hz] - shelf_hz) / 2000.0, 0, 1)
    return sp * (10 ** (gain_db / 10))[None, :]

def h1_boost(sp, f0, sr, boost_db):
    if boost_db <= 0: return sp
    K = sp.shape[1]; freqs = np.linspace(0, sr / 2, K); out = sp.copy()
    for t in range(sp.shape[0]):
        if f0[t] > 0:
            band = (freqs > 0.7 * f0[t]) & (freqs < 1.3 * f0[t])
            out[t, band] *= 10 ** (boost_db / 10)
    return out

def convert(x, sr, semitones, alpha1, alpha2, tilt, h1, breath):
    f0, t = pw.harvest(x, sr, f0_floor=60.0, f0_ceil=400.0); f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    f0n = f0 * (2 ** (semitones / 12.0))
    spn = warp_envelope(sp, sr, alpha1, alpha2)
    spn = tilt_and_shelf(spn, sr, tilt)
    spn = h1_boost(spn, f0n, sr, h1)
    K = ap.shape[1]; freqs = np.linspace(0, sr / 2, K)
    apn = ap + breath + np.where(freqs > 3000, 2 * breath, 0.0)[None, :]
    apn = np.clip(apn, 0.0, 1.0)
    y = pw.synthesize(f0n, spn, apn, sr)
    rms_in, rms_out = np.sqrt(np.mean(x ** 2)) + 1e-9, np.sqrt(np.mean(y ** 2)) + 1e-9
    y = y * (rms_in / rms_out)
    peak = np.max(np.abs(y))
    if peak > 0.98: y = y * (0.98 / peak)
    return y, dict(f0_median_in=float(np.median(f0[f0 > 0])) if (f0 > 0).any() else 0.0,
                   f0_median_out=float(np.median(f0n[f0n > 0])) if (f0n > 0).any() else 0.0,
                   unvoiced_frac=float(np.mean(f0 == 0)))

def _job(args):
    src, dst, params = args
    try:
        x, sr = load_wav(src); y, info = convert(x, sr, **params); save_wav(dst, y, sr); return (src.stem, "ok", info)
    except Exception as e:
        return (src.stem, f"error: {e!r}", {})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", required=True); ap.add_argument("--ids")
    ap.add_argument("--semitones", type=float, default=7.5); ap.add_argument("--alpha1", type=float, default=1.22); ap.add_argument("--alpha2", type=float, default=1.16)
    ap.add_argument("--tilt", type=float, default=1.5); ap.add_argument("--h1", type=float, default=2.5); ap.add_argument("--breath", type=float, default=0.04)
    ap.add_argument("--jobs", type=int, default=8); a = ap.parse_args()
    inp, out = Path(a.inp), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    files = sorted(inp.glob("*.wav"))
    if a.ids: want = set(a.ids.split(",")); files = [f for f in files if f.stem in want]
    params = dict(semitones=a.semitones, alpha1=a.alpha1, alpha2=a.alpha2, tilt=a.tilt, h1=a.h1, breath=a.breath)
    with Pool(a.jobs) as pool: res = list(pool.imap_unordered(_job, [(f, out / f.name, params) for f in files], chunksize=4))
    ok = [r for r in res if r[1] == "ok"]; bad = [r for r in res if r[1] != "ok"]
    if ok:
        print(f"converted {len(ok)} -> {out}; F0 median in {np.median([r[2]['f0_median_in'] for r in ok]):.0f} Hz, out {np.median([r[2]['f0_median_out'] for r in ok]):.0f} Hz; unvoiced {100*np.mean([r[2]['unvoiced_frac'] for r in ok]):.1f} %")
    for r in bad[:5]: print("  ", r[:2])

if __name__ == "__main__":
    main()
