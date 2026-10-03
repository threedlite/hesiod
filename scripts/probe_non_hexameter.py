#!/usr/bin/env python3
"""Probe for PERSEUS_AUDIO.md §3: how the released checkpoint behaves outside the hexameter, with no retraining.

Each condition is a phones.csv-shaped table synthesized with train/fs2.py (prediction mode) and scored with
train/recognize.py against its own phone string:
  A    Iliad validation lines, phones from Chamberlain's spans (must reproduce the reported 2.36 %)
  A2   the same lines through the scanner (real feet)
  B/B2 A2 with foot = 0 / with stand-in feet
  C/C2 the same lines with quantities by nature and position only (the scanner's fallback) and foot = 0 / stand-in feet
  D/D2 prose: Plato, Apology, the app's units of up to 60 syllables
  E/E2 the same prose cut into cola: hard stops (. · ;) always cut, short comma pieces merge to >= 10 syllables, stretches over 25 split
  F/F2 iambic trimeters: Sophocles, Oedipus Tyrannus 1-150
  G    Callimachus, Hymn to Athena: the hexameters, scanned; Gp/Gp2 its pentameters
  H2   every fallback (foot = 0) line of the released corpora, with stand-in feet
  D3/F3 prose units / trimeters with foot = 3 throughout ("mid-line" everywhere)
  D4/F4 the same with foot as a phrase-position control: 1 on the first three syllables, 5 and 6 on the last five, 3 between
Stand-in feet: syllables cut into runs of at most 17, each run numbered 1-6 in proportion; no metrical claim.
The summary's second table gives predicted long-vowel duration and pitch by foot number: how much line shape the foot input carries.
Prose and drama text comes from classicsviewer's perseus_texts_full.db (read-only).
Output: data/synth/probe_non_hexameter/ (tables, wavs, per-line PER, summary.md). Nothing else is written.
--samples: three Apology passages read as prose (cola with phrase-position feet, joined with pauses by punctuation mark),
in the unconverted voice (samples/male), the released female voice (samples/female, Phase 8 setting) and, for 38a only, a
lower male voice made with the female setting mirrored (samples/male_low: -7 st, formants / 1.14).
--dialogue [--socrates low|b|a|...] [--meletus female|...]: Apology 26c-26d, Socrates questioning Meletus, with the speaker turns marked by hand (the Apology is a speech: Perseus
marks this exchange with nothing, unlike the dialogues proper, whose speakers the app's database carries), Socrates in the low male
voice and Meletus in the female one.
Usage (tts env): python scripts/probe_non_hexameter.py [--only G,Gp,Gp2] [--summary-only] [--samples] [--dialogue] [--ckpt train/runs/fs2_full/best.pt]
"""
import argparse, copy, csv, math, re, sqlite3, subprocess, sys, wave
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "train"))
from greek2ipa.from_text import convert_text
from greek2ipa.from_spans import serialize
from prosody.scanner import build_nuclei, option_costs, Scan, scan_line, bare
from prosody import lexicon as L
from diff_transcripts import normalize
from corpora import ORDER, corpus
from prepare_features import tokens_of

OUT = ROOT / "data/synth/probe_non_hexameter"; PY = sys.executable
APP_DB = Path.home() / "git/classicsviewer/data-prep/perseus_texts_full.db"
FIELDS = ["id", "n_syll", "phones", "quantity", "accent", "foot", "text"]
MAX_UNIT = 60            # syllables: a 236-syllable unit overruns the decoder's 4,000-frame position table
LABELS = {"A": "Iliad validation, Chamberlain's spans", "A2": "Iliad validation, scanner, real feet", "B": "same, foot = 0", "B2": "same, stand-in feet",
          "C": "Iliad validation, quantities without the metre, foot = 0", "C2": "same, stand-in feet",
          "D": f"Plato, Apology, units up to {MAX_UNIT} syllables, foot = 0", "D2": "same, stand-in feet", "E": "Apology in cola, foot = 0", "E2": "same, stand-in feet",
          "F": "Sophocles, OT 1-150 (trimeters), foot = 0", "F2": "same, stand-in feet", "G": "Callimachus, Hymn 5: hexameters, scanned",
          "Gp": "Callimachus, Hymn 5: pentameters, foot = 0", "Gp2": "same, stand-in feet", "H2": "fallback lines of the released corpora, stand-in feet",
          "D3": "Apology units, foot = 3 throughout", "D4": "Apology units, foot as phrase position (1 … 3 … 5 6)",
          "F3": "OT trimeters, foot = 3 throughout", "F4": "OT trimeters, foot as phrase position"}
lex = None

def fallback_scan(text):
    """The last resort of prosody.scanner.scan_line: quantity by nature and position, no metre, foot 0."""
    nuclei, ws = build_nuclei(text, lex); nuclei = copy.deepcopy(nuclei); option_costs(nuclei, ws)
    if not nuclei: return None
    for x in nuclei: x.q = "L" if (x.nature == "L" or x.cons_after >= 2 or x is nuclei[-1]) else "S"; x.foot = 0
    return Scan(nuclei=nuclei, ok=True, pattern="".join(x.q for x in nuclei), cost=99.0, flags=["unmetrical"])

def render(id_, text, metrical):
    try:
        scan = scan_line(text, lex, fallback=False) if metrical else fallback_scan(text)
        if scan is None or not scan.ok: return None
        words, _ = convert_text(text, lex, scan=scan)
        if not words: return None
        sy = [s for w in words for s in w.sylls]
        return dict(id=id_, n_syll=len(sy), phones=serialize(words), quantity="".join(s.q for s in sy), accent="".join(s.accent for s in sy),
                    foot="".join(str(s.foot) for s in sy), text=text)
    except Exception as e:
        print("  not rendered:", id_, repr(e)[:80]); return None

def standin(n):
    runs = max(1, math.ceil(n / 17)); base, extra = divmod(n, runs); out = []
    for r in range(runs):
        m = base + (r < extra); out += [str(1 + (i * 6) // m) for i in range(m)]
    return "".join(out)

def phrase(n): return standin(n) if n < 9 else "111" + "3" * (n - 8) + "555" + "66"      # start, middle, close of one phrase

def with_feet(rows, zero=False, f=None):
    f = f or ((lambda n: "0" * n) if zero else standin); return [dict(r, foot=f(len(r["quantity"]))) for r in rows]

def clean(t):
    t = re.sub(r"\[[^\]]*\]", " ", t); t = re.sub(r"[\[\]†*\d()\"«»<>]", "", t)                 # section labels, editorial signs
    return normalize(re.sub(r"\s+", " ", t.replace("᾽", "’").replace("ʼ", "’")).strip())

def app_lines(db, author, title, limit):
    q = """select t.line_number, t.line_text from text_lines t join books b on b.id=t.book_id join works w on w.id=b.work_id
           where w.author_id=? and w.title=? order by b.book_number, t.sequence_number limit ?"""
    return [(n, t) for n, t in ((n, clean(t)) for n, t in db.execute(q, (author, title, limit))) if t]

HARD = ".·;"            # full stop, raised dot, question mark: always a colon boundary (a pause follows)
MIN_SYLL, MAX_SYLL = 10, 25

def n_syll(text): return len(build_nuclei(text, lex)[0])

CONJ = {"και", "αλλα", "η", "ως", "οτι", "ει", "επει", "επειδη", "οτε", "ινα", "οπως", "ωστε", "ουδε", "μηδε", "ουτε", "μητε"}
PREP = {"περι", "προς", "εν", "εκ", "εξ", "απο", "υπο", "εις", "κατα", "μετα", "παρα", "δια", "επι", "συν", "αντι", "υπερ"}
POSTPOSITIVE = {"δε", "δ", "γαρ", "μεν", "τε", "ουν", "αν", "γε", "τοι", "που"}
MIN_PART = 6

def split_long(text):
    """A stretch without punctuation above MAX_SYLL syllables is cut at a word boundary, preferring the conjunction, then
    the preposition, nearest the middle, never before a postpositive; each half is cut again if still too long."""
    nuclei, ws = build_nuclei(text, lex); n = len(nuclei)
    if n <= MAX_SYLL: return [text]
    cum = [0]
    for i in range(len(ws)): cum.append(cum[-1] + sum(1 for x in nuclei if x.word == i))
    b = [bare(w) for w in ws]                                       # letters only, no diacritics
    cands = [i for i in range(1, len(ws)) if MIN_PART <= cum[i] <= n - MIN_PART and b[i] not in POSTPOSITIVE] or [max(1, len(ws) // 2)]
    pool = [i for i in cands if b[i] in CONJ] or [i for i in cands if b[i] in PREP] or cands
    cut = min(pool, key=lambda i: abs(cum[i] - n / 2))
    return split_long(" ".join(ws[:cut])) + split_long(" ".join(ws[cut:]))

def cola(n, text):
    """Cut at punctuation: a hard mark (HARD) always closes a colon; after a comma or colon, short pieces are merged
    forward until MIN_SYLL syllables; anything longer than MAX_SYLL without punctuation is split at a word boundary."""
    out, cur = [], ""
    for p in [p.strip() for p in re.split(r"(?<=[,.·;:])\s+", text) if p.strip()]:
        cur = (cur + " " + p).strip()
        if p[-1] in HARD or n_syll(cur) >= MIN_SYLL: out += split_long(cur); cur = ""
    if cur: out += split_long(cur)
    return [(f"apol_{n}_{k}", c) for k, c in enumerate(out)]

def build():
    global lex
    lex = L.load_all(ROOT); T = {}
    val = [l.strip() for l in (ROOT / "data/iliad/splits/val.txt").open() if l.strip()]
    meta = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/metadata.csv").open())}
    ph = {r["id"]: r for r in csv.DictReader((ROOT / "data/iliad/phones.csv").open())}; val = [i for i in val if i in ph]
    T["A"] = [dict(id=i, n_syll=ph[i]["n_syll"], phones=ph[i]["phones"], quantity=ph[i]["quantity"], accent=ph[i]["accent"], foot=ph[i]["foot"], text=meta[i]["text_clean"]) for i in val]
    T["A2"] = [r for r in (render(i, meta[i]["text_clean"], True) for i in val) if r]
    T["B"], T["B2"] = with_feet(T["A2"], zero=True), with_feet(T["A2"])
    T["C"] = [r for r in (render(i, meta[i]["text_clean"], False) for i in val) if r]; T["C2"] = with_feet(T["C"])
    db = sqlite3.connect(f"file:{APP_DB}?mode=ro&immutable=1", uri=True)
    apol = app_lines(db, "tlg0059", "Apology", 300)
    units = [r for r in (render(f"apol_{n}", t, False) for n, t in apol) if r]
    print(f"  Apology: {len(units)} units, {sum(int(r['n_syll']) > MAX_UNIT for r in units)} above {MAX_UNIT} syllables left out of D")
    T["D"] = [r for r in units if int(r["n_syll"]) <= MAX_UNIT]; T["D2"] = with_feet(T["D"])
    T["D3"], T["D4"] = with_feet(T["D"], f=lambda n: "3" * n), with_feet(T["D"], f=phrase)
    T["E"] = [r for r in (render(i, c, False) for n, t in apol for i, c in cola(n, t)) if r]; T["E2"] = with_feet(T["E"])
    T["F"] = [r for r in (render(f"ot_{n}_{j}", t, False) for j, (n, t) in enumerate(app_lines(db, "tlg0011", "Oedipus Tyrannus", 150))) if r]; T["F2"] = with_feet(T["F"])
    T["F3"], T["F4"] = with_feet(T["F"], f=lambda n: "3" * n), with_feet(T["F"], f=phrase)
    h5 = app_lines(db, "tlg0533", "Hymn to Athena", 142)                                       # couplets: rows alternate hexameter, pentameter
    T["G"] = [r for r in (render(f"h5_{n}", t, True) for j, (n, t) in enumerate(h5) if j % 2 == 0) if r]
    T["Gp"] = [r for r in (render(f"h5_{n}", t, False) for j, (n, t) in enumerate(h5) if j % 2 == 1) if r]; T["Gp2"] = with_feet(T["Gp"])
    T["H2"] = []
    for name in ORDER:
        p = ROOT / corpus(name)["data"] / "phones.csv"
        if p.exists(): T["H2"] += with_feet([{k: r[k] for k in FIELDS} for r in csv.DictReader(p.open()) if r["phones"] and set(r["foot"]) <= {"0"}])
    for c, rows in T.items():
        with (OUT / f"{c}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
        (OUT / f"{c}.txt").write_text("\n".join(r["id"] for r in rows) + "\n")
    return list(T)

def run(c, ckpt):
    r = subprocess.run([PY, "train/fs2.py", "synth", "--ckpt", ckpt, "--list", str(OUT / f"{c}.txt"), "--phones", str(OUT / f"{c}.csv"), "--out", str(OUT / f"wav_{c}")],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode: print(r.stderr[-400:]); return
    with (OUT / f"manifest_{c}.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "wav", "phones"])
        for row in csv.DictReader((OUT / f"{c}.csv").open()): w.writerow([row["id"], str(OUT / f"wav_{c}" / f"{row['id']}.wav"), row["phones"]])
    r = subprocess.run([PY, "train/recognize.py", "--manifest", str(OUT / f"manifest_{c}.csv"), "--out", str(OUT / f"per_{c}.csv")], capture_output=True, text=True, cwd=ROOT)
    print(f"  {c}: {(r.stdout.strip().splitlines() or [r.stderr[-300:]])[-1]}")

def summarize(c):
    """Corpus PER, share of lines above 10 %, predicted vowel duration long : short, pace, acute minus unaccented pitch (semitones)."""
    if not (OUT / f"per_{c}.csv").exists(): return None
    rows = {r["id"]: r for r in csv.DictReader((OUT / f"{c}.csv").open())}; idx = {r["id"]: r for r in csv.DictReader((OUT / f"wav_{c}/synth_index.csv").open())}
    per = list(csv.DictReader((OUT / f"per_{c}.csv").open())); ms = 256 / 24000 * 1000
    dur = {1: [], 2: []}; f0 = {0: [], 1: []}; secs = syl = 0
    for i, r in rows.items():
        toks, n = tokens_of(r); d = [int(x) for x in idx[i]["pred_dur"].split()]; f = [float(x) for x in idx[i]["pred_f0"].split()]      # pred_f0 is log-F0
        secs += int(idx[i]["n_frames"]) * ms / 1000; syl += n
        vow = [k for k, t in enumerate(toks) if t[0][0] in "aeiouyɛɔ"]; med = np.median([f[k] for k in vow])
        for k in vow:
            if toks[k][1] in dur: dur[toks[k][1]].append(d[k] * ms)
            if toks[k][2] in f0: f0[toks[k][2]].append(12 / math.log(2) * (f[k] - med))
    return dict(c=c, n=len(per), per=100 * sum(int(r["errors"]) for r in per) / sum(int(r["n_ref"]) for r in per), over=100 * np.mean([float(r["per"]) > 0.10 for r in per]),
                ratio=np.mean(dur[1]) / np.mean(dur[2]), rate=syl / secs, acute=np.mean(f0[1]) - np.mean(f0[0]))

def foot_profile(c):
    """Predicted long-vowel duration (ms) and vowel pitch (st from the utterance median) by foot number 1-6."""
    if not (OUT / f"per_{c}.csv").exists(): return None
    rows = {r["id"]: r for r in csv.DictReader((OUT / f"{c}.csv").open())}; idx = {r["id"]: r for r in csv.DictReader((OUT / f"wav_{c}/synth_index.csv").open())}
    ms = 256 / 24000 * 1000; d = {k: [] for k in range(1, 7)}; p = {k: [] for k in range(1, 7)}
    for i, r in rows.items():
        toks, _ = tokens_of(r); dur = [int(x) for x in idx[i]["pred_dur"].split()]; f = [float(x) for x in idx[i]["pred_f0"].split()]
        vow = [k for k, t in enumerate(toks) if t[0][0] in "aeiouyɛɔ"]; med = np.median([f[k] for k in vow])
        for k in vow:
            if toks[k][3] in d:
                p[toks[k][3]].append(12 / math.log(2) * (f[k] - med))
                if toks[k][1] == 1: d[toks[k][3]].append(dur[k] * ms)
    return (f"| {c} | " + " | ".join(f"{np.mean(d[k]):.0f}" if d[k] else "" for k in range(1, 7)) + " | "
            + " | ".join(f"{np.mean(p[k]):+.2f}" if p[k] else "" for k in range(1, 7)) + " |")

PAUSE = {"": 0.15, ",": 0.25, ":": 0.40, "·": 0.40, ";": 0.55, ".": 0.60}        # seconds after a colon; "" = a cut inside a long stretch
SAMPLES = {
    "apology_17a": "ὅτι μὲν ὑμεῖς, ὦ ἄνδρες Ἀθηναῖοι, πεπόνθατε ὑπὸ τῶν ἐμῶν κατηγόρων, οὐκ οἶδα· ἐγὼ δ’ οὖν καὶ αὐτὸς ὑπ’ αὐτῶν ὀλίγου ἐμαυτοῦ ἐπελαθόμην, οὕτω πιθανῶς ἔλεγον.",
    "apology_38a": "ἐάντ’ αὖ λέγω ὅτι καὶ τυγχάνει μέγιστον ἀγαθὸν ὂν ἀνθρώπῳ τοῦτο, ἑκάστης ἡμέρας περὶ ἀρετῆς τοὺς λόγους ποιεῖσθαι καὶ τῶν ἄλλων περὶ ὧν ὑμεῖς ἐμοῦ ἀκούετε διαλεγομένου καὶ ἐμαυτὸν καὶ ἄλλους ἐξετάζοντος, ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ, ταῦτα δ’ ἔτι ἧττον πείσεσθέ μοι λέγοντι.",
    "apology_38a_short": "ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ.",
}
FEMALE = ["--semitones", "7", "--alpha1", "1.14", "--alpha2", "1.14", "--tilt", "0", "--h1", "0", "--breath", "0"]       # Phase 8 setting
LOW_MALE = ["--semitones", "-7", "--alpha1", "0.8772", "--alpha2", "0.8772", "--tilt", "0", "--h1", "0", "--breath", "0"]  # the same, mirrored (1/1.14)

DIALOGUE = [   # Apology 26c-26d; the app's units 174-177 with the turns separated by hand
    ("Socrates", "οὐ ταῦτα λέγεις ὅτι διδάσκων διαφθείρω;"),
    ("Meletus", "πάνυ μὲν οὖν σφόδρα ταῦτα λέγω."),
    ("Socrates", "πρὸς αὐτῶν τοίνυν, ὦ Μέλητε, τούτων τῶν θεῶν ὧν νῦν ὁ λόγος ἐστίν, εἰπὲ ἔτι σαφέστερον καὶ ἐμοὶ καὶ τοῖς ἀνδράσιν τουτοισί. "
                 "ἐγὼ γὰρ οὐ δύναμαι μαθεῖν πότερον λέγεις διδάσκειν με νομίζειν εἶναί τινας θεούς, καὶ αὐτὸς ἄρα νομίζω εἶναι θεοὺς καὶ οὐκ εἰμὶ τὸ παράπαν ἄθεος οὐδὲ ταύτῃ ἀδικῶ, "
                 "οὐ μέντοι οὕσπερ γε ἡ πόλις ἀλλὰ ἑτέρους, καὶ τοῦτ’ ἔστιν ὅ μοι ἐγκαλεῖς, ὅτι ἑτέρους, ἢ παντάπασί με φῂς οὔτε αὐτὸν νομίζειν θεοὺς τούς τε ἄλλους ταῦτα διδάσκειν."),
    ("Meletus", "ταῦτα λέγω, ὡς τὸ παράπαν οὐ νομίζεις θεούς."),
    ("Socrates", "ὦ θαυμάσιε Μέλητε, ἵνα τί ταῦτα λέγεις; οὐδὲ ἥλιον οὐδὲ σελήνην ἄρα νομίζω θεοὺς εἶναι, ὥσπερ οἱ ἄλλοι ἄνθρωποι;"),
    ("Meletus", "μὰ Δί’, ὦ ἄνδρες δικασταί, ἐπεὶ τὸν μὲν ἥλιον λίθον φησὶν εἶναι, τὴν δὲ σελήνην γῆν."),
    ("Socrates", "Ἀναξαγόρου οἴει κατηγορεῖν, ὦ φίλε Μέλητε; καὶ οὕτω καταφρονεῖς τῶνδε καὶ οἴει αὐτοὺς ἀπείρους γραμμάτων εἶναι "
                 "ὥστε οὐκ εἰδέναι ὅτι τὰ Ἀναξαγόρου βιβλία τοῦ Κλαζομενίου γέμει τούτων τῶν λόγων;"),
]
VOICE_SETTINGS = {   # the sphere voices of PERSEUS_AUDIO.md §4.5 (scripts/voice_sphere.py --theta ...)
    "female": FEMALE, "low": LOW_MALE,
    "a": ["--semitones", "-0.33", "--alpha1", "1.178", "--alpha2", "1.04", "--tilt", "2.01", "--h1", "1.68", "--breath", "0.054"],
    "b": ["--semitones", "-7.33", "--alpha1", "1.033", "--alpha2", "0.912", "--tilt", "2.01", "--h1", "1.68", "--breath", "0.054"],
    "v240": ["--semitones", "0.33", "--alpha1", "0.849", "--alpha2", "0.962", "--tilt", "-2.01", "--h1", "1.68", "--breath", "0.054"],
    "v300": ["--semitones", "7.33", "--alpha1", "0.968", "--alpha2", "1.096", "--tilt", "-2.01", "--h1", "1.68", "--breath", "0.054"]}
TURN_PAUSE = 0.5

def read_wav(p):
    with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)

def write_wav(p, x):
    with wave.open(str(p), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(x.tobytes())

def dialogue(ckpt, socrates="low", meletus="female"):
    """One passage, two voices: each turn is read as prose (cola, phrase-position feet, pauses by mark), converted with its speaker's
    setting, and the turns are joined with a longer pause. -> samples/dialogue/apology_26c[_<socrates>_<meletus>].wav"""
    global lex
    voices = {"Socrates": (socrates, VOICE_SETTINGS[socrates]), "Meletus": (meletus, VOICE_SETTINGS[meletus])}
    lex = lex or L.load_all(ROOT); S = OUT / "samples/dialogue"; (S / "turns").mkdir(parents=True, exist_ok=True)
    rows, plan = [], []
    for ti, (who, text) in enumerate(DIALOGUE):
        parts = []
        for k, (_, piece) in enumerate(cola(0, text)):
            r = render(f"turn{ti}_{k}", piece, False); r["foot"] = phrase(len(r["quantity"])); rows.append(r)
            parts.append((r["id"], piece[-1] if piece[-1] in PAUSE else ""))
        plan.append((who, parts))
    with (S / "cola.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    (S / "cola.txt").write_text("\n".join(r["id"] for r in rows) + "\n")
    subprocess.run([PY, "train/fs2.py", "synth", "--ckpt", ckpt, "--list", str(S / "cola.txt"), "--phones", str(S / "cola.csv"), "--out", str(S / "cola_wav")], cwd=ROOT, check=True, capture_output=True)
    for ti, (who, parts) in enumerate(plan):
        out = []
        for i, (id_, mark) in enumerate(parts):
            out.append(read_wav(S / "cola_wav" / f"{id_}.wav"))
            if i < len(parts) - 1: out.append(np.zeros(int(22050 * PAUSE[mark]), dtype=np.int16))
        write_wav(S / "turns" / f"turn{ti}.wav", np.concatenate(out))
    for name, setting in voices.values():
        ids = ",".join(f"turn{ti}" for ti, (who, _) in enumerate(plan) if voices[who][0] == name)
        subprocess.run([PY, "scripts/convert_voice.py", "--in", str(S / "turns"), "--out", str(S / f"turns_{name}"), "--ids", ids, *setting, "--jobs", "2"], cwd=ROOT, check=True, capture_output=True)
    out = []
    for ti, (who, _) in enumerate(plan):
        out.append(read_wav(S / f"turns_{voices[who][0]}" / f"turn{ti}.wav"))
        if ti < len(plan) - 1: out.append(np.zeros(int(22050 * TURN_PAUSE), dtype=np.int16))
    dst = S / ("apology_26c.wav" if (socrates, meletus) == ("low", "female") else f"apology_26c_{socrates}_{meletus}.wav")
    write_wav(dst, np.concatenate(out))
    for ti, (who, parts) in enumerate(plan): print(f"  {who} ({voices[who][0]}): {len(parts)} cola")
    print(f"  -> {dst}")

def samples(ckpt):
    """Prose as proposed in PERSEUS_AUDIO.md §4.5: cola, phrase-position feet, one file per passage, pauses by mark; then the female voice."""
    global lex
    lex = lex or L.load_all(ROOT); S = OUT / "samples"; (S / "male").mkdir(parents=True, exist_ok=True)
    rows, plan = [], {}
    for name, text in SAMPLES.items():
        plan[name] = []
        for k, (_, piece) in enumerate(cola(0, text)):
            r = render(f"{name}_{k}", piece, False); r["foot"] = phrase(len(r["quantity"])); rows.append(r)
            plan[name].append((r["id"], piece[-1] if piece[-1] in PAUSE else ""))
    with (S / "cola.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    (S / "cola.txt").write_text("\n".join(r["id"] for r in rows) + "\n")
    subprocess.run([PY, "train/fs2.py", "synth", "--ckpt", ckpt, "--list", str(S / "cola.txt"), "--phones", str(S / "cola.csv"), "--out", str(S / "cola_wav")], cwd=ROOT, check=True, capture_output=True)
    for name, parts in plan.items():
        out = []
        for i, (id_, mark) in enumerate(parts):
            with wave.open(str(S / "cola_wav" / f"{id_}.wav")) as w: out.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16))
            if i < len(parts) - 1: out.append(np.zeros(int(22050 * PAUSE[mark]), dtype=np.int16))
        with wave.open(str(S / "male" / f"{name}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(np.concatenate(out).tobytes())
        print(f"  {name}: {len(parts)} cola | " + " | ".join(piece for _, piece in cola(0, SAMPLES[name])))
    subprocess.run([PY, "scripts/convert_voice.py", "--in", str(S / "male"), "--out", str(S / "female"), *FEMALE, "--jobs", "3"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run([PY, "scripts/convert_voice.py", "--in", str(S / "male"), "--out", str(S / "male_low"), "--ids", "apology_38a", *LOW_MALE, "--jobs", "1"], cwd=ROOT, check=True, capture_output=True)
    print(f"  -> {S}/male, {S}/female, {S}/male_low (apology_38a only)")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ckpt", default="train/runs/fs2_full/best.pt"); ap.add_argument("--only", help="comma-separated conditions (default all)")
    ap.add_argument("--summary-only", action="store_true"); ap.add_argument("--samples", action="store_true"); ap.add_argument("--dialogue", action="store_true"); ap.add_argument("--socrates", default="low", choices=sorted(VOICE_SETTINGS)); ap.add_argument("--meletus", default="female", choices=sorted(VOICE_SETTINGS)); args = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    if args.samples: samples(args.ckpt); return
    if args.dialogue: dialogue(args.ckpt, args.socrates, args.meletus); return
    if not args.summary_only:
        conds = build(); conds = [c for c in conds if not args.only or c in args.only.split(",")]
        for c in conds: run(c, args.ckpt)
    S = [s for s in (summarize(c) for c in LABELS) if s]
    lines = ["| | Condition | Utterances | PER | Lines > 10 % | Vowel L : S | Syllables / s | Acute − none |", "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {s['c']} | {LABELS[s['c']]} | {s['n']} | {s['per']:.2f} % | {s['over']:.1f} % | {s['ratio']:.2f} | {s['rate']:.2f} | {s['acute']:+.2f} st |" for s in S]
    lines += ["", "| | Long vowel ms, foot 1 | 2 | 3 | 4 | 5 | 6 | Pitch st, foot 1 | 2 | 3 | 4 | 5 | 6 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [x for x in (foot_profile(c) for c in ("A2", "D2", "D3", "D4", "F2", "F3", "F4")) if x]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))

if __name__ == "__main__":
    main()
