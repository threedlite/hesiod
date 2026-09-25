# Phase 2: Chamberlain syllables → phones

Date: 2026-09-23. Code: `greek2ipa/rules.py`, `greek2ipa/from_spans.py`. Tests:
`tests/test_from_spans.py` (23 tests, all pass; run with `python3 -m pytest tests`
or the inline runner used here since pytest is not installed on the system Python).
Output: `data/iliad/phones.csv`, one row per reading-page line (15,638 lines,
245,834 syllables).

## What the converter does

Input is one line as Chamberlain's syllable spans (text, long/short, foot, word,
hemistich). Words are grouped by his word index; letters are decomposed to NFD and
phonemized with Allen's rules; each phone stays attached to the syllable it came
from, so the syllable's quantity (his span), accent (its diacritics), foot and
hemistich ride along.

| Rule | Realization |
|---|---|
| φ θ χ / π τ κ / β δ γ | pʰ tʰ kʰ / p t k / b d g |
| γ before γ κ χ ξ | ŋ |
| ζ, ξ, ψ | z d, k s, p s |
| σ (ς) before β γ δ λ μ ν ρ, also across a word boundary | z |
| initial ῥ | r̥ ; rough breathing on a vowel → h |
| geminates | two tokens (l l) |
| ε ο η ω | e o ɛː ɔː |
| ει ου | eː uː (Allen's classical values; ου as uː is a decision to revisit with the speaker profile) |
| αι οι υι αυ ευ ηυ ωυ | ai oi yi au eu ɛːu ɔːu |
| ᾳ ῃ ῳ | aːi ɛːi ɔːi |
| diaeresis | blocks the diphthong |
| α ι υ | length inferred, see below |

**Length of α ι υ.** Short if his syllable is short. If the syllable is long,
count the consonant letters between the vowel and the next vowel, within the word
and, when the word ends there, into the next word (ζ ξ ψ count two). Zero or one
consonant means the syllable is long by nature, so the vowel is long. Two or more
means long by position, so the vowel's length is unknown: default short and flag
`position_ambiguous`. A word-final vowel at the line end is `line_final_ambiguous`.
His syllable boundaries are deliberately ignored here because they separate
prefixes ("ἄτ.ας"), which would make open syllables look closed.

Other flags: `correption` (a naturally long vowel or diphthong in a short
syllable before a vowel), `synizesis` (two vowels in one span, e.g. δεω).

## Results

| | Count | Share of syllables |
|---|---|---|
| position_ambiguous (α ι υ length unknown, default short) | 20,723 | 8.4 % |
| line_final_ambiguous | 3,377 | 1.4 % |
| correption | 4,653 | 1.9 % |
| synizesis | 362 | 0.1 % |

Phone inventory: 40 phones, all within the declared set. Most frequent e, n, a,
s, o, t; rarest ɔːu (once, ωὐτός by crasis), aːi (43), ɛːu (308).

The 9.8 % of syllables with unknown α ι υ length is the gap the Phase 5 lexicon
closes. For training in the meantime these default to short, which is the more
frequent value but wrong for roughly a third of them (long-by-position syllables
whose vowel is also long by nature, e.g. πάντας).

## Serialization

`phones` column: space-separated tokens, `.` between syllables, `#` between words;
vowel tokens carry the syllable accent as a suffix (ˊ acute, ˋ grave, ˆ
circumflex). Example, Iliad 1.1:

```
m ɛːˆ . n i n # aˊ . eː . d e # tʰ e . aːˋ # p ɛː . l ɛː . i . aˊ . d e ɔː # a . kʰ i . l ɛːˆ . o s
```

`quantity`, `accent`, `foot` columns give one character per syllable; `flags`
lists syllable index and flag; `detail` is the full JSON. The token-to-model
mapping (private-use codepoints for Piper, or auxiliary embeddings) is decided in
Phase 4.

## Open items for Phase 2

- Speaker profile: after Phase 3 measures his ζ, φθχ, υ, ει/ου, add a profile
  layer and re-render.
- Digamma positions (special token) come from the scansion in Phase 5.
- The dictionary for MFA (Phase 3) is generated from `phones.csv` by word: each
  unique word form with its phones, so sandhi variants (final ς → z) become
  separate entries.
