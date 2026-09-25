# Phase 7: Hesiod synthesis, QC and package

Date: 2026-09-24. Model `train/runs/fs2_full/best.pt` (Phase 4). Script
`scripts/synth_hesiod.py`. Output directory `data/synth/hesiod_fs2_full/`.

## Package

`data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_fs2_full.zip` (147 MB), the
Classics Viewer layout with the app's own title strings:

| Path | Files |
|---|---|
| `Hesiod/Theogony/book_1/line_N.mp4` | 1,022 |
| `Hesiod/Works and Days/book_1/line_N.mp4` | 827 |
| `Hesiod/Shield of Heracles/book_1/line_N.mp4` | 479 |

AAC-LC, mono, 44.1 kHz, 96 kb/s, matching the Iliad package. Import through
Settings → Manage Audio like the Iliad package (`AUDIO_PACKAGES_INFO.md` in
`classicsviewer/audio`).

Not in the package:
- 24 lettered lines (Theogony 929a–t, Works and Days 169a–d): synthesized
  (`wav/tlg001_929a.wav` etc.) but the app stores them all under the integer line
  number, so only the unlettered line is addressable.
- (Update 2026-09-24: the 14 lines the scanner could not scan were recovered and added; the package now has 2,328 files and no gaps other than the lettered lines.)

## Lettered-line packages (for a modified app)

`--lettered` keeps the letter suffix in the file name (`line_929a.mp4`,
`line_169d.mp4`): `hesiod_chamberlain_tts_fs2_full_lettered.zip` and
`hesiod_chamberlain_tts_female_lettered.zip`, 2,352 files each, every line of all
three works. The current app cannot import them: `AudioImportWorker` takes the
text after `line_` as an integer, and `audio_mappings.line_number` is INTEGER.
To use them the app would need the line number kept as text there and in the
text viewer's lookup, or a separate suffix column. The unlettered packages
remain the ones to import today.

## QC (automatic, `reports/hesiod_qc_fs2_full.md`)

| | |
|---|---|
| Lines synthesized | 2,338 (+14 recovered later, 2,352) |
| Corpus PER (recognizer) | 3.14 % (real Iliad audio: 3.22 %) |
| Median line / p95 | 2.86 % / 9.09 % |
| Lines above the 10 % per-line threshold after four duration-scale retries | 31 (1.33 %); none above 20 % |
| Package gate (< 1 %) | **not met by 8 lines**; package produced anyway, the 31 lines are listed in `notes/human_qa_queue.md` |

Per work: Theogony 2.92 % (9 flagged), Works and Days 3.49 % (12), Shield 3.01 %
(10). Flagged lines are mostly name catalogues and lines with rare consonant
clusters; part of their PER is the recognizer's own uncertainty on rare
sequences, which cannot be separated without real Hesiod audio.

## What the output is

Product A (`notes/decisions.md`): a Chamberlain-style reading. Quantity is
realized as in his Iliad (long : short vowel ratio 2.08), pitch accent at his
conservative level (acute about 2.3 semitones above unaccented syllables,
circumflex rise-fall, grave flat), his vowel qualities (ει as a diphthong, ω
close, weak aspiration). Vowel length for the 5.7 % of α ι υ the meter and lexicon
could not fix defaults to short (Phase 6 report); this affects vowel quality
inside heavy syllables only, not rhythm.

## Left for a listener

`notes/human_qa_queue.md`: the 31 flagged Hesiod lines, the 14 unscanned lines,
the Iliad test passage in `data/synth/fs2_full/test_pred/` for a side-by-side with
the original, and the speaker-profile inferences from Phase 3.
