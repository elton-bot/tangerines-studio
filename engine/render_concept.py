#!/usr/bin/env python3
"""Render a Tangerines Studio concept homepage from a JSON spec.

Usage: python3 engine/render_concept.py spec.json [out_dir]

out_dir defaults to public/preview, so the page is served at /preview/<slug>/.

Rules the spec must follow (checked below):
- Every claim (facts, reviews, about text, hours, service area) comes from the
  business's own public pages, listed in "sources".
- Reviews are quoted verbatim from the business's own site, with the name as shown.
- No live forms: the template only shows a disabled preview.
- Images (logo_url, hero_image_url) are downloaded from the business's own site and
  served from the concept folder (img/), so http-only or broken-https sites still show
  them. An image that can't be fetched or isn't a real image is dropped, never guessed.
"""
import io
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

HERE = Path(__file__).resolve().parent

PALETTES = {
    "home": {"primary": "#12395B", "primary_ink": "#FFFFFF", "accent": "#F5A524", "accent_ink": "#1A1A1A", "surface": "#F3F6F9"},
    "wellness": {"primary": "#1F4D4A", "primary_ink": "#FFFFFF", "accent": "#9ED3C4", "accent_ink": "#10302D", "surface": "#F2F7F6"},
    "auto": {"primary": "#1D232A", "primary_ink": "#FFFFFF", "accent": "#C9352A", "accent_ink": "#FFFFFF", "surface": "#F4F4F2"},
}

ICON_PHONE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="currentColor" opacity="0.18"/><path d="M7 12.5l3.2 3.1L17 9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'

REQUIRED = ["business_name", "niche_palette", "hero_title", "hero_sub", "services", "about", "sources"]
IMAGE_KEYS = ("logo_url", "hero_image_url")
MAX_IMAGE_BYTES = 8_000_000
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"


def fetch_image(url: str) -> bytes:
    import requests
    tries = [url]
    if url.startswith("https://"):
        tries.append("http://" + url[len("https://"):])
    last = None
    for u in tries:
        try:
            r = requests.get(u, headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
            if r.status_code != 200:
                last = f"HTTP {r.status_code}"
                continue
            if len(r.content) > MAX_IMAGE_BYTES:
                last = "larger than 8 MB"
                continue
            return r.content
        except Exception as e:  # network or TLS error: try the next form of the URL
            last = type(e).__name__
    raise RuntimeError(last or "fetch failed")


def save_image(key: str, data: bytes, img_dir: Path) -> str:
    head = data[:512].lstrip().lower()
    if head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in head:
        text = data.decode("utf-8", "replace")
        if re.search(r"<script|\bon[a-z]+\s*=|javascript:", text, re.I):
            raise RuntimeError("SVG with script content")
        name = key.replace("_url", "") + ".svg"
        (img_dir / name).write_bytes(data)
        return name
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    im.load()
    if getattr(im, "is_animated", False):
        im.seek(0)
    if key == "logo_url":
        im = im.convert("RGBA")
        if im.height > 240:
            im = im.resize((max(1, round(im.width * 240 / im.height)), 240), Image.LANCZOS)
        name = "logo.png"
        im.save(img_dir / name, "PNG", optimize=True)
    else:
        if im.width < 600:
            raise RuntimeError(f"too small for a hero photo ({im.width}px wide)")
        im = im.convert("RGB")
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        name = "hero.jpg"
        im.save(img_dir / name, "JPEG", quality=82, optimize=True, progressive=True)
    return name


def localize_images(b: dict, page_dir: Path) -> list:
    notes = []
    img_dir = page_dir / "img"
    for key in IMAGE_KEYS:
        url = (b.get(key) or "").strip()
        if not url or url.startswith("img/"):
            continue
        if not re.match(r"https?://", url):
            notes.append(f"{key}: dropped (not a web address)")
            b[key] = ""
            continue
        try:
            img_dir.mkdir(parents=True, exist_ok=True)
            b[key] = "img/" + save_image(key, fetch_image(url), img_dir)
            notes.append(f"{key}: saved as {b[key]} from {url}")
        except Exception as e:
            notes.append(f"{key}: dropped ({e}) {url}")
            b[key] = ""
    return notes


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def phone_digits(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        digits = "1" + digits
    return "+" + digits if digits else ""


def validate(b: dict) -> list:
    problems = [f"missing {k}" for k in REQUIRED if not b.get(k)]
    if b.get("niche_palette") not in PALETTES and not b.get("palette"):
        problems.append("niche_palette must be home, wellness or auto (or give a palette)")
    if len(b.get("services", [])) < 3:
        problems.append("need at least 3 services")
    if not (b.get("phone") or b.get("email")):
        problems.append("need a phone or an email")
    for r in b.get("reviews", []) or []:
        if not (r.get("quote") and r.get("name")):
            problems.append("every review needs a verbatim quote and the name shown on their site")
    if b.get("reviews") and not b.get("reviews_source"):
        problems.append("reviews need reviews_source (where they were quoted from)")
    return problems


def render(spec_path: str, out_dir: str) -> Path:
    b = json.loads(Path(spec_path).read_text())
    problems = validate(b)
    if problems:
        raise SystemExit("Spec not valid: " + "; ".join(problems))
    b["phone_digits"] = phone_digits(b.get("phone", ""))
    palette = b.get("palette") or PALETTES[b["niche_palette"]]

    out = Path(out_dir)
    slug = b.get("slug") or slugify(f"{b['business_name']} {b.get('city', '')}")
    page_dir = out / slug
    page_dir.mkdir(parents=True, exist_ok=True)
    for note in localize_images(b, page_dir):
        print(note, file=sys.stderr)

    env = Environment(loader=FileSystemLoader([str(HERE / "templates"), str(HERE)]), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template("concept.html.j2").render(b=b, p=palette, icon_phone=ICON_PHONE, icon_check=ICON_CHECK)
    (page_dir / "index.html").write_text(html)
    return page_dir / "index.html"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    path = render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(HERE.parent / "public" / "preview"))
    print(path)
