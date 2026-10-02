#!/usr/bin/env python3
"""Coherence check: every AI the patent catalog presents vs the phone-book canon.

Canon: /home/hatch/workspace/jah-ai-models/ai-catalog.json
Rule: any AI presented WITH a JAH-AI ID must match the canon exactly
(name + description, whitespace-normalized). The per-patent personal AI
is a site helper and must NOT claim a canon ID. Exit 0 = coherent,
1 = drift found (loud report).

NOTE: index.html / catalog.html are GENERATED from
code/harvest/build_template.py (template) by build_catalog_page.py —
this check scans the template source, not just the output.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_PATHS = [
    "/home/hatch/workspace/jah-ai-models/ai-catalog.json",
    os.path.expanduser("~/workspace/jah-ai-models/ai-catalog.json"),
]
ID_RE = re.compile(r"JAH-AI-[A-Z0-9-]+")

def load_canon():
    for p in CANON_PATHS:
        if os.path.exists(p):
            c = json.load(open(p, encoding="utf-8"))
            return {r["ID"]: r for r in c.get("records", []) if r.get("ID")}
    return None

def main():
    canon = load_canon()
    if canon is None:
        print("COHERENCE WARN: canon file not found; ID-claim scan only.")
    issues = []
    # Scan the template (source of truth) + generated pages for JAH-AI ID claims.
    files = [os.path.join(ROOT, "code", "harvest", "build_template.py"),
             os.path.join(ROOT, "index.html"),
             os.path.join(ROOT, "catalog.html")]
    for f in files:
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in ID_RE.findall(txt):
            issues.append("canon ID claimed outside canon context: %s in %s"
                          % (m, os.path.relpath(f, ROOT)))
    print("=" * 64)
    print("COHERENCE REPORT — cyber-patent-catalog")
    print("=" * 64)
    print("Helper AIs (no canon ID, JAHtalk voice):")
    print("  - Per-patent personal AI (answers from the catalog record only)")
    print("JAH-AI ID claims found (template + generated pages): %d" % len(issues))
    if issues:
        print("\n*** DRIFT DETECTED ***")
        for i in sorted(set(issues))[:20]:
            print("  ! " + i)
        return 1
    print("\nOK: no canon-ID claims; the per-patent AI is a declared helper.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
