"""Vowel-length lexicon for α ι υ, built from Chamberlain's scansion via data/iliad/phones.csv.

lexicon[word_form][nucleus_index] = "L" | "S", where word_form is the NFC lowercase word with
accents and the elision apostrophe (see scanner.norm_word) and nucleus_index counts vowel
nuclei (diphthongs = one) from the start of the word. Only unflagged syllables contribute
(no position/line-final/synizesis/correption ambiguity). Majority vote per slot; ties dropped.
"""
import csv, json, sys, unicodedata
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prosody.scanner import norm_word, nuclei_of_word
from greek2ipa.rules import letters_with_marks

ROOT = Path(__file__).resolve().parents[1]
ACCENT = "ˊˋˆ"

def build(exclude_books=(), phones_csv=ROOT / "data/iliad/phones.csv"):
    votes = defaultdict(lambda: defaultdict(Counter))
    for r in csv.DictReader(phones_csv.open()):
        if r["book"] in set(map(str, exclude_books)): continue
        detail = json.loads(r["detail"]); sy_i = 0
        for g in r["phones"].split("#"):
            n_syll = g.count(".") + 1
            sylls = detail[sy_i: sy_i + n_syll]; sy_i += n_syll
            form = norm_word("".join(d["text"] for d in sylls))
            if not form: continue
            # per-syllable: vowel phones in order; a syllable's α ι υ nucleus gets its phone length
            nuc = nuclei_of_word(letters_with_marks(form), 0)
            # map nuclei to syllables by walking his syllables' vowel letters
            k = 0
            for d in sylls:
                bad = set(d["flags"]) & {"position_ambiguous", "line_final_ambiguous", "synizesis", "correption", "closed_long_syllable", "lexicon"}
                vph = [p.rstrip(ACCENT) for p in d["ph"] if p[0] in "aeiouyɛɔ"]
                nvow = sum(1 for b, _ in letters_with_marks(d["text"]) if b in "αεηιουω")
                # nuclei in this syllable = number of vowel phones (diphthong = 1 phone)
                for vp in vph:
                    if k >= len(nuc): break
                    x = nuc[k]; k += 1
                    if x.nature != "?" or bad: continue
                    if vp[0] in "aiy": votes[form][x.idx_in_word]["L" if "ː" in vp else "S"] += 1
    lex = {}
    for form, slots in votes.items():
        d = {}
        for idx, c in slots.items():
            (q1, n1), *rest = c.most_common()
            if not rest or n1 > rest[0][1]: d[idx] = q1
        if d: lex[form] = d
    return lex

def save(lex, path):
    with Path(path).open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["word", "nucleus", "length"])
        for form in sorted(lex):
            for idx, q in sorted(lex[form].items()): w.writerow([form, idx, q])

def load(path):
    lex = defaultdict(dict)
    for r in csv.DictReader(Path(path).open()): lex[r["word"]][int(r["nucleus"])] = r["length"]
    return dict(lex)

def load_all(root=ROOT):
    """Word-form lexicon merged with the lemma/ending generalization; exact forms take priority."""
    lex = load(root / "prosody/lexicon_lemma.csv") if (root / "prosody/lexicon_lemma.csv").exists() else {}
    for form, slots in load(root / "prosody/lexicon.csv").items():
        lex.setdefault(form, {}).update(slots)
    return lex

if __name__ == "__main__":
    lex = build(); save(lex, ROOT / "prosody/lexicon.csv")
    print(f"{len(lex)} word forms, {sum(len(v) for v in lex.values())} resolved α/ι/υ slots -> prosody/lexicon.csv")
