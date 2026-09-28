#!/usr/bin/env python3
"""
Merge harvested JSONL files, dedupe by publication_number,
and produce:
  - cyber_patents_merged.jsonl : full records, deduped
  - catalog_data.json           : compact records for web embedding
"""
import json
import glob
import os

SRC_DIR = "/home/hatch/workspace/your_files/cyber-patent-demos"
MERGED = os.path.join(SRC_DIR, "cyber_patents_merged.jsonl")
COMPACT = os.path.join(SRC_DIR, "catalog_data.json")

CPC_LABELS = {
    "H04L63": "Network Security",
    "H04L9": "Cryptography",
    "G06F21": "Computer Security",
    "H04W12": "Wireless Security",
    "H04K": "Secret Communication",
}


def main():
    seen = {}
    files = sorted(glob.glob(os.path.join(SRC_DIR, "cyber_patents*.jsonl")))
    files = [f for f in files if "merged" not in f]
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                num = rec.get("publication_number", "")
                if not num or num in seen:
                    continue
                seen[num] = rec
    print(f"merged {len(seen)} unique records from {len(files)} files")

    with open(MERGED, "w", encoding="utf-8") as fh:
        for num in sorted(seen):
            fh.write(json.dumps(seen[num], ensure_ascii=False) + "\n")

    compact = []
    for num in sorted(seen):
        r = seen[num]
        year = (r.get("priority_date") or r.get("filing_date") or "")[:4]
        snippet = r.get("abstract_snippet", "")[:170]
        compact.append({
            "n": num,
            "t": r.get("title", "")[:120],
            "a": r.get("assignee", "")[:60],
            "y": year,
            "c": r.get("cpc", ""),
            "s": snippet,
        })
    with open(COMPACT, "w", encoding="utf-8") as fh:
        json.dump(compact, fh, ensure_ascii=False, separators=(",", ":"))
    size_mb = os.path.getsize(COMPACT) / 1e6
    print(f"compact: {len(compact)} records, {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
