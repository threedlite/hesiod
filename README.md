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
from the trained model's output. The packages are
`data/synth/<corpus>_fs2_full/<corpus>_chamberlain_tts_female.zip`; the folder
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
`reports/phase9_hymns.md`, `reports/phase10_corpora.md`.

## What is here

| Path | Contents |
|---|---|
| `PROJECT_PLAN.md` | the plan, with status per phase |
| `reports/` | one report per phase: corpus reconciliation, phones, alignment and prosody baseline, scanner, Hesiod phones, TTS, Hesiod QC, female voice, Homeric Hymns, the other poets; one QC report per corpus |
| `notes/decisions.md`, `notes/human_qa_queue.md` | decisions with their evidence; what only a listener can settle |
| `scripts/` | corpus QC, hypotactic parsing, transcript cleanup, split, MFA corpus, alignment QC, prosody baseline, parse/scan/render/synthesis for every corpus (`--corpus`, registry in `corpora.py`, batch runner `run_corpora.sh`), voice conversion |
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

Environments: system Python 3 for text processing; conda env `aligner`
(Montreal Forced Aligner, parselmouth) and conda env `tts` (PyTorch, Vocos,
parselmouth) for audio. Order: `scripts/qc_iliad_audio.py`, `parse_hypotactic.py`,
`build_metadata.py`, `decode_trim.py`, `diff_transcripts.py`, `make_split.py`;
`scripts/build_lexicons.sh`; `scripts/build_mfa_corpus.py` and `align/run_align.sh`;
`train/prepare_features.py`, `train/phone_ctc.py`, `train/fs2.py train`;
`scripts/synth_hesiod.py --package`. Every other corpus runs the same three text
scripts with `--corpus <name>` and then `scripts/run_corpora.sh <name>` for synthesis,
the voice conversion and the package; `scripts/corpus_summary.py` tabulates the results.
