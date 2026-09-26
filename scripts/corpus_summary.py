#!/usr/bin/env python3
"""Phase 10: one table over every synthesized corpus (data/synth/<corpus>_fs2_full/per.csv and the female eval),
for reports/phase10_corpora.md. Usage: python3 scripts/corpus_summary.py [--md]"""
import csv, json, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from corpora import ORDER, corpus
import numpy as np
ROOT = Path(__file__).resolve().parents[1]

def skipped_note(d): return f" (+{d['skipped']} in non-hexameter books)" if d["skipped"] else ""

def main():
    rows = []
    for c in ORDER:
        C = corpus(c); out = ROOT / "data/synth" / f"{c}_fs2_full"; per_f = out / "per.csv"
        if not per_f.exists(): rows.append((c, C["author"], None)); continue
        per = {r["id"]: float(r["per"]) for r in csv.DictReader(per_f.open())}
        ph = {r["id"]: r for r in csv.DictReader((ROOT / C["data"] / "phones.csv").open())}
        n_lines = len(ph); n_syn = len(per); vals = np.array(list(per.values()))
        unmet = sum(1 for r in csv.DictReader((ROOT / C["data"] / "scansion.csv").open()) if "unmetrical" in r["flags"]); skipped = sum(1 for r in ph.values() if r["flags"] == "non_hexameter_book")
        z = out / f"{c}_chamberlain_tts_fs2_full.zip"; n_pkg = len(zipfile.ZipFile(z).namelist()) if z.exists() else 0
        zf = out / f"{c}_chamberlain_tts_female.zip"; size = (zf.stat().st_size if zf.exists() else 0) / 1e6      # the released package
        ev = ROOT / "data/synth" / f"{c}_fs2_full_female/eval_full.json"; e = json.load(ev.open()) if ev.exists() else None
        rows.append((c, C["author"], dict(lines=n_lines, syn=n_syn, unmet=unmet, skipped=skipped, per=100 * vals.mean(), med=100 * np.median(vals), p95=100 * np.percentile(vals, 95),
                                          bad=int((vals > 0.10).sum()), pkg=n_pkg, mb=size, f0=(e["orig"]["f0_median"], e["conv"]["f0_median"]) if e else None, per_conv=e["per_conv"] if e else None)))
    print("| Corpus | Author | Lines | Synthesized | Unmetrical | Corpus PER | Median / p95 | > 10 % | Package files | Zip (MB) | Female F0 | Female PER |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    tot = dict(lines=0, syn=0, bad=0, pkg=0, mb=0.0, err=0.0)
    for c, a, d in rows:
        if d is None: print(f"| {c} | {a} | | pending | | | | | | | | |"); continue
        print(f"| {c} | {a} | {d['lines']:,} | {d['syn']:,} | {d['unmet']}{skipped_note(d)} | {d['per']:.2f} % | {d['med']:.2f} / {d['p95']:.2f} | {d['bad']} ({100*d['bad']/d['syn']:.2f} %) | {d['pkg']:,} | {d['mb']:.0f} | "
              + (f"{d['f0'][0]:.0f} → {d['f0'][1]:.0f} Hz" if d['f0'] else "") + " | " + (f"{d['per_conv']:.1f} %" if d['per_conv'] else "") + " |")
        tot["lines"] += d["lines"]; tot["syn"] += d["syn"]; tot["bad"] += d["bad"]; tot["pkg"] += d["pkg"]; tot["mb"] += d["mb"]; tot["err"] += d["per"] * d["syn"]
    if tot["syn"]: print(f"| **all** | | {tot['lines']:,} | {tot['syn']:,} | | {tot['err']/tot['syn']:.2f} % | | {tot['bad']} ({100*tot['bad']/tot['syn']:.2f} %) | {tot['pkg']:,} | {tot['mb']:.0f} | | |")

if __name__ == "__main__":
    main()
