#!/usr/bin/env python3
"""
feature_grep.py -- STEP 1 stranding audit, as an ENUMERATED TABLE.

WHY THIS FILE EXISTS (CLAUDE.md, 2026-09-29):
    "This file says the STEP 1 grep list 'is now 58 targets over 17 root files.' That number
     cannot be derived from the paragraph that holds the list: a mechanical extraction yields
     49, and this run's audit checked and passed 46. Three numbers, one list."

    Rule (1): convert the grep list to an enumerated table (target | file | why load-bearing)
              and LET THE COUNT BE THE TABLE'S LENGTH rather than a hand-maintained integer.
    Rule (2): quoted counterexamples must live OUTSIDE the list they warn about, or they
              become entries in it.

Rule (2) is implemented here as KNOWN_ABSENT: the two names CLAUDE.md quotes as the cautionary
example of a grep list written from memory are asserted to be *absent*. That turns a documented
trap into a live NEGATIVE CONTROL -- if one of them ever starts matching, the audit itself is
matching too loosely, and we find that out instead of assuming it.

A MISS is a stranding-recurrence signal, NOT proof a feature is gone. CLAUDE.md:
    "A feature grep asserts a NAME, and the name is the fragile part ... when a grep misses,
     open the file and look for the feature under another shape before rebuilding it."
Fixing a grep target costs one line; rebuilding a wired source costs a day and can regress it.

Usage:
    python3 feature_grep.py            # audit, exit 1 on any miss or any control hit
    python3 feature_grep.py --verbose  # also print every PASS row
"""
import os
import sys

RUNDIR = os.environ.get("MSP_RUNDIR", os.path.dirname(os.path.abspath(__file__)) or ".")

# ---------------------------------------------------------------------------
# THE TABLE.  (target, file, why it is load-bearing)
# The audit's target count is len(TARGETS) -- never a number typed in prose.
# ---------------------------------------------------------------------------
TARGETS = [
    # --- fetch_feeds.py : sources and the iCal/timezone layer ----------------
    ("run_decc",            "fetch_feeds.py",  "SKILL.md:832 mandates DECC Duluth; was absent+invisible, built twice"),
    ("sppl",                "fetch_feeds.py",  "Saint Paul Public Library, 2nd-largest source; wired as a BIBLIO row, NOT run_sppl()"),
    ("run_tribe_rest",      "fetch_feeds.py",  "The Events Calendar REST intake"),
    ("TRIBE_FEEDS",         "fetch_feeds.py",  "registry the Tribe intake dispatches"),
    ("span_status",         "fetch_feeds.py",  "multi-day span handling for Tribe rows"),
    ("month_urls",          "fetch_feeds.py",  "LibCal month-loop URL builder; a 500-cap is per-CALENDAR"),
    ("MONTH_LOOP_ICAL",     "fetch_feeds.py",  "the calendars that need the month loop rather than one pull"),
    ("stillwater_libcal",   "fetch_feeds.py",  "washco sub-calendar fan-out; absence = silent under-fetch"),
    ("run_espn_sports",     "fetch_feeds.py",  "STEP 2 structured sports dispatch; absence returns sports to free-text only"),
    ("run_kid_chains",      "fetch_feeds.py",  "STEP 2 recurring kid-chain dispatch; absence silently drops Home Depot/IKEA/Cabela's rows"),
    ("_ical_parse",         "fetch_feeds.py",  "2026-09-29 tz fix: UTC->America/Chicago BEFORE the date test"),
    ("ical_date",           "fetch_feeds.py",  "thin wrapper over _ical_parse; raw-digit slicing misfiled evening events"),
    ("ical_time",           "fetch_feeds.py",  "same; UTC-stamped LibCal rows displayed +5h/+6h late"),
    ("DTSTART_P",           "fetch_feeds.py",  "DTSTART params threaded to 6 call sites; without it TZID is indistinguishable from floating"),

    # --- compile_step3.py : STEP 3 compile ----------------------------------
    ("tagify",              "compile_step3.py", "content tags for library rows; without them the image chooser has nothing to match"),
    ("covers_today",        "compile_step3.py", "out-of-window meal_deals/volunteer get date BLANKED and kept, events dropped"),
    ("LIBRARY_SRC",         "compile_step3.py", "assert-on-compile registry; drift left 669 sppl rows untagged"),

    # --- image layers -------------------------------------------------------
    ("wikimedia",           "image_upgrades.py", "4th image layer; eligible on curated_category (the first ratchet fix)"),
    ("_wiki_prime_cache",   "image_upgrades.py", "warm-starts _wiki_cache.json from the repo; cold run lands ~41 instead of ~50"),
    ("dnr_banner_map",      "step45_site_photo.py", "DNR /state_parks/ pages are JS redirect stubs; use location_tag"),
    ("MAX_FANOUT",          "step45_site_photo.py", "bounds the 4.5 fan-out inside the shared 20-min ENRICH_DEADLINE"),
    ("EVENT_PERMALINK_GAME","step45_site_photo.py", "espn.com/../game/_/gameId/<id> was offered as if it were a venue site"),
    ("EVENT_PERMALINK_TRAIL","step45_site_photo.py","/event/<slug>/<id>/ -- the id is NOT right after /event/, so the base pattern missed it"),
    ("run_date",            "step45_site_photo.py", "stamps the freshness marker; HALF of a two-part assertion"),
    ("__rejected__",        "step45_site_photo.py", "permanent-negative memo; absence silently re-buys proven-bad pages"),
    ("REJECT_SEED",         "step45_site_photo.py", "seeds the reject memo; same silent re-buy"),
    ("load_seen",           "step45_site_photo.py", "absence still 'works' but re-buys owned answers under budget pressure"),
    ("(?:spk|sra)",         "step45_site_photo.py", "DNR location_tag prefixes; sra added 2026-10-01 -- spk-only silently zeroed Big Bog (an SRA)"),
    ("load_curated",        "curated_repoint.py", "mapping logic IMPORTED from image_upgrades, never reimplemented"),
    ("skip_url_still_live", "curated_repoint.py", "the idempotency counter; its SHAPE proves the 2nd run repointed 0 correctly"),

    # --- safety filters -----------------------------------------------------
    ("_compound_drop",      "adult_events_filter.py", "bar-trivia needs alcohol+activity co-occurrence, never a flat keyword"),
    ("magnet senior center","adult_events_filter.py", "proper-noun pin for a venue whose adultness is not in the title"),
    ("DENYLIST",            "closed_venue_denylist.py", "SKILL.md-closed venues otherwise ride the carried base forward"),
    ("RX_ENTITY",           "entity_fix.py",   "&#39; makes a duplicate invisible to EVERY dedup pass; PRE-chain"),

    # --- dedup chain --------------------------------------------------------
    ("ntime",               "dupsweep.py",     "clock canonicalisation; 350 time-format duplicates found live"),
    ("minnesota",           "dupsweep.py",     "TRAILING-ONLY spelled-state strip -- see NEEDS_EYES, a bare hit does NOT prove this"),
    ("MIN_ANCHOR_TOKENS",   "sports_dedup.py", "collapses carried free-text sports rows into structured ESPN anchors"),
    ("find_groups",         "sports_dedup.py", "the grouping pass itself"),

    # --- STEP 8 repair + tripwires -----------------------------------------
    ("KEEP_APART",          "step8_venue_repair.py", "venues that must NOT be merged by the repair pass"),
    ("force_recoord",       "step8_venue_repair.py", "re-geocode after an address fix; a fixed address with a stale pin is worse"),
    ("TEAMS",               "sports_coverage.py", "the guarded roster; a named team can drop to 0 rows with nothing warning"),
    ("coverage",            "sports_coverage.py", "the tripwire itself"),
    ("TEAMS",               "espn_sports.py",  "the structured source's own registry (6 MN pros + 2 Gophers)"),
    ("schedule_url",        "espn_sports.py",  "the ESPN endpoint builder -- see the OPEN espn_season_param_check"),
    ("_to_local_date_time", "espn_sports.py",  "UTC->Central before the date test; naive slicing misfiles evening games"),
    ("timeValid",           "espn_sports.py",  "unannounced-kickoff guard; absence fabricates an 11 PM start a day early"),
    ("season_type",         "espn_sports.py",  "reads ESPN's OWN season.type; absence returns NHL/NBA to preseason STUBS"),
    ("game_key",            "espn_sports.py",  "merge identity for the stub supplement; a key on an absent field = silent +0"),

    # --- kid_chains.py : recurring national-chain kids' programs (2026-10-01) -
    ("PROGRAMS",            "kid_chains.py",   "the chain registry; absence = Home Depot/IKEA/Cabela's silently gone, no error"),
    ("fetch_all",           "kid_chains.py",   "additive+soft-fail entry; row_fn injected, never duplicates the 20-key schema"),
    ("nth_weekday",         "kid_chains.py",   "cadence dates are COMPUTED from a rule, never typed -- no stale-date class"),
    ("season_intersects",   "kid_chains.py",   "standing programs season-gated to the WINDOW's months; off-season emits nothing"),

    # --- deals --------------------------------------------------------------
    ("pumpkintrail",        "deals_overlay.py", "a standing-deal source; overlay is STEP 4.35, never a STEP 2 search"),
    ("window_months",       "deals_yield.py",  "the season gate reads the WINDOW's months; the run month alone was a FALSE OK"),
    ("in_season",           "deals_yield.py",  "takes a SET; an int raises TypeError so a reverted caller cannot pass silently"),

    # --- carried-row time repair (the THIRD ratchet, 2026-09-30) -------------
    ("OFFSETS",             "ical_time_repair.py", "the only two Central UTC offsets; admitting others turns a fingerprint into a curve fit"),
    ("plan",                "ical_time_repair.py", "pure decision fn -- GROUP set-match, so --dry-run and --apply cannot disagree"),
    ("skip_no_offset_match","ical_time_repair.py", "the partially-shifted-group counter; a per-row nearest match would move a real event"),

    # --- publish / log / STEP 1 plumbing ------------------------------------
    ("sha1",                "publish_feed.py", "verify by git blob SHA-1, never by size (size gave a false parks.csv FAIL)"),
    ("image_backfill",      "errlog_step7.py", "asserts STEP 4.5 RAN; the other HALF of the two-part assertion"),
    ("_image_backfill.json","errlog_step7.py", "the marker path it asserts exists AND is fresh, before any append"),
    ("run_date",            "errlog_step7.py", "checks the marker's stamp; either half alone passes on a stale value"),
    ("_regen_run_summary",  "errlog_step7.py", "the LANDED mk_run_summary promotion; counts READ from built CSVs, never typed"),
    ("FILES",               "base_from_csvs.py", "rebuilds the carried base from the published CSVs"),
    ("divergence",          "base_from_csvs.py", "reports base-vs-published drift"),
    ("run_date_verified",   "findings_init.py", "the mandatory _findings.json row errlog_step7 asserts by content"),
]

# ---------------------------------------------------------------------------
# NEGATIVE CONTROL (CLAUDE.md rule 2).  These names are quoted in CLAUDE.md as the
# cautionary example of a grep list written from memory instead of from the file.
# They must NOT exist.  A hit here means the audit is matching too loosely.
# ---------------------------------------------------------------------------
KNOWN_ABSENT = [
    ("ANCHOR_SRC",           "sports_dedup.py", "CLAUDE.md's own example of a target invented from memory"),
    ("one_home_game_per_day","sports_dedup.py", "ditto; a mechanical reader of the prose reports a FALSE stranding"),
]

# Targets whose string is also ordinary data, so a bare hit proves nothing.
# CLAUDE.md: "open na() and confirm the strip is TRAILING-ONLY; a hit on an over-broad
# variant is the wrong-merge error passing an audit designed to catch its absence."
NEEDS_EYES = {("minnesota", "dupsweep.py"): "confirm the state strip is TRAILING-ONLY (anchored $)"}


def _read(fn):
    p = os.path.join(RUNDIR, fn)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    verbose = "--verbose" in sys.argv
    cache, misses, control_hits, eyes = {}, [], [], []

    for tgt, fn, why in TARGETS:
        if fn not in cache:
            cache[fn] = _read(fn)
        src = cache[fn]
        if src is None:
            misses.append((tgt, fn, "FILE ABSENT", why))
        elif tgt not in src:
            misses.append((tgt, fn, "target not found", why))
        else:
            if (tgt, fn) in NEEDS_EYES:
                eyes.append((tgt, fn, NEEDS_EYES[(tgt, fn)]))
            if verbose:
                print(f"  PASS  {tgt:<22} {fn}")

    for tgt, fn, why in KNOWN_ABSENT:
        if fn not in cache:
            cache[fn] = _read(fn)
        src = cache[fn]
        if src is not None and tgt in src:
            control_hits.append((tgt, fn, why))

    files = sorted({fn for _, fn, _ in TARGETS})
    print(f"\nfeature_grep: {len(TARGETS)} targets over {len(files)} root files")
    print(f"  passed  : {len(TARGETS) - len(misses)}")
    print(f"  MISSING : {len(misses)}")
    print(f"  negative controls: {len(KNOWN_ABSENT)} asserted absent, {len(control_hits)} unexpectedly present")

    for tgt, fn, reason, why in misses:
        print(f"\n  MISS  {tgt}  ({fn}) -- {reason}")
        print(f"        load-bearing because: {why}")
        print(f"        -> open the file and look for the feature under ANOTHER SHAPE before rebuilding it.")
    for tgt, fn, why in control_hits:
        print(f"\n  CONTROL HIT  {tgt} ({fn}) -- this name should NOT exist. {why}")
    for tgt, fn, note in eyes:
        print(f"\n  NEEDS EYES  {tgt} ({fn}) -- {note}")

    ok = not misses and not control_hits
    print("\nRESULT:", "PASS -- no stranding recurrence" if ok else "FAIL -- investigate above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
