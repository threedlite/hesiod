# Audio for all the Greek in Perseus: an exploration

Written 2026-10-01, revised through 2026-10-03 (colon rule, voices, the sphere
and its checks). Companion to `PROJECT.md` and `PROJECT_PLAN.md`. This is not a
plan with phases and gates yet; it sets out what "all the Greek works in Perseus"
amounts to, what in the present pipeline carries over and what does not, and the
order of work I would recommend. Numbers marked *measured* were computed for this
document from the repository, the app database and a small synthesis probe (§3,
method in Appendix B); everything else is an estimate and says so.

---

## 1. Conclusions first

**The question underneath all of this: can a voice learned from Chamberlain's
hexameters be used for text that is not hexameter?** Yes, by measurement, with
one fix and one thing unmeasured. The existing model reads Plato, Sophocles'
trimeters and Callimachus' pentameters at 4.5–5.7 % phone error rate (Iliad
2.3 %, the shipped corpora 2.6–5.2 %), keeps its long : short vowel ratio and
its pitch accent, and by its own predicted durations and pitch carries over
little of the hexameter's line shape (§3).
The fix: never give it foot 0, which is what the fallback does today. The
unmeasured thing: how it sounds, since every figure here comes from a recognizer
that was itself trained only on his Iliad. His licence (CC BY 4.0) permits it.

1. **The hexameter work covers a tenth of the lines and a twentieth of the text.**
   Perseus holds 91 Greek authors, 772 works, 631,721 addressable units and 61.5
   million characters. What is left is about 109 hours of verse in other metres
   and roughly 1,500–1,900 hours of prose. Prose is 89 % of the text.
2. **The acoustic model is less of an obstacle than the project documents imply,
   and for a reason nobody had measured.** Fed prose, tragic trimeters or
   pentameters through the current fallback path, the model garbles them
   (29–33 % phone error rate). The cause is not the unfamiliar text: it is the
   foot number 0, which the model only ever saw on pauses. With stand-in foot
   numbers 1–6 the same model reads the same prose at 4.6 % PER with its
   long : short vowel ratio and its accent contrast intact, no retraining.
   Side effect: the 208 "unmetrical" lines already in the released packages are
   garbled for the same reason and can be repaired now (30.9 % → 4.4 %).
3. **The real problems, in order of difficulty:**
   - vowel length of α ι υ where no metre decides it (15–22 % of prose syllables
     are undecided with today's lexicon, against 9 % in the Odyssey before the
     metre is applied);
   - whether prose read with a verse reciter's cadence is acceptable, which no
     metric here can answer, and, beyond that, a delivery that follows the
     grammar (phrasing, sentence arc, questions, parentheses, emphasis),
     for which the dependency parses are on disk and the prosodic rules are
     still to write (§4.8);
   - what the text contains that should not be read aloud, and how the app
     addresses audio (2,785 line numbers are shared by more than one row);
   - scale: the whole corpus is about 2,100 hours of audio in 631,000 files,
     about 95 GB at the present encoding (32 GB at a speech bitrate), about
     seven days of continuous processing on the M4, and a QC queue no one can
     listen to (§5).
4. **Recommended order:** repair the fallback lines; finish the stichic verse
   (elegiac, trimeter, tetrameter, anapaests), which is cheap and which feeds
   Attic vocabulary into the length lexicon; retrain once with inputs that do not
   pretend everything is a hexameter; run a prose pilot of a few hours with a
   listening gate; then prose by author in order of readership; lyric last.
   Decide the delivery model (packs or on-device synthesis) before the bulk run,
   not after.
5. **One pronunciation, declared as such; as many voices as wanted.** The
   phone inventory is Chamberlain's realization of Allen's classical Attic. It
   cannot produce a Koine or Byzantine pronunciation, so Plutarch, the New
   Testament and Zonaras would be read as fifth-century Attic. That is the
   classroom convention and I recommend it, but it is a decision to take
   knowingly (§4.6). Voices are another matter: the conversion that makes the
   released female voice is one point in a six-variable space around his voice,
   and any number of further voices can be placed at the same distance from him
   (§4.5), for speakers in drama and dialogue or simply for choice.
6. **No new audio, and one gap that matters.** Audio from the internet may be
   used only if clearly licensed CC BY-SA or CC BY, and I found no recording of
   Greek prose in restored pronunciation that is. The whole proposal therefore
   rests on the one voice already in hand; §8 lists every source and its
   licence. The verse work has a reference recording to measure against
   (Chamberlain's Iliad); the prose work has none, so its prosody is designed
   rather than measured until a few hours of openly licensed prose in restored
   pronunciation are found or made (§4.8).

---

## 2. What "all the Greek works in Perseus" is

Source: the app's `perseus_texts_full.db` (built 2026-09-27), which holds every
Greek edition in the local `canonical-greekLit` checkout (commit `c40e7a033`,
2026-04-14). The checkout has 772 work directories with a Greek edition file and
the database has 772 Greek works; the nine author directories missing from the
database (the Old Testament entry, the Apostolic Fathers, pseudo-Lucian,
pseudo-Justin) have no Greek file. So the database is the whole of Perseus
Greek. All figures *measured*; hours are characters ÷ 8.18, the
characters-per-second rate of the 94.8 hours already synthesized.

| Group | Works | Units | Share of units | Characters | Share of text | Hours |
|---|---|---|---|---|---|---|
| Hexameter, done (15 corpora) | 60 | 65,149 | 10.3 % | 2.80 M | 4.5 % | 94.8 (actual) |
| Iliad (Chamberlain's own recording) | 1 | 15,687 | 2.5 % | 0.67 M | 1.1 % | 23 (actual) |
| Drama: Aeschylus, Sophocles, Euripides, Aristophanes | 45 | 61,967 | 9.8 % | 2.07 M | 3.4 % | ~70 |
| Greek Anthology | 1 | 21,065 | 3.3 % | 0.86 M | 1.4 % | ~29 |
| Lyric: Pindar, Bacchylides | 6 | 4,739 | 0.8 % | 0.17 M | 0.3 % | ~6 |
| Lycophron, Alexandra (trimeters) | 1 | 1,474 | 0.2 % | 0.05 M | 0.1 % | ~2 |
| Elegiac, left out so far: Callimachus Epigrams and Hymn 5, Theocritus Epigrams (plus the 97 Aeolic lines of Idylls 28–30, counted in the first row) | 4 | 1,005 | 0.2 % | 0.04 M | 0.1 % | ~1.5 |
| **Prose (68 authors)** | 591 | 460,635 | 72.9 % | 54.8 M | 89.2 % | ~1,860 at verse pace |
| **Total** | 772 | 631,721 | | 61.5 M | | |

Three things in this table shape everything below.

**Prose is the project.** The remaining verse is 90,250 lines and about 109
hours, slightly more than what has been done. Prose is seventeen times that.
Ten authors are half of it: Plutarch alone is 6.5 M characters (about 220 hours),
then Plato (118 h), Josephus, Diodorus, Dionysius of Halicarnassus, Polybius,
Athenaeus, Xenophon, Aristotle and Demosthenes. The authors most people read are
small by comparison: Herodotus about 40 hours, Thucydides 33, the New Testament
28, Lysias 12. Appendix A lists every author.

**A prose "line" is a sentence, and it is long.** The app stores prose as
sentence-like units numbered sequentially within a book. On 3,000-unit samples
(*measured*):

| Text | Syllables per unit, median | 90th percentile | Longest |
|---|---|---|---|
| Odyssey (for reference) | 16 | 17 | 18 |
| New Testament | 35 | 55 | 97 |
| Plato, Apology | 34 | 85 | 278 |
| Herodotus | 37 | 73 | 217 |
| Thucydides | 44 | 98 | 281 |
| Plutarch | 49 | 109 | 291 |

The model was trained on utterances of 12–17 syllables. A Thucydidean period is
fifteen times that.

**Drama is three metres' worth of work, not one.** By the TEI's own section
labels (`<div subtype="episode|strophe|antistrophe|anapests|trochees|…">`,
bucketed roughly, *measured*): about 54 % of dramatic lines sit in spoken
sections (iambic trimeter, with some tetrameters in Aristophanes), 7 % in
anapaests, 2 % in trochaics and 37 % in lyric. Aeschylus is 45 % lyric,
Sophocles 24 %, Euripides 35 %. The useful fact is that the markup exists: the
metre of a passage can be read from the edition instead of guessed.

Out of scope here: First1KGreek and the app's extended database (392 Greek
authors, 2.3 M units, 212 M characters, 3.5 times the full database). Nothing
below is specific to Perseus, so the same machinery would apply, but the prose
problems would need to be solved on Perseus first.

---

## 3. What the present pipeline assumes, and a probe of the model outside it

The pipeline that produced the fifteen corpora rests on four properties of
hexameter verse:

1. **The metre decides quantity.** `prosody/scanner.py` searches six feet and
   so fixes every syllable's weight and, in open syllables, the length of α ι υ.
   The lexicon (17,348 slots from Chamberlain's Iliad, 5,346 more from lemma and
   ending rules) is a prior for that search, not a substitute for it.
2. **Every syllable carries a foot number 1–6.** The model's input is
   phone + quantity + accent + foot (`train/fs2.py`). Foot 0 appears in training
   only on the start, end and word-boundary tokens.
3. **One utterance is one line.** The longest training utterance is a
   seventeen-syllable hexameter, and the decoder's position table stops at
   4,000 frames (42.7 s).
4. **Punctuation is discarded** (`letters_with_marks` drops it). Pauses come
   from the word-boundary token's predicted duration and nothing tells the model
   whether a line ends a sentence or runs on.

When the scanner cannot scan a line it falls back to quantities by nature and
position and sets foot to 0. That fallback is the only path a prose sentence or
a trimeter could take today. 208 such lines were synthesized for the released
corpora. Their recognizer scores, from the existing `per.csv` files
(*measured*): 30.9 % mean PER against 3.4 % for the 64,843 metrical lines, with
95 % of them above the 10 % threshold. The phase reports put this down to corrupt or dialectal text. The
probe says otherwise.

### The probe

Same checkpoint (`fs2_full`), same recognizer, prediction mode, unconverted
voice. Nothing was retrained and no existing file in the repository was
modified. "Stand-in feet" means cutting the syllables into runs of at most
seventeen and numbering each run's syllables 1–6 in proportion, with no
metrical claim at all.

| | Condition | Utterances | PER | Lines > 10 % | Vowel L : S | Syllables / s | Acute − none |
|---|---|---|---|---|---|---|---|
| A | Iliad validation, Chamberlain's spans | 311 | 2.36 % | 2.6 % | 2.08 | 3.02 | +2.29 st |
| A2 | Iliad validation, scanner, real feet | 311 | 2.30 % | 1.9 % | 2.07 | 3.03 | +2.29 st |
| B | same, foot = 0 | 311 | 29.07 % | 99.0 % | 2.08 | 4.78 | +0.82 st |
| B2 | same, stand-in feet | 311 | 2.33 % | 2.3 % | 2.06 | 3.08 | +2.27 st |
| C | Iliad validation, quantities without the metre, foot = 0 | 311 | 28.93 % | 98.7 % | 2.12 | 4.76 | +0.84 st |
| C2 | same, stand-in feet | 311 | 2.29 % | 1.9 % | 2.10 | 3.08 | +2.29 st |
| D | Plato, Apology, units up to 60 syllables, foot = 0 | 227 | 33.43 % | 98.7 % | 2.35 | 4.94 | +0.50 st |
| D2 | same, stand-in feet | 227 | 4.59 % | 6.2 % | 2.24 | 3.23 | +1.91 st |
| E | Apology in cola, foot = 0 | 890 | 32.35 % | 98.9 % | 2.39 | 4.69 | +0.54 st |
| E2 | same, stand-in feet | 890 | 4.52 % | 9.4 % | 2.26 | 3.11 | +1.87 st |
| F | Sophocles, OT 1–150 (trimeters), foot = 0 | 150 | 32.10 % | 99.3 % | 2.25 | 4.41 | +0.83 st |
| F2 | same, stand-in feet | 150 | 5.74 % | 20.7 % | 2.19 | 2.84 | +2.17 st |
| G | Callimachus, Hymn 5: hexameters, scanned | 64 | 5.12 % | 10.9 % | 2.11 | 3.08 | +2.03 st |
| Gp | Callimachus, Hymn 5: pentameters, foot = 0 | 71 | 32.08 % | 100.0 % | 2.34 | 4.98 | +1.06 st |
| Gp2 | same, stand-in feet | 71 | 4.50 % | 15.5 % | 2.25 | 3.11 | +2.41 st |
| H2 | fallback lines of the released corpora, stand-in feet | 208 | 4.41 % (was 30.85 %) | 8.7 % | 2.03 | 3.18 | +2.37 st |
| D3 | Apology units, foot = 3 throughout | 227 | 5.30 % | 9.7 % | 2.27 | 2.76 | +2.04 st |
| D4 | Apology units, foot as phrase position (1 … 3 … 5 6) | 227 | 5.25 % | 8.4 % | 2.27 | 2.85 | +2.01 st |
| F3 | OT trimeters, foot = 3 throughout | 150 | 6.41 % | 22.0 % | 2.17 | 2.56 | +2.19 st |
| F4 | OT trimeters, foot as phrase position | 150 | 5.84 % | 20.7 % | 2.17 | 2.81 | +2.08 st |

The letters are the condition names in `scripts/probe_non_hexameter.py`, which
prints this table.

What it shows:

- **Foot 0 is the whole failure.** Zeroing the foot on perfectly scanned Iliad
  lines takes them from 2.3 % to 29 %. The line shrinks from 5.2 s to 3.3 s, the
  recognizer hears 8,531 phones where 10,499 were intended, and the acute's
  pitch step falls from +2.3 to +0.8 semitones. The model has learned that foot 0 means
  "boundary" and swallows the syllables. Any foot value from training restores it.
- **The model does not need a real scansion to articulate.** Quantities taken
  without the metre plus invented feet score the same as the real scansion on
  the Iliad (2.29 % against 2.30 %).
- **Prose is within reach of the existing checkpoint.** 4.6 % PER is where the
  shipped Doric bucolics sit (Theocritus 5.15 %, Bion 4.87 %). The long : short
  vowel ratio (2.24) and the acute's pitch step (+1.9 st) survive. Pace stays at
  the reciter's three syllables a second.
- **Length did not hurt up to 60 syllables.** PER by unit length in the Apology
  sample: 10–17 syllables 4.3 %, 18–30 4.6 %, 31–45 4.6 %, 46–60 4.6 %. Cutting
  into cola (E2, median colon 14 syllables) changed nothing by this measure:
  4.52 % against 4.59 % for whole units.
- **There is a hard ceiling.** A 236-syllable unit crashed the synthesizer at
  the 4,000-frame position table. About a quarter of the Apology's units exceed
  60 syllables, so prose has to be synthesized in pieces and joined whatever
  else is decided.
- **Short lines look worse than they are.** The trimeter's 20.7 % flagged share
  is partly arithmetic: a twelve-syllable line crosses 10 % on three phone
  errors. The per-line threshold should scale with length.

### How much hexameter shape comes along

The worry with a hexameter-trained voice is that it will chant: start low, hold,
and drop at the end of every "line", whatever the text. The foot input is where
that shape would live, so it can be measured. Predicted long-vowel duration and
vowel pitch (semitones from the utterance median) by foot number:

| | Long vowel ms, foot 1 | 2 | 3 | 4 | 5 | 6 | Pitch st, foot 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A2 | 204 | 191 | 228 | 185 | 196 | 220 | -0.64 | +0.74 | +0.32 | +0.46 | +0.27 | -1.42 |
| D2 | 201 | 206 | 218 | 199 | 201 | 208 | -0.32 | +0.37 | +0.38 | +0.20 | +0.41 | -0.45 |
| D3 |  |  | 218 |  |  |  |  |  | +0.13 |  |  |  |
| D4 | 211 | 215 | 218 | 168 | 200 | 211 | -0.92 | +0.57 | +0.32 | +1.07 | +0.24 | -0.91 |
| F2 | 195 | 186 | 215 | 160 | 182 | 221 | -0.57 | +0.42 | -0.33 | +0.16 | +1.01 | -0.04 |
| F3 |  |  | 204 |  |  |  |  |  | +0.09 |  |  |  |
| F4 | 191 |  | 205 |  | 176 | 221 | -0.34 |  | -0.03 |  | +0.65 | -0.26 |

- In real hexameters (A2) the shape is plain: the line starts 0.6 st low, ends
  1.4 st low, and lengthens at the caesura (foot 3) and the close (foot 6).
- In prose with stand-in runs (D2) most of it is gone: the "line end" every
  seventeen syllables is a dip of under 1 st with almost no lengthening. In the
  trimeters (F2), where foot 6 is a true line end, there is no dip at all. So
  the Iliad's final fall is not something the number 6 forces onto other text.
  (Pitch by position is confounded with where the accents happen to fall, which
  differs between metres; read these as sizes, not as contours.)
- Foot 3 throughout (D3, F3) gives the flattest contour and still articulates
  (5.3 % and 6.4 %), but slows to 2.8 syllables a second, because foot 3 carries
  the caesura's lengthening everywhere.
- Using the foot as a phrase-position control (D4, F4: 1 at the start, 3 in the
  middle, 5 and 6 on the last five syllables of a real phrase) costs nothing in
  PER against D3 and puts the fall where the sense ends.

(The few D4 values under feet 2 and 4 come from units under nine syllables,
which keep stand-in feet.)

So the foot number is a mild prosodic control, not a metrical commitment, and
it can be set to serve the text. Which setting sounds best is for a listener;
by the numbers, stand-in runs articulate best and phrase-position feet are the
most defensible.

What it does not show, and this matters as much:

- **PER cannot see a wrong quantity.** Each condition is scored against its own
  intended phone string. If the text side says a long α is short, the model says
  it short and the recognizer agrees. Text-side correctness needs its own
  measure (§4.3).
- **PER cannot hear cadence.** The per-foot figures above say the imposed shape
  is small, but they are the model's own predictions of duration and pitch, not
  a judgement of the result. Whether Plato in this voice sounds like dignified
  reading or like chanting is a question for a listener.

---

## 4. The problems, one at a time

### 4.1 Repair first: the 208 fallback lines

Independent of everything else. One line in `scan_line`'s fallback (stand-in
feet instead of `x.foot = 0`), or the same in `tokens_of`, then re-synthesis of
208 lines across 14 corpora and a re-zip. The five worst Homeric Hymn lines, 73
lines of Nonnus and 42 of Theocritus are among them. The QC reports and the
README's per-corpus PER shift slightly (Theocritus most). `notes/decisions.md`
records "unmetrical lines are synthesized, not skipped"; this makes that decision
actually deliver audible lines.

### 4.2 Stichic verse in other metres

About 60,000 lines: the Anthology and the epigrams (elegiac couplets, with other
metres mixed in), the spoken parts of drama and Lycophron (iambic trimeter),
trochaic tetrameters, anapaests. Here the metre still decides quantity, so this
is the hexameter method with a different grammar.

- **Generalize the solver, not the scanner.** `solve()` hard-codes six feet of
  `LSS | LL` with a two-syllable close. Everything before it (nuclei, position,
  nature, option costs, synizesis) is metre-independent. A pattern grammar per
  metre replaces the loop: pentameter as two hemiepes with a fixed second half;
  trimeter as three metra `x L S L` with resolution at a cost and Porson's
  bridge as a tiebreak; tetrameter and anapaestic dimeter likewise.
- **Costs are per genre.** In Homer a stop + liquid normally makes position and
  the short scansion costs 1.0. In Attic dialogue it is the other way round
  (Attic correption). Epic correption of a final long vowel in hiatus hardly
  exists in tragedy. The `COST` table needs a profile per metre and genre.
- **Take the metre from the markup, never from the scanner.** The hexameter
  scanner is far too permissive to tell metres apart: it accepts 99 % of
  Anthology lines as hexameters although half are pentameters, and 83 % of the
  trimeters of the Oedipus Tyrannus (*measured*). This is why Idyll 29 and the
  pentameters in Idyll 8 slipped through in Phase 10. Drama has section labels;
  couplets alternate; the Anthology needs a per-poem guess (try couplet, then
  hexameter, then trimeter, keep the cheapest total cost) with the cost reported.
- **Validation.** There is no Chamberlain for the trimeter. What can be
  checked: internal consistency (a word form must get the same lengths wherever
  it occurs), agreement with the macronizer of §4.3 on tragic vocabulary
  (macronizer.gr was built on exactly the tragedians' 41,000 forms), and the
  scan-failure rate per play.
- **The foot feature.** Until the model is retrained (§4.5), number the
  positions 1–6 across the line as in the probe. A trimeter has six iambic
  feet, so for once the stand-in is almost honest.

Value beyond the audio: every line scanned in a new metre yields meter-certain
vowel lengths for Attic and Doric vocabulary that Homer never uses. Spoken
tragedy and comedy are the nearest thing to Attic prose that has a metre.

### 4.3 Vowel length without a metre

This is the central text-side problem of prose. *Measured*, with the current
lexicon and accent rules and no metre:

| Text | α ι υ undecided, % of syllables | of which in open syllables (weight depends on it) | Tokens found in the lexicon |
|---|---|---|---|
| Odyssey (reference) | 9.3 % | 4.7 % | 36.8 % |
| Plato, Apology | 15.5 % | 10.7 % | 19.5 % |
| Herodotus | 16.9 % | 11.5 % | 19.7 % |
| Sophocles, OT | 17.0 % | 11.1 % | 18.2 % |
| Thucydides | 18.3 % | 12.4 % | 16.1 % |
| New Testament | 19.9 % | 14.3 % | 15.5 % |
| Greek Anthology | 19.9 % | 13.0 % | 21.6 % |
| Aristophanes | 20.0 % | 14.1 % | 17.7 % |
| Plutarch | 21.8 % | 15.4 % | 14.7 % |
| Pindar | 23.3 % | 15.8 % | 19.9 % |

Undecided means "defaults to short", and most dichrona are short, so the error
rate is a fraction of these figures. On the Iliad validation lines, dropping the
metre changes the weight of 3.0 % of syllables, but only 0.6 % are syllables
the metre makes long and the prose path reads short; the rest are metrical
licences (correption, weak position) that prose does not have. With prose's
lower lexicon coverage I would expect a few per cent of syllables to carry a
wrong vowel length. That is an estimate; the test at the end of this section
replaces it with a number.

How much it matters: in verse a wrong length breaks the line. In prose it makes
one vowel about 100 ms too short inside an otherwise correct word. It is the
difference between a careful reading and a slightly careless one, not between
right and unintelligible. It deserves effort in proportion.

Sources of length, cheapest first:

1. **The verse already scanned.** The lexicon is built from the Iliad alone.
   The 65,000 lines of the other corpora have been scanned and their
   meter-certain lengths never fed back. Harvesting them (with the existing rule
   that lexicon-derived lengths must not count as evidence) is free and covers
   Hellenistic and imperial vocabulary. The verse of §4.2 then adds Attic.
2. **Morphology.** The lemma-and-ending rule already in `lemma_lexicon.py`
   generalizes once every token has a lemma and a tag. Opera Graeca Adnotata
   (40 M tokens; `workspace/conllu.zip` is already under the app's
   `data-sources/`) supplies both for essentially the whole corpus, by automatic
   annotation, under CC BY-SA 4.0. GLAUx (20 M tokens, also there) is a second
   opinion, but parts of it rest on CC BY-NC treebanks and texts, which cannot
   feed a CC BY-SA release; use it only text by text where its metadata says
   BY-SA. Dialect helps here: a Doric ᾱ whose Attic-Ionic lemma has η in that
   position is long, and Attic ᾱ after ε ι ρ in first-declension endings is
   long by rule.
3. **A macronizer.** Cleland and Cullhed, "Automatic Annotation of Ancient Greek
   Vowel Length" (arXiv 2608.01935, August 2026), describe a general-purpose
   macronizer that takes exactly that CoNLL-U input, with a rule system and a
   character-level transformer on top; the code is `grc-macronizer` (GPL-3.0,
   on PyPI). I have read the abstract and the README, not run it. It should be
   used as an external tool whose output table is consumed here; check its
   licence and the provenance of its bundled data before vendoring anything
   into a CC BY-SA repository.
4. **Dictionaries.** The English Wiktionary dump under `data-sources/` marks
   length in Ancient Greek headwords; LSJ marks it irregularly.

**The test that makes this measurable.** The metre is ground truth. Run the
prose path (lexicon, rules, macronizer, no metre) on verse, and compare its
lengths with what the scanner decides when it is allowed the metre: 80,000 lines
of labelled data for free, split by dialect and period. Tragic trimeters, once
scannable, are the proxy for Attic prose. A source is adopted when it raises
agreement on held-out verse; the prose error rate is then quoted from the
nearest verse (Sophocles and Aristophanes for Plato and Lysias; nothing good for
the New Testament, which has to be sampled by hand).

### 4.4 Lyric

Pindar, Bacchylides and the sung parts of drama: about 28,000 short lines,
perhaps 30 hours, the hardest text per hour in the corpus. No stichic pattern,
Doric colouring, heavy corruption, and colometry that differs between editions.

The lever is responsion: strophe and antistrophe scan alike, and Perseus marks
both. Align each strophic pair syllable by syllable; where one side is fixed by
nature or position and the other has an undecided α ι υ, the fixed side decides.
Epodes and astrophic passages get quantities by nature and position only. This
is a real piece of work with no validation set, and it should come last. Until
then lyric can be read with the prose path, which already gives the right phones
and mostly the right weights.

### 4.5 The acoustic model

The probe changes the question from "can it?" to "what would make it honest?".
Two options that are open, and one that is not:

- **Use `fs2_full` as it is, with stand-in or phrase-position feet.** Zero
  cost. Good enough to repair the fallback lines and to produce pilot audio for
  a listener. The six-foot shape it asserts turns out to be mild (§3), so this
  is a workable way to start, not only a stopgap.
- **Retrain once on the same 23 hours with inputs that exist for any text**
  (7.5 hours on the M4). Replace the foot stream, or drop it at random during
  training so the model has a genuine "no metre" mode, and add what prose
  actually has: the punctuation mark after each word as a boundary type, and the
  syllable's position in its phrase. The Iliad can teach this: 39 % of its
  lines have punctuation inside them, and line ends are 42 % unpunctuated, 22 %
  full stop, 18 % comma, 16 % raised dot (*measured*). A model that sees those
  marks can learn "sentence ends here" against "sense runs on", which is the
  distinction prose needs at every colon. Also raise the position table so a
  long colon cannot crash. The validation gate is the existing one: the Iliad
  PER, duration ratio and accent contrasts must not regress.
- **Prose training data from elsewhere: none found that the project's rule
  allows.** The rule (set 2026-10-01, widened 2026-10-02): audio from the
  internet may be used only if it is clearly licensed CC BY-SA or CC BY (the
  more liberal licence is acceptable), and any audio used is listed with its
  source (§8). There is no prose in Chamberlain's voice, and the two prose
  recordings a search turned up cannot be used: Ioannis Stratakis's audiobooks
  are sold, with no Creative Commons licence that I could find, and the LibriVox
  reading of Plato (3 h 42 min) is in modern Greek pronunciation, so it is
  useless here whatever its licence (it is "public domain in the USA", which is
  neither of the two licences the rule names). Two further searches for CC BY
  material found nothing at useful scale. I know of no CC BY or CC BY-SA
  recording of Greek prose in restored pronunciation. This option is therefore
  closed in practice unless such a recording appears; if one does, it means a
  second speaker, a multi-speaker model and a second alignment, and it enters
  the table in §8 before a single file is downloaded. The consequence is that
  prose cadence has to come from what the Iliad recordings can teach (the
  previous option) and from signal-level control of pauses and pace.

Rejected: a general-purpose multilingual or zero-shot TTS system. It would
sound more natural and would know nothing about quantity or pitch accent, which
are the reason this project exists.

**How prose should be cut.** Synthesize by colon and join the cola into one
file per app unit. The rule, as implemented in `scripts/probe_non_hexameter.py`
(`cola`, `split_long`) and used for the E conditions and the samples below:

- A full stop, raised dot or question mark always closes a colon.
- After a comma or colon, a short piece is merged forward until the colon has at
  least ten syllables, so that "οὐκ οἶδα·" stands alone but "ὦ ἄνδρες Ἀθηναῖοι,"
  does not.
- A stretch of more than 25 syllables without punctuation is cut at a word
  boundary, choosing the conjunction nearest the middle (καί, ἀλλά, ἤ, ὡς, ὅτι,
  εἰ, ἐπεί, ἵνα, ὥστε, οὐδέ …), failing that the preposition nearest the middle,
  failing that the nearest word boundary, never immediately before a postpositive
  (δέ, γάρ, μέν, τε, οὖν, ἄν …); each half is cut again if still too long.
- Each colon gets phrase-position feet (1 at the start, 3 in the middle, 5 and 6
  on the last five syllables). The pause after a colon follows its mark: 0.15 s
  for a cut with no mark, 0.25 s after a comma, 0.4 s after a raised dot or
  colon, 0.55 s after a question mark, 0.6 s after a full stop.

On the 300 Apology units this gives 890 cola, median 14 syllables, none above
25, 26 under six (*measured*). Articulation is unchanged by the cut (E2 4.52 %
against D2 4.59 %), so the cut is there for the frame ceiling, for pauses that
follow the sense, and to keep every piece inside the length the model was
trained on. An earlier version of the rule merged short pieces forward across a
raised dot and left 50-syllable stretches whole; both were audible in the first
samples and are fixed. What the rule cannot do is parse: it cuts before καί
whether that καί opens a clause or joins two nouns. The `dur_scale` option in
`fs2.py` can quicken prose by 10–20 % if three syllables a second proves too
stately; that is a listener's call.

**Samples.** `scripts/probe_non_hexameter.py --samples` reads three Apology
passages this way, in the unconverted voice and in the released female voice
(`data/synth/probe_non_hexameter/samples/{male,female}/`): the opening sentence
(17a, five cola, 20 s), the sentence ending ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς
ἀνθρώπῳ (38a, six cola, 35 s) and that clause alone (5 s). The 38a passage is
also given in a third voice, a lower male one (`samples/male_low/`, next
paragraph). `--dialogue` adds a two-voice passage, Apology 26c–d, Socrates
questioning Meletus (`samples/dialogue/apology_26c.wav`, seven turns, 2 min):
Socrates in the low male voice, Meletus in the female one, each turn read as
prose and the turns joined with a half-second pause; `--socrates b` gives the
same passage with voice b (120° on the sphere below, the voice the Phase 8
checks favour) as Socrates (`apology_26c_b_female.wav`), and either speaker can
take any of the sphere voices. The speaker turns were
marked by hand, and that is particular to this passage: the Apology is a speech,
and Perseus marks the live exchange with Meletus (26c–27e) with nothing at all
(its 33 `<q>` elements are quotations: the imagined Callias exchange, the oracle,
Homer), so the app's units run the turns together without so much as a space
("…διδάσκων διαφθείρω;πάνυ μὲν οὖν σφόδρα ταῦτα λέγω.πρὸς αὐτῶν τοίνυν…"). The
dialogues proper are marked: the Phaedo with `<label>` and `<said who>`, and the
app's `speaker` column is filled for the Laws (1,999 rows), Sophist, Philebus,
Gorgias, Theaetetus and the rest. For them, as for drama, a voice per speaker
comes straight from the database. They are the listening material for decision
2 of §7.

**The voices.** The WORLD conversion (+7 st, formants +14 %) is applied after
synthesis and is indifferent to what was synthesized. Phase 8 already records
that it is at the edge of what a warped male envelope tolerates. Across 2,000
hours a listener will notice more than across Hesiod. If a retraining is being
done anyway, training on the converted Iliad is worth one experiment: it removes
the conversion pass (about a sixth of the batch time: 5 of 30 minutes for the
Hymns) and lets the vocoder smooth WORLD's artefacts instead of receiving them
last.

The same machinery gives a second releasable voice for nothing: the Phase 8
setting mirrored, −7 st and formants ÷ 1.14, with tilt, first-harmonic boost
and breathiness again at 0. On the 38a sample (`samples/male_low/apology_38a.wav`)
the median F0 goes from 139 to 93 Hz and the timing and accent intervals are
untouched, as before. Three things about it:

| | Low male | Unconverted | Female (released) |
|---|---|---|---|
| F0 shift | −7 st (139 → 93 Hz) | 0 | +7 st (139 → 209 Hz) |
| Formant warp | × 0.877 | 1 | × 1.14 |
| Distance from Chamberlain's own voice | 7 st and 12 % | none: not released | 7 st and 14 % |

- It is as far from Chamberlain's voice as the female one, in the other
  direction, so the reason the unconverted audio is withheld (too close to his
  own voice) does not apply to it.
- Whether a downward warp sounds as clean as the upward one is not known; Phase 8
  only searched upward, and the "processed" quality it found above +15 %
  formants may appear here at −12 %. If it does, −5 st and × 0.92 is the next
  thing to try. One listener, one passage.
- It is the obvious second voice for drama and dialogue (§4.7): two speakers
  trading lines in the Apology, or a messenger against a chorus, can be told
  apart by voice without any change to the model, since the conversion is a
  per-file setting chosen from the speaker label. The `--dialogue` sample
  above does exactly this.

**What a voice is made of.** The female and low male voices move only two of
the converter's six variables. All six, with the step Phase 8 found usable,
which serves as the unit of each axis below:

| Variable | What it changes | Unit | Notes |
|---|---|---|---|
| Pitch shift | F0 × 2^(st/12); every accent interval preserved | 7 st | the female voice's +7 |
| Formant warp below 1 kHz (α₁) | vocal-tract length as heard in F1 | × 1.14 (log axis) | the female voice's +14 % |
| Formant warp above 1.5 kHz (α₂) | the same for F2 and F3; may differ from α₁ | × 1.14 (log axis) | Phase 8's two-band idea; blended 1–1.5 kHz |
| Spectral tilt | −k dB per octave above 300 Hz: darker or brighter | 3 dB/oct | Phase 8 grid 0–3 |
| First-harmonic boost (H1) | energy around F0 up: a more open glottis | 2.5 dB | one-sided: the converter ignores a negative boost |
| Breathiness | aperiodicity up, twice as much above 3 kHz | 0.08 | one-sided: clipped at 0 |

Not variables, on purpose: timing (the rhythm is a deliverable) and pitch range
(it carries the accent). The remaining knob the converter has, the −2 dB shelf
above 6 kHz, is fixed.

**Any number of voices: the sphere round Chamberlain.** Every voice is a point
in that six-dimensional space, whose origin is Chamberlain's own voice.
`scripts/voice_sphere.py` makes the construction general. The female voice is
the point (1, 1, 1, 0, 0, 0) and its distance from the origin, √3, is the radius.
Every voice the script produces lies on that sphere, so every one is exactly as
far from Chamberlain's voice as the released female one, which is the
requirement; two axes are one-sided (a negative H1 boost is ignored, breathiness
is clipped at 0), so directions are reflected into the allowed half-space.

A voice is named by its angle θ from the female direction and by the direction
it rotates toward: `plane` lowers pitch while both formant bands rise (0° the
female voice, 180° the low male), `split` moves F1 against F2–F3, `tilt`,
`breath` and `h1` leave the pitch–formant diagonal for those axes, and `all`,
the default, is the equal mix of the five, so the distance is spread over every
variable and no single one has to go far. `--random N` draws directions
uniformly on the sphere; `--vector` takes one explicitly. Made for the 38a
sample (`samples/sphere/<name>/apology_38a.wav`):

| Voice | θ, toward | Pitch | F1 warp | F2–F3 warp | Tilt | H1 | Breath |
|---|---|---|---|---|---|---|---|
| female (released) = `all_000` | 0° | +7.00 st (139 → 209 Hz) | × 1.140 | × 1.140 | 0 | 0 | 0 |
| **a** (`all_060`) | 60°, all | −0.33 st (139 → 137 Hz) | × 1.178 | × 1.040 | +2.0 dB/oct | +1.7 dB | 0.054 |
| **b** (`all_120`) | 120°, all | −7.33 st (139 → 91 Hz) | × 1.033 | × 0.912 | +2.0 dB/oct | +1.7 dB | 0.054 |
| low male = `all_180` | 180° | −7.00 st (139 → 93 Hz) | × 0.877 | × 0.877 | 0 | 0 | 0 |
| `all_240` | 240°, all | +0.33 st (139 → 142 Hz) | × 0.849 | × 0.962 | −2.0 dB/oct | +1.7 dB | 0.054 |
| `all_300` | 300°, all | +7.33 st (139 → 213 Hz) | × 0.968 | × 1.096 | −2.0 dB/oct | +1.7 dB | 0.054 |
| `plane_060` | 60°, plane | −5.07 st (139 → 104 Hz) | × 1.157 | × 1.157 | 0 | 0 | 0 |
| `plane_120` | 120°, plane | −12.07 st (139 → 69 Hz) | × 1.015 | × 1.015 | 0 | 0 | 0 |

The first six rows are one great circle of the sphere at 60° steps
(`--theta 0 60 120 180 240 300`), all made for the 38a passage: six voices at
the same distance from Chamberlain, with the released female voice and the low
male voice among them. Because the one-sided axes are reflected, 240° and 300°
are not the mirror images of 120° and 60°: they take the opposite pitch and
formant moves (a longer tract, a brighter tilt) but the same positive H1 boost
and breath.

On paper: **a** keeps Chamberlain's pitch and gets its distance from a shorter
vocal tract in the F1 region, a darker tilt, a more open glottis and some
breath; **b** is a low voice with its upper formants pulled down, the same tilt
and breath; `all_240` is at his pitch with a longer tract and a brighter tilt;
`all_300` is as high as the female voice but with a longer tract in the F1
region, brighter and breathier. The plane-only points show why the other variables matter: to be
√3 away using pitch and formants alone, `plane_120` has to go to 69 Hz and
`plane_060` to −5 st with +16 % formants, whereas the `all` points reach the same
distance with every variable inside the range Phase 8 tested. Spreading the
distance over six axes is what makes a large distance from Chamberlain
compatible with a natural-sounding voice.

Two cautions. Any point off the diagonal pairs features that natural voices
rarely combine, so the further from the diagonal, the more a voice is a
character rather than a second narrator; useful in comedy, less so in
Thucydides. And the sphere guarantees distance, not quality: which points are
worth releasing is, as with everything about the voices, a listener's choice,
and Phase 8's acoustic checks should run on any candidate before it reads 200
hours. They were run on these six.

**The Phase 8 checks on the six voices** (`voice_sphere.py --eval`, which runs
`scripts/eval_voice.py`; on the 227 Apology units of probe condition D2,
converted from the unconverted synthesis; *measured*):

| Voice | PER (unconverted 4.59 %) | F0 median → (target) | F1 ratio, front vowels (α₁) | F2 ratio, front vowels (α₂) | F2 ratio, back vowels ο ω ου | H1−H2 | HNR | Unvoiced | Acute step |
|---|---|---|---|---|---|---|---|---|---|
| female, 0° | 11.78 % | 206 Hz (204) | 1.17 (1.14) | 1.13 (1.14) | 1.11–1.16 | +4.7 dB | +3.7 dB | −5.9 pts | −0.10 st |
| a, 60° | 6.13 % | 135 Hz (133) | 1.12 (1.18) | 1.04 (1.04) | 1.10–1.16 | +2.3 dB | +4.3 dB | −6.5 pts | −0.11 st |
| b, 120° | 6.81 % | 90 Hz (89) | 0.99 (1.03) | 0.92 (0.91) | 1.00–1.02 | +4.4 dB | +3.6 dB | −5.0 pts | −0.11 st |
| low male, 180° | 11.63 % | 92 Hz (91) | 0.94 (0.88) | 0.93 (0.88) | **1.7–4.0** | +1.3 dB | +2.3 dB | −3.7 pts | −0.10 st |
| 240° | 5.17 % | 140 Hz (139) | 0.96 (0.85) | 0.99 (0.96) | **2.6–4.3** | +3.7 dB | −0.2 dB | −3.3 pts | −0.07 st |
| 300° | 6.19 % | 210 Hz (208) | 1.00 (0.97) | 1.09 (1.10) | 1.0, **4.6**, 1.2 | **+9.1 dB** | +0.7 dB | −3.7 pts | −0.08 st |

Against the Phase 8 criteria:

- **Articulation (PER, a relative guard).** The two pure pitch-and-formant
  voices sit where Phase 8 put the female voice (about 11–12 %: the recognizer
  reads a full ×1.14 warp as phonetic change). The four mixed voices sit at
  5–7 %, within two points of the unconverted audio, because each of their
  formant bands moves less. By this measure the mixed points are the better
  voices, which is the argument for the six-axis sphere in numbers.
- **Pitch.** Every median F0 lands within 2 Hz of its target and every accent
  contrast is preserved within 0.11 st, as the construction guarantees (F0 is
  scaled, never reshaped). All six pass.
- **Formants.** Where the warp goes up, the measured ratios match the intended
  ones within Phase 8's 5 % (a's F1 at 1.12 against 1.18 is the one borderline
  case). Where the warp goes down, the front vowels follow it only part of the
  way (180°: 0.94 against 0.88; 240°: 0.96 against 0.85) and the back vowels
  ο ω ου return F2 ratios of 1.7 to 4.6, which is not a formant moving but the
  tracker finding a different peak. Either the downward warp merges F1 and F2
  in the rounded back vowels and Praat reports F3 as F2, or WORLD's envelope
  really does lose the lower formant there. The measurement cannot tell; a
  listener can, in two seconds, on ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ in
  the 180° and 240° voices. Until that is heard, the voices with formants
  pulled down are the unproven half of the sphere, and Phase 8's remark that it
  only ever searched upward stands.
- **Source.** H1−H2 rises 2–5 dB where it should and HNR never falls by more
  than 3 dB (the released voice itself gains 3.7 dB: WORLD resynthesis is
  cleaner than the vocoder's output). The 300° voice's +9.1 dB is the H1 boost,
  the brighter tilt and the high pitch compounding; it will sound soft or
  breathy and is the one setting the checks say to tone down.
- **Artefacts.** Every voice, the released one included, lowers the unvoiced
  fraction by 3–6 points on Praat's tracker. Phase 8's 2-point rule was
  written for WORLD's own voicing decision; here it is a property of the
  conversion as such, not of any point on the sphere, so it does not separate
  the voices.

The same checks on the dialogue sample itself (its 18 Socrates cola in voice
b, its 4 Meletus cola in the female voice, each against the unconverted cola):
Socrates/b PER 3.43 → 5.32 %, F0 139 → 92 Hz, F1 ratios 0.95–1.00 against
1.03 intended and F2 0.90–0.99 against 0.91, the back vowels ο ω ου at
0.98–1.04 with no anomaly, H1−H2 +4.3 dB, HNR +3.4 dB. The accent contrasts
move more here than on the 227-unit set (acute +2.23 → +1.67 st, circumflex
+0.01 → −0.61) — on 18 short cola the per-class means rest on a handful of
syllables, and at a 92 Hz median some frames fall under the tracker's 60 Hz
floor; the F0 is scaled by a constant, so the intervals themselves are
unchanged. If b becomes a standing voice, the check should be run with more
headroom above the floor (a lower floor in `eval_voice.py`, or the voice a
semitone higher), so that the number means what it is meant to. Meletus/female: PER 5.98 → 16.24 % (the full ×1.14 warp, as always),
F0 138 → 207 Hz; four cola are too few for formant or accent statistics.

What the checks say, then: b (120°) is the cleanest new voice on every number,
on the 227-unit set and on the dialogue passage alike; a (60°) and 240° are
close behind with the back-vowel question open for 240°; the low male needs its
back vowels heard; and 300° needs its glottal boost reduced. None of this
replaces listening; it says where to listen first, and the two Socrates
versions of the dialogue (`apology_26c.wav`, low male; `apology_26c_b_female.wav`,
b) are the pair to listen to.

### 4.6 One pronunciation for nineteen centuries

The corpus runs from Homer to Zonaras. The model's forty phones are Chamberlain's
voice saying Allen's classical values: aspirated stops (barely aspirated, by the
Phase 3 measurements), ζ as [zd], υ as [y], long and short vowels, a pitch
accent. A pronunciation of the New Testament's own century needs [f θ x v ð ɣ],
no vowel length and a stress accent, and none of those sounds exist in 23 hours
of Homer. They cannot be synthesized without a different voice.

So the choice is between a uniform restored-Attic reading of everything and
leaving the late texts out. I recommend the uniform reading, stated plainly in
the README and the package names. It is what a classroom does, it keeps the
quantities that Greek prose rhythm (clausulae included) was built on, and it
costs nothing extra. Dialects need no new phones: Doric, Aeolic and Ionic
spellings map onto the same inventory, and their difference is in the length
lexicon (§4.3). The Phase 10 finding that dialect costs about two points of PER
is partly the recognizer's unfamiliarity and will apply to Attic too (the
Apology's 4.6 %).

### 4.7 What is read, and what is not

The hexameter parser strips brackets, daggers and digits and keeps supplied
text, on the rule that "the audio says what the app displays". Prose stretches
that rule. *Measured* over all 631,721 units, after removing the leading
section label:

| In the unit | Units | What to do |
|---|---|---|
| Section labels (`[17a]`, `[1.1]`, `[PROP.24]`) at the start | most prose | strip, never read |
| Editorial brackets, angle brackets, daggers | 14,216 | read the text, drop the signs (as now) |
| Arabic digits in the body | 11,838 | mostly embedded references; strip, and list the units where a digit stands for a word |
| No Greek letters at all | 666 | no audio |
| Latin-alphabet words | 114 | skip the word, flag the unit |
| Greek numeral signs (ʹ ͵) | 35 | expand to the number word, by hand at this count |

And kinds of text rather than characters:

- **Speaker labels** in drama and dialogue are metadata (`text_lines.speaker`)
  and are not read. That raises the one attractive luxury: a second WORLD
  setting per speaker in drama, for which the low male voice of §4.5 is the
  candidate (the `--dialogue` sample shows it). Drama and the Platonic
  dialogues have the labels in the database; the Apology's exchange with
  Meletus is the exception and needed hand marking. Not now.
- **Shared lines.** A trimeter split between two speakers is two rows with one
  line number (§5).
- **Verse quoted in prose** (oracles in Herodotus, Homer in Plato, most of
  Athenaeus) should take the verse path. The TEI marks it (`<quote type="oracle">`
  and 151 `<l>` in Herodotus, `<quote type="verse">` in the Republic, over
  11,000 `<l>` in Athenaeus), but the app's row does not: the two hexameters of
  the oracle at Herodotus 1.47 are one prose unit there. So the pipeline has to
  read the TEI, as the hexameter parser already does, and map lines back to
  app units.
- **Reference works are not read aloud.** Harpocration's lexicon, Euclid (where
  `ΑΒΓ` is a triangle and each letter would have to be read by name), Ptolemy's
  tables. Either leave these out or accept that the audio is a curiosity.
- **Fragments and lacunae**: synthesize what is there, as for the 25 empty lines
  of Phase 10.

Every one of these is a per-author check, which is the argument for processing
prose author by author with a text report each, as Phase 10 did per corpus.

---

### 4.8 Future work: delivery that follows the grammar

Everything above gets the sounds right and the pauses roughly right. What it
does not do is read with understanding: the colon rule knows punctuation and a
list of conjunctions, the model knows the hexameter's shape, and neither knows
that ὦ ἄνδρες Ἀθηναῖοι is a vocative set off from its sentence, that a
γάρ-clause explains what came before and should start lower and move faster,
that a question ending in ; rises, or that the second half of a μέν … δέ
contrast answers the first. A listener will hear that absence long before they
hear a wrong vowel length. Closing it is the main piece of work after the
pilot, and the material for it is already on disk.

**What "grammatical understanding" can mean here.** Not meaning, which no
component has, but syntactic structure, which Opera Graeca Adnotata and GLAUx
supply for every sentence in Perseus as dependency trees (lemma, part of
speech, morphology, head, relation), and a prosodic grammar that maps that
structure onto what the voice can do. The reference for the mapping is Devine
and Stephens, *The Prosody of Greek Speech* (1994), who reconstruct Greek
phrasing (which words cohere, where the breaks fall, how clitics and
postpositives attach) from the metrical and inscriptional evidence; the colon
rule of §4.5 is a crude stand-in for what they describe.

**The pieces, in order of payoff:**

1. **Phrasing from syntax instead of punctuation.** Cut cola at clause
   boundaries read off the parse: a finite verb with its subordinator or
   participle closes a clause; a καί that joins two nouns is not a boundary, a
   καί that opens a clause is. Keep clitics and postpositives (δέ, γάρ, μέν,
   τε, ἄν, ἐστι) with their hosts; keep a preposition with its noun phrase, an
   article with its noun, a vocative as its own colon. This replaces the
   conjunction list with the tree and is the one item that is pure engineering
   on data already present. Measure it as the share of cuts that fall on a
   dependency edge of the right kind, and by ear.
2. **A sentence arc.** Today every colon is synthesized alone and starts fresh,
   so a sentence of six cola is six beginnings; there is no declination, no
   final low that is lower than the others. Give the model, or a post-hoc F0
   shaper, the colon's place in the sentence (first, medial, last) and the
   sentence's place in the paragraph: a step down per colon and a reset at the
   sentence start. The Iliad can teach the shape of a single line's arc; the
   arc across cola is a rule to write, not a thing to learn, and the WORLD
   pass already exists to apply an F0 offset per colon.
3. **Boundary tones by clause type.** Questions rise or hold; statements fall;
   a colon that ends a subordinate clause before the main one holds rather
   than falls. The Iliad has 165 lines ending in a question mark, too few to
   learn from, so this is shaping by rule: an F0 contour over the last two or
   three syllables chosen from the clause type in the parse and the mark.
4. **Register for parentheses, explanations and quotations.** A γάρ-clause,
   a parenthesis between dashes, a relative clause inside its noun phrase:
   lower onset, narrower range, a little faster (`dur_scale` 0.9). A
   quotation inside a speech, or a change of speaker inside a unit: the
   second voice of §4.5, or a pitch offset.
5. **Prominence.** Which word in a colon carries the sense is the hardest and
   the most audible: the contrasted term in μέν … δέ, the fronted word, the
   negated word, the answer to the question just asked. Word order in Greek
   is itself the main cue (Dover, *Greek Word Order*; Dik, *Word Order in
   Ancient Greek*): the preverbal focus position and the clause-initial topic
   are readable from the parse and the word order together. The model has no
   emphasis input and Chamberlain's reading has no emphasis labels, so this
   is again shaping after synthesis: a larger pitch excursion and a longer
   duration on the focused word, with the quantities and the accent shape
   kept. Product B's F0 shaping, planned in Phase 7b and never built, is the
   same mechanism.

**The missing reference recording.** For verse the project has what every
one of its claims rests on: Chamberlain's 23 hours of the Iliad, read line by
line in restored pronunciation, aligned to the text and openly licensed. It is
the training data, the recognizer's floor (3.2 % PER on his own recordings),
the baseline every prosody metric is checked against (long : short 2.07,
acute +2.45 st), and the ground truth the scanner was validated on. For prose
there is nothing comparable, and so everything in this section, and the pilot
of §6, is judged against a listener's taste rather than against a reading.
What would serve: a few hours of Greek prose, ideally the texts of the pilot
(the Apology, Lysias 1, Herodotus 1, a Gospel), read in restored pronunciation
by a competent reader, at a known pace, aligned to the text at the sentence or
colon, under CC BY or CC BY-SA. Even two hours would do three things that
nothing else can: give the recognizer a prose floor (today its 4.6 % on the
Apology is unanchored, since it has never heard prose), supply the pause
lengths, sentence arcs and boundary tones that the five pieces above would
otherwise be written from theory, and offer a second speaker for the model if
one is wanted. §8 records that no such recording was found under the licence
rule. The two routes to one are to find it, which the searches so far have
not, or to make it: a reader, a text, a day in a quiet room, and a licence,
which is outside this repository but not outside the project. Until then the
Iliad stands in where it can (phones, quantities, accent), and the prose
prosody is designed, not measured.

**What this does not touch.** Phones, quantities and the accent's own shape
stay as they are; everything above moves pitch level, pitch range, pause and
pace at the level of the colon and the word, which is exactly what the WORLD
pass can do without disturbing them. And it is work for a listener as much as
for a parser: each of the five pieces needs a few passages judged by ear
before it is applied to a thousand hours. The order above is the order in
which they are both easiest to build and easiest to hear.

## 5. Addressing, scale and delivery

### Addressing

The app finds audio by author, work title, book number and integer line number,
parsed from the path. Three weaknesses, the first two already known from Hesiod:

- Lettered and compound line numbers (929a, 41_43) and the Dionysiaca's line 0
  are not addressable.
- **2,785 line numbers belong to more than one row** (*measured*): 1,807 of them
  in Aristophanes, where speakers trade half-lines. One `line_N.mp4` cannot
  serve both rows.
- A prose line number is a sequence number produced by the app's sentence
  splitter. If a database rebuild segments one sentence differently, every later
  unit in the book plays the wrong audio and nothing detects it.

For anything beyond stichic verse the package should be keyed to the row, not
the printed number: `sequence_number` within the book, plus a manifest that
records the database build and a hash of each unit's text, so the importer can
refuse or skip units whose text has changed. That is an app change, and it
blocks drama and prose more than any modelling question does.

### Scale

| | Done (15 hexameter corpora) | To do | Whole Perseus Greek corpus | Basis |
|---|---|---|---|---|
| Audio | 94.8 h | ~1,970 h at verse pace, ~1,600 h if prose is quickened 20 % | **~2,060 h** synthesized plus Chamberlain's 23 h; about 86 days of continuous listening | characters ÷ 8.18 per second |
| Files | 64,946 | ~551,000 units | **~631,000** | one file per app unit |
| Storage at AAC 96 kb/s | 4.3 GB | ~90 GB | **~95 GB**, plus the 1.0 GB Iliad package | 46 MB per hour including container overhead |
| Storage at 32 kb/s | | ~30 GB | **~32 GB** | a third of the above |
| Compute on the M4 | 8 h for 95 h of audio | ~150 h, about a week | **~160 h, about seven days** of continuous processing | 12.9 × real time, all stages: synthesis, recognizer QC, voice conversion, encoding, packaging |
| Lines flagged at the present rate | 1,329 (2.0 %) | ~11,000 at 2 %, 33,000–44,000 at the probe's 6–8 % | | per-line PER > 10 % |

The compute figure is the batch rate of Phase 10 (60,479 lines, 88 hours of
audio, 6 h 49 min wall clock) applied to the whole corpus; it excludes the
one-time costs, which are small by comparison (text tables for all 772 works,
hours; a retraining, 7.5 h; the lexicon work of §4.3, human time rather than
machine time). Both the hours of audio and the storage scale with the pace
chosen for prose: `dur_scale` 0.8 takes a fifth off every number in the
"whole corpus" column except the file count.

Compute is not the constraint. Storage and QC are.

**Storage.** 96 kb/s was chosen to match Chamberlain's files. For 22 kHz mono
synthetic speech, 32 kb/s (HE-AAC, or Opus where both platforms decode it) is
ample and brings the total to about 30 GB. That is still far beyond the Play
Store's 4 GB cumulative limit that the app's own download analysis records, and
the app deliberately has no network permission. Audio therefore stays
side-loaded, per author or per work, and the app's "one active package at a
time" rule has to go.

**The alternative: synthesize on the device.** The inputs to synthesis are
small. A compact phone table for the whole corpus is tens of megabytes
compressed (estimate), the acoustic model is 174 MB in float32 and would halve
or quarter when exported, and the pretrained vocoder is 54 MB as downloaded.
Both networks are non-autoregressive and should run several times faster than
real time on a phone (to be measured, not assumed). That would give audio for every Greek text
in a download smaller than one author's pack, with no network, in keeping with
the app's all-local design. The costs are real: an inference runtime in the
Android and iOS apps, the voice conversion either ported (WORLD is C++) or baked
in by training on converted audio (§4.5), and the loss of per-line QC of the
exact audio a user hears. The project's stated position is that "the model,
converter and scanner stay offline tools". At 95 hours that was clearly right.
At 2,000 it deserves a second look, and the decision changes what the bulk run
produces (audio files, or verified phone tables), so it should be made before
that run.

A sensible middle: pre-rendered, QC'd packs for verse and for the dozen prose
works most people read; phone tables for everything, so that on-device synthesis
can cover the long tail whenever the app is ready for it. The phone table is the
stable interface either way, and it is worth fixing its format now.

### QC at this scale

The present loop (PER per line, four duration-scale retries, worst forty lines
per corpus to a human queue) does not survive a 17-fold increase. What replaces
it:

- **Text-side checks carry most of the weight**, because the probe shows the
  model says what it is given: unknown characters, units with no Greek, colon
  lengths, the share of undecided α ι υ per work, the vowel-length agreement
  test of §4.3.
- **PER becomes a sampling instrument**: every unit is still scored (it is
  cheap), but the gate is the per-work distribution against the pilot's, with a
  length-scaled per-line threshold, and outlier works are examined, not outlier
  lines.
- **The recognizer is itself out of domain.** It has heard only Homer in one
  male voice. It cannot be checked on real prose audio, because none was found
  that the audio rule of §8 allows, so its prose PER is a relative measure
  only, as it already is for the female voice.
- **Listeners come from the users.** A "this line sounds wrong" report in the
  app, keyed to the same row identifiers as the manifest, is the only QA that
  scales to 550,000 units.

---

## 6. Recommended order of work

Each step is useful if the work stops after it.

| # | Step | Size | Why here |
|---|---|---|---|
| 0 | Stand-in feet in the fallback; re-synthesize the 208 lines; re-zip | hours | fixes shipped audio; needs nothing else |
| 1 | Harvest meter-certain lengths from the fourteen non-Iliad corpora into the lexicon; set up the metre-as-ground-truth test | a day | free coverage; gives §4.3 its yardstick before any prose is touched |
| 2 | Pentameter in the solver; metre from markup. Callimachus Hymn 5 and Epigrams, Theocritus Epigrams, then the Anthology | days; ~31 h audio | smallest step beyond hexameter; closes the gaps listed in the README |
| 3 | Trimeter, tetrameter, anapaests with an Attic cost profile. Lycophron, then spoken drama; lyric passages through the prose path for now | a week; ~72 h | complete plays; Attic lengths for the lexicon |
| 4 | Retrain with boundary types and optional foot; position table raised; try training on the converted voice | 1–2 days of compute | makes the model honest before the large run |
| 5 | Length sources for prose: OGA lemmas and tags, morphology rules, macronizer, Wiktionary; adopt each on the test of step 1 | a week | the central prose problem, now measurable |
| 6 | **Prose pilot, about 5 hours:** the Apology, Lysias 1, Herodotus 1.1–45, Mark. Colon cutting, pause rules, text report per work. **Listening gate.** | days | the one question metrics cannot answer |
| 6b | Delivery from the grammar (§4.8): phrasing from the OGA dependency parse, a sentence arc, boundary tones by clause type, register for parentheses and quotations, prominence from word order; each judged on a few passages by ear | weeks; after the pilot, before bulk prose | the difference between correct sounds and a reading that makes sense |
| 7 | App: row-keyed packages with a manifest, several packs active, lower bitrate. Decide packs against on-device | app work | blocks drama's shared lines and all prose |
| 8 | Prose by author in order of readership: Plato, Xenophon, Lysias and the orators, Herodotus, Thucydides, the New Testament, Lucian, then the large historians and Plutarch | ~a week of compute, a text report per author | bulk |
| 9 | Lyric by responsion: Pindar, Bacchylides, dramatic odes re-done | open-ended | hardest, smallest, no validation set |

Steps 0–3 need no decision from anyone and no listener. Step 6 does.

---

## 7. Decisions that are not mine to take

1. **Uniform restored-Attic pronunciation for every period**, late and Christian
   texts included (§4.6)? My recommendation: yes, declared.
2. **Is a reciter's cadence acceptable for prose**, and at what pace? Only the
   pilot can be judged, and only by ear.
3. **Packs or on-device synthesis** for the long tail (§5)? My recommendation:
   packs for verse and the core prose, phone tables for everything, on-device
   left open.
4. **What to leave out** (§4.7)? My recommendation: leave out Harpocration,
   Euclid and Ptolemy; read fragmentary works as far as they have text.
5. **Which voices to release** (§4.5)? The female one exists; the low male, a
   and b are made for one passage each. My recommendation: keep the female voice
   as the narrator, adopt one low voice for second speakers after a listener
   has chosen between the low male and b on the two dialogue samples (the
   Phase 8 checks favour b: 6.8 % against 11.6 % PER on 227 units, 5.3 % on the
   dialogue itself, and no back-vowel anomaly), and treat the rest of the
   sphere as a tool for drama, where character voices are wanted.
6. **Chamberlain.** The plan calls a note to him a courtesy. CC BY permits all of
   this, but two thousand hours of Greek literature in a voice derived from his
   23 hours, some of it texts he might not choose to be heard reading, is a
   different thing from a Hesiod. I would write before the prose release and
   describe exactly what the voice is.

Where no answer comes, the recommendations above are the defaults, and steps
0–5 of §6 do not depend on any of them.

---

## 8. Sources and licences

### Audio

Rule: audio from the internet is used only if it is clearly licensed CC BY-SA
or CC BY, and every audio source is listed here.

| Audio | Licence | Used for | Status |
|---|---|---|---|
| David Chamberlain, *A Reading of Homer*, Iliad, hypotactic.com (`homer/audio/{book}/line_{n}.mp4`), © 2016–2017 | CC BY 4.0 | training the acoustic model, the aligner and the recognizer | the project's existing and only audio source, attributed in `LICENSE`; meets the rule |
| LibriVox, Plato's Dialogues in Greek, <https://librivox.org/dialogues-by-plato/> | "public domain in the USA" | considered as prose training data | **not used**: modern Greek pronunciation; also neither licence the rule names |
| Ioannis Stratakis, <https://ancientgreek.eu/> | sold as audiobooks; no Creative Commons licence found | considered as prose training data | **not used** |
| Wikimedia Commons, "Audio files in Ancient Greek"; W. H. D. Rouse, *Sounds of Ancient Greek* (1932), on the Internet Archive | per file; not established | turned up by search, pages not opened | **not used**: single words or short passages, licences not checked |

Nothing in this document, including the probe of §3, used any audio other than
the model already trained on Chamberlain's recordings. No audio was downloaded.
The one recording the work lacks is described in §4.8: a few hours of Greek
prose in restored pronunciation, text-aligned, under CC BY or CC BY-SA, to do
for prose what Chamberlain's Iliad does for verse.

One existing dependency should be named for completeness: the pretrained Vocos
vocoder (`charactr/vocos-mel-24khz`, MIT-licensed weights), which every released
package already passes through. The project uses its weights, not any
recording. To my knowledge its authors trained it on LibriTTS, which is CC BY
4.0 and so within the rule; I have not re-verified that.

### Text and data this proposal would draw on

| Source | Licence | Role |
|---|---|---|
| Perseus `canonical-greekLit` | CC BY-SA 4.0 | every text read |
| Perseus Ancient Greek Dependency Treebank 2.0 | CC BY-SA 3.0 | lemma and morphology (already used) |
| Opera Graeca Adnotata v0.2.0 (local, `workspace/conllu.zip`) | CC BY-SA 4.0 | lemma and morphology for the whole corpus (§4.3) |
| GLAUx (local) | mostly CC BY-SA; some texts and treebank layers CC BY-NC | only where the per-text metadata says BY-SA |
| English Wiktionary dump (local) | CC BY-SA | vowel lengths in headwords |
| `grc-macronizer`, <https://github.com/Urdatorn/grc-macronizer> | GPL-3.0 | external tool; its output tables only, pending a check of its bundled data |

---

## Appendix A. Greek authors in Perseus by size

From `perseus_texts_full.db`; units are app rows, hours are characters ÷ 8.18 per
second. Verse authors already done are marked †, verse still to do ‡.

| Author | Works | Units | Characters | ~Hours |
|---|---|---|---|---|
| Plutarch | 143 | 42,341 | 6.49 M | 220 |
| Plato | 36 | 49,457 | 3.48 M | 118 |
| Flavius Josephus | 4 | 21,082 | 3.07 M | 104 |
| Diodorus Siculus | 1 | 17,349 | 2.64 M | 90 |
| Dionysius of Halicarnassus | 13 | 16,070 | 2.47 M | 84 |
| Polybius | 1 | 15,281 | 2.13 M | 72 |
| Athenaeus | 1 | 22,008 | 2.05 M | 70 |
| Xenophon | 14 | 18,981 | 1.94 M | 66 |
| Aristotle | 9 | 16,922 | 1.88 M | 64 |
| Demosthenes | 63 | 14,793 | 1.84 M | 63 |
| Strabo | 1 | 14,545 | 1.77 M | 60 |
| Lucian | 71 | 16,463 | 1.70 M | 58 |
| Procopius | 2 | 11,971 | 1.69 M | 57 |
| Appian | 14 | 9,908 | 1.42 M | 48 |
| Pausanias | 1 | 11,656 | 1.36 M | 46 |
| Clement of Alexandria | 3 | 10,956 | 1.22 M | 41 |
| Homer † (Iliad: Chamberlain) | 3 | 27,903 | 1.21 M | 41 |
| Cassius Dio | 1 | 10,594 | 1.20 M | 41 |
| Herodotus | 1 | 10,228 | 1.19 M | 40 |
| Dio Chrysostom | 1 | 9,442 | 1.10 M | 37 |
| Thucydides | 1 | 6,117 | 0.99 M | 33 |
| Nonnus † | 1 | 21,329 | 0.90 M | 32 |
| Euripides ‡ | 19 | 26,383 | 0.89 M | 30 |
| Aelian | 2 | 8,182 | 0.87 M | 30 |
| Greek Anthology ‡ | 1 | 21,065 | 0.86 M | 29 |
| New Testament | 27 | 7,943 | 0.83 M | 28 |
| Philostratus the Athenian | 5 | 5,194 | 0.78 M | 27 |
| Isocrates | 30 | 4,786 | 0.77 M | 26 |
| Euclid | 1 | 607 | 0.76 M | 26 |
| Arrian | 6 | 5,583 | 0.70 M | 24 |
| Diogenes Laertius | 1 | 9,481 | 0.69 M | 23 |
| Eusebius | 1 | 3,896 | 0.65 M | 22 |
| Hippocrates | 18 | 7,167 | 0.65 M | 22 |
| Aristophanes ‡ | 11 | 17,007 | 0.57 M | 19 |
| Zonaras | 1 | 4,074 | 0.57 M | 19 |
| Julian | 12 | 3,875 | 0.53 M | 18 |
| Epictetus | 3 | 7,984 | 0.51 M | 17 |
| John of Damascus | 1 | 3,566 | 0.41 M | 14 |
| Quintus Smyrnaeus † | 1 | 8,804 | 0.38 M | 13 |
| Sophocles ‡ | 8 | 10,513 | 0.36 M | 12 |
| Lysias | 34 | 2,981 | 0.36 M | 12 |
| Aretaeus | 4 | 4,425 | 0.31 M | 10 |
| Aeschines | 3 | 2,173 | 0.28 M | 10 |
| Achilles Tatius | 1 | 3,101 | 0.26 M | 9 |
| Aeschylus ‡ | 7 | 8,064 | 0.25 M | 9 |
| Apollonius Rhodius † | 1 | 5,834 | 0.25 M | 8 |

The remaining 45 authors are each under 0.25 M characters (under 8 hours):
Ptolemy, Harpocration, Apollodorus, Chariton, Isaeus, Galen, Marcus Aurelius,
Oppian †, pseudo-Plutarch, Aelius Aristides, Pindar ‡, Philostratus the Sophist,
Theocritus † (Epigrams and Idylls 28–30 ‡), Longus, Antiphon, Andocides, Xenophon
of Ephesus, Hesiod †, the Homeric Hymns †, Demetrius, Oppian of Apamea †, Aeneas
Tacticus, Longinus, Onasander, Hyperides, Callimachus † (Epigrams and Hymn 5 ‡),
Lycurgus, Dinarchus, Lycophron ‡, Aratus †, Philostratus the Younger,
Theophrastus, Parthenius, the Epistle of Barnabas, Asclepiodotus, Bacchylides ‡,
Basil, Tryphiodorus †, Callistratus, Moschus †, Colluthus †, Demades,
Agathemerus, Bion †, Proclus.

## Appendix B. How the probe was run

`scripts/probe_non_hexameter.py` (tts env) builds every table, synthesizes,
scores and prints both tables of §3; `--only G,Gp,Gp2` runs a subset and
`--summary-only` re-tabulates. Outputs, including the WAVs, go to
`data/synth/probe_non_hexameter/` (not in git); nothing else is written. To hear
the Apology's first sentence in the unconverted voice:
`afplay data/synth/probe_non_hexameter/wav_D2/apol_1.wav`; the three joined
passages of §4.5 are under `samples/` (`--samples`), the two-voice passage
under `samples/dialogue/` (`--dialogue`), and the sphere voices under
`samples/sphere/` (`scripts/voice_sphere.py`). All inputs are in the
repository or the app database.

1. **Tables.** For each condition a `phones.csv`-shaped table (id, phones,
   quantity, accent, foot). Iliad rows are the 311 validation ids from
   `data/iliad/splits/val.txt`, text from `metadata.csv`, rendered with
   `greek2ipa.from_text.convert_text` using either `scan_line(..., fallback=False)`
   or a scan built exactly as the fallback branch of `scan_line` does
   (`build_nuclei`, `option_costs`, long if long by nature, two consonants
   follow, or last). Prose is the first 300 units of the Apology from the app
   database, section labels and editorial signs removed, passed through
   `diff_transcripts.normalize`; cola as in §4.5 (hard stops always cut, short
   comma pieces merged to at least ten syllables, stretches over 25 split at the
   conjunction nearest the middle). Trimeters are OT 1–150; the elegiac sample is
   Callimachus' Hymn to Athena, odd rows as hexameters, even rows as pentameters.
2. **Stand-in feet.** `runs = ceil(n / 17)`; syllables divided evenly among the
   runs; within a run of `m` syllables, syllable `i` gets foot `1 + (6·i) // m`.
   Phrase-position feet (D4, F4): 1 on the first three syllables, 5 on the three
   before the last two, 6 on the last two, 3 between; units under nine syllables
   keep stand-in feet.
3. **Synthesis and scoring.** `train/fs2.py synth --ckpt train/runs/fs2_full/best.pt
   --phones <table> --list <ids> --out <dir>`, then `train/recognize.py --manifest`
   with each row's own phone string as the reference. Vowel durations and
   per-token F0 are read from the `synth_index.csv` that `synth` writes.
4. **Checks on the probe itself.** The Iliad validation rows taken straight from
   `data/iliad/phones.csv` reproduce the reported 2.36 %; the scanner path gives
   2.30 %; the accent step reproduces the report's +2.29 st.

Limits: one prose work, one play, one elegiac poem; the unconverted voice only;
units above 60 syllables excluded from the whole-unit condition after the
4,000-frame failure; and the recognizer has never heard anything but the Iliad.

## Appendix C. Every command behind the numbers

All in the `tts` conda environment, from the repository root. Outputs go under
`data/synth/probe_non_hexameter/` (not in git); nothing else is written.

```
# §3: the probe, all conditions, both tables (about 40 min on the M4)
python scripts/probe_non_hexameter.py
python scripts/probe_non_hexameter.py --only G,Gp,Gp2        # a subset
python scripts/probe_non_hexameter.py --summary-only         # re-tabulate

# §4.5: three Apology passages read as prose, in the unconverted, female and
# (38a only) low male voices -> samples/{male,female,male_low}/
python scripts/probe_non_hexameter.py --samples

# §4.5: Apology 26c-d, Socrates (low male) and Meletus (female) -> samples/dialogue/apology_26c.wav
python scripts/probe_non_hexameter.py --dialogue
python scripts/probe_non_hexameter.py --dialogue --socrates b          # -> apology_26c_b_female.wav; --meletus likewise

# §4.5: the checks on the dialogue's own cola (D = samples/dialogue; SOC/MEL = the turn0,2,4,6 / turn1,3,5 ids in D/cola.csv)
python scripts/convert_voice.py --in $D/cola_wav --out $D/eval_b/wav --ids $SOC \
    --semitones -7.33 --alpha1 1.033 --alpha2 0.912 --tilt 2.01 --h1 1.68 --breath 0.054
python scripts/eval_voice.py --orig $D/cola_wav --conv $D/eval_b/wav --index $D/cola_wav/synth_index.csv \
    --phones $D/cola.csv --ids $SOC --json $D/eval_b/eval.json
# and the same for $MEL with the female setting into $D/eval_female/

# §4.5: the low male voice by hand (what --samples does for male_low): the Phase 8 female setting mirrored
python scripts/convert_voice.py --in data/synth/probe_non_hexameter/samples/male \
    --out data/synth/probe_non_hexameter/samples/male_low --ids apology_38a \
    --semitones -7 --alpha1 0.8772 --alpha2 0.8772 --tilt 0 --h1 0 --breath 0
# (the released female voice: --semitones 7 --alpha1 1.14 --alpha2 1.14 --tilt 0 --h1 0 --breath 0)

# §4.5: the sphere. Print settings for angles; make the six voices of the 38a passage -> samples/sphere/all_NNN/
python scripts/voice_sphere.py --theta 0 60 120 180 240 300
python scripts/voice_sphere.py --theta 0 60 120 180 240 300 \
    --convert data/synth/probe_non_hexameter/samples/male --ids apology_38a
python scripts/voice_sphere.py --theta 60 120 --toward plane \
    --convert data/synth/probe_non_hexameter/samples/male --ids apology_38a      # plane_060, plane_120
python scripts/voice_sphere.py --random 3 --seed 1                                 # three random directions, settings only

# §4.5: the Phase 8 checks on the six voices, on the 227 Apology units of condition D2
python scripts/voice_sphere.py --theta 0 60 120 180 240 300 \
    --convert data/synth/probe_non_hexameter/wav_D2 --eval data/synth/probe_non_hexameter/D2.csv
# -> samples/sphere/all_NNN/eval.json. (The run reported in §4.5 was the same conversion and the same
#    eval_voice.py call issued from a shell loop into samples/sphere_eval/all_NNN/ before --eval existed.)
```

The settings `voice_sphere.py` printed for the six voices, as passed to
`convert_voice.py`:

| Name | `--semitones` | `--alpha1` | `--alpha2` | `--tilt` | `--h1` | `--breath` |
|---|---|---|---|---|---|---|
| all_000 (female) | 7.00 | 1.1400 | 1.1400 | 0.00 | 0.00 | 0.000 |
| all_060 (a) | −0.33 | 1.1780 | 1.0400 | 2.01 | 1.68 | 0.054 |
| all_120 (b) | −7.33 | 1.0330 | 0.9120 | 2.01 | 1.68 | 0.054 |
| all_180 (low male) | −7.00 | 0.8772 | 0.8772 | 0.00 | 0.00 | 0.000 |
| all_240 | 0.33 | 0.8490 | 0.9620 | −2.01 | 1.68 | 0.054 |
| all_300 | 7.33 | 0.9680 | 1.0960 | −2.01 | 1.68 | 0.054 |
| plane_060 | −5.07 | 1.1570 | 1.1570 | 0.00 | 0.00 | 0.000 |
| plane_120 | −12.07 | 1.0150 | 1.0150 | 0.00 | 0.00 | 0.000 |

Constants that define the sphere, in `scripts/voice_sphere.py`: `UNIT` =
(7 st, ln 1.14, ln 1.14, 3 dB/oct, 2.5 dB, 0.08), `FEMALE` = (1, 1, 1, 0, 0, 0),
radius √3; `TOWARD` directions `plane` = (−2, 1, 1, 0, 0, 0), `split` =
(0, 1, −1, 0, 0, 0), `tilt`, `breath`, `h1` the unit axes, `all` their
normalized sum. In `scripts/probe_non_hexameter.py`: the colon rule
`HARD = ".·;"`, `MIN_SYLL = 10`, `MAX_SYLL = 25`, `MIN_PART = 6`, the `CONJ`,
`PREP` and `POSTPOSITIVE` word lists; pauses `PAUSE` = 0.15 s (no mark), 0.25
(comma), 0.40 (colon, raised dot), 0.55 (question mark), 0.60 (full stop);
`TURN_PAUSE = 0.5`; the dialogue voices are chosen from `VOICE_SETTINGS`
(female, low, a, b, v240, v300: the sphere settings of Appendix C's table);
phrase-position feet `phrase(n)` = `111` + `3`×(n−8) +
`555` + `66` for n ≥ 9; stand-in feet: runs of at most 17, foot
`1 + (6·i) // m`; `MAX_UNIT = 60` syllables for condition D; the dialogue
voices default to Socrates → low male, Meletus → female.

## References consulted outside the repository

Read, not used as data. Audio and data sources are in §8.

- Cleland and Cullhed, "Automatic Annotation of Ancient Greek Vowel Length",
  arXiv 2608.01935 (abstract only): <https://arxiv.org/abs/2608.01935v1>
- `grc-macronizer` (README only): <https://github.com/Urdatorn/grc-macronizer>
- Macronizer for the tragedians' vocabulary: <http://macronizer.gr/>
- Opera Graeca Adnotata v0.2.0 and GLAUx: local READMEs under
  `~/git/classicsviewer/data-sources/`
- LibriVox page for Plato's Dialogues (licence and pronunciation statement only)
  and the front page of ancientgreek.eu
- Search results only, pages not opened:
  <https://commons.wikimedia.org/wiki/Category:Audio_files_in_Ancient_Greek>,
  <https://archive.org/details/grc-whdr-sounds.b>
