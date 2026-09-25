# Hesiod TTS

A synthesized reading of Hesiod (Theogony, Works and Days, Shield of Heracles)
and of the 33 Homeric Hymns in reconstructed ancient Greek pronunciation, made by
training a text-to-speech model on David Chamberlain's line-by-line recording of
the Iliad.

**License: CC BY-SA 4.0** for everything here (audio, package, model weights,
tables, code, documents). See `LICENSE` for the legal code and the full
attribution notice. In short, the sources are:

- David Chamberlain, *A Reading of Homer*, hypotactic.com, © 2016–2017,
  CC BY 4.0: the Iliad recordings the model is trained on and the scansion the
  lexicon is built from.
- Perseus Digital Library, canonical-greekLit, CC BY-SA 4.0: the Iliad,
  Hesiod and Homeric Hymns texts.
- Perseus Ancient Greek Dependency Treebank 2.0, CC BY-SA 3.0: lemma and
  morphology for the lexicon extension.
- W. S. Allen, *Vox Graeca* (3rd ed., 1987): the pronunciation rules.

Please keep the attribution notice when redistributing or adapting.

## What is here

| Path | Contents |
|---|---|
| `PROJECT_PLAN.md` | the plan, with status per phase |
| `reports/` | one report per phase: corpus reconciliation, phones, alignment and prosody baseline, scanner, Hesiod phones, TTS, Hesiod QC, female voice, Homeric Hymns |
| `notes/decisions.md`, `notes/human_qa_queue.md` | decisions with their evidence; what only a listener can settle |
| `scripts/` | corpus QC, hypotactic parsing, transcript cleanup, split, MFA corpus, alignment QC, prosody baseline, parse/scan/render/synthesis for Hesiod and the Hymns (`--corpus`, registry in `corpora.py`), voice conversion |
| `greek2ipa/` | Allen-based phonemization from Chamberlain's syllable spans (`from_spans.py`) and from plain text via the scanner (`from_text.py`) |
| `prosody/` | hexameter scanner, vowel-length lexicon and its lemma/ending extension |
| `train/` | feature preparation, the acoustic model (`fs2.py`), the phone recognizer used for QC (`phone_ctc.py`, `recognize.py`), evaluation |
| `align/` | Montreal Forced Aligner runner, dictionary, acoustic model |
| `data/hesiod/`, `data/hymns/`, `data/iliad/` | line tables, phone tables, metadata (audio and features are not in git) |
| `data/synth/hesiod_fs2_full/`, `data/synth/hymns_fs2_full/` | the Hesiod and Homeric Hymns audio and the Classics Viewer packages (male and female voice) |

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
audio scores 2.4 % phone error rate on unseen Iliad lines, 3.1 % on Hesiod and
2.9 % on the Homeric Hymns, against 3.2 % for the real recordings.

## Reproducing

Environments: system Python 3 for text processing; conda env `aligner`
(Montreal Forced Aligner, parselmouth) and conda env `tts` (PyTorch, Vocos,
parselmouth) for audio. Order: `scripts/qc_iliad_audio.py`, `parse_hypotactic.py`,
`build_metadata.py`, `decode_trim.py`, `diff_transcripts.py`, `make_split.py`;
`scripts/build_lexicons.sh`; `scripts/build_mfa_corpus.py` and `align/run_align.sh`;
`train/prepare_features.py`, `train/phone_ctc.py`, `train/fs2.py train`;
`scripts/synth_hesiod.py --package`. The Homeric Hymns run the same four text
scripts with `--corpus hymns`, then `scripts/convert_voice.py` for the female voice.
