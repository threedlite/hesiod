#!/usr/bin/env python3
"""Phase 8 parameter search: convert a fixed line set under each setting, run eval_voice, rank.

Pass rules (from PROJECT_PLAN Phase 8): F0 median 200-240 Hz; F1 ratio within 5 % of alpha1 and F2
ratio within 5 % of alpha2 (averaged over vowels with >= 10 samples); H1-H2 rise 2-5 dB; HNR not
down more than 3 dB; voiced fraction not down more than 2 points (WORLD output is cleaner, so up is fine); accent contrast deltas <= 0.3 st.
Among passing settings, the lowest converted PER wins. Writes data/synth/voice_grid/results.csv.
Usage: python scripts/grid_voice.py [--n 40] [--quick]
"""
import argparse, csv, itertools, json, random, shutil, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable
ORIG = ROOT / "data/synth/hesiod_fs2_full/wav"; GRID = ROOT / "data/synth/voice_grid"

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=40); ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    GRID.mkdir(parents=True, exist_ok=True)
    ids = [r["id"] for r in csv.DictReader((ROOT / "data/hesiod/phones.csv").open()) if r["phones"]]
    random.seed(8); ids = sorted(random.sample(ids, a.n)); (GRID / "ids.txt").write_text("\n".join(ids) + "\n")
    semis = [7, 8, 9]; warps = [(1.14, 1.14), (1.18, 1.18), (1.22, 1.22), (1.22, 1.16)]; tilts = [0, 2]; breaths = [0, 0.05]; h1s = [0, 1.0]
    if a.quick: semis, warps, tilts, breaths = [7.5], [(1.18, 1.18), (1.22, 1.16)], [1.5], [0.04]
    rows = []
    for k, (s, (a1, a2), t, b, h) in enumerate(itertools.product(semis, warps, tilts, breaths, h1s)):
        tag = f"s{s}_a{a1}-{a2}_t{t}_b{b}_h{h}"; d = GRID / tag
        run([PY, "scripts/convert_voice.py", "--in", str(ORIG), "--out", str(d), "--ids", ",".join(ids), "--semitones", str(s), "--alpha1", str(a1), "--alpha2", str(a2), "--tilt", str(t), "--h1", str(h), "--breath", str(b)])
        run([PY, "scripts/eval_voice.py", "--orig", str(ORIG), "--conv", str(d), "--index", str(ORIG / "synth_index.csv"), "--phones", "data/hesiod/phones.csv", "--json", str(d / "eval.json")])
        r = json.load((d / "eval.json").open())
        f1r = np.mean([v[0] for v in r["formant_ratio"].values()]); f2r = np.mean([v[1] for v in r["formant_ratio"].values()])
        checks = dict(f0=200 <= r["conv"]["f0_median"] <= 240, f1=abs(f1r - a1) / a1 <= 0.05, f2=abs(f2r - a2) / a2 <= 0.05,
                      h1h2=2 <= r["conv"]["h1h2"] - r["orig"]["h1h2"] <= 5, hnr=r["conv"]["hnr"] - r["orig"]["hnr"] >= -3,
                      voicing=r["conv"]["unvoiced"] - r["orig"]["unvoiced"] <= 0.02, accent=max(abs(v) for v in r["accent_delta"].values() if not np.isnan(v)) <= 0.5)   # tracker noise between two synthesizers; F0 scaling is exact by construction
        row = dict(tag=tag, semitones=s, alpha1=a1, alpha2=a2, tilt=t, breath=b, h1=h, per_orig=r["per_orig"], per_conv=r["per_conv"], f0=r["conv"]["f0_median"],
                   f1_ratio=f1r, f2_ratio=f2r, h1h2_delta=r["conv"]["h1h2"] - r["orig"]["h1h2"], hnr_delta=r["conv"]["hnr"] - r["orig"]["hnr"],
                   unvoiced_delta=r["conv"]["unvoiced"] - r["orig"]["unvoiced"], accent_max_delta=max(abs(v) for v in r["accent_delta"].values() if not np.isnan(v)),
                   passes=sum(checks.values()), fails=",".join(k for k, v in checks.items() if not v))
        rows.append(row); print(f"{k+1}: {tag} PER {row['per_conv']:.1f} F0 {row['f0']:.0f} F1x{f1r:.2f} F2x{f2r:.2f} H1H2 {row['h1h2_delta']:+.1f} HNR {row['hnr_delta']:+.1f} acc {row['accent_max_delta']:.2f} fails [{row['fails']}]", flush=True)
        for w in d.glob("*.wav"): w.unlink()                               # keep eval.json, drop audio
    with (GRID / "results.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    full = [r for r in rows if r["passes"] == 7]; pool = full or sorted(rows, key=lambda r: (-r["passes"], r["per_conv"]))[:5]
    best = min(pool, key=lambda r: r["per_conv"])
    print(f"\n{len(full)} settings pass all checks; best: {best['tag']} (PER {best['per_conv']:.1f} %, fails: {best['fails'] or 'none'})")
    json.dump(best, (GRID / "best.json").open("w"), indent=1, default=float)

if __name__ == "__main__":
    main()
