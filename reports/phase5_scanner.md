# Phase 5: hexameter scanner and vowel-length lexicon

Date: 2026-09-23. Code: `prosody/scanner.py`, `prosody/lexicon.py`; validation
`scripts/validate_scanner.py`; tests `tests/test_scanner.py` (5 tests, pass).

## Method

1. **Nuclei.** Each vowel or diphthong is a nucleus (diaeresis blocks a diphthong;
   in α-υι sequences with a mark on the ι, the grouping is α | υι, as in γεγαυῖα).
2. **Position** is computed across the whole line: the consonants between a nucleus
   and the next vowel, including those of elided words (δ’) and the next word's
   onset; ζ ξ ψ count two.
3. **Nature.** η ω, diphthongs, iota subscript: long. ε ο: short. α ι υ: macron or
   breve if written, else the lexicon, else accent rules (circumflex → long;
   accent on the antepenult → short ultima; circumflex on the penult → short
   ultima; acute on the penult with a short ultima → short penult), else unknown.
4. **Options with costs.** Every nucleus gets {L, S} with a cost per choice: 0 for
   what nature and position dictate; 0.5 for correption of a word-final long
   vowel in hiatus (×3 before a digamma word); 1.5 for internal correption; 1.0 to
   overrule the lexicon and 1.5 to overrule an accent rule; 2.0 for metrical
   lengthening of ε ο (1.0 before a word beginning with λ μ ν ρ σ or a digamma
   stem); 1.0 for a stop+liquid cluster not making position, 2.0 for any
   word-initial cluster not making position; 1.5 for a fifth-foot spondee; 2.0
   for a synizesis. The line-final syllable is always long.
5. **Solver.** Depth-first search over the six feet (dactyl or spondee in 1–5, two
   syllables in 6) picking the cheapest assignment; synizesis alternatives (one
   merged pair from εω εα εο εου εοι εαι ηυ ια ιο υα) compete on total cost.

## Lexicon

`prosody/lexicon.csv`: 13,023 word forms, 17,348 resolved α/ι/υ slots, built from
Chamberlain's Iliad scansion through `data/iliad/phones.csv` (only syllables whose
vowel length was certain contribute; majority vote per slot). Keyed by the exact
accented word form, so it generalizes to Hesiod only for shared forms; unshared
forms fall back to accent rules and the meter.

## Lemma and ending extension

`prosody/lemma_lexicon.py` generalizes the word-form lexicon with the Perseus
treebanks (form, lemma, morphology tag) for the Iliad and all three Hesiod works:

- **Lemma prefix.** An unknown form inherits the length of each α ι υ nucleus that
  lies inside the longest common letter prefix with a known form of the same lemma
  (majority vote across known forms).
- **Ending.** For each (morphology tag, ending) pair, where the ending runs from
  the last (or second-to-last) nucleus to the end of the form, the length of that
  nucleus is voted from known forms and applied to unknown forms with the same
  tag and ending (at least two votes and a 3:1 majority).

Precision on held-out Iliad books (form lexicon and tables built without the
book, predictions judged against Chamberlain's meter-certain lengths): lemma
rule 95.9 % on 1,197 predictions, ending rule 96.2 % on 496. The extension holds
5,346 slots for 4,547 forms (`prosody/lexicon_lemma.csv`); exact forms take
priority when both exist. `scripts/build_lexicons.sh` encodes the build order
(render without lexicon → form lexicon → extension → final renders), because
lexicon-derived lengths must not feed back into the lexicon as evidence.

Effect on unknown-length α ι υ (default short) in the phone tables:

| Corpus | Without lexicon | Form lexicon | Form + extension |
|---|---|---|---|
| Iliad | 8.4 % + 1.4 % line-final | 6.9 % + 0.6 % | 5.5 % + 0.1 % |
| Hesiod | 8.2 % + 1.7 % | 7.1 % + 0.8 % | 5.6 % + 0.1 % |

Word-form coverage of Hesiod tokens rose from 29.5 % to 44.2 %.

## Validation against Chamberlain, 24-fold by book

The lexicon for each book is built from the other 23.

| Outcome | Lines | Share |
|---|---|---|
| identical quantities | 15,388 | 98.38 % |
| same syllable count, different quantities | 38 | 0.24 % |
| different syllable count | 190 | 1.21 % |
| no scansion found | 25 | 0.16 % |

Where the syllable counts agree, 99.75 % of lines are identical. Of the 38
mismatches, most are in book 16, where his 2016 span data contains metrically
impossible sequences (feet like S S S or L S L); those are errors on his page.
The syllable-count differences are mostly his synizesis choices (θεοί, ἐών, ἔα,
ἔασιν) where the line also scans without them, plus a few of mine he did not make.
The 25 unscanned lines are dominated by proper names (Ἱστίαιαν, Ἐνυαλίῳ,
Εἰρέτριαν) needing synizesis of pairs not in the list, and edition variants.

The plan's target was 97 %.

## Hesiod

All three works scanned with the full Iliad lexicon (`scripts/scan_hesiod.py` → `data/hesiod/scansion.csv`).

| Work | Lines | Scanned | Unscanned |
|---|---|---|---|
| Theogony | 1042 | 1037 (99.5 %) | 5 |
| Works and Days | 831 | 828 (99.6 %) | 3 |
| Shield | 479 | 473 (98.7 %) | 6 |

Flags over the 2352 lines: correption 607, synizesis 126 (two per line allowed), lexicon overruled 84, metrical lengthening 63, word-initial cluster not making position 60. Lines with two equally cheap scansions: 2. Before solving, 7–8 % of nuclei had an α ι υ of unknown length (Iliad: similar), which the meter then fixed; the lexicon covers the shared vocabulary only.

Update 2026-09-24: all 14 formerly unscanned lines now scan after adding synizesis pairs (εη, αε, εε, ηε, ιω, υω, αι, οω, εει, ιη) and allowing up to three synizeses per line; a last-resort mode (quantities by nature and position, flagged `unmetrical`) exists but no line needed it. Iliad agreement after the change: 98.41 %, 0 unscanned. The lines that had failed:

- Theogony 764: τοῦ δὲ σιδηρέη μὲν κραδίη, χάλκεον δέ οἱ ἦτορ
- Theogony 800: ἄλλος γ’ ἐξ ἄλλου δέχεται χαλεπώτερος ἄεθλος.
- Theogony 850: τρέε δ’ Ἀίδης, ἐνέροισι καταφθιμένοισιν ἀνάσσων,
- Theogony 902: Εὐνουμίην τε Δίκην τε καὶ Εἰρήνην τεθαλυῖαν,
- Theogony 983: βοῶν ἕνεκ’ εἰλιπόδων ἀμφιρρύτῳ εἰν Ἐρυθείῃ.
- Works and Days 607: βουσὶ καὶ ἡμιόνοισιν ἐπηετανόν. αὐτὰρ ἔπειτα
- Works and Days 640: Ἄσκρῃ, χεῖμα κακῇ, θέρει ἀργαλέῃ, οὐδέ ποτ’ ἐσθλῇ.
- Works and Days 656: ἄεθλ’ ἔθεσαν παῖδες μεγαλήτορος· ἔνθα μέ φημι
- Shield 3: Ἀλκμήνη, θυγάτηρ λαοσσόου Ἠλεκτρύωνος·
- Shield 16: πρὶν λεχέων ἐπιβῆναι ἐυσφύρου Ἠλεκτρυώνης,
- Shield 35: αὐτῇ μὲν γὰρ νυκτὶ τανυσφύρου Ἠλεκτρυώνης
- Shield 67: χαλκῷ δηιώσειν καὶ ἀπὸ κλυτὰ τεύχεα δύσειν.
- Shield 82: κτείνας Ἠλεκτρύωνα βοῶν ἕνεκ’ εὐρυμετώπων·
- Shield 86: ζῶε δ’ ἀγαλλόμενος σὺν ἐυσφύρῳ Ἠλεκτρυώνῃ,

They are synthesized and in both packages; their scansions are in `data/hesiod/scansion.csv` for a listener to check.

## Known limitations

- Digamma is handled only through a stem list that affects correption and
  lengthening costs; there is no explicit digamma token yet.
- The lexicon is word-form based; a lemma-level table (stem + ending) would extend
  coverage to Hesiod's unshared forms and is the natural next improvement.
- Ambiguity that the meter cannot resolve (both quantities cost 0) is reported in
  `alternatives`; it is rare after the lexicon (1 line in the Iliad) but will be
  more common in Hesiod.
