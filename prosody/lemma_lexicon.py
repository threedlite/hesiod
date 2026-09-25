"""Lemma- and ending-level generalization of the vowel-length lexicon (Track H, Phase 5).

Sources: Perseus treebanks (form, lemma, postag) for the Iliad and Hesiod; the word-form
lexicon (prosody/lexicon.py) for the Iliad.

Two generalizations, applied to forms the word-form lexicon does not cover:
  1. lemma prefix: a target form inherits the length of each α ι υ nucleus that lies inside
     the longest common letter prefix with a known form of the same lemma (majority vote).
  2. ending: for (postag, ending) pairs, where ending = the letters from the last nucleus
     (and separately from the second-to-last nucleus) to the end of the form, the lengths of
     those final nuclei are voted from known forms and applied to targets with the same
     postag and ending.
build_extended(exclude_books) -> {form: {nucleus_idx: L/S}} covering treebank forms of both corpora.
validate() reports precision of the generalizations on held-out Iliad books.
"""
import csv, re, sys, unicodedata
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prosody.scanner import norm_word, nuclei_of_word
from prosody import lexicon as L
from greek2ipa.rules import letters_with_marks

ROOT = Path(__file__).resolve().parents[1]
TB = Path.home() / "git/classicsviewer/data-sources/treebank_data/v2.0/Greek/nonArethusaCompliant"
FILES = {"iliad": "tlg0012.tlg001.perseus-grc1.tb.xml", "theogony": "tlg0020.tlg001.perseus-grc1.tb.xml",
         "wd": "tlg0020.tlg002.perseus-grc1.tb.xml", "shield": "tlg0020.tlg003.perseus-grc1.tb.xml"}

def read_treebank(name):
    """(form, lemma, postag, book, line) per word. Book/line come from the word's cite when present
    (Iliad, Theogony, Shield); Works and Days has none, so book = 1, line = 0."""
    s = (TB / FILES[name]).read_text(encoding="utf8")
    out = []
    for m in re.finditer(r"<word\b([^>]*)/?>", s):
        at = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        f = norm_word(at.get("form", ""))
        if not f or not at.get("postag"): continue
        cm = re.search(r":(\d+)\.(\d+)", at.get("cite", ""))
        book, line = (int(cm.group(1)), int(cm.group(2))) if cm else (1, 0)
        out.append((f, norm_word(at.get("lemma", "")), at["postag"], book, line))
    return out

def bare_letters(form):
    return [b for b, _ in letters_with_marks(form) if b != "’"]

def nucleus_spans(form):
    lets = letters_with_marks(form); nuc = nuclei_of_word(lets, 0)
    spans, li = [], 0
    for n in nuc:
        while li < len(lets) and lets[li][0] not in "αεηιουω": li += 1
        spans.append((li, li + len(n.letters), n.nature)); li += len(n.letters)
    return [b for b, _ in lets], spans

def common_prefix(a, b):
    k = 0
    while k < len(a) and k < len(b) and a[k] == b[k]: k += 1
    return k

def build_tables(known, entries):
    """known: form -> {idx: L/S}. entries: treebank tuples. Returns (lemma_table, ending_table)."""
    by_lemma = defaultdict(set)
    ending_votes = defaultdict(lambda: defaultdict(Counter))    # (postag, ending_from_nucleus_-k) -> position -> Counter
    for form, lemma, postag, *_ in entries:
        if form in known: by_lemma[lemma].add(form)
    for form, lemma, postag, *_ in set((f, l, p) for f, l, p, *_ in entries):
        if form not in known: continue
        lets, spans = nucleus_spans(form)
        for k in (1, 2):
            if len(spans) < k: continue
            idx = len(spans) - k
            if spans[idx][2] != "?" or idx not in known[form]: continue
            ending = "".join(lets[spans[idx][0]:])
            ending_votes[(postag, ending)][-k][known[form][idx]] += 1
    return by_lemma, ending_votes

def predict(form, lemma, postag, known, by_lemma, ending_votes):
    """Return {idx: (L/S, source)} for α ι υ nuclei of form not already known."""
    lets, spans = nucleus_spans(form)
    out = {}
    have = known.get(form, {})
    for idx, (a, b, nature) in enumerate(spans):
        if nature != "?" or idx in have: continue
        votes = Counter(); src = None
        for kf in by_lemma.get(lemma, ()):
            klets, kspans = nucleus_spans(kf)
            p = common_prefix(lets, klets)
            if b <= p and idx < len(kspans) and kspans[idx][:2] == (a, b) and idx in known[kf]:
                votes[known[kf][idx]] += 1
        if votes:
            (q, n), *rest = votes.most_common()
            if not rest or n > rest[0][1]: out[idx] = (q, "lemma"); continue
        for k in (1, 2):
            if idx == len(spans) - k:
                ending = "".join(lets[a:])
                v = ending_votes.get((postag, ending), {}).get(-k)
                if v:
                    (q, n), *rest = v.most_common()
                    if n >= 2 and (not rest or n >= 3 * rest[0][1]): out[idx] = (q, "ending")
    return out

def build_extended(exclude_books=(), corpora=("iliad", "theogony", "wd", "shield")):
    known = L.build(exclude_books=exclude_books)
    iliad = [e for e in read_treebank("iliad") if e[3] not in set(exclude_books)]
    by_lemma, ending_votes = build_tables(known, iliad)
    ext = {}
    for name in corpora:
        for form, lemma, postag, *_ in set((f, l, p) for f, l, p, *_ in read_treebank(name)):
            pred = predict(form, lemma, postag, known, by_lemma, ending_votes)
            if pred: ext.setdefault(form, {}).update({i: q for i, (q, _) in pred.items()})
    return known, ext

def validate(books=(1, 5, 9, 16, 22)):
    """Precision of lemma/ending predictions on held-out books, judged by Chamberlain's certain lengths."""
    tot = Counter(); correct = Counter()
    for b in books:
        known_other = L.build(exclude_books=[b]); truth = L.build()      # truth includes book b
        iliad = read_treebank("iliad")
        by_lemma, ending_votes = build_tables(known_other, [e for e in iliad if e[3] != b])
        for form, lemma, postag, bk, ln in set(iliad):
            if bk != b or form in known_other or form not in truth: continue
            for idx, (q, src) in predict(form, lemma, postag, known_other, by_lemma, ending_votes).items():
                if idx in truth[form]:
                    tot[src] += 1; correct[src] += (q == truth[form][idx])
        print(f"book {b}: {dict(tot)}", file=sys.stderr)
    for src in tot: print(f"{src}: {tot[src]} predictions on held-out forms, precision {100*correct[src]/tot[src]:.1f} %")
    return tot, correct

def main():
    known, ext = build_extended()
    with (ROOT / "prosody/lexicon_lemma.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["word", "nucleus", "length"])
        for form in sorted(ext):
            for idx, q in sorted(ext[form].items()): w.writerow([form, idx, q])
    print(f"extended lexicon: {len(ext)} forms, {sum(len(v) for v in ext.values())} slots -> prosody/lexicon_lemma.csv")

if __name__ == "__main__":
    if "--validate" in sys.argv: validate()
    else: main()
