# Hesiod Text-to-Speech Project Plan

Goal: train a single-speaker, phoneme-input text-to-speech (TTS) model on David
Chamberlain's line-by-line Iliad recordings (hypotactic.com), then use it to
generate a reading of Hesiod (Theogony, Works and Days, Shield) in reconstructed
pronunciation following W. Sidney Allen's *Vox Graeca*, with metrical quantity
realized and pitch accent realized as far as the data allows (see §2). The only
deliverable for the app is the pre-rendered Hesiod audio package; the model,
converter and scanner are offline tools.

Written 2026-09-23. Revised 2026-09-23 after Phase 1 reconciliation and review.

---

## 1. Assets already in hand

| Asset | Location | Notes |
|---|---|---|
| Iliad audio (all 24 books) | `~/git/classicsviewer/audio/homer_iliad_chamberlain_audio.zip`, extracted to `data/iliad/raw/` | 15,693 files, all books complete. 15,643 usable clips, 22.75 h of speech. AAC-LC, mono, 44.1 kHz, ~96 kb/s. See `reports/phase1_reconciliation.md`. |
| Download script | `~/git/classicsviewer/audio/download_iliad_controlled.sh` | Sequential curl from `https://hypotactic.com/homer/audio/{book}/line_{n}.mp4`. Its "expected" counts are vulgate counts, not hypotactic's; see the report. |
| Packaging scripts | `package_audio.sh`, `create_complete_iliad_package.sh` in the same dir | Produce `Author/Work/book_N/line_X.mp4` zips the app imports. Reuse for the Hesiod output. |
| App audio format spec | `~/git/classicsviewer/audio/AUDIO_SYSTEM_DOCUMENTATION.md` | MP4/AAC, path-parsed metadata, one active package at a time. |
| Iliad Greek text (TEI) | `~/git/classicsviewer/data-sources/canonical-greekLit/data/tlg0012/tlg001/` | Perseus. Used only for vulgate line numbering; the transcript is Chamberlain's text. |
| Hesiod Greek text (TEI) | `~/git/classicsviewer/data-sources/canonical-greekLit/data/tlg0020/` | tlg001 Theogony (1022 lines), tlg002 Works and Days (828), tlg003 Shield (480). Target text. |
| Hesiod treebanks | `~/git/classicsviewer/data-sources/treebank_data/v2.0/Greek/nonArethusaCompliant/tlg0020.*.tb.xml` | Lemma + morphology per token, for the vowel-length lexicon. |
| Chamberlain's Iliad scansion | `data/scansion/iliad/` (reading pages, audio-index order), `data/scansion/iliad_scanned/` (2026 revision, Perseus-aligned), `data/scansion/iliad_csv/` (2017 CSV) | Every syllable tagged long/short, foot, word, hemistich. Parsed to `data/iliad/hypotactic*_lines.csv`. His syllabification deliberately separates prefixes and is not linguistic. |
| hypotactic Hesiod readers | `data/scansion/hesiod/` | Theogony and Works and Days with lemma/POS/gloss per word. **No scansion, no Shield, CC BY-NC-SA**: reference only, do not redistribute. |
| Local tools | `ffmpeg`/`ffprobe` installed (Homebrew). Python 3.14. | `mfa` and `sox` not installed. TTS stacks want Python 3.10–3.12, so use a separate env for the ML work. |

## 2. What the data can and cannot teach

Chamberlain describes his reading as "a tolerable effort at reconstructed
pronunciation with a very conservative pitch accent," says his stress accent
"comes through too much," and that he was "inconsistent on digamma." He also
varied playback pace per line in the web player (the raw files are unaffected).

Consequences:

- A model trained on this voice reproduces **his** prosody. Explicit F0
  conditioning can sharpen what is in the data but cannot invent a pitch accent
  he did not produce.
- Two possible end products, decided after the Phase 3 prosody baseline shows
  how much accent is measurable:
  - **Product A (default):** a Chamberlain-style reading of Hesiod, with his
    rhythm and conservative accent. This is what the pipeline produces naturally.
  - **Product B (stretch):** a stricter Allen realization, which needs a
    post-TTS F0-shaping step (Phase 7b) driven by the accent marks.
- Digamma: scansion shows where it counts metrically, not whether he voiced it.
  Training uses a special token at digamma positions so the model learns his
  mixed behaviour; the Hesiod output makes an explicit choice (default: silent,
  with hiatus preserved).

## 3. Licensing

Recordings and reading pages: **CC-BY 4.0**, © 2016, 2017 David Chamberlain
(verified on hypotactic.com and in the audio README). Hesiod readers on the
same site are CC BY-NC-SA and are not used for any output.

- Credit Chamberlain and hypotactic.com in every released artifact (audio
  package, model weights, repo README) and link the license.
- Released under CC BY-SA 4.0 (`LICENSE`), because the Hesiod text is Perseus's
  BY-SA text; the attribution notice there cites every source.
- Voice conversion (Phase 8) is a courtesy, not a requirement. Email
  Chamberlain before release; he may want to link to the result.

## 4. QA without listening

No human listening or QA is available until the end of the project, so every
check must be a computed metric with a threshold, and anything only ears can
settle goes into `notes/human_qa_queue.md` for later. The instruments:

- **Alignment score.** The MFA acoustic model trained on the real audio
  (Phase 3) scores any (audio, phone string) pair. Low per-utterance
  log-likelihood flags transcript errors in the corpus and mispronunciations in
  synthesized audio.
- **Phone recognizer.** A small CTC phone recognizer (wav2vec2-base
  fine-tuned on the corpus with the training phone set, a few GPU hours).
  Phone error rate (PER) on held-out real audio sets the floor; PER of
  synthesized audio against its intended phone string measures
  intelligibility line by line.
- **Prosody metrics.** F0 contour by accent type and duration by quantity from
  the aligned real audio (baseline) and from synthesized audio (must match the
  baseline within tolerance).
- **Naturalness and speaker proxies.** A pretrained MOS predictor (UTMOS or
  NISQA) and speaker-embedding cosine similarity (ECAPA/Resemblyzer) between
  synthesized and real audio.
- **Acoustic speaker profile.** Instead of listening for how he says ζ, φ/θ/χ,
  υ, ει/ου, measure them on aligned segments: aspiration duration for φθχ vs
  πτκ, closure presence for ζ, F1/F2 of υ against ι and ου, formant movement in
  ει/ου, and F0 by accent. Decisions are made by threshold and written down as
  such, with the caveat that they are inferences.

Every phase below names which of these it uses and what threshold counts as a
pass.

## 5. Two tracks

The Iliad training track and the Hesiod text track are independent until
Phase 7. Work them in parallel: the training track is compute-bound and can run
while the Hesiod scanner and lexicon (the longest human-effort item) are built.

```
Track I (Iliad → model)         Track H (Hesiod text → phones)
  Phase 1  corpus prep            Phase 5  hexameter scanner + length lexicon
  Phase 2  syllables → phones     Phase 6  Hesiod phones + prosody features
  Phase 3  alignment + baseline
  Phase 4  training + eval
                     ↘          ↙
                  Phase 7  generate Hesiod
                  Phase 8  voice conversion (optional)
                  Phase 9  release
```

## 6. Phases

### Phase 0. Environment (½ day)

- `uv venv --python 3.11` (or conda) for ML tooling. Greek text processing in
  plain Python.
- Install: `montreal-forced-aligner` (conda), `praat-parselmouth`, `librosa`,
  `pytest`.
- GPU: rent one 24 GB card (RunPod / Lambda, ~$0.50–1.00 per hour, 40–80 hours
  across runs). Apple Silicon is for inference and small experiments only.

### Phase 1. Corpus preparation (Track I, 2–3 days)

Status 2026-09-23: reconcile and pair-with-text done; see
`reports/phase1_reconciliation.md`. Audio index drifts from vulgate numbering
in books 8, 9, 11, 14, 18 (mapping in `data/iliad/line_map.csv`); 50 lines
excluded; transcripts are Chamberlain's reading-page text.

1. **Reconcile.** Done: `scripts/qc_iliad_audio.py`, `scripts/parse_hypotactic.py`,
   `scripts/build_metadata.py` → `data/iliad/metadata.csv`, `exclusions.csv`.
2. **Decode.** Done: `scripts/decode_trim.py` → `data/iliad/wavs/`, 22,050 Hz
   mono 16-bit, 15,641 clips, 23.1 h.
3. **Trim and normalize.** Done. The recordings are noise-gated, so the end is
   the last frame above −35 dBFS plus 150 ms (a silence-gap rule cuts inside
   lines); start is the first frame above −40 dBFS minus 100 ms. RMS over
   speech normalized to −20 dBFS, peak limited to −1 dBFS. 21.427 (12 s) and
   9.188 (0.7 s stub) excluded.
4. **Transcript cleanup.** Done: `scripts/diff_transcripts.py` compares the
   reading page against the scanned page and Perseus, normalizes apostrophes
   and spacing, adopts Perseus word boundaries where the reading page split or
   joined words, keeps his accent conventions and edition variants, and
   applies seven hand-written repairs from `data/iliad/transcript_overrides.csv`.
   Every difference is logged in `data/iliad/transcript_diff.csv`.
5. **Automated transcript check** replaces listening: after Phase 3 alignment,
   rank utterances by alignment log-likelihood; inspect the bottom 1 % by
   re-aligning against the scanned and Perseus variants and picking the best
   scoring text; exclude what still scores badly. Queue the excluded lines for
   human review later.
6. **Split.** Done: `scripts/make_split.py`. Train 15,278 / val 311 (2 % per
   book) / test 52 (Iliad 1.1–52). Phase 1 complete.

Deliverable: `data/iliad/wavs/`, cleaned `metadata.csv`, `notes/human_qa_queue.md`.

### Phase 2. Chamberlain syllables → phones (Track I, 2–3 days)

Status 2026-09-23: converter, tests and full render done; see
`reports/phase2_phones.md`. 9.8 % of syllables have α ι υ of unknown length
(default short, flagged) pending the Phase 5 lexicon. Speaker profile and digamma
token still to come after Phase 3/5.

The Iliad needs no lexicon: his syllable spans give syllabification, word
boundaries and quantity for every syllable, and an open long syllable implies a
long vowel or diphthong. This phase is a small deterministic converter over his
spans, not the full Greek G2P.

- **Consonants (Allen).** φ θ χ → pʰ tʰ kʰ; π τ κ → p t k; β δ γ → b d g; γ
  before γ κ χ ξ → ŋ; ζ → zd; ξ ψ → ks ps; ρ → r, initial ῥ → r̥; σ → s, z before
  voiced consonants; rough breathing → h; geminates → long consonant.
- **Vowels.** ε → e, η → ɛː, ο → o, ω → ɔː; ει → eː, ου → oː/uː; υ → y;
  αι οι αυ ευ → ai oi au eu; ᾳ ῃ ῳ → aːi ɛːi ɔːi. α ι υ length from the
  syllable: open + long ⇒ long vowel; closed ⇒ short unless the lexicon (Phase 5,
  when available) says otherwise; log the closed-syllable cases.
- **Re-syllabify** his prefix-separating spans into linguistic syllables
  (onset-maximal) before deriving vowel length; keep his quantity per syllable.
- **Accent** as a separate stream per syllable: acute, circumflex, grave, none.
- **Elision, movable ν, correption** are already reflected in his spans; digamma
  positions get the special token from §2.
- **Speaker profile.** Start with pure Allen. After Phase 3's acoustic
  speaker profile, override Allen where the measurements say his practice
  differs (e.g. ζ without a stop closure → [z]); re-run alignment and keep the
  profile that scores better. Train on that profile.

Tests: ~200 hand-checked words, a dozen whole lines, and property tests
(every output phone is in the phone set; every input character consumed).

Deliverable: done. `greek2ipa/from_spans.py`, `data/iliad/phones.csv`
(15,638 lines), `reports/phase2_phones.md`.

### Phase 3. Forced alignment and prosody baseline (Track I, 2–3 days, mandatory)

Status 2026-09-23: MFA 3.4.2 installed (`align/run_align.sh`); acoustic model
trained from scratch in 57 min (`align/chamberlain_acoustic.zip`); scoring
alignment exported for 15,573 utterances; 9 failed and are excluded
(`scripts/apply_alignment_exclusions.py`); QC in `reports/alignment_qc.md`,
bottom 1 % queued. Prosody baseline and speaker profile done:
`reports/phase3_alignment_prosody.md`. Quantity ratio 1.67 (d 1.18); accent
present but subtle (acute d 0.41, circumflex fall d 0.26) → Product A first,
Product B planned (`notes/decisions.md`). Phone recognizer (3b) done: val PER
3.22 % (`train/recognize.py` scores any audio). **Phase 3 complete.**

Runs before training. It is the only scalable check that transcripts match
audio, and it produces the prosody baseline that decides Product A vs B.

- MFA pronunciation dictionary from Phase 2 (one entry per unique token
  including elided forms).
- `mfa train` from scratch on the corpus, then `mfa align`. No pretrained
  model fits this phone set.
- QC: alignment log-likelihood distribution; inspect the worst 1 %; fix
  transcripts or exclude.
- Baseline: F0 per aligned syllable with parselmouth. Mean contour by accent
  type, mean duration by quantity, long:short ratio. **Decision point:** if the
  circumflex rise-fall and acute rise are measurable and consistent (effect
  size d > 0.5 against unaccented syllables), Product A suffices; if weak, plan
  Product B (Phase 7b).
- Acoustic speaker profile (§4) on the aligned segments →
  `reports/speaker_profile.md`; feeds back into the Phase 2 profile.
- **3b. Phone recognizer.** Fine-tune wav2vec2-base (or a comparable CTC
  model) on the training split with the phone tokens; report PER on the
  validation split. This PER is the reference floor for all later
  intelligibility checks.

Deliverable: TextGrids, `reports/alignment_qc.md`, `reports/prosody_baseline.md`,
`reports/speaker_profile.md`, the recognizer checkpoint and its PER,
recorded decisions in `notes/decisions.md`.

### Phase 4. Model training and evaluation (Track I, 1–2 weeks wall clock)

Status 2026-09-24: model chosen and built (`notes/decisions.md`): explicit-duration
FastSpeech2-style acoustic model in plain PyTorch (`train/fs2.py`) with phone +
quantity + accent + foot embeddings, MFA durations, pitch/energy predictors, and
the pretrained Vocos 24 kHz vocoder (transparent to the recognizer). Features in
`data/features/` (`train/prepare_features.py`). 2 h subset passes all gates
(`reports/phase4_tts.md`, after fixing a dropout/LayerNorm order bug in the
variance predictors). Full-corpus model `train/runs/fs2_full/best.pt`: PER 2.36 %
val / 2.37 % test, below the real-audio floor; durations and accent contrasts
match the baseline. **Phase 4 complete.** 4b is not needed as a separate model:
this model already has explicit duration and pitch predictors.

**Input format.** Check this before choosing a model: Piper takes characters or
espeak phonemes, not feature-suffixed tokens. Either map each (phone, quantity,
accent) combination to a single private-use codepoint, or pick a model that
accepts auxiliary per-phone embeddings. Also confirm Piper's maintenance status;
spend an hour on alternatives that take custom phone sets (Matcha-TTS, VITS
reference implementation, StyleTTS2) before committing.

**4a. Baseline.** VITS-family (Piper or reference VITS) on the 22.05 kHz clips
with the codepoint-mapped tokens. First on a 2 h subset to prove the pipeline,
then full. Success: intelligible, natural, matches held-out lines, quantity
ratio close to the Phase 3 baseline.

**4b. If accent realization lags the baseline:** FastPitch/FastSpeech2 with
accent and quantity as embeddings and F0/duration predictors trained on the
Phase 3 alignments. HiFi-GAN vocoder fine-tuned on the same data.

**Evaluation** on the held-out lines, all automatic:

| Metric | Pass |
|---|---|
| PER of synthesized audio (phone recognizer) | ≤ 1.5 × the real-audio PER |
| MFA alignment log-likelihood of synthesized audio | within the real-audio interquartile range |
| Mel-cepstral distortion vs the real recording | reported, used to rank models |
| F0 correlation on accented syllables; % circumflex rise-fall; % acute rise | within 10 points of the Phase 3 baseline |
| Long:short duration ratio | within 10 % of the baseline |
| MOS predictor (UTMOS/NISQA) | ≥ real audio minus 0.3 |
| Speaker similarity (embedding cosine) | ≥ 0.8 to real audio |

Iliad 1.1–52 and 30 Hesiod lines are synthesized and stored for the human
listening session at the end, with their metrics beside them.

Common practice: fixed seeds, TensorBoard/W&B, and the converter version hash
saved with every checkpoint.

Deliverable: checkpoints, configs, `synthesize.py`, `reports/eval_<model>.md`.

### Phase 5. Hexameter scanner and length lexicon (Track H, ~2 weeks)

Status 2026-09-23: scanner and word-form lexicon built and validated at 98.4 %
line agreement with Chamberlain (24-fold); see `reports/phase5_scanner.md`.
Remaining: digamma token. (All Hesiod lines scan as of 2026-09-24.)

The long pole of the project; start it as soon as Phase 2 is done and run it
alongside Phases 3–4.

- **Lexicon** of α ι υ length: LSJ macrons, Perseus morphology, the Hesiod and
  Iliad treebanks, and morphological rules (-ᾱς gen., -ῑ dat. pl., etc.).
- **Scanner**: 6 feet, dactyl/spondee, fixed 5th-foot dactyl, 6th foot of two
  syllables; position rules, correption, synizesis, elision, digamma hiatus.
  Scanner and lexicon feed each other: a syllable forced long by the meter
  adds a lexicon entry; a lexicon entry constrains the scan.
- **Validation** on the Iliad against Chamberlain's re-syllabified scansion.
  Target: >97 % of lines identical; disagreements are classified
  automatically (his 2016 vs 2026 versions disagree with each other too, and
  those lines are excluded from the score).
- Run on Hesiod. Checks without a human: every line must scan as a valid
  hexameter; the lexicon must be self-consistent (a lemma+ending gets one
  length everywhere); lines with unresolved syllables are counted and listed.
  If the sedes project (github.com/sasansom/sedes) publishes Hesiod scansion,
  use it as an external reference; check availability first.

Deliverable: `prosody/scanner.py`, `prosody/lexicon.tsv`, validation report.

### Phase 6. Hesiod phones and prosody features (Track H, 2–3 days)

Status 2026-09-23: done for phones; see `reports/phase6_hesiod_phones.md`.
All 2,352 lines rendered, inventory identical to training.

- Parse tlg0020 TEI into line tables; strip editorial marks; NFC.
- Full Greek G2P (`greek2ipa/from_text.py`): the Phase 2 rules plus the Phase 5
  lexicon and scansion for vowel length, syllabification, accent, sandhi.
- Same feature encoding as training: phone, quantity, accent, foot position,
  word boundary, caesura. Same codepoint mapping. Assert the phone inventory is
  a subset of the training inventory; list OOV phones and Hesiod-only names.

Deliverable: done, `data/hesiod/phones.csv`.

### Phase 7. Generate Hesiod (1 day compute + QC)

Status 2026-09-24: done for Product A; see `reports/phase7_hesiod.md`. Package
`data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_fs2_full.zip` (2,328 lines after recovering the 14 unscanned ones).
Corpus PER 3.14 %; 31 lines (1.33 %) flagged for listening, gate of 1 % missed by
8 lines. 7b (F0 shaping, Product B) not started.

- `synthesize.py` per line; encode AAC-LC mono 44.1 kHz 96 kb/s MP4 to match
  the existing package.
- **7b (Product B only):** F0 shaping by accent mark with WORLD or PSOLA
  resynthesis, then re-run the accent metrics.
- Layout: `Hesiod/Theogony/book_1/line_N.mp4` etc. Confirm the work titles
  match the app's database strings for tlg0020 first.
- Package with `package_audio.sh` (parametrize source dir and name).
- QC, automatic for every line: PER against the intended phones, alignment
  score, MOS proxy, duration ratio, accent metrics. Lines failing any threshold
  are regenerated with a different seed; persistent failures are listed in
  `notes/human_qa_queue.md` ranked by PER. Package only when the failure list
  is under 1 % of lines.

Deliverable: `hesiod_chamberlain_tts_audio.zip` importable by the app, plus
`reports/hesiod_qc.md`.

### Phase 8. Voice conversion to a female voice with WORLD (planned 2026-09-24, ~1 day)

Status 2026-09-24: done. Search over 96 settings; the grid's choice (+8 st, warp
1.22/1.16, breathy) sounded processed to the listener, so the mild setting
(+7 st, uniform +14 % formants, no breathiness) was adopted; all 2,338 lines converted to
`data/synth/hesiod_fs2_full_female/wav/`, package
`data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_female.zip`; original untouched.
See `reports/phase8_voice.md`. Finding: the male-trained recognizer penalizes
female formants, so selection was on acoustic targets with PER as a guard.

Goal: a second Hesiod package in a female voice, made from the finished Product A
audio by signal processing, with the original package untouched. Method: the
WORLD vocoder through `pyworld` (installed in the `tts` env; verified: 0.6 s per
line with `harvest`, 0.2 s with `dio`), which separates each line into F0, a
spectral envelope and aperiodicity so the three can be scaled independently
and resynthesized. Background and parameter guidance: `conv.txt`.

**Why WORLD rather than a neural converter.** The accent lives in the F0 contour.
WORLD multiplies F0 by a constant, which preserves every interval in semitones
exactly, so the acute rise and circumflex rise-fall survive by construction;
neural converters re-predict pitch and can flatten them. The rhythm is untouched
because frame timing is unchanged.

**What actually differs between a male and a female voice**, and what is done
about each. Pitch is the smallest part of the job; a male voice raised 8
semitones with nothing else changed sounds like a small man or a cartoon. The
transforms below are all applied per line in `scripts/convert_voice.py` (new):

| Property | Male vs female | Transform in WORLD terms | Setting (search range) |
|---|---|---|---|
| Fundamental frequency | female mean ≈ 1.6–1.8× male | F0 × 2^(s/12); intervals in semitones unchanged, so the accent contours are preserved | s = +7.5 st (7–9); his mean is 140 Hz → 210–235 Hz |
| Vocal-tract length → formant positions | female formants 15–20 % higher; F1 tends to rise more than F2/F3 | warp the spectral envelope's frequency axis: envelope'(f) = envelope(f/α(f)), with a two-band warp: α₁ for 0–1 kHz (F1 region), α₂ above, blended over 1–1.5 kHz; resample per frame with interpolation | α₁ = 1.22 (1.18–1.26), α₂ = 1.16 (1.12–1.20); a single α = 1.18 is the fallback |
| Formant bandwidths | scale with the warp | come along with the envelope warp; no separate step | |
| Glottal source: open quotient, H1–H2 | female phonation has a higher open quotient: the first harmonic is stronger relative to the second, i.e. a steeper low-frequency tilt | tilt the envelope: −k dB per octave above ~300 Hz, plus a small boost (+2–3 dB) in the band around the new F0 | k = 1.5 dB/oct (0–3); the boost follows F0 per frame |
| Breathiness | female voices are on average breathier: more aspiration noise, especially above 2 kHz | raise D4C aperiodicity: +b uniformly, and +2b above 3 kHz; clip to 1 | b = 0.04 (0–0.08) |
| Overall spectral tilt / brightness | after the warp the energy above 4 kHz moves up and can sound harsh | gentle low-pass shelf −2 dB above 6 kHz after warping | fixed |
| Speaking rate, quantity, pauses | not a sex difference of any size; the rhythm is a deliverable | unchanged (frame timing untouched) | |
| Pitch range and accent size | female speakers' semitone ranges are similar; the accent contrasts must stay Chamberlain's | unchanged: multiplicative F0 keeps them exactly | |
| Jitter, shimmer | no useful difference | unchanged | |
| Loudness | none | re-normalize to −20 dBFS RMS after synthesis | fixed |

Frequency warping and tilting operate on the CheapTrick envelope (513 bins at
24 kHz), so harmonics stay at exact multiples of the new F0 and the result does
not go metallic; that separation is the reason WORLD is used instead of warping
the raw spectrum. The two-band formant warp is the one item that goes beyond
`conv.txt`'s uniform scaling; the formant check below decides whether it earns
its place (if the uniform warp passes as well, keep the simpler one).

Analysis with `harvest` + `stonemask`, `cheaptrick`, `d4c`; synthesis with
`pw.synthesize`; the input is the 22.05 kHz WAV, upsampled to 24 kHz for the
analysis window defaults and returned to 22.05 kHz.

**Parameter search, automatic** (no listener): a grid over s = 7, 8, 9; formant
warp uniform 1.14 / 1.18 / 1.22 or two-band (1.22, 1.16); tilt 0 / 1.5 / 3 dB
per octave; breathiness 0 / 0.04 / 0.08, on 60 Hesiod lines plus the Iliad test
passage (about 100 settings, a few minutes each on 8 cores), scored by:

1. Recognizer PER against the intended phones. Caveat: the recognizer was
   trained on a male voice, so PER will rise from the voice change alone;
   report it as relative to the unconverted line and use it to reject settings
   that break articulation, not as an absolute gate.
2. Formant check with parselmouth: median F1 and F2 of ι, υ, ου, α, ε, ο after
   conversion must be the unconverted values × the intended warp within 5 %,
   and the F1/F2 ratios must stay in the female region of published vowel
   charts (F1 of α around 900–1000 Hz, F2 of ι around 2500–2800 Hz).
2b. Source check: H1−H2 (first minus second harmonic level at vowel midpoints)
   must rise by 2–5 dB against the unconverted line, and the harmonics-to-noise
   ratio must not fall by more than 3 dB (breathier, not noisy).
3. Pitch check: mean F0 by accent class in semitones relative to the utterance
   median must equal the unconverted values within 0.1 st (they should be
   identical), and the median F0 must be 200–240 Hz.
4. Artifact check: fraction of frames WORLD marks unvoiced must not change by
   more than 2 points (a large change means the pitch tracker failed).

Pick the setting with the lowest PER among those passing 2–4; if several tie,
prefer the middle of the grid.

**Full conversion.** All 2,338 Hesiod WAVs plus the Iliad test passage, 8
processes, into `data/synth/hesiod_fs2_full_female/wav/`. QC on every line with
the same four checks; failures listed in `reports/hesiod_qc_female.md` and the QA
queue. Then `scripts/synth_hesiod.py --package-only` generalized to take a WAV
directory and a package name, producing
`hesiod_chamberlain_tts_female.zip` in the same Classics Viewer layout (author
"Hesiod", same titles; a different package name so both can be imported).

**Deliverables.** `scripts/convert_voice.py`, the female WAV directory and
package, `reports/phase8_voice.md` with the chosen parameters and the grid
results, the original package unchanged, and a line in `LICENSE`'s notice
that the female voice is a transformation of Chamberlain's.

**Risks.** WORLD buzz or metallic timbre at large shifts (mitigated by the
moderate settings and the artifact check); envelope warping widens the
apparent vocal tract mismatch for back vowels (formant check catches it); the
recognizer's male bias makes PER a relative metric only; whether the result
sounds like a woman rather than a pitched-up man is a listening judgment for
the QA queue.

### Phase 9. Release (1 day)

README with attribution, license, method, limitations; model card; publish
`greek2ipa` and the scanner separately; send Chamberlain a link.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Pitch accent in the data is too weak to learn | Phase 3 baseline measures it before training; Product A/B decision; Phase 7b F0 shaping. |
| No human listening until the end | §4 metrics with thresholds at every phase; recognizer PER as the intelligibility instrument; `notes/human_qa_queue.md` collects what only ears can settle. |
| Transcript errors (typos, text-version drift) | Phase 1 word-level diff; Phase 3 alignment log-likelihoods. |
| Scanner and lexicon take longer than planned | On Track H, off the training critical path; Iliad validation catches errors early. |
| Vowel length for α ι υ wrong → wrong rhythm in Hesiod | Scansion-first resolution; lexicon; log and review unresolved cases. |
| Hesiod names and words unseen in training | Phone-level input; OOV report in Phase 6; check those lines first in Phase 7 QC. |
| TTS model does not accept the feature stream | Codepoint mapping decided in Phase 4 before training; hash the mapping into checkpoints. |
| Phone-set drift between training and inference | Version hash asserted in `synthesize.py`. |
| Python 3.14 vs ML libs | Separate 3.11 env. |
| GPU cost or time overrun | 2 h subset first. |

## 8. Repository layout

```
hesiod/
  PROJECT_PLAN.md
  README.md
  pyproject.toml
  scripts/             # qc_iliad_audio, parse_hypotactic, build_metadata, decode/trim
  greek2ipa/           # from_spans.py (Track I), from_text.py (Track H), profiles, tests
  prosody/             # scanner, lexicon, feature encoding
  data/
    iliad/             # raw/ (gitignored), wavs/ (gitignored), metadata.csv, phones.csv
    hesiod/            # line tables, phones.csv
    scansion/          # hypotactic pages and CSV (zips gitignored)
  align/               # MFA dictionary, model, TextGrids (gitignored)
  train/               # configs and launch scripts per model
  synth/               # synthesize.py, packaging
  reports/             # phase1_reconciliation, alignment_qc, prosody_baseline, eval
  notes/               # chamberlain_pronunciation.md, decisions.md
```

## 9. Milestones

Effort assumes roughly full-time work; part-time stretches the calendar, not
the order.

| # | Milestone | Track | When |
|---|---|---|---|
| M1 | WAVs trimmed, transcripts cleaned, split | I | done 2026-09-23 |
| M2 | Phones for all Iliad lines from Chamberlain's spans | I | done 2026-09-23 |
| M3 | Alignment QC'd; prosody baseline; speaker profile; phone recognizer PER; Product A/B decided | I | done 2026-09-23 |
| M4 | 2 h subset model proves the pipeline | I | done 2026-09-24 (all gates pass) |
| M5 | Scanner validated on the Iliad; lexicon | H | done 2026-09-23 (98.4 %) |
| M6 | Full model; eval report; go/no-go on 4b | I | done 2026-09-24 (PER 2.4 %, below the real-audio floor) |
| M7 | Hesiod phones with OOV report | H | done 2026-09-23 |
| M8 | Hesiod generated, packaged, imports in Classics Viewer | both | package built 2026-09-24; app import not yet tried |
| M9 | Optional voice conversion; release | both | Week 7–8 |

## 10. Open questions

- Resolved: the app database titles are "Theogony", "Works and Days", "Shield of Heracles" under author "Hesiod" (`data-prep/perseus_texts_extended.db`); `scripts/synth_hesiod.py --package` uses them.
- Product A vs B (decided at M3).
- Digamma choice for Hesiod output (default silent with hiatus).

## 11. Immediate next steps

1. Done: Phases 1, 2, 5 (scanner + word-form lexicon), 6 (Hesiod phones). MFA
   installed (`align/run_align.sh`), acoustic model training in progress.
2. Done: Phase 3 alignment, QC, prosody baseline, speaker profile.
3. Done: Phase 3b phone recognizer (val PER 3.22 %).
4. Track H: lemma-level lexicon from the treebanks; digamma token.
5. Done: TTS model and input format decided; Phase 4 subset training running.
6. Done: Hesiod package (Product A).
7. Import the package into Classics Viewer and play a few lines (needs a device).
8. Listening session with `notes/human_qa_queue.md`.
9. Done: Phase 8 female-voice package.
10. Optional: Phase 7b F0 shaping (Product B), model card, a note to Chamberlain.
