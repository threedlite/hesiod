#!/usr/bin/env python3
"""Join the audio scan, hypotactic transcripts and Perseus mapping into data/iliad/metadata.csv.

One row per audio index (book, idx) in the download layout. Columns:
  id            b{book}_l{idx}
  book, idx     audio index (hypotactic reading-page numbering)
  perseus_n     vulgate line number in Perseus tlg0012.tlg001 (empty if none)
  status        ok | excluded
  reason        why excluded (empty when ok)
  dur, lead, trail, speech, peak   from scan.csv
  text          transcript as Chamberlain's reading page prints it (what he read)
  text_scanned  same line from the newer scanned page (Perseus-aligned, corrected)
  trimmed_dur   seconds after decode_trim.py (empty until it has run)
  wav           relative path of the raw clip
  clean_wav     relative path of the trimmed 22.05 kHz WAV
Also rewrites data/iliad/exclusions.csv with the final reasons.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/iliad"
MIN_SPEECH = 2.0
MAX_SPEECH = 8.0   # 21.427 is 12 s (two lines run together); it would dominate batch padding

scan = {(int(r["book"]), int(r["line"])): r for r in csv.DictReader((D / "scan.csv").open())}
hyp = {(int(r["book"]), int(r["idx"])): r["text"] for r in csv.DictReader((D / "hypotactic_lines.csv").open())}
lmap = {(int(r["book"]), int(r["idx"])): r["perseus_n"] for r in csv.DictReader((D / "line_map.csv").open())}
scanned = {}
for r in csv.DictReader((D / "hypotactic_scanned_lines.csv").open()):
    scanned[(int(r["book"]), int(r["idx"]))] = r["text"]
smap = {(int(r["book"]), int(r["idx"])): r["perseus_n"] for r in csv.DictReader((D / "line_map_scanned.csv").open())}
scanned_by_perseus = {(b, int(n)): scanned[(b, i)] for (b, i), n in smap.items() if n}

trim = {r["id"]: r for r in csv.DictReader((D / "trim_log.csv").open())} if (D / "trim_log.csv").exists() else {}
MIN_TRIMMED = 2.0

hyp_count = {}
for (b, i) in hyp: hyp_count[b] = max(hyp_count.get(b, 0), i)

rows, excl = [], []
for (b, i), s in sorted(scan.items()):
    if b == 19:
        # reading page for book 19 lost lines 101-144 after the audio was made; audio has all 424 lines
        pn = str(i); text = scanned_by_perseus.get((b, i), "")
    else:
        pn = lmap.get((b, i), ""); text = hyp.get((b, i), "")
    text_scanned = scanned_by_perseus.get((b, int(pn)), "") if pn else ""
    status, reason = "ok", ""
    if s["status"] == "html404":
        if b != 19 and i > hyp_count.get(b, 0):
            reason = "no_such_line (index beyond Chamberlain's text; vulgate numbering differs)"
        else:
            reason = "not_recorded (server 404)"
    elif s["status"] == "broken_mp4":
        reason = "broken_mp4"
    elif s["status"] == "missing":
        reason = "file_missing"
    elif float(s["speech"]) < MIN_SPEECH:
        reason = f"stub_audio (speech {float(s['speech']):.2f}s)"
    elif float(s["speech"]) > MAX_SPEECH:
        reason = f"outlier_duration (speech {float(s['speech']):.2f}s)"
    elif not text:
        reason = "no_transcript"
    elif f"b{b}_l{i}" in trim and trim[f"b{b}_l{i}"]["out_dur"] and float(trim[f"b{b}_l{i}"]["out_dur"]) < MIN_TRIMMED:
        reason = f"stub_after_trim (trimmed {float(trim[f'b{b}_l{i}']['out_dur']):.2f}s)"
    if reason:
        status = "excluded"; excl.append([b, i, pn, reason])
    t = trim.get(f"b{b}_l{i}", {})
    rows.append(dict(id=f"b{b}_l{i}", book=b, idx=i, perseus_n=pn, status=status, reason=reason,
                     dur=s["dur"], lead=s["lead"], trail=s["trail"], speech=s["speech"], peak=s["peak"],
                     trimmed_dur=t.get("out_dur", ""), text=text, text_scanned=text_scanned,
                     wav=f"data/iliad/raw/Homer/Iliad/book_{b}/line_{i}.mp4",
                     clean_wav=f"data/iliad/wavs/b{b}_l{i}.wav" if status == "ok" and t else ""))

with (D / "metadata.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with (D / "exclusions.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["book", "idx", "perseus_n", "reason"]); w.writerows(excl)

ok = [r for r in rows if r["status"] == "ok"]
from collections import Counter
print(f"rows {len(rows)}  ok {len(ok)}  excluded {len(excl)}")
print(Counter(e[3].split(" (")[0] for e in excl))
print(f"usable speech: {sum(float(r['speech']) for r in ok)/3600:.2f} h (scan measure)")
if trim: print(f"trimmed corpus: {sum(float(r['trimmed_dur']) for r in ok if r['trimmed_dur'])/3600:.2f} h")
print("text differs between reading page and scanned page:", sum(1 for r in ok if r['text_scanned'] and r['text'] != r['text_scanned']))
