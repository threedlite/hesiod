"""Minimal Praat TextGrid (long format) reader: returns {tier_name: [(start, end, label), ...]}."""
import re
def read_textgrid(path):
    txt = open(path, encoding="utf8").read()
    tiers = {}
    for m in re.finditer(r'item \[\d+\]:\s*class = "IntervalTier"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', txt, re.S):
        name, body = m.group(1), m.group(2)
        ivs = re.findall(r'xmin = ([\d.eE+-]+)\s*xmax = ([\d.eE+-]+)\s*text = "([^"]*)"', body)
        tiers[name] = [(float(a), float(b), t) for a, b, t in ivs]
    return tiers
