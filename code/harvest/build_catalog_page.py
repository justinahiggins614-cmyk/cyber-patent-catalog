#!/usr/bin/env python3
"""Build the Globally Rejustered Patent Catalog site (lazy-load architecture).

Run from the repo root:  python3 code/harvest/build_catalog_page.py
Reads data/patents.jsonl and writes:
  data/patents.search.json.gz  compact search index (titles/numbers/meta + byte offsets)
  data/meta.json               authoritative catalog metadata
  index.html / catalog.html    small app shell (~90KB) — the dataset is NOT inlined

The browser loads the search index (~1-3MB gz) then fetches individual full
records on demand via HTTP Range requests against data/patents.jsonl, using
the byte offsets in the search index. Called by the cyber-patent-drip-harvest
cron step 5 after every harvest sync.
"""
import gzip
import json
import os
import re
import urllib.parse
import hashlib
from datetime import date
from html import unescape as html_unescape

from build_template import build_html, CLASS_NAMES, SECTION_NAMES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "patents.jsonl")
IDMAP = os.path.join(ROOT, "code", "harvest", "jah_patent_ids.json")
SEARCH_DST = os.path.join(ROOT, "data", "patents.search.json.gz")
META_DST = os.path.join(ROOT, "data", "meta.json")
DST = os.path.join(ROOT, "index.html")
DST2 = os.path.join(ROOT, "catalog.html")

NUM_RE = re.compile(r"^([A-Z]{2})(\d+)([A-Z]\d*)?$")


def parse_number(pub):
    """Split a publication number into (country, number, kind) — canonical ID parts."""
    n = (pub or "").upper().replace(" ", "")
    m = NUM_RE.match(n)
    if m:
        return m.group(1), m.group(2), m.group(3) or ""
    digits = re.sub(r"\D", "", n)
    return "", digits or n, ""


def canonical_id(pub):
    c, num, kind = parse_number(pub)
    return (c + num + kind).upper()


def record_type(kind, grant_date):
    k = (kind or "").upper()
    if k.startswith("B") or k.startswith("C") or k.startswith("E"):
        return "Granted patent"
    if k.startswith("A") or k.startswith("U") or k.startswith("P"):
        return "Published patent application"
    if grant_date:
        return "Granted patent"
    return "Patent record (type not specified by source)"


def letter_of(title):
    for ch in title.strip().upper():
        if "A" <= ch <= "Z":
            return ch
        if ch.isalpha() or ch.isdigit():
            return "#"
    return "#"


def main():
    today = date.today().isoformat()
    # --- persistent JAH-PAT id map (permanent catalog identity, never reassigned)
    try:
        idmap = json.load(open(IDMAP, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        idmap = {}
    next_id = max([int(v.split("-")[-1]) for v in idmap.values()] or [0]) + 1

    # --- read source records with byte offsets (for lazy Range fetches)
    raws = []
    with open(SRC, "rb") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.strip():
                continue
            try:
                raws.append((json.loads(line.decode("utf-8")), off, len(line)))
            except Exception as e:
                print("SKIP bad line at offset %d: %s" % (off, e))

    # --- enrich + quarantine + dedupe (quarantine flags; data is never dropped)
    enriched = []
    seen = {}
    dupes = 0
    quarantined = 0
    for d, off, ln in raws:
        g = lambda k: html_unescape(str(d.get(k, "") or ""))
        pub = g("publication_number")
        title = g("title")
        country, number, kind = parse_number(pub)
        canon = canonical_id(pub)
        rtype = record_type(kind, g("grant_date"))
        flags = []
        if not title:
            flags.append("missing-title")
        if not canon or not re.search(r"\d", canon):
            flags.append("malformed-number")
        pd = g("publication_date")
        if pd and pd > "2030-01-01":
            flags.append("future-date")
        if canon in seen:
            flags.append("possible-duplicate")
            dupes += 1
        else:
            seen[canon] = True
        if flags:
            quarantined += 1
        if canon not in idmap:
            idmap[canon] = "JAH-PAT-%06d" % next_id
            next_id += 1
        enriched.append({
            "jah": idmap[canon],
            "pub": pub, "title": title, "abstract": g("abstract_snippet"),
            "assignee": g("assignee"), "inventor": g("inventor"),
            "priority_date": g("priority_date"), "filing_date": g("filing_date"),
            "grant_date": g("grant_date"), "publication_date": g("publication_date"),
            "language": g("language") or "en", "cpc": g("cpc"),
            "country": country, "number": number, "kind": kind,
            "canon": canon, "family": (country + number).upper(),
            "rtype": rtype, "flags": flags,
            "off": off, "len": ln,
        })

    with open(IDMAP, "w", encoding="utf-8") as f:
        json.dump(idmap, f, indent=1, sort_keys=True)

    # --- compact search index (abstract capped at 400 chars; full record lazy-fetched)
    rows = []
    for e in enriched:
        rows.append([
            e["pub"], e["title"], e["abstract"][:400], e["inventor"], e["assignee"],
            e["cpc"], e["publication_date"], e["off"], e["len"], e["jah"],
            e["rtype"], e["family"], e["country"], e["kind"], letter_of(e["title"]),
            1 if e["flags"] else 0,
        ])
    rows.sort(key=lambda r: r[1].lower())
    with gzip.open(SEARCH_DST, "wt", encoding="utf-8") as gz:
        json.dump(rows, gz, separators=(",", ":"), ensure_ascii=False)
    print("search index: %d rows -> %s (%.1f MB)" % (
        len(rows), SEARCH_DST, os.path.getsize(SEARCH_DST) / 1048576))

    # --- authoritative metadata
    h = hashlib.sha256()
    for e in enriched:
        h.update((e["canon"] + "|" + e["title"]).encode("utf-8"))
    sections = {}
    for e in enriched:
        s = (e["cpc"] or "?")[:1]
        sections[s] = sections.get(s, 0) + 1
    meta = {
        "catalog_version": "GRPC-" + today.replace("-", ""),
        "record_count": len(enriched),
        "last_updated": today,
        "source_snapshot": "Google Patents harvest, all CPC A-H, 1976-2026",
        "catalog_hash": "sha256:" + h.hexdigest(),
        "sections": sections,
        "dupes_flagged": dupes,
        "quarantined": quarantined,
    }
    with open(META_DST, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print("meta:", json.dumps(meta))

    html = build_html(meta)
    for dst in (DST, DST2):
        with open(dst, "w", encoding="utf-8") as f:
            f.write(html)
    print("wrote %s + catalog.html (%d KB each)" % (DST, os.path.getsize(DST) // 1024))

    # The wiki's ?page=PAT: articles fetch patent records by byte range via
    # data/patents.idx.json.gz — rebuild it AFTER patents.jsonl was rewritten,
    # or the offsets go stale. (The drip cron also runs build_patent_index.py,
    # but it runs BEFORE this builder; this keeps the pair consistent always.)
    import build_patent_index
    build_patent_index.main()

    build_sitemaps(enriched)
    refresh_api(len(enriched), today)


def build_sitemaps(enriched):
    SITE = "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/"
    CHUNK = 40000
    import glob as _glob
    files = []
    pubs = [e["pub"] for e in enriched]
    for n, start in enumerate(range(0, len(pubs), CHUNK), 1):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in pubs[start:start + CHUNK]:
            lines.append('  <url><loc>%s?patent=%s</loc><changefreq>monthly</changefreq></url>' %
                         (SITE, urllib.parse.quote(p, safe="")))
        lines.append('</urlset>')
        fname = "sitemap-records-%d.xml" % n
        with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        files.append(fname)
    for stale in _glob.glob(os.path.join(ROOT, "sitemap-records-*.xml")):
        if os.path.basename(stale) not in files:
            os.remove(stale)
    ilines = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
              '  <sitemap><loc>%ssitemap.xml</loc></sitemap>' % SITE]
    for fname in files:
        ilines.append('  <sitemap><loc>%s%s</loc></sitemap>' % (SITE, fname))
    ilines.append('</sitemapindex>')
    with open(os.path.join(ROOT, "sitemap-index.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(ilines) + "\n")
    print("sitemaps: %d file(s), %d urls" % (len(files), len(pubs)))


def refresh_api(count, today):
    api_path = os.path.join(ROOT, "api.json")
    try:
        txt = open(api_path, encoding="utf-8").read()
        txt = re.sub(r'"records_approx":\s*\d+', '"records_approx": %d' % count, txt)
        txt = re.sub(r'"records_as_of":\s*"[^"]*"', '"records_as_of": "%s"' % today, txt)
        open(api_path, "w", encoding="utf-8").write(txt)
        print("refreshed api.json counts")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
