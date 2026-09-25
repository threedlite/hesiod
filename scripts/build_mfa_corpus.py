#!/usr/bin/env python3
"""Phase 3: build the MFA corpus and pronunciation dictionary from data/iliad/phones.csv.

Layout: align/corpus/chamberlain/<id>.wav (hard link to data/iliad/wavs) + <id>.lab.
Each word token in the .lab is <wordform>_<k>, where k indexes the distinct phone
sequence this word form received in context (final ς voicing, inferred vowel length),
so the dictionary maps every token to exactly one pronunciation. Accent suffixes
and syllable/word markers are stripped: the aligner sees phones only.
Also writes align/phones.txt (inventory) and align/word_map.csv (token -> word form, phones, count).
"""
import csv, json, os, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "align/corpus/chamberlain"
ACCENT = "ˊˋˆ"

def word_forms(detail_json):
    """Group syllables into words using the serialized detail (word boundaries were not
    stored there, so we take them from the phones string instead)."""
    raise NotImplementedError

def main():
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open())}
    overrides = {r["id"] for r in csv.DictReader((ROOT / "data/iliad/transcript_overrides.csv").open())}
    CORPUS.mkdir(parents=True, exist_ok=True)
    pron_index = defaultdict(dict)      # wordform -> {phones_tuple: k}
    token_count = Counter(); n_utt = 0; skipped = Counter()
    for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open()):
        m = meta.get(r["id"])
        if not m or m["status"] != "ok": skipped["not_ok"] += 1; continue
        if r["id"] in overrides: skipped["override_line"] += 1; continue
        if m["split"] == "test": skipped["test_split"] += 1; continue
        detail = json.loads(r["detail"])
        # words: split the phones string on '#'; syllable texts give the word form
        word_phone_groups = [g.strip() for g in r["phones"].split("#")]
        # reconstruct word forms from syllable texts in order, using the same '#' grouping:
        # count syllables per word from the number of '.'-separated groups
        sy_i, tokens = 0, []
        for g in word_phone_groups:
            n_syll = g.count(".") + 1 if g else 1
            form = "".join(d["text"] for d in detail[sy_i: sy_i + n_syll]); sy_i += n_syll
            form = unicodedata.normalize("NFC", re.sub(r"[^\w’]", "", form)).lower()
            phones = tuple(p.rstrip(ACCENT) for p in g.split() if p not in (".", "#"))
            if not phones: continue
            k = pron_index[form].setdefault(phones, len(pron_index[form]) + 1)
            tok = f"{form}_{k}"; tokens.append(tok); token_count[tok] += 1
        assert sy_i == len(detail), r["id"]
        src = ROOT / m["clean_wav"]; dst = CORPUS / f"{r['id']}.wav"
        if not dst.exists(): os.link(src, dst)
        (CORPUS / f"{r['id']}.lab").write_text(" ".join(tokens) + "\n")
        n_utt += 1
    with (ROOT / "align/dictionary.txt").open("w") as f, (ROOT / "align/word_map.csv").open("w", newline="") as g:
        w = csv.writer(g); w.writerow(["token", "wordform", "phones", "count"])
        for form, prons in sorted(pron_index.items()):
            for phones, k in sorted(prons.items(), key=lambda x: x[1]):
                tok = f"{form}_{k}"
                f.write(f"{tok}\t{' '.join(phones)}\n"); w.writerow([tok, form, " ".join(phones), token_count[tok]])
    inv = Counter(p for prons in pron_index.values() for phones in prons for p in phones)
    (ROOT / "align/phones.txt").write_text("\n".join(sorted(inv)) + "\n")
    print(f"utterances {n_utt}, skipped {dict(skipped)}")
    print(f"word forms {len(pron_index)}, dictionary entries {sum(len(v) for v in pron_index.values())}, phones {len(inv)}")
    multi = sum(1 for v in pron_index.values() if len(v) > 1)
    print(f"word forms with >1 pronunciation variant: {multi}")

if __name__ == "__main__":
    main()
