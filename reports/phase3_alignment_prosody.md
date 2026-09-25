# Phase 3: alignment, prosody baseline, acoustic speaker profile

Date: 2026-09-23. MFA 3.4.2, acoustic model trained from scratch on the corpus
(`align/chamberlain_acoustic.zip`, 57 min on 8 cores), scoring alignment exported
with per-utterance analysis. Scripts: `align/run_align.sh`, `scripts/build_mfa_corpus.py`,
`scripts/alignment_qc.py`, `scripts/prosody_baseline.py`. Data:
`align/textgrids/`, `data/iliad/alignment_scores.csv`, `data/iliad/syllable_acoustics.csv`
(244,840 syllables with duration, F0 and formant measures).

## Alignment QC (`reports/alignment_qc.md`)

- 15,582 utterances submitted; 15,573 aligned; 9 produced no alignment and are now
  excluded (`alignment_failed`): 2.551, 4.260, 4.399, 5.65, 5.370, 6.343, 13.221,
  16.250, 16.251. Two of them (2.551, 4.260) were the shortest clips flagged in
  Phase 1, so the audio almost certainly does not contain the text. The 16.249–252
  cluster also scores worst among the aligned lines, suggesting a shifted or
  mis-numbered stretch there.
- Speech log-likelihood per frame: median −44.7, p1 −51.4, p99 −38.9. The
  bottom 1 % (156 utterances, ranked by a combined suspicion score) are listed in
  `data/iliad/alignment_scores.csv` and appended to `notes/human_qa_queue.md`.
- Usable corpus after all exclusions: 15,632 lines (train 15,269 / val 311 / test 52).

## Prosody baseline

**Quantity is strongly realized.** Long syllables average 367 ms, short 220 ms
(ratio 1.67, Cohen's d = 1.18). Long vowels are about twice their short
counterparts (a 111 ms vs aː 207; i 109 vs iː 252; y 95 vs yː 218; e 101 vs eː 246).

**Pitch accent is present but conservative** (semitones relative to the
utterance median; n = 244,840 syllables):

| Accent | mean F0 | within-syllable slope | fall from peak | d(mean) vs none | d(fall) vs none |
|---|---|---|---|---|---|
| acute (n 59,119) | +1.58 | +0.95 rising | 2.79 | +0.41 | −0.19 |
| circumflex (n 13,910) | +0.23 | −0.29 | 4.85 | +0.09 | +0.26 |
| grave (n 23,115) | −0.17 | −0.01 | 3.04 | 0.00 | −0.13 |
| none (n 145,907) | −0.16 | −0.61 | 3.64 | 0 | 0 |

The pattern is Allen's: the acute is a rise (higher mean, rising slope), the
circumflex a rise then fall (larger fall from peak, near-zero net slope), and the
grave is indistinguishable from an unaccented syllable. But the effect sizes are
below the plan's 0.5 threshold (acute 0.41, circumflex 0.26), matching his own
description of "a very conservative pitch accent".

**Decision (Product A vs B).** A model trained on this data will reproduce a
real but subtle accent. Product A (Chamberlain-style) is the default deliverable
and is produced first. Product B (Phase 7b, F0 shaping driven by the accent
marks) is planned as the stretch deliverable, with these baseline contours as
the shape to amplify, not to invent. Recorded in `notes/decisions.md`.

## Acoustic speaker profile (inferred, not heard)

| Feature | Measurement | Inference | Effect on labels |
|---|---|---|---|
| ζ | z part 159 ms + stop part 73 ms (1 % at the 30 ms floor), vs plain δ 92 ms | a stop is present: [zd] as labeled | none |
| φ θ χ vs π τ κ | 121/130/127 ms vs 120/124/128 ms | no extra duration: aspiration weak or absent, not fricatives (those would be longer) | none needed; the labels stay distinct, the model learns his sounds |
| υ | F1 312, F2 1422 (short), F2 1855 (long); i has F2 2104, uː 656 | front rounded [y]-like, long υ very fronted | none |
| ει | F1 373, F2 2096, F2 rises +299 Hz across the vowel | a rising diphthong [ei], not a monophthong [eː] | label kept as `eː`; document |
| ου | F2 656, movement −15 | monophthong [uː] | none |
| η | F1 544, F2 1863 ≈ ε (580, 1778) | same quality as ε, i.e. [eː] not open [ɛː] | label kept; document |
| ω vs ο | ω F1 390, F2 664; ο F1 619, F2 981 | ω is close [oː], ο is open [ɔ]: the reverse of Allen's openness | label kept; document |
| grave | F0 = unaccented | no rise on the grave, as Allen | none |

Since labels are only identifiers the model learns from his audio, no
re-rendering is needed: Hesiod synthesized with the same labels will carry his
values. The IPA symbols in the reports describe Allen's targets, not his output;
the table above is the correction. Digamma was not measured (no token yet).

## Phase 3b: phone recognizer

`train/phone_ctc.py`: 80-band log-mel → two conv layers (4× subsampling) → 3-layer
BiGRU → CTC over the 40 phones, trained from scratch on the 15,269 training lines
for 8 epochs (~12 min each on the M4 GPU; CTC loss on CPU since MPS lacks the
kernel). Checkpoint `train/checkpoints/phone_ctc.pt`, vocabulary
`train/phone_vocab.json`.

| Epoch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| val PER | 9.13 % | 6.54 % | 5.04 % | 4.35 % | 3.78 % | 3.41 % | 3.33 % | 3.22 % |

**Intelligibility floor: 3.22 % PER on real audio** (validation split, 311 lines
spread across the books). On the held-out test passage Iliad 1.1–52 it is 4.93 %
(`data/iliad/recognizer_test_per.csv`); those are the first lines he recorded, and
he notes that his pace varied in the early books, so the passage is slightly
atypical of the corpus. `train/recognize.py`
scores any audio against an intended phone string, which is the Phase 4 and 7
instrument: synthesized audio should stay within 1.5 × this floor.

## Next

- Phase 4: fix the token format, train the TTS baseline on a 2 h subset.
