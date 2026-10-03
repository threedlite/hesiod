# Hesiod TTS

A synthesized reading of Hesiod (Theogony, Works and Days, Shield of Heracles),
the 33 Homeric Hymns, and the other hexameter poets in Perseus (Odyssey,
Apollonius, Theocritus, Moschus, Bion, Callimachus, Aratus, Quintus, both
Oppians, Nonnus, Tryphiodorus, Colluthus) in reconstructed ancient Greek
pronunciation, made by training a text-to-speech model on David Chamberlain's
line-by-line recording of the Iliad and converting its output to a female voice.

**License: CC BY-SA 4.0** for everything here (audio, package, model weights,
tables, code, documents). See `LICENSE` for the legal code and the full
attribution notice. In short, the sources are:

- David Chamberlain, *A Reading of Homer*, hypotactic.com, © 2016–2017,
  CC BY 4.0: the Iliad recordings the model is trained on and the scansion the
  lexicon is built from.
- Perseus Digital Library, canonical-greekLit, CC BY-SA 4.0: the Iliad,
  Hesiod, Homeric Hymns and the other hexameter texts (listed in `LICENSE`).
- Perseus Ancient Greek Dependency Treebank 2.0, CC BY-SA 3.0: lemma and
  morphology for the lexicon extension.
- W. S. Allen, *Vox Graeca* (3rd ed., 1987): the pronunciation rules.

Please keep the attribution notice when redistributing or adapting.

## What is read

Every hexameter poet in Perseus, in a female voice derived by signal processing
from the trained model's output. The packages and the models are published in
the **[v1.0 release](https://github.com/threedlite/hesiod/releases/tag/v1.0)**
(file list below); locally they are
`data/synth/<corpus>_fs2_full/<corpus>_chamberlain_tts_female.zip`. The folder
names inside are the app's own author and work strings. The unconverted
synthesis is an intermediate for QC and is not distributed: it is too close to
Chamberlain's own voice. Lines are the Perseus line counts; the corpus PER is the
phone recognizer's error rate on the synthesized audio (3.2 % on Chamberlain's
own recordings).

| Corpus | Author | Works | Lines | Corpus PER |
|---|---|---|---|---|
| `hesiod` | Hesiod | Theogony, Works and Days, Shield of Heracles | 2,352 | 3.15 % |
| `hymns` | Homeric Hymns | Hymns 1–33 | 2,342 | 2.91 % |
| `homer` | Homer | Odyssey, Epigrams (the Iliad is Chamberlain's own recording) | 12,216 | 2.70 % |
| `apollonius` | Apollonius Rhodius | Argonautica | 5,834 | 3.16 % |
| `theocritus` | Theocritus | Idylls (28–30, Aeolic, and the elegiac Epigrams left out) | 2,717 | 5.15 % |
| `moschus` | Moschus | Eros Drapeta, Europa, Epitaphius Bios, Megara, Fragmenta | 481 | 4.12 % |
| `bion` | Bion of Phlossa | Epitaphius Adonis, Epithalamium, Fragmenta | 246 | 4.87 % |
| `callimachus` | Callimachus | Hymns 1–4 and 6 (5 and the Epigrams are elegiac) | 941 | 3.91 % |
| `aratus` | Aratus Solensis | Phaenomena | 1,155 | 3.38 % |
| `quintus` | Quintus Smyrnaeus | Fall of Troy | 8,825 | 2.58 % |
| `oppian` | Oppian | Halieutica | 3,506 | 3.53 % |
| `oppian_apamea` | Oppian of Apamea | Cynegetica | 2,144 | 3.79 % |
| `nonnus` | Nonnus of Panopolis | Dionysiaca | 21,329 | 4.23 % |
| `tryphiodorus` | Tryphiodorus | The Taking of Ilios | 691 | 3.19 % |
| `colluthus` | Colluthus of Lycopolis | The Rape of Helen | 394 | 3.43 % |

Not in Perseus, so not read: Nicander, Euphorion, Rhianus, Antimachus,
Panyassis, Choerilus, Dionysius Periegetes, Musaeus, Gregory of Nazianzus, the
Orphica, the Sibylline Oracles. Details per corpus: `reports/phase7_hesiod.md`,
`reports/phase9_hymns.md`, `reports/phase10_corpora.md`. What it would take to
read the rest of Perseus, prose included, is in `PERSEUS_AUDIO.md`.

## The release

[v1.0: the hexameter poets](https://github.com/threedlite/hesiod/releases/tag/v1.0)
(2026-10-03, tag `v1.0`), 19 files, 4.3 GB. Packages are AAC-LC mono 44.1 kHz
96 kb/s MP4, one file per line, `<Author>/<Work>/book_N/line_N.mp4`, imported
through Settings → Manage Audio; the line count is the number of files in the
package (lettered lines such as Theogony 929a are not addressable by the app and
are left out). Every file is listed in `SHA256SUMS.txt`. Known defect: the 208
lines that fell back to no metre are garbled in this release (`PERSEUS_AUDIO.md`
§3, §4.1).

| File | Size | Contents |
|---|---|---|
| `hesiod_chamberlain_tts_female.zip` | 154 MB | Hesiod: Theogony, Works and Days, Shield of Heracles — 2,328 lines |
| `hymns_chamberlain_tts_female.zip` | 154 MB | Homeric Hymns 1–33 — 2,326 lines |
| `homer_chamberlain_tts_female.zip` | 804 MB | Homer: Odyssey, Epigrams — 12,216 lines |
| `apollonius_chamberlain_tts_female.zip` | 385 MB | Apollonius Rhodius: Argonautica — 5,832 lines |
| `theocritus_chamberlain_tts_female.zip` | 171 MB | Theocritus: Idylls — 2,593 lines |
| `moschus_chamberlain_tts_female.zip` | 32 MB | Moschus — 481 lines |
| `bion_chamberlain_tts_female.zip` | 16 MB | Bion of Phlossa — 246 lines |
| `callimachus_chamberlain_tts_female.zip` | 62 MB | Callimachus: Hymns 1–4 and 6 — 940 lines |
| `aratus_chamberlain_tts_female.zip` | 76 MB | Aratus: Phaenomena — 1,154 lines |
| `quintus_chamberlain_tts_female.zip` | 584 MB | Quintus Smyrnaeus: Fall of Troy — 8,770 lines |
| `oppian_chamberlain_tts_female.zip` | 233 MB | Oppian: Halieutica — 3,506 lines |
| `oppian_apamea_chamberlain_tts_female.zip` | 143 MB | Oppian of Apamea: Cynegetica — 2,144 lines |
| `nonnus_chamberlain_tts_female.zip` | 1,459 MB | Nonnus of Panopolis: Dionysiaca — 21,325 lines |
| `tryphiodorus_chamberlain_tts_female.zip` | 47 MB | Tryphiodorus: The Taking of Ilios — 691 lines |
| `colluthus_chamberlain_tts_female.zip` | 27 MB | Colluthus of Lycopolis: The Rape of Helen — 394 lines |
| `fs2_full_model.tar.gz` | 162 MB | the acoustic model `best.pt` with its `config.json`; unpack into `train/runs/fs2_full/` for `train/fs2.py synth` and `scripts/synth_hesiod.py` |
| `phone_ctc.pt` | 13 MB | the phone recognizer used for QC; goes in `train/checkpoints/` for `train/recognize.py` |
| `chamberlain_acoustic.zip` | 61 MB | the Montreal Forced Aligner acoustic model; goes in `align/` for `align/run_align.sh align` |
| `SHA256SUMS.txt` | 2 KB | SHA-256 of the 18 files above |

Not released: the unconverted synthesis (too close to Chamberlain's own voice),
the `_lettered` package variants, and the pretrained Vocos vocoder
(`charactr/vocos-mel-24khz`), which the code downloads.

`scripts/fetch_release.sh` downloads from the release into the places the code
expects, checking every file against `SHA256SUMS.txt`:

```
bash scripts/fetch_release.sh --list            # what is available
bash scripts/fetch_release.sh hesiod hymns      # packages by corpus name -> data/synth/<corpus>_fs2_full/
bash scripts/fetch_release.sh models            # best.pt + config.json -> train/runs/fs2_full/, phone_ctc.pt -> train/checkpoints/,
                                                # chamberlain_acoustic.zip -> align/
bash scripts/fetch_release.sh all               # everything, 4.3 GB
```

Re-running skips what is already in place; `--verify` re-checks files in place
against the checksums (the model tarball is re-fetched, since the checksum is of
the archive). `HESIOD_RELEASE`, `HESIOD_RELEASE_REPO` and `HESIOD_RELEASE_DEST`
select another tag, repository or destination root.

## What is here

| Path | Contents |
|---|---|
| `PROJECT_PLAN.md` | the plan, with status per phase |
| `PERSEUS_AUDIO.md` | what reading all the Greek in Perseus would take: inventory, a probe of the model outside the hexameter, prose, voices, scale, order of work |
| `reports/` | one report per phase: corpus reconciliation, phones, alignment and prosody baseline, scanner, Hesiod phones, TTS, Hesiod QC, female voice, Homeric Hymns, the other poets; one QC report per corpus |
| `notes/decisions.md`, `notes/human_qa_queue.md` | decisions with their evidence; what only a listener can settle |
| `scripts/` | corpus QC, hypotactic parsing, transcript cleanup, split, MFA corpus, alignment QC, prosody baseline, parse/scan/render/synthesis for every corpus (`--corpus`, registry in `corpora.py`, batch runner `run_corpora.sh`), voice conversion; `probe_non_hexameter.py` and `voice_sphere.py` for `PERSEUS_AUDIO.md` |
| `greek2ipa/` | Allen-based phonemization from Chamberlain's syllable spans (`from_spans.py`) and from plain text via the scanner (`from_text.py`) |
| `prosody/` | hexameter scanner, vowel-length lexicon and its lemma/ending extension |
| `train/` | feature preparation, the acoustic model (`fs2.py`), the phone recognizer used for QC (`phone_ctc.py`, `recognize.py`), evaluation |
| `align/` | Montreal Forced Aligner runner, dictionary, acoustic model |
| `data/<corpus>/`, `data/iliad/` | line tables, phone tables, metadata per corpus (`scripts/corpora.py` lists them; audio and features are not in git) |
| `data/synth/<corpus>_fs2_full/` | the Classics Viewer package (`*_female.zip`) per corpus, with the unconverted intermediate audio and QC tables |

## Method in one paragraph

Chamberlain's 15,632 usable Iliad lines (23 h) were trimmed, transcribed from his
own reading pages, and phonemized with W. S. Allen's *Vox Graeca* rules, taking
syllable quantity from his scansion. Montreal Forced Aligner, trained from scratch,
gave phone durations and an alignment-based check of every transcript. A
FastSpeech2-style acoustic model with explicit duration, pitch and energy
predictors and phone + quantity + accent + foot inputs was trained on the Apple GPU,
with the pretrained Vocos vocoder. For Hesiod, a hexameter scanner (98.4 % agreement
with Chamberlain on the Iliad) and a vowel-length lexicon derived from his data
supply quantities and vowel lengths from the Perseus text. Quality is measured
without a listener by a phone recognizer trained on the same corpus: the synthesized
audio scores 2.4 % phone error rate on unseen Iliad lines, 3.1 % on Hesiod,
2.9 % on the Homeric Hymns and 2.7 % on the Odyssey, against 3.2 % for the real
recordings; the Doric bucolic poets score worst at about 5 %.

## Reproducing

To use the released models and packages without rebuilding anything:
`bash scripts/fetch_release.sh models` (and any corpora wanted); the steps below
regenerate them from the sources.

Environments: system Python 3 for text processing; conda env `aligner`
(Montreal Forced Aligner, parselmouth) and conda env `tts` (PyTorch, Vocos,
parselmouth) for audio. Order: `scripts/qc_iliad_audio.py`, `parse_hypotactic.py`,
`build_metadata.py`, `decode_trim.py`, `diff_transcripts.py`, `make_split.py`;
`scripts/build_lexicons.sh`; `scripts/build_mfa_corpus.py` and `align/run_align.sh`;
`train/prepare_features.py`, `train/phone_ctc.py`, `train/fs2.py train`;
`scripts/synth_hesiod.py --package`. Every other corpus runs the same three text
scripts with `--corpus <name>` and then `scripts/run_corpora.sh <name>` for synthesis,
the voice conversion and the package; `scripts/corpus_summary.py` tabulates the results.
