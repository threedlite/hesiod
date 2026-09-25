# Phase 6: Hesiod phones

Date: 2026-09-23. Code: `greek2ipa/from_text.py` (text → scanner → syllables →
`phonemize_word`, the same function as the Iliad path), `scripts/parse_hesiod.py`,
`scripts/render_hesiod_phones.py`. Output: `data/hesiod/lines.csv`,
`data/hesiod/phones.csv` (same columns as the Iliad table).

## Text

Perseus TEI tlg0020, Greek text only, apparatus notes and editorial marks removed,
normalized like the Iliad transcripts (NFC, one apostrophe form, space after elision).

| Work | Lines | Note |
|---|---|---|
| Theogony | 1,042 | includes 929a–929t, the interpolated lines Perseus prints |
| Works and Days | 831 | |
| Shield | 479 | |

## Rendering

| | |
|---|---|
| Lines rendered | 2,352 of 2,352 (the 14 once-unscannable lines were recovered by extending synizesis; Phase 5 report) |
| Syllables | 36,606 |
| Phones outside the training inventory | none |
| Training phones unused by Hesiod | ɔːu only |
| α ι υ resolved by the lexicon (form + lemma/ending extension) | 1,533 (4.2 % of syllables) |
| α ι υ still unknown, default short | 2,032 position-ambiguous (5.6 %) + 35 line-final (0.1 %) |

Lexicon coverage of Hesiod: 3,650 of 6,741 word types (54.1 %), 7,154 of
16,193 tokens (44.2 %), after the lemma/ending extension described in the Phase 5
report. The Iliad table was re-rendered the same way: unknown-length syllables
fell from 8.4 % + 1.4 % to 5.5 % + 0.1 %.

## What this means for synthesis

Because the phone inventory is identical and the rules are shared, any model
trained on the Iliad phones can be fed the Hesiod phones directly. The residual
risk is the 5.7 % of α ι υ defaulting to short; a wrong default lengthens or
shortens a vowel the meter has already fixed as a long *syllable*, so rhythm is
unaffected and only vowel quality/length within a heavy syllable can be off.
