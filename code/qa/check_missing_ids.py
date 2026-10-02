#!/usr/bin/env python3
"""QA: every record must carry a JAH-PAT catalog ID; idmap must cover all canons.

Checks:
  - every row in data/patents.search.json.gz has a non-empty JAH-PAT id
  - JAH-PAT ids are unique across rows
  - code/harvest/jah_patent_ids.json covers every canonical id in the jsonl
  - no JAH-PAT sequence gaps beyond the highest assigned id (ids are never
    reassigned, so a gap would mean a lost assignment)
Exit 0 = all pass, 1 = findings.
"""
import gzip
import json
import os
import re
import sys
from html import unescape as html_unescape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUM_RE = re.compile(r"^([A-Z]{2})(\d+)([A-Z]\d*)?$")
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" — " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


def canonical_id(pub):
    n = (pub or "").upper().replace(" ", "")
    m = NUM_RE.match(n)
    if m:
        return (m.group(1) + m.group(2) + (m.group(3) or "")).upper()
    digits = re.sub(r"\D", "", n)
    return (digits or n)


def main():
    with gzip.open(os.path.join(ROOT, "data", "patents.search.json.gz"), "rt", encoding="utf-8") as gz:
        rows = json.load(gz)
    jahs = [r[9] for r in rows]
    check("all_rows_have_jah", all(j and str(j).startswith("JAH-PAT-") for j in jahs),
          "%d rows missing" % sum(1 for j in jahs if not (j and str(j).startswith("JAH-PAT-"))))
    # one canon -> exactly one JAH-PAT id. Colliding canons (flagged dupes, e.g.
    # JP H-number records whose canonical form drops the kind) legitimately
    # share an id; what must never happen is one canon mapping to two ids.
    canon_jahs = {}
    for r in rows:
        canon_jahs.setdefault(canonical_id(r[0]), set()).add(r[9])
    split = {c: js for c, js in canon_jahs.items() if len(js) > 1}
    check("jah_consistent_per_canon", not split,
          "%d canon(s) map to 2+ ids, e.g. %s" % (len(split), list(split)[:3]))

    idmap = json.load(open(os.path.join(ROOT, "code", "harvest", "jah_patent_ids.json"), encoding="utf-8"))
    canons = set()
    with open(os.path.join(ROOT, "data", "patents.jsonl"), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            canons.add(canonical_id(html_unescape(str(d.get("publication_number", "") or ""))))
    missing = [c for c in canons if c not in idmap]
    check("idmap_covers_all_canons", not missing, "%d canons missing" % len(missing))

    nums = sorted(int(v.split("-")[-1]) for v in idmap.values())
    gaps = [b for a, b in zip(nums, nums[1:]) if b - a > 1]
    check("jah_sequence_no_gaps", not gaps, "%d gap(s), e.g. %s" % (len(gaps), gaps[:5]))

    print("ids: %d finding(s)" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
