#!/usr/bin/env python3
"""Phase 5: validate the scanner against Chamberlain's scansion, 24-fold by book.

For each book, the lexicon is built from the other 23 books, every line of the book is scanned
from its clean text, and the quantity string is compared with his (phones.csv `quantity`).
Lines whose syllable counts differ are reported separately (his synizesis/diaeresis choices).
Writes reports/scanner_validation.md and data/iliad/scanner_vs_chamberlain.csv.
"""
import csv, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prosody.scanner import scan_line
from prosody import lexicon as L

ROOT = Path(__file__).resolve().parents[1]

def main(no_lexicon=False):
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open()) if r["status"] == "ok"}
    ph = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}
    rows, tot = [], Counter()
    for b in range(1, 25):
        lex = None if no_lexicon else L.build(exclude_books=[b])
        for i in sorted(int(x["idx"]) for x in ph.values() if x["book"] == str(b)):
            id_ = f"b{b}_l{i}"
            if id_ not in meta: continue
            text = meta[id_]["text_clean"]; his = ph[id_]["quantity"]
            s = scan_line(text, lex)
            mine = s.quantities()
            if not s.ok: cat = "no_scan"
            elif len(mine) != len(his): cat = "syllable_count_differs"
            elif mine == his: cat = "match"
            else: cat = "mismatch"
            tot[cat] += 1
            rows.append(dict(id=id_, category=cat, mine=mine, his=his, cost=s.cost, alternatives=s.n_alternatives,
                             flags=";".join(s.flags), unknown_left=sum(1 for n in s.nuclei if n.how == "unknown"), text=text))
        print(f"book {b}: {dict(tot)}", file=sys.stderr)
    with (ROOT / "data/iliad/scanner_vs_chamberlain.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    n = len(rows); same_count = [r for r in rows if r["category"] in ("match", "mismatch")]
    amb = sum(1 for r in rows if r["category"] == "match" and r["alternatives"] > 1)
    lines = ["# Scanner validation against Chamberlain (24-fold by book)", "",
             f"Lines: {n}. Lexicon built from the other 23 books for each book{' (lexicon disabled)' if no_lexicon else ''}.", "",
             "| Outcome | Lines | Share |", "|---|---|---|"]
    for k in ("match", "mismatch", "syllable_count_differs", "no_scan"):
        lines.append(f"| {k} | {tot[k]} | {100*tot[k]/n:.2f} % |")
    lines += ["", f"Among lines with the same syllable count: {100*tot['match']/max(1,len(same_count)):.2f} % identical.",
              f"Matches that still had more than one equally cheap scansion: {amb} ({100*amb/max(1,tot['match']):.1f} % of matches).",
              f"Unresolved α/ι/υ nuclei remaining after lexicon and accent rules: {sum(r['unknown_left'] for r in rows)} over {n} lines.", "",
              "## Sample mismatches", "", "| id | mine | his | flags | text |", "|---|---|---|---|---|"]
    for r in [r for r in rows if r["category"] == "mismatch"][:20]:
        lines.append(f"| {r['id']} | {r['mine']} | {r['his']} | {r['flags']} | {r['text']} |")
    lines += ["", "## Sample syllable-count differences", "", "| id | mine | his | flags | text |", "|---|---|---|---|---|"]
    for r in [r for r in rows if r["category"] == "syllable_count_differs"][:15]:
        lines.append(f"| {r['id']} | {r['mine']} | {r['his']} | {r['flags']} | {r['text']} |")
    lines += ["", "## No scan", "", "| id | flags | text |", "|---|---|---|"]
    for r in [r for r in rows if r["category"] == "no_scan"][:15]:
        lines.append(f"| {r['id']} | {r['flags']} | {r['text']} |")
    (ROOT / "reports/scanner_validation.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:14]))

if __name__ == "__main__":
    main(no_lexicon="--no-lexicon" in sys.argv)
