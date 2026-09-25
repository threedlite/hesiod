#!/usr/bin/env python3
"""Score audio against intended phone strings with the Phase 3b recognizer (the intelligibility instrument).

Usage:
  python train/recognize.py --split test                  # PER on the held-out Iliad test lines
  python train/recognize.py --manifest file.csv           # columns: id, wav, phones (phones as in phones.csv)
Writes per-utterance PER to stdout / --out CSV and prints the corpus PER.
"""
import argparse, csv, json, sys
from pathlib import Path
import torch
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phone_ctc import Model, Data, collate, greedy, edit_distance, phone_seq, ROOT

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--split"); ap.add_argument("--manifest"); ap.add_argument("--out")
    ap.add_argument("--ckpt", default=str(ROOT / "train/checkpoints/phone_ctc.pt")); args = ap.parse_args()
    vocab = json.load((ROOT / "train/phone_vocab.json").open()); inv = {i: p for p, i in vocab.items()}
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = Model(len(vocab) + 1).to(dev); model.load_state_dict(torch.load(args.ckpt, map_location=dev, weights_only=True)); model.eval()
    if args.manifest:
        rows = [dict(id=r["id"], clean_wav=r["wav"], phones=phone_seq(r["phones"])) for r in csv.DictReader(open(args.manifest))]
    else:
        meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open()) if r["split"] == args.split}
        ph = {r["id"]: phone_seq(r["phones"]) for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}
        rows = [dict(id=i, clean_wav=m["clean_wav"], phones=ph[i]) for i, m in meta.items() if i in ph]
    unk = {p for r in rows for p in r["phones"] if p not in vocab}
    if unk: print("phones outside the recognizer vocabulary:", unk, file=sys.stderr)
    rows = [dict(r, phones=[p for p in r["phones"] if p in vocab]) for r in rows]
    dl = torch.utils.data.DataLoader(Data(rows, vocab), batch_size=16, shuffle=False, collate_fn=collate)
    out, err, tot = [], 0, 0
    with torch.no_grad():
        for X, xl, Y, yl, ids in dl:
            logp, ol = model(X.to(dev), xl.to(dev)); hyps = greedy(logp.cpu(), ol.cpu(), inv); k = 0
            for h, n, id_ in zip(hyps, yl.tolist(), ids):
                ref = [inv[t] for t in Y[k:k + n].tolist()]; k += n
                e = edit_distance(h, ref); err += e; tot += n
                out.append(dict(id=id_, n_ref=n, errors=e, per=round(e / max(1, n), 4), hyp=" ".join(h)))
    if args.out:
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    else:
        for o in sorted(out, key=lambda o: -o["per"])[:10]: print(o["id"], o["per"], o["hyp"][:80])
    print(f"corpus PER {100*err/max(1,tot):.2f} % over {len(out)} utterances")

if __name__ == "__main__":
    main()
