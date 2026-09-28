#!/usr/bin/env python3
"""
Harvest cyber-security patent records from Google Patents XHR search.

Covers CPC classes:
  H04L63 - network security architectures / protocols
  H04L9  - secret communication, encryption
  G06F21 - computer / data security
  H04W12 - wireless security
  H04K   - secret communication (legacy)

Output: JSONL, one record per patent:
  publication_number, title, abstract_snippet, assignee, inventor,
  priority_date, filing_date, grant_date, publication_date,
  language, cpc (query class that found it)

Polite crawling: ~1.2s between requests, backoff on 429.
Deduplicates by publication_number across classes.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

CPCS = ["H04L63", "H04L9", "G06F21", "H04W12", "H04K"]
OUT_PATH = "/home/hatch/workspace/your_files/cyber-patent-demos/cyber_patents.jsonl"
STATE_PATH = "/home/hatch/workspace/your_files/cyber-patent-demos/harvest_state.json"
TARGET_RECORDS = 25000
PER_PAGE = 10
MAX_PAGES = 100
REQUEST_DELAY = float(os.environ.get("HARVEST_DELAY", "1.2"))


def qurl(query, page=0):
    inner = urllib.parse.quote(query, safe="") + urllib.parse.quote(f"&page={page}", safe="")
    return f"https://patents.google.com/xhr/query?url=q%3D{inner}&exp="


def fetch_json(url, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < retries - 1:
                wait = 15 * (attempt + 1)
                print(f"  HTTP {e.code}, backing off {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise
    raise RuntimeError("fetch failed after retries")


def clean_snippet(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_records(data, cpc):
    out = []
    for cluster in data["results"].get("cluster", []):
        for item in cluster.get("result", []):
            p = item["patent"]
            out.append({
                "publication_number": p.get("publication_number", ""),
                "title": (p.get("title") or "").strip(),
                "abstract_snippet": clean_snippet(p.get("snippet", "")),
                "assignee": p.get("assignee", ""),
                "inventor": p.get("inventor", ""),
                "priority_date": p.get("priority_date", ""),
                "filing_date": p.get("filing_date", ""),
                "grant_date": p.get("grant_date", ""),
                "publication_date": p.get("publication_date", ""),
                "language": p.get("language", ""),
                "cpc": cpc,
            })
    return out


def window_query(cpc, after, before):
    return f"{cpc}&before=priority:{before}&after=priority:{after}"


def harvest_window(cpc, after, before, seen, out_fh, target=TARGET_RECORDS, depth=0):
    """Harvest one date window; split it if it exceeds what we can page."""
    if len(seen) >= target:
        return
    q = window_query(cpc, after, before)
    data = fetch_json(qurl(q, 0))
    total = data["results"]["total_num_results"]
    time.sleep(REQUEST_DELAY)
    if total == 0:
        return
    max_retrievable = MAX_PAGES * PER_PAGE
    if total > max_retrievable and depth < 5:
        mid = midpoint(after, before)
        if mid and mid != after and mid != before:
            harvest_window(cpc, after, mid, seen, out_fh, target, depth + 1)
            harvest_window(cpc, mid, before, seen, out_fh, target, depth + 1)
            return
    pages = min(MAX_PAGES, (total + PER_PAGE - 1) // PER_PAGE)
    got = 0
    for page in range(pages):
        if len(seen) >= target:
            break
        data = fetch_json(qurl(q, page))
        for rec in extract_records(data, cpc):
            num = rec["publication_number"]
            if num and num not in seen:
                seen.add(num)
                out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                got += 1
        time.sleep(REQUEST_DELAY)
    print(f"  [{cpc} {after}-{before}] total={total} pages={pages} new={got} "
          f"unique={len(seen)}", flush=True)


def midpoint(after, before):
    """Midpoint between YYYYMMDD strings; None if window < 45 days."""
    try:
        from datetime import date, timedelta
        da = date(int(after[:4]), int(after[4:6]), int(after[6:8]))
        db = date(int(before[:4]), int(before[4:6]), int(before[6:8]))
        delta = (db - da).days
        if delta < 45:
            return None
        dm = da + timedelta(days=delta // 2)
        return dm.strftime("%Y%m%d")
    except Exception:
        return None


def main():
    cpcs = CPCS
    out_path = OUT_PATH
    target = TARGET_RECORDS
    if len(sys.argv) > 1:
        cpcs = sys.argv[1].split(",")
    if len(sys.argv) > 2:
        out_path = sys.argv[2]
    if len(sys.argv) > 3:
        target = int(sys.argv[3])
    year_start = int(sys.argv[4]) if len(sys.argv) > 4 else 1976
    year_end = int(sys.argv[5]) if len(sys.argv) > 5 else 2026
    batch_limit = int(sys.argv[6]) if len(sys.argv) > 6 else 0  # max NEW records this run (0 = no limit)
    seen = set()
    # resume support
    try:
        with open(out_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    seen.add(json.loads(line)["publication_number"])
                except Exception:
                    pass
        print(f"Resuming with {len(seen)} existing records", flush=True)
    except FileNotFoundError:
        pass

    # window-progress state (batch/drip mode): where to continue
    state = {}
    if batch_limit:
        try:
            with open(STATE_PATH, encoding="utf-8") as fh:
                state = json.load(fh)
            if state.get("cpcs") != cpcs or state.get("out") != out_path:
                state = {}
        except Exception:
            state = {}
        if state:
            print(f"Continuing from {state['cpcs'][state['cpc_idx']]} year {state['year']}", flush=True)

    def save_state(cpc_idx, year):
        if not batch_limit:
            return
        try:
            with open(STATE_PATH, "w", encoding="utf-8") as fh:
                json.dump({"cpc_idx": cpc_idx, "year": year,
                           "cpcs": cpcs, "out": out_path}, fh)
        except Exception as e:
            print(f"  state save failed: {e}", flush=True)

    mode = "a" if seen else "w"
    if batch_limit:
        target = len(seen) + batch_limit
        print(f"batch mode: {len(seen)} existing, will stop at {target}", flush=True)
    start_ci = state.get("cpc_idx", 0) if state else 0
    start_ci = min(start_ci, len(cpcs) - 1)
    with open(out_path, mode, encoding="utf-8") as out_fh:
        for ci in range(start_ci, len(cpcs)):
            cpc = cpcs[ci]
            year = state.get("year", year_start) if (state and ci == start_ci) else year_start
            print(f"=== {cpc} [{year}-{year_end}] ===", flush=True)
            while year < year_end and len(seen) < target:
                nxt = min(year + 2, year_end)
                after = f"{year}0101"
                before = f"{nxt}0101" if nxt < year_end else f"{year_end}0101"
                try:
                    harvest_window(cpc, after, before, seen, out_fh, target)
                except Exception as e:
                    print(f"  window {after}-{before} failed: {e}; pausing, will retry next run",
                          flush=True)
                    save_state(ci, year)
                    print(f"PAUSED: {len(seen)} unique records -> {out_path}", flush=True)
                    return
                year = nxt
                save_state(ci, year)
            if len(seen) >= target:
                # batch cap hit mid-sweep: keep state so next run resumes here
                save_state(ci, year)
                break
        else:
            # every CPC and year window completed: clear resume state
            if batch_limit:
                try:
                    os.remove(STATE_PATH)
                except OSError:
                    pass
    print(f"DONE: {len(seen)} unique records -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
