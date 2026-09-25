#!/usr/bin/env python3
"""Phase 6 step 1: Perseus TEI -> data/<corpus>/lines.csv (work, tlg, n, text, text_clean). Default corpus Hesiod (tlg0020);
--corpus hymns does the Homeric Hymns (tlg0013). <supplied>/<add>/<surplus> text is kept (it is what the app shows), <note> and <gap> are dropped;
Editorial marks ([ ], †, numbers, apparatus sigla) are stripped; apostrophes unified; NFC."""
import argparse, csv, html, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from diff_transcripts import normalize
from corpora import corpus, add_corpus_arg

ROOT = Path(__file__).resolve().parents[1]

def main():
    C = corpus(add_corpus_arg(argparse.ArgumentParser()).parse_args().corpus)
    SRC, WORKS, OUT = C["src"], C["works"], ROOT / C["data"] / "lines.csv"; OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for tlg, name in WORKS.items():
        f = next((SRC / tlg).glob("*grc*.xml"))
        s = f.read_text(encoding="utf8")
        body = s[s.find("<body"):]
        for m in re.finditer(r'<l\b([^>]*)>(.*?)</l>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            n = re.search(r'\bn="([^"]+)"', attrs); n = n.group(1) if n else ""
            inner = re.sub(r"<!--.*?-->", "", inner, flags=re.S)                     # XML comments (the Hymns have commented-out quote milestones)
            inner = re.sub(r"<note\b.*?</note>", "", inner, flags=re.S)          # apparatus notes
            inner = re.sub(r"<choice\b.*?<corr>(.*?)</corr>.*?</choice>", r"\1", inner, flags=re.S)   # <choice><sic/><corr/>: read the correction (Hymn 3.181)
            t = html.unescape(re.sub(r"<[^>]+>", "", inner))
            t = re.sub(r"[\[\]†*\d]", "", t)                                      # editorial brackets, daggers, digits
            t = re.sub(r"\s+", " ", t).strip()
            clean = normalize(t)
            rows.append(dict(work=name, tlg=tlg, n=n, text=t, text_clean=clean, source=f.name))
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter(r["work"] for r in rows)
    print({k: v for k, v in c.items()}, "->", OUT)
    odd = Counter(ch for r in rows for ch in r["text_clean"] if not (unicodedata.category(ch)[0] in "LM" or ch in " ’.,·;!?—-…"))
    print("unusual characters:", dict(odd))
    print("non-numeric or empty line numbers:", [r["n"] for r in rows if not r["n"].isdigit()][:10])

if __name__ == "__main__":
    main()
