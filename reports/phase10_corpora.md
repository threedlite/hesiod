# Phase 10: the other hexameter poets in Perseus

Date: 2026-09-25. Same model (`fs2_full`), scanner, lexicons, phonemizer,
recognizer and female-voice setting as Phases 7–9; nothing retrained. Code:
`scripts/corpora.py` (registry), the `book` column through
`parse_hesiod.py` / `scan_hesiod.py` / `render_hesiod_phones.py` /
`synth_hesiod.py`, `scripts/run_corpora.sh` (one corpus end to end),
`scripts/corpus_summary.py` (this report's results table).

## What was included

`others.txt` names the hexameter authors in Perseus. All of them are in the
local canonical-greekLit checkout and in the app's database
(`perseus_texts_full.db`), whose `authors.name` and `works.title` strings and
`books.book_number` are used verbatim for the package layout
`<Author>/<Work>/book_<N>/line_<n>.mp4`.

| Corpus | Author | Works (app titles) | Lines | Books | Left out |
|---|---|---|---|---|---|
| colluthus | Colluthus of Lycopolis | The Rape of Helen | 394 | 1 | |
| tryphiodorus | Tryphiodorus | The Taking of Ilios | 691 | 1 | |
| bion | Bion of Phlossa | Epitaphius Adonis; Epithalamium Achillis et Deidameiae; Fragmenta | 246 | 1; 1; 16 | |
| moschus | Moschus | Eros Drapeta; Europa; Epitaphius Bios; Megara; Fragmenta | 481 | 1 ×4; 4 | |
| callimachus | Callimachus | Hymn to Zeus, to Apollo, to Artemis, to Delos, to Demeter | 941 | 1 each | Hymn to Athena (elegiac); Epigrams (elegiac) |
| aratus | Aratus Solensis | Phaenomena | 1,155 | 1 | |
| theocritus | Theocritus | Εἰδύλλια | 2,717 | 30 | Idylls 28–30 (Aeolic); Ἐπιγράμματα (elegiac) |
| oppian_apamea | Oppian of Apamea | Cynegetica | 2,144 | 4 | |
| oppian | Oppian | Halieutica | 3,506 | 5 | |
| apollonius | Apollonius Rhodius | Argonautica | 5,834 | 4 | |
| quintus | Quintus Smyrnaeus | Fall of Troy | 8,825 | 14 | |
| homer | Homer | Odyssey; Epigrams | 12,216 | 24; 17 | Iliad (the app has Chamberlain's recording) |
| nonnus | Nonnus of Panopolis | Dionysiaca | 21,329 | 48 | |
| **total** | | | **60,479** | | |

Not in Perseus and therefore not done: Nicander, Euphorion, Rhianus,
Antimachus, Panyassis, Choerilus, Dionysius Periegetes, Musaeus, Gregory of
Nazianzus, the Orphica, the Sibylline Oracles. First1KGreek is not checked out
locally.

## Text stage

The Phase 9 parser with four additions: books from `<div subtype="book|poem|epigram" n>`,
parentheses and quotation marks dropped (Callimachus, Theocritus), the koronis
read as the elision apostrophe (Bion, Homer Epigrams), and the seven printed
digammas (Argonautica 1.298 etc., Nonnus 17.7) dropped as silent with the hiatus
kept, because the training inventory has no [w]. Callimachus is read from the
`perseus-grc3` edition, the one the app holds.

| Corpus | Lines | Scan as hexameter | Unmetrical (fallback) | Dropped | Lexicon coverage (tokens) | α ι υ unresolved |
|---|---|---|---|---|---|---|
| colluthus | 394 | 390 | 4 | | 30.6 % | |
| tryphiodorus | 691 | 688 | 3 | | 29.7 % | |
| bion | 246 | 243 | 3 | | 23.1 % | |
| moschus | 481 | 480 | 1 | | 25.8 % | |
| callimachus | 941 | 935 | 6 | 1 empty line | 24.8 % | |
| aratus | 1,155 | 1,151 | 4 | | 26.2 % | |
| theocritus | 2,717 | 2,618 | 99 (Doric forms, Idyll 15 above all) | Idylls 28–30 (97 lines); 3 empty | 22.6 % | |
| oppian_apamea | 2,144 | 2,134 | 10 | | 27.1 % | |
| oppian | 3,506 | 3,501 | 5 | | 26.3 % | |
| apollonius | 5,834 | 5,828 | 6 | | 31.2 % | |
| quintus | 8,825 | 8,784 | 41 | 21 empty lines | 37.9 % | |
| homer | 12,216 | 12,189 | 27 | | 36.2 % | |
| nonnus | 21,329 | 21,256 | 73 | | 22.4 % | |

Every phone is in the training inventory. Lexicon coverage falls with distance
from Homer (Hesiod was 44 %); the meter and the accent rules still decide most
α ι υ. The scanner's unmetrical detector has false negatives: Idyll 29
(Aeolic) scanned as hexameter line by line and is excluded by name in
`corpora.py`; the elegiac pentameters inside Idyll 8 are not caught either and
are read as if hexameter.

Non-integer line numbers (`41_43`, `66b`, `142a`, `74_75`: Theocritus, Aratus,
Apollonius, Quintus, Nonnus) are synthesized but only the `_lettered` packages
carry them, as for Hesiod 929a–t.

## Synthesis, QC, packages

`scripts/run_corpora.sh <corpus>`: synthesis with four duration-scale retries,
recognizer PER per line, the male package, the female conversion (+7 st, +14 %
formants, Phase 8), its package, `_lettered` variants where needed, and the
Phase 8 acoustic checks (a 600-line sample for corpora above 3,000 lines). Each
WAV is encoded once to MP4 and hard-linked into every package that needs it.
Rate on the M4: about 1.7 lines per second all in (Colluthus 394 lines in 3.8
min).

Batch of 2026-09-25, 05:07–11:56 on the M4 (6 h 49 min for the 13 corpora,
60,479 lines, no failures). `scripts/corpus_summary.py`, all corpora including
Phases 7 and 9 for comparison:

| Corpus | Author | Lines | Synthesized | Unmetrical | Corpus PER | Median / p95 | > 10 % | Package files | Zips (MB) | Female F0 | Female PER |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hesiod | Hesiod | 2,352 | 2,352 | 0 | 3.15 % | 2.86 / 9.09 | 33 (1.40 %) | 2,328 | 308 | 136 → 206 Hz | 11.3 % |
| hymns | Homeric Hymns | 2,342 | 2,342 | 5 | 2.91 % | 2.86 / 8.57 | 31 (1.32 %) | 2,326 | 308 | 135 → 205 Hz | 11.2 % |
| colluthus | Colluthus of Lycopolis | 394 | 394 | 4 | 3.43 % | 2.94 / 9.19 | 9 (2.28 %) | 394 | 54 | 134 → 205 Hz | 11.6 % |
| tryphiodorus | Tryphiodorus | 691 | 691 | 3 | 3.19 % | 2.94 / 8.70 | 7 (1.01 %) | 691 | 93 | 136 → 207 Hz | 11.5 % |
| bion | Bion of Phlossa | 246 | 246 | 3 | 4.87 % | 3.45 / 9.92 | 11 (4.47 %) | 246 | 33 | 137 → 209 Hz | 13.3 % |
| moschus | Moschus | 481 | 481 | 1 | 4.12 % | 3.03 / 9.68 | 17 (3.53 %) | 481 | 64 | 137 → 208 Hz | 12.3 % |
| callimachus | Callimachus | 941 | 940 | 6 | 3.91 % | 3.03 / 9.09 | 24 (2.55 %) | 940 | 124 | 137 → 207 Hz | 12.3 % |
| aratus | Aratus Solensis | 1,155 | 1,155 | 4 | 3.38 % | 2.94 / 9.09 | 21 (1.82 %) | 1,154 | 152 | 136 → 206 Hz | 11.4 % |
| theocritus | Theocritus | 2,717 | 2,617 | 99 (+97 in non-hexameter books) | 5.15 % | 5.26 / 11.11 | 163 (6.23 %) | 2,593 | 341 | 137 → 207 Hz | 13.3 % |
| oppian_apamea | Oppian of Apamea | 2,144 | 2,144 | 10 | 3.79 % | 3.03 / 9.09 | 47 (2.19 %) | 2,144 | 285 | 137 → 208 Hz | 12.0 % |
| oppian | Oppian | 3,506 | 3,506 | 5 | 3.53 % | 2.94 / 9.09 | 61 (1.74 %) | 3,506 | 465 | 138 → 208 Hz | 12.2 % |
| apollonius | Apollonius Rhodius | 5,834 | 5,834 | 6 | 3.16 % | 2.94 / 8.82 | 69 (1.18 %) | 5,832 | 768 | 137 → 207 Hz | 11.7 % |
| quintus | Quintus Smyrnaeus | 8,825 | 8,804 | 41 | 2.58 % | 2.78 / 8.33 | 63 (0.72 %) | 8,770 | 1166 | 137 → 207 Hz | 11.4 % |
| homer | Homer | 12,216 | 12,216 | 27 | 2.70 % | 2.78 / 8.57 | 130 (1.06 %) | 12,216 | 1605 | 135 → 205 Hz | 10.8 % |
| nonnus | Nonnus of Panopolis | 21,329 | 21,329 | 73 | 4.23 % | 3.03 / 9.38 | 643 (3.01 %) | 21,325 | 2908 | 137 → 208 Hz | 13.1 % |
| **all** | | 65,173 | 65,051 | | 3.48 % | | 1329 (2.04 %) | 64,946 | 8673 | | |

"Lines" counts the TEI lines; "Synthesized" excludes empty lines and dropped
books; "Package files" excludes non-integer line numbers, which the `_lettered`
variants carry; "Zips" is the male plus the female package; "Female PER" is the
male-trained recognizer on the converted audio (Phase 8: relative guard only).

What the table shows:

- **The archaic and Homeric-style epics score like Hesiod or better.** The
  Odyssey (2.70 %) and Quintus (2.58 %, the only corpus under the 1 % gate) are
  the closest to the training text in vocabulary and formula; Apollonius,
  Aratus, Tryphiodorus, Colluthus and both Oppians sit at 3.2–3.8 %.
- **Dialect costs about two points.** The Doric bucolics are the worst:
  Theocritus 5.15 % with 6.2 % of lines flagged (median line 5.3 %, twice
  everyone else's), Bion 4.87 %, Moschus 4.12 %. The rules are Ionic-epic and
  the recognizer never heard Doric forms, so part of this is the instrument.
- **Nonnus is in between** (4.23 %, 3.0 % flagged, 643 lines): late vocabulary
  and dense proper names, the same pattern as the Theogony's catalogues, at
  21,000 lines.
- The female conversion behaves identically everywhere (F0 135–138 → 205–209 Hz,
  PER 10.8–13.3 %).

Peculiarities of the texts, all carried through as printed: each of the 48 books of
Nonnus' Dionysiaca opens with a summary verse numbered 0 (`line_0.mp4`, which
the app will not address); 25 lines are empty in Perseus (Quintus 21, Theocritus 3,
Callimachus 1) and have no audio; the Homer Epigrams are 17 short poems, one
per `book_N/`.

The flagged share (> 10 % PER after retries) is reported per corpus, not
enforced: it rises with distance from the training text and with proper names.
The worst 40 lines of each corpus are in `notes/human_qa_queue.md`; all are in
`data/synth/<corpus>_fs2_full/per.csv`.

## Packages

`data/synth/<corpus>_fs2_full/<corpus>_chamberlain_tts_fs2_full.zip` and
`<corpus>_chamberlain_tts_female.zip`, AAC-LC mono 44.1 kHz 96 kb/s, importable
through Settings → Manage Audio one at a time. Theocritus' package uses the
app's Greek title `Εἰδύλλια` as the folder name (UTF-8 zip entries); whether
the importer matches it is an open item for the device test.

## Left for a listener

The per-corpus QA-queue sections; a female/male pair per corpus
(`data/synth/<corpus>_fs2_full_female/wav/` vs `<corpus>_fs2_full/wav/`);
the Doric idylls of Theocritus (the pronunciation rules are Ionic-epic);
Nonnus' name-heavy catalogues.
