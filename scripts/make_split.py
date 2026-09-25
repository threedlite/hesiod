#!/usr/bin/env python3
"""Phase 1 step 6: assign every usable line to train / val / test.

  test  = Iliad 1.1-1.52 (the listening passage, never trained on)
  val   = 2 % of each book's remaining usable lines, deterministic (seed 20260923)
  train = the rest
Adds a `split` column to data/iliad/metadata.csv and writes data/iliad/splits/{train,val,test}.txt (one id per line).
"""
import csv, random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "data/iliad"
SEED, VAL_FRAC, TEST = 20260923, 0.02, ("1", range(1, 53))

rows = list(csv.DictReader((D / "metadata.csv").open()))
by_book = defaultdict(list)
for r in rows:
    r["split"] = ""
    if r["status"] != "ok": continue
    if r["book"] == TEST[0] and int(r["idx"]) in TEST[1]:
        r["split"] = "test"
    else:
        by_book[r["book"]].append(r)
rng = random.Random(SEED)
for b, lst in by_book.items():
    n = max(1, round(len(lst) * VAL_FRAC))
    chosen = set(r["id"] for r in rng.sample(lst, n))
    for r in lst: r["split"] = "val" if r["id"] in chosen else "train"

with (D / "metadata.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
(D / "splits").mkdir(exist_ok=True)
for name in ("train", "val", "test"):
    ids = [r["id"] for r in rows if r["split"] == name]
    (D / "splits" / f"{name}.txt").write_text("\n".join(ids) + "\n")
    hours = sum(float(r["trimmed_dur"]) for r in rows if r["split"] == name) / 3600
    print(f"{name:5s} {len(ids):6d} lines  {hours:6.2f} h")
