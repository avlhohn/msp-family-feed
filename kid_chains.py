#!/usr/bin/env python3
"""STEP 2 structured kid-chain intake -- recurring FREE kids' programs at national chains.
Folder root, undated, window/season-driven.

WHY THIS EXISTS
---------------
National retail chains run reliable, free, recurring kids' programs (Home Depot's monthly Kids
Workshop, IKEA's Småland play area, Bass Pro / Cabela's holiday crafts).  A family guide should
carry them, but a ONE-TIME hand-add decays: the feed window rolls forward every nightly and a
dated row ages out, so next week the recurring program is simply gone.  The correct mechanism is
a DETERMINISTIC SOURCE that regenerates the current window's occurrences on every run -- exactly
the espn_sports.py pattern, minus the network.

This module emits, for each registered program, the occurrences whose dates fall inside the run
window (cadence programs) or a standing blank-date row when the window intersects the program's
season (standing programs).  It owns no dates of its own: every dated row is computed from a
cadence rule against [today, end], so the set is always current and never stale.

DESIGN RULES (each load-bearing; breaking one fails silently)
-------------------------------------------------------------
1. ADDITIVE + SOFT-FAIL, like espn_sports.  fetch_all() wraps every program in try/except and
   returns ([], ERROR-note) for that program on ANY failure, so a bug in one registry entry
   contributes zero rows and CANNOT break the nightly.  There is no network here, so the only
   failure surface is a malformed registry entry -- but the discipline is identical.

2. DATES ARE COMPUTED, NEVER TYPED.  A cadence program carries a RULE ("1st Saturday of the
   month"), and the occurrences are generated against the window.  Typing a literal date is the
   stale-date class CLAUDE.md documents repeatedly: a value a helper can derive is a value it
   will eventually carry wrong.  The ONLY thing a cadence entry states is the rule.

3. price_type is SOURCED, not guessed -- and it is NOT always "Free" (relaxed 2026-10-01,
   owner-approved).  Most registry programs are genuinely free (Home Depot Kids Workshop, IKEA
   Småland, Santa's Wonderland crafts, Lowe's/Michaels/B&N kids' programs).  But a program may
   legitimately carry a free/paid MIX -- REI Family & Kids classes run both free intro sessions
   and ticketed ones -- and such a program is stamped "Varies", the honest enum value, NOT "Free"
   and NOT dropped.  CLAUDE.md: stamping Free is a claim a family acts on at a counter, so "Free"
   is only ever written for a program confirmed free end-to-end; anything with a paid component is
   "Varies".  The enum is strictly Free | Paid | Varies; the value lives in the registry entry and
   to_feed_rows copies it through verbatim.

4. COORDINATES ARE REAL, geocoded per store (Census / Nominatim), NEVER fabricated.  A store
   with no resolved coordinate is omitted rather than pinned to a guess.

5. row_fn IS INJECTED, the schema is NOT duplicated.  Production passes fetch_feeds.row (single
   source of truth for the 20-key event dict); tests pass a stub.  Same registry-drift avoidance
   as espn_sports.

6. STANDING programs are SEASON-GATED.  IKEA Småland is year-round (season = all months); Santa's
   Wonderland is Nov-Dec only.  A standing row carries a BLANK date (CLAUDE.md: blank date == a
   recurring/standing attraction that is never aged out) and is emitted ONLY when the run window's
   months intersect the program's season.  So in March the helper emits nothing for a Nov-Dec
   program -- the SOURCE controls seasonality, not the aging logic.

The module NEVER does I/O at import time (import must not be a write -- CLAUDE.md 2026-09-18);
all work is behind functions and the __main__ guard.
"""
import datetime as _dt

# ---- store registry (real geocoded coordinates -- rule 4) --------------------------------
# Coordinates: Census geocoder where it resolved, else Nominatim (both real geocoders, no
# fabrication).  Source tag per store keeps provenance.
HOME_DEPOT_STORES = [
    {"name": "The Home Depot - Apple Valley", "address": "15101 Flagstaff Ave, Apple Valley, MN 55124", "lat": 44.72945, "lon": -93.19783},
    {"name": "The Home Depot - Bloomington",  "address": "400 W 79th St, Bloomington, MN 55420",        "lat": 44.85943, "lon": -93.27324},
    {"name": "The Home Depot - Maple Grove",  "address": "15800 Grove Cir N, Maple Grove, MN 55369",     "lat": 45.13634, "lon": -93.48146},
    {"name": "The Home Depot - Plymouth",     "address": "1705 Annapolis Ln N, Plymouth, MN 55441",      "lat": 44.99780, "lon": -93.45394},
    {"name": "The Home Depot - Richfield",    "address": "6301 Richfield Pkwy, Richfield, MN 55423",     "lat": 44.88819, "lon": -93.25029},
]

CABELAS_STORES = [
    {"name": "Cabela's - Woodbury", "address": "8400 Hudson Rd, Woodbury, MN 55125", "lat": 44.94160, "lon": -92.93381},
    {"name": "Cabela's - Rogers",   "address": "20200 Rogers Dr, Rogers, MN 55374",  "lat": 45.18770, "lon": -93.53648},
]

IKEA_STORES = [
    {"name": "IKEA Twin Cities - Bloomington", "address": "8000 IKEA Way, Bloomington, MN 55425", "lat": 44.85757, "lon": -93.24340},
]

# ---- pass-2 chains (added 2026-10-01; standing cards, owner-approved) ---------------------
# Coordinates Census-geocoded 2026-10-01; B&N Edina resolved to the Galleria mall (3510
# Galleria) since the store sits inside it -- a real resolved coordinate, not a fabrication.
LOWES_STORES = [
    {"name": "Lowe's Home Improvement - West St. Paul",    "address": "1795 Robert St S, West St Paul, MN 55118",     "lat": 44.89121, "lon": -93.080672},
    {"name": "Lowe's Home Improvement - Plymouth",         "address": "3205 Vicksburg Lane N, Plymouth, MN 55447",    "lat": 45.016462, "lon": -93.481823},
    {"name": "Lowe's Home Improvement - Maple Grove",      "address": "11201 Fountains Dr N, Maple Grove, MN 55369",  "lat": 45.091595, "lon": -93.422724},
    {"name": "Lowe's Home Improvement - Oak Park Heights", "address": "5888 Nova Scotia Ave N, Oak Park Heights, MN 55082", "lat": 45.03332, "lon": -92.826427},
]

MICHAELS_STORES = [
    {"name": "Michaels - Bloomington", "address": "4240 W 78th St, Bloomington, MN 55435",      "lat": 44.858932, "lon": -93.332135},
    {"name": "Michaels - Minnetonka",  "address": "11522 Wayzata Blvd, Minnetonka, MN 55305",    "lat": 44.971382, "lon": -93.424764},
    {"name": "Michaels - Maplewood",   "address": "2980 White Bear Ave N, Maplewood, MN 55109",  "lat": 45.030756, "lon": -93.017974},
    {"name": "Michaels - Maple Grove", "address": "7980 Wedgwood Ln N, Maple Grove, MN 55369",    "lat": 45.099251, "lon": -93.448946},
]

BN_STORES = [
    {"name": "Barnes & Noble - Edina (Galleria)", "address": "3230 Galleria, Edina, MN 55435",       "lat": 44.878036, "lon": -93.323188},
    {"name": "Barnes & Noble - Roseville",        "address": "2100 N Snelling Ave, Roseville, MN 55113", "lat": 45.006234, "lon": -93.166288},
    {"name": "Barnes & Noble - Maple Grove",      "address": "8040 Wedgewood Lane, Maple Grove, MN 55369", "lat": 45.099843, "lon": -93.449332},
]

REI_STORES = [
    {"name": "REI - Bloomington", "address": "750 W American Blvd, Bloomington, MN 55420",   "lat": 44.859526, "lon": -93.290894},
    {"name": "REI - Maple Grove", "address": "11581 Fountains Dr, Maple Grove, MN 55369",    "lat": 45.092378, "lon": -93.426804},
    {"name": "REI - Roseville",   "address": "1955 County Rd B2 W, Roseville, MN 55113",     "lat": 45.015002, "lon": -93.182227},
]

# ---- program registry --------------------------------------------------------------------
# A CADENCE program lists occurrences on a recurring rule inside the window.
#   cadence = {"type": "nth_weekday_monthly", "n": 1, "weekday": 5}   # 1st Saturday (Mon=0..Sun=6)
# A STANDING program emits one blank-date row per store when the window intersects `season`.
#   cadence = {"type": "standing"}; season = set of month ints (1..12)
PROGRAMS = [
    {
        "key": "home_depot_kids_workshop",
        "title": "Home Depot Kids Workshop",
        "chain": "The Home Depot",
        "description": ("Free monthly build-it workshop for kids. Children get a free project kit, "
                        "apron, and pin while they build a small wood project with a grown-up. "
                        "Drop in anytime during the workshop window; project changes each month. "
                        "Typically the first Saturday of the month, 9:00 AM - 12:00 PM."),
        "age_range": "5-12",
        "time": "9:00 AM - 12:00 PM",
        "price_type": "Free",
        "tags": "crafts,workshop,indoor,family",
        "website": "https://www.homedepot.com/workshops",
        "stores": HOME_DEPOT_STORES,
        "cadence": {"type": "nth_weekday_monthly", "n": 1, "weekday": 5},
        "season": set(range(1, 13)),
    },
    {
        "key": "cabelas_santas_wonderland",
        "title": "Santa's Wonderland at Cabela's",
        "chain": "Cabela's",
        "description": ("Free holiday crafts and activities for kids during the holiday season, "
                        "plus a free photo with Santa. Daily free craft stations and games run "
                        "through the holidays (seasonal, November-December). No purchase required."),
        "age_range": "All ages",
        "time": "",
        "price_type": "Free",
        "tags": "holiday,crafts,seasonal,family",
        "website": "https://www.cabelas.com/content/santas-wonderland",
        "stores": CABELAS_STORES,
        "cadence": {"type": "standing"},
        "season": {11, 12},
    },
    {
        "key": "ikea_smaland",
        "title": "IKEA Småland Free Kids' Play Area",
        "chain": "IKEA",
        "description": ("Småland is IKEA's free supervised play area where kids can play in a "
                        "ball pit and activity space while grown-ups shop. Free, year-round, "
                        "first-come first-served; children must be potty-trained and within the "
                        "posted height range. A standing free amenity rather than a dated event."),
        "age_range": "4-10",
        "time": "Store hours",
        "price_type": "Free",
        "tags": "play,indoor,free,family",
        "website": "https://www.ikea.com/us/en/stores/smaland/",
        "stores": IKEA_STORES,
        "cadence": {"type": "standing"},
        "season": set(range(1, 13)),
    },
    # ---- pass-2 standing programs (added 2026-10-01, owner-approved) ----------------------
    {
        "key": "lowes_kids_workshop",
        "title": "Lowe's Kids Workshop",
        "chain": "Lowe's",
        "description": ("Free hands-on build-it workshop for kids. Children build a small take-home "
                        "wood project and get a free apron; kits are free while supplies last. "
                        "Offered periodically throughout the year -- check your local store's events "
                        "page for the next workshop date and to reserve a free kit."),
        "age_range": "5-12",
        "time": "",
        "price_type": "Free",
        "tags": "crafts,workshop,indoor,family",
        "website": "https://www.lowes.com/l/diy-u.html",
        "stores": LOWES_STORES,
        "cadence": {"type": "standing"},
        "season": set(range(1, 13)),
    },
    {
        "key": "michaels_kids_club",
        "title": "Michaels Kids Club",
        "chain": "Michaels",
        "description": ("Free Sunday Kids Club crafting for children. Kids make a free seasonal "
                        "craft project with provided materials -- no purchase required. Typically "
                        "Sunday mornings; check your local store for the weekly time. (Michaels also "
                        "runs paid MAKEbreak sessions, which are separate from this free program.)"),
        "age_range": "3-12",
        "time": "",
        "price_type": "Free",
        "tags": "crafts,workshop,indoor,family",
        "website": "https://www.michaels.com/kids-club",
        "stores": MICHAELS_STORES,
        "cadence": {"type": "standing"},
        "season": set(range(1, 13)),
    },
    {
        "key": "barnes_noble_storytime",
        "title": "Barnes & Noble Storytime",
        "chain": "Barnes & Noble",
        "description": ("Free weekly children's storytime. A staff reader shares a picture book "
                        "aloud, often with a simple related activity afterward -- a free, "
                        "drop-in reading event for young kids. The day and time vary by store, so "
                        "check your local Barnes & Noble's events calendar for the weekly schedule."),
        "age_range": "2-8",
        "time": "",
        "price_type": "Free",
        "tags": "storytime,reading,books,family,indoor",
        "website": "https://stores.barnesandnoble.com/events",
        "stores": BN_STORES,
        "cadence": {"type": "standing"},
        "season": set(range(1, 13)),
    },
    {
        "key": "rei_family_kids_classes",
        "title": "REI Family & Kids Outdoor Classes",
        "chain": "REI",
        "description": ("Family-friendly outdoor skills classes and events -- things like intro to "
                        "camping, bike maintenance, and seasonal nature programs. Some sessions are "
                        "free and some are ticketed, so pricing varies; check your local REI's "
                        "events calendar for the current schedule and to register."),
        "age_range": "All ages",
        "time": "",
        "price_type": "Varies",
        "tags": "outdoor,classes,active,family",
        "website": "https://www.rei.com/events",
        "stores": REI_STORES,
        "cadence": {"type": "standing"},
        "season": set(range(1, 13)),
    },
]


# ---- pure date generation (no I/O) -------------------------------------------------------
def _parse(d):
    return _dt.date.fromisoformat(d)


def nth_weekday(year, month, n, weekday):
    """The date of the n-th `weekday` (Mon=0..Sun=6) in (year, month). n is 1-based."""
    first = _dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + _dt.timedelta(days=offset) + _dt.timedelta(weeks=n - 1)


def window_months(today, end):
    """The set of (year, month) pairs the window touches, in order."""
    t, e = _parse(today), _parse(end)
    out, y, m = [], t.year, t.month
    while (y, m) <= (e.year, e.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def season_intersects(today, end, season):
    """True if any month the window touches is in `season` (a set of 1..12 ints)."""
    return any(m in season for (_y, m) in window_months(today, end))


def occurrences(cadence, today, end):
    """Dated occurrences (list of 'YYYY-MM-DD') for a cadence program inside [today, end].
    A standing program returns [''] (a single blank-date row) when season-gated upstream."""
    ctype = cadence.get("type")
    if ctype == "standing":
        return [""]
    if ctype == "nth_weekday_monthly":
        n, wd = cadence["n"], cadence["weekday"]
        t, e = _parse(today), _parse(end)
        out = []
        for (y, m) in window_months(today, end):
            d = nth_weekday(y, m, n, wd)
            if t <= d <= e:
                out.append(d.isoformat())
        return out
    raise ValueError(f"unknown cadence type: {ctype!r}")


# ---- row mapping (injected row_fn -- rule 5) ---------------------------------------------
def to_feed_rows(program, today, end, row_fn):
    """Map one program to pipeline event rows (one per store x occurrence), fully enriched.
    Standing programs that do not intersect the window season emit nothing."""
    cadence = program["cadence"]
    standing = cadence.get("type") == "standing"
    if standing and not season_intersects(today, end, program.get("season", set(range(1, 13)))):
        return []
    dates = occurrences(cadence, today, end)
    rows = []
    for store in program["stores"]:
        if store.get("lat") in (None, "") or store.get("lon") in (None, ""):
            continue  # rule 4: no fabricated coordinate -> omit the store
        title = f"{program['title']} - {store['name'].split(' - ')[-1]}" if " - " in store["name"] else program["title"]
        for d in dates:
            r = row_fn(title, program["description"], store["address"], d, program["time"],
                       program["website"], f"chain_{program['key']}", program["tags"])
            r["price_type"] = program["price_type"]          # rule 3: sourced Free, not guessed
            r["age_range"] = program["age_range"]
            r["latitude"] = store["lat"]                     # rule 4: real geocoded coords
            r["longitude"] = store["lon"]
            rows.append(r)
    return rows


def fetch_program(program, today, end, row_fn):
    """(rows, report) for one program.  SOFT-FAIL: any exception -> ([], ERROR report)."""
    key = f"chain_{program.get('key', '?')}"
    try:
        rows = to_feed_rows(program, today, end, row_fn)
    except Exception as e:  # noqa: BLE001 -- soft-fail is the whole point (rule 1)
        return [], {"source": key, "status": "ERROR", "in_window": 0,
                    "note": f"{type(e).__name__}: {str(e)[:120]}"}
    standing = program["cadence"].get("type") == "standing"
    if not rows:
        status = "OUT_OF_SEASON" if standing else "NO_OCCURRENCE_IN_WINDOW"
    else:
        status = "OK"
    stores = len([s for s in program["stores"] if s.get("lat") not in (None, "")])
    note = f"{len(rows)} rows ({stores} stores, {'standing' if standing else 'cadence'}) in [{today}..{end}]"
    return rows, {"source": key, "status": status, "in_window": len(rows), "note": note}


def fetch_all(today, end, http_fn=None, row_fn=None):
    """(all_rows, reports) across every program.  Additive + soft-fail; safe to call always.

    `http_fn` is accepted for signature-parity with the other fetchers and is unused (this source
    is purely generative -- no network).  `row_fn` is required in production (fetch_feeds.row)."""
    if row_fn is None:
        raise ValueError("row_fn is required (inject fetch_feeds.row)")
    all_rows, reports = [], []
    for program in PROGRAMS:
        rows, rep = fetch_program(program, today, end, row_fn)
        all_rows.extend(rows)
        reports.append(rep)
    return all_rows, reports


if __name__ == "__main__":
    import sys
    import fetch_feeds as F  # imports fine only when MSP_TODAY / MSP_END are set
    rows, reports = fetch_all(F.TODAY, F.END, None, F.row)
    for rep in reports:
        print(rep)
    print(f"\nkid-chain in-window rows: {len(rows)}")
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        import json
        print(json.dumps(rows, indent=1, ensure_ascii=False))
