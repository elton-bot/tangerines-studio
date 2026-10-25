# Design decisions

Binding for later jobs, next to CLAUDE.md. Update this file whenever a design decision changes.

## Studio site (tangerinesstudio.com), v3

### What a generic AI-made landing page looks like, and what we do instead

| Generic | Ours |
| --- | --- |
| Centered hero, gradient blob, "Grow your business" | Left-aligned headline on a 12-column grid, plain words, and the work itself under it at large scale |
| Inter or a bookish free serif | One precise grotesk (Instrument Sans) in few sizes, tight tracking on display sizes |
| Three icon cards per section, every section equally loud | Typographic lists on hairline rules. Only two loud moments: the work and the closing call to action |
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
- Display: clamp(2.6rem, 6vw, 5.4rem), weight 500, letter-spacing -0.035em, line-height 1.02.
- Section titles: clamp(1.9rem, 3.4vw, 3rem), weight 500, -0.025em.
- Body 1.0625rem / 1.6. Small labels 0.8125rem, weight 600, letter-spacing 0.02em, sentence case (no all-caps eyebrows everywhere).
- Numbers use font-variant-numeric: tabular-nums.

### Layout

- Max width 1320px, 12-column grid, side padding clamp(20px, 5vw, 64px).
- Section rhythm: 128px top on desktop, 80px on phones. Each section starts with a hairline, a small label on the left 3 columns and the title on the right 9.
- Header: wordmark left, four text links, one outlined pill "Free homepage". No background bar; it sits on paper and becomes sticky with a paper background and a hairline after scroll.
- Hero: headline across 9 columns, a short paragraph and two actions, then a wide composition: Juniper Ridge desktop screenshot in a browser frame, Northline and Harbor Street phone screenshots overlapping its right edge.
- Work: dark band. Each sample gets a full-width row: big desktop screenshot, phone screenshot, name, trade, three design decisions, link.
- Request: a reserved block with id="request" holds the email call to action today and the form from B-0003 later.
- Headshot: the "Who you're working with" block has a 4:5 frame with the initials EA. Replace the inner element with an img (same frame, object-fit cover) when Elton sends a photo; nothing else moves.

### Assets

- Sample screenshots for the studio site: public/img/work/{juniper,northline,harbor}-desktop-{640,960,1440}.webp and -phone-{360,600}.webp, made with Playwright at 1440x900 and 390x844 (2x). Re-shoot them when a sample changes.
- Share image: public/img/og.jpg (1200x630). Favicons: public/favicon.svg, favicon-32.png, favicon.ico, apple-touch-icon.png.
- Asset URLs on studio pages are absolute (/img/, /fonts/) so the same files work from /review/ and from /. Page links are relative.

### Mark

public/favicon.svg: tangerine circle with a green leaf. The wordmark is the mark plus "Tangerines Studio" set in Instrument Sans 600.

## Sample sites (public/work/)

Each sample has its own identity. No orange in any sample. Shared rules: ribbon "Sample website by Tangerines Studio for a fictional business." at the top linking to https://tangerinesstudio.com/, disabled form with a sample note, sticky call bar on phones (under 760px), noindex meta plus the /work/ header.

### Juniper Ridge Heating & Air (home services)
- Feel: sturdy, local, family. Evergreen and frost.
- Palette: pine #18352B, pine-2 #24493B, frost #DCEBF0, snow #F7F8F5, ink #14201B; accent ice blue #8CC3D6 on pine only.
- Type: Archivo (variable width and weight), self-hosted in the sample's fonts/ folder. All sample fonts are OFL, from Fontsource. Headlines semi-condensed 700; body 400.
- Ideas: phone number is the biggest thing after the headline; a "heating / cooling" split for services; hours table; town list as large type.

### Northline Chiropractic (wellness)
- Feel: calm, unhurried, clinical without being cold.
- Palette: linen #F4F1EC, mist #E4E9E6, slate ink #1D2B30, sage #466760 (5.5:1 on linen), line #CDD3CF.
- Type: Newsreader for headings (light italic accents), Figtree for body.
- Ideas: lots of air, a thin vertical "north line" motif, first-visit steps, weekly hours as a simple week grid.

### Harbor Street Auto (auto repair)
- Feel: direct, shop-floor, high contrast.
- Palette: asphalt #121417, steel #23272D, concrete #E9E9E6, signal yellow #F3C316 (on dark only, or as a background with dark text).
- Type: Barlow Condensed 600/700 uppercase for headings, Barlow 400/600 body.
- Ideas: big "We call with a price before any work" promise, services as a numbered board, hours like a shop sign, address block with a drawn street map in SVG (no third-party map).
