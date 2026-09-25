#!/usr/bin/env python3
"""Phase 8 checks for a converted directory against the unconverted one (same timing).

Uses the synthesized lines' token durations (synth_index.csv from fs2.py synth) to locate vowel
midpoints, so formants, H1-H2 and accent pitch are measured on the same segments in both.
Reports: PER (recognizer) for both, F1/F2 medians per vowel and their ratios, H1-H2 change, HNR
change, median F0, accent contrasts in semitones, unvoiced fraction.
Usage: python scripts/eval_voice.py --orig <dir> --conv <dir> --index <synth_index.csv> --phones <phones.csv> [--ids a,b] [--json out.json]
"""
import argparse, csv, json, subprocess, sys
from collections import defaultdict
from pathlib import Path
import numpy as np, parselmouth
from parselmouth.praat import call
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "train"))
from prepare_features import tokens_of

ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable
FPS = 24000 / 256; VOWELS = ("a", "e", "i", "o", "y", "uː", "eː", "ɛː", "ɔː", "aː", "iː", "yː")
ACC = {0: "none", 1: "acute", 2: "grave", 3: "circumflex"}

def per(ids, wavdir, phones, tag, out):
    m = out / f"{tag}_manifest.csv"
    with m.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "wav", "phones"]); [w.writerow([i, str(Path(wavdir) / f"{i}.wav"), phones[i]["phones"]]) for i in ids]
    r = subprocess.run([PY, "train/recognize.py", "--manifest", str(m), "--out", str(out / f"{tag}_per.csv")], capture_output=True, text=True, cwd=ROOT)
    return float(r.stdout.strip().splitlines()[-1].split("PER")[1].split("%")[0])

def measure(wav, toks, durs, ceiling):
    snd = parselmouth.Sound(str(wav)); sr = snd.sampling_frequency
    # ceiling 400 Hz: below the 2nd harmonic of a ~210 Hz voice, so the tracker cannot octave-jump on converted audio
    pitch = snd.to_pitch(time_step=0.005, pitch_floor=60, pitch_ceiling=400); f0 = pitch.selected_array["frequency"]; tt = pitch.xs()
    voiced = f0 > 0; med = np.median(f0[voiced]) if voiced.any() else 0
    formant = snd.to_formant_burg(time_step=0.005, max_number_of_formants=5, maximum_formant=5500)
    hnr_obj = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=60); hnr = call(hnr_obj, "Get mean", 0, 0)
    rec = dict(f0_median=float(med), unvoiced=float(np.mean(~voiced)), hnr=float(hnr), formants=defaultdict(list), acc=defaultdict(list), h1h2=[], f0=f0, tt=tt)
    pos = 0.0
    for (p, q, a, foot), d in zip(toks, durs):
        dur = d / FPS; mid = pos + dur / 2
        if p in VOWELS and dur > 0.04:
            f1 = call(formant, "Get value at time", 1, mid, "Hertz", "Linear"); f2 = call(formant, "Get value at time", 2, mid, "Hertz", "Linear")
            if not (np.isnan(f1) or np.isnan(f2)): rec["formants"][p].append((f1, f2))
            sel = (tt >= pos) & (tt < pos + dur) & voiced
            if sel.any(): rec["acc"][ACC[a]].append(12 * np.log2(np.mean(f0[sel]) / med))
            # H1 - H2 from a 40 ms spectrum slice at the vowel midpoint
            f0m = np.mean(f0[sel]) if sel.any() else 0
            if f0m > 0:
                part = snd.extract_part(from_time=max(0, mid - 0.02), to_time=mid + 0.02, preserve_times=False)
                spec = part.to_spectrum(); freqs = spec.xs(); mag = 10 * np.log10(np.abs(spec.values[0] + 1j * spec.values[1]) ** 2 + 1e-12)
                def lvl(f):
                    band = (freqs > 0.85 * f) & (freqs < 1.15 * f); return mag[band].max() if band.any() else np.nan
                h1, h2 = lvl(f0m), lvl(2 * f0m)
                if not (np.isnan(h1) or np.isnan(h2)): rec["h1h2"].append(h1 - h2)
        pos += dur
    return rec

def accent_joint(ra, rb, toks, durs):
    """Per-class mean pitch (st vs median) for both files, over frames voiced in BOTH (timing is identical)."""
    n = min(len(ra["f0"]), len(rb["f0"])); fa, fb, tt = ra["f0"][:n], rb["f0"][:n], ra["tt"][:n]
    mask = (fa > 0) & (fb > 0)
    if mask.sum() < 10: return
    for rec, f0 in ((ra, fa), (rb, fb)):
        med = np.median(f0[mask]); rec["acc"] = defaultdict(list); pos = 0.0
        for (p, q, a, foot), d in zip(toks, durs):
            dur = d / FPS
            if p in VOWELS and dur > 0.04:
                sel = (tt >= pos) & (tt < pos + dur) & mask
                if sel.any(): rec["acc"][ACC[a]].append(12 * np.log2(np.mean(f0[sel]) / med))
            pos += dur

def summarize(recs):
    s = dict(f0_median=float(np.median([r["f0_median"] for r in recs])), unvoiced=float(np.mean([r["unvoiced"] for r in recs])),
             hnr=float(np.mean([r["hnr"] for r in recs])), h1h2=float(np.mean([v for r in recs for v in r["h1h2"]])) if any(r["h1h2"] for r in recs) else float("nan"))
    fm = defaultdict(list)
    for r in recs:
        for v, lst in r["formants"].items(): fm[v].extend(lst)
    s["formants"] = {v: (float(np.median([a for a, _ in l])), float(np.median([b for _, b in l])), len(l)) for v, l in fm.items() if len(l) >= 10}
    ac = defaultdict(list)
    for r in recs:
        for k, l in r["acc"].items(): ac[k].extend(l)
    s["accent"] = {k: float(np.mean(l)) for k, l in ac.items()}
    return s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--orig", required=True); ap.add_argument("--conv", required=True); ap.add_argument("--index", required=True)
    ap.add_argument("--phones", required=True); ap.add_argument("--ids"); ap.add_argument("--json"); ap.add_argument("--no-per", action="store_true"); a = ap.parse_args()
    idx = {r["id"]: r for r in csv.DictReader(open(a.index))}; phones = {r["id"]: r for r in csv.DictReader(open(a.phones))}
    ids = a.ids.split(",") if a.ids else [f.stem for f in sorted(Path(a.conv).glob("*.wav"))]
    out = Path(a.conv).parent / "eval"; out.mkdir(exist_ok=True)
    res = {}
    if not a.no_per:
        res["per_orig"] = per(ids, a.orig, phones, "orig", out); res["per_conv"] = per(ids, a.conv, phones, "conv", out)
    ro, rc = [], []
    for i in ids:
        toks, _ = tokens_of(phones[i]); durs = list(map(int, idx[i]["pred_dur"].split()))
        r1 = measure(Path(a.orig) / f"{i}.wav", toks, durs, 500); r2 = measure(Path(a.conv) / f"{i}.wav", toks, durs, 500)   # identical tracker settings
        accent_joint(r1, r2, toks, durs); ro.append(r1); rc.append(r2)
    so, sc = summarize(ro), summarize(rc); res["orig"], res["conv"] = so, sc
    res["formant_ratio"] = {v: (sc["formants"][v][0] / so["formants"][v][0], sc["formants"][v][1] / so["formants"][v][1]) for v in so["formants"] if v in sc["formants"]}
    con = lambda S, k: S["accent"].get(k, float("nan")) - S["accent"].get("none", float("nan"))
    res["contrast_orig"] = {k: con(so, k) for k in ("acute", "circumflex", "grave")}
    res["contrast_conv"] = {k: con(sc, k) for k in ("acute", "circumflex", "grave")}
    res["accent_delta"] = {k: res["contrast_conv"][k] - res["contrast_orig"][k] for k in res["contrast_orig"]}
    print(f"PER orig {res.get('per_orig', float('nan')):.2f} % -> conv {res.get('per_conv', float('nan')):.2f} %")
    print(f"F0 median {so['f0_median']:.0f} -> {sc['f0_median']:.0f} Hz | unvoiced {100*so['unvoiced']:.1f} -> {100*sc['unvoiced']:.1f} % | HNR {so['hnr']:.1f} -> {sc['hnr']:.1f} dB | H1-H2 {so['h1h2']:.1f} -> {sc['h1h2']:.1f} dB")
    print("formant ratios conv/orig (F1, F2):", {v: (round(r1, 2), round(r2, 2)) for v, (r1, r2) in res["formant_ratio"].items()})
    print("accent contrasts vs unaccented (st) orig:", {k: round(v, 2) for k, v in res["contrast_orig"].items()}, "conv:", {k: round(v, 2) for k, v in res["contrast_conv"].items()})
    if a.json: json.dump(res, open(a.json, "w"), indent=1, default=float)

if __name__ == "__main__":
    main()
