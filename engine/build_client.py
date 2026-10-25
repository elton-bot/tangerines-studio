#!/usr/bin/env python3
"""Build a paying client's site from its content file.

Usage: python3 engine/build_client.py clients/<slug>/site.json [out_dir]

Writes the whole site to <out_dir>/<slug>/ (default public/clients), served at
https://tangerinesstudio.com/clients/<slug>/ for review and, after launch, on the
client's own domain through a host rewrite in vercel.json. Prints the pages written.
Exits non-zero with "Site not valid: ..." on a bad content file.

The content file is the approved preview spec (same fields, see CLAUDE.md) plus:
  package       "one-page" or "full" (full = home plus up to 4 more pages)
  pages         full sites only: [{slug, title, nav?, label?, heading?, intro?, description?,
                sections: [...]}]. Section types: services, about, reviews, visit, contact
                (the same blocks as the homepage), text {heading, label?, paragraphs,
                items?, image?, image_alt?} and gallery {heading, intro?, images: [{url, alt}]}.
  form          false to leave out the contact form (default: on, posting to /api/contact)
  launched      true once the site is live on the client's domain (drops noindex)
  live_domain   the client's domain without www, e.g. "harborstreetauto.com"
  year          footer copyright year (default 2026); credit: false hides "Website by"
  seo_title, seo_description   the home page's title and description

Design comes from the theme; content lives only in site.json and clients/<slug>/img/,
so a care edit (text, hours, phone, photos) is a change to site.json and a rebuild.
clients/<slug>/refine.css is inlined on every page, like a preview's refine.css.
The form's recipient is never in this repo: it is the CLIENT_FORM_TO variable in Vercel.
"""
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_concept as rc  # noqa: E402

SECTION_TYPES = {"services", "about", "reviews", "visit", "contact", "text", "gallery"}


def validate_site(b: dict, folder: Path) -> list:
    problems = []
    if b.get("package") not in ("one-page", "full"):
        problems.append('package must be "one-page" or "full"')
    if not b.get("slug") or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", b["slug"]):
        problems.append("slug is required (lowercase letters, numbers and hyphens)")
    elif folder.name != b["slug"]:
        problems.append(f"slug {b['slug']} must match the folder name {folder.name}")
    if b.get("fictional"):
        problems.append("client sites are never fictional")
    pages = b.get("pages") or []
    if b.get("package") == "one-page" and pages:
        problems.append("a one-page site has no extra pages")
    if len(pages) > 4:
        problems.append("a full site has the homepage plus at most 4 pages")
    seen = set()
    for pg in pages:
        ps = pg.get("slug", "")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", ps) or ps in seen or ps in ("img", "fonts", "api"):
            problems.append(f"page slug {ps!r} must be unique, lowercase and not img, fonts or api")
        seen.add(ps)
        if not pg.get("title"):
            problems.append(f"page {ps} needs a title")
        if not pg.get("sections"):
            problems.append(f"page {ps} needs sections")
        for s in pg.get("sections") or []:
            if s.get("type") not in SECTION_TYPES:
                problems.append(f"page {ps}: unknown section type {s.get('type')!r}")
            if s.get("type") == "text" and not s.get("heading"):
                problems.append(f"page {ps}: text sections need a heading")
            if s.get("type") == "gallery" and not s.get("images"):
                problems.append(f"page {ps}: gallery sections need images")
    if b.get("launched") and not b.get("live_domain"):
        problems.append("launched sites need live_domain")
    if b.get("live_domain") and not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", b["live_domain"]):
        problems.append("live_domain must be a bare domain like example.com")
    return problems


def section_images(b: dict, out: Path, spec_dir: Path) -> list:
    """Download or copy the images used in page sections into img/."""
    notes = []
    (out / "img").mkdir(exist_ok=True)
    for pg in b.get("pages") or []:
        for si, s in enumerate(pg.get("sections") or []):
            s["id"] = f"{pg['slug']}-{si + 1}"
            entries = []
            if s.get("image"):
                entries.append((s, "image", s["image"]))
            for gi, g in enumerate(s.get("images") or []):
                entries.append((g, None, g.get("url", "")))
            new_images = []
            for n, (holder, key, url) in enumerate(entries):
                try:
                    if re.match(r"https?://", url):
                        data = rc.fetch_image(url)
                    else:
                        local = (spec_dir / url).resolve()
                        if not local.is_file():
                            raise RuntimeError("not a web address or a local file")
                        data = local.read_bytes()
                    info = rc.save_image(f"sec-{pg['slug']}-{si + 1}-{n + 1}_url", data, out / "img")
                    if key:
                        holder[key] = info
                    else:
                        new_images.append({**info, "alt": holder.get("alt", "")})
                    notes.append(f"{pg['slug']}: saved {info['src']} from {url}")
                except Exception as e:
                    if key:
                        holder[key] = None
                    notes.append(f"{pg['slug']}: dropped image ({e}) {url}")
            if s.get("images") is not None:
                s["images"] = new_images
    return notes


def build(site_path: str, out_dir: str) -> list:
    site_file = Path(site_path).resolve()
    folder = site_file.parent
    b = json.loads(site_file.read_text())
    problems = validate_site(b, folder)
    if problems:
        raise SystemExit("Site not valid: " + "; ".join(problems))
    try:
        theme, p = rc.prepare(b)
    except SystemExit as e:
        raise SystemExit(str(e).replace("Spec not valid", "Site not valid"))

    out = Path(out_dir) / b["slug"]
    if out.exists():
        shutil.rmtree(out)
    rc.prepare_dirs(out, theme)
    for note in rc.localize_images(b, out, folder) + section_images(b, out, folder):
        print(note, file=sys.stderr)
    rc.write_credits(b, out)
    refine = folder / "refine.css"
    refine_css = refine.read_text() if refine.is_file() else ""

    pages = b.get("pages") or []
    by_slug = {pg["slug"]: pg for pg in pages}
    env = rc.environment()
    written = []

    def nav_for(current, root):
        if not pages:
            return rc.one_page_nav(b)
        home = root or "./"
        nav = []
        if "services" not in by_slug:
            nav.append({"label": "Services", "href": f"{root}#services" if root else "#services"})
        for pg in pages:
            if pg["slug"] == "contact":
                continue
            nav.append({"label": pg.get("nav") or pg["title"], "href": f"{root}{pg['slug']}/", "current": pg["slug"] == current})
        nav.append({"label": "Contact", "href": f"{root}contact/" if "contact" in by_slug else (f"{root}#contact" if root else "#contact"),
                    "current": current == "contact"})
        return nav

    def contact_href(root):
        if "contact" in by_slug:
            return f"{root}contact/"
        return f"{root}#contact" if root else "#contact"

    html = rc.render_html(env, theme, b=b, p=p, mode="client", nav=nav_for(None, ""), root="",
                          contact_href=contact_href(""), home_href="#main", refine_css=refine_css)
    (out / "index.html").write_text(html)
    written.append(out / "index.html")
    for pg in pages:
        d = out / pg["slug"]
        d.mkdir()
        html = rc.render_html(env, theme, b=b, p=p, mode="client", page=pg, nav=nav_for(pg["slug"], "../"), root="../",
                              contact_href=contact_href("../"), home_href="../", refine_css=refine_css)
        (d / "index.html").write_text(html)
        written.append(d / "index.html")

    if b.get("launched"):
        base = f"https://{b['live_domain']}/"
        urls = [base] + [f"{base}{pg['slug']}/" for pg in pages]
        (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n")
        (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                         + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    else:
        (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    return written


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    root = Path(__file__).resolve().parent.parent
    for path in build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(root / "public" / "clients")):
        print(path)
