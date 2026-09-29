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
    # A - Human necessities
    "A01": "Agriculture & forestry", "A21": "Baking", "A22": "Butchery & meat",
    "A23": "Foods & foodstuffs", "A24": "Tobacco", "A41": "Clothing",
    "A42": "Headwear", "A43": "Footwear", "A44": "Jewellery & haberdashery",
    "A45": "Luggage & hand articles", "A46": "Brushware", "A47": "Furniture",
    "A61": "Medical & veterinary", "A62": "Life-saving & fire-fighting",
    "A63": "Sports & games",
    # B - Performing operations; transporting
    "B01": "Chemical processes", "B02": "Crushing & milling", "B03": "Separating solids",
    "B04": "Centrifuges", "B05": "Spraying & coating", "B06": "Mechanical vibrations",
    "B07": "Sorting", "B08": "Cleaning", "B21": "Metal-working (no cutting)",
    "B22": "Casting & powder metallurgy", "B23": "Machine tools", "B24": "Grinding & polishing",
    "B25": "Hand tools", "B26": "Cutting tools", "B27": "Woodworking",
    "B28": "Working stone & clay", "B29": "Plastics", "B30": "Presses",
    "B31": "Paper & packaging", "B32": "Layered products", "B33": "3D printing",
    "B41": "Printing", "B42": "Bookbinding", "B43": "Writing implements",
    "B44": "Decorative arts", "B60": "Vehicles", "B61": "Railways",
    "B62": "Cycles & motorcycles", "B63": "Ships", "B64": "Aircraft",
    "B65": "Conveying & packaging", "B66": "Lifting & hoisting", "B67": "Bottles & containers",
    "B68": "Upholstery", "B81": "Microtechnology", "B82": "Nanotechnology",
    # C - Chemistry; metallurgy
    "C01": "Inorganic chemistry", "C02": "Water treatment", "C03": "Glass & ceramics",
    "C04": "Cements & concrete", "C05": "Fertilisers", "C06": "Explosives",
    "C07": "Organic chemistry", "C08": "Polymers", "C09": "Dyes, paints & adhesives",
    "C10": "Petroleum & fuels", "C11": "Oils, fats & detergents", "C12": "Biochemistry",
    "C13": "Sugar", "C14": "Leather", "C21": "Iron metallurgy",
    "C22": "Metallurgy & alloys", "C23": "Metal coating", "C25": "Electrolytic processes",
    "C30": "Crystal growth",
    # D - Textiles; paper
    "D01": "Fibres & spinning", "D02": "Yarns", "D03": "Weaving",
    "D04": "Knitting & lace", "D05": "Sewing & embroidery", "D06": "Textile treatment",
    "D07": "Ropes & cables", "D21": "Paper-making",
    # E - Fixed constructions
    "E01": "Roads & bridges", "E02": "Hydraulic engineering", "E03": "Water & sewerage",
    "E04": "Building", "E05": "Locks & safes", "E06": "Doors & windows",
    "E21": "Drilling & mining",
    # F - Mechanical engineering
    "F01": "Engines (general)", "F02": "Combustion engines", "F03": "Wind & water motors",
    "F04": "Pumps & compressors", "F15": "Fluid-pressure devices", "F16": "Machine elements",
    "F17": "Gas & liquid storage", "F21": "Lighting", "F22": "Steam generation",
    "F23": "Combustion apparatus", "F24": "Heating & cooling", "F25": "Refrigeration",
    "F26": "Drying", "F27": "Furnaces & ovens", "F28": "Heat exchange",
    "F41": "Weapons", "F42": "Ammunition & blasting",
    # G - Physics
    "G01": "Measuring & testing", "G02": "Optics", "G03": "Photography",
    "G04": "Clocks & watches", "G05": "Controlling & regulating", "G06": "Computing",
    "G07": "Checking devices", "G08": "Signalling", "G09": "Displays & education",
    "G10": "Music & acoustics", "G11": "Information storage", "G12": "Instrument details",
    "G16": "Applied ICT", "G21": "Nuclear engineering",
    # H - Electricity
    "H01": "Electric devices", "H02": "Electric power", "H03": "Electronic circuitry",
    "H04": "Electric communication", "H05": "Electric techniques", "H10": "Semiconductors",
    # Legacy specific classes (kept for existing records)
    "H04L63": "Network security", "H04L9": "Cryptography", "G06F21": "System security",
    "H04W12": "Wireless security", "H04K": "Secret communication",
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
areas = sorted(set(r[8] for r in records if r[8]))
areas_json = json.dumps(areas, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Catalog of Public Patents</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #eef2f6; color: #1f2a37; }
  header { padding: 30px 20px 22px; text-align: center; color: #fff;
           background: linear-gradient(160deg, #16337a, #0d2149);
           border-bottom: 4px solid #c9a227; }
  .seal { width: 74px; height: 74px; margin: 0 auto 12px; border-radius: 50%;
          border: 3px double #c9a227; display: flex; align-items: center;
          justify-content: center; font-family: Georgia, serif; font-size: 2em;
          color: #e8c766; background: rgba(255,255,255,.05); }
  .eyebrow { margin: 0 0 8px; font-size: .72em; letter-spacing: .35em;
             color: #d9b84a; font-weight: 700; }
  header h1 { margin: 0 0 8px; font-size: 1.9em; font-family: Georgia, "Times New Roman", serif;
              letter-spacing: .01em; }
  header p.sub { margin: 0 auto; max-width: 640px; color: #c3cfe6; font-size: .98em;
                 line-height: 1.5; }
  .stats { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
           margin-top: 16px; }
  .stats .chip { background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.22);
                 padding: 8px 16px; border-radius: 999px; font-size: .9em; color: #e6ecf7; }
  .stats .chip b { color: #fff; }
  .sortrow { display: flex; align-items: center; justify-content: center; gap: 8px;
             margin: 14px 0 0; color: #5b6b7f; font-size: .9em; }
  .sortrow select { background: #fff; color: #1f2a37; border: 1px solid #b9c6d6;
                   border-radius: 8px; padding: 8px 10px; font-size: .95em; }
  #totop { position: fixed; right: 16px; bottom: 16px; z-index: 30; width: 48px; height: 48px;
           border-radius: 50%; border: none; background: #16337a; color: #fff;
           font-size: 1.4em; cursor: pointer; display: none;
           box-shadow: 0 4px 14px rgba(0,0,0,.3); }
  .tag { display: inline-block; background: #dbe4f5; color: #1e3a8a; font-size: .75em;
         font-weight: 700; padding: 3px 10px; border-radius: 999px; margin-top: 8px; }
  .searchwrap { max-width: 860px; margin: 20px auto 0; padding: 0 16px; }
  .searchrow { display: flex; gap: 8px; }
  #q { flex: 1; min-width: 0; padding: 13px 16px; font-size: 1.05em; border-radius: 8px;
       border: 1px solid #b9c6d6; background: #fff; color: #1f2a37; }
  #q::placeholder { color: #8a97a8; }
  #go { padding: 0 24px; border-radius: 8px; border: none; background: #16337a;
        color: #fff; font-size: 1.05em; font-weight: 700; cursor: pointer; }
  #go:active { background: #0d2149; }
  .filters { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
             margin: 14px 0 4px; }
  .filters button { padding: 8px 14px; border-radius: 999px; border: 1px solid #9fb0c6;
                    background: #fff; color: #33507e; cursor: pointer; font-size: .9em; }
  .filters button.active { background: #16337a; border-color: #16337a; color: #fff; }
  #letters { position: sticky; top: 0; z-index: 20; background: #ffffff;
             border-top: 1px solid #d3dce6; border-bottom: 1px solid #d3dce6;
             box-shadow: 0 2px 6px rgba(20,40,80,.08);
             display: flex; gap: 4px; overflow-x: auto; padding: 8px 10px;
             margin-top: 14px; -webkit-overflow-scrolling: touch; }
  #letters button { flex: 0 0 auto; min-width: 34px; padding: 8px 0; border-radius: 8px;
                    border: 1px solid #c4d0e0; background: #f4f7fb; color: #33507e;
                    font-size: .95em; font-weight: 700; cursor: pointer; }
  #letters button.hit { background: #16337a; border-color: #16337a; color: #fff; }
  #letters button:disabled { opacity: .25; cursor: default; }
  #letters button.top { background: #dbe4f5; }
  #count { text-align: center; color: #5b6b7f; margin: 12px 0 0; font-size: .92em;
           padding: 0 16px; }
  #results { max-width: 860px; margin: 0 auto; padding: 12px 16px 60px; }
  .card { background: #fff; border: 1px solid #d3dce6; border-left: 4px solid #c9a227;
          border-radius: 8px; padding: 14px 16px; margin: 10px 0;
          scroll-margin-top: 64px; box-shadow: 0 1px 3px rgba(20,40,80,.06); }
  .card .num { font-size: .78em; color: #16337a; font-weight: 700; letter-spacing: .05em; }
  .card h3 { margin: 6px 0 8px; font-size: 1.05em; line-height: 1.35; color: #14213a; }
  .card .meta { font-size: .85em; color: #5b6b7f; }
  .card .abs { font-size: .9em; color: #33415c; margin-top: 8px; display: none;
               line-height: 1.55; }
  .card.open .abs { display: block; }
  .card .toggle { margin-top: 8px; font-size: .85em; color: #1d4ed8; cursor: pointer;
                  background: none; border: none; padding: 0; font-weight: 600; }
  .card a.full { display: inline-block; margin-top: 10px; font-size: .9em; font-weight: 700;
                 color: #1d4ed8; text-decoration: none; }
  .card a.full:hover { text-decoration: underline; }
  #more { display: block; margin: 18px auto 0; padding: 11px 26px; border-radius: 8px;
          border: none; background: #16337a; color: #fff; font-size: 1em; font-weight: 600;
          cursor: pointer; }
  .noscript { max-width: 860px; margin: 20px auto; padding: 16px; background: #7f1d1d;
              color: #fff; border-radius: 8px; text-align: center; }
  footer { background: #0d2149; color: #a9b8d4; font-size: .8em; padding: 26px 20px 34px;
           text-align: center; line-height: 1.6; }
  footer .fname { font-family: Georgia, serif; color: #e8c766; font-size: 1.05em; }
  .ptools { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
  .pbtn { border: 1px solid #16337a; background: #16337a; color: #fff; border-radius: 8px;
          padding: 8px 12px; font-size: .85em; cursor: pointer; }
  .pbtn.ghost { background: #fff; color: #16337a; }
  .aichat { display: none; margin-top: 10px; border: 1px solid #c9d4e5; border-radius: 10px;
            background: #f7fafd; padding: 10px; }
  .aichat.open { display: block; }
  .ailog { max-height: 240px; overflow-y: auto; margin-bottom: 8px; font-size: .9em; }
  .ailog .u { margin: 6px 0; text-align: right; }
  .ailog .u span { display: inline-block; background: #16337a; color: #fff;
                   padding: 6px 10px; border-radius: 12px 12px 4px 12px; max-width: 92%; text-align: left; }
  .ailog .a { margin: 6px 0; }
  .ailog .a span { display: inline-block; background: #e9eef7; color: #1f2a37;
                   padding: 6px 10px; border-radius: 12px 12px 12px 4px; max-width: 92%; }
  .ailog .a .airead { margin-left: 6px; border: none; background: none; cursor: pointer; font-size: 1em; }
  .airow { display: flex; gap: 6px; }
  .airow input { flex: 1; min-width: 0; padding: 8px 10px; border-radius: 8px;
                 border: 1px solid #b9c6d6; font-size: .9em; }

  .jahnet { background:#0d2149; color:#a9b8d4; font-size:.78em; padding:7px 12px; text-align:center; line-height:2; }
  .jahnet-t { color:#e8c766; font-weight:700; letter-spacing:.25em; margin-right:10px; }
  .jahnet a { color:#9fc2ff; text-decoration:none; margin:0 7px; white-space:nowrap; }
  .jahnet a:hover { text-decoration:underline; }
</style>
</head>
<body>
<div class="jahnet"><span class="jahnet-t">THE JAH NETWORK</span>
<a href="https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/">Patent Catalog</a>
<a href="https://justinahiggins614-cmyk.github.io/signature-one-archive/">Spec Catalog</a>
<a href="https://justinahiggins614-cmyk.github.io/jah-dictionary/">IWB Dictionary</a>
<a href="https://justinahiggins614-cmyk.github.io/jah-wiki/">JAH Wiki</a>
<a href="https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/">Wiki Leaks</a>
<a href="https://justinahiggins614-cmyk.github.io/jah-calculator/">Calculator</a>
<a href="https://justinahiggins614-cmyk.github.io/jah-ai-models/">AI Telephone Book</a>
</div>
<header>
  <div class="seal">&#167;</div>
  <p class="eyebrow">PUBLIC RECORDS INDEX</p>
  <h1>The Catalog of Public Patents</h1>
  <p class="sub">A comprehensive public index of published patent records &mdash;
  every field of invention, from software to medicine to engineering &mdash; fully searchable.</p>
  <div class="stats">
    <span class="chip"><b>__COUNT__</b> patents</span>
    <span class="chip"><b>__AREAS_N__</b> technology areas</span>
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
  <div class="fname">The Catalog of Public Patents</div>
  <p>An independent index of publicly available patent records, cataloged for compatibility
  and certification purposes. All patents remain the property of their respective owners.<br>
  Full patent texts open on Google Patents. This catalog is not affiliated with the USPTO
  or any government agency.</p>
</footer>
<script>
var DATA = __DATA__;
var CLASS_NAMES = __CLASSES__;
var AREAS = __AREAS__;
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
    '<div class="ptools">' +
    '<button class="pbtn readbtn" type="button" data-i="' + i + '">&#128266; Read aloud</button>' +
    '<button class="pbtn ghost aibtn" type="button" data-i="' + i + '">&#128172; Ask the AI</button>' +
    '<button class="pbtn ghost copybtn" type="button" data-i="' + i + '">&#10697; Copy</button>' +
    '<button class="pbtn ghost dlbtn" type="button" data-i="' + i + '">&#8681; Download</button>' +
    '</div>' +
    '<div class="aichat"><div class="ailog"></div>' +
    '<div class="airow"><input type="text" class="aiinput" placeholder="Ask about this patent&hellip;" aria-label="Ask the AI about this patent">' +
    '<button class="pbtn aisend" type="button" data-i="' + i + '">Send</button></div></div>' +
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
    AREAS.map(function (c) { return { c: c, n: CLASS_NAMES[c] || c }; }));
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
  /* ---- per-patent read-aloud (tiered: built-in voice, else online voice hosts) ---- */
  var readingBtn = null;
  function hasSpeech2(){ try { return ("speechSynthesis" in window) && !!window.speechSynthesis && typeof window.speechSynthesis.speak === "function"; } catch(e){ return false; } }
  try { if (hasSpeech2()) { window.speechSynthesis.getVoices(); } } catch(e){}
  function pickVoice2(){ try { var vs = window.speechSynthesis.getVoices() || [];
    for (var i=0;i<vs.length;i++){ var n=((vs[i].name||"")+" "+(vs[i].lang||"")).toLowerCase();
      if ((vs[i].lang||"").toLowerCase().indexOf("en")===0 && /female|samantha|zira|google us english|aria|jenny|karen|moira|tessa|veena|fiona|hazel/.test(n)) return vs[i]; }
    for (i=0;i<vs.length;i++){ if ((vs[i].lang||"").toLowerCase().indexOf("en")===0) return vs[i]; }
  } catch(e){} return null; }
  var TTS_TIERS2 = [
    function(t){ return "https://code.responsivevoice.org/getvoice.php?t="+encodeURIComponent(t)+"&tl=en-US"; },
    function(t){ return "https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q="+encodeURIComponent(t); },
    function(t){ return "https://translate.googleapis.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q="+encodeURIComponent(t); }];
  function fxChunks2(text){ var out=[], cur="", parts=String(text).split(/([.!?]["']?(?:\s+|$))/);
    function pushWords(s){ var w=s.split(" "), c=""; for (var k=0;k<w.length;k++){ var t=(c+" "+w[k]).trim();
      if (t.length>180){ if (c) out.push(c); c=w[k]; } else c=t; } if (c) out.push(c); }
    for (var i=0;i<parts.length;i+=2){ var s=((parts[i]||"")+(parts[i+1]||"")).replace(/\s+/g," ").trim(); if(!s) continue;
      if (s.length>180){ if(cur){out.push(cur);cur="";} pushWords(s); continue; }
      if (cur && (cur+" "+s).length>180){ out.push(cur); cur=s; } else cur=cur?cur+" "+s:s; }
    if (cur) out.push(cur); return out; }
  var FX2 = { audio: null, active: false };
  function fxPlay2(list, i, tier, retry, done){
    if (!FX2.active) return;
    if (i>=list.length){ FX2.active=false; if(done)done(); return; }
    var a; try { a = new Audio(TTS_TIERS2[tier](list[i])); } catch(e){ if(done)done(); return; }
    FX2.audio = a;
    a.onended = function(){ if (FX2.active){ fxPlay2(list, i+1, tier, 0, done); } };
    a.onerror = function(){ if (!FX2.active) return;
      if (retry<1){ fxPlay2(list, i, tier, retry+1, done); return; }
      if (tier+1<TTS_TIERS2.length){ fxPlay2(list, i, tier+1, 0, done); return; }
      FX2.active=false; if(done)done(); };
    try { var pr=a.play(); if (pr&&pr.catch) pr.catch(function(){}); } catch(e){}
  }
  function stopAudio2(){
    try { if (hasSpeech2()) window.speechSynthesis.cancel(); } catch(e){}
    FX2.active=false;
    if (FX2.audio){ try { FX2.audio.pause(); } catch(e){} FX2.audio=null; }
    if (readingBtn){ readingBtn.innerHTML="\\uD83D\\uDD0A Read aloud"; readingBtn=null; }
  }
  function readText2(text, btn, done){
    stopAudio2();
    if (!text || !text.trim()){ if(done)done(); return; }
    readingBtn = btn; if (btn) btn.innerHTML="\u23F9 Stop";
    var fin = function(){ if(done)done(); };
    if (hasSpeech2()){
      try { window.speechSynthesis.cancel(); } catch(e){}
      var chunks = fxChunks2(text), vi = 0, v = pickVoice2();
      (function next(){
        if (vi>=chunks.length){ stopAudio2(); fin(); return; }
        var u = new SpeechSynthesisUtterance(chunks[vi]);
        u.rate=1; u.lang="en-US"; if (v) u.voice=v;
        u.onend = function(){ vi++; next(); };
        u.onerror = function(){ vi++; next(); };
        window.speechSynthesis.speak(u);
      })();
    } else {
      FX2.active=true;
      fxPlay2(fxChunks2(text), 0, 0, 0, function(){ stopAudio2(); fin(); });
    }
  }
  function patentText(r){
    var parts = ["Patent " + r[0] + ".", r[1] + "."];
    if ((r[3]||"").trim()) parts.push("Owner: " + r[3].trim() + ".");
    if ((r[4]||"").trim()) parts.push("Inventor: " + r[4].trim() + ".");
    if (r[5]) parts.push("Filed " + r[5] + ".");
    if (r[7]) parts.push("Published " + r[7] + ".");
    if (r[6]) parts.push("Granted " + r[6] + ".");
    parts.push("Field: " + (CLASS_NAMES[r[8]] || r[8] || "general invention") + ".");
    if ((r[2]||"").trim()) parts.push("Abstract: " + r[2].trim());
    return parts.join(" ");
  }
  /* ---- per-patent personal AI (answers from this catalog record only) ---- */
  var AIREPLIES = [];
  function firstSentences(s, n){
    var m = String(s).match(/[^.!?]+[.!?]+/g) || [String(s)];
    return m.slice(0, n).join(" ").trim();
  }
  function linkify(s){
    return esc(s).replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  }
  function patentAI(r, q){
    var num=r[0], title=r[1], abs=(r[2]||"").trim(), owner=(r[3]||"").trim(), inv=(r[4]||"").trim();
    var filed=r[5]||"", pub=r[7]||"", grant=r[6]||"";
    var cls = (CLASS_NAMES[r[8]] || r[8] || "general invention") + (r[8] ? " (" + r[8] + ")" : "");
    var link = "https://patents.google.com/patent/" + encodeURIComponent(num) + "/";
    var t = " " + String(q).toLowerCase() + " ";
    function has(){ for (var i=0;i<arguments.length;i++) if (t.indexOf(arguments[i])>=0) return true; return false; }
    if (has("hello"," hi "," hey ","good morning","good afternoon","good evening"))
      return "Hello! I'm the personal AI for patent " + num + ". Ask me who invented it, who owns it, what it's about, or its filing and grant dates \u2014 I answer from this catalog's record.";
    if (has("inventor","who invented","who made","who created","invented by","who designed"))
      return inv ? ("The listed inventor is " + inv + ".") : "This record doesn't name an inventor.";
    if (has("owner","who owns","owned by","company","assignee","who holds","holder"))
      return owner ? ("The listed owner (assignee) is " + owner + ".") : "This record doesn't name an owner.";
    if (has("grant","when granted","granted on","issue date","issued"))
      return grant ? ("It was granted on " + grant + ".") : "This record shows no grant date.";
    if (has("filed","filing","when filed","file date","application date","applied"))
      return filed ? ("It was filed on " + filed + ".") : "This record shows no filing date.";
    if (has("publish","when published","publication date"))
      return pub ? ("It was published on " + pub + ".") : "This record shows no publication date.";
    if (has("field","category","class","cpc","what area","what kind","sector"))
      return "It's classed under " + cls + ".";
    if (has("number","patent no","patent number","publication no"))
      return "The publication number is " + num + ".";
    if (has("simple","eli5","plain","easy","simple terms","like i'm five","like i am five","explain simply","dumb it down"))
      return "In simple terms: " + title.charAt(0).toLowerCase() + title.slice(1) + ". " + (abs ? firstSentences(abs, 2) : "");
    if (has("link","full text","full patent","read more","more detail","google patent","official"))
      return "You can read the full official patent text here: " + link;
    if (has("what is","summar","about","explain","describe","tell me","overview","mean","what does"))
      return title + ". " + (abs ? firstSentences(abs, 3) : "No abstract is listed for this record.");
    if (has("thank"))
      return "You're welcome! Anything else about patent " + num + "?";
    if (has("bye","goodbye"))
      return "Goodbye! I'll be right here on patent " + num + " whenever you need me.";
    return "I can tell you about this patent \u2014 try: who invented it, who owns it, what it's about (or \u2018explain simply\u2019), its field, or its filing and grant dates.";
  }
  function aiBubble(log, who, text){
    var k = -1, div = document.createElement("div");
    div.className = who;
    if (who === "a"){ k = AIREPLIES.length; AIREPLIES.push(text);
      div.innerHTML = "<span>" + linkify(text) + "</span>" +
        '<button class="airead" type="button" data-k="' + k + '" title="Read this answer aloud">\\uD83D\\uDD0A</button>';
    } else {
      div.innerHTML = "<span>" + esc(text) + "</span>";
    }
    log.appendChild(div); log.scrollTop = log.scrollHeight;
  }

  function patentFileText(r){
    var L = [];
    L.push("THE CATALOG OF PUBLIC PATENTS");
    L.push("Patent: " + r[0]);
    L.push("Title: " + r[1]);
    if ((r[3]||"").trim()) L.push("Owner: " + r[3].trim());
    if ((r[4]||"").trim()) L.push("Inventor: " + r[4].trim());
    if (r[5]) L.push("Filed: " + r[5]);
    if (r[7]) L.push("Published: " + r[7]);
    if (r[6]) L.push("Granted: " + r[6]);
    L.push("Field: " + (CLASS_NAMES[r[8]] || r[8] || "general invention") + (r[8] ? " (" + r[8] + ")" : ""));
    L.push("Full text: https://patents.google.com/patent/" + encodeURIComponent(r[0]) + "/");
    if ((r[2]||"").trim()) L.push("", "Abstract:", r[2].trim());
    return L.join("\\n");
  }
  function downloadFile2(name, content){
    var b = new Blob([content], {type: "text/plain"});
    var u = URL.createObjectURL(b), a = document.createElement("a");
    a.href = u; a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(u); a.remove(); }, 800);
  }
  function copyText2(t, btn){
    function done(){ if (btn){ var o = btn.innerHTML; btn.innerHTML = "Copied!"; setTimeout(function(){ btn.innerHTML = o; }, 1400); } }
    function fallback(){
      var ta = document.createElement("textarea"); ta.value = t;
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch(e){}
      ta.remove();
    }
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(t).then(done, fallback);
    } else fallback();
  }
  document.getElementById("results").addEventListener("click", function (e) {
    var rb = e.target.closest ? e.target.closest(".readbtn") : null;
    if (rb){
      var ri = +rb.getAttribute("data-i");
      if (readingBtn === rb){ stopAudio2(); return; }
      readText2(patentText(filtered[ri]), rb);
      return;
    }
    var abtn = e.target.closest ? e.target.closest(".aibtn") : null;
    if (abtn){
      var card = abtn.closest(".card"), chat = card.querySelector(".aichat");
      var log = chat.querySelector(".ailog");
      chat.classList.toggle("open");
      if (chat.classList.contains("open") && !log.children.length){
        aiBubble(log, "a", patentAI(filtered[+abtn.getAttribute("data-i")], "hello"));
      }
      return;
    }
    var sd = e.target.closest ? e.target.closest(".aisend") : null;
    if (sd){
      var card2 = sd.closest(".card"), chat2 = card2.querySelector(".aichat");
      var log2 = chat2.querySelector(".ailog"), inp = chat2.querySelector(".aiinput");
      var q = (inp.value || "").trim();
      if (!q) return;
      inp.value = "";
      aiBubble(log2, "u", q);
      aiBubble(log2, "a", patentAI(filtered[+sd.getAttribute("data-i")], q));
      return;
    }
    var ar = e.target.closest ? e.target.closest(".airead") : null;
    if (ar){
      readText2(AIREPLIES[+ar.getAttribute("data-k")] || "", null);
      return;
    }
    var cb = e.target.closest ? e.target.closest(".copybtn") : null;
    if (cb){
      copyText2(patentFileText(filtered[+cb.getAttribute("data-i")]), cb);
      return;
    }
    var db = e.target.closest ? e.target.closest(".dlbtn") : null;
    if (db){
      var r2 = filtered[+db.getAttribute("data-i")];
      downloadFile2("patent-" + String(r2[0]).replace(/[^A-Za-z0-9]+/g, "_") + ".txt", patentFileText(r2));
      return;
    }
    var b = e.target.closest ? e.target.closest(".toggle") : null;
    if (!b) return;
    var c = b.parentElement;
    c.classList.toggle("open");
    b.textContent = c.classList.contains("open") ? "Hide abstract" : "Show abstract";
  });
  document.getElementById("results").addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target && e.target.classList && e.target.classList.contains("aiinput")){
      var card = e.target.closest(".card"), btn = card.querySelector(".aisend");
      if (btn) btn.click();
    }
  });
  apply();
})();
</script>
</body>
</html>
"""

html = html.replace("__DATA__", data_json).replace("__CLASSES__", class_json)
html = html.replace("__AREAS__", areas_json)
html = html.replace("__COUNT__", f"{len(records):,}")
html = html.replace("__AREAS_N__", f"{len(areas):,}")
html = html.replace("__DATE__", date.today().isoformat())
with open(DST, "w", encoding="utf-8") as fh:
    fh.write(html)
with open(DST2, "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"wrote {DST} + catalog.html with {len(records)} patents ({os.path.getsize(DST)/1024:.0f} KB)")
