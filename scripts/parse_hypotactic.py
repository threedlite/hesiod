#!/usr/bin/env python3
"""Parse hypotactic.com Iliad pages: the reading pages (data/scansion/iliad/, whose sequential
line ids are the audio file indices) and the newer scanned pages (data/scansion/iliad_scanned/).

Outputs:
  data/iliad/hypotactic_lines.csv   book, idx, n_syll, text, syllables (JSON list of {s, q, foot, word, hemi, footend, wordend})
  data/iliad/line_map.csv           book, idx (hypotactic/audio index), perseus_n, sim (0-1 text similarity)
Hypotactic numbers lines sequentially within its own text; Perseus keeps the vulgate
numbering and includes a few lines Chamberlain's text omits, so the two drift apart.
"""
import csv, difflib, html, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data/scansion/iliad"
PERSEUS = Path.home() / "git/classicsviewer/data-sources/canonical-greekLit/data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml"

def norm(t):
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c)[0] == "L")   # letters only, no marks/punct
    return t.lower()

def parse_page(b, scanned=False):
    fn = PAGES.parent / "iliad_scanned" / f"iliad{b}scanned.html" if scanned else PAGES / f"iliad{b}.html"
    s = fn.read_text(encoding="utf8", errors="ignore")
    out = []
    for m in re.finditer(r'<div class="line[^"]*" id="line(\d+)"[^>]*>(.*?)</div>', s, re.S):
        idx = int(m.group(1)); inner = m.group(2)
        sylls = []
        for sm in re.finditer(r'<span\s+class=\s*"([^"]*)"[^>]*>(.*?)</span>', inner, re.S):
            cls = sm.group(1).split(); txt = html.unescape(sm.group(2))
            if "syll" not in cls: continue
            txt = re.sub(r"&?n?b?s?nbsp;?", "", txt)          # broken entities on the scanned pages
            txt = txt.replace("\xa0", " ").strip()
            d = {"s": txt, "q": "L" if "long" in cls else "S" if "short" in cls else "?"}
            for c in cls:
                for k in ("foot", "word", "hemi"):
                    if c.startswith(k) and c[len(k):].isdigit(): d[k] = int(c[len(k):])
            d["footend"] = "footend" in cls; d["wordend"] = "wordend" in cls
            sylls.append(d)
        # rebuild the text from the syllables: the reading pages have no whitespace between
        # spans, so word boundaries come from the word index, not from the markup
        parts, prev_word = [], None
        for d in sylls:
            if prev_word is not None and d.get("word") != prev_word: parts.append(" ")
            parts.append(d["s"]); prev_word = d.get("word")
        text = re.sub(r"\s+", " ", "".join(parts)).strip()
        out.append((idx, text, sylls))
    out.sort()
    return out

def perseus_lines():
    s = PERSEUS.read_text(encoding="utf8")
    books = {}
    for m in re.finditer(r'<div[^>]*subtype="[Bb]ook"[^>]*n="(\d+)"[^>]*>(.*?)(?=<div[^>]*subtype="[Bb]ook"|</body>)', s, re.S):
        b = int(m.group(1)); lines = []
        for lm in re.finditer(r'<l\b[^>]*n="(\d+)"[^>]*>(.*?)</l>', m.group(2), re.S):
            t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", lm.group(2)))).strip()
            lines.append((int(lm.group(1)), t))
        books[b] = lines
    return books

def align(hyp, per):
    """Monotonic alignment of hypotactic lines to Perseus lines by normalized text."""
    a = [norm(t) for _, t, _ in hyp]; b = [norm(t) for _, t in per]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    mapping = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): mapping[hyp[i1 + k][0]] = (per[j1 + k][0], 1.0)
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                sim = difflib.SequenceMatcher(a=a[i1 + k], b=b[j1 + k]).ratio()
                mapping[hyp[i1 + k][0]] = (per[j1 + k][0], round(sim, 3))
        elif tag in ("replace", "delete"):
            # unequal replace: greedy best match within the window, keep monotonic
            jj = j1
            for i in range(i1, i2):
                best = None
                for j in range(jj, j2):
                    sim = difflib.SequenceMatcher(a=a[i], b=b[j]).ratio()
                    if best is None or sim > best[1]: best = (j, sim)
                if best and best[1] >= 0.6:
                    mapping[hyp[i][0]] = (per[best[0]][0], round(best[1], 3)); jj = best[0] + 1
                else:
                    mapping[hyp[i][0]] = ("", 0.0)
    return mapping

def run(per, scanned):
    lines_out, map_out = [], []
    for b in range(1, 25):
        hyp = parse_page(b, scanned)
        mp = align(hyp, per[b])
        unmapped = [i for i, _, _ in hyp if mp.get(i, ("", 0))[0] == ""]
        low = [i for i, _, _ in hyp if 0 < mp.get(i, ("", 0))[1] < 0.9]
        per_missing = sorted(set(n for n, _ in per[b]) - set(v[0] for v in mp.values()))
        print(f"book {b:2d}: hyp {len(hyp):3d}  perseus {len(per[b]):3d}  unmapped {len(unmapped)}  low-sim {len(low)}  "
              f"perseus-only lines {per_missing}", file=sys.stderr)
        for i, t, sy in hyp:
            lines_out.append([b, i, len(sy), t, json.dumps(sy, ensure_ascii=False)])
            n, sim = mp.get(i, ("", 0.0))
            map_out.append([b, i, n, sim])
    tag = "_scanned" if scanned else ""
    with (ROOT / f"data/iliad/hypotactic{tag}_lines.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["book", "idx", "n_syll", "text", "syllables"]); w.writerows(lines_out)
    with (ROOT / f"data/iliad/line_map{tag}.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["book", "idx", "perseus_n", "sim"]); w.writerows(map_out)
    print(f"{len(lines_out)} hypotactic{tag} lines written", file=sys.stderr)

def main():
    per = perseus_lines()
    print("== reading pages (audio index order) ==", file=sys.stderr); run(per, False)
    print("== scanned pages (newer, Perseus-aligned) ==", file=sys.stderr); run(per, True)

if __name__ == "__main__":
    main()
