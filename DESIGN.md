# Design decisions

Binding for later jobs, next to CLAUDE.md. Update this file whenever a design decision changes.

## Studio site (tangerinesstudio.com), v4

Live at / since 25 Oct 2026, with /terms/, /privacy/ and /404.html. v4 keeps the v3 palette, type and components and changes the page structure: the offer is the headline, the work is on the first screen, and sections vary in layout instead of repeating one pattern.

### What a generic AI-made landing page looks like, and what we do instead

| Generic | Ours |
| --- | --- |
| Centered hero, gradient blob, "Grow your business" | The offer itself as the headline ("We build your new homepage first. Free."), left-aligned, with a sample site beside the copy on the first screen |
| Inter or a bookish free serif | One precise grotesk (Instrument Sans) in few sizes, tight tracking on display sizes |
| Three icon cards per section, every section equally loud | Typographic lists on hairline rules. Two loud moments only: the dark work band and the dark closing call to action. Sections between them change layout (stacked header, side header, ledger rows) so the page does not repeat one template |
| A stats band under the hero | Three quiet offer notes under the buttons, small type on hairlines |
| Stats band, logos, testimonials | None. Trust comes from the work, the process, the prices and the guarantees |
| Pricing as three cards with a "Most popular" badge | A price ledger: rows, tabular figures, one rule between items |
| Orange everywhere, colored header bar | Paper background, ink text. Tangerine only in the mark, the primary button and step numerals |
| Stock photo of a worker as the hero | Real screenshots of our sample sites in a quiet browser frame and phone frame |

### Palette

| Token | Value | Use |
| --- | --- | --- |
| --paper | #F5F3EE | Page background |
| --paper-2 | #ECE9E2 | Quiet panels (work frames, FAQ hover) |
| --ink | #16150F | Text, the dark work band background |
| --ink-2 | #4A4740 | Secondary text (8.4:1 on paper) |
| --rule | #D6D2C8 | Hairlines |
| --tangerine | #F26B1D | Mark, primary button background (button text is ink, 6.0:1) |
| --tangerine-ink | #A84508 | Orange text on paper when needed (5.4:1) |

Dark band (the work): background --ink, text #F5F3EE, secondary #B9B5AA.

### Type

- Instrument Sans variable (400 to 700), self-hosted at /fonts/instrument-sans.woff2, font-display swap. OFL.
- Display (hero h1): clamp(2.75rem, 5.9vw, 5.4rem), weight 500, letter-spacing -0.045em, line-height 0.98, max-width 15.5ch so it sets in two lines on desktop.
- Section titles (.h2): clamp(2rem, 3.8vw, 3.25rem), weight 500, -0.032em, line-height 1.04.
- Prices: clamp(2.75rem, 5vw, 4.25rem), weight 500, ink (never grey).
- Body 1.0625rem / 1.6. Small labels 0.8125rem, weight 600, letter-spacing 0.02em, sentence case (no all-caps eyebrows everywhere).
- Numbers use font-variant-numeric: tabular-nums.

### Layout

- Max width 1320px, 12-column grid, side padding clamp(20px, 5vw, 64px).
- Section rhythm: clamp(88px, 11vw, 152px). Section headers are a small label above the title, left-aligned. Two sections (Every site includes, Questions) put the header in a left column of 4 and the content in a right column of 7. Lists start with a 1px ink rule and separate rows with --rule hairlines.
- Header: wordmark left, four text links, one outlined pill "Free homepage". No background bar; it sits on paper and becomes sticky with a paper background and a hairline after scroll.
- Hero: label, then the headline across the page. Below it, the copy in 5 columns (paragraph, primary button, "See the work" link, three offer notes) and the Juniper Ridge desktop screenshot in a browser frame in the other 7, bleeding toward the right edge, with the Harbor Street phone screenshot over its lower right. A caption under it says these are sample designs for fictional businesses. On phones the composition follows the buttons and starts inside the first screen.
- Work: dark band. Header with the title on the left and the fictional-business note on the right. Each sample gets a row: desktop screenshot with the phone screenshot over its lower right, and a text column with "01 · Trade", a "Fictional business" tag, name, one-line description, "Design decisions for this trade" (three rows) and a link. The middle row is flipped (text left).
- How it works: four columns on desktop, each under a 1px ink rule with a big --tangerine-ink numeral. Stacked rows on phones.
- Pricing: --paper-2 band. A full-width ledger (name, price, description), then "Why it costs hundreds, not thousands" as a real heading with two paragraphs, and "What we don't build" in a side column.
- What you can count on: ledger rows, the promise in large type on the left and one supporting line on the right.
- Request: a reserved block with id="request" holds the email call to action today and the form from B-0003 later.
- Headshot: the "Who you're working with" block has a 4:5 frame (3 columns) holding a circle with the initials EA, and the caption "Elton Aclao, Tangerines Studio". Replace the span inside .frame with an img (object-fit cover) when Elton sends a photo; nothing else moves.
- Pages built from this look (previews, the request form from B-0003) reuse these tokens, the outlined pill, the orange primary button with ink text, the hairline lists and the dark band for one loud moment. Never a colored header bar, never orange as a background for a whole section.

### Assets

- Sample screenshots for the studio site: public/img/work/{juniper,northline,harbor}-desktop-{640,960,1440}.webp and -phone-{240,360,600}.webp, made with Playwright at 1440x900 and 390x844 (2x). Re-shoot them when a sample changes.
- Share image: public/img/og.jpg (1200x630): wordmark, the hero headline, the Juniper Ridge desktop and Harbor Street phone screenshots. Re-render it when the headline or the screenshots change. Favicons: public/favicon.svg, favicon-32.png, favicon.ico, apple-touch-icon.png.
- Asset URLs on studio pages are absolute (/img/, /fonts/) so the same files work from /review/ and from /. Page links are relative.

### Mark

public/favicon.svg: tangerine circle with a green leaf. The wordmark is the mark plus "Tangerines Studio" set in Instrument Sans 600.

## Sample sites (public/work/)

Each sample has its own identity. No orange in any sample. Shared rules: ribbon "Sample website by Tangerines Studio for a fictional business." at the top linking to https://tangerinesstudio.com/, disabled form with a sample note, sticky call bar on phones (under 760px), noindex meta plus the /work/ header. Every photo is listed with its Unsplash page URL in the sample's img/CREDITS.txt.

### Juniper Ridge Heating & Air (home services)
- Feel: sturdy, local, family. Evergreen and frost.
- Palette: pine #18352B, pine-2 #24493B, frost #DCEBF0, snow #F7F8F5, ink #14201B; accent ice blue #8CC3D6 on pine only.
- Type: Archivo (variable width and weight), self-hosted in the sample's fonts/ folder. All sample fonts are OFL, from Fontsource. Headlines semi-condensed 700; body 400.
- Ideas: phone number is the biggest thing after the headline; a "heating / cooling" split for services; hours table; town list as large type.
- Photos must look American: the hero is a US-style round outdoor condenser, the About photo a family room. No European heat pumps or Celsius thermostats.

### Northline Chiropractic (wellness)
- Feel: calm, unhurried, clinical without being cold.
- Palette: linen #F4F1EC, mist #E4E9E6, slate ink #1D2B30, sage #466760 (5.5:1 on linen), line #CDD3CF.
- Type: Newsreader for headings (light italic accents), Figtree for body.
- Ideas: lots of air, a thin vertical "north line" motif, first-visit steps, weekly hours as a simple week grid.
- The fictional doctor is Dr. Daniel Ellison, DC. Photos of the practitioner must stay consistent with that (one man, or hands only). The hero is a hands-only adjustment photo.

### Harbor Street Auto (auto repair)
- Feel: direct, shop-floor, high contrast.
- Palette: asphalt #121417, steel #23272D, concrete #E9E9E6, signal yellow #F3C316 (on dark only, or as a background with dark text).
- Type: Barlow Condensed 600/700 uppercase for headings, Barlow 400/600 body.
- Ideas: big "We call with a price before any work" promise, services as a numbered board, hours like a shop sign, address block with a drawn street map in SVG (no third-party map).

## Preview themes (engine/templates/, B-0002)

The free homepage previews start from one of three themes, each built from the matching sample so a preview is at the sample's standard. Same rules as the samples: no orange, the concept note at the very top ("Concept for {business} by Tangerines Studio. Not the official website."), a disabled form with a note, a call bar on phones under 760px, noindex. Palette tokens are per theme and can be overridden per business with palette in the spec; set them from the business's own logo when it has a clear brand color.

| Theme | From sample | Default tokens | Type | With no photo | With no logo |
| --- | --- | --- | --- | --- | --- |
| home | Juniper Ridge | main #18352B, tint #DCEBF0, accent #8CC3D6, bg #F7F8F5 | Archivo, condensed 800 headings | Full-width main-color hero, headline over 7 columns, a "Call us" panel with the phone and hours on the right, a faint roofline drawing along the bottom | Rounded initials tile with an accent base line, name in two lines (trade words on the small second line) |
| wellness | Northline | main #1D2B30, tint #E4E9E6, accent_text #466760, bg #F4F1EC | Newsreader headings, Figtree body | An arch-shaped tint panel in place of the arched photo, with "Call to book", the phone and hours | The thin vertical north line mark and the name in serif with the trade in small caps |
| auto | Harbor Street | main #121417, main2 #1E2227, accent #F3C316, bg #F6F6F4 | Barlow Condensed uppercase headings, Barlow body | Dark hero with the initials as a huge outlined letterform, a shop ticket with the phone and hours, and a yellow hazard stripe along the bottom | Yellow initials tag and the name in condensed caps; a logo sits on a small white plate on the dark header |

Section order: hero, facts strip (only from the business's own claims), services, reviews (only when quoted from their site, with "Quoted word for word from ..."), about, hours and area or location, contact with the disabled form, footer saying where the content came from. Services lay out in 3 columns (2 when there are exactly 4). Long headlines step down in size automatically (over 52 and over 80 characters).

Per-business identity comes from the hand pass: palette from their logo, their own kicker and section titles, image crops, and a refine.css beside the page for a signature detail. Never ship a theme's defaults unchanged when the business has a brand color of its own.
