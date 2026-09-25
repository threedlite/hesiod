#!/usr/bin/env python3
"""Phase 5/6: scan every Hesiod line with the full Iliad lexicon -> data/hesiod/scansion.csv + summary."""
import csv, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prosody.scanner import scan_line
from prosody import lexicon as L

ROOT = Path(__file__).resolve().parents[1]

def main():
    lex = L.load_all(ROOT)
    rows, out = list(csv.DictReader((ROOT / "data/hesiod/lines.csv").open())), []
    stats = Counter(); unres = Counter(); flags = Counter(); words = Counter(); words_in_lex = Counter()
    for r in rows:
        s = scan_line(r["text_clean"], lex)
        stats["ok" if s.ok else "no_scan"] += 1
        for f in s.flags: flags[f] += 1
        nu = sum(1 for n in s.nuclei if n.how == "unknown")
        unres[r["work"]] += nu
        for n in s.nuclei: words[r["work"]] += 1
        out.append(dict(work=r["work"], n=r["n"], ok=s.ok, pattern=s.pattern, quantities=s.quantities(), cost=s.cost,
                        alternatives=s.n_alternatives, unknown_nuclei=nu, flags=";".join(s.flags),
                        nuclei=" ".join(f"{x.text}:{x.q}:{x.how}" for x in s.nuclei), text=r["text_clean"]))
    with (ROOT / "data/hesiod/scansion.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("lines:", len(rows), dict(stats))
    print("flags:", dict(flags.most_common()))
    print("alternatives>1:", sum(1 for o in out if o["ok"] and o["alternatives"] > 1))
    for wk in unres: print(f"{wk}: unresolved α/ι/υ before solving {unres[wk]} of {words[wk]} nuclei ({100*unres[wk]/words[wk]:.1f} %)")
    print("no_scan lines:"); [print("  ", o["work"], o["n"], o["text"]) for o in out if not o["ok"]][:30]

if __name__ == "__main__":
    main()
