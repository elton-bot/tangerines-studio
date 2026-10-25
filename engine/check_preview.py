#!/usr/bin/env python3
"""Check a rendered preview (or any page folder) before it ships.

Usage: python3 engine/check_preview.py <page_dir> [--out DIR] [--concept] [--root DIR] [--live]

<page_dir> is a folder with index.html, for example public/preview/<slug>.
Serves the folder (or the public/ folder it sits in) on a local port, opens it in Chromium at 390x844 and 1440x900,
saves full-page screenshots to --out (default /tmp/preview-check/<folder name>/:
mobile.png, desktop.png, mobile-top.png, desktop-top.png) and checks:

- no horizontal overflow at either width
- every image loads (naturalWidth > 0), has an alt attribute (text on previews) and width/height; no failed requests
- no leftover placeholders ({{, {%, TODO, lorem ipsum, None, undefined, PLACEHOLDER)
- no em or en dashes and no exclamation marks in the text, title, meta or alt text
- a noindex robots meta tag (not with --live, for launched client pages); exactly one h1; headings never skip a level
- for previews (path under preview/, or --concept): the note
  "Concept for {business} by Tangerines Studio. Not the official website." at the very top
  and no enabled form fields or submit buttons

Prints every problem and exits 1 if there is any, 0 when clean.
"""
import argparse
import functools
import http.server
import re
import socketserver
import sys
import threading
from pathlib import Path

PLACEHOLDERS = re.compile(r"\{\{|\{%|\bTODO\b|(?i:lorem ipsum)|\bPLACEHOLDER\b|\bundefined\b|\bNone\b|\bnull\b|\[object Object\]")
DASHES = re.compile(r"[–—]|&[mn]dash;|&#821[12];")

JS_COLLECT = """() => {
  const vis = document.body.innerText;
  const attrs = [];
  document.querySelectorAll('[alt],[title],[aria-label],[placeholder]').forEach(e => {
    ['alt','title','aria-label','placeholder'].forEach(a => { if (e.hasAttribute(a)) attrs.push(e.getAttribute(a)); });
  });
  document.querySelectorAll('meta[name=description],meta[property^=og]').forEach(m => attrs.push(m.content || ''));
  const imgs = [...document.images].map(i => ({src: i.currentSrc || i.src, ok: i.complete && i.naturalWidth > 0,
    alt: i.getAttribute('alt'), w: i.getAttribute('width'), h: i.getAttribute('height')}));
  const heads = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]);
  const robots = (document.querySelector('meta[name=robots]') || {}).content || '';
  const first = document.body.firstElementChild;
  const firstText = first ? first.innerText.trim() : '';
  const live = [...document.querySelectorAll('input,select,textarea,button[type=submit],button:not([type])')]
    .filter(e => !e.disabled && !e.closest('fieldset[disabled]')).length;
  return {vis, attrs, imgs, heads, robots, firstText, live, title: document.title,
    sw: document.documentElement.scrollWidth, iw: window.innerWidth};
}"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root: Path):
    handler = functools.partial(QuietHandler, directory=str(root))
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page_dir")
    ap.add_argument("--out")
    ap.add_argument("--concept", action="store_true", help="check the concept note even outside preview/")
    ap.add_argument("--root", help="serve this folder (the page must be inside it); default public/ when the page is in it")
    ap.add_argument("--live", action="store_true", help="a launched client page: no noindex expected")
    a = ap.parse_args()

    page = Path(a.page_dir).resolve()
    if not (page / "index.html").is_file():
        raise SystemExit(f"No index.html in {page}")
    out = Path(a.out) if a.out else Path("/tmp/preview-check") / page.name
    out.mkdir(parents=True, exist_ok=True)
    concept = a.concept or "preview" in page.parts
    problems = []

    html = (page / "index.html").read_text()
    bare = re.sub(r"<style.*?</style>|<script.*?</script>", "", html, flags=re.S)
    for m in PLACEHOLDERS.finditer(bare):
        problems.append(f"placeholder text in HTML: {bare[max(0, m.start() - 30):m.end() + 30]!r}")
    for m in DASHES.finditer(html):
        problems.append(f"em or en dash in HTML: {html[max(0, m.start() - 30):m.end() + 30]!r}")

    # serve from public/ when the page lives in it, so absolute links (/fonts/, /img/) resolve
    root, sub = page, ""
    if a.root:
        root = Path(a.root).resolve()
        sub = str(page.relative_to(root)).strip(".") + "/" if page != root else ""
    elif "public" in page.parts:
        i = len(page.parts) - 1 - page.parts[::-1].index("public")
        root = Path(*page.parts[:i + 1])
        sub = "/".join(page.parts[i + 1:]) + "/"
    httpd = serve(root)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/" + sub
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, w, h in (("mobile", 390, 844), ("desktop", 1440, 900)):
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg = ctx.new_page()
            failed = []
            pg.on("requestfailed", lambda r: failed.append(f"{r.url} ({r.failure})"))
            pg.on("response", lambda r: failed.append(f"{r.url} (HTTP {r.status})") if r.status >= 400 and r.url.startswith(url.split("/", 3)[0] + "//" + url.split("/", 3)[2]) else None)
            pg.goto(url, wait_until="networkidle")
            pg.screenshot(path=str(out / f"{name}-top.png"))
            # load lazy images before the full-page shot
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(400)
            pg.wait_for_load_state("networkidle")
            pg.evaluate("window.scrollTo(0, 0)")
            pg.wait_for_timeout(200)
            d = pg.evaluate(JS_COLLECT)
            pg.screenshot(path=str(out / f"{name}.png"), full_page=True)
            if d["sw"] > d["iw"]:
                problems.append(f"{name}: horizontal overflow ({d['sw']}px wide in a {d['iw']}px window)")
            for f in sorted(set(failed)):
                if "fonts.g" not in f:
                    problems.append(f"{name}: failed request {f}")
            if name == "mobile":
                for i in d["imgs"]:
                    if not i["ok"]:
                        problems.append(f"image did not load: {i['src']}")
                    if i["alt"] is None or (concept and not i["alt"].strip()):
                        problems.append(f"image without alt text: {i['src']}")
                    if not (i["w"] and i["h"]):
                        problems.append(f"image without width and height: {i['src']}")
                text = "\n".join([d["vis"], d["title"]] + d["attrs"])
                for m in re.finditer(r"!", text):
                    problems.append(f"exclamation mark: {text[max(0, m.start() - 40):m.end() + 10]!r}")
                for m in DASHES.finditer(text):
                    problems.append(f"em or en dash in text: {text[max(0, m.start() - 40):m.end() + 10]!r}")
                if not a.live and "noindex" not in d["robots"]:
                    problems.append("no noindex robots meta tag")
                if d["heads"].count(1) != 1:
                    problems.append(f"expected one h1, found {d['heads'].count(1)}")
                for prev, cur in zip(d["heads"], d["heads"][1:]):
                    if cur > prev + 1:
                        problems.append(f"heading level skips from h{prev} to h{cur}")
                        break
                if concept:
                    if not re.match(r"Concept for .+ by Tangerines Studio\. Not the official website\.", d["firstText"]):
                        problems.append(f"concept note missing at the top (found {d['firstText'][:80]!r})")
                    if d["live"]:
                        problems.append(f"{d['live']} form fields or buttons are enabled; previews only show a disabled form")
            ctx.close()
        browser.close()
    httpd.shutdown()

    print(f"Screenshots: {out}/mobile.png, desktop.png (full page), mobile-top.png, desktop-top.png")
    if problems:
        print(f"{len(problems)} problem(s) in {page}:")
        for pr in problems:
            print(" - " + pr)
        sys.exit(1)
    print(f"OK: {page}")


if __name__ == "__main__":
    main()
