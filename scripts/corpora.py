"""Target corpora for Track H (text -> phones -> synthesis). Hesiod (tlg0020) was the first;
the Homeric Hymns (tlg0013) reuse the same scanner, lexicon, model and package layout.

Each corpus: the Perseus TEI directory, the app's author string and per-work title strings
(`authors.name` / `works.title` in classicsviewer's perseus_texts_full.db; the app stores every
work here as book 1), the data directory under data/, and the line-id prefix per work."""
from pathlib import Path

PERSEUS = Path.home() / "git/classicsviewer/data-sources/canonical-greekLit/data"

HYMN_TITLES = {   # works.title in the app database (note the capital "To" in 17: it is the app's string)
    1: "Hymn 1 to Dionysus", 2: "Hymn 2 to Demeter", 3: "Hymn 3 to Apollo", 4: "Hymn 4 to Hermes", 5: "Hymn 5 to Aphrodite",
    6: "Hymn 6 to Aphrodite", 7: "Hymn 7 to Dionysus", 8: "Hymn 8 to Ares", 9: "Hymn 9 to Artemis", 10: "Hymn 10 to Aphrodite",
    11: "Hymn 11 to Athena", 12: "Hymn 12 to Hera", 13: "Hymn 13 to Demeter", 14: "Hymn 14 to the Mother of the Gods",
    15: "Hymn 15 to Heracles", 16: "Hymn 16 to Asclepius", 17: "Hymn 17 To the Dioscuri", 18: "Hymn 18 to Hermes", 19: "Hymn 19 to Pan",
    20: "Hymn 20 to Hephaestus", 21: "Hymn 21 to Apollo", 22: "Hymn 22 to Poseidon", 23: "Hymn 23 to Zeus", 24: "Hymn 24 to Hestia",
    25: "Hymn 25 to the Muses and Apollo", 26: "Hymn 26 to Dionysus", 27: "Hymn 27 to Artemis", 28: "Hymn 28 to Athena",
    29: "Hymn 29 to Hestia", 30: "Hymn 30 to Earth", 31: "Hymn 31 to Helios", 32: "Hymn 32 to Selene", 33: "Hymn 33 to the Dioscuri"}

CORPORA = {
    "hesiod": dict(
        src=PERSEUS / "tlg0020", author="Hesiod", data="data/hesiod",
        works={"tlg001": "Theogony", "tlg002": "Works and Days", "tlg003": "Shield"},       # short names used in the tables
        titles={"Theogony": "Theogony", "Works and Days": "Works and Days", "Shield": "Shield of Heracles"},   # app title strings
        prefix=lambda tlg: tlg),                                                            # ids tlg001_1 ...
    "hymns": dict(
        src=PERSEUS / "tlg0013", author="Homeric Hymns", data="data/hymns",
        works={f"tlg{n:03d}": f"Hymn {n}" for n in range(1, 34)},                          # short names: Hymn 1 ... Hymn 33
        titles={f"Hymn {n}": t for n, t in HYMN_TITLES.items()},
        prefix=lambda tlg: "h" + tlg[-2:]),                                                 # ids h01_1 ... h33_19
}

def corpus(name):
    c = dict(CORPORA[name]); c["name"] = name; return c

def add_corpus_arg(ap):
    ap.add_argument("--corpus", default="hesiod", choices=sorted(CORPORA), help="target corpus (default hesiod)"); return ap
