#!/usr/bin/env python3
"""Phase 6 step 1: Perseus TEI for Hesiod (tlg0020) -> data/hesiod/lines.csv (work, n, text, text_clean).
Editorial marks ([ ], †, numbers, apparatus sigla) are stripped; apostrophes unified; NFC."""
import csv, html, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from diff_transcripts import normalize

ROOT = Path(__file__).resolve().parents[1]
SRC = Path.home() / "git/classicsviewer/data-sources/canonical-greekLit/data/tlg0020"
WORKS = {"tlg001": "Theogony", "tlg002": "Works and Days", "tlg003": "Shield"}

def main():
    rows = []
    for tlg, name in WORKS.items():
        f = next((SRC / tlg).glob("*grc*.xml"))
        s = f.read_text(encoding="utf8")
        body = s[s.find("<body"):]
        for m in re.finditer(r'<l\b([^>]*)>(.*?)</l>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            n = re.search(r'\bn="([^"]+)"', attrs); n = n.group(1) if n else ""
            inner = re.sub(r"<note\b.*?</note>", "", inner, flags=re.S)          # apparatus notes
            t = html.unescape(re.sub(r"<[^>]+>", "", inner))
            t = re.sub(r"[\[\]†*\d]", "", t)                                      # editorial brackets, daggers, digits
            t = re.sub(r"\s+", " ", t).strip()
            clean = normalize(t)
            rows.append(dict(work=name, tlg=tlg, n=n, text=t, text_clean=clean, source=f.name))
    with (ROOT / "data/hesiod/lines.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter(r["work"] for r in rows)
    print({k: v for k, v in c.items()}, "->", ROOT / "data/hesiod/lines.csv")
    odd = Counter(ch for r in rows for ch in r["text_clean"] if not (unicodedata.category(ch)[0] in "LM" or ch in " ’.,·;!?—-…"))
    print("unusual characters:", dict(odd))
    print("non-numeric or empty line numbers:", [r["n"] for r in rows if not r["n"].isdigit()][:10])

if __name__ == "__main__":
    main()
