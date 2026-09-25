#!/bin/bash
# Build order for the vowel-length lexicons (Track H). Run from the repo root.
#   1. Iliad phones from Chamberlain's spans with no lexicon (only meter-certain lengths)
#   2. word-form lexicon from those certain lengths
#   3. lemma/ending extension from the treebanks
#   4. final phone tables for the Iliad (spans + lexicon) and Hesiod (scanner + lexicon)
set -euo pipefail
cd "$(dirname "$0")/.."
python3 greek2ipa/from_spans.py --no-lexicon | head -1
python3 prosody/lexicon.py
python3 prosody/lemma_lexicon.py
python3 greek2ipa/from_spans.py | sed -n 2p
python3 scripts/scan_hesiod.py 2>&1 | sed -n '1p;4,6p'
python3 scripts/render_hesiod_phones.py | sed -n 2,5p
