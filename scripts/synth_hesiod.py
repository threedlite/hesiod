#!/usr/bin/env python3
"""Phase 7: synthesize every line of a corpus (default Hesiod; --corpus hymns), QC it automatically, and package for Classics Viewer.

  1. synth all lines of data/<corpus>/phones.csv with the checkpoint (prediction mode) -> data/synth/<corpus>_<name>/wav/<id>.wav
  2. recognizer PER per line; lines above PER_MAX are re-synthesized with a slightly different
     duration scale (0.97, 1.03) and the best is kept; persistent failures listed
  3. reports/<corpus>_qc_<name>.md; notes/human_qa_queue.md gets the failures
  4. --package: AAC-LC mono 44.1 kHz 96 kb/s MP4 in <Author>/<Work>/book_1/line_<n>.mp4 and a zip
Usage: python scripts/synth_hesiod.py [--corpus hymns] --ckpt train/runs/<run>/best.pt [--package] [--limit N]
"""
import argparse, csv, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); from corpora import corpus, add_corpus_arg

ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable
PER_MAX = 0.10          # per-line threshold (recognizer floor on real audio is 0.032 corpus-wide)
C = None   # the corpus dict (scripts/corpora.py), set in main()

def run(cmd): r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT); return r.stdout + r.stderr

def synth(ckpt, ids, out, dur_scale=1.0):
    lst = out.parent / f"{out.name}.txt"; lst.write_text("\n".join(ids) + "\n")
    return run([PY, "train/fs2.py", "synth", "--ckpt", ckpt, "--list", str(lst), "--phones", f"{C['data']}/phones.csv", "--out", str(out), "--dur_scale", str(dur_scale)])

def score(ids, wavdir, phones, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "wav", "phones"])
        for i in ids: w.writerow([i, str(wavdir / f"{i}.wav"), phones[i]["phones"]])
    run([PY, "train/recognize.py", "--manifest", str(path), "--out", str(path).replace("manifest", "per")])
    return {r["id"]: float(r["per"]) for r in csv.DictReader(open(str(path).replace("manifest", "per")))}

def main():
    global C
    ap = add_corpus_arg(argparse.ArgumentParser()); ap.add_argument("--ckpt", required=True); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--package", action="store_true"); ap.add_argument("--package-only", action="store_true"); ap.add_argument("--name")
    ap.add_argument("--wav-dir", help="package these WAVs instead of <out>/wav (e.g. a converted voice)"); ap.add_argument("--package-name", help="zip/package label (default: <corpus>_chamberlain_tts_<name>)")
    ap.add_argument("--lettered", action="store_true", help="keep lettered line numbers (line_929a.mp4) for an app that accepts text line numbers"); args = ap.parse_args()
    C = corpus(args.corpus); name = args.name or Path(args.ckpt).parent.name; out = ROOT / "data/synth" / f"{C['name']}_{name}"; out.mkdir(parents=True, exist_ok=True)
    phones = {r["id"]: r for r in csv.DictReader((ROOT / C["data"] / "phones.csv").open()) if r["phones"]}
    ids = list(phones)[:args.limit] if args.limit else list(phones)
    if args.package_only:
        package(out, ids, phones, name, wav_dir=Path(args.wav_dir) if args.wav_dir else None, label=args.package_name, lettered=args.lettered); return
    print(synth(args.ckpt, ids, out / "wav").strip().splitlines()[-1])
    per = score(ids, out / "wav", phones, out / "manifest.csv")
    bad = [i for i in ids if per[i] > PER_MAX]; print(f"lines above PER {PER_MAX}: {len(bad)} of {len(ids)}")
    for scale in (0.97, 1.03, 0.94, 1.06):
        if not bad: break
        alt = out / f"wav_retry_{scale}"; synth(args.ckpt, bad, alt, scale); per_alt = score(bad, alt, phones, out / f"manifest_retry_{scale}.csv")
        for i in bad:
            if per_alt[i] < per[i]:
                per[i] = per_alt[i]; (out / "wav" / f"{i}.wav").write_bytes((alt / f"{i}.wav").read_bytes())
        bad = [i for i in bad if per[i] > PER_MAX]; print(f"after retry x{scale}: {len(bad)} still above")
    vals = np.array([per[i] for i in ids])
    L = [f"# {C['author']} synthesis QC: " + name, "", f"Lines synthesized: {len(ids)}. Corpus PER {100*vals.mean():.2f} % (median line {100*np.median(vals):.2f} %, p95 {100*np.percentile(vals,95):.2f} %).",
         f"Lines above the per-line threshold ({100*PER_MAX:.0f} %) after retries: {len(bad)} ({100*len(bad)/len(ids):.2f} %). Package gate: < 1 %.", "",
         "| Work | lines | mean PER | above threshold |", "|---|---|---|---|"]
    for wk in C["works"].values():
        w_ids = [i for i in ids if phones[i]["work"] == wk]
        if w_ids: L.append(f"| {wk} | {len(w_ids)} | {100*np.mean([per[i] for i in w_ids]):.2f} % | {sum(1 for i in w_ids if per[i] > PER_MAX)} |")
    L += ["", "## Worst 20 lines", "", "| id | PER | text |", "|---|---|---|"]
    for i in sorted(ids, key=lambda i: -per[i])[:20]: L.append(f"| {i} | {100*per[i]:.1f} % | {phones[i]['text']} |")
    (ROOT / f"reports/{C['name']}_qc_{name}.md").write_text("\n".join(L) + "\n"); print("\n".join(L[:8]))
    with (out / "per.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "work", "n", "per"]); [w.writerow([i, phones[i]["work"], phones[i]["n"], per[i]]) for i in ids]
    if bad:
        qa = ROOT / "notes/human_qa_queue.md"; t = qa.read_text()
        t += f"\n## {C['author']} synthesized lines above PER {100*PER_MAX:.0f} % ({name})\n" + "".join(f"- {i} ({100*per[i]:.0f} %): {phones[i]['text']}\n" for i in sorted(bad, key=lambda i: -per[i]))
        qa.write_text(t)
    if args.package: package(out, ids, phones, name)

def package(out, ids, phones, name, wav_dir=None, label=None, lettered=False):
    """AAC MP4s in <Author>/<Work>/book_1/line_<n>.mp4. Lettered line numbers (Theogony 929a-t, Hymn 2 137a) are
    skipped: the app stores them all under the integer line number, so only the unlettered line is addressable."""
    wav_dir = wav_dir or (out / "wav"); label = label or f"{C['name']}_chamberlain_tts_{name}"
    if lettered: label = label + "_lettered"
    pkg = out / ("package" if (wav_dir == out / "wav" and not lettered) else f"package_{label}"); skipped = []
    for i in ids:
        r = phones[i]
        if not r["n"].isdigit() and not lettered: skipped.append(i); continue
        d = pkg / C["author"] / C["titles"][r["work"]] / "book_1"; d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav_dir / f"{i}.wav"), "-ar", "44100", "-ac", "1", "-c:a", "aac", "-b:a", "96k", str(d / f"line_{r['n']}.mp4")], check=True)
    zpath = out / f"{label}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(pkg.rglob("*.mp4")): z.write(p, p.relative_to(pkg))
    n = sum(1 for _ in pkg.rglob("*.mp4"))
    print(f"package: {zpath} ({n} files; " + (f"{len(skipped)} lettered lines synthesized but not packaged: {', '.join(skipped[:5])}..." if skipped else "lettered line numbers kept in file names") + ")")

if __name__ == "__main__":
    main()
