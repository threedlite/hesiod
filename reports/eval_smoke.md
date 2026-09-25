# TTS evaluation: smoke

Checkpoint `train/runs/smoke/last.pt`. Recognizer floor on real audio: val 3.22 %, test 4.93 %.

| Set | PER | Pass (≤ 1.5 × real) |
|---|---|---|
| val, predicted durations/pitch | 92.55 % | no |
| test (Iliad 1.1–52), predicted | 90.80 % | no |
| val, teacher-forced durations/pitch (copy synthesis) | 91.13 % | no |

## Duration: vowel duration by syllable quantity (ms)

| | real L | real S | ratio | pred L | pred S | ratio | pass (±10 %) |
|---|---|---|---|---|---|---|---|
| val | 190 | 84 | 2.27 | 205 | 203 | 1.01 | no |

## Pitch: mean log-F0 of vowel tokens by accent, semitones vs utterance median

| Accent | real | predicted | diff |
|---|---|---|---|
| acute | +1.87 | +0.00 | -1.87 |
| circumflex | -1.32 | -0.04 | +1.27 |
| grave | -0.83 | -0.04 | +0.79 |
| none | -1.02 | +0.01 | +1.03 |

Acute − none: real +2.89 st, predicted -0.01 st.

Audio for the listening session: `data/synth/smoke/test_pred/` (Iliad 1.1–52) and `val_pred/`.
