#!/usr/bin/env python3
"""Phase 3: prosody baseline and acoustic speaker profile from the aligned corpus.

Reads align/textgrids/chamberlain/<id>.TextGrid (phone tier) and data/iliad/phones.csv,
maps aligned phones back to syllables, extracts F0 (parselmouth) and formants, and reports:
  - F0 contour and level by accent type (A/G/C/0), with effect sizes vs unaccented
  - duration by syllable quantity (L/S) and by vowel length (aː vs a etc.)
  - stop duration pʰ/tʰ/kʰ vs p/t/k (aspiration proxy), ζ = z+d durations
  - F1/F2 of y vs i vs uː, F2 movement inside eː and uː (monophthong check)
Writes reports/prosody_baseline.md and data/iliad/syllable_acoustics.csv.
Usage: python scripts/prosody_baseline.py [--sample N]
"""
import csv, json, sys, math, random, argparse
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from textgrid import read_textgrid
import parselmouth
from parselmouth.praat import call

ROOT = Path(__file__).resolve().parents[1]
TG = ROOT / "align/textgrids/chamberlain"
ACCENT = "ˊˋˆ"
ACC_NAME = {"A": "acute", "G": "grave", "C": "circumflex", "0": "none"}

def syllables_of(row):
    """[(syll_index, [phones...])] from the phones string, accents stripped."""
    out, si = [], 0
    for wi, word in enumerate(row["phones"].split("#")):
        for syl in word.strip().split("."):
            ph = [p.rstrip(ACCENT) for p in syl.split() if p]
            if ph: out.append(ph)
    return out

def cohen_d(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if len(a) < 2 or len(b) < 2: return float("nan")
    s = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / s if s else float("nan")

def analyze(row, meta):
    tg = read_textgrid(TG / f"{row['id']}.TextGrid")
    phones = [(a, b, t) for a, b, t in tg.get("phones", []) if t and t not in ("sil", "sp", "spn", "")]
    sylls = syllables_of(row)
    expected = [p for s in sylls for p in s]
    got = [t for _, _, t in phones]
    if got != expected: return None, "phone_mismatch"
    snd = parselmouth.Sound(str(ROOT / meta["clean_wav"]))
    pitch = snd.to_pitch(time_step=0.005, pitch_floor=60, pitch_ceiling=300)
    f0 = pitch.selected_array["frequency"]; t0 = pitch.xs()
    voiced = f0 > 0
    if voiced.sum() < 10: return None, "unvoiced"
    med = np.median(f0[voiced]); st = np.where(voiced, 12 * np.log2(np.maximum(f0, 1) / med), np.nan)
    formant = snd.to_formant_burg(time_step=0.005, max_number_of_formants=5, maximum_formant=5000)
    q, acc, foot = row["quantity"], row["accent"], row["foot"]
    recs, k = [], 0
    for si, s in enumerate(sylls):
        seg = phones[k: k + len(s)]; k += len(s)
        a, b = seg[0][0], seg[-1][1]
        sel = (t0 >= a) & (t0 < b) & voiced
        vals = st[sel]
        if len(vals) >= 2:
            half = len(vals) // 2
            rise = np.nanmax(vals) - vals[0]; fall = np.nanmax(vals) - vals[-1]
            slope1 = np.nanmean(vals[half:]) - np.nanmean(vals[:half])
            mean_st, max_st = float(np.nanmean(vals)), float(np.nanmax(vals))
        else:
            rise = fall = slope1 = mean_st = max_st = float("nan")
        vowel = next(((pa, pb, pt) for pa, pb, pt in seg if pt[0] in "aeiouyɛɔ"), None)
        f1 = f2 = f2a = f2b = float("nan"); vph = ""
        if vowel:
            pa, pb, vph = vowel; mid = (pa + pb) / 2
            f1 = call(formant, "Get value at time", 1, mid, "Hertz", "Linear"); f2 = call(formant, "Get value at time", 2, mid, "Hertz", "Linear")
            f2a = call(formant, "Get value at time", 2, pa + 0.25 * (pb - pa), "Hertz", "Linear")
            f2b = call(formant, "Get value at time", 2, pa + 0.75 * (pb - pa), "Hertz", "Linear")
        recs.append(dict(id=row["id"], syll=si, q=q[si], acc=acc[si], foot=foot[si], n_ph=len(s), dur=b - a,
                         vowel=vph, vowel_dur=(vowel[1] - vowel[0]) if vowel else float("nan"),
                         f0_mean_st=mean_st, f0_max_st=max_st, rise_st=rise, fall_st=fall, slope_st=slope1,
                         f1=f1, f2=f2, f2_move=(f2b - f2a) if vowel else float("nan"),
                         phone_durs=json.dumps([(pt, round(pb - pa, 4)) for pa, pb, pt in seg])))
    return recs, "ok"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sample", type=int, default=0); args = ap.parse_args()
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open())}
    rows = [r for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open()) if (TG / f"{r['id']}.TextGrid").exists()]
    if args.sample: random.seed(1); rows = random.sample(rows, min(args.sample, len(rows)))
    recs, status = [], defaultdict(int)
    for i, r in enumerate(rows):
        out, st = analyze(r, meta[r["id"]]); status[st] += 1
        if out: recs.extend(out)
        if i % 500 == 0: print(f"{i}/{len(rows)}", dict(status), file=sys.stderr)
    with (ROOT / "data/iliad/syllable_acoustics.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
    # ---- report ----
    L = lambda key, cond: np.array([x[key] for x in recs if cond(x) and not (isinstance(x[key], float) and math.isnan(x[key]))])
    lines = ["# Prosody baseline and acoustic speaker profile", "", f"Utterances analyzed: {status['ok']} (skipped: {dict((k, v) for k, v in status.items() if k != 'ok')}). Syllables: {len(recs)}.", ""]
    lines += ["## F0 by accent type (semitones relative to the utterance median)", "", "| Accent | n | mean | max | rise to peak | fall from peak | 2nd half − 1st half | d(mean) vs none | d(fall) vs none |", "|---|---|---|---|---|---|---|---|---|"]
    none_mean = L("f0_mean_st", lambda x: x["acc"] == "0"); none_fall = L("fall_st", lambda x: x["acc"] == "0")
    for a in "AC G 0".replace(" ", ""):
        c = lambda x, a=a: x["acc"] == a
        m, mx, ri, fa, sl = (L(k, c) for k in ("f0_mean_st", "f0_max_st", "rise_st", "fall_st", "slope_st"))
        if not len(m): continue
        lines.append(f"| {ACC_NAME[a]} | {len(m)} | {m.mean():+.2f} | {mx.mean():+.2f} | {ri.mean():.2f} | {fa.mean():.2f} | {sl.mean():+.2f} | {cohen_d(m, none_mean):+.2f} | {cohen_d(fa, none_fall):+.2f} |")
    lines += ["", "## Duration by syllable quantity", "", "| Quantity | n | mean syllable dur (ms) | mean vowel dur (ms) |", "|---|---|---|---|"]
    for qv in "LS":
        d = L("dur", lambda x, qv=qv: x["q"] == qv); v = L("vowel_dur", lambda x, qv=qv: x["q"] == qv)
        lines.append(f"| {qv} | {len(d)} | {1000*d.mean():.0f} | {1000*v.mean():.0f} |")
    dl, ds = L("dur", lambda x: x["q"] == "L"), L("dur", lambda x: x["q"] == "S")
    lines.append(f"\nLong:short syllable duration ratio = {dl.mean()/ds.mean():.2f}, d = {cohen_d(dl, ds):.2f}")
    lines += ["", "## Vowel duration by phone (ms)", "", "| vowel | n | mean | | vowel | n | mean |", "|---|---|---|---|---|---|---|"]
    pairs = [("a", "aː"), ("i", "iː"), ("y", "yː"), ("e", "eː"), ("o", "uː"), ("ɛː", "ɔː")]
    for p1, p2 in pairs:
        a1 = L("vowel_dur", lambda x, p=p1: x["vowel"] == p); a2 = L("vowel_dur", lambda x, p=p2: x["vowel"] == p)
        lines.append(f"| {p1} | {len(a1)} | {1000*a1.mean() if len(a1) else float('nan'):.0f} | | {p2} | {len(a2)} | {1000*a2.mean() if len(a2) else float('nan'):.0f} |")
    lines += ["", "## Stops: aspirated vs plain (phone duration, ms; aspiration adds length)", "", "| plain | n | ms | aspirated | n | ms |", "|---|---|---|---|---|---|"]
    pd = defaultdict(list)
    for x in recs:
        for pt, d in json.loads(x["phone_durs"]): pd[pt].append(d)
    for p, ph in (("p", "pʰ"), ("t", "tʰ"), ("k", "kʰ")):
        lines.append(f"| {p} | {len(pd[p])} | {1000*np.mean(pd[p]):.0f} | {ph} | {len(pd[ph])} | {1000*np.mean(pd[ph]):.0f} |")
    zz, zd = [], []
    for x in recs:
        ph = json.loads(x["phone_durs"])
        for i in range(len(ph) - 1):
            if ph[i][0] == "z" and ph[i + 1][0] == "d": zz.append(ph[i][1]); zd.append(ph[i + 1][1])
    if zd: lines.append(f"\nζ as z+d: z part {1000*np.mean(zz):.0f} ms, stop part {1000*np.mean(zd):.0f} ms (n={len(zd)}, {100*np.mean(np.array(zd)<=0.0301):.0f} % at the 30 ms floor); plain δ {1000*np.mean(pd['d']):.0f} ms. A ζ read as [z] alone would leave the stop interval at the floor.")
    lines += ["", "## Vowel quality (F1/F2 at midpoint, Hz)", "", "| vowel | n | F1 | F2 | F2 move (75% − 25%) |", "|---|---|---|---|---|"]
    for v in ("i", "iː", "y", "yː", "uː", "eː", "e", "ɛː", "o", "ɔː", "a", "aː"):
        f1 = L("f1", lambda x, v=v: x["vowel"] == v); f2 = L("f2", lambda x, v=v: x["vowel"] == v); mv = L("f2_move", lambda x, v=v: x["vowel"] == v)
        if len(f1): lines.append(f"| {v} | {len(f1)} | {np.median(f1):.0f} | {np.median(f2):.0f} | {np.median(mv):+.0f} |")
    lines += ["", "Reading guide: υ as [y] shows F2 between i (≈2000+) and uː (<1000) with low F1; ει/ου as monophthongs show small F2 movement; aspirated stops longer than plain by ≥20 ms; circumflex should show a larger fall from peak than acute.", ""]
    (ROOT / "reports/prosody_baseline.md").write_text("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
