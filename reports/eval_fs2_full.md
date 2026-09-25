# TTS evaluation: fs2_full

Checkpoint `train/runs/fs2_full/best.pt`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.

| Set | PER | Pass (≤ 1.5 × real) |
|---|---|---|
| val, predicted durations/pitch | 2.36 % | yes |
| test (Iliad 1.1–52), predicted | 2.37 % | yes |
| val, teacher-forced durations/pitch (copy synthesis) | 2.97 % | yes |

## Duration: vowel duration by syllable quantity (ms)

| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |
|---|---|---|---|---|---|---|---|
| val | 206 | 99 | 2.07 | 205 | 99 | 2.08 | yes |

## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median

| Accent | real | predicted | diff |
|---|---|---|---|
| acute | +1.84 | +1.75 | -0.10 |
| circumflex | +0.04 | -0.17 | -0.21 |
| grave | -0.64 | -0.59 | +0.06 |
| none | -0.61 | -0.54 | +0.07 |

Acute − none: real +2.45 st, predicted +2.29 st.

Audio for the listening session: `data/synth/fs2_full/test_pred/` (Iliad 1.1–52) and `val_pred/`.
