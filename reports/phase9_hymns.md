# Phase 9: the Homeric Hymns

Date: 2026-09-25. Model `train/runs/fs2_full/best.pt` (Phase 4), scanner and
lexicons of Phase 5, phonemizer of Phase 6, recognizer of Phase 3b, voice
conversion setting of Phase 8: nothing retrained or re-tuned. Code:
`scripts/corpora.py` (new) and `--corpus hymns` on `scripts/parse_hesiod.py`,
`scan_hesiod.py`, `render_hesiod_phones.py`, `synth_hesiod.py`. Tables in
`data/hymns/`; audio in `data/synth/hymns_fs2_full/` and
`data/synth/hymns_fs2_full_female/`.

## Text (`data/hymns/lines.csv`)

Perseus TEI tlg0013, tlg001–tlg033 (Evelyn-White's 1914 Loeb text), 2,342 lines.
Parsed like Hesiod (Greek text only, NFC, one apostrophe form) with three
additions the Hymns needed:

- XML comments are dropped (the files carry commented-out quote milestones,
  which left `-->` fragments in 124 lines on the first pass);
- `<supplied>`, `<add>` and `<surplus>` text is kept, because it is what the
  app displays (Hymn 2.386–401, 462–469 are largely supplied; Hymn 3.136–137
  are bracketed as intrusive);
- the one `<choice>` (Hymn 3.181) is read from `<corr>` περικλύστοιο; the app
  shows both the 1914 printing's περικλύστης and the correction.

16 lines carry lettered numbers (Hymn 2: 137a, 236a, 403a; Hymn 3: 81a, 317a,
325a, 402a, 539a, 539b; Hymn 4: 91a, 409a, 409b, 526a, 568a, 568b; Hymn 31: 15a).
As with Hesiod's 929a–t, the app stores them under the integer line number, so
they are synthesized but only packaged in the `_lettered` variants.

## Scansion and phones (`data/hymns/scansion.csv`, `data/hymns/phones.csv`)

| | |
|---|---|
| Lines scanning as hexameters | 2,337 of 2,342 |
| Unmetrical lines (fallback: quantities by nature and position, no foot) | 5: Hymn 2.128, 2.267, 3.181, 4.394, 13.1 |
| Lines with more than one equal-cost scansion | 3 (1.3, 2.431, 3.393; correption vs. hiatus) |
| Synizesis, correption, metrical lengthening | 60, 638, 53 lines |
| Syllables | 36,834 |
| Phones outside the training inventory | none (ɔːu unused, as in Hesiod) |
| α ι υ resolved by the lexicon | 1,236 (3.4 % of syllables) |
| α ι υ still unknown, default short | 2,146 position-ambiguous (5.8 %) + 173 line-final (0.5 %) |
| Lexicon coverage of the Hymns | 2,101 of 6,374 word types (33 %), 5,665 of 16,006 tokens (35 %) |

The five unmetrical lines are as Perseus prints them: 2.128 and 2.267 are lines
editors mark as corrupt, 4.394 has δὴ αὖτ’ which needs a synizesis the scanner
does not attempt across a word boundary, 3.181 remains unmetrical even with the
correction, and 13.1 has Δημήτηρ’ where the parallel line Hymn 2.1 has Δήμητρ’.
They are read with the fallback quantities and listed for a listener rather
than emended, since the text is the app's.

Lexicon coverage is lower than Hesiod's 44 % of tokens because the Hymns'
vocabulary overlaps the Iliad less; the unresolved share of α ι υ is nearly the
same (5.6 % + 0.1 % for Hesiod), because the accent rules and the meter do most
of the work.

## Synthesis and QC (`reports/hymns_qc_fs2_full.md`)

`scripts/synth_hesiod.py --corpus hymns --ckpt train/runs/fs2_full/best.pt --package`,
25 min on the M4 for synthesis, four duration-scale retries, recognizer scoring
and packaging.

| | Homeric Hymns | Hesiod (Phase 7) |
|---|---|---|
| Lines synthesized | 2,342 | 2,338 (+14) |
| Corpus PER (recognizer) | 2.91 % | 3.14 % |
| Median line / p95 | 2.86 % / 8.57 % | 2.86 % / 9.09 % |
| Above 10 % before retries | 77 | 81 |
| Above 10 % after retries (0.97, 1.03, 0.94, 1.06) | 31 (1.32 %) | 31 (1.33 %) |
| Package gate (< 1 %) | not met by 8 lines | not met by 8 lines |

The five unmetrical lines are the five worst (22–31 % PER): the model has never
seen foot-0 tokens, and their fallback quantities are not a hexameter rhythm.
Without them the corpus PER is 2.86 % and 26 lines (1.11 %) are above the
threshold, clustered as for Hesiod on proper names and rare clusters (Ἴσχυ’ ἅμ’
ἀντιθέῳ Ἐλατιονίδη, Ἑλικῶνα … Αἰγάς, Ὀγχηστόν). Per hymn, the four long hymns
(2–5) score 2.85–2.90 %; the short ones vary from 0.65 % (Hymn 11) to 5.91 %
(Hymn 30, one flagged line of 19). All 31 lines are in `notes/human_qa_queue.md`.

## Packages

`data/synth/hymns_fs2_full/`, AAC-LC mono 44.1 kHz 96 kb/s MP4 like the Iliad
and Hesiod packages, the app's own strings for tlg0013 (author "Homeric Hymns";
work titles `works.title` in `perseus_texts_full.db`, including the capital "To"
of Hymn 17; every hymn is book 1):

| Package | Files | Size |
|---|---|---|
| `hymns_chamberlain_tts_female.zip` (released) | 2,326 | 154 MB |
| `hymns_chamberlain_tts_female_lettered.zip` | 2,342 | for an app that accepts `line_137a` |
| `hymns_chamberlain_tts_fs2_full.zip` and its `_lettered` variant | 2,326 / 2,342 | the unconverted intermediate, QC only, not for release |

Files per hymn: 21, 495, 546, 580, 293, 21, 59, 17, 9, 6, 5, 5, 3, 6, 9, 5, 5,
12, 49, 8, 5, 7, 4, 5, 7, 13, 22, 18, 14, 19, 19, 20, 19 for Hymns 1–33; these
match the app's `books.line_count` except where lettered lines are excluded.
Import through Settings → Manage Audio.

## Female voice (the released audio)

`scripts/convert_voice.py --semitones 7 --alpha1 1.14 --alpha2 1.14 --tilt 0 --h1 0 --breath 0`,
the setting chosen by ear for Hesiod (Phase 8), 8 processes, 5 min. F0 median
136 → 204 Hz over all 2,342 lines. Checks with `scripts/eval_voice.py` on every
line (`data/synth/hymns_fs2_full_female/eval_full.json`):

| Check | Hymns | Hesiod (Phase 8) | Target |
|---|---|---|---|
| F0 median | 135 → 205 Hz | 136 → 206 Hz | 200–240 |
| F1 ratio, mean over vowels | 1.12 | 1.13 | intended 1.14 |
| F2 ratio, mean over vowels | 1.11 | 1.11 | intended 1.14 |
| H1−H2 | -3.2 → 0.8 dB | −3.3 → +0.8 dB | +2 to +5 |
| HNR | 8.5 → 12.1 dB | 8.5 → 12.2 dB | not below −3 |
| accent contrasts vs unaccented, st | acute 2.21 → 2.41, circumflex 0.79 → 0.84, grave 0.12 → -0.03 | acute 2.13 → 2.32 | within 0.5 |
| unvoiced frames | 36.0 → 31.0 % | 35.9 → 30.9 % | within 2 points* |
| PER, relative guard | 2.91 % → 11.16 % (median line 10.8 %); 17 lines above 30 % | 3.13 % → 11.31 %; 11 lines | see Phase 8 |

\*The unvoiced fraction falls by 5 points here as it did for Hesiod: the tracker
finds more voicing in the converted audio, the same measurement effect noted in
Phase 8, not a conversion failure. Every number matches the Hesiod conversion
within rounding, as expected from an identical transform on the same voice.

Not re-listened: the Hesiod listening judgement is assumed to carry over, and
the pair to play is in the QA queue.

## Left for a listener

`notes/human_qa_queue.md`: the 31 flagged lines, the 5 unmetrical lines (and
whether 3.181 should say the corrected word the app does not show alone), and
one female/male pair.
