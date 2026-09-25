# TTS evaluation: fs2_2h_v3

Checkpoint `train/runs/fs2_2h_v3/best.pt`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.

| Set | PER | Pass (≤ 1.5 × real) |
|---|---|---|
| val, predicted durations/pitch | 4.24 % | yes |
| test (Iliad 1.1–52), predicted | 4.04 % | yes |
| val, teacher-forced durations/pitch (copy synthesis) | 4.42 % | yes |

## Duration: vowel duration by syllable quantity (ms)

| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |
|---|---|---|---|---|---|---|---|
| val | 206 | 99 | 2.07 | 204 | 97 | 2.10 | yes |

## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median

| Accent | real | predicted | diff |
|---|---|---|---|
| acute | +1.84 | +1.68 | -0.16 |
| circumflex | +0.04 | -0.06 | -0.10 |
| grave | -0.64 | -0.53 | +0.11 |
| none | -0.61 | -0.53 | +0.08 |

Acute − none: real +2.45 st, predicted +2.22 st.

Audio for the listening session: `data/synth/fs2_2h_v3/test_pred/` (Iliad 1.1–52) and `val_pred/`.
