# TTS evaluation: fs2_2h_ep19

Checkpoint `train/runs/fs2_2h/best_ep19.pt`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.

| Set | PER | Pass (≤ 1.5 × real) |
|---|---|---|
| val, predicted durations/pitch | 26.00 % | no |
| test (Iliad 1.1–52), predicted | 28.31 % | no |
| val, teacher-forced durations/pitch (copy synthesis) | 4.12 % | yes |

## Duration: vowel duration by syllable quantity (ms)

| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |
|---|---|---|---|---|---|---|---|
| val | 206 | 97 | 2.13 | 425 | 170 | 2.50 | no |

## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median

| Accent | real | predicted | diff |
|---|---|---|---|
| acute | +1.66 | +2.05 | +0.40 |
| circumflex | +0.48 | -0.74 | -1.22 |
| grave | -0.00 | +0.05 | +0.05 |
| none | -0.46 | -0.60 | -0.14 |

Acute − none: real +2.12 st, predicted +2.65 st.

Audio for the listening session: `data/synth/fs2_2h_ep19/test_pred/` (Iliad 1.1–52) and `val_pred/`.
