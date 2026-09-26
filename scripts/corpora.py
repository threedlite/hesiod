"""Target corpora for Track H (text -> phones -> synthesis). Hesiod (tlg0020) was the first; the Homeric
Hymns (tlg0013) and, since 2026-09-25, the other hexameter poets in Perseus reuse the same scanner, lexicon,
model and package layout.

Each corpus: the Perseus TEI directory, the app's author string and per-work title strings (`authors.name`
and `works.title` in classicsviewer's perseus_texts_full.db, copied verbatim, Greek titles included), the
data directory under data/, whether the works are divided into books (TEI <div subtype="book|poem|epigram">;
the app's book_number), and the line-id scheme. Single-book corpora (hesiod, hymns) keep their original ids
(tlg001_1, h02_137a); book corpora use <prefix>_<book>_<n> (od_1_1, non_48_10)."""
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

def _c(tlg_group, author, works, prefix, books=True, titles=None, ident=None, data=None, skip_books=None):
    """works: {tlg: short name used in the tables}; titles: {short name: app title} (default: the short name itself);
    skip_books: {short name: {book, ...}} known not to be hexameter (the scanner's unmetrical rate misses Aeolic lines)."""
    return dict(src=PERSEUS / tlg_group, author=author, works=works, titles=titles or {v: v for v in works.values()},
                books=books, prefix=prefix, ident=ident or (lambda tlg, book, n: f"{prefix(tlg)}_{book}_{n}"), data=data, skip_books=skip_books or {})

CORPORA = {
    # the two original corpora: single-book works, ids without a book part, data/hesiod and data/hymns
    "hesiod": _c("tlg0020", "Hesiod", {"tlg001": "Theogony", "tlg002": "Works and Days", "tlg003": "Shield"}, lambda tlg: tlg, books=False,
                 titles={"Theogony": "Theogony", "Works and Days": "Works and Days", "Shield": "Shield of Heracles"}, ident=lambda tlg, book, n: f"{tlg}_{n}"),
    "hymns": _c("tlg0013", "Homeric Hymns", {f"tlg{n:03d}": f"Hymn {n}" for n in range(1, 34)}, lambda tlg: "h" + tlg[-2:], books=False,
                titles={f"Hymn {n}": t for n, t in HYMN_TITLES.items()}, ident=lambda tlg, book, n: f"h{tlg[-2:]}_{n}"),
    # the other hexameter poets in Perseus (others.txt), 2026-09-25. The Iliad is left out: the model was trained on
    # Chamberlain's recording of it, which the app already has. Elegiac works are left out (Theocritus and Callimachus
    # Epigrams, Callimachus Hymn 5 to Athena); non-hexameter books inside a work (Theocritus 28-30) are dropped by
    # render_hesiod_phones.py from the scanner's unmetrical rate.
    "homer": _c("tlg0012", "Homer", {"tlg002": "Odyssey", "tlg003": "Epigrams"}, lambda tlg: {"tlg002": "od", "tlg003": "hep"}[tlg]),
    "apollonius": _c("tlg0001", "Apollonius Rhodius", {"tlg001": "Argonautica"}, lambda tlg: "arg"),
    "theocritus": _c("tlg0005", "Theocritus", {"tlg001": "Idylls"}, lambda tlg: "th", titles={"Idylls": "Εἰδύλλια"},
                     skip_books={"Idylls": {"28", "29", "30"}}),                       # Aeolic metres; 29 scans as hexameter by accident
    "moschus": _c("tlg0035", "Moschus", {"tlg001": "Eros Drapeta", "tlg002": "Europa", "tlg003": "Epitaphius Bios", "tlg004": "Megara", "tlg005": "Fragmenta"},
                  lambda tlg: "mo" + tlg[-1]),
    "bion": _c("tlg0036", "Bion of Phlossa", {"tlg001": "Epitaphius Adonis", "tlg002": "Epithalamium Achillis et Deidameiae", "tlg003": "Fragmenta"}, lambda tlg: "bi" + tlg[-1]),
    "callimachus": _c("tlg0533", "Callimachus", {"tlg015": "Hymn to Zeus", "tlg016": "Hymn to Apollo", "tlg017": "Hymn to Artemis", "tlg018": "Hymn to Delos", "tlg020": "Hymn to Demeter"},
                      lambda tlg: "ca" + tlg[-2:]),
    "aratus": _c("tlg0653", "Aratus Solensis", {"tlg001": "Phaenomena"}, lambda tlg: "ar"),
    "quintus": _c("tlg2046", "Quintus Smyrnaeus", {"tlg001": "Fall of Troy"}, lambda tlg: "qs"),
    "oppian": _c("tlg0023", "Oppian", {"tlg001": "Halieutica"}, lambda tlg: "hal"),
    "oppian_apamea": _c("tlg0024", "Oppian of Apamea", {"tlg001": "Cynegetica"}, lambda tlg: "cyn"),
    "nonnus": _c("tlg2045", "Nonnus of Panopolis", {"tlg001": "Dionysiaca"}, lambda tlg: "non"),
    "tryphiodorus": _c("tlg0647", "Tryphiodorus", {"tlg001": "The Taking of Ilios"}, lambda tlg: "try"),
    "colluthus": _c("tlg4081", "Colluthus of Lycopolis", {"tlg001": "The Rape of Helen"}, lambda tlg: "col"),
}
ORDER = ["hesiod", "hymns", "colluthus", "tryphiodorus", "bion", "moschus", "callimachus", "aratus", "theocritus",
         "oppian_apamea", "oppian", "apollonius", "quintus", "homer", "nonnus"]          # small to large

def corpus(name):
    c = dict(CORPORA[name]); c["name"] = name; c["data"] = c["data"] or f"data/{name}"; return c

def add_corpus_arg(ap):
    ap.add_argument("--corpus", default="hesiod", choices=sorted(CORPORA), help="target corpus (default hesiod)"); return ap

if __name__ == "__main__":
    for n in ORDER: print(n, corpus(n)["author"], list(corpus(n)["works"].values()))
