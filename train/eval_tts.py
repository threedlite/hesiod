#!/usr/bin/env python3
"""Phase 4 evaluation of a checkpoint, all automatic (see PROJECT_PLAN §4).

  1. synthesize val (prediction), test (prediction) and val (teacher-forced durations/pitch) -> wavs
  2. recognizer PER per set (train/recognize.py)
  3. duration: predicted vowel duration for long vs short syllables vs the real corpus
  4. pitch: predicted per-token log-F0 by accent class (vowel tokens) vs the real corpus
Writes reports/eval_<name>.md and data/synth/<name>/...
Usage: python train/eval_tts.py --ckpt train/runs/fs2_2h/best.pt [--n-val 311]
"""
import argparse, csv, json, subprocess, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable
VOWEL = set("aeiouyɛɔ")

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout

def per(manifest):
    out = run([PY, "train/recognize.py", "--manifest", str(manifest), "--out", str(manifest).replace("manifest", "per")])
    return float(out.strip().splitlines()[-1].split("PER")[1].split("%")[0])

def manifest(ids, wavdir, phones, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "wav", "phones"])
        for i in ids: w.writerow([i, str(Path(wavdir) / f"{i}.wav"), phones[i]["phones"]])

def token_stats(index_csv, phones, stats):
    """From synth_index.csv: per-token predicted durations/F0 grouped by vowel quantity and accent."""
    sys.path.insert(0, str(ROOT / "train")); from prepare_features import tokens_of
    dur_q, f0_acc = defaultdict(list), defaultdict(list)
    for r in csv.DictReader(open(index_csv)):
        toks, _ = tokens_of(phones[r["id"]]); d = list(map(int, r["pred_dur"].split())); f = list(map(float, r["pred_f0"].split()))
        vow = [(t, dd, ff) for t, dd, ff in zip(toks, d, f) if t[0][0] in VOWEL]
        med = np.median([ff for _, _, ff in vow]) if vow else 0
        for (p, q, acc, foot), dd, ff in vow:
            dur_q[{1: "L", 2: "S"}.get(q, "?")].append(dd * 256 / 24000 * 1000)
            f0_acc[{0: "none", 1: "acute", 2: "grave", 3: "circumflex"}[acc]].append(12 * (ff - med) / np.log(2))
    return dur_q, f0_acc

def real_stats(ids):
    dur_q, f0_acc = defaultdict(list), defaultdict(list)
    for i in ids:
        d = np.load(ROOT / "data/features" / f"{i}.npz")
        vow = [(t, q, a, dd, ff) for t, q, a, dd, ff in zip(d["tokens"], d["q"], d["acc"], d["dur"], d["f0"]) if t[0] in VOWEL and ff > 0]
        med = np.median([ff for *_, ff in vow]) if vow else 0
        for t, q, a, dd, ff in vow:
            dur_q[{1: "L", 2: "S"}.get(int(q), "?")].append(dd * 256 / 24000 * 1000)
            f0_acc[{0: "none", 1: "acute", 2: "grave", 3: "circumflex"}[int(a)]].append(12 * (ff - med) / np.log(2))
    return dur_q, f0_acc

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ckpt", required=True); ap.add_argument("--n-val", type=int, default=311); ap.add_argument("--name"); args = ap.parse_args()
    name = args.name or Path(args.ckpt).parent.name; out = ROOT / "data/synth" / name; out.mkdir(parents=True, exist_ok=True)
    phones = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}
    val = [l.strip() for l in (ROOT / "data/iliad/splits/val.txt").open()][:args.n_val]; test = [l.strip() for l in (ROOT / "data/iliad/splits/test.txt").open()]
    (out / "val.txt").write_text("\n".join(val) + "\n"); (out / "test.txt").write_text("\n".join(test) + "\n")
    print(run([PY, "train/fs2.py", "synth", "--ckpt", args.ckpt, "--list", str(out / "val.txt"), "--phones", "data/iliad/phones.csv", "--out", str(out / "val_pred")]).strip().splitlines()[-1])
    print(run([PY, "train/fs2.py", "synth", "--ckpt", args.ckpt, "--list", str(out / "test.txt"), "--phones", "data/iliad/phones.csv", "--out", str(out / "test_pred")]).strip().splitlines()[-1])
    print(run([PY, "train/fs2.py", "synth", "--ckpt", args.ckpt, "--list", str(out / "val.txt"), "--teacher", "--out", str(out / "val_teacher")]).strip().splitlines()[-1])
    res = {}
    for tag, ids in (("val_pred", val), ("test_pred", test), ("val_teacher", val)):
        manifest(ids, out / tag, phones, out / f"{tag}_manifest.csv"); res[tag] = per(out / f"{tag}_manifest.csv"); print(tag, "PER", res[tag])
    real_per = {"val": 3.22, "test": 4.93}
    pd, pf = token_stats(out / "val_pred/synth_index.csv", phones, None); rd, rf = real_stats(val)
    L = ["# TTS evaluation: " + name, "", f"Checkpoint `{args.ckpt}`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.", "",
         "| Set | PER | Pass (≤ 1.5 × real) |", "|---|---|---|",
         f"| val, predicted durations/pitch | {res['val_pred']:.2f} % | {'yes' if res['val_pred'] <= 1.5*3.22 else 'no'} |",
         f"| test (Iliad 1.1–52), predicted | {res['test_pred']:.2f} % | {'yes' if res['test_pred'] <= 1.5*4.93 else 'no'} |",
         f"| val, teacher-forced durations/pitch (copy synthesis) | {res['val_teacher']:.2f} % | {'yes' if res['val_teacher'] <= 1.5*3.22 else 'no'} |", "",
         "## Duration: vowel duration by syllable quantity (ms)", "", "| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |", "|---|---|---|---|---|---|---|---|"]
    rr, pr = np.mean(rd["L"]) / np.mean(rd["S"]), np.mean(pd["L"]) / np.mean(pd["S"])
    L.append(f"| val | {np.mean(rd['L']):.0f} | {np.mean(rd['S']):.0f} | {rr:.2f} | {np.mean(pd['L']):.0f} | {np.mean(pd['S']):.0f} | {pr:.2f} | {'yes' if abs(pr-rr)/rr <= 0.1 else 'no'} |")
    L += ["", "## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median", "", "| Accent | real | predicted | diff |", "|---|---|---|---|"]
    for a in ("acute", "circumflex", "grave", "none"):
        L.append(f"| {a} | {np.mean(rf[a]):+.2f} | {np.mean(pf[a]):+.2f} | {np.mean(pf[a])-np.mean(rf[a]):+.2f} |")
    L += ["", f"Acute − none: real {np.mean(rf['acute'])-np.mean(rf['none']):+.2f} st, predicted {np.mean(pf['acute'])-np.mean(pf['none']):+.2f} st.",
          "", "Audio for the listening session: `data/synth/" + name + "/test_pred/` (Iliad 1.1–52) and `val_pred/`.", ""]
    (ROOT / f"reports/eval_{name}.md").write_text("\n".join(L)); print("\n".join(L))

if __name__ == "__main__":
    main()
