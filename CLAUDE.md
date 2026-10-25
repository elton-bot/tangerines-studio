# Tangerines Studio websites

Every website Tangerines Studio publishes lives in this repo: the studio site (tangerinesstudio.com), sample sites, the free homepage previews sent to prospects, and paying clients' sites. Claude Code designs and builds all of it, front end and back end, as the studio's website builder. Elton Aclao runs the studio and approves anything that changes the studio site. A separate operations run handles prospecting, every email to prospects and clients, payments and the pipeline. It queues website jobs for the builder and never edits site code.

Read this file in full before any work. It is binding.

## Map

| Path | What it is |
| --- | --- |
| public/ | Everything Vercel serves |
| public/index.html, public/img/, public/fonts/ | The studio site (screenshots of the samples in public/img/work/) |
| public/work/{slug}/ | Sample sites for fictional businesses (photos in img/) |
| public/preview/{slug}/ | Free homepage previews for real businesses |
| public/review/{name}/ | Review copies of studio-site changes waiting for Elton's approval |
| public/clients/{slug}/ | Paying clients' sites, built from clients/{slug}/ (see Client sites). Never edit by hand |
| clients/{slug}/ | Each client's content: site.json, img/, refine.css |
| api/ | Vercel Functions: request.js (studio request form), contact.js (client contact forms), _lib/mail.js |
| engine/ | Preview builder: render_concept.py, check_preview.py, templates/ (themes), fonts/, samples/ (specs and test images) |
| tools/render_emails.py | Used by the operations run for outreach email. Don't change it. |
| vercel.json | Output directory, headers, rewrites |
| DESIGN.md | Design decisions for the studio site and each sample. Read it before visual work |

## Hosting and deploys

- Vercel project tangerines-studio on Elton's Pro team, connected to this repo. A push to main deploys production in about a minute. Domains: tangerinesstudio.com, and www.tangerinesstudio.com redirecting to it.
- Check a deploy at https://tangerines-studio.vercel.app/{path}. It serves the same content as the live domain, and some networks block the custom domain.
- outputDirectory is public and there is no build command and no package.json. Pages are static; the only server code is two Vercel Functions in api/ (Node, no npm packages, so a plain push still deploys everything). See Back end below.
- DNS and email for tangerinesstudio.com are at DreamHost. Never change DNS, mail records or any account setting (Vercel, Stripe, Google, DreamHost, GitHub). Write what's needed in the job notes for Elton instead.
- Other runs push to main too. Always `git pull --rebase origin main` right before `git push origin main`, and stage only the paths your job changed.
- Studio-site changes go to public/review/{name}/ first (noindex, with links that work from there) and replace the live pages only after Elton approves. Samples, previews and client review pages publish directly to their own paths.
- Keep design decisions (palettes, type, components, themes) in DESIGN.md so later jobs stay consistent.

## Job types (queued by the operations run)

- studio: changes to the studio site, samples, engine or back end, as described in the job.
- preview: a free homepage for a business that said yes. Research their own site and build public/preview/{slug}/ (slug = business-city, lowercase, hyphens).
- client: a paying client's site, from their approved preview and the content they emailed.
- revision: changes a prospect or client asked for on their preview or site.
- care: an edit on a live client site under the care plan.
- launch: connect a client's domain to their site.
- takedown: remove a preview or site.

## Truth rules (previews and client sites)

1. Every fact on the page comes from the business's own website or from what the client sent: services, years, areas, hours, phone, email, address, team names, credentials.
2. Reviews and testimonials appear only when quoted word for word from the business's own site, with the name as shown there and a note saying where they were quoted from. Never write, shorten or improve a review.
3. Images come only from the business's own site or from files the client sent. They're downloaded at build time and served from the page's img/ folder. If their site refuses a request, leave that image out and never work around the refusal. Stock photos only when a client asks for them in writing, and only free-license ones (Unsplash free license, not Unsplash+).
4. Previews carry a visible note at the very top: "Concept for {business} by Tangerines Studio. Not the official website." They have no live forms (a disabled form with a note is fine), a noindex meta tag, and the noindex header for /preview/.
5. Nothing invented: no numbers, awards, guarantees, prices or claims the business doesn't make itself.
6. A business can ask for its preview to be taken down at any time. Takedown jobs come first.

## Preview command (contract with the operations run)

`python3 engine/render_concept.py <spec.json> [out_dir]` writes `<out_dir>/<slug>/index.html` plus `img/` and `fonts/`. out_dir defaults to public/preview. It prints the page path, and exits non-zero with "Spec not valid: ..." on a bad spec. Needs Python 3 and `pip install --break-system-packages jinja2 pillow requests`.

The spec format is engine/samples/juniper-ridge.json. Required: business_name, niche_palette (home, wellness or auto) or palette, hero_title, hero_sub, services (3 or more, each {name, text}), about (paragraphs), sources (pages used). Optional: slug, city, phone, email, address, facts, services_title, services_intro, about_title, hours (each {days, time}), service_area, logo_url, hero_image_url, hero_image_alt, reviews (each {quote, name}) with reviews_source.

Optional fields added in B-0002 (all safe to leave out): theme (home, wellness or auto; defaults to niche_palette), palette (theme tokens main, main2, tint, accent, accent_text, bg, ink, ink2, line, deep; the old primary, accent and surface keys still work), kicker (the small line above the headline; defaults to city), wordmark ([main, sub] to override how the name is split), initials, about_image_url and about_image_alt, hero_image_position (CSS object-position), cta_label, contact_title, contact_text, hours_note, reviews_title, website, image_credits (lines written to img/CREDITS.txt), fictional (true adds "A fictional business" to the top note; only for samples and tests).

Image URLs can be web addresses (downloaded at render time; a 401, 403 or 429 is a refusal and the image is dropped, never retried another way) or paths relative to the spec file (for files a client sent). Photos are saved as hero-/about- 640, 1000 and 1600 WebP; logos as PNG (trimmed, 200px tall) or a script-free SVG. The renderer warns on stderr when a custom palette fails contrast (white on main or ink on bg under 4.5:1).

Keep this command and these fields working, with any new fields optional, so a preview can always be produced from a spec, even when a job also refines the page by hand. If you change it, update this section in the same commit.

### Themes

engine/templates/home.html.j2, wellness.html.j2 and auto.html.j2 (shared parts in _base.html.j2 and _macros.html.j2), each drawn from the matching sample in public/work/. Fonts are copied from engine/fonts/ into each preview's fonts/ folder (OFL, from Fontsource). Every theme has a photo layout and a type-led layout for when there is no usable hero photo, and sets the name as a wordmark (a small theme mark plus the name in two lines) when there is no usable logo. Design details are in DESIGN.md under "Preview themes".

### Check command

`python3 engine/check_preview.py <page_dir> [--out DIR] [--concept]` serves the page locally, takes full-page and first-screen screenshots at 390x844 and 1440x900 (default /tmp/preview-check/<folder>/), and exits 1 with a list of problems: horizontal overflow, images that fail to load or lack alt text or width and height, failed requests, leftover placeholders, em or en dashes, exclamation marks, no noindex meta, not exactly one h1, skipped heading levels, and for previews (any path under preview/, or --concept) a missing concept note at the top or any enabled form field. Run it on every preview before pushing and look at the screenshots.

### How a preview job combines the engine with hand refinement

1. Research their own site and write specs/{slug}.json (gitignored) with only what their pages say. Pick the theme by trade. When their logo has a clear brand color, set palette.main (and accent) from it, keeping the contrast the renderer checks.
2. Render with the engine. It does the layout, images, fonts, noindex, the concept note and the disabled form.
3. Refine for this business so it does not look like the template recolored: wording, section titles, kicker, service order and image crops in the spec; anything visual (a signature element from their trade or logo, spacing, a different hero crop) in public/preview/{slug}/refine.css, which the renderer never overwrites and inlines on every render. Edit index.html by hand only for structural changes the theme cannot do, and then do not re-render that page.
4. Run the check command, look at both screenshots, fix, push only public/preview/{slug}/.

## Back end (forms)

- api/_lib/mail.js sends mail through DreamHost SMTP over SSL (smtp.dreamhost.com, port 465) with a small built-in client, plus shared validation, a per-instance rate limit (5 posts per 15 minutes per IP), a same-origin check and a honeypot field named company. Files under api/_lib are not served.
- Environment variables, set by Elton in Vercel (Project tangerines-studio, Settings, Environment Variables, Production and Preview), never committed: SMTP_USER (the DreamHost mailbox that sends, for example forms@tangerinesstudio.com; mail goes out From this address), SMTP_PASS (its password), optional SMTP_HOST and SMTP_PORT, optional REQUEST_TO (defaults to elton@tangerinesstudio.com), and CLIENT_FORM_TO for client forms (below). A new or changed variable needs a redeploy to take effect.
- /api/request/ (studio form; always call the functions with the trailing slash, because trailingSlash in vercel.json redirects the bare path): GET answers {"enabled": true} once SMTP_USER and SMTP_PASS exist. POST takes name, business, website, email, phone (optional), message (optional) as JSON or a normal form post, and emails elton@tangerinesstudio.com with the subject "Website request: {business name}", a plain text body with one field per line, and Reply-To set to the requester. Errors come back as JSON with a field list, or with fallback: true when sending is not possible.
- The studio page keeps the email link as the fallback: the form stays hidden until GET /api/request says enabled, and any failed send shows "Write the email instead".
- /api/contact (client sites): POST with the site's slug. The recipient comes from CLIENT_FORM_TO, a JSON object in Vercel such as {"harbor-street-auto-port-lewis": {"to": "owner@theirdomain.com", "name": "Harbor Street Auto"}}. Elton adds each client's line when their site goes up for review (the operations run gives him the address); the address never goes in this repo. Subject "Website message from {name}", Reply-To the visitor when they gave an email. Until the slug is in CLIENT_FORM_TO the form answers "Please call or email instead".
- To test locally without real mail, run the functions with a fake SMTP server (any TLS server on a local port with SMTP_HOST=localhost and NODE_TLS_REJECT_UNAUTHORIZED=0). Never put real credentials in a test.
- vercel.json sets security headers on every path (nosniff, referrer policy, frame options, HSTS, a permissions policy and a Content Security Policy that allows only this site's own files, inline styles and scripts, and data: images; adding any third-party script, font or embed means updating the CSP), long caching for fonts (1 year, immutable) and images (30 days for the studio and samples, 1 day for previews, reviews and client sites, since those change in place), and X-Robots-Tag noindex for /preview/, /work/, /review/, /clients/ and /api/.

## Client sites

Decision: one Vercel project (tangerines-studio) serves every client site, with a host-based rewrite per client in vercel.json. Why: one repo and one push deploy all sites; the forms, headers and engine are shared; Elton's Pro team allows many domains on one project; and nothing new has to be created in Vercel per client except the domain itself. A project per client would mean a new project, settings and environment variables for every client, all done by hand by Elton.

How a client site is made:
1. Input (the operations run collects it from the client's emails and puts it in the client job): the client's approved preview (its slug), the package (one-page or full), the domain they own, the email address the form should send to (it goes to Elton for CLIENT_FORM_TO, not into the repo), any text changes, extra pages and what goes on them for the full site (up to 5 pages in all), photos as attachments or links, and anything they want left out. Facts still come only from them or their own site.
2. Content: clients/{slug}/site.json is the approved preview spec (copy specs/{slug}.json, and copy public/preview/{slug}/refine.css to clients/{slug}/refine.css) plus package, pages, live_domain and launched. Photos the client sent go in clients/{slug}/img/ and are referenced by relative path. The fields and section types are in engine/build_client.py; engine/samples/stonebridge-demo/site.json is a full example.
3. Build: `python3 engine/build_client.py clients/{slug}/site.json` writes public/clients/{slug}/ (home plus one folder per page), with no concept note, a live form posting to /api/contact, "Website by Tangerines Studio" in the footer, robots noindex and a robots.txt that disallows everything until launch. Check every page with `python3 engine/check_preview.py public/clients/{slug}/{page}` and look at the screenshots.
4. Review: https://tangerinesstudio.com/clients/{slug}/ (noindex by header and meta, not linked anywhere). Care edits are a change to site.json (or img/) and a rebuild, never a hand edit of public/clients/.
5. Launch (launch job): set "launched": true and "live_domain" in site.json and rebuild (this drops noindex, adds canonical links, robots.txt and sitemap.xml for their domain). Add this rule to "rewrites" in vercel.json, with their domain:
   {"source": "/:path((?!api/).*)", "has": [{"type": "host", "value": "(www\\.)?theirdomain\\.com"}], "destination": "/clients/{slug}/:path"}
   Push, then set the job to blocked with notes_for_ops for Elton: "Pep: in Vercel, project tangerines-studio, Settings, Domains, add theirdomain.com and www.theirdomain.com (set www to redirect to theirdomain.com), and add their form address to CLIENT_FORM_TO." Vercel then shows the exact DNS records for each domain.
6. DNS the client adds at their registrar (the operations run emails these; the values Vercel shows in Domains win if they differ): for theirdomain.com an A record with host @ and value 76.76.21.21, and for www a CNAME with host www and value cname.vercel-dns.com. They remove any other A or AAAA record on @ and any other www record. They do not touch MX, TXT or any email records, so their email keeps working. After DNS is live Vercel issues the certificate on its own; check https://theirdomain.com/ loads the site and the form sends, then set the job to done.
7. Takedown of a client site: remove its rewrite, its folder in public/clients/ and clients/, and ask Elton (notes_for_ops) to remove the domain and its CLIENT_FORM_TO line.

## Business facts (the only source for studio copy)

- Tangerines Studio designs and builds websites for US local service businesses: home services (HVAC, plumbing, roofing, landscaping and lawn care, house cleaning), wellness practices (chiropractic, physical therapy, massage) and auto repair (general repair, transmission, brakes, body shops). Owner-run, single-location businesses.
- Run by Elton Aclao. New projects: elton@tangerinesstudio.com. Client support: support@tangerinesstudio.com. Mailing address: 30 N Gould St, STE R, Sheridan, WY 82801, USA.
- The new homepage comes first and is free, ready within a day, built from the business's own logo, photos and services. No calls: everything is by email, so every answer and price is in writing.
- One-page site $297. Full site, up to 5 pages, $497 (launch price for the first 10 clients). The full site is ready for review within 3 business days of getting the client's content.
- Care plan after launch: $49 a month or $490 a year for hosting, security and small edits by email, done within 2 business days. Cancel anytime and keep the site files.
- Refunds: the homepage preview is free. Once the finished site has been handed over, payments are non-refundable. Care plan payments aren't refunded, but the plan can be cancelled anytime with no further charges.
- Payment by card through Stripe. The client's domain and email stay theirs; only the website records change at launch.
- Out of scope: online stores, booking systems, member logins, more than 5 pages.

## Content rules (every page in this repo)

- Plain English, short sentences. No em dashes or en dashes in any copy. No exclamation marks.
- Don't pitch AI on any site. Elton: "These days, nobody likes AI does everything."
- The studio is new. Never invent testimonials, reviews, ratings, client logos, client counts, stats, awards, years in business, team size or results for the studio. Trust comes from the work, the process, the prices and the guarantees.
- Sample sites are for fictional businesses and say so in a ribbon at the top. Use 555 phone numbers and example.com addresses.
- Prices, timings and policies exactly as above. Changing them is Elton's call.
- Never mention any other company or brand of Elton's on any site.
- Record where every stock photo came from in img/CREDITS.txt next to it.

## Quality bar

- It must look like an established, premium studio made it. Two earlier studio designs were rejected: "It doesn't look premium AND feels like a plaything only" and "This seems like a newbie made this. How can we be trusted if this is our website?"
- Each sample site and each preview has its own identity drawn from the business and its trade, not one template recolored.
- Responsive from 360px to 1440px and wider, no horizontal scroll, visible keyboard focus, prefers-reduced-motion respected, text contrast at least 4.5:1, headings in order, alt text on every image.
- Lighthouse on mobile: 95 or better for performance, accessibility, best practices and SEO on the studio site and samples. Previews and client sites as close as their source images allow.
- Images sized and compressed, width and height set, lazy below the fold. Fonts self-hosted or loaded with display=swap.
- Before every push that changes how a page looks: Playwright screenshots at 390x844 and 1440x900 (full page too), and look at them. After the deploy, load the vercel.app URL and check the change is live.

## Repo hygiene

- This repo is public until Elton makes it private: no secrets, no prospect or client email addresses or private content, no internal business documents. Secrets go in Vercel environment variables, which Elton sets.
- .gitignore keeps specs/ and .private/ out. Keep it that way.
- Only the studio site goes in search: noindex for /preview/, /work/, /review/ and client review paths (header and meta tag), and sitemap.xml lists studio pages only.
