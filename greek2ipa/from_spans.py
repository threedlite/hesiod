#!/usr/bin/env python3
"""Chamberlain syllable spans -> phones (Track I, Phase 2).

Input: one line as a list of syllable dicts {s, q, foot, word, hemi, footend, wordend}
(from data/iliad/hypotactic_lines.csv). Output: a Line with words -> syllables -> phones,
plus per-syllable quantity (from his span), accent (from the diacritics), foot, hemi.

Vowel length for α ι υ is inferred from the syllable: long if the span is long and the
syllable is open (ends in that vowel) and the next syllable does not begin with a
consonant cluster (position). Closed syllables and cluster-initial followers leave the
length unknown: default short, flagged, to be resolved by the Phase 5 lexicon.
"""
import csv, json, sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from greek2ipa.rules import *

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class Syll:
    text: str; q: str; foot: int; hemi: int; accent: str = "0"
    phones: list = field(default_factory=list); flags: list = field(default_factory=list)

@dataclass
class Word:
    sylls: list; elided: bool = False

def accent_of(marks_list):
    ms = set().union(*marks_list) if marks_list else set()
    if CIRC in ms: return "C"
    if ACUTE in ms: return "A"
    if GRAVE in ms: return "G"
    return "0"

def consonant_run_at_start(letters):
    """Number of consonant letters (ζ ξ ψ count 2) before the first vowel of a letter list."""
    n = 0
    for b, _ in letters:
        if b in VOWELS: break
        if b == "’": continue
        n += 2 if b in CLUSTER_LETTERS else 1
    return n

def phonemize_word(sylls, next_word_first_letters, line_final, lexicon=None):
    """sylls: list of Syll for one word (text already set). Fills phones/accent/flags."""
    # flatten letters with syllable index
    L = []   # (base, marks, syll_idx)
    for si, s in enumerate(sylls):
        for b, m in letters_with_marks(s.text):
            L.append((b, m, si))
    elided = any(b == "’" for b, _, _ in L)
    L = [(b, m, si) for b, m, si in L if b != "’"]
    if not L: return elided
    # lexicon: word form -> {nucleus index: "L"/"S"}; nucleus index counts vowel groups (diphthong = 1)
    lex_entry = None
    if lexicon:
        from prosody.scanner import norm_word
        lex_entry = lexicon.get(norm_word("".join(s.text for s in sylls)))
    nucleus_idx = -1
    rough_initial = ROUGH in L[0][1] or (len(L) > 1 and L[0][0] in VOWELS and ROUGH in L[1][1] and L[1][0] in VOWELS)
    # rough breathing on the first vowel group (may sit on the 2nd element of a diphthong)
    first_v = next((i for i, (b, _, _) in enumerate(L) if b in VOWELS), None)
    if first_v is not None:
        grp = [L[first_v]] + ([L[first_v + 1]] if first_v + 1 < len(L) and L[first_v + 1][0] in VOWELS and L[first_v + 1][2] == L[first_v][2] else [])
        rough_initial = any(ROUGH in m for _, m, _ in grp) and first_v == 0
    i = 0
    while i < len(L):
        b, m, si = L[i]; s = sylls[si]
        if b == "ρ":
            if i == 0 and ROUGH in m: s.phones.append("r̥")
            elif i > 0 and L[i - 1][0] == "ρ" and ROUGH in m: s.phones.append("r̥")   # ῤῥ
            else: s.phones.append("r")
            i += 1; continue
        if b in CONSONANTS:
            nxt = L[i + 1][0] if i + 1 < len(L) else (next_word_first_letters[0][0] if next_word_first_letters else "")
            if b == "γ" and nxt in VELARS: s.phones.append("ŋ")
            elif b in ("σ", "ς") and nxt in VOICED_C: s.phones.append("z")
            else: s.phones.extend(CONSONANTS[b])
            i += 1; continue
        if b in VOWELS:
            nucleus_idx += 1
            if i == 0 and rough_initial: s.phones.append("h")
            # diphthong?
            if (i + 1 < len(L) and L[i + 1][0] in VOWELS and L[i + 1][2] == si
                    and (b, L[i + 1][0]) in DIPHTHONGS and DIAER not in L[i + 1][1] and not (m & {ACUTE, GRAVE, CIRC, ROUGH, SMOOTH})):
                ph, _ = DIPHTHONGS[(b, L[i + 1][0])]
                s.phones.append(ph); i += 2
                if s.q == "S": s.flags.append("correption")
                continue
            if IOTA_SUB in m:
                s.phones.append(IOTA_SUB_DIPH.get(b, b)); i += 1
                if s.q == "S": s.flags.append("correption")
                continue
            if b in FIXED:
                ph, long_ = FIXED[b]
                s.phones.append(ph + ("ː" if long_ else ""))
                if long_ and s.q == "S": s.flags.append("correption")
                i += 1
                if i < len(L) and L[i][0] in VOWELS and L[i][2] == si: s.flags.append("synizesis")
                continue
            # α ι υ: infer length from the syllable quantity and what follows the vowel.
            # His syllable boundaries are ignored here (they separate prefixes, so "ἄτ.ας"
            # would look closed): count consonant letters up to the next vowel, within the
            # word or into the next word.
            ph = VARIABLE[b]
            if MACRON in m: long_ = True
            elif BREVE in m: long_ = False
            elif s.q == "S": long_ = False
            elif i + 1 < len(L) and L[i + 1][0] in VOWELS and L[i + 1][2] == si:
                long_ = False; s.flags.append("synizesis")
            else:
                rest = [(x[0], x[1]) for x in L[i + 1:]]
                run = consonant_run_at_start(rest)
                no_vowel_after = not any(b2 in VOWELS for b2, _ in rest)
                unknown_end = False
                if no_vowel_after:
                    if next_word_first_letters is None or line_final: unknown_end = True
                    else: run += consonant_run_at_start(next_word_first_letters)
                lexq = lex_entry.get(nucleus_idx) if lex_entry else None
                if unknown_end or run >= 2:
                    if lexq in ("L", "S"):
                        long_ = lexq == "L"; s.flags.append("lexicon")
                    else:
                        long_ = False; s.flags.append("line_final_ambiguous" if unknown_end else "position_ambiguous")
                else:
                    long_ = True
            s.phones.append(ph + ("ː" if long_ else "")); i += 1
            continue
        i += 1   # unknown letter: dropped (should not happen; property test catches it)
    for s in sylls:
        s.accent = accent_of([m for b, m, si in L if si == sylls.index(s) and b in VOWELS])
    return elided

def line_to_words(sylls_json):
    words, cur, cur_idx = [], [], None
    for d in sylls_json:
        if cur and d.get("word") != cur_idx:
            words.append(cur); cur = []
        cur_idx = d.get("word")
        cur.append(Syll(text=d["s"], q=d["q"], foot=d.get("foot", 0), hemi=d.get("hemi", 0)))
    if cur: words.append(cur)
    return words

def convert_line(sylls_json, lexicon=None):
    words = line_to_words(sylls_json)
    out = []
    for wi, w in enumerate(words):
        nxt = None
        if wi + 1 < len(words):
            nxt = letters_with_marks("".join(s.text for s in words[wi + 1]))
            nxt = [(b, m) for b, m in nxt if b != "’"]
        elided = phonemize_word(w, nxt, line_final=(wi + 1 == len(words)), lexicon=lexicon)
        out.append(Word(sylls=w, elided=elided))
    return out

def serialize(words):
    """Flat token string: phones separated by spaces, '.' between syllables, '#' between words.
    Vowel tokens carry the syllable accent as a suffix (ˊ acute, ˋ grave, ˆ circumflex)."""
    toks = []
    for wi, w in enumerate(words):
        if wi: toks.append("#")
        for si, s in enumerate(w.sylls):
            if si: toks.append(".")
            for p in s.phones:
                if p[0] in "aeiouyɛɔ" and s.accent != "0":
                    p += {"A": "ˊ", "G": "ˋ", "C": "ˆ"}[s.accent]
                toks.append(p)
    return " ".join(toks)

def main():
    src = ROOT / "data/iliad/hypotactic_lines.csv"; dst = ROOT / "data/iliad/phones.csv"
    # Book 19's reading page lost lines 101-144 after the audio was made, so its sequential
    # ids no longer match the audio index; the scanned page has all 424 lines in Perseus
    # numbering, which for book 19 equals the audio index. Use it for that book.
    rows = [r for r in csv.DictReader(src.open()) if r["book"] != "19"]
    rows += [r for r in csv.DictReader((ROOT / "data/iliad/hypotactic_scanned_lines.csv").open()) if r["book"] == "19"]
    rows.sort(key=lambda r: (int(r["book"]), int(r["idx"])))
    flags, inv, out = Counter(), Counter(), []
    lexicon = None
    lex_path = ROOT / "prosody/lexicon.csv"
    if lex_path.exists() and "--no-lexicon" not in sys.argv:
        from prosody import lexicon as LX
        lexicon = LX.load_all(ROOT)
    for r in rows:
        words = convert_line(json.loads(r["syllables"]), lexicon)
        sy = [s for w in words for s in w.sylls]
        for s in sy:
            for f in s.flags: flags[f] += 1
            for p in s.phones: inv[p] += 1
        out.append(dict(book=r["book"], idx=r["idx"], id=f"b{r['book']}_l{r['idx']}", n_syll=len(sy),
                        phones=serialize(words),
                        quantity="".join(s.q for s in sy), accent="".join(s.accent for s in sy),
                        foot="".join(str(s.foot) for s in sy),
                        flags=";".join(f"{i}:{f}" for i, s in enumerate(sy) for f in s.flags),
                        detail=json.dumps([{"text": s.text, "q": s.q, "acc": s.accent, "foot": s.foot, "hemi": s.hemi,
                                            "ph": s.phones, "flags": s.flags} for s in sy], ensure_ascii=False)))
    with dst.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    nsyl = sum(o["n_syll"] for o in out)
    print(f"{len(out)} lines, {nsyl} syllables -> {dst}")
    print("flags:", {k: f"{v} ({100*v/nsyl:.1f}%)" for k, v in flags.most_common()})
    print("phone inventory:", sorted(inv.items(), key=lambda x: -x[1]))
    unknown = set(inv) - PHONE_SET
    print("phones outside PHONE_SET:", unknown or "none")

if __name__ == "__main__":
    main()
