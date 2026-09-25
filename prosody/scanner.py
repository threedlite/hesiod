"""Dactylic hexameter scanner.

scan_line(text, lexicon=None) -> Scan with, per syllable: text, nucleus letters, quantity
(L/S), foot (1-6), how the quantity was decided, plus line-level flags and the number of
equally good alternative scansions.

Pipeline: letters -> nuclei (vowels, diphthongs) -> consonant counts between nuclei across the
whole line (position) -> nature of each nucleus (η ω diphthongs long; ε ο short; α ι υ from
macron/breve, the lexicon, or accent rules, else unknown) -> DP over the six feet, choosing the
cheapest consistent assignment. If nothing scans, retry with one synizesis (εω εα εο εου ηυ
merged), then with weak-position clusters allowed short, then with correption disallowed.
"""
import copy, re, sys, unicodedata
from dataclasses import dataclass, field
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from greek2ipa.rules import (letters_with_marks, VOWELS, DIPHTHONGS, ACUTE, GRAVE, CIRC, DIAER, IOTA_SUB,
                             MACRON, BREVE, ROUGH, SMOOTH, CLUSTER_LETTERS)

STOPS = set("πτκφθχβδγ"); LIQUIDS = set("λρμν")
SYNIZESIS_PAIRS = {("ε", "ω"), ("ε", "α"), ("ε", "ο"), ("ε", "ου"), ("ε", "οι"), ("ε", "αι"), ("η", "υ"), ("ε", "ῳ"), ("ι", "α"), ("ι", "ο"), ("υ", "α"),
                   ("ε", "η"), ("α", "ε"), ("ε", "ε"), ("η", "ε"), ("ι", "ω"), ("υ", "ω"), ("α", "ι"), ("ο", "ω"), ("ε", "ει"), ("ι", "η")}
COST = dict(correption=0.5, internal_correption=1.5, weak_position_short=1.0, initial_cluster_short=2.0,
            metrical_lengthening=2.0, lengthening_before_liquid=1.0, lexicon_override=1.0, accent_override=1.5,
            synizesis=2.0, spondee5=1.5)
LIQUID_INITIAL = set("λμνρσ")
# words whose initial digamma still makes position / blocks correption in Homer (lemma stems, lowercase, no accents)
DIGAMMA_STEMS = ("αναξ", "ανακτ", "ανασσ", "αστυ", "εαρ", "εθεν", "εθνος", "εικοσ", "ειπ", "εκαστ", "εκατ", "εκηβολ", "εκων", "ελπ", "εννυμ", "εο", "εοι", "επος", "επε", "εργ", "ερδ", "ερρ", "εσπερ", "ετος", "ηδυ", "ιδ", "ειδ", "ις", "ιφι", "ιλιο", "ιον", "ιοχειρ", "οικ", "οινο", "ος ", "οι", "ε ", "εθ", "ρηγνυ", "ρηξ", "ερυ")

@dataclass
class Nucleus:
    word: int; text: str; letters: list           # letters: [(base, marks)] of the vowel(s)
    nature: str                                    # "L", "S", "?"
    idx_in_word: int; n_in_word: int
    accent: str = "0"
    cons_after: int = 0; weak_after: bool = False; hiatus_after: bool = False; word_final: bool = False
    chars_after: list = field(default_factory=list); own_cons: int = 0
    allowed: set = field(default_factory=set); how: str = ""; q: str = ""; foot: int = 0; flags: list = field(default_factory=list)

@dataclass
class Scan:
    nuclei: list; ok: bool; pattern: str = ""; cost: float = 0.0; n_alternatives: int = 0; flags: list = field(default_factory=list)
    def quantities(self): return "".join(n.q for n in self.nuclei)

def norm_word(w):
    w = unicodedata.normalize("NFC", w).lower()
    return "".join(c for c in w if unicodedata.category(c)[0] in "LM" or c == "’")

def words_of(text):
    text = unicodedata.normalize("NFC", text).replace("ʼ", "’").replace("'", "’")
    return [w for w in re.split(r"\s+", text.strip()) if norm_word(w)]

def nuclei_of_word(letters, wi):
    """letters: [(base, marks)] for one word (apostrophe kept). Returns nuclei and trailing consonant count etc."""
    out, i = [], 0
    vpos = [k for k, (b, _) in enumerate(letters) if b in VOWELS]
    n_syll = 0
    # first pass: group diphthongs
    groups = []
    while i < len(letters):
        b, m = letters[i]
        if b in VOWELS:
            nxt_is_ui = (i + 2 < len(letters) and letters[i + 1][0] == "υ" and letters[i + 2][0] == "ι"
                         and DIAER not in letters[i + 2][1] and (letters[i + 2][1] & {ACUTE, GRAVE, CIRC, ROUGH, SMOOTH}))
            if (i + 1 < len(letters) and letters[i + 1][0] in VOWELS and (b, letters[i + 1][0]) in DIPHTHONGS
                    and DIAER not in letters[i + 1][1] and not (m & {ACUTE, GRAVE, CIRC, ROUGH, SMOOTH}) and not nxt_is_ui):
                groups.append((i, i + 2)); i += 2
            else:
                groups.append((i, i + 1)); i += 1
        else: i += 1
    for gi, (a, b) in enumerate(groups):
        lets = letters[a:b]; marks = set().union(*(m for _, m in lets))
        base = "".join(x for x, _ in lets)
        if len(lets) == 2 or IOTA_SUB in marks or base in "ηω": nature = "L"
        elif base in "εο": nature = "S"
        elif MACRON in marks: nature = "L"
        elif BREVE in marks: nature = "S"
        else: nature = "?"
        acc = "C" if CIRC in marks else "A" if ACUTE in marks else "G" if GRAVE in marks else "0"
        # consonants after this nucleus up to the next vowel (within word); flag if the word ends before a vowel
        j, cons, chars = b, 0, []
        while j < len(letters) and letters[j][0] not in VOWELS:
            if letters[j][0] != "’": cons += 2 if letters[j][0] in CLUSTER_LETTERS else 1; chars.append(letters[j][0])
            j += 1
        word_final = j >= len(letters)
        n = Nucleus(word=wi, text=base, letters=lets, nature=nature, idx_in_word=gi, n_in_word=len(groups), accent=acc,
                    cons_after=cons, word_final=word_final, chars_after=chars, own_cons=cons)
        out.append(n)
    return out

def accent_hints(nuclei):
    """Apply accent rules to unknown α ι υ nuclei of one word (in place)."""
    n = len(nuclei)
    if n == 0: return
    accented = [k for k, x in enumerate(nuclei) if x.accent in "AC"]
    for x in nuclei:
        if x.accent == "C" and x.nature == "?": x.nature = "L"; x.how = "circumflex"
    if not accented: return
    k = accented[-1]
    ult = nuclei[-1]
    ult_short_for_accent = ult.nature == "S" or (ult.text in ("αι", "οι") and ult.word_final)
    if k == n - 3 and ult.nature == "?":                       # antepenult accented -> ultima short
        ult.nature = "S"; ult.how = "antepenult_accent"
    if k == n - 2:
        pen = nuclei[k]
        if pen.accent == "C" and ult.nature == "?": ult.nature = "S"; ult.how = "properispomenon"
        if pen.accent == "A" and pen.nature == "?" and ult_short_for_accent: pen.nature = "S"; pen.how = "paroxytone_short_ultima"

def build_nuclei(text, lexicon=None):
    ws = words_of(text); all_n = []
    for wi, w in enumerate(ws):
        lets = letters_with_marks(w)
        nuc = nuclei_of_word(lets, wi)
        if not nuc: continue
        key = norm_word(w)
        if lexicon and key in lexicon:
            for x in nuc:
                if x.nature == "?" and lexicon[key].get(x.idx_in_word) in ("L", "S"):
                    x.nature = lexicon[key][x.idx_in_word]; x.how = "lexicon"
        accent_hints(nuc)
        all_n.extend(nuc)
    # position across word boundaries
    for k, x in enumerate(all_n):
        nxt = all_n[k + 1] if k + 1 < len(all_n) else None
        cons = x.cons_after; chars = list(x.chars_after)
        if x.word_final and nxt is not None:
            # add the consonants of any vowel-less words in between (elided δ’, τ’, ...) and the
            # next word's initial consonants
            for wj in range(x.word + 1, nxt.word + 1):
                lets = [b for b, _ in letters_with_marks(ws[wj]) if b != "’"]
                j = 0
                while j < len(lets) and lets[j] not in VOWELS:
                    cons += 2 if lets[j] in CLUSTER_LETTERS else 1; chars.append(lets[j]); j += 1
            x.hiatus_after = (cons == 0)
        x.cons_after = cons
        x.weak_after = (cons == 2 and len(chars) == 2 and chars[0] in STOPS and chars[1] in LIQUIDS)
    return all_n, ws

def bare(w):
    return "".join(c for c in unicodedata.normalize("NFD", w).lower() if c.isalpha())

def option_costs(nuclei, ws):
    """Set x.options = {q: cost} for every nucleus. how/flags record the basis."""
    for k, x in enumerate(nuclei):
        last = k == len(nuclei) - 1
        nxt_word = ws[nuclei[k + 1].word] if (not last and x.word_final) else None
        nxt_bare = bare(nxt_word) if nxt_word else ""
        digamma_next = bool(nxt_bare) and any(nxt_bare.startswith(st.strip()) for st in DIGAMMA_STEMS if st.strip())
        if last: x.options = {"L": 0.0}; x.how = x.how or "line_final"; continue
        if x.cons_after >= 2:
            x.how = x.how or ("position" if x.nature != "L" else "nature+position")
            opts = {"L": 0.0}
            if x.weak_after: opts["S"] = COST["weak_position_short"]
            elif x.word_final and x.own_cons == 0 and nxt_word:
                opts["S"] = COST["initial_cluster_short"]          # whole cluster is the next word's onset (Σκ-, Ζ-, ...)
            if x.nature == "L": opts.pop("S", None)
            x.options = opts; continue
        if x.nature == "L":
            x.how = x.how or "nature"
            if x.cons_after == 0 and not last:
                if x.word_final: x.options = {"L": 0.0, "S": COST["correption"] * (3 if digamma_next else 1)}
                else: x.options = {"L": 0.0, "S": COST["internal_correption"]}
            else: x.options = {"L": 0.0}
            if x.how in ("lexicon",): x.options["S"] = min(x.options.get("S", 9), COST["lexicon_override"])
            if x.how in ("circumflex", "antepenult_accent", "properispomenon", "paroxytone_short_ultima"):
                x.options["S"] = min(x.options.get("S", 9), COST["accent_override"])
        elif x.nature == "S":
            x.how = x.how or "nature"
            c = COST["metrical_lengthening"]
            if nxt_bare and (nxt_bare[0] in LIQUID_INITIAL or digamma_next): c = COST["lengthening_before_liquid"]
            if x.how == "lexicon": c = min(c, COST["lexicon_override"])
            if x.how in ("antepenult_accent", "properispomenon", "paroxytone_short_ultima"): c = min(c, COST["accent_override"])
            x.options = {"S": 0.0, "L": c}
        else:
            x.how = x.how or "unknown"; x.options = {"L": 0.0, "S": 0.0}

def solve(nuclei):
    """DP over feet with per-option costs. Returns (best_cost, pattern, n_best) or None."""
    n = len(nuclei)
    patterns5 = [("L", "S", "S"), ("L", "L")]
    results = []
    def rec(pos, foot, cost, assign):
        if cost > 12: return
        if foot == 6:
            if pos + 2 == n and "L" in nuclei[pos].options and "L" in nuclei[pos + 1].options:
                results.append((cost + nuclei[pos].options["L"], assign + "LL"))
            return
        for pat in patterns5:
            if pos + len(pat) > n: continue
            c = 0.0; ok = True
            for j, q in enumerate(pat):
                o = nuclei[pos + j].options
                if q not in o: ok = False; break
                c += o[q]
            if not ok: continue
            extra = COST["spondee5"] if (foot == 5 and pat == ("L", "L")) else 0.0
            rec(pos + len(pat), foot + 1, cost + c + extra, assign + "".join(pat))
    rec(0, 1, 0.0, "")
    if not results: return None
    results.sort(); bc = results[0][0]
    return bc, results[0][1], len({a for c, a in results if abs(c - bc) < 1e-9})

def try_synizesis(nuclei):
    """Yield nucleus lists with one adjacent in-word vowel pair merged."""
    for k in range(len(nuclei) - 1):
        a, b = nuclei[k], nuclei[k + 1]
        if a.word == b.word and a.cons_after == 0 and (a.text, b.text) in SYNIZESIS_PAIRS:
            merged = Nucleus(word=a.word, text=a.text + b.text, letters=a.letters + b.letters, nature="L",
                             idx_in_word=a.idx_in_word, n_in_word=a.n_in_word - 1, accent=b.accent if b.accent != "0" else a.accent,
                             cons_after=b.cons_after, weak_after=b.weak_after, hiatus_after=b.hiatus_after, word_final=b.word_final, own_cons=b.own_cons)
            merged.chars_after = list(b.chars_after); merged.flags = ["synizesis"]; merged.how = "synizesis"; merged.nature = "L"
            yield nuclei[:k] + [merged] + nuclei[k + 2:]

def scan_line(text, lexicon=None, fallback=True):
    base, ws = build_nuclei(text, lexicon)
    attempts = [(base, [], 0.0)] + [(alt, ["synizesis"], COST["synizesis"]) for alt in try_synizesis(base)]
    # two synizeses in one line (e.g. two -έων genitives): merge again inside each single-merge alternative
    seen = {tuple(x.text for x in a[0]) for a in attempts}
    level = list(attempts[1:])
    for depth in (2, 3):                                              # up to three synizeses in one line
        nxt = []
        for alt, _, _ in level:
            for alt2 in try_synizesis(alt):
                key = tuple(x.text for x in alt2)
                if key not in seen: seen.add(key); item = (alt2, ["synizesis"] * depth, depth * COST["synizesis"]); attempts.append(item); nxt.append(item)
        level = nxt
    best = None
    for src, flags, extra in attempts:
        nuclei = copy.deepcopy(src)
        for x in nuclei: x.how = "synizesis" if "synizesis" in x.flags else x.how
        option_costs(nuclei, ws)
        r = solve(nuclei)
        if r and (best is None or r[0] + extra < best[0]):
            best = (r[0] + extra, r[1], r[2], nuclei, flags)
    if best is None:
        if not fallback:
            for x in base: x.q = "?"
            return Scan(nuclei=base, ok=False, flags=["no_scan"])
        # last resort: quantities by nature and position only, no metrical constraint, flagged
        nuclei = copy.deepcopy(base); option_costs(nuclei, ws)
        for x in nuclei:
            x.q = "L" if (x.nature == "L" or x.cons_after >= 2 or x is nuclei[-1]) else "S"; x.foot = 0
        return Scan(nuclei=nuclei, ok=True, pattern="".join(x.q for x in nuclei), cost=99.0, n_alternatives=0, flags=["unmetrical"])
    cost, pat, nb, nuclei, flags = best
    foot, i = 1, 0
    for x, q in zip(nuclei, pat):
        x.q = q
        if x.options.get(q, 0) > 0:
            tag = {("S", "nature"): "correption", ("L", "nature"): "metrical_lengthening", ("S", "position"): "cluster_short",
                   ("S", "nature+position"): "cluster_short", ("S", "lexicon"): "lexicon_overridden", ("L", "lexicon"): "lexicon_overridden"}.get((q, x.how), "override")
            x.flags.append(tag)
    while i < len(pat):
        step = 3 if pat[i:i + 3] == "LSS" and foot < 6 else 2
        for j in range(i, min(i + step, len(pat))): nuclei[j].foot = foot
        i += step; foot += 1
    line_flags = sorted(set(flags + [f for x in nuclei for f in x.flags if f != "synizesis"]))
    if "synizesis" in flags: line_flags = ["synizesis"] + line_flags
    return Scan(nuclei=nuclei, ok=True, pattern=pat, cost=cost, n_alternatives=nb, flags=line_flags)

if __name__ == "__main__":
    for line in sys.argv[1:]:
        s = scan_line(line)
        print(s.ok, s.pattern, s.cost, s.n_alternatives, s.flags)
        print("  " + " ".join(f"{n.text}:{n.q}({n.how})" for n in s.nuclei))
