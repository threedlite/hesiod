# Scanner validation against Chamberlain (24-fold by book)

Lines: 15632. Lexicon built from the other 23 books for each book.

| Outcome | Lines | Share |
|---|---|---|
| match | 15384 | 98.41 % |
| mismatch | 43 | 0.28 % |
| syllable_count_differs | 205 | 1.31 % |
| no_scan | 0 | 0.00 % |

Among lines with the same syllable count: 99.72 % identical.
Matches that still had more than one equally cheap scansion: 1 (0.0 % of matches).
Unresolved α/ι/υ nuclei remaining after lexicon and accent rules: 9591 over 15632 lines.

## Sample mismatches

| id | mine | his | flags | text |
|---|---|---|---|---|
| b2_l537 | LSSLLSLSSLSSLLSLL | LSSLSSLSSLSSLSSLL | unmetrical | Χαλκίδα τ’ Εἰρέτριάν τε πολυστάφυλόν θ’ Ἱστίαιαν |
| b10_l402 | LLLSSLLLSSLSSLL | LLLLLSSLSSLSSLL | metrical_lengthening | ἵππων Αἰακίδαο δαίφρονος· οἳ δ’ ἀλεγεινοὶ |
| b11_l532 | LLLSSLLLLLSSLL | LSSLLLLLLLSSLL | lexicon_overridden | μάστιγι λιγυρῇ· τοὶ δὲ πληγῆς ἀΐοντες |
| b14_l289 | LLLSSLSSLSSLSSLL | LSSLLLSSLSSLSSLL | override | ὄρνιθι λιγυρῇ ἐναλίγκιος, ἥν τ’ ἐν ὄρεσσι |
| b15_l171 | LSSLLLLLSSLSSLL | LLLSSLLLSSLSSLL | correption;metrical_lengthening | ψυχρὴ ὑπὸ ῥιπῆς αἰθρηγενέος Βορέαο, |
| b16_l20 | LSSLSSLSSLLLSSLL | SSSLSSLSSLLLSSLL |  | τὸν δὲ βαρὺ στενάχων προσέφης Πατρόκλεες ἱππεῦ· |
| b16_l48 | LSSLLLSSLSSLSSLL | LSSLSLSSLSSLSSLL |  | τὸν δὲ μέγ’ ὀχθήσας προσέφη πόδας ὠκὺς Ἀχιλλεύς· |
| b16_l49 | LLLSSLLLSSLSSLL | LLLSSSLLSSLSSLL |  | ὤ μοι διογενὲς Πατρόκλεες οἷον ἔειπες· |
| b16_l101 | LLLLLSSLLLSSLL | LLLSLSSLLLSSLL | lexicon_overridden | ὣς οἳ μὲν τοιαῦτα πρὸς ἀλλήλους ἀγόρευον, |
| b16_l210 | LLLLLSSLLLSSLL | LLLLSSSLLLSSLL |  | ὣς εἰπὼν ὄτρυνε μένος καὶ θυμὸν ἑκάστου. |
| b16_l233 | LSSLLLSSLSSLSSLL | LSSLSLSSLSSLSSLL |  | Ζεῦ ἄνα Δωδωναῖε Πελασγικὲ τηλόθι ναίων |
| b16_l269 | LSSLSSLLLSSLSSLL | LSSSSSLLLSSLSSLL | synizesis;metrical_lengthening;synizesis | Μυρμιδόνες ἕταροι Πηληϊάδεω Ἀχιλῆος |
| b16_l275 | LLLLLSSLLLSSLL | LLLLSSSLLLSSLL |  | ὣς εἰπὼν ὄτρυνε μένος καὶ θυμὸν ἑκάστου, |
| b16_l326 | LLLLLSSLLLSSLL | LLLSLSSLLLSSLL |  | ὣς τὼ μὲν δοιοῖσι κασιγνήτοισι δαμέντε |
| b16_l352 | LSSLLLSSLSSLSSLL | LSSLLSSSLSSLSSLL |  | ὡς δὲ λύκοι ἄρνεσσιν ἐπέχραον ἢ ἐρίφοισι |
| b16_l372 | LLLSSLSSLSSLSSLL | LSLSSLSSLSSLSSLL |  | Πάτροκλος δ’ ἕπετο σφεδανὸν Δαναοῖσι κελεύων |
| b16_l433 | LSSLSSLLLSSLSSLL | LSSSSSLLLSSLSSLL | correption | ὤ μοι ἐγών, ὅ τέ μοι Σαρπηδόνα φίλτατον ἀνδρῶν |
| b16_l439 | LLLSSLSSLLLSSLL | LLSSSLSSLLLSSLL |  | τὸν δ’ ἠμείβετ’ ἔπειτα βοῶπις πότνια Ἥρη· |
| b16_l538 | LLLLLSSLSSLSSLL | LLSLLSSLSSLSSLL |  | Ἕκτορ νῦν δὴ πάγχυ λελασμένος εἰς ἐπικούρων, |
| b16_l557 | LLLSSLSSLSSLSSLL | LSLSSLSSLSSLSSLL | correption | οἷοί περ πάρος ἦτε μετ’ ἀνδράσιν ἢ καὶ ἀρείους. |

## Sample syllable-count differences

| id | mine | his | flags | text |
|---|---|---|---|---|
| b1_l171 | LSSLSSLSSLLLSSLL | LLLSSLSSLLLSSLL |  | ἐνθάδ’ ἄτιμος ἐὼν ἄφενος καὶ πλοῦτον ἀφύξειν. |
| b1_l176 | LLLSSLSSLSSLSSLL | LLLSSLSSLSSLLLL | correption;lexicon_overridden | ἔχθιστος δέ μοί ἐσσι διοτρεφέων βασιλήων· |
| b1_l276 | LSSLLLSSLSSLSSLL | LLLLLSSLSSLSSLL | lexicon_overridden | ἀλλ’ ἔα ὥς οἱ πρῶτα δόσαν γέρας υἷες Ἀχαιῶν· |
| b1_l489 | LSSLLLSSLSSLSSLL | LSSLLLLLSSLSSLL | correption | διογενὴς Πηλῆος υἱὸς πόδας ὠκὺς Ἀχιλλεύς· |
| b2_l98 | LSSLLLSSLSSLSSLL | LSSLLLSSLSSLLLL | lexicon_overridden | σχοίατ’, ἀκούσειαν δὲ διοτρεφέων βασιλήων. |
| b2_l125 | LLLLLSSLSSLSSLL | LLLLLSSLSSLLLL | correption | Τρῶας μὲν λέξασθαι ἐφέστιοι ὅσσοι ἔασιν, |
| b2_l196 | LLLSSLSSLSSLSSLL | LLLSSLSSLSSLLLL | lexicon_overridden;metrical_lengthening | θυμὸς δὲ μέγας ἐστὶ διοτρεφέων βασιλήων, |
| b2_l272 | LSSLLLSSLLLSSLL | LSSLLLSSLLLLLL | correption | ὢ πόποι ἦ δὴ μυρί’ Ὀδυσσεὺς ἐσθλὰ ἔοργε |
| b2_l415 | LSSLLLSSLSSLSSLL | LSSLLLSSLLLSSLL | correption | αἰθαλόεν, πρῆσαι δὲ πυρὸς δηίοιο θύρετρα, |
| b2_l544 | LLLLLSSLLLLLL | LLLLLLLLLLLL | correption | θώρηκας ῥήξειν δηίων ἀμφὶ στήθεσσι· |
| b2_l576 | LSSLLLLLLLSSLL | LSSLLLLLLLLLL |  | τῶν ἑκατὸν νηῶν ἦρχε κρείων Ἀγαμέμνων |
| b2_l662 | LSSLSSLSSLLLSSLL | LLLSSLSSLLLSSLL |  | αὐτίκα πατρὸς ἑοῖο φίλον μήτρωα κατέκτα |
| b2_l704 | LSSLLLSSLLLSSLL | LLLLLSSLLLSSLL | lexicon_overridden | ἀλλά σφεας κόσμησε Ποδάρκης ὄζος Ἄρηος |
| b2_l811 | LSSLSSLSSLSLLSSLL | LSSLSSLSSLLLSSLL | unmetrical | Ἔστι δέ τις προπάροιθε πόληος αἰπεῖα κολώνη |
| b3_l57 | LSSLSSLSSLSSLSSLL | LSSLSSLSSLSSLLLL |  | λάϊνον ἕσσο χιτῶνα κακῶν ἕνεχ’ ὅσσα ἔοργας. |

## No scan

| id | flags | text |
|---|---|---|
