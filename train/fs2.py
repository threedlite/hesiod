#!/usr/bin/env python3
"""Phase 4: explicit-duration acoustic model (FastSpeech2-style) with pitch/energy predictors.

Input tokens: phone id + syllable quantity + accent + foot embeddings.
Targets: Vocos 100-bin log-mel at 24 kHz; per-token duration (frames), log-F0, log-energy.
Usage:
  python train/fs2.py train --hours 2 --epochs 40          # subset run
  python train/fs2.py train --epochs 30                    # full corpus
  python train/fs2.py synth --ckpt ... --ids b1_l1,... --out dir [--teacher]   # -> 22.05 kHz wavs via Vocos
"""
import argparse, csv, json, math, random, sys, time, wave
from pathlib import Path
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]; FEAT = ROOT / "data/features"
SR, HOP, N_MEL = 24000, 256, 100
SPECIAL = ["^", "$", "#"]

# ---------------- data ----------------
def load_vocab():
    v = json.load((ROOT / "train/phone_vocab.json").open())            # phones 1..40
    vocab = dict(v)
    for s in SPECIAL: vocab[s] = len(vocab) + 1
    return vocab                                                        # 0 = pad

class DS(torch.utils.data.Dataset):
    def __init__(self, ids, vocab, stats): self.ids, self.vocab, self.stats = ids, vocab, stats
    def __len__(self): return len(self.ids)
    def __getitem__(self, i):
        d = np.load(FEAT / f"{self.ids[i]}.npz")
        tok = torch.tensor([self.vocab[t] for t in d["tokens"]])
        f0 = d["f0"].astype(np.float32); f0n = np.where(f0 > 0, (f0 - self.stats["f0_mean"]) / self.stats["f0_std"], 0.0)
        en = (d["energy"].astype(np.float32) - self.stats["en_mean"]) / self.stats["en_std"]
        return dict(id=self.ids[i], tok=tok, q=torch.tensor(d["q"]).long(), acc=torch.tensor(d["acc"]).long(), foot=torch.tensor(d["foot"]).long(),
                    dur=torch.tensor(d["dur"]).long(), f0=torch.tensor(f0n).float(), en=torch.tensor(en).float(),
                    mel=torch.tensor(d["mel"].astype(np.float32)).T)     # (T, 100)

def collate(b):
    pad = lambda k, v=0: nn.utils.rnn.pad_sequence([x[k] for x in b], batch_first=True, padding_value=v)
    out = {k: pad(k) for k in ("tok", "q", "acc", "foot", "dur", "f0", "en", "mel")}
    out["tok_len"] = torch.tensor([len(x["tok"]) for x in b]); out["mel_len"] = torch.tensor([x["mel"].shape[0] for x in b]); out["id"] = [x["id"] for x in b]
    return out

def compute_stats(ids):
    f0s, ens = [], []
    for i in ids[:3000]:
        d = np.load(FEAT / f"{i}.npz"); f0s.append(d["f0"][d["f0"] > 0]); ens.append(d["energy"][1:-1])
    f0s, ens = np.concatenate(f0s), np.concatenate(ens)
    return dict(f0_mean=float(f0s.mean()), f0_std=float(f0s.std()), en_mean=float(ens.mean()), en_std=float(ens.std()))

# ---------------- model ----------------
class ContigGrad(torch.autograd.Function):
    """Identity whose backward makes the incoming gradient contiguous (MPS conv backward needs it)."""
    @staticmethod
    def forward(ctx, x): return x
    @staticmethod
    def backward(ctx, g): return g.contiguous()

class Conv1d(nn.Module):
    """Conv1d expressed as Conv2d over (B, C, 1, T) with a contiguous gradient: works on MPS."""
    def __init__(self, cin, cout, k, padding=0):
        super().__init__(); self.c = nn.Conv2d(cin, cout, (1, k), padding=(0, padding))
    def forward(self, x): return ContigGrad.apply(self.c(ContigGrad.apply(x.unsqueeze(2).contiguous()))).squeeze(2)

class FFT(nn.Module):
    def __init__(self, d, heads=2, k=9, drop=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(d, heads, dropout=drop, batch_first=True); self.ln1 = nn.LayerNorm(d)
        self.conv = nn.Sequential(Conv1d(d, 4 * d, k, padding=k // 2), nn.ReLU(), nn.Dropout(drop), Conv1d(4 * d, d, k, padding=k // 2)); self.ln2 = nn.LayerNorm(d); self.drop = nn.Dropout(drop)
    def forward(self, x, pad_mask):
        x = x.contiguous(); a, _ = self.attn(x, x, x, key_padding_mask=pad_mask); x = self.ln1(x + self.drop(a))
        c = self.conv(x.transpose(1, 2).contiguous()).transpose(1, 2).contiguous(); x = self.ln2(x + self.drop(c))
        return x.masked_fill(pad_mask.unsqueeze(-1), 0.0)

class Predictor(nn.Module):
    """FastSpeech2 variance predictor: (conv → ReLU → LayerNorm → dropout) × 2 → linear.
    LayerNorm must come before dropout; with dropout first, the output layer learns on sparse
    rescaled activations and is biased at inference (measured: +0.45 in log-duration)."""
    def __init__(self, d, k=3, drop=0.3):
        super().__init__()
        self.c1, self.c2 = Conv1d(d, d, k, padding=k // 2), Conv1d(d, d, k, padding=k // 2)
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d); self.drop = nn.Dropout(drop); self.out = nn.Linear(d, 1)
    def forward(self, x):
        h = F.relu(self.c1(x.transpose(1, 2).contiguous())).transpose(1, 2).contiguous(); h = self.drop(self.ln1(h))
        h = F.relu(self.c2(h.transpose(1, 2).contiguous())).transpose(1, 2).contiguous(); h = self.drop(self.ln2(h))
        return self.out(h).squeeze(-1)

def sinusoid(n, d):
    pos = torch.arange(n).unsqueeze(1); div = torch.exp(torch.arange(0, d, 2) * (-math.log(10000.0) / d))
    pe = torch.zeros(n, d); pe[:, 0::2] = torch.sin(pos * div); pe[:, 1::2] = torch.cos(pos * div); return pe

def length_regulate(x, dur, max_len=None):
    B, N, D = x.shape; out = []
    for b in range(B):
        idx = torch.repeat_interleave(torch.arange(N, device=x.device), dur[b].clamp(min=0)); out.append(x[b].index_select(0, idx))
    L = max_len or max(o.shape[0] for o in out)
    y = x.new_zeros(B, L, D)
    for b, o in enumerate(out): y[b, :min(L, o.shape[0])] = o[:L]
    return y

class FS2(nn.Module):
    def __init__(self, n_vocab, d=256, n_enc=4, n_dec=4, n_bins=256):
        super().__init__()
        self.emb = nn.Embedding(n_vocab + 1, d, padding_idx=0); self.q = nn.Embedding(3, d); self.acc = nn.Embedding(4, d); self.foot = nn.Embedding(7, d)
        self.register_buffer("pe", sinusoid(4000, d)); self.enc = nn.ModuleList([FFT(d) for _ in range(n_enc)]); self.dec = nn.ModuleList([FFT(d) for _ in range(n_dec)])
        self.dur_p, self.f0_p, self.en_p = Predictor(d), Predictor(d), Predictor(d)
        self.f0_bins = nn.Parameter(torch.linspace(-3, 3, n_bins - 1), requires_grad=False); self.f0_emb = nn.Embedding(n_bins, d)
        self.en_bins = nn.Parameter(torch.linspace(-3, 3, n_bins - 1), requires_grad=False); self.en_emb = nn.Embedding(n_bins, d)
        self.mel = nn.Linear(d, N_MEL)
        self.post = nn.Sequential(*[nn.Sequential(Conv1d(N_MEL if i == 0 else 256, 256 if i < 4 else N_MEL, 5, padding=2), nn.BatchNorm1d(256 if i < 4 else N_MEL), nn.Tanh() if i < 4 else nn.Identity(), nn.Dropout(0.3)) for i in range(5)])
    def encode(self, tok, q, acc, foot):
        pad = tok == 0
        x = self.emb(tok) + self.q(q) + self.acc(acc) + self.foot(foot) + self.pe[:tok.shape[1]]
        for l in self.enc: x = l(x, pad)
        return x, pad
    def forward(self, b, teacher=True, dur_scale=1.0, f0_shift=0.0):
        x, pad = self.encode(b["tok"], b["q"], b["acc"], b["foot"])
        xd = x.detach()                                   # variance predictors do not shape the encoder (FastSpeech2)
        log_dur = self.dur_p(xd); f0 = self.f0_p(xd); en = self.en_p(xd)
        if teacher: dur, f0_used, en_used = b["dur"], b["f0"], b["en"]
        else:
            dur = ((torch.exp(log_dur) - 1) * dur_scale).round().long().clamp(min=0).masked_fill(pad, 0)   # target was log(dur + 1)
            f0_used = (f0 + f0_shift).masked_fill(pad, 0); en_used = en.masked_fill(pad, 0)
        x = x + self.f0_emb(torch.bucketize(f0_used, self.f0_bins)) + self.en_emb(torch.bucketize(en_used, self.en_bins))
        y = length_regulate(x, dur, b["mel"].shape[1] if teacher else None)
        mpad = torch.arange(y.shape[1], device=y.device).unsqueeze(0) >= dur.sum(1).unsqueeze(1)
        y = y + self.pe[:y.shape[1]]
        for l in self.dec: y = l(y, mpad)
        mel = self.mel(y); mel_post = mel + self.post(mel.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
        return dict(mel=mel, mel_post=mel_post, log_dur=log_dur, f0=f0, en=en, dur=dur, mpad=mpad, pad=pad)

def losses(out, b):
    pad = out["pad"]; mpad = out["mpad"]
    mmask = (~mpad).unsqueeze(-1).float(); tmask = (~pad).float()
    l_mel = (F.l1_loss(out["mel"], b["mel"], reduction="none") * mmask).sum() / mmask.sum() / N_MEL
    l_post = (F.l1_loss(out["mel_post"], b["mel"], reduction="none") * mmask).sum() / mmask.sum() / N_MEL
    l_dur = (F.mse_loss(out["log_dur"], torch.log(b["dur"].float() + 1), reduction="none") * tmask).sum() / tmask.sum()
    vmask = tmask * (b["f0"] != 0).float()
    l_f0 = (F.mse_loss(out["f0"], b["f0"], reduction="none") * vmask).sum() / vmask.sum().clamp(min=1)
    l_en = (F.mse_loss(out["en"], b["en"], reduction="none") * tmask).sum() / tmask.sum()
    return l_mel + l_post + l_dur + 0.5 * l_f0 + 0.5 * l_en, dict(mel=l_mel.item(), post=l_post.item(), dur=l_dur.item(), f0=l_f0.item(), en=l_en.item())

# ---------------- train / synth ----------------
def to(b, dev): return {k: (v.to(dev) if torch.is_tensor(v) else v) for k, v in b.items()}

def train(args):
    dev = torch.device("cpu" if args.cpu else ("mps" if torch.backends.mps.is_available() else "cpu")); print("device", dev)
    if args.anomaly: torch.autograd.set_detect_anomaly(True)
    idx = list(csv.DictReader((FEAT / "index.csv").open()))
    tr = [r for r in idx if r["split"] == "train"]; va = [r for r in idx if r["split"] == "val"]
    random.seed(0); random.shuffle(tr)
    if args.hours:
        frames, sel = 0, []
        for r in tr:
            sel.append(r); frames += int(r["n_frames"])
            if frames / (SR / HOP) / 3600 >= args.hours: break
        tr = sel
    tr_ids = [r["id"] for r in tr]; va_ids = [r["id"] for r in va]
    vocab = load_vocab(); stats = compute_stats(tr_ids)
    run = ROOT / "train/runs" / args.name; run.mkdir(parents=True, exist_ok=True)
    json.dump(dict(stats=stats, vocab=vocab, args=vars(args)), (run / "config.json").open("w"), ensure_ascii=False, indent=1)
    print(f"train {len(tr_ids)} utts ({sum(int(r['n_frames']) for r in tr)/(SR/HOP)/3600:.2f} h), val {len(va_ids)}")
    # length-bucketed batches
    tr.sort(key=lambda r: int(r["n_frames"])); batches = [tr[i:i + args.batch] for i in range(0, len(tr), args.batch)]
    ds = DS(tr_ids, vocab, stats); pos = {i: k for k, i in enumerate(tr_ids)}
    vdl = torch.utils.data.DataLoader(DS(va_ids, vocab, stats), batch_size=args.batch, collate_fn=collate)
    model = FS2(len(vocab)).to(dev); opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.98), weight_decay=1e-2)
    total = args.epochs * len(batches); warm = max(1, min(1000, total // 10))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * (0.5 * (1 + math.cos(math.pi * min(1.0, max(0, s - warm) / max(1, total - warm))))))
    log = (run / "log.txt").open("a"); best = 1e9; step = 0
    for ep in range(args.epochs):
        random.shuffle(batches); model.train(); t0 = time.time(); agg = {}
        for bt in batches:
            b = to(collate([ds[pos[r["id"]]] for r in bt]), dev)
            out = model(b, teacher=True); loss, parts = losses(out, b)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); step += 1
            for k, v in parts.items(): agg[k] = agg.get(k, 0) + v
        model.eval(); vagg = {}; n = 0
        with torch.no_grad():
            for b in vdl:
                b = to(b, dev); out = model(b, teacher=True); _, parts = losses(out, b); n += 1
                for k, v in parts.items(): vagg[k] = vagg.get(k, 0) + v
        tr_s = " ".join(f"{k} {v/len(batches):.3f}" for k, v in agg.items()); va_s = " ".join(f"{k} {v/n:.3f}" for k, v in vagg.items())
        msg = f"epoch {ep} step {step} | train {tr_s} | val {va_s} | {time.time()-t0:.0f}s"; print(msg, flush=True); log.write(msg + "\n"); log.flush()
        vpost = vagg["post"] / n
        if vpost < best: best = vpost; torch.save(model.state_dict(), run / "best.pt")
        torch.save(model.state_dict(), run / "last.pt")
    print("best val post-mel L1", f"{best:.4f}")

def save_wav(p, x, sr=22050):
    with wave.open(str(p), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def batch_from_phones(row, vocab):
    """Model input from a phones.csv row (Iliad or Hesiod): no durations or mel, prediction only."""
    sys.path.insert(0, str(ROOT / "train")); from prepare_features import tokens_of
    toks, _ = tokens_of(row)
    return dict(id=row["id"], tok=torch.tensor([vocab[t[0]] for t in toks]), q=torch.tensor([t[1] for t in toks]).long(),
                acc=torch.tensor([t[2] for t in toks]).long(), foot=torch.tensor([t[3] for t in toks]).long(),
                dur=torch.zeros(len(toks)).long(), f0=torch.zeros(len(toks)), en=torch.zeros(len(toks)), mel=torch.zeros(1, N_MEL))

def synth(args):
    import torchaudio
    from vocos import Vocos
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    run = Path(args.ckpt).parent; cfg = json.load((run / "config.json").open()); vocab, stats = cfg["vocab"], cfg["stats"]
    model = FS2(len(vocab)).to(dev); model.load_state_dict(torch.load(args.ckpt, map_location=dev, weights_only=True)); model.eval()
    voc = Vocos.from_pretrained("charactr/vocos-mel-24khz")
    ids = args.ids.split(",") if args.ids else [l.strip() for l in open(args.list)]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True); rows = []
    if args.phones:
        ph = {r["id"]: r for r in csv.DictReader(open(args.phones))}
        items = [batch_from_phones(ph[i], vocab) for i in ids]
    else:
        ds = DS(ids, vocab, stats); items = [ds[i] for i in range(len(ids))]
    with torch.no_grad():
        for i in range(len(ids)):
            b = to(collate([items[i]]), dev); o = model(b, teacher=args.teacher, dur_scale=args.dur_scale, f0_shift=args.f0_shift)
            mel = o["mel_post"][0, :o["dur"][0].sum()].T.cpu()                    # (100, T)
            y = voc.decode(mel.unsqueeze(0))[0]; y22 = torchaudio.functional.resample(y, SR, 22050).numpy()
            save_wav(out / f"{ids[i]}.wav", y22)
            rows.append(dict(id=ids[i], n_frames=int(o["dur"][0].sum()), pred_dur=" ".join(map(str, o["dur"][0].tolist())),
                             pred_f0=" ".join(f"{v:.2f}" for v in (o["f0"][0] * stats["f0_std"] + stats["f0_mean"]).tolist())))
    with (out / "synth_index.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"synthesized {len(rows)} -> {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    t = sub.add_parser("train"); t.add_argument("--name", default="fs2"); t.add_argument("--hours", type=float, default=0); t.add_argument("--epochs", type=int, default=30)
    t.add_argument("--batch", type=int, default=16); t.add_argument("--lr", type=float, default=5e-4); t.add_argument("--cpu", action="store_true"); t.add_argument("--anomaly", action="store_true")
    s = sub.add_parser("synth"); s.add_argument("--ckpt", required=True); s.add_argument("--ids"); s.add_argument("--list"); s.add_argument("--out", required=True)
    s.add_argument("--phones", help="phones.csv to synthesize from (prediction only; default: feature files)"); s.add_argument("--teacher", action="store_true"); s.add_argument("--dur_scale", type=float, default=1.0); s.add_argument("--f0_shift", type=float, default=0.0)
    a = ap.parse_args(); train(a) if a.cmd == "train" else synth(a)
