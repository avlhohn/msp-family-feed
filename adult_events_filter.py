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
    # --- added 2026-08-28: synonym vocabulary the library feeds actually use ---
    # (the original list was built from one 2026-08-25 sample and missed these; 130
    #  computer/tech-help rows were slipping through under names the list never had.)
    "computer tutor", "tech tutor", "technology assistance", "technology help",
    "technology tutor", "public computer aide", "computer lab", "tech time",
    "1:1 technology", "1:1 tech", "one-on-one tech", "one-on-one computer",
    "book a tech", "digital literacy", "device help", "smartphone help",
    # career / workforce synonyms
    # NOTE: bare "career exploration" is deliberately NOT here — it also names teen/youth
    #  career nights, which are family programming. Keep the specific adult form only.
    "career exploration for adults",
    "careerforce", "career planning", "career counseling", "job help",
    # senior programming (specific phrases only — a bare "senior" is too broad, it
    #  also names high-school seniors; keep these tightly scoped)
    "senior coffee", "senior social", "senior chef", "for seniors", "older adults",
    "55+",
    # veteran services — NOTE the KEEP_GUARDS below exempt "Veterans Park / Pow Wow /
    #  Farmers Market / Memorial", which are place names, not veteran-services programming
    "resources for veterans", "veterans resource", "veteran services",
    # library adult-programming staples that table employers/partners
    "community partner of the day",
    # --- added 2026-08-31: adult-only titles found stale in the live app ---
    # (each is an unambiguous adult title that essentially never names a kids/family event;
    #  the compound trivia rule below handles bar/brewery trivia, which "trivia" alone can't.)
    "estate planning", "dementia", "happy hour", "retirement party",
    "blood drive", "pub trivia", "bar trivia", "trivia night at the bar",
    # --- added 2026-09-01: adult / non-family titles found stale in the live app ---
    # (the "safe keywords" half of the 2026-09-01 audit. Each phrase below was verified against
    #  the live feed to hit ONLY the adult rows and NOT the family false-positives that a looser
    #  keyword would sweep in — see the notes on each. Concerts are handled by CONCERT_TITLES.)
    #
    # fundraiser galas / banquets — a ticketed adult evening dinner, never a kids event.
    #   "gala" is safe as a standalone token; a family event essentially never calls itself a gala.
    #   "fundraiser dinner"/"dinner gala"/"annual banquet" are the specific adult forms.
    "gala", "fundraiser dinner", "annual banquet", "hall of fame award",
    # professional / business conferences & continuing-ed (adult workforce programming).
    #   NOTE: bare "conference" is NOT here — "MN Rec & Park Association Annual Conference" is
    #   caught by "annual conference"; a school "parent-teacher conference" must survive, so we
    #   require the adult-context words. "leadership conference", "women in leadership",
    #   "realtor", "chamber of commerce", "continuing education"/"ce" are adult-only.
    "annual conference", "leadership conference", "women in leadership",
    "realtor", "chamber of commerce", "homesteading summit", "marketing matters",
    "executive minds", "stewardship conference", "social media marketing for business",
    # men-only adult groups — "men's bible study", "men's book club", F3 men's workout.
    #   Gendered college sports ("UMD Men's Hockey", "Gophers Women's Soccer") are family KEEPs,
    #   so we do NOT drop on bare "men's"/"women's"; only these specific adult-group forms.
    "men's bible study", "men's book club", "f3 men's workout",
    # adult wellness / mental-health talks & fairs.
    #   "wellness fair" and "holistic healing" name adult health expos; "maternal mental health"
    #   and "the working caregiver" and "changing the narrative on mental health" are adult talks.
    "wellness fair", "holistic healing", "maternal mental health",
    "the working caregiver", "changing the narrative on mental health",
    # adult endurance / rucking
    "ruck life",
    # adult women's dance-fitness class (recurring; scoped to the full phrase, never bare "shine")
    "shine @ fitness in the parks", "shine at fitness in the parks",
    # adult import-car expo (community "car show"s are family KEEPs, so scope to this brand)
    "importexpo", "import expo",
]

# --- explicit concert / comedy title list (added 2026-09-01) --------------------------------
# Named touring musicians and stand-up comics carry NO "adult" keyword, so no phrase rule can
# catch them without false-positiving on family shows (a kids' concert is still a concert).
# The precision-first answer the owner chose is an explicit allow-to-drop list of the specific
# ticketed adult acts verified on the 2026-09-01 feed. Matched as a normalized substring of the
# title. Extend this list by hand as new adult touring acts appear — never broaden it to a
# generic "tour"/"concert" rule (that would drop "Happy Together KIDS Tour"-style family shows).
CONCERT_TITLES = [
    "bombargo", "brandon flowers", "doug stone farewell", "happy together tour",
    "ida undertow", "liz phair", "phoebe bridgers", "sugarland ride or die",
    "tom papa", "tyler polzin", "wallflowers 30th anniversary",
]

# --- generic adult-programming rule (guarded) -------------------------------------------
# "Adult Craft", "Book Club for Adults", "Adult Coloring Hour" etc. are adult programming
# but the words are generic, so this rule is fenced by KEEP_GUARDS: it must NEVER fire on
# a family event that merely uses "adult" as the top of an age range, on a kids/maker title
# that contains a tech-ish substring, on a veterans PLACE name, or on the teen "young adult"
# library category. Each guard below is a real false-positive observed on the live feed.
GENERIC_ADULT = [
    "for adults", "adult",
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

# --- KEEP_GUARDS: if any of these match the title, the GENERIC_ADULT rule is suppressed.
# These do NOT protect against the explicit DROP_PHRASES above (those are unambiguous);
# they only fence the generic "adult"/"for adults" catch. Every pattern is a real live case:
#   - age range:  "best for ages 8 to adult", "ages 3-adult", "adults welcome" (family nature walks)
#   - maker/kids: "Createch Unplugged", "Sewing Techniques", "3D Modeling ... Techniques"
#   - place name: "Veterans Memorial Park / Pow Wow / Farmers Market"
#   - teen cat.:  "Young Adult Book Club" (YA is a teen category, not adult services)
KEEP_GUARDS = [
    re.compile(r"\bages?\b.*\badults?\b", re.I),
    re.compile(r"\bto\s+adults?\b", re.I),
    re.compile(r"\b-\s*adults?\b", re.I),
    re.compile(r"\badults?\s+welcome\b", re.I),
    re.compile(r"\bcreatech\b", re.I),
    re.compile(r"\btechniques?\b", re.I),
    re.compile(r"veterans?\s+(memorial|park|pow\s*wow|farmers|field|stadium|hall|bridge)", re.I),
    re.compile(r"\byoung\s+adults?\b", re.I),
]


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
            # Only require a \b where the phrase edge is a word char. A phrase like "55+"
            # ends in a non-word char, and \b between two non-word chars never matches, so
            # a trailing \b there would make the phrase impossible to hit.
            left = r"\b" if p[:1].isalnum() else ""
            right = r"\b" if p[-1:].isalnum() else ""
            rx = _RX_CACHE[p] = re.compile(left + re.escape(p) + right)
        if rx.search(title_norm):
            return p
    return None


def _guarded(title_norm):
    """True if any KEEP_GUARD fires — meaning the generic adult rule must NOT drop this row."""
    return any(rx.search(title_norm) for rx in KEEP_GUARDS)


# --- compound rule (added 2026-08-31): trivia AT a bar / brewery is adult programming, but
# bare "trivia" is NOT droppable — libraries run all-ages trivia ("Trivia Night with Trivia
# Mafia" @ Galaxie Library is a real family KEEP). So drop a trivia title ONLY when it also
# carries an alcohol word-boundary token. Word boundaries are load-bearing: \bpub\b will not
# fire inside "public", \bbar\b will not fire inside "library" or "barn". This catches
# "Trivia Thursday at Minnesota BEER Company" but leaves "OMNI Brewery Oktoberfest" alone
# (no "trivia") and library trivia alone (no alcohol token).
_RX_TRIVIA = re.compile(r"\btrivia\b")
_RX_ALCOHOL = re.compile(r"\b(beer|brewery|taproom|distillery|pub|bar|cider|winery)\b")


def _compound_drop(title_norm):
    """'trivia' co-occurring with an alcohol token -> bar/brewery trivia (adult). Else None."""
    if _RX_TRIVIA.search(title_norm) and _RX_ALCOHOL.search(title_norm):
        return "trivia+alcohol"
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
    # explicit named-act concert/comedy list (no keyword catches these; extend by hand)
    if not drop_hit:
        for c in CONCERT_TITLES:
            if c in t:
                drop_hit = "concert:" + c
                break
    # compound bar/brewery-trivia rule (trivia + alcohol token); bare trivia is left alone
    if not drop_hit:
        drop_hit = _compound_drop(t)
    # generic adult rule only fires when no KEEP_GUARD protects the title
    if not drop_hit and not _guarded(t):
        drop_hit = _match(t, GENERIC_ADULT)
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
