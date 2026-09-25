import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prosody.scanner import scan_line

def q(text, lex=None): s = scan_line(text, lex); assert s.ok, text; return s.quantities()

def test_iliad_opening():
    assert q("μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος") == "LSSLSSLLLSSLSSLL"
    assert q("οὐλομένην, ἣ μυρί’ Ἀχαιοῖς ἄλγε’ ἔθηκε,") == "LSSLLLSSLLLSSLL"
    assert q("πολλὰς δ’ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν") == "LLLLLLLSSLSSLL"
    assert q("ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν") == "LLLLLSSLSSLSSLL"
    assert q("οἰωνοῖσί τε πᾶσι, Διὸς δ’ ἐτελείετο βουλή,") == "LLLSSLSSLSSLSSLL"

def test_synizesis_flagged():
    s = scan_line("μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"); assert "synizesis" in s.flags

def test_position_across_word_boundary():
    s = scan_line("πολλὰς δ’ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν")
    assert s.nuclei[0].how == "position"          # πολ- before λλ
    assert s.nuclei[2].how == "position"          # -ὰς δ’ ἰφ- : ς + δ across the boundary

def test_accent_rules():
    from prosody.scanner import build_nuclei
    n, _ = build_nuclei("θάλασσα")                  # antepenult accent -> ultima short
    assert n[-1].nature == "S" and n[-1].how == "antepenult_accent"
    n, _ = build_nuclei("δῶρα")                     # circumflex -> long
    assert n[0].nature == "L"
    n, _ = build_nuclei("λόγος")                    # acute on penult with short ultima: nothing to say about ο (already S)
    n, _ = build_nuclei("πολίτης")                  # acute on penult, ultima long: no inference
    assert n[1].nature == "?"
    n, _ = build_nuclei("μάλα")                     # acute penult + unknown ultima: no inference
    assert n[0].nature == "?"

def test_hesiod_opening():
    # Theogony 1: Μουσάων Ἑλικωνιάδων ἀρχώμεθ’ ἀείδειν
    assert q("Μουσάων Ἑλικωνιάδων ἀρχώμεθ’ ἀείδειν") == "LLLSSLSSLLLSSLL"

def test_homeric_hymn_openings():
    # Hymn 2 (Demeter) 1 and Hymn 3 (Apollo) 1: the Hymns scan with the same scanner and lexicon as Hesiod
    assert q("Δήμητρ’ ἠύκομον, σεμνὴν θεόν, ἄρχομ’ ἀείδειν,") == "LLLSSLLLSSLSSLL"
    # -ος of Ἀπόλλωνος makes position before ἑκάτοιο (digamma stem ϝεκ-): metrical lengthening, not correption
    assert q("μνήσομαι οὐδὲ λάθωμαι Ἀπόλλωνος ἑκάτοιο,") == "LSSLSSLSSLLLSSLL"
