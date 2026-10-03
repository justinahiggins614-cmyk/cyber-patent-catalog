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
from datetime import date, datetime, timedelta
from html import unescape as html_unescape

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:
    ET = None

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


def harvest_status(meta):
    """Per-section harvest status + last/next harvest times, all derived live.

    Sections with records -> Indexed. The section holding the class the
    30-min harvester is currently on -> Processing note. Sections at 0 ->
    Queued with their queue position (a bare 0 never reads as "no patents
    exist"). Times come from data/patents.jsonl's mtime (written by the
    harvest sync just before this builder runs); next harvest = +30 min.
    """
    harv = {"sections": {}, "harvest_line": ""}
    try:
        last_ts = os.path.getmtime(SRC)
    except OSError:
        last_ts = None
    state = {}
    try:
        with open(os.path.expanduser(
                "~/workspace/your_files/cyber-patent-demos/harvest_state.json"),
                encoding="utf-8") as f:
            state = json.load(f)
    except (FileNotFoundError, ValueError):
        pass
    cpcs = state.get("cpcs", [])
    idx = state.get("cpc_idx")
    cur_class = cpcs[idx] if cpcs and idx is not None and 0 <= idx < len(cpcs) else ""
    cur_letter = cur_class[:1]
    total = len(cpcs)
    pos = (idx + 1) if idx is not None else 0
    first_of = {}
    for i, c in enumerate(cpcs):
        first_of.setdefault(c[:1], i + 1)

    sections = meta.get("sections", {})
    for s in "ABCDEFGH":
        n = sections.get(s, 0)
        if n > 0:
            if s == cur_letter and cur_class:
                stat = ("Indexed · harvest in progress (%s · class %d of %d)"
                        % (cur_class, pos, total))
            else:
                stat = "Indexed"
        elif s == cur_letter and cur_class:
            stat = "Processing (%s · class %d of %d)" % (cur_class, pos, total)
        else:
            qn = first_of.get(s)
            stat = ("Queued · class #%d of %d up next" % (qn, total)) if qn else "Queued"
        harv["sections"][s] = {"stat": stat}

    def fmt_et(ts):
        dt = datetime.fromtimestamp(ts, tz=ET) if ET else datetime.fromtimestamp(ts).astimezone()
        return dt.strftime("%b %-d, %Y, %-I:%M %p ET").replace(" 0", " ").replace("AM", "AM").replace("PM", "PM")

    count = meta.get("record_count", 0)
    if last_ts:
        last_s = fmt_et(last_ts)
        next_s = fmt_et(last_ts + 30 * 60)
        line = ("Patent records currently indexed: <b>%s</b>"
                '<span class="sep">·</span>Harvesting: <b>ongoing</b>'
                '<span class="sep">·</span>Last harvest: <b>%s</b>'
                '<span class="sep">·</span>Next harvest: <b>%s</b> (every 30 min)'
                % (f"{count:,}", last_s, next_s))
    else:
        line = ("Patent records currently indexed: <b>%s</b>"
                '<span class="sep">·</span>Harvesting: <b>ongoing</b>' % f"{count:,}")
    harv["harvest_line"] = line
    return harv


def main():
    today = date.today().isoformat()
    # --- persistent JAH-PAT id map (permanent catalog identity, never reassigned)
    try:
        idmap = json.load(open(IDMAP, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        idmap = {}
    next_id = max([int(v.split("-")[-1]) for v in idmap.values()] or [0]) + 1
    start_next = next_id  # FIX-02 (2026-10-02): JAH-PAT numbers at/after this are this run's new records

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
        rehash = hashlib.sha256((canon + "|" + title).encode("utf-8")).hexdigest()[:12]
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
            "rtype": rtype, "flags": flags, "rehash": rehash,
            "off": off, "len": ln,
        })

    with open(IDMAP, "w", encoding="utf-8") as f:
        json.dump(idmap, f, indent=1, sort_keys=True)

    # FIX-02 (2026-10-02): records minted this run, for the incremental registry feed.
    new_recs = [e for e in enriched if int(e["jah"].rsplit("-", 1)[-1]) >= start_next]

    # --- compact search index (abstract capped at 400 chars; full record lazy-fetched)
    rows = []
    for e in enriched:
        rows.append([
            e["pub"], e["title"], e["abstract"][:400], e["inventor"], e["assignee"],
            e["cpc"], e["publication_date"], e["off"], e["len"], e["jah"],
            e["rtype"], e["family"], e["country"], e["kind"], letter_of(e["title"]),
            1 if e["flags"] else 0, e["rehash"],
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
    classes_covered = set()
    for e in enriched:
        s = (e["cpc"] or "?")[:1]
        sections[s] = sections.get(s, 0) + 1
        if e["cpc"]:
            classes_covered.add(e["cpc"])
    classes_covered = sorted(classes_covered)
    meta = {
        "catalog_version": "GRPC-" + today.replace("-", ""),
        "record_count": len(enriched),
        "last_updated": today,
        "source_snapshot": "Google Patents harvest, all CPC A-H, 1976-2026",
        "catalog_hash": "sha256:" + h.hexdigest(),
        "sections": sections,
        "areas_covered": len(classes_covered),
        "classes_covered": classes_covered,
        "dupes_flagged": dupes,
        "quarantined": quarantined,
    }
    with open(META_DST, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print("meta:", json.dumps(meta))

    html = build_html(meta, harvest_status(meta), enriched)
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

    build_sitemaps(enriched, set(e["pub"] for e in new_recs))
    build_csv(enriched)
    write_registry_feed(new_recs, meta, today)
    refresh_api(len(enriched), today)


def build_csv(enriched):
    """Full machine-readable export: one row per patent record."""
    import csv
    path = os.path.join(ROOT, "data", "patents.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["publication_number", "title", "publication_date", "filing_date",
                    "assignee", "inventor", "cpc_classification", "record_type",
                    "catalog_id", "record_hash", "country", "kind_code",
                    "catalog_url"])
        for e in enriched:
            url = ("https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/"
                   "?patent=" + urllib.parse.quote(e["pub"], safe=""))
            w.writerow([e["pub"], e["title"], e["publication_date"], e["filing_date"],
                        e["assignee"], e["inventor"], e["cpc"], e["rtype"],
                        e["jah"], e["rehash"], e["country"], e["kind"], url])
    print("csv: %d rows -> %s (%.1f MB)" % (
        len(enriched), path, os.path.getsize(path) / 1048576))


def build_sitemaps(enriched, new_pubs=None):
    """Rebuild per-record sitemaps. FIX-02 (2026-10-02): records harvested in
    the newest batch carry <lastmod> so crawlers see what's fresh."""
    SITE = "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/"
    CHUNK = 40000
    today = date.today().isoformat()
    new_pubs = new_pubs or set()
    import glob as _glob
    files = []
    pubs = [e["pub"] for e in enriched]
    for n, start in enumerate(range(0, len(pubs), CHUNK), 1):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in pubs[start:start + CHUNK]:
            tag = '  <url><loc>%s?patent=%s</loc>' % (
                SITE, urllib.parse.quote(p, safe=""))
            if p in new_pubs:
                tag += '<lastmod>%s</lastmod>' % today
            tag += '<changefreq>monthly</changefreq></url>'
            lines.append(tag)
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


def write_registry_feed(new_recs, meta, today):
    """FIX-02 (2026-10-02): dedicated incremental patent registry feed.
    data/index-batches.json is the persistent append-only batch log (last 24
    batches kept); data/patents-index.json is the public feed with batch
    summaries + the 200 most recent additions."""
    SITE = "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/"
    batch_path = os.path.join(ROOT, "data", "index-batches.json")
    try:
        batches = json.load(open(batch_path, encoding="utf-8"))
        if not isinstance(batches, list):
            batches = []
    except (FileNotFoundError, ValueError):
        batches = []
    batch = {
        "catalog_version": meta["catalog_version"],
        "date": today,
        "added": len(new_recs),
        "records": [
            {"pub": e["pub"], "title": e["title"],
             "publication_date": e["publication_date"], "cpc": e["cpc"],
             "catalog_id": e["jah"],
             "url": SITE + "?patent=" + urllib.parse.quote(e["pub"], safe="")}
            for e in new_recs[:500]
        ],
    }
    existing = None
    for b in batches:
        if b.get("catalog_version") == batch["catalog_version"]:
            existing = b
            break
    if existing is None:
        batches.append(batch)
    else:
        # Same-day rebuild (the 30-min cron): merge the new records in so the
        # batch stays additive instead of being skipped or duplicated.
        have = set(r["pub"] for r in existing["records"])
        for rec in batch["records"]:
            if rec["pub"] not in have:
                existing["records"].append(rec)
                have.add(rec["pub"])
        existing["records"] = existing["records"][:1000]
        existing["added"] = len(existing["records"])
        existing["date"] = batch["date"]
    batches = batches[-24:]
    with open(batch_path, "w", encoding="utf-8") as f:
        json.dump(batches, f, ensure_ascii=False)
    recent = []
    for b in reversed(batches):
        for rec in b["records"]:
            recent.append(rec)
            if len(recent) >= 200:
                break
        if len(recent) >= 200:
            break
    feed = {
        "title": "Globally Rejustered Patent Catalog — registry feed",
        "description": "Incremental registry of newly harvested patent batches. "
                       "Independent catalog of public records; not affiliated "
                       "with the USPTO or any government agency.",
        "home_page_url": SITE,
        "feed_url": SITE + "data/patents-index.json",
        "catalog_version": meta["catalog_version"],
        "record_count": meta["record_count"],
        "updated": today,
        "batches": [{"catalog_version": b["catalog_version"], "date": b["date"],
                     "added": b["added"]} for b in batches],
        "recent_additions": recent,
    }
    with open(os.path.join(ROOT, "data", "patents-index.json"), "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False)
    print("registry feed: %d batches, %d recent additions" % (len(batches), len(recent)))


def refresh_api(count, today):
    api_path = os.path.join(ROOT, "api.json")
    try:
        txt = open(api_path, encoding="utf-8").read()
        txt = re.sub(r'"records_approx":\s*\d+', '"records_approx": %d' % count, txt)
        txt = re.sub(r'"records_as_of":\s*"[^"]*"', '"records_as_of": "%s"' % today, txt)
        # FIX-02 (2026-10-02): advertise the incremental registry feed to bots.
        if '"data/patents-index.json"' not in txt:
            txt = txt.replace(
                '    {\n      "path": "data/patents.jsonl",',
                '    {\n      "path": "data/patents-index.json",\n'
                '      "format": "json",\n'
                '      "desc": "Incremental registry feed: newly harvested batches '
                'and the 200 most recent additions."\n'
                '    },\n'
                '    {\n      "path": "data/patents.jsonl",')
        open(api_path, "w", encoding="utf-8").write(txt)
        print("refreshed api.json counts")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
