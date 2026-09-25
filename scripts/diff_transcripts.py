#!/usr/bin/env python3
"""Phase 1 step 4: build text_clean for every usable line and log every difference.

Witnesses: R = Chamberlain's reading page (what he read; primary), S = his 2026 scanned
page, P = Perseus. Rules, in order:
  1. Normalize R: NFC, all apostrophe variants -> ’ (U+2019), "’Ρ/’ρ" -> Ῥ/ῥ, a space
     after an elision apostrophe, single spaces.
  2. If R and P have the same letters but different word boundaries, adopt P's
     tokenization, except for the -δε suffix (οἶκονδε / θάνατον δὲ are edition choices).
  3. Diacritic-only differences from P are his conventions: keep R, log them.
  4. Word differences from P are edition variants: keep R, log them, unless the line
     is in data/iliad/transcript_overrides.csv (garbled text and typos, fixed by hand).
Writes data/iliad/transcript_diff.csv and adds text_clean to data/iliad/metadata.csv.
"""
import csv, difflib, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_hypotactic import perseus_lines

ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "data/iliad"
APOS = "’'ʼ‘`´"

def normalize(t):
    t = "".join("’" if c in APOS else c for c in t)
    t = unicodedata.normalize("NFC", t)
    t = t.replace("’Ρ", "Ῥ").replace("’ρ", "ῥ").replace("*", "")
    t = re.sub(r"’(?=[^\s’.,·;!?])", "’ ", t)
    return re.sub(r"\s+", " ", t).strip()

def L(t): return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) in ("Ll", "Lu")).lower()
def LM(t): return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c)[0] in "LM" and unicodedata.category(c) != "Lm").lower()
def words(t): return [w for w in re.split(r"[\s’]+", t) if L(w)]
def strip_punct(w): return "".join(c for c in w if unicodedata.category(c)[0] in "LM" or c == "’")

def _respace(chunk, p_words):
    """Re-insert spaces into chunk (R text with its spaces removed) at P's word boundaries,
    counting letters only, so apostrophes, punctuation and diacritics are preserved."""
    targets, acc = [], 0
    for w in p_words[:-1]:
        acc += len(L(w)); targets.append(acc)
    out, count, ti = [], 0, 0
    i = 0
    while i < len(chunk):
        c = chunk[i]; out.append(c)
        if unicodedata.category(c) in ("Ll", "Lu"): count += 1
        # after reaching a boundary, also swallow trailing marks / apostrophe / punctuation
        if ti < len(targets) and count == targets[ti]:
            j = i + 1
            while j < len(chunk) and (unicodedata.category(chunk[j])[0] == "M" or chunk[j] in "’.,·;!?"):
                out.append(chunk[j]); j += 1
            out.append(" "); ti += 1; i = j; continue
        i += 1
    return "".join(out)

def retokenize(r, p):
    """Adopt P's word boundaries where R differs only by spacing (except -δε)."""
    rt = r.split(" ")                      # after normalize(), space-separated tokens are words
    rl = [L(t) for t in rt]; pw = words(p); pl = [L(w) for w in pw]
    sm = difflib.SequenceMatcher(a=[x for x in rl if x], b=pl, autojunk=False)
    # map letter-bearing token positions back to rt indices
    pos = [i for i, x in enumerate(rl) if x]
    out, changed, last = [], False, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        rb = [rt[k] for k in pos[i1:i2]]; pb = pw[j1:j2]
        if rb and "".join(L(t) for t in rb) == "".join(L(w) for w in pb) and not any(L(w) == "δε" for w in rb + pb):
            start, end = pos[i1], pos[i2 - 1] + 1
            out.extend(rt[last:start]); out.append(_respace("".join(rt[start:end]), pb)); last = end; changed = True
    out.extend(rt[last:])
    return (" ".join(out).replace("  ", " ").strip(), changed) if changed else (r, False)

def main():
    per = perseus_lines(); perd = {(b, n): t for b, ls in per.items() for n, t in ls}
    overrides = {r["id"]: r for r in csv.DictReader((D / "transcript_overrides.csv").open())}
    rows = list(csv.DictReader((D / "metadata.csv").open()))
    log = []
    for r in rows:
        r["text_clean"] = ""
        if r["status"] != "ok": continue
        R = normalize(r["text"]); P = perd.get((int(r["book"]), int(r["perseus_n"])), "") if r["perseus_n"] else ""
        S = normalize(r["text_scanned"]) if r["text_scanned"] else ""
        cat, action, clean = "same", "keep", R
        if r["id"] in overrides:
            cat, action, clean = "override", overrides[r["id"]]["reason"], normalize(overrides[r["id"]]["text_clean"])
        elif P and L(R) != L(P):
            cat, action = "word_variant", "keep R (edition variant)"
        elif P and words(R) and [L(w) for w in words(R)] != [L(w) for w in words(P)]:
            clean, ch = retokenize(R, P); cat = "tokens"; action = "adopt P tokenization" if ch else "keep R (-δε)"
        elif P and LM(R) != LM(P):
            cat, action = "diacritics", "keep R (his convention)"
        r["text_clean"] = clean
        if cat != "same" or (S and L(S) != L(R)):
            log.append(dict(id=r["id"], category=cat, action=action, reading=r["text"], scanned=r["text_scanned"], perseus=P, text_clean=clean))
    with (D / "metadata.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with (D / "transcript_diff.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0].keys())); w.writeheader(); w.writerows(log)
    from collections import Counter
    print(Counter(x["category"] for x in log)); print(f"{len(log)} logged differences -> {D/'transcript_diff.csv'}")
    for x in log:
        if x["category"] in ("tokens", "override"): print(f"  {x['id']:9s} {x['category']:8s} {x['action'][:28]:28s} | {x['reading']}  ->  {x['text_clean']}")
    ok = [r for r in rows if r["status"] == "ok"]
    print("all ok rows have text_clean:", all(r["text_clean"] for r in ok))
    chars = Counter(c for r in ok for c in unicodedata.normalize("NFC", r["text_clean"]))
    odd = {c: n for c, n in chars.items() if not (unicodedata.category(c)[0] in "LM" or c in " ’.,·;!?")}
    print("non-letter, non-punctuation characters remaining in text_clean:", odd)

if __name__ == "__main__":
    main()
