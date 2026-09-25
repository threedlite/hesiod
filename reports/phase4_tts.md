# Phase 4: acoustic model training and evaluation

Date: 2026-09-24. Code: `train/prepare_features.py`, `train/fs2.py`, `train/eval_tts.py`.
Decisions: `notes/decisions.md` (explicit-duration model + Vocos; input format).

## Setup

- **Features** (`data/features/`, 15,573 utterances, 23.05 h): Vocos 100-bin log-mel at
  24 kHz (hop 256 = 10.67 ms), per-token durations from the MFA phone tier with pauses
  assigned to ^ / # / $ tokens, per-token mean log-F0 (parselmouth) and log-energy.
- **Model**: phone + quantity + accent + foot embeddings (d = 256) → 4 FFT blocks →
  duration / pitch / energy predictors on the detached encoder output → pitch and
  energy bin embeddings → length regulation → 4 FFT blocks → 100-bin mel + 5-layer
  postnet. Losses: L1 mel (before and after postnet), MSE log-duration, MSE pitch on
  voiced tokens, MSE energy. AdamW, warmup + cosine. Apple GPU (M4), with 1-D convs
  expressed as 2-D and a contiguous-gradient shim (MPS backward quirk).
- **Vocoder**: pretrained `charactr/vocos-mel-24khz`, no training; verified transparent
  to the recognizer (PER 3.67 % on vocoded real clips = original).

## Early read: 2 h subset, first attempt, epoch 19 of 40 (`reports/eval_fs2_2h_ep19.md`)

| Condition | PER | Note |
|---|---|---|
| copy synthesis (real durations and pitch, predicted mel) | 4.12 % | passes the 1.5 × 3.22 % gate: the spectral model is already good |
| predicted durations and pitch, test passage | 28.3 % | fails: vowels twice too long (L 425 vs 206 ms, S 170 vs 97) |

Pitch by accent was already right in shape: acute − unaccented +2.65 st predicted vs
+2.12 real. Two defects explained the duration failure and were fixed before the
second attempt: the variance predictors were not detached from the encoder (the
reference design detaches them; without it the predictor overfits the small subset,
validation duration loss rose after epoch 5), and inference forgot to subtract the 1
inside the log(dur + 1) target.

## 2 h subset, second attempt (`train/runs/fs2_2h_v2`, `reports/eval_fs2_2h_v2.md`)

Copy synthesis 4.16 % PER (pass); predicted mode 22.5 % val / 22.1 % test (fail);
vowel durations still 2× too long (L 424 vs 206 ms). Pitch contrasts right
(acute − unaccented +2.74 st predicted vs +2.45 real; grave = unaccented).

Diagnosis by direct measurement of the duration predictor against its targets:

| Utterances | Mode | bias in log-duration | RMSE |
|---|---|---|---|
| training subset | eval | +0.45 | 0.58 |
| validation | eval | +0.47 | 0.75 |
| validation | train (dropout on) | +0.01 | 0.49 |

The bias is present on training data in eval mode and absent with dropout on, so it
is a train/eval discrepancy, not overfitting: the predictor applied dropout *before*
its LayerNorm, and the output layer learned on sparse, rescaled activations it never
sees at inference. The reference FastSpeech2 order is conv → ReLU → LayerNorm →
dropout. Fixed for the third attempt. (The same class serves the pitch and energy
predictors; pitch was unaffected in the report because the accent metric is relative
to the utterance median, which cancels a constant offset.)

## 2 h subset, third attempt (`train/runs/fs2_2h_v3`, 25 epochs, `reports/eval_fs2_2h_v3.md`)

All gates pass with 2 h of training data:

| Metric | Result | Gate |
|---|---|---|
| PER, val, predicted durations and pitch | 4.24 % | ≤ 4.83 % (1.5 × 3.22) |
| PER, test passage Iliad 1.1–52, predicted | 4.04 % | ≤ 7.40 % (1.5 × 4.93) |
| PER, val, copy synthesis | 4.42 % | ≤ 4.83 % |
| vowel duration long : short | 2.10 (204 / 97 ms) vs real 2.07 (206 / 99) | ±10 % |
| acute − unaccented pitch | +2.22 st vs real +2.45 | within 10 points |
| circumflex, grave, none | all within 0.16 st of real | |

Validation duration loss fell from 0.45 to 0.16 with the LayerNorm/dropout fix, and
the train/val gap closed. The pipeline is proven end to end; M4 done.

## Hesiod dry run with the subset model (`reports/hesiod_qc_fs2_2h_v3.md`)

`scripts/synth_hesiod.py` on the first 300 Theogony lines: corpus PER 4.47 %
(median line 3.1 %, p95 11.5 %), the same level as unseen Iliad lines, so the
model generalizes to Hesiod's text. 21 lines (7 %) stay above the 10 % per-line
threshold after the duration-scale retries; the package gate is 1 %. The worst
lines are the catalogues of names (Theogony 200–280: Nereids, Harpies, Gorgons),
whose phone sequences are rare in the Iliad. Part of that PER is the recognizer's
own uncertainty on rare sequences, which cannot be separated without real Hesiod
audio; the full model and, if needed, a lower per-line threshold for name-heavy
lines are the levers.

## Full corpus (`train/runs/fs2_full`, 30 epochs of ~15 min, `reports/eval_fs2_full.md`)

Validation post-net mel L1 0.665 (subset model: 0.770). Evaluation, all automatic:

| Metric | Result | Gate |
|---|---|---|
| PER, val, predicted durations and pitch | **2.36 %** | ≤ 4.83 % |
| PER, test passage Iliad 1.1–52, predicted | **2.37 %** | ≤ 7.40 % |
| PER, val, copy synthesis | 2.97 % | ≤ 4.83 % |
| vowel duration long : short | 2.08 (205 / 99 ms) vs real 2.07 | ±10 % |
| acute − unaccented pitch | +2.29 st vs real +2.45 | |
| circumflex / grave / none | within 0.21 st of real | |

The synthesized speech scores *lower* PER than Chamberlain's own recordings
(3.22 % val, 4.93 % test): the model produces the canonical version of his
pronunciation without the recording's noise gate artifacts, breaths and pace
variation. This is the model used for Hesiod (Phase 7).

Not measured (instruments not installed): MOS predictor and speaker-embedding
similarity from §4 of the plan; the audio for the listening session is in
`data/synth/fs2_full/test_pred/` and `val_pred/`.

