# TTS evaluation: fs2_2h_v2

Checkpoint `train/runs/fs2_2h_v2/best.pt`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.

| Set | PER | Pass (≤ 1.5 × real) |
|---|---|---|
| val, predicted durations/pitch | 22.53 % | no |
| test (Iliad 1.1–52), predicted | 22.14 % | no |
| val, teacher-forced durations/pitch (copy synthesis) | 4.16 % | yes |

## Duration: vowel duration by syllable quantity (ms)

| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |
|---|---|---|---|---|---|---|---|
| val | 206 | 99 | 2.07 | 424 | 159 | 2.67 | no |

## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median

| Accent | real | predicted | diff |
|---|---|---|---|
| acute | +1.84 | +2.16 | +0.31 |
| circumflex | +0.04 | -0.24 | -0.28 |
| grave | -0.64 | -0.54 | +0.10 |
| none | -0.61 | -0.59 | +0.02 |

Acute − none: real +2.45 st, predicted +2.74 st.

Audio for the listening session: `data/synth/fs2_2h_v2/test_pred/` (Iliad 1.1–52) and `val_pred/`.
