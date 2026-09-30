#!/usr/bin/env python3
"""Rebuild data/patents.idx.json.gz — the 6-column byte-offset index over
data/patents.jsonl used by the JAH Wiki for ?page=PAT:<pub> byte-range fetches.

Row: [publication_number, title, cpc, assignee, byte_offset, byte_length]
(byte_offset/length measured in bytes of the UTF-8 encoded line incl. newline)

Run after every harvest sync that changes patents.jsonl, BEFORE committing,
or the wiki will fetch wrong records (stale offsets). Called by the
cyber-patent-drip-harvest cron step 5.
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
SRC = os.path.join(DATA, "patents.jsonl")
DST = os.path.join(DATA, "patents.idx.json.gz")


def main():
    rows = []
    with open(SRC, "rb") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.strip():
                continue
            try:
                r = json.loads(line.decode("utf-8"))
            except Exception as e:
                print("SKIP bad line at offset %d: %s" % (off, e), file=sys.stderr)
                continue
            rows.append([
                r.get("publication_number", ""),
                r.get("title", ""),
                r.get("cpc", ""),
                r.get("assignee", ""),
                off,
                len(line),
            ])
    tmp = DST + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as gz:
        json.dump(rows, gz, separators=(",", ":"))
    os.replace(tmp, DST)
    print("wrote %d rows -> %s" % (len(rows), DST))


if __name__ == "__main__":
    main()
