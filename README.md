# Tangerines Studio

The website at tangerinesstudio.com and the tools behind its free homepage previews.

- `public/` is everything Vercel serves: the studio site at `/` and homepage previews at `/preview/<name>/`. Previews are never indexed (robots.txt plus an `X-Robots-Tag: noindex` header from `vercel.json`).
- `engine/render_concept.py` builds a preview page from a JSON spec (`engine/samples/juniper-ridge.json` is a fictional example) into `public/preview/<name>/`, including copies of the business's own logo and photo. Needs `pip install jinja2 pillow requests`.
- `tools/render_emails.py` renders outreach emails from the pipeline sheet and checks them before anything is sent.

- `engine/check_preview.py` screenshots a page at phone and desktop width and checks it before it ships.
- `engine/build_client.py` builds a paying client's site from `clients/<slug>/site.json` into `public/clients/<slug>/`.
- `api/` holds two Vercel Functions: the request form on the studio site and the contact forms on client sites. They send mail through DreamHost SMTP using credentials kept in Vercel environment variables.

There is no build step and no package.json. Vercel serves `public/` as is plus the functions in `api/` (see `vercel.json`), and every push to `main` deploys. CLAUDE.md has the full rules.
