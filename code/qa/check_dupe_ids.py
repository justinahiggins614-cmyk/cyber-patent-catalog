#!/usr/bin/env python3
"""QA: duplicate publication-number detection across the dataset.

Recomputes canonical IDs from data/patents.jsonl the same way the builder
does and reports any publication number appearing more than once.
Also cross-checks the builder's meta.json dupes_flagged tally.
Exit 0 = no unexpected dupes, 1 = findings.
"""
import json
import os
import re
import sys
from html import unescape as html_unescape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUM_RE = re.compile(r"^([A-Z]{2})(\d+)([A-Z]\d*)?$")


def canonical_id(pub):
    n = (pub or "").upper().replace(" ", "")
    m = NUM_RE.match(n)
    if m:
        return (m.group(1) + m.group(2) + (m.group(3) or "")).upper()
    digits = re.sub(r"\D", "", n)
    return (digits or n)


def main():
    seen = {}
    dupes = 0
    with open(os.path.join(ROOT, "data", "patents.jsonl"), encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            if not line.strip():
                continue
            d = json.loads(line)
            canon = canonical_id(html_unescape(str(d.get("publication_number", "") or "")))
            if canon in seen:
                dupes += 1
                if dupes <= 10:
                    print("DUPE %s (lines %d and %d)" % (canon, seen[canon], ln))
            else:
                seen[canon] = ln
    meta = json.load(open(os.path.join(ROOT, "data", "meta.json"), encoding="utf-8"))
    flagged = meta.get("dupes_flagged", 0)
    ok = dupes == flagged
    print(("PASS " if ok else "FAIL ") + "dupe_tally: recomputed=%d meta=%d" % (dupes, flagged))
    print("dupes: %d finding(s)" % (0 if ok else 1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
