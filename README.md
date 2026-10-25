# Tangerines Studio

The website at tangerinesstudio.com and the tools behind its free homepage previews.

- `public/` is everything Vercel serves: the studio site at `/` and homepage previews at `/preview/<name>/`. Previews are never indexed (robots.txt plus an `X-Robots-Tag: noindex` header from `vercel.json`).
- `engine/render_concept.py` builds a preview page from a JSON spec (`engine/samples/juniper-ridge.json` is a fictional example) into `public/preview/<name>/`, including copies of the business's own logo and photo. Needs `pip install jinja2 pillow requests`.
- `tools/render_emails.py` renders outreach emails from the pipeline sheet and checks them before anything is sent.

There is no build step. Vercel serves `public/` as is (see `vercel.json`), and every push to `main` deploys.
