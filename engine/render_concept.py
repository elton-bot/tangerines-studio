#!/usr/bin/env python3
"""Render a Tangerines Studio concept homepage from a JSON spec.

Usage: python3 engine/render_concept.py spec.json [out_dir]

Writes <out_dir>/<slug>/index.html plus img/ and fonts/. out_dir defaults to
public/preview, so the page is served at /preview/<slug>/. Prints the page path.
Exits non-zero with "Spec not valid: ..." on a bad spec.

Themes (engine/templates/<theme>.html.j2), picked by "theme" or "niche_palette":
  home      home services. Evergreen and frost, Archivo. Matches /work/juniper-ridge-heating-air/
  wellness  wellness practices. Linen and slate, Newsreader with Figtree. Matches /work/northline-chiropractic/
  auto      auto repair. Asphalt and signal yellow, Barlow. Matches /work/harbor-street-auto/
Each theme has a photo layout and a type-led layout for when there is no usable photo,
and sets the business name as a wordmark when there is no usable logo.

Truth rules the spec must follow (see CLAUDE.md):
- Every claim (facts, reviews, about text, hours, service area) comes from the
  business's own public pages, listed in "sources".
- Reviews are quoted verbatim from the business's own site, with the name as shown.
- No live forms: the templates only show a disabled form.
- Images come from the business's own site (or files the client sent). They are
  downloaded here and served from the page's img/ folder. An image that can't be
  fetched or isn't a real image is dropped, never guessed or worked around.

Hand refinement: a refine.css file in the page folder is never overwritten and is
inlined after the theme CSS on every render, so re-rendering keeps it.
"""
import colorsys
import io
import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

HERE = Path(__file__).resolve().parent

THEMES = {
    "home": {
        "main": "#18352B", "main2": "#24493B", "tint": "#DCEBF0", "accent": "#8CC3D6",
        "accent_text": "#18352B", "bg": "#F7F8F5", "ink": "#14201B", "ink2": "#46524C",
        "line": "#D3DBD6", "deep": "#0E1512",
    },
    "wellness": {
        "main": "#1D2B30", "main2": "#2E4148", "tint": "#E4E9E6", "accent": "#B9D0C9",
        "accent_text": "#466760", "bg": "#F4F1EC", "ink": "#1D2B30", "ink2": "#4D5A5E",
        "line": "#CDD3CF", "deep": "#1D2B30", "paper": "#FBFAF7",
    },
    "auto": {
        "main": "#121417", "main2": "#1E2227", "tint": "#E9E9E6", "accent": "#F3C316",
        "accent_text": "#121417", "bg": "#F6F6F4", "ink": "#121417", "ink2": "#4B5058",
        "line": "#C9CAC6", "deep": "#000000", "on_main_muted": "#B4B9C0",
    },
}
# Older specs gave a palette as primary/accent/surface. Map those onto theme tokens.
LEGACY_KEYS = {"primary": "main", "accent": "accent", "surface": "tint"}
FONTS = {
    "home": ["archivo.woff2"],
    "wellness": ["newsreader.woff2", "figtree.woff2"],
    "auto": ["barlow-condensed-700.woff2", "barlow-condensed-600.woff2", "barlow-400.woff2", "barlow-600.woff2"],
}

ICON_PHONE = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'

REQUIRED = ["business_name", "hero_title", "hero_sub", "services", "about", "sources"]
IMAGE_KEYS = ("logo_url", "hero_image_url", "about_image_url")
MAX_IMAGE_BYTES = 8_000_000
WIDTHS = (640, 1000, 1600)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
TRADE_WORDS = {
    "heating", "cooling", "air", "hvac", "plumbing", "plumbers", "plumber", "roofing", "roofers", "electric",
    "electrical", "landscaping", "lawn", "care", "cleaning", "services", "service", "chiropractic", "chiropractor",
    "physical", "therapy", "massage", "wellness", "clinic", "center", "auto", "automotive", "repair", "transmission",
    "transmissions", "brakes", "brake", "body", "shop", "collision", "tire", "tires", "garage", "&", "and", "co", "co.",
    "company", "inc", "inc.", "llc", "conditioning", "mechanical", "home", "pt", "spa", "studio", "motors",
}


# ---------- images ----------

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
                if r.status_code in (401, 403, 429):
                    break  # the site refused: never work around a refusal
                continue
            if len(r.content) > MAX_IMAGE_BYTES:
                last = "larger than 8 MB"
                continue
            return r.content
        except Exception as e:  # network or TLS error: try the next form of the URL
            last = type(e).__name__
    raise RuntimeError(last or "fetch failed")


def is_svg(data: bytes) -> bool:
    head = data[:1024].lstrip().lower()
    return head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in head


def svg_size(text: str):
    m = re.search(r'viewBox\s*=\s*"[\d.\-]+[\s,]+[\d.\-]+[\s,]+([\d.]+)[\s,]+([\d.]+)"', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    w = re.search(r'<svg[^>]*\bwidth\s*=\s*"([\d.]+)', text)
    h = re.search(r'<svg[^>]*\bheight\s*=\s*"([\d.]+)', text)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    return 3.0, 1.0


def save_image(key: str, data: bytes, img_dir: Path) -> dict:
    """Save one image and return {src, srcset, width, height}."""
    base = key.replace("_image_url", "").replace("_url", "")
    if is_svg(data):
        if key != "logo_url":
            raise RuntimeError("SVG is only used for logos")
        text = data.decode("utf-8", "replace")
        if re.search(r"<script|\bon[a-z]+\s*=|javascript:|<foreignObject", text, re.I):
            raise RuntimeError("SVG with script content")
        (img_dir / "logo.svg").write_bytes(data)
        w, h = svg_size(text)
        return {"src": "img/logo.svg", "srcset": "", "width": round(w), "height": round(h)}
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(data))
    im.load()
    if getattr(im, "is_animated", False):
        im.seek(0)
    im = ImageOps.exif_transpose(im)
    if key == "logo_url":
        im = im.convert("RGBA")
        bbox = im.getbbox()  # trim transparent padding so the logo sits on the baseline
        if bbox:
            im = im.crop(bbox)
        if im.height > 200:
            im = im.resize((max(1, round(im.width * 200 / im.height)), 200), Image.LANCZOS)
        im.save(img_dir / "logo.png", "PNG", optimize=True)
        return {"src": "img/logo.png", "srcset": "", "width": im.width, "height": im.height}
    if im.width < 600:
        raise RuntimeError(f"too small for a feature photo ({im.width}px wide)")
    im = im.convert("RGB")
    out = []
    for w in WIDTHS:
        if w > im.width and out:
            break
        ww = min(w, im.width)
        r = im if ww == im.width else im.resize((ww, round(im.height * ww / im.width)), Image.LANCZOS)
        name = f"{base}-{ww}.webp"
        r.save(img_dir / name, "WEBP", quality=78, method=6)
        out.append((name, ww))
    largest = out[-1][1]
    mid = out[1][0] if len(out) > 1 else out[0][0]
    return {
        "src": "img/" + mid,
        "srcset": ", ".join(f"img/{n} {w}w" for n, w in out),
        "width": largest,
        "height": round(im.height * largest / im.width),
    }


def localize_images(b: dict, page_dir: Path, spec_dir: Path) -> list:
    """Download (or copy, for local files) every image into img/ and replace the URL with image info."""
    notes = []
    img_dir = page_dir / "img"
    for key in IMAGE_KEYS:
        url = (b.get(key) or "").strip()
        b[key] = None
        if not url:
            continue
        try:
            img_dir.mkdir(parents=True, exist_ok=True)
            if re.match(r"https?://", url):
                data = fetch_image(url)
            else:
                local = (spec_dir / url).resolve()
                if not local.is_file():
                    raise RuntimeError("not a web address or a local file")
                data = local.read_bytes()
            b[key] = save_image(key, data, img_dir)
            notes.append(f"{key}: saved as {b[key]['src']} from {url}")
        except Exception as e:
            notes.append(f"{key}: dropped ({e}) {url}")
    return notes


# ---------- colors ----------

def _rgb(hex_: str):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(hex_: str) -> float:
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lighten(hex_: str, amount: float) -> str:
    r, g, b = _rgb(hex_)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, min(1, l + amount), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def build_palette(b: dict, theme: str) -> dict:
    p = dict(THEMES[theme])
    custom = dict(b.get("palette") or {})
    for old, new in LEGACY_KEYS.items():
        if old in custom and new not in custom:
            custom[new] = custom.pop(old)
    for k, v in custom.items():
        if k in p and isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            p[k] = v.upper()
    if "main" in custom and "main2" not in custom:
        p["main2"] = lighten(p["main"], 0.07)
    return p


def palette_warnings(p: dict, theme: str) -> list:
    checks = [("white text on main", "#FFFFFF", p["main"], 4.5), ("ink on bg", p["ink"], p["bg"], 4.5),
              ("ink2 on bg", p["ink2"], p["bg"], 4.5), ("accent on main", p["accent"], p["main"], 3.0)]
    if theme == "wellness":
        checks.append(("accent_text on bg", p["accent_text"], p["bg"], 4.5))
    return [f"palette: {name} contrast {contrast(a, c):.1f}:1 is below {need}:1"
            for name, a, c, need in checks if contrast(a, c) < need]


# ---------- text helpers ----------

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def phone_digits(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        digits = "1" + digits
    return "+" + digits if digits else ""


def split_name(name: str):
    """Split a business name into a wordmark: ("Juniper Ridge", "Heating & Air")."""
    words = name.split()
    i = len(words)
    while i > 1 and words[i - 1].lower().strip(",.") in TRADE_WORDS:
        i -= 1
    if i == len(words) or i == 0:
        return name, ""
    return " ".join(words[:i]), " ".join(words[i:])


def initials(name: str) -> str:
    main = split_name(name)[0]
    parts = [w for w in re.split(r"[\s\-]+", main) if w and w[0].isalnum()]
    return ("".join(w[0] for w in parts[:2]) or name[:1]).upper()


def site_domain(b: dict) -> str:
    for s in [b.get("website", "")] + list(b.get("sources") or []):
        m = re.match(r"https?://(?:www\.)?([^/]+)", s or "")
        if m:
            return m.group(1)
    return ""


def validate(b: dict) -> list:
    problems = [f"missing {k}" for k in REQUIRED if not b.get(k)]
    theme = b.get("theme") or b.get("niche_palette")
    if theme not in THEMES and not b.get("palette"):
        problems.append("niche_palette must be home, wellness or auto (or give a palette)")
    if b.get("theme") and b["theme"] not in THEMES:
        problems.append("theme must be home, wellness or auto")
    services = b.get("services") or []
    if len(services) < 3:
        problems.append("need at least 3 services")
    if any(not (isinstance(s, dict) and s.get("name")) for s in services):
        problems.append("every service needs a name")
    if isinstance(b.get("about"), str):
        b["about"] = [b["about"]]
    if not (b.get("phone") or b.get("email")):
        problems.append("need a phone or an email")
    for r in b.get("reviews", []) or []:
        if not (r.get("quote") and r.get("name")):
            problems.append("every review needs a verbatim quote and the name shown on their site")
    if b.get("reviews") and not b.get("reviews_source"):
        problems.append("reviews need reviews_source (where they were quoted from)")
    for h in b.get("hours", []) or []:
        if not (isinstance(h, dict) and h.get("days") and h.get("time")):
            problems.append("every hours row needs days and time")
    return problems


# ---------- render ----------

def prepare(b: dict) -> tuple:
    """Validate a spec and fill in derived fields. Returns (theme, palette)."""
    problems = validate(b)
    if problems:
        raise SystemExit("Spec not valid: " + "; ".join(problems))
    theme = b.get("theme") or (b.get("niche_palette") if b.get("niche_palette") in THEMES else "home")
    p = build_palette(b, theme)
    for w in palette_warnings(p, theme):
        print("warning: " + w, file=sys.stderr)
    b["phone_digits"] = phone_digits(b.get("phone", ""))
    wm = b.get("wordmark")
    if isinstance(wm, list) and wm:
        b["wm_main"], b["wm_sub"] = wm[0], (wm[1] if len(wm) > 1 else "")
    else:
        b["wm_main"], b["wm_sub"] = split_name(b["business_name"])
    b["initials"] = b.get("initials") or initials(b["business_name"])
    b["domain"] = site_domain(b)
    b["about"] = [x for x in b.get("about") or [] if x]
    b["facts"] = [x for x in b.get("facts") or [] if x][:4]
    b["service_area"] = [x for x in b.get("service_area") or [] if x]
    b["hours"] = b.get("hours") or []
    b["reviews"] = (b.get("reviews") or [])[:6]
    n = len(b["services"])
    b["svc_cols"] = 2 if n in (4,) else 3
    b["title_size"] = "long" if len(b["hero_title"]) > 80 else ("mid" if len(b["hero_title"]) > 52 else "short")
    if b.get("address"):
        from urllib.parse import quote_plus
        b["map_url"] = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{b['business_name']}, {b['address']}")
    b["visit_label"] = "Hours" if b["hours"] else ("Location" if b.get("address") else "Area")
    b["slug"] = b.get("slug") or slugify(f"{b['business_name']} {b.get('city', '')}")
    return theme, p


def one_page_nav(b: dict) -> list:
    nav = [{"label": "Services", "href": "#services"}, {"label": "About", "href": "#about"}]
    if b["hours"] or b.get("address") or b["service_area"]:
        nav.append({"label": b["visit_label"], "href": "#visit"})
    nav.append({"label": "Contact", "href": "#contact"})
    return nav


def prepare_dirs(page_dir: Path, theme: str) -> None:
    page_dir.mkdir(parents=True, exist_ok=True)
    img_dir = page_dir / "img"
    if img_dir.is_dir():  # stale images from an earlier render
        for f in img_dir.iterdir():
            if f.name != "CREDITS.txt" and re.match(r"(hero|about|logo|sec)[.-]", f.name):
                f.unlink()
    font_dir = page_dir / "fonts"
    if font_dir.is_dir():
        shutil.rmtree(font_dir)
    font_dir.mkdir()
    for f in FONTS[theme]:
        shutil.copy2(HERE / "fonts" / f, font_dir / f)


def write_credits(b: dict, page_dir: Path) -> None:
    if b.get("image_credits"):
        (page_dir / "img").mkdir(exist_ok=True)
        (page_dir / "img" / "CREDITS.txt").write_text("\n".join(b["image_credits"]) + "\n")


def environment() -> Environment:
    return Environment(loader=FileSystemLoader(str(HERE / "templates")), autoescape=select_autoescape(["html", "j2"]),
                       trim_blocks=True, lstrip_blocks=True)


def render_html(env: Environment, theme_name: str, **ctx) -> str:
    ctx.setdefault("icon_phone", ICON_PHONE)
    ctx.setdefault("page", None)
    ctx.setdefault("mode", "preview")
    ctx.setdefault("root", "")
    ctx.setdefault("refine_css", "")
    ctx.setdefault("theme", theme_name)
    html = env.get_template(f"{theme_name}.html.j2").render(**ctx)
    return re.sub(r"\n\s*\n+", "\n", html)


def render(spec_path: str, out_dir: str) -> Path:
    spec_file = Path(spec_path)
    b = json.loads(spec_file.read_text())
    theme, p = prepare(b)
    page_dir = Path(out_dir) / b["slug"]
    prepare_dirs(page_dir, theme)
    for note in localize_images(b, page_dir, spec_file.parent):
        print(note, file=sys.stderr)
    write_credits(b, page_dir)
    refine = page_dir / "refine.css"
    html = render_html(environment(), theme, b=b, p=p, mode="preview", nav=one_page_nav(b),
                       refine_css=refine.read_text() if refine.is_file() else "")
    (page_dir / "index.html").write_text(html)
    return page_dir / "index.html"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    path = render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(HERE.parent / "public" / "preview"))
    print(path)
