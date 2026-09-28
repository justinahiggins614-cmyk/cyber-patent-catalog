#!/usr/bin/env python3
"""Build a searchable static catalog page (index.html) from data/patents.jsonl.

Run from the repo root:  python3 code/harvest/build_catalog_page.py
Reads data/patents.jsonl, writes index.html with the data embedded.
"""
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "patents.jsonl")
DST = os.path.join(ROOT, "index.html")
DST2 = os.path.join(ROOT, "catalog.html")

CLASS_NAMES = {
    "H04L63": "Network security",
    "H04L9": "Cryptography",
    "G06F21": "System security",
    "H04W12": "Wireless security",
    "H04K": "Secret communication",
}

records = []
with open(SRC, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        records.append([
            d.get("publication_number", ""),
            d.get("title", ""),
            d.get("abstract_snippet", ""),
            d.get("assignee", ""),
            d.get("inventor", ""),
            d.get("filing_date", ""),
            d.get("grant_date", ""),
            d.get("publication_date", ""),
            d.get("cpc", ""),
        ])

data_json = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
class_json = json.dumps(CLASS_NAMES, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cyber Patent Catalog</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #0f172a; color: #e2e8f0; }
  header { padding: 28px 20px 18px; text-align: center;
           background: linear-gradient(135deg, #1e3a8a, #0f172a); }
  header h1 { margin: 0 0 6px; font-size: 1.7em; }
  header p { margin: 0; color: #94a3b8; }
  header p.stamp { margin-top: 8px; font-size: .85em; color: #60a5fa; font-weight: 600; }
  .bar { max-width: 860px; margin: 18px auto 0; padding: 0 16px; }
  #q { width: 100%; padding: 13px 16px; font-size: 1.05em; border-radius: 10px;
       border: 1px solid #334155; background: #1e293b; color: #e2e8f0; }
  #q::placeholder { color: #64748b; }
  .filters { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
             margin: 14px 0 4px; }
  .filters button { padding: 8px 14px; border-radius: 999px; border: 1px solid #334155;
                    background: #1e293b; color: #cbd5e1; cursor: pointer; font-size: .9em; }
  .filters button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
  #count { text-align: center; color: #94a3b8; margin: 10px 0 0; font-size: .92em; }
  #results { max-width: 860px; margin: 0 auto; padding: 12px 16px 60px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px;
          padding: 14px 16px; margin: 10px 0; }
  .card .num { font-size: .78em; color: #60a5fa; font-weight: 600; letter-spacing: .04em; }
  .card h3 { margin: 6px 0 8px; font-size: 1.02em; line-height: 1.35; }
  .card .meta { font-size: .85em; color: #94a3b8; }
  .card .abs { font-size: .9em; color: #cbd5e1; margin-top: 8px; display: none;
               line-height: 1.5; }
  .card.open .abs { display: block; }
  .card .toggle { margin-top: 8px; font-size: .85em; color: #60a5fa; cursor: pointer;
                  background: none; border: none; padding: 0; }
  #more { display: block; margin: 18px auto 0; padding: 11px 26px; border-radius: 10px;
          border: 1px solid #334155; background: #2563eb; color: #fff; font-size: 1em;
          cursor: pointer; }
  footer { text-align: center; color: #64748b; font-size: .8em; padding: 0 16px 30px;
           max-width: 860px; margin: 0 auto; }
</style>
</head>
<body>
<header>
  <h1>Cyber Patent Catalog</h1>
  <p>Searchable index of cybersecurity patents &mdash; compatibility reference only</p>
  <p class="stamp">__COUNT__ patents &middot; updated __DATE__</p>
</header>
<div class="bar">
  <input id="q" type="search" placeholder="Search by name, keyword, company, inventor, or patent number&hellip;" autocomplete="off">
  <div class="filters" id="filters"></div>
</div>
<p id="count"></p>
<div id="results"></div>
<button id="more" style="display:none">Show more</button>
<footer>
  Patent records belong to their respective owners and are listed for compatibility
  and certification reference only. Data harvested from Google Patents.
</footer>
<script>
var DATA = __DATA__;
var CLASS_NAMES = __CLASSES__;
var state = { q: "", cpc: "", shown: 40 };
var filtered = [];

function hay(r) {
  return (r[0] + " " + r[1] + " " + r[2] + " " + r[3] + " " + r[4]).toLowerCase();
}
function apply() {
  var q = state.q.toLowerCase().trim();
  filtered = DATA.filter(function (r) {
    if (state.cpc && r[8] !== state.cpc) return false;
    if (q && hay(r).indexOf(q) < 0) return false;
    return true;
  });
  state.shown = 40;
  render();
}
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function card(r) {
  var num = esc(r[0]), title = esc(r[1]), abs = esc(r[2]);
  var who = esc(r[3] || r[4] || "Unknown");
  var dates = [r[7] && ("pub " + r[7]), r[6] && ("granted " + r[6])]
    .filter(Boolean).map(esc).join(" · ");
  var cls = esc((CLASS_NAMES[r[8]] || r[8]) + (r[8] ? " (" + r[8] + ")" : ""));
  return '<div class="card"><div class="num">' + num + '</div><h3>' + title + '</h3>' +
    '<div class="meta">' + who + (dates ? " · " + dates : "") + "<br>" + cls + "</div>" +
    (abs ? '<div class="abs">' + abs + "</div>" +
      '<button class="toggle" type="button">Show abstract</button>' : "") +
    "</div>";
}
function render() {
  var box = document.getElementById("results");
  var slice = filtered.slice(0, state.shown);
  box.innerHTML = slice.map(card).join("");
  document.getElementById("count").textContent =
    filtered.length.toLocaleString() + " of " + DATA.length.toLocaleString() + " patents";
  document.getElementById("more").style.display =
    state.shown < filtered.length ? "block" : "none";
}
(function init() {
  var f = document.getElementById("filters");
  var btns = [{ c: "", n: "All areas" }].concat(
    Object.keys(CLASS_NAMES).map(function (c) { return { c: c, n: CLASS_NAMES[c] }; }));
  btns.forEach(function (b) {
    var el = document.createElement("button");
    el.textContent = b.n;
    if (!b.c) el.classList.add("active");
    el.onclick = function () {
      state.cpc = b.c;
      Array.prototype.forEach.call(f.children, function (x) { x.classList.remove("active"); });
      el.classList.add("active");
      apply();
    };
    f.appendChild(el);
  });
  var input = document.getElementById("q"), t;
  input.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(function () { state.q = input.value; apply(); }, 180);
  });
  document.getElementById("more").onclick = function () { state.shown += 60; render(); };
  document.getElementById("results").addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".toggle") : null;
    if (!b) return;
    var c = b.parentElement;
    c.classList.toggle("open");
    b.textContent = c.classList.contains("open") ? "Hide abstract" : "Show abstract";
  });
  apply();
})();
</script>
</body>
</html>
"""

html = html.replace("__DATA__", data_json).replace("__CLASSES__", class_json)
html = html.replace("__COUNT__", f"{len(records):,}")
html = html.replace("__DATE__", date.today().isoformat())
with open(DST, "w", encoding="utf-8") as fh:
    fh.write(html)
with open(DST2, "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"wrote {DST} + catalog.html with {len(records)} patents ({os.path.getsize(DST)/1024:.0f} KB)")
