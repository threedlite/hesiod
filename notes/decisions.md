# Decisions

- 2026-09-23 **Product A first, Product B planned.** Phase 3 baseline: acute d = 0.41,
  circumflex fall d = 0.26 against unaccented syllables, grave = unaccented. Below the
  0.5 threshold, so the trained model will carry a subtle accent. Ship Product A
  (Chamberlain-style Hesiod) first; add Phase 7b F0 shaping (Product B) as a stretch,
  amplifying the measured contour shapes (acute: rise; circumflex: rise-fall).
- 2026-09-23 **No speaker-profile relabeling.** His ει is a diphthong, η ≈ [eː], ω close
  and ο open, aspiration weak. Labels are identifiers learned from his audio, so the
  Hesiod output inherits his values without changing the phone tables. Documented in
  `reports/phase3_alignment_prosody.md`.
- 2026-09-23 **ου = uː** in the labels (Allen's classical value); measured F2 656 confirms
  a back monophthong.
- 2026-09-23 **Trim rule** = last frame above −35 dBFS + 150 ms, because the recordings
  are noise-gated (Phase 1 report).
- 2026-09-23 **Transcript = Chamberlain's reading page**, with Perseus word boundaries and
  seven hand repairs; edition variants kept (Phase 1 report).
- 2026-09-24 **Phase 4 model: explicit-duration acoustic model + Vocos vocoder** (plan 4b first,
  not the Piper/VITS 4a baseline). Reasons: MFA gives phone durations, so a FastSpeech2-style
  model in plain PyTorch trains stably on the M4 GPU without monotonic alignment search or a
  Lightning stack; explicit pitch and duration predictors give the accent control Product B
  needs; the pretrained Vocos 24 kHz vocoder is transparent to the recognizer (PER 3.67 % on
  40 vocoded real clips vs 3.67 % original), so no vocoder training. Piper (OHF-Voice/piper1-gpl,
  maintained, GPL-3, accepts `phoneme_type text` codepoints) stays as the fallback if quality
  is poor: https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/TRAINING.md
- 2026-09-24 **Input format:** per-phone token = phone id plus embedded feature streams
  (syllable quantity, accent, foot); word boundaries are explicit tokens whose target
  duration is the pause MFA found there (0 if none). No codepoint packing needed since the
  model is ours.
- 2026-09-25 **Homeric Hymns through the unchanged pipeline.** The 33 hymns (Perseus tlg0013,
  2,342 lines) use the same scanner, lexicons, phonemizer, `fs2_full` model, recognizer and
  female-voice setting as Hesiod; nothing was retrained or re-tuned. The change is a corpus
  registry (`scripts/corpora.py`) and a `--corpus` option on the four Hesiod scripts, whose
  defaults regenerate `data/hesiod/*` byte for byte (checked with `git diff`).
- 2026-09-25 **Hymns text: the audio says what the app displays.** `<supplied>`, `<add>` and
  `<surplus>` text is kept (the app prints it); XML comments and `<note>` are dropped; the one
  `<choice>` (Hymn 3.181) is read from `<corr>` περικλύστοιο although the app shows both words,
  because the sic/corr pair is a printing correction, not two readings.
- 2026-09-25 **Unmetrical lines are synthesized, not skipped.** Five lines that Perseus prints in
  a form that is not a hexameter (Hymn 2.128, 2.267, 3.181, 4.394, 13.1) take the scanner's
  fallback (quantities by nature and position, no foot); they are the five worst lines by PER
  (22–31 %) and are queued for a listener rather than emended.
- 2026-09-25 **Hymns package produced despite 1.32 % > 1 % gate**, as for Hesiod: 31 lines, of
  which the 5 unmetrical ones account for the excess (26 otherwise, 1.11 %).
- 2026-09-25 **Every hexameter poet in Perseus (others.txt) goes through the same pipeline**, one corpus
  per app author, with a `book` column and `book_N/` package folders for multi-book works. The Iliad is
  left out (the app has Chamberlain's own recording; synthesizing training text proves nothing). Elegiac
  works are left out by hand (Theocritus and Callimachus Epigrams, Callimachus Hymn 5); non-hexameter
  books inside a work are dropped when the scanner finds more than a quarter of their lines unmetrical
  (Theocritus 28, 30) or when listed in `corpora.py` (Theocritus 29, Aeolic, which scans by accident).
- 2026-09-25 **Printed digammas are dropped** (ϝ in six Argonautica lines and one of Nonnus): the
  training inventory has no [w], and plan §2 chose a silent digamma with hiatus kept.
- 2026-09-25 **The package gate is reported, not enforced, per corpus**: the flagged share is expected to
  rise with distance from Homer (Colluthus 2.3 %); every package is produced and the flagged lines go to
  `per.csv` and the QA queue (40 worst per corpus).
- 2026-09-25 **Only the female-voice package is released.** The unconverted synthesis reproduces
  Chamberlain's voice too closely to distribute; it stays on disk as the intermediate the QC
  metrics are computed on (the recognizer was trained on his voice) and as the input to the
  WORLD conversion. Every `*_chamberlain_tts_female.zip` is the deliverable; the `*_fs2_full.zip`
  files are not to be shipped.
