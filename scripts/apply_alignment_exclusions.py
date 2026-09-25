#!/usr/bin/env python3
"""Mark utterances that MFA could not align as excluded (status/reason) in metadata.csv and exclusions.csv,
preserving all other columns (text_clean, split, ...)."""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "data/iliad"
scores = {r["id"]: r for r in csv.DictReader((D / "alignment_scores.csv").open())}
rows = list(csv.DictReader((D / "metadata.csv").open()))
excl = list(csv.DictReader((D / "exclusions.csv").open()))
have = {(e["book"], e["idx"]) for e in excl}
n = 0
for r in rows:
    s = scores.get(r["id"])
    if r["status"] == "ok" and s and s["aligned"] == "False":
        r["status"], r["reason"], r["split"] = "excluded", "alignment_failed (MFA produced no alignment)", ""
        if (r["book"], r["idx"]) not in have:
            excl.append(dict(book=r["book"], idx=r["idx"], perseus_n=r["perseus_n"], reason="alignment_failed (MFA produced no alignment)")); n += 1
with (D / "metadata.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
excl.sort(key=lambda e: (int(e["book"]), int(e["idx"])))
with (D / "exclusions.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["book", "idx", "perseus_n", "reason"]); w.writeheader(); w.writerows(excl)
for name in ("train", "val", "test"):
    (D / "splits" / f"{name}.txt").write_text("\n".join(r["id"] for r in rows if r["split"] == name) + "\n")
ok = [r for r in rows if r["status"] == "ok"]
print(f"newly excluded {n}; ok {len(ok)}; excluded total {len(excl)}; splits:", {k: sum(1 for r in rows if r['split'] == k) for k in ('train', 'val', 'test')})
