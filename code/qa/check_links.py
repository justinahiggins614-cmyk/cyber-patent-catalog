#!/usr/bin/env python3
"""QA: link audit for the catalog site.

Fetches (GET, following redirects) every nav link in the built index.html,
the cross-site deep-link handlers referenced per record (JAH Wiki ?page=PAT:,
JAH-N ?dossier=, Spec Catalog specs.html), the record full-text host
(patents.google.com, sampled), and the sitemap/robots/api data files.
Reports any non-2xx/3xx final status as a finding. No browser needed.
Exit 0 = all live, 1 = findings.
"""
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fails = []


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "JAH-QA-linkcheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.url
    except urllib.error.HTTPError as e:
        # Google throttles scripted fetches; one polite retry separates a
        # throttled-but-live link from a genuinely dead one.
        if e.code in (429, 503):
            import time
            time.sleep(20)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r2:
                    return r2.status, r2.url
            except Exception as e2:
                return "ERR %s (after retry)" % e2, url
        return "ERR %s" % e, url
    except Exception as e:
        return "ERR %s" % e, url


def check(name, url, must_contain=None):
    status, final = fetch(url)
    ok = isinstance(status, int) and status < 400
    body_ok = True
    if ok and must_contain:
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(final, headers={"User-Agent": "JAH-QA-linkcheck/1.0"}),
                    timeout=25) as r:
                body_ok = must_contain.encode() in r.read(200000)
        except Exception:
            body_ok = False
    good = ok and body_ok
    print(("PASS " if good else "FAIL ") + "%s -> %s (%s)" % (name, final, status))
    if not good:
        fails.append(name)


def main():
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    nav = re.findall(r'<a href="(https://justinahiggins614-cmyk\.github\.io/[^"]+)"', html)
    print("nav links found: %d" % len(nav))
    for u in nav:
        check("nav " + u.rsplit("/", 2)[-2][:40], u)

    # cross-site per-record deep-link handlers (sampled with a real record id)
    sample = "US7654321B2"
    check("wiki ?page=PAT: handler",
          "https://justinahiggins614-cmyk.github.io/jah-wiki/?page=PAT:" + sample,
          must_contain="html")
    check("leaks ?dossier= handler",
          "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/?dossier=" + sample,
          must_contain="html")

    # record full-text host (sampled)
    check("google patents record link",
          "https://patents.google.com/patent/" + sample + "/")

    # data + plumbing files served by this site
    base = "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/"
    for rel in ("robots.txt", "sitemap.xml", "sitemap-index.xml", "api.json", "data/meta.json"):
        check("self " + rel, base + rel)

    # ?patent= deep link on this site resolves
    check("self ?patent= deep link", base + "?patent=" + sample, must_contain="html")

    print("links: %d finding(s)" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
