#!/usr/bin/env python3
"""Phase 3: alignment QC from MFA's alignment_analysis.csv and the TextGrids.

Inputs : align/textgrids/alignment_analysis.csv (per utterance: overall/speech log-likelihood,
         phone_duration_deviation, snr, ...), align/textgrids/chamberlain/<id>.TextGrid, metadata.
Outputs: data/iliad/alignment_scores.csv (joined, with z-scores and a combined suspicion rank),
         reports/alignment_qc.md, and the bottom 1 % appended to notes/human_qa_queue.md.
"""
import csv, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from textgrid import read_textgrid

ROOT = Path(__file__).resolve().parents[1]
TGDIR = ROOT / "align/textgrids"
ANALYSIS = TGDIR / "alignment_analysis.csv"

def main():
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open())}
    rows = list(csv.DictReader(ANALYSIS.open()))
    for r in rows:
        r["id"] = Path(r["file"]).stem
        for k in ("overall_log_likelihood", "speech_log_likelihood", "phone_duration_deviation", "snr", "intensity_deviation", "max_running_short_interval"):
            try: r[k] = float(r[k])
            except (ValueError, TypeError): r[k] = float("nan")
        tgp = TGDIR / "chamberlain" / f"{r['id']}.TextGrid"
        r["aligned"] = tgp.exists()
        tg = read_textgrid(tgp) if r["aligned"] else {}
        ph = [(a, b, t) for a, b, t in tg.get("phones", []) if t and t not in ("sil", "sp", "spn")]
        r["n_phones"] = len(ph)
        r["min_phone_ms"] = 1000 * min((b - a) for a, b, _ in ph) if ph else float("nan")
        r["n_phones_at_floor"] = sum(1 for a, b, _ in ph if (b - a) <= 0.0301)     # MFA's 3-frame floor
        sil = [(a, b) for a, b, t in tg.get("phones", []) if t in ("sil", "sp", "")]
        r["max_internal_sil_ms"] = 1000 * max([(b - a) for a, b in sil[1:-1]] or [0])
    def z(key, sign=1):
        v = np.array([r[key] for r in rows]); m, s = np.nanmean(v), np.nanstd(v)
        for r, x in zip(rows, v): r[f"z_{key}"] = sign * (x - m) / s if s else 0.0
    z("speech_log_likelihood", 1); z("phone_duration_deviation", -1); z("n_phones_at_floor", -1)
    for r in rows:
        r["suspicion"] = -(r["z_speech_log_likelihood"] + r["z_phone_duration_deviation"] + r["z_n_phones_at_floor"]) / 3
        if not r["aligned"]: r["suspicion"] = 99.0
        m = meta.get(r["id"], {}); r["text"] = m.get("text_clean", ""); r["split"] = m.get("split", "")
    rows.sort(key=lambda r: -r["suspicion"])
    keys = ["id", "split", "aligned", "speech_log_likelihood", "overall_log_likelihood", "phone_duration_deviation", "snr", "n_phones", "n_phones_at_floor", "min_phone_ms", "max_internal_sil_ms", "suspicion", "text"]
    with (ROOT / "data/iliad/alignment_scores.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    rows_al = [r for r in rows if r["aligned"]]
    ll = np.array([r["speech_log_likelihood"] for r in rows_al]); dd = np.array([r["phone_duration_deviation"] for r in rows_al])
    fl = np.array([r["n_phones_at_floor"] for r in rows_al]); snr = np.array([r["snr"] for r in rows_al])
    n_bottom = max(1, len(rows) // 100)
    q = lambda v, p: float(np.nanpercentile(v, p))
    n_unal = sum(1 for r in rows if not r["aligned"])
    lines = ["# Alignment QC", "", f"Utterances: {len(rows)}; {n_unal} failed to align (no TextGrid): {', '.join(r['id'] for r in rows if not r['aligned'])}.", "Source: MFA `alignment_analysis.csv` plus TextGrid phone intervals.", "",
             "| Metric | p1 | p5 | median | p95 | p99 |", "|---|---|---|---|---|---|",
             f"| speech log-likelihood (per frame) | {q(ll,1):.2f} | {q(ll,5):.2f} | {q(ll,50):.2f} | {q(ll,95):.2f} | {q(ll,99):.2f} |",
             f"| phone duration deviation | {q(dd,1):.2f} | {q(dd,5):.2f} | {q(dd,50):.2f} | {q(dd,95):.2f} | {q(dd,99):.2f} |",
             f"| phones at the 30 ms floor per utterance | {q(fl,1):.0f} | {q(fl,5):.0f} | {q(fl,50):.0f} | {q(fl,95):.0f} | {q(fl,99):.0f} |",
             f"| SNR (dB) | {q(snr,1):.1f} | {q(snr,5):.1f} | {q(snr,50):.1f} | {q(snr,95):.1f} | {q(snr,99):.1f} |", "",
             f"Suspicion = mean of z-scores of (−speech log-likelihood, duration deviation, phones at floor). Bottom 1 % = {n_bottom} utterances, listed in `data/iliad/alignment_scores.csv` (sorted) and queued for review.", "",
             "## Most suspicious 25", "", "| id | speech LL | dur dev | floor phones | text |", "|---|---|---|---|---|"]
    for r in rows[:25]:
        lines.append(f"| {r['id']} | {r['speech_log_likelihood']:.2f} | {r['phone_duration_deviation']:.2f} | {r['n_phones_at_floor']} | {r['text']} |")
    (ROOT / "reports/alignment_qc.md").write_text("\n".join(lines) + "\n")
    qa = ROOT / "notes/human_qa_queue.md"; txt = qa.read_text()
    block = "\n## Alignment: bottom 1 % by suspicion (Phase 3)\n" + "\n".join(f"- {r['id']} (LL {r['speech_log_likelihood']:.2f}, dur dev {r['phone_duration_deviation']:.2f}): {r['text']}" for r in rows[:n_bottom]) + "\n"
    if "## Alignment: bottom 1 %" not in txt: qa.write_text(txt + block)
    print("\n".join(lines[:12]))

if __name__ == "__main__":
    main()
