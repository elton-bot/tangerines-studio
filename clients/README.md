# Client content

One folder per paying client: `clients/<slug>/site.json` (the content file), `img/` (photos the client sent) and an optional `refine.css`. Build with `python3 engine/build_client.py clients/<slug>/site.json`. The output in `public/clients/<slug>/` is generated; never edit it by hand. See "Client sites" in CLAUDE.md.

Never put the client's private contact address (where their form sends) in this folder: that lives in the CLIENT_FORM_TO variable in Vercel.
