#!/usr/bin/env python3
"""Render Tangerines Studio sequence emails (steps 1 to 3) exactly as docs/sequence.md defines them.

Usage:
  python3 render_emails.py --step 1 --leads leads.json --config config.json [--ids TS-0001,TS-0002]

leads.json: the Leads values as returned by the Sheets API (first row = header), or a list of
            objects keyed by the header names.
config.json: the Config values as returned by the Sheets API ([key, value, note] rows), or an object.

Prints a JSON list: {"id", "to", "subject", "body", "words", "problems"}.
Never send a row whose "problems" list is not empty.
"""
import argparse
import json
import re
import sys

NICHE_PLURAL = {
    "plumbing": "plumbers",
    "hvac": "heating and air companies",
    "roofing": "roofing companies",
    "house cleaning": "house cleaning services",
    "landscaping / lawn care": "landscaping and lawn care companies",
    "chiropractor": "chiropractors",
    "physical therapy clinic": "physical therapy clinics",
    "massage therapist": "massage therapists",
    "auto repair": "auto repair shops",
    "transmission": "transmission shops",
    "brakes": "brake and auto repair shops",
    "body shop": "body shops",
}

SUFFIX = re.compile(r"(,?\s+(LLC|L\.L\.C\.|Inc\.?|PC|P\.C\.|PLLC|Co\.|Corp\.?|Company LLC))+$", re.I)

STEP1 = """Hi {first},

I was looking at {niche_plural} in {city} and came across {business_short}. {compliment_sentence}

Your website doesn't show that off yet. {Issue_1}, and {issue_2}.

I run Tangerines Studio, and we rebuild websites for local businesses. I'd like to mock up a new homepage for {business_short} using your own logo, photos and services, so you can see the difference before spending anything. If it's not for you, just delete it.

Want me to put it together?"""

STEP2 = """Hi {first}, quick follow-up on the homepage idea. I'm happy to build it first so you're judging a finished page, not a pitch. It takes about a day.

Should I go ahead?"""

STEP3 = """Hi {first}, last note from me. If a new website isn't a priority right now, no problem, and I won't follow up again.

If it is, just reply "yes" and your homepage concept will be ready within a day."""

FOOTER = """Elton Aclao
Tangerines Studio · {mailing_address}
This is a sales email. Reply "stop" and you won't hear from me again."""


def business_short(name):
    s = re.sub(r"\s*\([^)]*\)", "", name).strip()
    s = SUFFIX.sub("", s).strip().rstrip(",")
    return s


def load_rows(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and "values" in data:
        data = data["values"]
    if data and isinstance(data[0], list):
        head = data[0]
        return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in data[1:]]
    return data


def load_config(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and "values" in data:
        data = data["values"]
    if isinstance(data, list):
        return {r[0]: (r[1] if len(r) > 1 else "") for r in data if r}
    return data


def render(row, cfg, step):
    problems = []
    name = (row.get("business_name") or "").strip()
    short = business_short(name)
    first = (row.get("owner_first_name") or "").strip() or "there"
    niche = (row.get("niche") or "").strip()
    plural = NICHE_PLURAL.get(niche.lower())
    if not plural:
        problems.append("no niche_plural for niche %r" % niche)
    issue_1 = (row.get("issue_1") or "").strip()
    issue_2 = (row.get("issue_2") or "").strip()
    compliment = (row.get("compliment") or "").strip()
    if step == 1:
        if not issue_1 or not issue_2:
            problems.append("missing issue_1 or issue_2")
        if not compliment:
            problems.append("missing compliment")
        elif len(compliment.split()) > 20:
            problems.append("compliment over 20 words")
        if compliment and not compliment.endswith("."):
            problems.append("compliment is not a finished sentence")
    address = (cfg.get("mailing_address") or "").strip()
    if not address or "pending" in address.lower():
        problems.append("Config mailing_address not set")
    subject = "New homepage for %s?" % short
    if step == 1:
        body = STEP1.format(
            first=first,
            niche_plural=plural or "{niche_plural}",
            city=(row.get("city") or "").strip(),
            business_short=short,
            compliment_sentence=compliment,
            Issue_1=issue_1[:1].upper() + issue_1[1:],
            issue_2=issue_2,
        )
    elif step == 2:
        body, subject = STEP2.format(first=first), "Re: " + subject
    else:
        body, subject = STEP3.format(first=first), "Re: " + subject
    words = len(body.split())
    full = body + "\n\n" + FOOTER.format(mailing_address=address)
    if "{" in full or "}" in full:
        problems.append("unfilled placeholder")
    for ch, label in (("—", "em dash"), ("–", "en dash"), ("!", "exclamation mark")):
        if ch in full:
            problems.append("contains " + label)
    if re.search(r"https?://|www\.", body) and step == 1:
        problems.append("link in step 1")
    if step == 1 and not (90 <= words <= 160):
        problems.append("step 1 body is %d words (needs 90 to 160)" % words)
    email = (row.get("email") or "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        problems.append("bad email")
    return {"id": row.get("id"), "to": email, "subject": subject, "body": full, "words": words, "problems": problems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, choices=(1, 2, 3), required=True)
    ap.add_argument("--leads", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    rows = load_rows(a.leads)
    cfg = load_config(a.config)
    want = {x.strip() for x in a.ids.split(",") if x.strip()}
    out = [render(r, cfg, a.step) for r in rows if not want or r.get("id") in want]
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
