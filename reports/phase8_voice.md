# Phase 8: female voice by WORLD conversion

Date: 2026-09-24. Code: `scripts/convert_voice.py` (pyworld: harvest+stonemask, CheapTrick, D4C), `scripts/eval_voice.py` (checks), `scripts/grid_voice.py` (search). Search data: `data/synth/voice_grid/results.csv` (96 settings × 40 Hesiod lines).

## What the search showed

Recognizer PER depends almost only on the formant warp; pitch shift, spectral tilt, breathiness and the first-harmonic boost barely move it:

| Factor | Levels → mean PER over the other factors |
|---|---|
| F0 shift (st) | 7: 19.2 %, 8: 18.9 %, 9: 18.6 % |
| formant warp α₁ (0–1 kHz) | 1.14: 11.8 %, 1.18: 19.1 %, 1.22: 22.3 % |
| formant warp α₂ (>1.5 kHz) | 1.14: 11.8 %, 1.16: 18.4 %, 1.18: 19.1 %, 1.22: 26.2 % |
| tilt (dB/oct) | 0: 18.8 %, 2: 19.0 % |
| breathiness | 0: 19.1 %, 0.05: 18.7 % |
| H1 boost (dB) | 0: 18.8 %, 1.0: 19.0 % |

The recognizer was trained on Chamberlain's male voice, so it reads formant position as phonetic content: the more female the vocal tract, the worse it scores. Selecting by lowest PER would therefore always choose the least-converted voice. PER is kept as a relative guard (does a setting break articulation beyond what its warp implies?) and the choice is made on acoustic targets.

Two measurement artifacts were identified and handled: the pitch tracker octave-jumped on converted audio with a 500 Hz ceiling (fixed at 400 Hz), and the accent-contrast check failed on all 96 settings by the same 0.58–0.60 st, a constant offset between tracking WORLD output and Vocos output rather than any change in the contours (F0 is scaled by a constant, so intervals are preserved by construction; verified frame-by-frame at 7.5 ± 0.4 st on 95 % of frames).

## Chosen setting (revised after listening)

The grid's acoustic-target choice (+8 st, two-band warp 1.22/1.16, breathiness
0.05) was converted in full and then compared by ear on Works and Days 1–3 with
the mildest grid setting. The listener preferred the mild one: the larger warp
gave a hollow, metallic quality and the added breathiness put noise in the upper
bands. The larger-warp conversion is kept as `hesiod_fs2_full_female_v1` for
reference; the package is rebuilt from the mild setting.

| Control | Value | Measured on 40 lines (grid) |
|---|---|---|
| F0 | +7 st | median 137 → 205 Hz |
| formant warp | uniform 1.14 | F1 × 1.13, F2 × 1.10 |
| spectral tilt, H1 boost, breathiness | 0 | H1−H2 +3.6 dB, HNR +3.8 dB |
| duration, pauses, accent intervals | unchanged | |
| PER (relative guard) | 10.9 % vs 5.0 % unconverted | lowest of the grid |

Lesson recorded: the +15–20 % formant targets from the literature describe real
female vocal tracts, not how far a warped male envelope can be stretched before
WORLD's resynthesis sounds processed. The recognizer's steep PER rise with the
warp, read at first as pure male-training bias, was partly real degradation. For
this pipeline the usable range is about +12–15 % formants and +7 st; a more
convincingly female voice would need a different method (a neural converter
trained on female speech, at the cost of the guaranteed accent preservation).

## Full conversion

All 2,338 Hesiod lines and the Iliad test passage (1.1–52) converted with the revised
setting: `data/synth/hesiod_fs2_full_female/wav/`, `data/synth/fs2_full_female/test_pred/`.
Package `data/synth/hesiod_fs2_full/hesiod_chamberlain_tts_female.zip` (2,328 files after the 14 recovered lines,
146 MB, same layout and exclusions as the original; the original package is untouched).

Checks on all 2,338 lines (`data/synth/hesiod_fs2_full_female/eval_full.json`), revised setting:

| Check | Result | Target |
|---|---|---|
| F0 median | 136 → 206 Hz | 200–240 |
| F1 ratio, mean over vowels | 1.13 | intended 1.14 |
| F2 ratio, mean over vowels | 1.11 | intended 1.14 |
| H1−H2 | -3.3 → +0.8 dB (+4.1) | +2 to +5 |
| HNR | 8.5 → 12.2 dB | not below −3 |
| accent contrasts vs unaccented, st | acute 2.13 → 2.32, circumflex 0.53 → 0.75, grave 0.15 → -0.01 | within 0.5 |
| PER, relative guard | 3.13 % → 11.31 % (median line 11.1 %, p95 21.9 %); 11 lines above 30 % | see above |

Timing is unchanged by construction, so the quantity ratio is the original's.

## What only a listener can settle

- Does it read as a woman rather than a raised man? (Play `wav/tlg001_1.wav` against
  `data/synth/hesiod_fs2_full/wav/tlg001_1.wav`.)
- The 11 lines with converted PER above 30 % (top of `eval/conv_per.csv`): are they
  degraded, or merely shifted for a recognizer that never heard a higher voice?
- Whether the conservative setting (+7 st, +14 % formants) is preferable; it is one
  command away with `scripts/convert_voice.py`.
