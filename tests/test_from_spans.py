"""Hand-checked cases for greek2ipa.from_spans (Allen, Vox Graeca).

W("μῆ:L νιν:S") builds one word from syllable:quantity pairs. ph(...) returns the phone
tokens of the word (no accent suffixes); acc(...) the accent string per syllable.
"""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from greek2ipa.from_spans import Syll, phonemize_word, convert_line, serialize
from greek2ipa.rules import PHONE_SET

def W(spec):
    out = []
    for tok in spec.split():
        t, q = tok.rsplit(":", 1); out.append(Syll(text=t, q=q, foot=0, hemi=0))
    return out

def run(spec, nxt=None, final=False):
    s = W(spec); phonemize_word(s, nxt, final); return s

def ph(spec, nxt=None, final=False): return [p for s in run(spec, nxt, final) for p in s.phones]
def acc(spec): return "".join(s.accent for s in run(spec))
def flags(spec, nxt=None, final=False): return [f for s in run(spec, nxt, final) for f in s.flags]

NXT_CONS = [("δ", set())]          # next word begins with a single consonant
NXT_VOW = [("ἀ", set())]

# ---- consonants -------------------------------------------------------------
def test_aspirates_and_plain_stops():
    assert ph("φί:S λος:S") == ["pʰ", "i", "l", "o", "s"]
    assert ph("θε:S ός:S") == ["tʰ", "e", "o", "s"]
    assert ph("χα:S ρά:L", NXT_CONS) == ["kʰ", "a", "r", "aː"]
    assert ph("πα:S τήρ:L") == ["p", "a", "t", "ɛː", "r"]
    assert ph("κα:S κός:S") == ["k", "a", "k", "o", "s"]

def test_voiced_stops():
    assert ph("βί:S ος:S") == ["b", "i", "o", "s"]
    assert ph("δό:S μος:S") == ["d", "o", "m", "o", "s"]
    assert ph("γέ:S νος:S") == ["g", "e", "n", "o", "s"]

def test_gamma_nasal_before_velars():
    assert ph("ἄγ:L γε:S λος:S") == ["a", "ŋ", "g", "e", "l", "o", "s"]
    assert ph("ἀ:S νάγ:L κη:L") == ["a", "n", "a", "ŋ", "k", "ɛː"]
    assert ph("ἄγ:L χι:S") == ["a", "ŋ", "kʰ", "i"]
    assert ph("Σφίγξ:L") == ["s", "pʰ", "i", "ŋ", "k", "s"]

def test_zeta_xi_psi():
    assert ph("Ζεύς:L") == ["z", "d", "eu", "s"]
    assert ph("ξέ:S νος:S") == ["k", "s", "e", "n", "o", "s"]
    assert ph("ψυ:L χή:L") == ["p", "s", "yː", "kʰ", "ɛː"]

def test_sigma_voicing_before_voiced_consonants():
    assert ph("κόσ:L μος:S") == ["k", "o", "z", "m", "o", "s"]
    assert ph("πολ:L λὰς:L", [("δ", set())]) == ["p", "o", "l", "l", "a", "z"]   # final ς before δ of next word
    assert ph("ἔσ:L τι:S") == ["e", "s", "t", "i"]

def test_rho_and_rough_breathing():
    assert ph("ῥό:S δον:S") == ["r̥", "o", "d", "o", "n"]
    assert ph("ἥ:L ρως:L") == ["h", "ɛː", "r", "ɔː", "s"]
    assert ph("οἱ:L") == ["h", "oi"]                          # breathing on the diphthong's 2nd element
    assert ph("ὑ:S πό:S") == ["h", "y", "p", "o"]
    assert ph("ἀ:S νήρ:L") == ["a", "n", "ɛː", "r"]           # smooth breathing: nothing

def test_geminates_kept_as_two_tokens():
    assert ph("ἄλ:L λος:S") == ["a", "l", "l", "o", "s"]
    assert ph("ἀλλ’:L") == ["a", "l", "l"]

# ---- vowels -----------------------------------------------------------------
def test_fixed_vowels():
    assert ph("ἐ:S πί:S") == ["e", "p", "i"]
    assert ph("ὅ:S τε:S") == ["h", "o", "t", "e"]
    assert ph("μή:L") == ["m", "ɛː"]
    assert ph("ὦ:L") == ["ɔː"]

def test_diphthongs():
    assert ph("καί:L") == ["k", "ai"]
    assert ph("οἶ:L κος:S") == ["oi", "k", "o", "s"]
    assert ph("εἰ:L μί:S") == ["eː", "m", "i"]
    assert ph("οὐ:L") == ["uː"]
    assert ph("αὐ:L τός:S") == ["au", "t", "o", "s"]
    assert ph("εὖ:L") == ["eu"]
    assert ph("υἱ:L ός:S") == ["h", "yi", "o", "s"]
    assert ph("ηὗ:L ρον:S") == ["h", "ɛːu", "r", "o", "n"]

def test_diaeresis_blocks_diphthong():
    assert ph("Ἀ:S ΐ:S δης:L") == ["a", "i", "d", "ɛː", "s"]
    assert ph("πρα:S ΰς:L") == ["p", "r", "a", "y", "s"]

def test_iota_subscript_and_adscript():
    assert ph("τῇ:L") == ["t", "ɛːi"]
    assert ph("ᾧ:L") == ["h", "ɔːi"]
    assert ph("χώ:L ρᾳ:L") == ["kʰ", "ɔː", "r", "aːi"]

def test_variable_vowel_length_from_syllable():
    assert ph("θε:S ά:L", NXT_CONS) == ["tʰ", "e", "aː"]            # open long syllable -> long vowel
    assert ph("θε:S ά:S", NXT_VOW) == ["tʰ", "e", "a"]              # short syllable -> short vowel
    assert ph("ψυ:L χή:L") == ["p", "s", "yː", "kʰ", "ɛː"]
    assert ph("μυ:L ρί’:S") == ["m", "yː", "r", "i"]
    assert ph("Δι:S ός:S", [("τ", set())]) == ["d", "i", "o", "s"]
    assert ph("Δι:S ός:S", NXT_CONS) == ["d", "i", "o", "z"]           # final ς voiced before δ

def test_closed_syllable_is_ambiguous_and_flagged():
    assert ph("ἄλ:L γος:S") == ["a", "l", "g", "o", "s"]
    assert "position_ambiguous" in flags("ἄλ:L γος:S")
    assert flags("θε:S ά:L", NXT_CONS) == []

def test_his_prefix_style_split_does_not_hide_an_open_syllable():
    assert ph("ἄτ:L ας:L", NXT_CONS) == ["aː", "t", "a", "z"]         # 1st α: single τ follows -> long; 2nd: ς+δ -> position (and ς -> z)
    assert flags("ἄτ:L ας:L", NXT_CONS) == ["position_ambiguous"]
    assert ph("ἄτ:L α:L", NXT_CONS) == ["aː", "t", "aː"]
    assert "position_ambiguous" in flags("ἄνδρ:L εσσ:L ι:S")          # νδρ cluster
    assert ph("πάτ:S ερ:S") == ["p", "a", "t", "e", "r"]

def test_position_before_cluster_is_ambiguous():
    assert "position_ambiguous" in flags("ἔ:S τι:L", [("σ", set()), ("τ", set())])
    assert "position_ambiguous" in flags("δι:L", [("ζ", set())])
    assert flags("δι:L", NXT_CONS) == [] and ph("δι:L", NXT_CONS) == ["d", "iː"]

def test_line_final_is_ambiguous():
    assert "line_final_ambiguous" in flags("θε:S ά:L", None, final=True)

def test_correption_flag():
    assert "correption" in flags("καὶ:S", NXT_VOW)
    assert ph("καὶ:S", NXT_VOW) == ["k", "ai"]
    assert "correption" in flags("δή:S", NXT_VOW)

def test_synizesis():
    assert ph("δεω:L") == ["d", "e", "ɔː"] and "synizesis" in flags("δεω:L")

def test_macron_breve_override():
    assert ph("ᾱ:S") == ["aː"] and ph("ᾰ:L") == ["a"]

# ---- accent -----------------------------------------------------------------
def test_accent_types():
    assert acc("μῆ:L νιν:S") == "C0"
    assert acc("ἄ:S ει:L δε:S") == "A00"
    assert acc("θε:S ὰ:L") == "0G"
    assert acc("αὐ:L τοὺς:L") == "0G"
    assert acc("οἰ:L ω:L νοῖ:L σί:S") == "00CA"

def test_serialize_marks_accent_on_vowels():
    words = convert_line([{"s": "μῆ", "q": "L", "word": 1}, {"s": "νιν", "q": "S", "word": 1},
                          {"s": "ἄ", "q": "S", "word": 2}, {"s": "ει", "q": "L", "word": 2}, {"s": "δε", "q": "S", "word": 2}])
    assert serialize(words) == "m ɛːˆ . n i n # aˊ . eː . d e"

def test_elision_and_uppercase_and_final_sigma():
    s = run("δ’:S"); assert [p for x in s for p in x.phones] == ["d"]
    assert ph("Ὀ:S δυσ:L σεύς:L") == ["o", "d", "y", "s", "s", "eu", "s"]

# ---- properties over the whole corpus ---------------------------------------
def test_corpus_properties():
    src = Path(__file__).resolve().parents[1] / "data/iliad/hypotactic_lines.csv"
    if not src.exists(): return
    import unicodedata
    bad_empty, bad_phone, n = 0, 0, 0
    for r in csv.DictReader(src.open()):
        sy = json.loads(r["syllables"]); words = convert_line(sy)
        out = [s for w in words for s in w.sylls]
        assert len(out) == len(sy)                                  # syllable count preserved
        for s in out:
            n += 1
            has_letter = any(unicodedata.category(c)[0] == "L" and c not in "’" for c in s.text)
            if has_letter and not s.phones: bad_empty += 1
            bad_phone += sum(1 for p in s.phones if p not in PHONE_SET)
    assert bad_empty == 0, f"{bad_empty} lettered syllables produced no phones"
    assert bad_phone == 0, f"{bad_phone} phones outside PHONE_SET"
