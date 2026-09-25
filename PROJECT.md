# Hesiod TTS: full project document

As of 2026-09-25. Companion to `PROJECT_PLAN.md` (the plan, with per-phase status)
and the phase reports in `reports/`. This document is the complete, current
account of what was built, what the data turned out to contain, what the results
are, and what remains.

---

## 1. Overview

A synthesized reading of all of Hesiod (Theogony, Works and Days, Shield of
Heracles) now exists as a Classics Viewer audio package, and since 2026-09-25 so
does one of all 33 Homeric Hymns, made with the same pipeline (§8b). It was produced by a
text-to-speech model trained on David Chamberlain's line-by-line Iliad
recordings and judged by automated metrics rather than a listener. The
synthesized audio scores a 2.4 % phone error rate on unseen Iliad lines and
3.1 % on Hesiod, against 3.2 % for Chamberlain's own recordings, with his
metrical rhythm and his conservative pitch accent reproduced within tolerance.

The work ran on 2026-09-23 and 2026-09-24 on one Apple M4 laptop (32 GB), in two
parallel tracks: the Iliad audio became a training corpus and a model (Track I),
while the Hesiod text became phone strings through a hexameter scanner and a
vowel-length lexicon built from Chamberlain's own scansion (Track H).

| Deliverable | Where | Size |
|---|---|---|
| Hesiod audio package for the app (2,328 lines; female-voice package alongside) | `data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_fs2_full.zip` | 147 MB |
| Individual Hesiod WAVs (2,338 lines, 22.05 kHz) | `data/synth/hesiod_fs2_full/wav/` | |
| Homeric Hymns audio package (2,326 lines; female-voice package alongside) | `data/synth/hymns_fs2_full/hymns_chamberlain_tts_fs2_full.zip` | 154 MB |
| Individual Homeric Hymns WAVs (2,342 lines) | `data/synth/hymns_fs2_full/wav/`, `data/synth/hymns_fs2_full_female/wav/` | |
| Acoustic model | `train/runs/fs2_full/best.pt` | 176 MB |
| Phone recognizer (QA instrument) | `train/checkpoints/phone_ctc.pt` | 13 MB |
| Forced-alignment acoustic model | `align/chamberlain_acoustic.zip` | 59 MB |
| Scanner, lexicon, phonemizer | `prosody/`, `greek2ipa/` | code |
| Reports per phase | `reports/` | 12 files |

The app receives only the pre-rendered audio; the model, converter and scanner
stay offline tools.

---

## 2. Source data and licensing

| Source | What it provided | License |
|---|---|---|
| David Chamberlain, *A Reading of Homer*, hypotactic.com: `homer/audio/{book}/line_{n}.mp4` | 15,693 Iliad clips, AAC mono 44.1 kHz, 23 h | CC-BY 4.0, © 2016–2017 |
| His reading pages `homer/iliad{N}.html` | the text he read, with every syllable tagged long/short, foot, word, hemistich (audio-index order) | CC-BY 4.0 |
| His scanned pages `homer/scanned/iliad{N}scanned.html` (2026 revision) | same, aligned to Perseus numbering, better syllabification | CC-BY 4.0 |
| His 2017 CSV export `IliadAllCSV.zip` | cross-check only | CC-BY 4.0 |
| Perseus TEI (`canonical-greekLit`): tlg0012.tlg001, tlg0020.tlg001–003, tlg0013.tlg001–033 | vulgate line numbering for the Iliad; the Hesiod and Homeric Hymns texts | Perseus CC-BY-SA |
| Perseus treebanks (`treebank_data`): Iliad, Theogony, Works and Days, Shield | form, lemma, morphology tag per word, for the lexicon | CC-BY-SA |
| hypotactic Hesiod readers `hesiod/theogony.html`, `WandD.html` | lemma/gloss per word; **no scansion, no Shield** | CC BY-NC-SA: reference only, not used in any output |

Everything in this repository (audio, package, model weights, tables, code,
documents) is released under **CC BY-SA 4.0**: the Hesiod audio is a reading of
Perseus texts licensed BY-SA, and Chamberlain's BY material is compatible.
`LICENSE` carries the legal code and the full attribution notice. Voice
conversion to a different voice is optional and was not done.

### What the recordings can and cannot teach

Chamberlain describes his reading as "a tolerable effort at reconstructed
pronunciation with a very conservative pitch accent," says his stress accent
"comes through too much," and that he was "inconsistent on digamma." A model
trained on this voice reproduces his prosody; it cannot invent an accent he did
not produce. Two products were therefore defined: **Product A**, a
Chamberlain-style reading (delivered), and **Product B**, a stricter Allen
realization by post-hoc F0 shaping (not started).

---

## 3. Track I: the Iliad training corpus

### 3.1 Reconciliation (`reports/phase1_reconciliation.md`)

The zip contained exactly the expected 15,693 files. 61 lines are excluded:

| Reason | Lines |
|---|---|
| Never recorded (server 404) | 16 |
| No such line (index beyond Chamberlain's text) | 11 |
| Stub audio under 2 s | 22 |
| Broken MP4 | 2 |
| 12 s outlier (two lines run together, 21.427) | 1 |
| Forced alignment failed (Phase 3) | 9 |

**Numbering.** hypotactic numbers lines sequentially within its own text, which
omits a few vulgate lines, so the audio index drifts behind the Perseus number in
books 8 (4 lines after 8.548), 9 (4 after 9.457), 11, 14 (1 each), 18 (1 after
18.603). Book 19's reading page later lost lines 101–144 but the audio is
complete, so it maps one to one. `data/iliad/line_map.csv` holds the mapping.

**Clip structure.** Clips are padded to a fixed ~6 s grid and the recordings are
noise-gated: every mid-line pause is digital silence. The trim rule that works is
"last frame above −35 dBFS plus 150 ms" (a silence-gap rule cut inside 3,806
lines). RMS normalized to −20 dBFS. Result: 15,632 WAVs at 22.05 kHz, 23.1 h.

**Transcripts.** The text is Chamberlain's reading page (what he read), rebuilt
from the span word indices, compared word by word with his scanned page and
Perseus. 15,550 lines are identical at the letter level; 47 keep his accent
conventions, 17 take Perseus word boundaries, 6 keep his edition variants, 7
garbled lines were repaired by hand (`data/iliad/transcript_overrides.csv`).

**Split.** train 15,269 / val 311 (2 % per book, seed 20260923) / test 52 (Iliad
1.1–52, never trained on).

### 3.2 Phones from his spans (`reports/phase2_phones.md`)

`greek2ipa/from_spans.py` phonemizes with W. S. Allen's *Vox Graeca* values
(φ θ χ = pʰ tʰ kʰ; ζ = zd; σ voiced before voiced consonants, also across word
boundaries; η ω = ɛː ɔː; ει ου = eː uː; υ = y; rough breathing = h; initial ῥ =
r̥) and takes syllable quantity, accent (acute/grave/circumflex), foot and
hemistich from his spans. Length of α ι υ is inferred: short if his syllable is
short; long if it is long and open (0–1 consonants before the next vowel, counted
across the word end into the next word); otherwise unknown, default short,
flagged. 23 hand-checked tests. 40-phone inventory.

---

## 4. Alignment, prosody baseline, speaker profile (`reports/phase3_alignment_prosody.md`)

Montreal Forced Aligner 3.4.2, acoustic model trained from scratch on the corpus
(57 min, 8 cores), dictionary of 23,597 word-form pronunciations generated from
the phone table. 15,573 of 15,582 utterances aligned; the 9 failures include the
two shortest clips flagged earlier, confirming those clips do not contain their
text. The bottom 1 % by alignment score are queued for listening.

**Quantity is strongly realized.** Long syllables 367 ms vs short 220 ms (ratio
1.67, Cohen's d 1.18); long vowels about twice their short counterparts.

**Pitch accent is real but subtle** (n = 244,840 syllables, semitones relative to
the utterance median):

| Accent | mean F0 | slope within syllable | fall from peak | d(mean) vs none |
|---|---|---|---|---|
| acute | +1.58 | rising (+0.95) | 2.79 | 0.41 |
| circumflex | +0.23 | −0.29 | 4.85 | 0.09 (fall: 0.26) |
| grave | −0.17 | −0.01 | 3.04 | 0.00 |
| none | −0.16 | −0.61 | 3.64 | 0 |

The shapes are Allen's (acute rise, circumflex rise-fall, grave = unaccented),
but the effect sizes are below the 0.5 threshold, matching his self-description.
Decision: Product A first, Product B planned.

**Acoustic speaker profile** (measured, not heard): ζ has a 73 ms stop component
(a real [zd]); φ θ χ are no longer than π τ κ (aspiration weak or absent, not
fricatives); υ is front rounded (F2 1422–1855 Hz between i and u); ει has a
+299 Hz F2 glide (a diphthong [ei], not [eː]); η has the quality of ε; ω is
close [oː] and ο open [ɔ], the reverse of Allen's openness. No relabeling was
needed: labels are identifiers the model learns from his audio, so Hesiod
inherits his values.

**Phone recognizer** (Phase 3b): 80-band log-mel → 2 conv → 3-layer BiGRU → CTC
over the 40 phones, trained from scratch (8 epochs, 12 min each). Validation PER
3.22 %, test passage 4.93 %. `train/recognize.py` scores any audio against an
intended phone string and is the intelligibility instrument for everything after.

---

## 5. Track H: the Hesiod text (`reports/phase5_scanner.md`, `reports/phase6_hesiod_phones.md`)

**Scanner** (`prosody/scanner.py`). Nuclei (vowels, diphthongs), consonant counts
across the whole line for position, nature (η ω diphthongs long; ε ο short; α ι υ
from macron, lexicon, or accent rules, else unknown), then a depth-first search
over six feet with per-option costs: correption 0.5 (×3 before a digamma word),
internal correption 1.5, lexicon overrule 1.0, accent-rule overrule 1.5, metrical
lengthening of ε ο 2.0 (1.0 before λ μ ν ρ σ or a digamma stem), stop+liquid not
making position 1.0, word-initial cluster not making position 2.0, fifth-foot
spondee 1.5, synizesis 2.0 (up to two per line).

**Validation** against Chamberlain, 24-fold by book (lexicon built without the
book): 98.4 % of lines identical, 99.75 % where the syllable counts agree; most
remaining mismatches are metrically impossible sequences in his book 16 data.
Target was 97 %.

**Lexicon** (`prosody/lexicon.py`, `prosody/lemma_lexicon.py`). Word-form
lexicon from his meter-certain lengths: 13,023 forms, 17,348 α/ι/υ slots. A
lemma-prefix rule and a (morphology tag, ending) rule from the treebanks add
5,346 slots at ~96 % precision on held-out books. Build order is in
`scripts/build_lexicons.sh` because lexicon-derived lengths must not feed back
as evidence. Unknown-length vowels fell from 9.8 % to 5.6 % of syllables in both
corpora.

**Hesiod phones** (`greek2ipa/from_text.py`). All 2,352 lines scan after the
synizesis list was extended (14 name-heavy lines had failed at first). Every Hesiod phone
is in the training inventory. Lexicon coverage of Hesiod tokens: 44 %.

---

## 6. The acoustic model (`reports/phase4_tts.md`)

**Choice.** An explicit-duration FastSpeech2-style model in plain PyTorch with
the pretrained Vocos 24 kHz vocoder, instead of Piper/VITS: MFA durations make it
stable without alignment search, explicit pitch and duration predictors give the
control Product B needs, and Vocos is transparent to the recognizer (PER 3.67 %
on vocoded real clips = original). Piper (OHF-Voice/piper1-gpl, maintained,
GPL-3) remains the fallback.

**Input.** Per phone: phone id + syllable quantity + accent + foot embeddings;
word boundaries are explicit tokens whose target duration is the pause MFA found
there; ^ and $ carry leading/trailing silence.

**Architecture.** d = 256, 4 FFT encoder blocks, duration/pitch/energy predictors
on the detached encoder output, pitch and energy bin embeddings, length
regulation, 4 FFT decoder blocks, 100-bin mel, 5-layer postnet. Losses: L1 mel
(pre and post), MSE log-duration, MSE pitch on voiced tokens, MSE energy. Apple
GPU with two workarounds: 1-D convolutions expressed as 2-D, and a
contiguous-gradient shim for the MPS convolution backward.

**Two bugs found by measurement.** With 2 h of data, copy synthesis passed (4.1 %
PER) but predicted durations were 2× too long. The predictor's bias was +0.45 in
log-duration on training data in eval mode and 0.01 with dropout on: a
train/eval discrepancy from dropout placed before LayerNorm. Fixed to the
reference order (conv → ReLU → LayerNorm → dropout); the predictors were also
detached from the encoder and the log(dur+1) offset restored at inference.

**Runs.**

| Run | Data | Epochs | Val mel L1 | PER val / test (predicted) |
|---|---|---|---|---|
| fs2_2h_v3 | 2 h subset | 25 | 0.770 | 4.24 % / 4.04 % |
| fs2_full | 23 h | 30 (~15 min each) | 0.665 | **2.36 % / 2.37 %** |

---

## 7. QA without a listener

Every gate is a computed metric; what only ears can settle is in
`notes/human_qa_queue.md`.

| Instrument | Use | Result |
|---|---|---|
| MFA alignment log-likelihood | transcript errors; 9 unalignable lines excluded; bottom 1 % queued | done |
| Phone recognizer PER | intelligibility of synthesized audio; floor 3.22 % (val), 4.93 % (test) | synthesized Iliad 2.36 % / 2.37 %; Hesiod 3.14 % |
| Duration ratio long : short vowels | rhythm | 2.08 predicted vs 2.07 real |
| Pitch by accent class | accent | acute − none +2.29 st vs +2.45 real; others within 0.21 st |
| Copy synthesis PER | spectral model alone | 2.97 % |
| Acoustic speaker profile | pronunciation choices | inferred (§4) |
| MOS predictor, speaker similarity | naturalness, voice | not run (instruments not installed) |

The synthesized speech scores lower PER than the real recordings because it is
the canonical version of his pronunciation without the noise gate, breaths and
pace variation.

**Hesiod QC** (`reports/hesiod_qc_fs2_full.md`): 2,338 lines; corpus PER 3.14 %,
median line 2.86 %, p95 9.09 %. After four duration-scale retries (0.97, 1.03,
0.94, 1.06), 31 lines (1.33 %) remain above the 10 % per-line threshold, none
above 20 %. The package gate of 1 % is missed by 8 lines; the package was
produced and the 31 lines are queued. They cluster on the Theogony's name
catalogues (Nereids, Harpies, Gorgons), where rare phone sequences also raise
the recognizer's own uncertainty.

---

## 8. The Hesiod package (`reports/phase7_hesiod.md`)

`data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_fs2_full.zip`, AAC-LC mono
44.1 kHz 96 kb/s MP4, the Classics Viewer layout with the app's own title
strings (author "Hesiod"; the app stores every Hesiod work as book 1):

| Path | Files |
|---|---|
| `Hesiod/Theogony/book_1/line_N.mp4` | 1,022 |
| `Hesiod/Works and Days/book_1/line_N.mp4` | 827 |
| `Hesiod/Shield of Heracles/book_1/line_N.mp4` | 479 |

Import through Settings → Manage Audio like the Iliad package. Not in the
package: 24 lettered lines (Theogony 929a–t, Works and Days 169a–d), synthesized
as WAVs but unaddressable because the app stores them under the integer line
number. (The 14 once-unscannable lines were recovered on 2026-09-24 and are included.)
  Variant packages with `_lettered` in the name keep the suffix in the file name
  (`line_929a.mp4`, 2,352 files) for an app modified to accept text line numbers.

To listen locally: `afplay data/synth/hesiod_fs2_full/wav/tlg001_1.wav`
(tlg001 Theogony, tlg002 Works and Days, tlg003 Shield). For a side-by-side with
the real voice: `data/synth/fs2_full/test_pred/b1_l1.wav` vs `data/iliad/wavs/b1_l1.wav`.

---

## 8b. The Homeric Hymns package (`reports/phase9_hymns.md`)

On 2026-09-25 the finished pipeline was run on the 33 Homeric Hymns (Perseus
tlg0013, 2,342 lines) without retraining or relexiconizing: the same scanner,
lexicons, phonemizer, `fs2_full` model, recognizer and female-voice setting. The
only code change is a corpus registry (`scripts/corpora.py`) and a `--corpus`
option on the four Hesiod scripts, whose defaults still regenerate the Hesiod
tables unchanged.

| | Hesiod | Homeric Hymns |
|---|---|---|
| Lines | 2,352 | 2,342 |
| Lines scanning as hexameters | 2,352 | 2,337 (5 lines Perseus prints in an unmetrical form get quantities by nature and position, no foot) |
| Corpus PER (recognizer) | 3.14 % | 2.91 % (median line 2.86 %, p95 8.57 %) |
| Lines above 10 % after retries | 31 (1.33 %) | 31 (1.32 %), of which the 5 unmetrical lines are the worst 5 |
| Package files (unlettered) | 2,328 | 2,326 (16 lettered lines only in the `_lettered` variants) |
| Layout | `Hesiod/<Work>/book_1/` | `Homeric Hymns/Hymn N to <god>/book_1/`, the app's strings for tlg0013 |

Packages: `data/synth/hymns_fs2_full/hymns_chamberlain_tts_fs2_full.zip`,
`hymns_chamberlain_tts_female.zip`, and the two `_lettered` variants. Text
handling specific to the Hymns: XML comments dropped, `<supplied>`/`<add>`/
`<surplus>` text kept (it is what the app shows), `<choice>` read from `<corr>`
(Hymn 3.181, where the app shows both readings). Lexicon coverage of the Hymns'
tokens is 35 %, lower than Hesiod's 44 %; the share of α ι υ left unresolved is
about the same (5.8 % position-ambiguous, 0.5 % line-final).

## 9. Decisions (`notes/decisions.md`)

| Date | Decision | Basis |
|---|---|---|
| 09-23 | Transcript = Chamberlain's reading page, Perseus word boundaries, 7 hand repairs; edition variants kept | word-level three-way diff |
| 09-23 | Trim rule = last frame above −35 dBFS + 150 ms | recordings are noise-gated |
| 09-23 | ου labeled uː | Allen; measured F2 656 Hz |
| 09-23 | Product A first, Product B planned | accent d = 0.41 / 0.26, below 0.5 |
| 09-23 | No speaker-profile relabeling | labels are identifiers learned from his audio |
| 09-24 | Explicit-duration model + Vocos, not Piper/VITS | MFA durations; control; Vocos transparent; Piper as fallback |
| 09-24 | Input = phone + quantity + accent + foot embeddings, boundary tokens with pause durations | model is ours, no codepoint packing |
| 09-24 | Package produced despite 1.33 % > 1 % gate | 31 lines, none above 20 %, listed for listening |
| 09-25 | Homeric Hymns through the unchanged pipeline; `--corpus` on the Hesiod scripts | same scanner, lexicon, model, recognizer, voice setting; Hesiod defaults regenerate byte for byte |
| 09-25 | Hymns text: keep supplied/surplus text, read `<corr>`, drop comments and notes | the audio should say what the app displays; the one `<choice>` is a printing correction |
| 09-25 | Hymns package produced despite 1.32 % > 1 % gate | 5 of the 31 are lines Perseus prints unmetrically; 26 (1.11 %) otherwise |

---

## 10. Limitations, open items, and what a listener should check

**Limitations**
- 5.6 % of syllables have an α ι υ whose length the meter and lexicon could not
  fix; they default to short. This affects vowel length inside heavy syllables
  only, never the rhythm.
- Digamma is handled only through a stem list in the scanner's costs; there is no
  digamma token in the phone stream.
- The lexicon is word-form and lemma-prefix based; genuinely Hesiodic vocabulary
  falls back to accent rules and the meter.
- The pitch accent is Chamberlain's conservative one. A stricter realization
  needs Product B.
- MOS and speaker-similarity proxies were not run.

**Open items**
- Import the package on a device and play lines (needs a device).
- Listening session from `notes/human_qa_queue.md`: the 31 flagged Hesiod lines,
  the 14 recovered lines, the 7 repaired Iliad transcripts, the 6 edition
  variants, the 2 shortest clips, the speaker-profile inferences, and the
  synthesized Iliad opening next to the original.
- Done: Phase 8, a second package in a female voice by WORLD/pyworld conversion
  of the finished audio (+7 st, formants +14 %, no breathiness, chosen by ear over
  the grid's larger warp, which sounded processed; original package kept): `hesiod_chamberlain_tts_female.zip`,
  `reports/phase8_voice.md`.
- Done 2026-09-25: the 33 Homeric Hymns in both voices (§8b, `reports/phase9_hymns.md`);
  their 31 flagged lines and 5 unmetrical lines are in the QA queue.
- Optional: Phase 7b F0 shaping (Product B); model card; a note to Chamberlain.

---

## 11. Repository map and reproduction

```
hesiod/
  PROJECT.md, PROJECT_PLAN.md, README.md
  reports/        phase1_reconciliation, phase2_phones, phase3_alignment_prosody,
                  phase4_tts, phase5_scanner, phase6_hesiod_phones, phase7_hesiod,
                  alignment_qc, prosody_baseline, scanner_validation, eval_*, hesiod_qc_*
  notes/          decisions.md, human_qa_queue.md
  scripts/        corpora (Hesiod and Homeric Hymns registry),
                  qc_iliad_audio, parse_hypotactic, build_metadata, decode_trim,
                  diff_transcripts, make_split, build_mfa_corpus, alignment_qc,
                  apply_alignment_exclusions, prosody_baseline, parse_hesiod,
                  scan_hesiod, render_hesiod_phones, validate_scanner,
                  build_lexicons.sh, synth_hesiod, textgrid
  greek2ipa/      rules.py, from_spans.py, from_text.py
  prosody/        scanner.py, lexicon.py, lemma_lexicon.py, lexicon.csv, lexicon_lemma.csv
  train/          prepare_features, fs2 (model/train/synth), phone_ctc, recognize,
                  eval_tts, runs/, checkpoints/
  align/          run_align.sh, dictionary.txt, chamberlain_acoustic.zip, textgrids/
  tests/          test_from_spans.py (23), test_scanner.py (5)
  data/iliad/     metadata.csv, phones.csv, line maps, splits/, raw/ and wavs/ (not in git)
  data/hesiod/    lines.csv, phones.csv, scansion.csv
  data/hymns/     the same three tables for the Homeric Hymns (ids h01_1 … h33_19)
  data/scansion/  hypotactic pages and CSV
  data/features/  training features (not in git)
  data/synth/     synthesized audio, evaluation sets, the Hesiod package
```

Environments: system Python 3 for text processing; conda env `aligner` (MFA,
parselmouth); conda env `tts` (PyTorch 2 with MPS, Vocos, parselmouth). Install:
`brew install --cask miniforge`, then `conda create -n aligner -c conda-forge
montreal-forced-aligner` and `conda create -n tts python=3.11 pytorch torchaudio
-c pytorch -c conda-forge; pip install vocos praat-parselmouth`.

Order of execution:

1. `scripts/qc_iliad_audio.py`, `parse_hypotactic.py`, `build_metadata.py`,
   `decode_trim.py`, `diff_transcripts.py`, `make_split.py`
2. `scripts/build_lexicons.sh` (renders `data/iliad/phones.csv`, builds both
   lexicons, renders `data/hesiod/phones.csv`)
3. `scripts/build_mfa_corpus.py`; `bash align/run_align.sh train`; `bash
   align/run_align.sh align`; `scripts/alignment_qc.py`;
   `scripts/apply_alignment_exclusions.py`; `scripts/prosody_baseline.py`
   (aligner env)
4. `train/prepare_features.py`; `train/phone_ctc.py --epochs 8`;
   `train/fs2.py train --name fs2_full --epochs 30`; `train/eval_tts.py --ckpt
   train/runs/fs2_full/best.pt` (tts env)
5. `scripts/synth_hesiod.py --ckpt train/runs/fs2_full/best.pt --package`
6. Homeric Hymns: `scripts/parse_hesiod.py --corpus hymns`, `scan_hesiod.py --corpus hymns`,
   `render_hesiod_phones.py --corpus hymns` (system Python), then
   `synth_hesiod.py --corpus hymns --ckpt train/runs/fs2_full/best.pt --package`,
   `convert_voice.py --in data/synth/hymns_fs2_full/wav --out data/synth/hymns_fs2_full_female/wav
   --semitones 7 --alpha1 1.14 --alpha2 1.14 --tilt 0 --h1 0 --breath 0`, and
   `synth_hesiod.py --corpus hymns --ckpt … --package-only --wav-dir data/synth/hymns_fs2_full_female/wav
   --package-name hymns_chamberlain_tts_female` (tts env)

Wall-clock on the M4: MFA training 57 min; recognizer 1.7 h; TTS full run 7.5 h;
Hesiod synthesis, QC and packaging about 40 min. The Homeric Hymns
(2,342 lines) took 25 min for synthesis, QC and packaging and 5 min for the voice conversion.
