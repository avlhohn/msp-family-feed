#!/usr/bin/env python3
"""
adult_events_filter.py  —  STEP 4.3a exclusion pass (runs in STEP 4.3, before dedup_titles.py)

WHAT THIS SOLVES
----------------
Library / community-center calendars publish adult-services programming — job-search help,
career services, Medicare/MNsure counseling, 1:1 tech help for seniors, small-business
support — into the same feeds we harvest for family events. These are NOT family/kid events
and should not appear in the guide. On the 2026-08-25 live feed, 230 event rows (59 unique
titles) were this kind of adult programming.

DESIGN (mirrors dedup_titles.py: precision over recall, DROP vs REVIEW, real-case tests)
----------------------------------------------------------------------------------------
1. **Title-only match.** We match on the normalized TITLE, never the description. A community
   festival ("Fiesta Latina") whose description merely mentions a job-resource booth must NOT
   be dropped — description matching produced exactly that false positive in testing.
2. **Two tiers.** DROP_PHRASES are unambiguous adult-service titles that essentially never name
   a kids' event. REVIEW_PHRASES are borderline (e.g. "senior center") — reported for a human,
   NEVER auto-dropped. A wrong DROP silently deletes a real family event; a missed one is
   cosmetic. Same asymmetry dedup_titles.py is built around.
3. **Events category only.** Adult services route to `events`. Parks / restaurants / meal_deals /
   volunteer are left untouched.
4. **Seeds are never dropped.** A row carrying is_seed = true is a hand-vetted inclusion; skip it
   (and log it under `review` if it somehow matched, so the collision is visible).
5. **Every drop is logged** to _adult_filter_report.json and printed, so nothing disappears
   silently. STEP 7 reads the report to emit `adult_event_filtered` pipeline info rows.

Accepts either shape of _compiled_work.json: a flat list of rows, or a {category: [rows]} dict.
Idempotent — re-running on already-filtered data drops nothing.

Usage:
    python3 adult_events_filter.py _compiled_work.json --dry-run   # report only, changes nothing
    python3 adult_events_filter.py _compiled_work.json             # apply; prints every drop
"""
import json
import re
import sys
import unicodedata

# --- unambiguous adult-service title phrases (normalized substring match) ---------------
# Each phrase, if present in the normalized title of an `events` row, drops that row.
# Keep these specific: a phrase must be one that essentially never appears in a genuine
# kids'/family event title. When in doubt, put it in REVIEW_PHRASES instead.
DROP_PHRASES = [
    # job / career / workforce
    "job search", "job seeker", "job club", "job training", "job fair",
    "career services", "career service", "career fair", "career help",
    "career lab", "career center", "career exploration for adults",
    "resume", "cover letter", "interview skills", "interview prep",
    "interviewing workshop", "virtual interviewing", "workforce",
    "employment resource", "employer of the day", "minneapolis works",
    "work wednesday", "in-person job", "job assistance",
    # health-benefits enrollment / counseling
    "medicare", "medicaid", "mnsure", "minnesotacare", "minnesota care",
    # gov / legal / financial adult services
    "small business support", "small business", "business consultation",
    "business consultations", "entrepreneur", "naturalization",
    "citizenship class", "notary", "aarp",
    # adult tech / computer help (library one-on-one appointments)
    "tech help", "tech drop-in", "tech drop in", "computer help",
    "computer and tech help", "one-to-one computer",
    # library adult-programming staples that table employers/partners
    "community partner of the day",
]

# --- borderline: report, do NOT auto-drop -----------------------------------------------
# These CAN name adult programming but could also head a legitimate family event
# (e.g. "Family Bingo at the Senior Center"). Never delete on these — surface for review.
REVIEW_PHRASES = [
    "senior center", "adult literacy", "adult education", "ged",
    "esl class", "homebuyer", "grief", "support group", "caregiver support",
]

F_TITLE = "title"
F_CAT = "category"
F_SEED = "is_seed"
EVENTS_CAT = "events"


def norm(s):
    """lowercase, strip accents (résumé -> resume), & -> and, collapse whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


_RX_CACHE = {}


def _match(title_norm, phrases):
    """Word-boundary match, so a short token like 'ged' does NOT fire inside 'unplugged'
    or 'ridgedale'. Multi-word phrases ('job search') still match as a bounded unit."""
    for p in phrases:
        rx = _RX_CACHE.get(p)
        if rx is None:
            rx = _RX_CACHE[p] = re.compile(r"\b" + re.escape(p) + r"\b")
        if rx.search(title_norm):
            return p
    return None


def classify(row):
    """Return ('drop', phrase) | ('review', phrase) | (None, None) for one row.
    Only ever acts on events-category rows; never drops a seed."""
    if norm(row.get(F_CAT)) != EVENTS_CAT:
        return None, None
    t = norm(row.get(F_TITLE))
    if not t:
        return None, None
    drop_hit = _match(t, DROP_PHRASES)
    review_hit = _match(t, REVIEW_PHRASES)
    is_seed = str(row.get(F_SEED)).strip().lower() in ("true", "1", "yes")
    if drop_hit:
        # a seed that matches a drop phrase is a collision — never delete a seed, surface it
        if is_seed:
            return "review", "SEED-COLLISION:" + drop_hit
        return "drop", drop_hit
    if review_hit:
        return "review", review_hit
    return None, None


def _iter_events(data):
    """Yield (container, index, row) for every events-category row, for both shapes."""
    if isinstance(data, dict):
        rows = data.get(EVENTS_CAT, [])
        for i, r in enumerate(rows):
            yield rows, i, r
    elif isinstance(data, list):
        for i, r in enumerate(data):
            if isinstance(r, dict):
                yield data, i, r


def run(path, dry_run=False):
    with open(path) as f:
        data = json.load(f)

    drops, reviews = [], []
    for _, _, row in _iter_events(data):
        verdict, phrase = classify(row)
        rec = {"title": row.get(F_TITLE), "phrase": phrase,
               "date": row.get("date", ""), "address": row.get("address", "")}
        if verdict == "drop":
            drops.append(rec)
        elif verdict == "review":
            reviews.append(rec)

    drop_titles = {(d["title"], d["date"], d["address"]) for d in drops}

    if not dry_run and drops:
        if isinstance(data, dict):
            data[EVENTS_CAT] = [
                r for r in data.get(EVENTS_CAT, [])
                if (r.get(F_TITLE), r.get("date", ""), r.get("address", "")) not in drop_titles
                or classify(r)[0] != "drop"
            ]
        elif isinstance(data, list):
            data[:] = [
                r for r in data
                if not (isinstance(r, dict) and classify(r)[0] == "drop")
            ]
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    report = {"dropped_count": len(drops), "review_count": len(reviews),
              "dropped": drops, "review": reviews, "dry_run": dry_run}
    with open("_adult_filter_report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"adult_events_filter: {'DRY-RUN ' if dry_run else ''}"
          f"dropped {len(drops)} event rows, flagged {len(reviews)} for REVIEW")
    from collections import Counter
    for phrase, n in Counter(d["phrase"] for d in drops).most_common():
        print(f"  DROP   x{n:<3} [{phrase}]")
    for phrase, n in Counter(r["phrase"] for r in reviews).most_common():
        print(f"  REVIEW x{n:<3} [{phrase}]")
    print("  report -> _adult_filter_report.json")
    return len(drops), len(reviews)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    path = args[0] if args else "_compiled_work.json"
    run(path, dry_run=dry)
