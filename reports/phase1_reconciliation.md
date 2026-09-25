# Phase 1: Iliad audio reconciliation

Date: 2026-09-23. Scripts: `scripts/qc_iliad_audio.py`, `scripts/parse_hypotactic.py`,
`scripts/build_metadata.py`. Outputs: `data/iliad/scan.csv`, `data/iliad/metadata.csv`,
`data/iliad/exclusions.csv`, `data/iliad/line_map*.csv`, `data/iliad/hypotactic*_lines.csv`.

## Summary

| | |
|---|---|
| Files in zip | 15,693 (the 15,719 zip entries include 26 directory entries; no extras) |
| Per-book counts vs download script | all 24 books match exactly |
| Valid audio clips | 15,664 |
| Usable for training after exclusions | 15,641 clips, 23.1 h after trimming |
| Excluded | 52 (table below) |
| Clip format | AAC-LC mono 44.1 kHz ~96 kb/s, in MP4 |
| Speech per clip | median 5.32 s, p5 4.38 s, p95 5.86 s, one outlier 12.4 s (21.427) |
| Peak level | median −9 dBFS, p5 −12, p95 −7; no quiet clips |

## Exclusions (52)

| Reason | Count | Lines |
|---|---|---|
| Not recorded (server returns 404) | 16 | 5.632, 7.138, 7.141, 7.142, 8.244, 8.252, 9.538 (=vulgate 9.542), 10.103, 10.302, 10.346, 10.348, 11.150–154 |
| No such line (index beyond Chamberlain's text) | 11 | 8.562–565, 9.710–713, 11.848, 14.522, 18.617 |
| Stub audio, under 2 s of speech | 21 | 17.245, 17.560, 17.668, 17.714, 18.64, 18.356, 18.392, 19.73, 21.368, 22.76, 22.130, 22.336, 23.236, 23.305, 23.481, 23.617, 23.626, 23.707, 24.88, 24.216, 24.227 |
| Broken MP4 (no moov atom / 262 bytes) | 2 | 20.490, 21.447 |
| Duration outlier (two lines run together, 12 s) | 1 | 21.427 |
| Stub found after trimming (0.7 s of speech, then a breath bump) | 1 | 9.188 |

The 27 "HTML" files are 404 pages that the download script's 1,000-byte size check
let through. All were re-checked against the server today and still 404. The stubs
and broken files are byte-identical to what the server serves, so they are not
download errors. None of these are worth retrying.

## Line numbering: audio index vs vulgate number

hypotactic numbers lines sequentially within its own text. Its text omits a few
vulgate lines, so after each omission the audio index runs one or more behind the
Perseus line number. `data/iliad/line_map.csv` holds the mapping, derived by
monotonic text alignment of the reading page against Perseus tlg0012.tlg001.

| Book | Chamberlain's text omits | Drift after |
|---|---|---|
| 8 | 548, 550, 551, 552 | 8.548 (4 lines) |
| 9 | 458–461 (Perseus omits these too) | 9.457 (4 lines) |
| 11 | 543 (Perseus omits too) | 11.542 (1 line) |
| 14 | 269 (Perseus omits too) | 14.268 (1 line) |
| 18 | 604 | 18.603 (1 line) |
| 19 | reading page now lacks 101–144, but audio has all 424 lines | none: audio index = vulgate number |

All other books map 1:1. The download script's "expected" counts were vulgate
counts, which is why books 8, 9, 11, 14, 18 appeared to be missing their last lines.

## Transcripts

Three witnesses per line:

- **R, reading pages** (`data/scansion/iliad/`): the text Chamberlain read from,
  in audio-index order. Primary transcript (`metadata.csv: text`). The pages have
  no whitespace between syllable spans, so the text is rebuilt from the spans'
  word indices (an early version of the parser lost the spaces, which made the
  two hypotactic versions look 1,501 lines apart; the real figure is 18).
- **S, scanned pages** (`data/scansion/iliad_scanned/`): 2026 revision, aligned
  to Perseus numbering, improved syllabification. `text_scanned`. Known defects:
  1.310 and 5.818 truncated, 13.838 an empty line, several broken `&nbsp;`
  entities (scrubbed by the parser).
- **P, Perseus** tlg0012.tlg001: used for word boundaries and as the tiebreaker.

`scripts/diff_transcripts.py` produces `text_clean` and logs every difference in
`data/iliad/transcript_diff.csv` (80 lines). Against Perseus, after normalizing
apostrophes (Perseus uses U+02BC, which Unicode classes as a letter):

| Category | Lines | Action |
|---|---|---|
| Identical letters, words and diacritics | 15,550 | none |
| Diacritics differ (δηίων/δηΐων, κληῖδι/κληῗδι, ὃ/ὁ, ’Ρ for Ῥ, capitals) | 47 | keep R; ’Ρ normalized to Ῥ |
| Word boundaries differ | 17 | 9 adopt Perseus (mid-word spaces such as "κρόμυ ον", "ἀ πὸ", "χαλκοχιτών ων"; missing spaces such as "καὶμοῖρα"); 8 keep R (-δε compounds, an edition choice) |
| Edition variants (θελ’/ἔθελ’, πόληος/πόλιος, ἱόν/υἱόν, εὐθύς/ἰθύς, σά/σύ, κεκόπων/κεκοπώς) | 6 | keep R, he read R |
| Garbled or typo on the reading page | 7 | hand repairs in `data/iliad/transcript_overrides.csv`: 2.765, 8.298, 8.303, 8.325, 18.604, 22.379, 23.2 |

Normalization applied to every `text_clean`: NFC, one apostrophe form (U+2019),
a space after each elision apostrophe so whitespace tokens are words, a stray
`*` removed (16.301), single spaces. No non-letter characters remain apart from
punctuation. Hypotactic's syllable counts per line are 12–17, as expected for
hexameter, and the two versions' counts agree on all but 20 lines.

The seven repaired lines and the six edition variants cannot be verified without
listening; they are in `notes/human_qa_queue.md`.

## Clip structure

Clips are cut from a continuous recording and padded to a fixed grid (most are
5.94, 5.97 or 6.06 s). Speech ends, then there is digital silence (below −80 dBFS),
then in many clips a small bump at −35 to −45 dBFS in the last 200 ms, which is
overhang from the next line's onset or a breath. Nothing is cut off at the end.
About 2,100 clips have speech within 40 ms of the clip start, so leading-edge
trimming must be conservative (keep everything from sample 0 when lead is short).

**The recordings are noise-gated.** Mid-line pauses, even 100–300 ms ones, drop
to digital silence, so a "first silence gap after the midpoint" rule cuts inside
lines (it shortened 3,806 clips on the first attempt). The rule that works:

- start = first 20 ms frame above −40 dBFS, minus 100 ms, clamped at 0
- end = last frame above −35 dBFS, plus 150 ms, clamped at the clip end

The −35 dBFS threshold excludes the breath/room bumps (−36 to −50 dBFS) that sit
after the final digital-silence run in about 2,400 clips; spot checks confirm the
material between −35 and −40 is never speech. Gain is set so the RMS over speech
frames is −20 dBFS, with peaks limited to −1 dBFS. Implemented in
`scripts/decode_trim.py`; per-clip log in `data/iliad/trim_log.csv`.

Result: 15,641 WAVs (22.05 kHz mono 16-bit) in `data/iliad/wavs/`, 23.1 h,
median 5.45 s, p5 4.57 s, max 6.32 s. One more clip (9.188) turned out to be a
0.7 s stub once the tail bump was excluded and is now in the exclusion list
(51 excluded in total). The shortest remaining clips (4.260 at 2.95 s, 2.551
at 3.83 s) should be checked by ear during the listening pass.

The reading pages also carry a per-line `data-speeds` array (0.9–1.10) the web
player uses to alter playback rate. The raw files are unaffected; ignore it.

## Scansion sources found

- Reading and scanned pages tag every syllable with `long/short`, `foot1–6`,
  `word#`, `hemi1/hemi2`, `footend`, `wordend`. Parsed into
  `hypotactic_lines.csv` and `hypotactic_scanned_lines.csv` (JSON per line).
- Chamberlain's CSV export of the same data: `data/scansion/iliad_csv/` (2016–17,
  one row per syllable). Superseded by the scanned pages but useful as a cross-check.
- **Hesiod**: `hypotactic.com/hesiod/` has Theogony and Works and Days readers
  (2019) with lemma, part-of-speech tag, dependency head and a gloss per word, but
  no syllable scansion, and they are licensed CC BY-NC-SA. No Shield. So Hesiod
  quantity must come from the fallback scanner in Phase 3; the readers can serve
  as a morphology cross-check but their data must not be redistributed.

## License note

The reading pages and the audio README both say CC-BY 4.0. The Hesiod readers are
CC BY-NC-SA 4.0 (different material, different license).

## Next steps

1. Done: decode, trim, normalize (`data/iliad/wavs/`).
2. Done: transcript cleanup (`text_clean`).
3. Done: split (`scripts/make_split.py`, seed 20260923): train 15,278 lines
   (22.59 h), val 311 lines (2 % per book, 0.46 h), test 52 lines (Iliad
   1.1–52, 0.07 h). Ids in `data/iliad/splits/`, `split` column in metadata.
4. Phase 2: phones from Chamberlain's spans; Phase 3: alignment, which is the
   automated check on the transcripts and the shortest clips (4.260, 2.551).
