#!/usr/bin/env python3
"""Phase 1 QC: scan the raw Iliad clips for validity, duration, and speech extent.

Writes data/iliad/scan.csv with one row per expected (book, line):
  book,line,path,status,size,dur,lead,trail,speech,md5
status: ok | html404 | broken_mp4 | missing
lead/trail = seconds before the first / after the last 20 ms frame whose RMS exceeds SPEECH_DB.
peak = loudest frame RMS in dBFS.
"""
import array, csv, hashlib, math, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/iliad/raw/Homer/Iliad"
OUT = ROOT / "data/iliad/scan.csv"
SR = 16000
FRAME = 0.02      # seconds per RMS frame
SPEECH_DB = -40   # frames above this count as speech
EXPECTED = {1:611,2:877,3:461,4:544,5:909,6:529,7:482,8:565,9:713,10:579,11:848,12:471,
            13:837,14:522,15:746,16:867,17:761,18:617,19:424,20:503,21:611,22:515,23:897,24:804}

def analyze(item):
    book, line = item
    p = RAW / f"book_{book}" / f"line_{line}.mp4"
    row = dict(book=book, line=line, path=str(p.relative_to(ROOT)), status="missing",
               size=0, dur="", lead="", trail="", speech="", peak="", md5="")
    if not p.exists():
        return row
    data = p.read_bytes()
    row["size"] = len(data); row["md5"] = hashlib.md5(data).hexdigest()
    if data[:15].lstrip().lower().startswith(b"<!doctype html") or data[:6].lower() == b"<html>":
        row["status"] = "html404"; return row
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True).stdout
    if len(pcm) < SR // 10:
        row["status"] = "broken_mp4"; return row
    a = array.array("h"); a.frombytes(pcm[: len(pcm) // 2 * 2])
    n = int(SR * FRAME)
    frames = []
    for i in range(0, len(a) - n + 1, n):
        seg = a[i:i + n]
        rms = math.sqrt(sum(x * x for x in seg) / n) / 32768
        frames.append(20 * math.log10(rms) if rms > 0 else -120.0)
    dur = len(a) / SR
    speech_idx = [i for i, f in enumerate(frames) if f > SPEECH_DB]
    if not speech_idx:
        row.update(status="ok", dur=f"{dur:.3f}", lead=f"{dur:.3f}", trail="0.000", speech="0.000", peak=f"{max(frames):.1f}")
        return row
    lead = speech_idx[0] * FRAME
    trail = dur - (speech_idx[-1] + 1) * FRAME
    row.update(status="ok", dur=f"{dur:.3f}", lead=f"{lead:.3f}", trail=f"{trail:.3f}",
               speech=f"{dur - lead - trail:.3f}", peak=f"{max(frames):.1f}")
    return row

def main():
    items = [(b, l) for b, n in EXPECTED.items() for l in range(1, n + 1)]
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(analyze, items))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(Counter(r["status"] for r in rows), file=sys.stderr)
    print(f"wrote {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
