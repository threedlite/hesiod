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
