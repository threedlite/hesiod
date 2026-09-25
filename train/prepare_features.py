#!/usr/bin/env python3
"""Phase 4: per-utterance training features for the explicit-duration acoustic model.

For every usable utterance with a TextGrid:
  mel     Vocos log-mel (100 x T) at 24 kHz, hop 256 (10.667 ms frames), float16
  tokens  phone ids incl. ^ (start), $ (end), # (word boundary); syllable markers dropped
  q/acc/foot   per-token syllable quantity (0 none/1 L/2 S), accent (0 none/1 A/2 G/3 C), foot 0-6
  dur     frames per token from the MFA phone tier; silences go to ^, $, # (or extend the previous phone)
  f0      per-token mean log-F0 of voiced frames (0 = unvoiced), parselmouth
  energy  per-token mean log frame energy
Writes data/features/<id>.npz and data/features/index.csv. Parallel over 8 processes.
"""
import csv, json, sys, wave, math
from multiprocessing import Pool
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from textgrid import read_textgrid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/features"; TG = ROOT / "align/textgrids/chamberlain"
SR_IN, SR, HOP = 22050, 24000, 256
FPS = SR / HOP
ACCENT = "ˊˋˆ"; QMAP = {"L": 1, "S": 2}; AMAP = {"A": 1, "G": 2, "C": 3}
SPECIAL = ["^", "$", "#"]

_vocos = None
def vocos():
    global _vocos
    if _vocos is None:
        import torch; torch.set_num_threads(1)
        from vocos import Vocos; _vocos = Vocos.from_pretrained("charactr/vocos-mel-24khz")
    return _vocos

def load_wav(p):
    with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

def tokens_of(row):
    """Token list with per-token features from a phones.csv row."""
    toks = [("^", 0, 0, 0)]
    q, acc, foot = row["quantity"], row["accent"], row["foot"]
    si = 0
    for wi, word in enumerate(row["phones"].split("#")):
        if wi: toks.append(("#", 0, 0, 0))
        for syl in word.strip().split("."):
            ph = [p.rstrip(ACCENT) for p in syl.split() if p]
            if not ph: continue
            for p in ph: toks.append((p, QMAP.get(q[si], 0), AMAP.get(acc[si], 0), int(foot[si]) if foot[si].isdigit() else 0))
            si += 1
    toks.append(("$", 0, 0, 0))
    return toks, si

def process(args):
    id_, wav_path, row, split = args
    try:
        import torch, torchaudio, parselmouth
        x = load_wav(ROOT / wav_path)
        x24 = torchaudio.functional.resample(torch.from_numpy(x), SR_IN, SR)
        with torch.no_grad(): mel = vocos().feature_extractor(x24.unsqueeze(0))[0].numpy()     # (100, T)
        T = mel.shape[1]
        toks, n_syll = tokens_of(row)
        # durations from the TextGrid
        tg = read_textgrid(TG / f"{id_}.TextGrid")["phones"]
        dur = [0] * len(toks); ti = 1                        # ti: next phone token index (0 is ^)
        n_phone_tokens = sum(1 for t in toks if t[0] not in SPECIAL)
        for a, b, lab in tg:
            fa, fb = int(round(a * FPS)), int(round(b * FPS)); n = max(0, fb - fa)
            if lab in ("", "sil", "sp", "spn"):
                if ti == 1: dur[0] += n                                        # leading silence -> ^
                elif ti >= len(toks) - 1 or all(t[0] in SPECIAL for t in toks[ti:]): dur[-1] += n   # trailing -> $
                elif toks[ti][0] == "#": dur[ti] += n                          # pause at a word boundary
                else: dur[ti - 1] += n                                         # mid-word silence: extend previous phone
                continue
            while ti < len(toks) and toks[ti][0] == "#": ti += 1              # skip boundary tokens without pause
            if ti >= len(toks) - 1 or toks[ti][0] != lab: return (id_, f"phone_mismatch at {ti}: {lab} vs {toks[ti][0] if ti < len(toks) else None}")
            dur[ti] += n; ti += 1
        total = sum(dur); dur[-1] += T - total                                 # rounding: absorb in $
        if dur[-1] < 0: dur[-2] += dur[-1]; dur[-1] = 0
        if min(dur) < 0 or sum(dur) != T: return (id_, f"duration_sum {sum(dur)} vs {T}")
        # F0 per frame, then per token
        snd = parselmouth.Sound(x24.numpy().astype(np.float64), sampling_frequency=SR)
        pitch = snd.to_pitch(time_step=HOP / SR, pitch_floor=60, pitch_ceiling=300)
        f0 = np.zeros(T, dtype=np.float32)
        pf = pitch.selected_array["frequency"]; pt = pitch.xs()
        idx = np.clip(np.round(pt * FPS).astype(int), 0, T - 1); f0[idx] = pf
        energy_frame = np.log(np.exp(mel).mean(0) + 1e-6).astype(np.float32)
        f0_tok = np.zeros(len(toks), dtype=np.float32); en_tok = np.zeros(len(toks), dtype=np.float32)
        pos = 0
        for i, d in enumerate(dur):
            seg = f0[pos:pos + d]; v = seg[seg > 0]
            f0_tok[i] = np.log(v).mean() if len(v) else 0.0
            en_tok[i] = energy_frame[pos:pos + d].mean() if d > 0 else 0.0
            pos += d
        np.savez_compressed(OUT / f"{id_}.npz", mel=mel.astype(np.float16), tokens=np.array([t[0] for t in toks]),
                            q=np.array([t[1] for t in toks], dtype=np.int8), acc=np.array([t[2] for t in toks], dtype=np.int8),
                            foot=np.array([t[3] for t in toks], dtype=np.int8), dur=np.array(dur, dtype=np.int32), f0=f0_tok, energy=en_tok)
        return (id_, "ok", T, len(toks), split)
    except Exception as e:
        return (id_, f"error: {e!r}")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open()) if r["status"] == "ok"}
    ph = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}
    jobs = [(i, m["clean_wav"], ph[i], m["split"]) for i, m in meta.items() if i in ph and (TG / f"{i}.TextGrid").exists()]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    if limit: jobs = jobs[:limit]
    results = []
    with Pool(8) as pool:
        for k, r in enumerate(pool.imap_unordered(process, jobs, chunksize=8)):
            results.append(r)
            if k % 1000 == 0: print(f"{k}/{len(jobs)}", file=sys.stderr, flush=True)
    ok = [r for r in results if r[1] == "ok"]; bad = [r for r in results if r[1] != "ok"]
    with (OUT / "index.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "split", "n_frames", "n_tokens"])
        for id_, _, T, n, split in sorted(ok): w.writerow([id_, split, T, n])
    with (OUT / "failed.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "reason"]); w.writerows(bad)
    print(f"ok {len(ok)}, failed {len(bad)}; frames {sum(r[2] for r in ok)} ({sum(r[2] for r in ok)/FPS/3600:.2f} h)")
    for r in bad[:10]: print("  ", r)

if __name__ == "__main__":
    main()
