#!/usr/bin/env python3
"""Build the searchable Catalog of Public Patents static site.

Run from the repo root:  python3 code/harvest/build_catalog_page.py
Reads data/patents.jsonl, writes index.html and catalog.html with data embedded.
"""
import json
import os
from datetime import date
from html import unescape as html_unescape

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


def letter_of(title):
    for ch in title.strip().upper():
        if "A" <= ch <= "Z":
            return ch
        if ch.isalpha() or ch.isdigit():
            return "#"
    return "#"


records = []
with open(SRC, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        g = lambda k: html_unescape(str(d.get(k, "") or ""))
        title = g("title")
        records.append([
            g("publication_number"),
            title,
            g("abstract_snippet"),
            g("assignee"),
            g("inventor"),
            g("filing_date"),
            g("grant_date"),
            g("publication_date"),
            g("cpc"),
            letter_of(title),
        ])

# Alphabetical by title so the A-Z jump bar makes sense.
records.sort(key=lambda r: r[1].lower())

data_json = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
class_json = json.dumps(CLASS_NAMES, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Catalog of Public Patents</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #0f172a; color: #e2e8f0; }
  header { padding: 28px 20px 18px; text-align: center;
           background: linear-gradient(135deg, #1e3a8a, #0f172a); }
  header h1 { margin: 0 0 6px; font-size: 1.7em; }
  header p { margin: 0; color: #94a3b8; }
  header p.stamp { margin-top: 8px; font-size: .85em; color: #60a5fa; font-weight: 600; }
  .stats { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
           margin-top: 14px; }
  .stats .chip { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15);
                 padding: 8px 16px; border-radius: 999px; font-size: .9em; color: #e2e8f0; }
  .stats .chip b { color: #fff; }
  .sortrow { display: flex; align-items: center; justify-content: center; gap: 8px;
             margin: 12px 0 0; color: #94a3b8; font-size: .9em; }
  .sortrow select { background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
                   border-radius: 8px; padding: 8px 10px; font-size: .95em; }
  #totop { position: fixed; right: 16px; bottom: 16px; z-index: 30; width: 48px; height: 48px;
           border-radius: 50%; border: none; background: #2563eb; color: #fff;
           font-size: 1.4em; cursor: pointer; display: none;
           box-shadow: 0 4px 14px rgba(0,0,0,.4); }
  .card { transition: border-color .15s; }
  .card:hover { border-color: #475569; }
  .tag { display: inline-block; background: #1e3a8a; color: #bfdbfe; font-size: .75em;
         font-weight: 600; padding: 3px 10px; border-radius: 999px; margin-top: 8px; }
  .searchwrap { max-width: 860px; margin: 18px auto 0; padding: 0 16px; }
  .searchrow { display: flex; gap: 8px; }
  #q { flex: 1; min-width: 0; padding: 13px 16px; font-size: 1.05em; border-radius: 10px;
       border: 1px solid #334155; background: #1e293b; color: #e2e8f0; }
  #q::placeholder { color: #64748b; }
  #go { padding: 0 22px; border-radius: 10px; border: none; background: #2563eb;
        color: #fff; font-size: 1.05em; font-weight: 600; cursor: pointer; }
  #go:active { background: #1d4ed8; }
  .filters { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
             margin: 14px 0 4px; }
  .filters button { padding: 8px 14px; border-radius: 999px; border: 1px solid #334155;
                    background: #1e293b; color: #cbd5e1; cursor: pointer; font-size: .9em; }
  .filters button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
  #letters { position: sticky; top: 0; z-index: 20; background: #0f172a;
             border-top: 1px solid #1e293b; border-bottom: 1px solid #1e293b;
             display: flex; gap: 4px; overflow-x: auto; padding: 8px 10px;
             margin-top: 12px; -webkit-overflow-scrolling: touch; }
  #letters button { flex: 0 0 auto; min-width: 34px; padding: 8px 0; border-radius: 8px;
                    border: 1px solid #334155; background: #1e293b; color: #cbd5e1;
                    font-size: .95em; font-weight: 600; cursor: pointer; }
  #letters button.hit { background: #2563eb; border-color: #2563eb; color: #fff; }
  #letters button:disabled { opacity: .25; cursor: default; }
  #letters button.top { background: #334155; }
  #count { text-align: center; color: #94a3b8; margin: 10px 0 0; font-size: .92em;
           padding: 0 16px; }
  #results { max-width: 860px; margin: 0 auto; padding: 12px 16px 60px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px;
          padding: 14px 16px; margin: 10px 0; scroll-margin-top: 64px; }
  .card .num { font-size: .78em; color: #60a5fa; font-weight: 600; letter-spacing: .04em; }
  .card h3 { margin: 6px 0 8px; font-size: 1.02em; line-height: 1.35; }
  .card .meta { font-size: .85em; color: #94a3b8; }
  .card .abs { font-size: .9em; color: #cbd5e1; margin-top: 8px; display: none;
               line-height: 1.5; }
  .card.open .abs { display: block; }
  .card .toggle { margin-top: 8px; font-size: .85em; color: #60a5fa; cursor: pointer;
                  background: none; border: none; padding: 0; }
  .card a.full { display: inline-block; margin-top: 10px; font-size: .9em; font-weight: 600;
                 color: #93c5fd; text-decoration: none; }
  .card a.full:hover { text-decoration: underline; }
  #more { display: block; margin: 18px auto 0; padding: 11px 26px; border-radius: 10px;
          border: 1px solid #334155; background: #2563eb; color: #fff; font-size: 1em;
          cursor: pointer; }
  .noscript { max-width: 860px; margin: 20px auto; padding: 16px; background: #7f1d1d;
              border-radius: 10px; text-align: center; }
  footer { text-align: center; color: #64748b; font-size: .8em; padding: 0 16px 30px;
           max-width: 860px; margin: 0 auto; }
</style>
</head>
<body>
<header>
  <h1>The Catalog of Public Patents</h1>
  <p>The full collection &mdash; every cybersecurity patent gathered, searchable</p>
  <div class="stats">
    <span class="chip"><b>__COUNT__</b> patents</span>
    <span class="chip"><b>5</b> technology areas</span>
    <span class="chip">Updated <b>__DATE__</b></span>
  </div>
</header>
<div class="searchwrap">
  <div class="searchrow">
    <input id="q" type="search" placeholder="Search by name, keyword, company, inventor, or patent number&hellip;" autocomplete="off">
    <button id="go" type="button">Search</button>
  </div>
  <div class="filters" id="filters"></div>
  <div class="sortrow">Sort:
    <select id="sort">
      <option value="az">A to Z</option>
      <option value="new">Newest first</option>
      <option value="old">Oldest first</option>
    </select>
  </div>
</div>
<nav id="letters" aria-label="Jump by letter"></nav>
<noscript><div class="noscript">This catalog needs JavaScript turned on to search and list patents.</div></noscript>
<p id="count"></p>
<div id="results"></div>
<button id="more" type="button" style="display:none">Show more</button>
<button id="totop" type="button" title="Back to top">&#8593;</button>
<footer>
  All patents remain the property of their respective owners and are cataloged here
  for compatibility and certification. Full patent texts open on Google Patents.
</footer>
<script>
var DATA = __DATA__;
var CLASS_NAMES = __CLASSES__;
var LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ#".split("");
var state = { q: "", cpc: "", sort: "az", shown: 40 };
var filtered = [];

function hay(r) {
  return (r[0] + " " + r[1] + " " + r[2] + " " + r[3] + " " + r[4]).toLowerCase();
}
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function apply() {
  var q = state.q.toLowerCase().trim();
  filtered = DATA.filter(function (r) {
    if (state.cpc && r[8] !== state.cpc) return false;
    if (q && hay(r).indexOf(q) < 0) return false;
    return true;
  });
  if (state.sort === "new" || state.sort === "old") {
    filtered.sort(function (a, b) {
      var da = a[7] || "", db = b[7] || "";
      if (da === db) return a[1].toLowerCase() < b[1].toLowerCase() ? -1 : 1;
      if (state.sort === "new") return db < da ? -1 : 1;
      return da < db ? -1 : 1;
    });
  }
  state.shown = 40;
  render();
}
function card(r, i) {
  var num = esc(r[0]), title = esc(r[1]), abs = esc(r[2]);
  var assignee = (r[3] || "").trim(), inventor = (r[4] || "").trim();
  var dates = [["Filed", r[5]], ["Published", r[7]], ["Granted", r[6]]]
    .filter(function (d) { return d[1]; })
    .map(function (d) { return d[0] + " " + esc(d[1]); }).join(" · ");
  var cls = esc((CLASS_NAMES[r[8]] || r[8]) + (r[8] ? " (" + r[8] + ")" : ""));
  var link = "https://patents.google.com/patent/" + encodeURIComponent(r[0]) + "/";
  return '<div class="card" id="p' + i + '" data-letter="' + r[9] + '">' +
    '<div class="num">' + num + '</div><h3>' + title + '</h3>' +
    '<div class="meta">' +
    (assignee ? "Owner: " + esc(assignee) + "<br>" : "") +
    (inventor ? "Inventor: " + esc(inventor) + "<br>" : "") +
    (dates ? dates : "") + '</div><div><span class="tag">' + cls + "</span></div>" +
    (abs ? '<div class="abs">' + abs + "</div>" +
      '<button class="toggle" type="button">Show abstract</button><br>' : "") +
    '<a class="full" href="' + link + '" target="_blank" rel="noopener">View full patent text &#8594;</a>' +
    "</div>";
}
function renderLetters() {
  var nav = document.getElementById("letters");
  var present = {};
  filtered.forEach(function (r) { present[r[9]] = true; });
  var h = '<button type="button" class="top" data-l="^" title="Back to top">&#8593;</button>';
  h += LETTERS.map(function (L) {
    return '<button type="button" data-l="' + L + '"' +
      (present[L] ? "" : " disabled") + ">" + L + "</button>";
  }).join("");
  nav.innerHTML = h;
}
function render() {
  renderLetters();
  var box = document.getElementById("results");
  var slice = filtered.slice(0, state.shown);
  box.innerHTML = slice.map(card).join("");
  var label = filtered.length.toLocaleString() + " of " + DATA.length.toLocaleString() + " patents";
  if (state.q.trim()) label += ' &mdash; results for &ldquo;' + esc(state.q.trim()) + "&rdquo;";
  document.getElementById("count").innerHTML = label;
  document.getElementById("more").style.display =
    state.shown < filtered.length ? "block" : "none";
}
function jumpToLetter(L) {
  if (L === "^") { window.scrollTo(0, 0); return; }
  var idx = -1;
  for (var i = 0; i < filtered.length; i++) {
    if (filtered[i][9] === L) { idx = i; break; }
  }
  if (idx < 0) return;
  if (idx >= state.shown) { state.shown = idx + 1; render(); }
  var el = document.getElementById("p" + idx);
  if (el && el.scrollIntoView) el.scrollIntoView(true);
  var cards = document.querySelectorAll("#results .card.hit");
  for (var j = 0; j < cards.length; j++) cards[j].classList.remove("hit");
  if (el) {
    el.style.borderColor = "#2563eb";
    setTimeout(function () { el.style.borderColor = ""; }, 1600);
  }
}
(function init() {
  var f = document.getElementById("filters");
  var btns = [{ c: "", n: "All areas" }].concat(
    Object.keys(CLASS_NAMES).map(function (c) { return { c: c, n: CLASS_NAMES[c] }; }));
  btns.forEach(function (b) {
    var el = document.createElement("button");
    el.type = "button";
    el.textContent = b.n;
    if (!b.c) el.classList.add("active");
    el.onclick = function () {
      state.cpc = b.c;
      for (var k = 0; k < f.children.length; k++) f.children[k].classList.remove("active");
      el.classList.add("active");
      apply();
    };
    f.appendChild(el);
  });
  var input = document.getElementById("q"), t;
  function doSearch() { state.q = input.value; apply(); }
  document.getElementById("go").onclick = doSearch;
  input.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(doSearch, 200);
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); doSearch(); }
  });
  document.getElementById("more").onclick = function () { state.shown += 60; render(); };
  document.getElementById("sort").onchange = function (e) {
    state.sort = e.target.value;
    apply();
  };
  var totop = document.getElementById("totop");
  totop.onclick = function () { window.scrollTo(0, 0); };
  window.addEventListener("scroll", function () {
    totop.style.display = window.scrollY > 600 ? "block" : "none";
  });
  document.getElementById("letters").addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("button[data-l]") : null;
    if (!b || b.disabled) return;
    jumpToLetter(b.getAttribute("data-l"));
  });
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
