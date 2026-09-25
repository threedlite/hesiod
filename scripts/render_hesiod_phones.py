#!/usr/bin/env python3
"""Phase 6: corpus text (default Hesiod; --corpus hymns) -> data/<corpus>/phones.csv with the same columns as data/iliad/phones.csv, plus inventory and coverage checks."""
import argparse, csv, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from greek2ipa.from_text import convert_text
from greek2ipa.from_spans import serialize
from prosody.scanner import norm_word, words_of
from prosody import lexicon as L
sys.path.insert(0, str(Path(__file__).resolve().parent)); from corpora import corpus, add_corpus_arg

ROOT = Path(__file__).resolve().parents[1]

def main():
    C = corpus(add_corpus_arg(argparse.ArgumentParser()).parse_args().corpus); D = ROOT / C["data"]; prefix = C["prefix"]
    lex = L.load_all(ROOT)
    train_inv = set((ROOT / "align/phones.txt").read_text().split())
    rows = list(csv.DictReader((D / "lines.csv").open()))
    out, inv, flags, wf, wf_known = [], Counter(), Counter(), Counter(), Counter()
    for r in rows:
        for w in words_of(r["text_clean"]):
            k = norm_word(w); wf[k] += 1
            if k in lex: wf_known[k] += 1
        words, scan = convert_text(r["text_clean"], lex)
        id_ = f"{prefix(r['tlg'])}_{r['n']}"
        if words is None:
            out.append(dict(work=r["work"], n=r["n"], id=id_, n_syll="", phones="", quantity="", accent="", foot="", flags="no_scan", detail="", text=r["text_clean"])); continue
        sy = [s for w in words for s in w.sylls]
        for s in sy:
            for p in s.phones: inv[p] += 1
            for f in s.flags: flags[f] += 1
        for f in scan.flags: flags["scan:" + f] += 1
        out.append(dict(work=r["work"], n=r["n"], id=id_, n_syll=len(sy), phones=serialize(words),
                        quantity="".join(s.q for s in sy), accent="".join(s.accent for s in sy), foot="".join(str(s.foot) for s in sy),
                        flags=";".join(f"{i}:{f}" for i, s in enumerate(sy) for f in s.flags),
                        detail=json.dumps([{"text": s.text, "q": s.q, "acc": s.accent, "foot": s.foot, "ph": s.phones, "flags": s.flags} for s in sy], ensure_ascii=False),
                        text=r["text_clean"]))
    with (D / "phones.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    nsyl = sum(int(o["n_syll"]) for o in out if o["n_syll"])
    print(f"{len(out)} lines, {sum(1 for o in out if o['phones'])} rendered, {nsyl} syllables -> {D / 'phones.csv'}")
    print("flags:", {k: f"{v} ({100*v/nsyl:.1f}%)" if not k.startswith("scan:") else v for k, v in flags.most_common()})
    print("phones not in the training inventory:", sorted(set(inv) - train_inv) or "none")
    print("training phones unused by this corpus:", sorted(train_inv - set(inv)) or "none")
    tok = sum(wf.values()); typ = len(wf)
    print(f"word forms: {typ} types / {tok} tokens; in Iliad lexicon: {len(wf_known)} types ({100*len(wf_known)/typ:.1f} %), {sum(wf_known.values())} tokens ({100*sum(wf_known.values())/tok:.1f} %)")

if __name__ == "__main__":
    main()
