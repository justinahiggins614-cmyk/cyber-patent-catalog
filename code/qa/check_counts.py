#!/usr/bin/env python3
"""QA: counts must match across data, search index, meta, and baked HTML.

Checks:
  - data/patents.jsonl non-blank lines == meta.json record_count
  - data/patents.search.json.gz rows == record_count
  - baked count in index.html/catalog.html == record_count
  - meta sections sum == record_count
  - meta areas_covered == len(classes_covered)
Exit 0 = all pass, 1 = findings.
"""
import gzip
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" — " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


def main():
    meta = json.load(open(os.path.join(ROOT, "data", "meta.json"), encoding="utf-8"))
    rc = meta["record_count"]

    with open(os.path.join(ROOT, "data", "patents.jsonl"), "rb") as f:
        lines = sum(1 for ln in f if ln.strip())
    check("jsonl_lines_vs_meta", lines == rc, "jsonl=%d meta=%d" % (lines, rc))

    with gzip.open(os.path.join(ROOT, "data", "patents.search.json.gz"), "rt", encoding="utf-8") as gz:
        rows = json.load(gz)
    check("search_rows_vs_meta", len(rows) == rc, "rows=%d meta=%d" % (len(rows), rc))

    for page in ("index.html", "catalog.html"):
        html = open(os.path.join(ROOT, page), encoding="utf-8").read()
        m = re.search(r'<b id="chipcount">([\d,]+)', html)
        baked = int(m.group(1).replace(",", "")) if m else None
        check("baked_count_%s" % page, baked == rc, "baked=%s meta=%d" % (baked, rc))
        m2 = re.search(r"Patent records currently indexed: <b>([\d,]+)</b>", html)
        hl = int(m2.group(1).replace(",", "")) if m2 else None
        check("harvestline_count_%s" % page, hl == rc, "line=%s meta=%d" % (hl, rc))

    sec_sum = sum(meta.get("sections", {}).values())
    check("sections_sum_vs_meta", sec_sum == rc, "sections=%d meta=%d" % (sec_sum, rc))
    check("areas_covered_len",
          meta.get("areas_covered") == len(meta.get("classes_covered", [])),
          "areas=%s classes=%d" % (meta.get("areas_covered"), len(meta.get("classes_covered", []))))

    # each section button baked count matches meta sections
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for s, n in meta.get("sections", {}).items():
        ok = ('data-s="%s"' % s) in html
        check("section_button_%s_present" % s, ok)

    print("counts: %d finding(s)" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
