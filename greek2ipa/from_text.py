"""Greek text -> phones via the scanner (Track H, Phase 6).

Uses prosody.scanner to get nuclei and quantities, builds one syllable per nucleus
(onset-maximal: a single consonant goes to the next syllable, of a cluster the first
consonant closes the preceding syllable), then runs the same phonemize_word() as the
Iliad path so the two corpora share one phone inventory and one set of rules.
"""
import re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from greek2ipa.from_spans import Syll, Word, phonemize_word, serialize
from greek2ipa.rules import letters_with_marks, VOWELS, CLUSTER_LETTERS
from prosody.scanner import scan_line, words_of

def syllabify_word(word_text, n_nuclei, merged_pairs):
    """Split a word (NFC string) into n_nuclei syllable strings following the nucleus grouping used by the scanner.
    merged_pairs: set of nucleus indices (in this word) that were merged by synizesis with the following nucleus."""
    s = unicodedata.normalize("NFD", word_text)
    # positions of vowel letters in the NFD string
    chars = list(s)
    is_v = [unicodedata.category(c) == "Ll" and unicodedata.normalize("NFD", c) in "αεηιουω" or (c.lower() in "αεηιουω") for c in chars]
    # group vowel letters into nuclei as the scanner does: reuse scanner grouping by re-deriving from letters
    from prosody.scanner import nuclei_of_word
    lets = letters_with_marks(word_text)
    nuc = nuclei_of_word(lets, 0)
    # map each nucleus to the span of letter indices (in `lets`) it covers
    spans, li = [], 0
    for n in nuc:
        while li < len(lets) and lets[li][0] not in VOWELS: li += 1
        start = li; li += len(n.letters); spans.append((start, li))
    # apply synizesis merges
    for k in sorted(merged_pairs, reverse=True):
        if k + 1 < len(spans): spans[k] = (spans[k][0], spans[k + 1][1]); del spans[k + 1]
    # syllable boundaries between consecutive nuclei
    bounds = [0]
    for a, b in zip(spans, spans[1:]):
        cons = [i for i in range(a[1], b[0]) if lets[i][0] not in ("’",)]
        if len(cons) <= 1: cut = a[1]                     # 0 or 1 consonant -> all to the next syllable
        else: cut = cons[1]                               # first consonant closes the preceding syllable
        bounds.append(cut)
    bounds.append(len(lets))
    # rebuild strings from the original NFC characters: letters_with_marks drops punctuation, so we
    # reconstruct by walking the NFD string and keeping marks with their base letter
    out, li, cur = [], 0, ""
    i = 0
    pieces = []  # per letter index: the NFD substring (base + marks) or punctuation attached to previous
    for c in s:
        cat = unicodedata.category(c)
        if cat.startswith("M"): pieces[-1] += c if pieces else c
        elif c in "’'ʼ" or cat[0] == "L": pieces.append(c)
        else:
            if pieces: pieces[-1] += c
    assert len(pieces) == len(lets), (word_text, len(pieces), len(lets))
    for k in range(len(bounds) - 1):
        out.append(unicodedata.normalize("NFC", "".join(pieces[bounds[k]: bounds[k + 1]])))
    return out

def convert_text(text, lexicon=None, scan=None):
    scan = scan or scan_line(text, lexicon)
    if not scan.ok: return None, scan
    ws = words_of(text)
    words, k = [], 0
    for wi, w in enumerate(ws):
        nuc = [n for n in scan.nuclei if n.word == wi]
        if not nuc: continue                                  # elided consonant-only word: attach to next word's onset
        merged = {n.idx_in_word for n in nuc if "synizesis" in n.flags}
        sylls_text = syllabify_word(w, len(nuc), merged)
        assert len(sylls_text) == len(nuc), (w, sylls_text, [n.text for n in nuc])
        sylls = [Syll(text=t, q=n.q, foot=n.foot, hemi=0) for t, n in zip(sylls_text, nuc)]
        # consonant-only words before this one (δ’, τ’) become the onset context: prepend to the first syllable
        j = wi - 1
        while j >= 0 and not any(n.word == j for n in scan.nuclei):
            sylls[0].text = ws[j] + sylls[0].text; j -= 1
        words.append(sylls)
    out = []
    for wi, sy in enumerate(words):
        nxt = None
        if wi + 1 < len(words):
            nxt = [(b, m) for b, m in letters_with_marks("".join(s.text for s in words[wi + 1])) if b != "’"]
        elided = phonemize_word(sy, nxt, line_final=(wi + 1 == len(words)), lexicon=lexicon)
        out.append(Word(sylls=sy, elided=elided))
    return out, scan

if __name__ == "__main__":
    from prosody import lexicon as L
    lex = L.load_all(Path(__file__).resolve().parents[1])
    for t in sys.argv[1:]:
        words, scan = convert_text(t, lex)
        print(scan.pattern, scan.flags); print(" ", serialize(words) if words else "NO SCAN")
