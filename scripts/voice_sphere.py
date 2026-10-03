#!/usr/bin/env python3
"""Voices on the sphere around Chamberlain's voice (PERSEUS_AUDIO.md §4.5).

scripts/convert_voice.py moves a voice in a six-dimensional parameter space whose origin is Chamberlain's own voice:
pitch shift, formant warp below 1 kHz (F1), formant warp above 1.5 kHz (F2, F3), spectral tilt, first-harmonic boost,
breathiness. Timing and pitch range are not in it: they carry the rhythm and the accent. Each axis is scaled so that one unit
is the step Phase 8 found usable (7 st; x 1.14 on a log axis, twice; 3 dB/oct; 2.5 dB; 0.08). The released female voice is
(1, 1, 1, 0, 0, 0); its distance from the origin, sqrt(3), is the radius, and every voice here lies on that sphere: as far
from Chamberlain as the female voice, in some other direction. Two axes are one-sided (the converter ignores a negative
H1 boost and clips breathiness at 0), so directions are reflected into the allowed half-space.

Ways to name a point:
  --theta T [T ...] [--toward plane|split|tilt|breath|h1|all]
        angle T from the female direction, rotating toward a direction orthogonal to it: `plane` lowers pitch while both
        formant bands rise (0 deg female, 180 deg the low male voice); `split` moves F1 against F2/F3; `tilt`, `breath`,
        `h1` leave the pitch-formant diagonal for those axes; `all` (default) is the equal mix of the five, so the
        distance is spread over every variable and no single one has to go far.
  --random N [--seed S]      N directions uniform on the sphere
  --vector v1..v6            an explicit direction (scaled to the radius)
--convert DIR [--ids a,b] converts those WAVs with each voice into data/synth/probe_non_hexameter/samples/sphere/<name>/.
--eval PHONES.csv, with --convert, then runs the Phase 8 checks (scripts/eval_voice.py) of each voice against the unconverted
WAVs, using DIR/synth_index.csv for the token timing; results in .../sphere/<name>/eval.json.
Usage (tts env): python scripts/voice_sphere.py --theta 60 120 --convert data/synth/probe_non_hexameter/samples/male --ids apology_38a
                 python scripts/voice_sphere.py --theta 0 60 120 180 240 300 --convert data/synth/probe_non_hexameter/wav_D2 \
                        --eval data/synth/probe_non_hexameter/D2.csv
"""
import argparse, math, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable
AXES = ["semitones", "log_alpha1", "log_alpha2", "tilt", "h1", "breath"]
UNIT = np.array([7.0, math.log(1.14), math.log(1.14), 3.0, 2.5, 0.08])
FEMALE = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0]); RADIUS = float(np.linalg.norm(FEMALE)); F = FEMALE / RADIUS
ONE_SIDED = [4, 5]                                                   # h1, breath: only >= 0 has an effect
TOWARD = {"plane": np.array([-2.0, 1.0, 1.0, 0, 0, 0]), "split": np.array([0, 1.0, -1.0, 0, 0, 0]),
          "tilt": np.array([0, 0, 0, 1.0, 0, 0]), "breath": np.array([0, 0, 0, 0, 0, 1.0]), "h1": np.array([0, 0, 0, 0, 1.0, 0])}
OUT = ROOT / "data/synth/probe_non_hexameter/samples/sphere"

def unit(v): return v / np.linalg.norm(v)

def toward(name):
    if name == "all": return unit(sum(unit(v) for v in TOWARD.values()))
    return unit(TOWARD[name])

def on_sphere(v):
    """Scale to the radius and reflect the one-sided axes into their half-space (the distance is unchanged)."""
    p = RADIUS * unit(v); p[ONE_SIDED] = np.abs(p[ONE_SIDED]); return p

def at_angle(theta_deg, e): t = math.radians(theta_deg); return on_sphere(math.cos(t) * F + math.sin(t) * e)

def settings(p):
    """convert_voice.py arguments for a point in unit space."""
    x = p * UNIT
    return dict(semitones=round(x[0], 2), alpha1=round(math.exp(x[1]), 4), alpha2=round(math.exp(x[2]), 4), tilt=round(x[3], 2), h1=round(max(0.0, x[4]), 2), breath=round(max(0.0, x[5]), 3))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--theta", type=float, nargs="*", default=[]); ap.add_argument("--toward", default="all", choices=list(TOWARD) + ["all"])
    ap.add_argument("--random", type=int, default=0); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--vector", type=float, nargs=6)
    ap.add_argument("--convert", help="directory of WAVs to convert"); ap.add_argument("--ids"); ap.add_argument("--eval", help="phones.csv: run eval_voice.py after converting"); a = ap.parse_args()
    voices = [(f"{a.toward}_{int(round(t)) % 360:03d}", at_angle(t, toward(a.toward))) for t in a.theta]
    rng = np.random.default_rng(a.seed); voices += [(f"random{a.seed}_{i}", on_sphere(rng.standard_normal(6))) for i in range(a.random)]
    if a.vector: voices.append(("vector", on_sphere(np.array(a.vector))))
    print(f"radius {RADIUS:.3f} units; 1 unit = 7 st | x1.14 F1 | x1.14 F2-F3 | 3 dB/oct | 2.5 dB H1 | 0.08 breath")
    print("| name | semitones | F1 warp | F2-F3 warp | tilt dB/oct | H1 dB | breath | distance |"); print("|---|---|---|---|---|---|---|---|")
    for name, p in voices:
        s = settings(p)
        print(f"| {name} | {s['semitones']:+.2f} | x {s['alpha1']:.3f} | x {s['alpha2']:.3f} | {s['tilt']:+.2f} | {s['h1']:.2f} | {s['breath']:.3f} | {np.linalg.norm(p):.3f} |")
        if a.convert:
            cmd = [PY, "scripts/convert_voice.py", "--in", a.convert, "--out", str(OUT / name), *sum(([f"--{k}", str(v)] for k, v in s.items()), []), "--jobs", "2"] + (["--ids", a.ids] if a.ids else [])
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True); print("   ", (r.stdout.strip().splitlines() or [r.stderr[-200:]])[-1])
            if a.eval:
                cmd = [PY, "scripts/eval_voice.py", "--orig", a.convert, "--conv", str(OUT / name), "--index", str(Path(a.convert) / "synth_index.csv"), "--phones", a.eval, "--json", str(OUT / name / "eval.json")] + (["--ids", a.ids] if a.ids else [])
                r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True); print("    " + "\n    ".join(l for l in r.stdout.strip().splitlines() if not l.startswith(" ")) if r.returncode == 0 else r.stderr[-300:])

if __name__ == "__main__":
    main()
