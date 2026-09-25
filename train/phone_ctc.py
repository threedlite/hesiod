#!/usr/bin/env python3
"""Phase 3b: small CTC phone recognizer trained from scratch on the Iliad corpus.

Input : data/iliad/metadata.csv (split, clean_wav), data/iliad/phones.csv (phones column)
Model : 80-dim log-mel (10 ms hop) -> 2 conv layers (4x time subsampling) -> 3-layer BiGRU -> CTC over 40 phones
Output: train/checkpoints/phone_ctc.pt, train/phone_ctc_log.txt, PER on val each epoch.
Usage : python train/phone_ctc.py [--epochs 12] [--limit N] [--eval-only ckpt]
The recognizer is the intelligibility instrument for Phase 4/7: recognize.py uses it to score any audio.
"""
import argparse, csv, json, math, random, sys, time
from pathlib import Path
import wave
import numpy as np, torch, torchaudio, torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
SR, N_MELS, HOP = 22050, 80, 220        # 220 samples ≈ 10 ms at 22.05 kHz
ACCENT = "ˊˋˆ"

def load_wav(path):
    """16-bit mono PCM WAV -> float tensor in [-1, 1] (no torchaudio backend needed)."""
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1 and w.getframerate() == SR, path
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return torch.from_numpy(x)

def phone_seq(s):
    return [p.rstrip(ACCENT) for p in s.split() if p not in (".", "#")]

class Data(torch.utils.data.Dataset):
    def __init__(self, rows, vocab):
        self.rows, self.vocab = rows, vocab
        self.mel = torchaudio.transforms.MelSpectrogram(sample_rate=SR, n_fft=1024, hop_length=HOP, n_mels=N_MELS)
    def __len__(self): return len(self.rows)
    def __getitem__(self, i):
        r = self.rows[i]
        wav = load_wav(ROOT / r["clean_wav"])
        m = torch.log(self.mel(wav) + 1e-6).T                      # (T, 80)
        m = (m - m.mean(0)) / (m.std(0) + 1e-5)
        y = torch.tensor([self.vocab[p] for p in r["phones"]], dtype=torch.long)
        return m, y, r["id"]

def collate(batch):
    xs, ys, ids = zip(*batch)
    xl = torch.tensor([x.shape[0] for x in xs]); yl = torch.tensor([y.shape[0] for y in ys])
    X = nn.utils.rnn.pad_sequence(xs, batch_first=True); Y = torch.cat(ys)
    return X, xl, Y, yl, ids

class Model(nn.Module):
    def __init__(self, n_out, hid=256):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv2d(1, 32, 3, stride=2, padding=1), nn.GELU(),
                                  nn.Conv2d(32, 32, 3, stride=2, padding=1), nn.GELU())
        self.proj = nn.Linear(32 * ((N_MELS + 3) // 4), hid)
        self.rnn = nn.GRU(hid, hid, num_layers=3, bidirectional=True, batch_first=True, dropout=0.15)
        self.out = nn.Linear(2 * hid, n_out)
    def forward(self, x, xl):
        x = self.conv(x.unsqueeze(1))                                 # (B, 32, T/4, F/4)
        b, c, t, f = x.shape
        x = self.proj(x.permute(0, 2, 1, 3).reshape(b, t, c * f))
        xl = torch.div(xl - 1, 4, rounding_mode="floor") + 1
        x = nn.utils.rnn.pack_padded_sequence(x, xl.cpu(), batch_first=True, enforce_sorted=False)
        x, _ = self.rnn(x); x, _ = nn.utils.rnn.pad_packed_sequence(x, batch_first=True)
        return self.out(x).log_softmax(-1), xl

def greedy(logp, xl, inv):
    out = []
    for i in range(logp.shape[0]):
        best = logp[i, :xl[i]].argmax(-1).tolist(); seq, prev = [], 0
        for t in best:
            if t != prev and t != 0: seq.append(inv[t])
            prev = t
        out.append(seq)
    return out

def edit_distance(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = d[j]; d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
    return d[len(b)]

def evaluate(model, loader, inv, dev):
    model.eval(); err = tot = 0; per_utt = []
    with torch.no_grad():
        for X, xl, Y, yl, ids in loader:
            logp, ol = model(X.to(dev), xl.to(dev)); hyps = greedy(logp.cpu(), ol.cpu(), inv)
            k = 0
            for h, n, id_ in zip(hyps, yl.tolist(), ids):
                ref = [inv[t] for t in Y[k:k + n].tolist()]; k += n
                e = edit_distance(h, ref); err += e; tot += n; per_utt.append((id_, e / max(1, n)))
    model.train(); return err / max(1, tot), per_utt

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=12); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=16); ap.add_argument("--eval-only", default=""); args = ap.parse_args()
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu"); print("device", dev)
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open()) if r["status"] == "ok"}
    ph = {r["id"]: phone_seq(r["phones"]) for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}
    rows = [dict(id=i, clean_wav=m["clean_wav"], phones=ph[i], split=m["split"]) for i, m in meta.items() if i in ph and m["split"] in ("train", "val")]
    phones = sorted({p for r in rows for p in r["phones"]}); vocab = {p: i + 1 for i, p in enumerate(phones)}; inv = {i: p for p, i in vocab.items()}
    (ROOT / "train/phone_vocab.json").write_text(json.dumps(vocab, ensure_ascii=False, indent=0))
    tr = [r for r in rows if r["split"] == "train"]; va = [r for r in rows if r["split"] == "val"]
    if args.limit: random.seed(0); tr = random.sample(tr, min(args.limit, len(tr)))
    print(f"train {len(tr)} val {len(va)} phones {len(vocab)}")
    dl = lambda rs, sh: torch.utils.data.DataLoader(Data(rs, vocab), batch_size=args.batch, shuffle=sh, collate_fn=collate, num_workers=0)
    tl, vl = dl(tr, True), dl(va, False)
    model = Model(len(vocab) + 1).to(dev)
    (ROOT / "train/checkpoints").mkdir(exist_ok=True)
    if args.eval_only:
        model.load_state_dict(torch.load(args.eval_only, map_location=dev, weights_only=True)); per, _ = evaluate(model, vl, inv, dev); print(f"val PER {100*per:.2f} %"); return
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    steps = args.epochs * len(tl); sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=steps, pct_start=0.1)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True); log = (ROOT / "train/phone_ctc_log.txt").open("a"); best = 1.0
    for ep in range(args.epochs):
        t0 = time.time(); tot = n = 0
        for X, xl, Y, yl, _ in tl:
            logp, ol = model(X.to(dev), xl.to(dev))
            loss = ctc(logp.transpose(0, 1).cpu(), Y, ol.cpu(), yl)      # CTC has no MPS kernel; loss on CPU
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step(); sched.step()
            tot += loss.item(); n += 1
            if n % 200 == 0: print(f"ep {ep} step {n}/{len(tl)} loss {tot/n:.3f}", flush=True)
        per, _ = evaluate(model, vl, inv, dev)
        msg = f"epoch {ep} loss {tot/max(1,n):.3f} val PER {100*per:.2f} % ({time.time()-t0:.0f}s)"; print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if per < best: best = per; torch.save(model.state_dict(), ROOT / "train/checkpoints/phone_ctc.pt")
    print("best val PER", f"{100*best:.2f} %")

if __name__ == "__main__":
    main()
