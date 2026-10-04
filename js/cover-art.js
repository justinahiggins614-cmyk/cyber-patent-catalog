/* =====================================================================
   Signature Cover Engine v1 — deterministic product-cover art.
   Same family as the signature-books covers (FNV-1a hash -> 8 palettes),
   but the motif is driven by the record's CATEGORY so the picture reads
   at a glance: software shows the tool on a PC screen, hardware shows a
   device silhouette, methods show a flowchart, chemistry a flask, etc.
   Zero storage cost: pure client-side SVG, painted lazily on scroll.
   ES5-safe. No dependencies.
   ===================================================================== */
window.CoverArt = (function () {
  "use strict";

  /* FNV-1a, same as signature-books coverSVG */
  function hashStr(s) {
    var h = 2166136261;
    s = String(s);
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = (h * 16777619) >>> 0; }
    return h;
  }
  function cEsc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  /* Same 8 palettes as the book covers, for visual consistency. */
  var PALS = [
    { bg: ["#1a2f3a", "#0d1b22"], acc: "#e8b64c", ink: "#f5edd8" },
    { bg: ["#3a1a2e", "#1c0d16"], acc: "#e86a4c", ink: "#f7e8d8" },
    { bg: ["#1e3a24", "#0e1c11"], acc: "#9fd67a", ink: "#eef5e0" },
    { bg: ["#2a2350", "#12102a"], acc: "#b48ce8", ink: "#ece8f7" },
    { bg: ["#4a2f14", "#241505"], acc: "#f0c060", ink: "#f7ecd4" },
    { bg: ["#0f3a3a", "#071c1c"], acc: "#5cd6d6", ink: "#e0f5f5" },
    { bg: ["#3a3a1e", "#1c1c0e"], acc: "#d6c45c", ink: "#f5f2df" },
    { bg: ["#501818", "#280b0b"], acc: "#f08c8c", ink: "#f7e4e4" }
  ];
  function rnd(seed) {
    var s = seed >>> 0;
    return function (n) { s = (s * 1103515245 + 12345) >>> 0; return n ? s % n : s; };
  }

  /* ---------- category -> motif (first match wins; order matters) ---------- */
  var RULES = [
    ["screen", /software|digital|\bai\b|artificial intelligence|machine learning|data|cloud|cyber|network|database|operating system|compiler|\bapi\b|gaming|mobile|web|virtual|encrypt|blockchain|firmware|simulat|\bcad\b|stream|vision|nlp|search|payment|recommend|anomaly|edge|container|geospatial|voice|testing|compress|rout|identity|developer|comput|ict|signal|communicat|algorithm|program|code|platform|interface|language|display|smart|\bapp\b/],
    ["chip", /chip|semiconductor|processor|microchip|micro |nano|circuit|transistor|memory/],
    ["engine", /engine|motor|turbine|pump|compressor|combustion|furnace|boiler|reactor|propuls/],
    ["vehicle", /vehicle|car|automotive|aircraft|ship|rail|cycle|motorcycle|boat|drone|transport|convey|lift|truck|aero/],
    ["tool", /tool|wrench|drill|saw|cutter|grind|polish|press|mill|lathe|hammer|blade|implement/],
    ["medical", /medical|health|dental|surgical|diagnos|therapy|prosthe|veterinar|life.saving|implant/],
    ["flask", /chem|polymer|compound|molecule|flask|pharma|drug|reagent|catalyst|crystal|alloy|petroleum|fuel/],
    ["flow", /method|process|manufactur|workflow|procedure|protocol|treatment|separat|sort|coat|spray|pipeline|logistic|supply/],
    ["gear", /gear|machine|mechanic|bearing|clutch|transmission|valve|hydraulic|pneumatic|vibrat/],
    ["device", /device|apparatus|equipment|instrument|appliance|gadget|sensor|detect|meter|watch|clock|camera|phone|battery|power|electric|electronic|lamp|light|antenna|robot|printer|printing|optics|speaker|wearable/],
    ["draft", /design|draft|architect|fashion|\bart\b|decor|print|furniture|cloth|footwear|jewel|textile|weav|knit|sew|paper|packag|bookbind|brush|luggage/],
    ["food", /food|beverage|cook|recipe|bak|agricultur|farm|meat|tobacco|sugar|dairy/],
    ["building", /build|construction|road|bridge|door|window|lock|safe|drill|mining/],
    ["media", /media|video|audio|music|game|sport|toy|film|photo/]
  ];
  function motifFor(cat) {
    var c = " " + String(cat || "").toLowerCase() + " ";
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i][1].test(c)) return RULES[i][0];
    }
    return "device";
  }

  /* ---------- motif painters (art zone ~ x40-280, y30-160) ---------- */
  var CX = 160, CY = 98;
  function M() { return {}; }
  var PAINT = {
    screen: function (p, R) {
      var s = "";
      s += '<path d="M138,168 L182,168 L174,198 L146,198 Z" fill="' + p.ink + '" opacity="0.85"/>';
      s += '<rect x="118" y="196" width="84" height="9" rx="4.5" fill="' + p.ink + '" opacity="0.85"/>';
      s += '<rect x="66" y="36" width="188" height="136" rx="10" fill="#141824"/>';
      s += '<rect x="66" y="36" width="188" height="136" rx="10" fill="none" stroke="' + p.acc + '" stroke-width="2" opacity="0.5"/>';
      s += '<rect x="76" y="46" width="168" height="116" rx="4" fill="' + p.acc + '" opacity="0.14"/>';
      s += '<rect x="76" y="46" width="168" height="17" rx="4" fill="' + p.acc + '" opacity="0.9"/>';
      for (var d = 0; d < 3; d++)
        s += '<circle cx="' + (88 + d * 12) + '" cy="54.5" r="3.4" fill="#141824" opacity="0.75"/>';
      var yy = 76;
      [[120, .8], [150, .55], [100, .65]].forEach(function (w, i) {
        s += '<rect x="88" y="' + (yy + i * 14) + '" width="' + w[0] + '" height="7" rx="3.5" fill="' + p.ink + '" opacity="' + w[1] + '"/>';
      });
      for (var b = 0; b < 4; b++) {
        var bh = 18 + R(30);
        s += '<rect x="' + (88 + b * 38) + '" y="' + (150 - bh) + '" width="24" height="' + bh + '" rx="3" fill="' + p.acc + '" opacity="0.9"/>';
      }
      s += '<polygon points="226,132 238,132 232,146" fill="' + p.ink + '"/>';
      s += '<line x1="232" y1="146" x2="224" y2="158" stroke="' + p.ink + '" stroke-width="2.5"/>';
      return s;
    },
    chip: function (p, R) {
      var s = "", i, x;
      for (i = 0; i < 6; i++) {
        x = 118 + i * 17;
        s += '<line x1="' + x + '" y1="38" x2="' + x + '" y2="56" stroke="' + p.acc + '" stroke-width="4"/>';
        s += '<line x1="' + x + '" y1="144" x2="' + x + '" y2="162" stroke="' + p.acc + '" stroke-width="4"/>';
      }
      for (i = 0; i < 4; i++) {
        var y = 72 + i * 20;
        s += '<line x1="92" y1="' + y + '" x2="110" y2="' + y + '" stroke="' + p.acc + '" stroke-width="4"/>';
        s += '<line x1="210" y1="' + y + '" x2="228" y2="' + y + '" stroke="' + p.acc + '" stroke-width="4"/>';
      }
      s += '<rect x="110" y="56" width="100" height="88" rx="8" fill="#1c2230" stroke="' + p.acc + '" stroke-width="3"/>';
      s += '<rect x="136" y="80" width="48" height="40" fill="' + p.acc + '" opacity="0.28" stroke="' + p.acc + '" stroke-width="2"/>';
      s += '<circle cx="122" cy="68" r="5" fill="' + p.acc + '"/>';
      s += '<text x="160" y="140" text-anchor="middle" font-family="monospace" font-size="13" fill="' + p.ink + '" opacity="0.8">JAH-1</text>';
      return s;
    },
    engine: function (p, R) {
      var s = "";
      for (var i = 0; i < 3; i++) {
        var x = 112 + i * 34;
        s += '<rect x="' + x + '" y="52" width="22" height="34" rx="4" fill="' + p.acc + '" opacity="0.85"/>';
        s += '<circle cx="' + (x + 11) + '" cy="46" r="9" fill="none" stroke="' + p.acc + '" stroke-width="4"/>';
      }
      s += '<rect x="98" y="86" width="124" height="66" rx="8" fill="#1c2230" stroke="' + p.acc + '" stroke-width="3"/>';
      s += '<rect x="112" y="100" width="96" height="10" rx="5" fill="' + p.acc + '" opacity="0.5"/>';
      s += '<rect x="112" y="118" width="64" height="10" rx="5" fill="' + p.acc + '" opacity="0.3"/>';
      s += '<rect x="86" y="152" width="148" height="12" rx="6" fill="' + p.ink + '" opacity="0.7"/>';
      return s;
    },
    vehicle: function (p, R) {
      var s = "";
      s += '<path d="M58,128 L70,104 Q74,96 86,94 L118,90 L142,62 Q146,56 154,56 L196,56 Q204,56 208,62 L226,90 L254,96 Q266,98 266,110 L266,128 Z" fill="' + p.acc + '" opacity="0.9"/>';
      s += '<path d="M150,64 L192,64 L206,88 L138,88 Z" fill="' + p.bg[1] + '" opacity="0.85"/>';
      s += '<rect x="58" y="126" width="208" height="10" rx="5" fill="#141824"/>';
      s += '<circle cx="112" cy="140" r="20" fill="#141824" stroke="' + p.ink + '" stroke-width="4"/>';
      s += '<circle cx="112" cy="140" r="7" fill="' + p.acc + '"/>';
      s += '<circle cx="208" cy="140" r="20" fill="#141824" stroke="' + p.ink + '" stroke-width="4"/>';
      s += '<circle cx="208" cy="140" r="7" fill="' + p.acc + '"/>';
      return s;
    },
    tool: function (p, R) {
      var s = "";
      s += '<rect x="128" y="66" width="26" height="104" rx="13" transform="rotate(28 141 118)" fill="' + p.acc + '" opacity="0.92"/>';
      s += '<path d="M150,44 m-26,0 a26,26 0 1,0 44,18 L186,50 L168,68 Z" fill="' + p.acc + '" opacity="0.92"/>';
      s += '<circle cx="141" cy="196" r="10" fill="none" stroke="' + p.ink + '" stroke-width="5"/>';
      return s;
    },
    medical: function (p, R) {
      var s = '<rect x="102" y="42" width="116" height="116" rx="26" fill="' + p.acc + '" opacity="0.16" stroke="' + p.acc + '" stroke-width="6"/>';
      s += '<rect x="144" y="64" width="32" height="72" rx="6" fill="' + p.acc + '"/>';
      s += '<rect x="122" y="86" width="76" height="32" rx="6" fill="' + p.acc + '"/>';
      return s;
    },
    flask: function (p, R) {
      var s = '<rect x="146" y="34" width="28" height="34" fill="none" stroke="' + p.acc + '" stroke-width="6"/>';
      s += '<path d="M146,68 L104,152 L216,152 L174,68 Z" fill="' + p.acc + '" opacity="0.14" stroke="' + p.acc + '" stroke-width="6" stroke-linejoin="round"/>';
      s += '<path d="M118,124 Q140,116 160,124 T202,124 L216,152 L104,152 Z" fill="' + p.acc + '" opacity="0.75"/>';
      var b = [[140, 100, 6], [168, 90, 8], [154, 138, 5], [184, 132, 6]];
      for (var i = 0; i < b.length; i++)
        s += '<circle cx="' + b[i][0] + '" cy="' + b[i][1] + '" r="' + b[i][2] + '" fill="' + p.ink + '" opacity="0.85"/>';
      return s;
    },
    flow: function (p, R) {
      var s = "", xs = [48, 130, 212], i;
      for (i = 0; i < 3; i++) {
        s += '<rect x="' + xs[i] + '" y="76" width="60" height="46" rx="9" fill="' + (i === 1 ? p.acc : "#1c2230") + '" stroke="' + p.acc + '" stroke-width="3"/>';
        s += '<rect x="' + (xs[i] + 12) + '" y="88" width="36" height="6" rx="3" fill="' + (i === 1 ? "#141824" : p.ink) + '" opacity="0.8"/>';
        s += '<rect x="' + (xs[i] + 12) + '" y="100" width="24" height="6" rx="3" fill="' + (i === 1 ? "#141824" : p.ink) + '" opacity="0.5"/>';
      }
      s += '<line x1="108" y1="99" x2="126" y2="99" stroke="' + p.acc + '" stroke-width="4"/>';
      s += '<polygon points="126,91 138,99 126,107" fill="' + p.acc + '"/>';
      s += '<line x1="190" y1="99" x2="208" y2="99" stroke="' + p.acc + '" stroke-width="4"/>';
      s += '<polygon points="208,91 220,99 208,107" fill="' + p.acc + '"/>';
      return s;
    },
    gear: function (p, R) {
      var s = "", i, a, x1, y1;
      for (i = 0; i < 8; i++) {
        a = i * Math.PI / 4;
        x1 = CX + Math.cos(a) * 46; y1 = CY + Math.sin(a) * 46;
        s += '<rect x="' + (x1 - 9) + '" y="' + (y1 - 9) + '" width="18" height="18" rx="3" transform="rotate(' + (i * 45) + ' ' + x1 + ' ' + y1 + ')" fill="' + p.acc + '"/>';
      }
      s += '<circle cx="' + CX + '" cy="' + CY + '" r="42" fill="#1c2230" stroke="' + p.acc + '" stroke-width="5"/>';
      s += '<circle cx="' + CX + '" cy="' + CY + '" r="15" fill="' + p.bg[1] + '" stroke="' + p.acc + '" stroke-width="4"/>';
      return s;
    },
    device: function (p, R) {
      var s = '<rect x="112" y="44" width="96" height="118" rx="16" fill="#1c2230" stroke="' + p.acc + '" stroke-width="4"/>';
      s += '<rect x="124" y="60" width="72" height="56" rx="6" fill="' + p.acc + '" opacity="0.25"/>';
      s += '<rect x="132" y="70" width="56" height="7" rx="3.5" fill="' + p.ink + '" opacity="0.8"/>';
      s += '<rect x="132" y="82" width="38" height="7" rx="3.5" fill="' + p.ink + '" opacity="0.5"/>';
      s += '<circle cx="140" cy="138" r="10" fill="none" stroke="' + p.acc + '" stroke-width="4"/>';
      s += '<circle cx="180" cy="138" r="10" fill="' + p.acc + '" opacity="0.85"/>';
      s += '<rect x="148" y="36" width="24" height="7" rx="3.5" fill="' + p.acc + '"/>';
      return s;
    },
    draft: function (p, R) {
      var s = '<path d="M84,152 L84,52 L188,152 Z" fill="none" stroke="' + p.acc + '" stroke-width="6" stroke-linejoin="round"/>';
      s += '<line x1="84" y1="102" x2="136" y2="102" stroke="' + p.acc + '" stroke-width="3" stroke-dasharray="8 6" opacity="0.7"/>';
      s += '<rect x="196" y="66" width="16" height="72" rx="4" transform="rotate(38 204 102)" fill="' + p.ink + '" opacity="0.9"/>';
      s += '<polygon points="228,128 240,152 216,140" fill="' + p.acc + '"/>';
      s += '<circle cx="160" cy="98" r="66" fill="none" stroke="' + p.ink + '" stroke-width="2" stroke-dasharray="5 7" opacity="0.4"/>';
      return s;
    },
    food: function (p, R) {
      var s = '<path d="M96,128 A64,64 0 0 1 224,128 Z" fill="' + p.acc + '" opacity="0.9"/>';
      s += '<circle cx="160" cy="58" r="8" fill="' + p.acc + '"/>';
      s += '<rect x="84" y="128" width="152" height="10" rx="5" fill="' + p.ink + '" opacity="0.85"/>';
      s += '<path d="M120,100 Q140,84 160,100 T200,100" fill="none" stroke="' + p.bg[1] + '" stroke-width="4" opacity="0.6"/>';
      return s;
    },
    building: function (p, R) {
      var s = '<polygon points="160,40 238,96 222,96 222,156 98,156 98,96 82,96" fill="' + p.acc + '" opacity="0.9"/>';
      s += '<rect x="146" y="116" width="28" height="40" fill="' + p.bg[1] + '" opacity="0.85"/>';
      s += '<rect x="112" y="108" width="22" height="18" fill="' + p.ink + '" opacity="0.7"/>';
      s += '<rect x="186" y="108" width="22" height="18" fill="' + p.ink + '" opacity="0.7"/>';
      return s;
    },
    media: function (p, R) {
      var s = '<rect x="104" y="52" width="112" height="96" rx="18" fill="' + p.acc + '" opacity="0.16" stroke="' + p.acc + '" stroke-width="6"/>';
      s += '<polygon points="146,76 146,124 188,100" fill="' + p.acc + '"/>';
      s += '<rect x="104" y="156" width="112" height="8" rx="4" fill="' + p.ink + '" opacity="0.5"/>';
      return s;
    }
  };

  function wrapTitle(t) {
    var words = String(t || "").split(/\s+/), lines = [], cur = "";
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if ((cur + " " + w).trim().length > 26) { if (cur) lines.push(cur); cur = w; }
      else cur = (cur + " " + w).trim();
    }
    if (cur) lines.push(cur);
    if (lines.length > 2) { lines = lines.slice(0, 2); lines[1] += "…"; }
    return lines;
  }

  /* Full cover SVG. id = record id, title = record title, cat = category. */
  function svg(id, title, cat) {
    id = String(id || ""); title = String(title || ""); cat = String(cat || "");
    var h = hashStr(id), pal = PALS[h % PALS.length], R = rnd(h >> 4);
    var motif = motifFor(cat), art = PAINT[motif](pal, R);
    var gid = "cg" + (h % 1000003);
    var lines = wrapTitle(title), tsvg = "", ty = 198;
    for (var i = 0; i < lines.length; i++) {
      tsvg += '<text x="160" y="' + (ty + i * 22) + '" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="bold" font-size="18" fill="' + pal.ink + '">' + cEsc(lines[i]) + "</text>";
    }
    var bw = Math.min(300, id.length * 7.6 + 22);
    return '<svg viewBox="0 0 320 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cover art for ' + cEsc(title) + '">' +
      '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + pal.bg[0] + '"/><stop offset="1" stop-color="' + pal.bg[1] + '"/></linearGradient>' +
      '<pattern id="' + gid + 'p" width="20" height="20" patternUnits="userSpaceOnUse">' +
      '<path d="M20,0 H0 V20" fill="none" stroke="#ffffff" stroke-width="1" opacity="0.06"/></pattern></defs>' +
      '<rect width="320" height="240" fill="url(#' + gid + ')"/>' +
      '<rect width="320" height="240" fill="url(#' + gid + 'p)"/>' +
      art +
      '<rect x="0" y="170" width="320" height="70" fill="#000000" opacity="0.55"/>' +
      tsvg +
      '<rect x="10" y="10" width="' + bw + '" height="26" rx="13" fill="' + pal.acc + '"/>' +
      '<text x="' + (10 + bw / 2) + '" y="28" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="bold" font-size="12.5" fill="#141414">' + cEsc(id) + "</text>" +
      '<text x="310" y="26" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="10" letter-spacing="2" fill="' + pal.ink + '" opacity="0.75">SIGNATURE</text>' +
      "</svg>";
  }

  /* Lazy placeholder for card lists: painted when near the viewport. */
  function ph(id, title, cat) {
    return '<div class="covph" data-cov-id="' + cEsc(id) + '" data-cov-t="' + cEsc(title) +
      '" data-cov-c="' + cEsc(cat) + '" aria-hidden="true"></div>';
  }

  var obs = null;
  function paintEl(el) {
    if (!el || el.getAttribute("data-painted")) return;
    try {
      el.innerHTML = svg(el.getAttribute("data-cov-id"), el.getAttribute("data-cov-t"), el.getAttribute("data-cov-c"));
      el.setAttribute("data-painted", "1");
    } catch (e) { /* never break the list on a cover failure */ }
  }
  /* Observe all unpainted placeholders under root; call after each render(). */
  function paintAll(root) {
    var scope = root || document;
    var els = scope.querySelectorAll ? scope.querySelectorAll(".covph:not([data-painted])") : [];
    if (!els.length) return;
    if (typeof IntersectionObserver === "undefined") {
      for (var i = 0; i < els.length; i++) paintEl(els[i]);
      return;
    }
    if (!obs) {
      obs = new IntersectionObserver(function (entries) {
        for (var j = 0; j < entries.length; j++) {
          if (entries[j].isIntersecting) { paintEl(entries[j].target); obs.unobserve(entries[j].target); }
        }
      }, { rootMargin: "320px 0px" });
    }
    for (var k = 0; k < els.length; k++) obs.observe(els[k]);
  }

  return { svg: svg, ph: ph, paintAll: paintAll, motifFor: motifFor, palettes: PALS.length };
})();
