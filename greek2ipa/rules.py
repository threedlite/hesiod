"""Letter-to-phone tables (Allen, Vox Graeca) and Unicode helpers."""
import unicodedata

# combining marks (NFD)
SMOOTH, ROUGH = "̓", "̔"
ACUTE, GRAVE, CIRC = "́", "̀", "͂"
DIAER, IOTA_SUB, MACRON, BREVE = "̈", "ͅ", "̄", "̆"
MARKS = {SMOOTH, ROUGH, ACUTE, GRAVE, CIRC, DIAER, IOTA_SUB, MACRON, BREVE}

VOWELS = set("αεηιουω")
# vowels whose length is fixed by the letter
FIXED = {"ε": ("e", False), "ο": ("o", False), "η": ("ɛ", True), "ω": ("ɔ", True)}
# vowels whose length must be inferred
VARIABLE = {"α": "a", "ι": "i", "υ": "y"}

# diphthongs: (first, second) -> (phones, long)
DIPHTHONGS = {
    ("α", "ι"): ("ai", True), ("ο", "ι"): ("oi", True), ("ε", "ι"): ("eː", True),
    ("υ", "ι"): ("yi", True), ("α", "υ"): ("au", True), ("ε", "υ"): ("eu", True),
    ("ο", "υ"): ("uː", True), ("η", "υ"): ("ɛːu", True), ("ω", "υ"): ("ɔːu", True),
}
# iota subscript / adscript long diphthongs
IOTA_SUB_DIPH = {"α": "aːi", "η": "ɛːi", "ω": "ɔːi"}

CONSONANTS = {
    "π": ["p"], "τ": ["t"], "κ": ["k"],
    "φ": ["pʰ"], "θ": ["tʰ"], "χ": ["kʰ"],
    "β": ["b"], "δ": ["d"], "γ": ["g"],
    "ζ": ["z", "d"], "ξ": ["k", "s"], "ψ": ["p", "s"],
    "λ": ["l"], "μ": ["m"], "ν": ["n"], "ρ": ["r"], "σ": ["s"], "ς": ["s"],
    "ϝ": ["w"],
}
VOICED_C = set("βγδλμνρ")          # σ -> z before these
VELARS = set("γκχξ")               # γ -> ŋ before these
CLUSTER_LETTERS = set("ζξψ")       # single letters that count as two consonants

PHONE_SET = {"p", "t", "k", "pʰ", "tʰ", "kʰ", "b", "d", "g", "ŋ", "z", "s", "l", "m", "n", "r", "r̥", "h", "w",
             "a", "aː", "e", "eː", "ɛː", "i", "iː", "o", "uː", "ɔː", "y", "yː",
             "ai", "oi", "yi", "au", "eu", "ɛːu", "ɔːu", "aːi", "ɛːi", "ɔːi"}

def nfd(t): return unicodedata.normalize("NFD", t)

def letters_with_marks(text):
    """NFD text -> list of (base_letter_lower, set_of_marks). Punctuation dropped; ’ kept as ('’', set())."""
    out = []
    for c in nfd(text):
        if c in MARKS:
            if out: out[-1][1].add(c)
        elif c == "’" or c == "'" or c == "ʼ":
            out.append(("’", set()))
        elif unicodedata.category(c)[0] == "L":
            out.append((c.lower(), set()))
        # everything else (punctuation, spaces) is dropped
    return out
