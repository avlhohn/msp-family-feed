#!/usr/bin/env python3
"""
STEP 7 helper - per-source deals yield check.

WHY THIS EXISTS
---------------
On 2026-08-22 the entire deals/discount cluster produced almost nothing and NOTHING WAS
LOGGED. The error log had 33 rows for iCal pulls and 15 for library feeds, and zero rows for
any deal source. A silent zero is indistinguishable from a step that never ran.

This emits one error-log row PER SOURCE so a zero is visible and attributable.

Aggregate counts are useless here: several sources are legitimately zero out of season
(DNR free park days, Kids Bowl Free, Marcus Kids Dream). An aggregate hides "smARTpass
returned nothing" behind "the seasonal ones are correctly zero." Hence per-source, with an
explicit seasonal allowlist.

THE SEASON GATE TESTS THE WINDOW, NOT THE RUN MONTH (fixed 2026-09-30)
----------------------------------------------------------------------
It used to read `month = int(run_date.split("-")[1])` and ask "is this source in season
TODAY?". But this pipeline publishes a ROLLING WINDOW (TODAY .. END_DATE, up to ~62 days),
so a source can be out of season today and plainly in season inside the window it is being
scored against. On 2026-09-30 (window 09-30..11-30) `dnr_free_park_days` was scored
"out of season - zero is CORRECT, not a failure" on a window that CONTAINS the Nov 27 free
park day. That is a FALSE OK, and this project rates a false PASS worse than a false warning:
a shortfall gets investigated, an "OK" never does.

The gate is now a WINDOW-OVERLAP gate, the same shape `sports_coverage.py` already uses for
its per-team `active_months`: a source is live if ANY month the window touches is in its
range. The window comes from MSP_TODAY/MSP_END (or --run-date/--end-date) and its ABSENCE IS
A CRASH, never a default -- a date a helper can guess is a date it will guess wrong.

Usage:
    MSP_TODAY=2026-09-30 MSP_END=2026-11-30 python3 deals_yield.py _compiled_work.json
    python3 deals_yield.py _compiled_work.json --run-date 2026-09-30 --end-date 2026-11-30
"""
import json
import os
import re
import sys
from datetime import date

CATS = ("events", "parks", "meal_deals", "volunteer_opportunities", "restaurants")

# Sources that CONTRIBUTE ROWS TO standing_deals.csv and are live year-round.
# A zero from any of these is a REAL failure. Membership here is a claim that the source
# publishes venue-level standing discounts - verify that before adding one.
YEAR_ROUND = {
    "melsa_smartpass": "smartpass.melsa.org",
    "venue_direct_kids_eat_free": "venue-direct kids-eat-free pages (Andiamo, Ze's, Tipsy Steer, Smashburger)",
    "venue_direct_museum_free": "venue-direct museum free-admission pages (Walker)",
}

# Fetched every run, but NOT contributors to the standing-deal table. Reporting zero here is
# the correct steady state, so these must never warn.
#
# The distinction matters: a source can be healthy, useful and correctly fetched while
# contributing nothing to THIS table. Filing such a source under YEAR_ROUND makes it warn on
# every single run forever, and a permanent warning is worse than no warning - it teaches the
# reader to skim past the whole block, which is how the original silent failure survived.
NON_TABLE = {
    "thrifty_minnesota": "thriftyminnesota.com is an events/articles site, not a venue-discount "
                         "list. Probed 2026-08-22: the homepage yields dated events (feed those "
                         "to STEP 2) and its state-park page only mirrors the DNR dates, which "
                         "dnr_free_park_days already covers. Useful as corroboration, not a "
                         "table contributor.",
}

# Retired sources: no longer fetched, but historical rows may still carry the provenance key.
RETIRED = {
    "upparent": "upparent.com returns 403 to WebFetch (2026-08-22); coverage overlaps the "
                "Frugal Mom kids-eat-free list. See deal-source-registry.md.",
    "frugalmom_discount_guide": "Twin Cities Frugal Mom discount guide - RETIRED as a fetch "
                "source 2026-08-28 at the owner's request. Her guide mostly aggregates "
                "publicly-true venue facts (Como free, Mia free, Museums for All, MNHS "
                "income-qualifying rates) but also carried deals EXCLUSIVE to her (branded "
                "codes TCFM / FRUGALMOM25 / TCFMB), which should not be republished. The "
                "public venue facts already captured stay in standing_deals.csv; source any "
                "new ones from the venues/CVBs directly. See deal-source-registry.md.",
    "frugalmom_kids_eat_free": "Twin Cities Frugal Mom kids-eat-free list - RETIRED as a fetch "
                "source 2026-08-28 at the owner's request (see frugalmom_discount_guide). "
                "Existing kids-eat-free rows stay; re-confirm new ones from each venue directly.",
}

# Month ranges (inclusive) in which each seasonal source can plausibly yield.
#
# ERRING NARROW IS DELIBERATE, and now costs more than it used to: the gate below tests the
# whole WINDOW, so a range that is one month too generous warns on every run whose window
# merely TOUCHES that month -- roughly two months of runs, not one. A missed shoulder-week is
# cosmetic; a permanent false warning trains the reader to skim the whole block, which is how
# the original silent failure survived.
SEASONAL = {
    "dnr_free_park_days": [(1, 1), (4, 4), (6, 6), (11, 11)],
    "kids_bowl_free": [(5, 9)],
    # Narrowed from (6,8) on 2026-08-23. Two probes that day: the dedicated
    # /promotions-and-events/kids-dream page returns 404, and the live
    # /promotions-and-events index lists only fall titles (Harry Potter Passport,
    # Hunger Games Passport, Met Opera) with no kids summer series. The series is
    # over well before August ends, so a (6,8) window made this WARN every
    # late-August run about a source that was behaving correctly -- exactly the
    # permanent-warning failure the NON_TABLE note above exists to prevent.
    "marcus_kids_dream": [(6, 7)],
    # Narrowed from [(11,12),(1,2)] on 2026-09-30, when the switch to a window gate turned
    # (11,12) into a warning on every autumn run. VERIFIED, not assumed: the most recent MN
    # season ran Jan 16 - Feb 21 2026, and Ice Castles' own CEO, on the year the company
    # called its "earliest opening in a decade" (Dec 31), said "this is only the SECOND time
    # we've been able to open before New Year's Day." So November is never live and December
    # is live roughly once a decade, on its final day.
    # THE COST IS STATED RATHER THAN HIDDEN: in a year that does open Dec 31, a zero on that
    # one day goes unwarned. That is the marcus_kids_dream (6,8)->(6,7) trade of 2026-08-23 --
    # one cosmetic miss bought in exchange for not warning falsely every single autumn run.
    "ice_castles": [(1, 2)],
    "great_pumpkin_trail": [(9, 10)],
}


def truthy(v):
    return str(v).strip().lower() in ("true", "yes", "1")


def window_months(start_iso, end_iso):
    """The SET of calendar months the run window touches, inclusive, year-crossing safe.

    A rolling window up to ~62 days long spans 2-3 months, and the whole point of the fix is
    that the run month alone is not the window.  Returns e.g. {9,10,11} for 09-30..11-30 and
    {12,1} for 12-15..01-31.
    """
    sy, sm = int(start_iso[:4]), int(start_iso[5:7])
    ey, em = int(end_iso[:4]), int(end_iso[5:7])
    if (ey, em) < (sy, sm):
        raise SystemExit(f"deals_yield: END ({end_iso}) precedes TODAY ({start_iso})")
    months, y, m = set(), sy, sm
    while (y, m) <= (ey, em):
        months.add(m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def in_season(name, months):
    """True if ANY month the window touches falls in the source's season.

    `months` is a SET (window-overlap), never a single int.  Passing an int here silently
    reverts the 2026-09-30 fix -- `lo <= month <= hi` on an int is the OLD gate and is still
    valid Python -- so the int case is rejected loudly instead.
    """
    if isinstance(months, int):
        raise TypeError("in_season() takes the WINDOW's month SET, not the run month")
    for lo, hi in SEASONAL.get(name, []):
        if any(lo <= mo <= hi for mo in months):
            return True
    return False


ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _date_arg(flag, env, label):
    """A STEP 1 value: --flag wins, then the env var, then a CRASH. Never date.today().

    `run_date` used to default to the sandbox clock, which this project has caught being wrong
    -- and wrong IN AGREEMENT with the injected currentDate -- on two consecutive runs. A date
    a helper can guess is a date it will guess wrong.
    """
    v = ""
    if flag in sys.argv:
        i = sys.argv.index(flag) + 1
        v = sys.argv[i] if i < len(sys.argv) else ""
    v = (v or os.environ.get(env, "")).strip()
    if not ISO.match(v):
        raise SystemExit(
            f"deals_yield: {label} must come from STEP 1 -- set {env} or pass {flag} YYYY-MM-DD "
            f"(got {v!r}). Refusing to default to the sandbox clock."
        )
    return v


def main():
    # Positional args, with each --flag's VALUE consumed so a date is never mistaken for the
    # input path. The old one-liner dropped only tokens starting with "--", so `--run-date
    # 2026-09-30 _compiled_work.json` silently read the DATE as the path.
    args, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
            continue
        if a in ("--run-date", "--end-date"):
            skip = True
            continue
        if a.startswith("--"):
            continue
        args.append(a)
    path = args[0] if args else "_compiled_work.json"
    run_date = _date_arg("--run-date", "MSP_TODAY", "the run date")
    end_date = _date_arg("--end-date", "MSP_END", "the window END_DATE")
    months = window_months(run_date, end_date)

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    deal_rows = []
    for cat in CATS:
        for r in data.get(cat, []):
            if truthy(r.get("has_deal")) or cat == "meal_deals":
                deal_rows.append((cat, r))

    def attributed(key):
        """Count rows whose `deal_source` provenance field names this source.

        Deliberately an EXACT match on a provenance field, never a substring scan of the
        text. Substring scanning was tried first and produced nonsense - 'kids_bowl_free'
        matched every deal_description containing the word 'kids' (193 false hits).
        """
        return sum(1 for _cat, r in deal_rows if (r.get("deal_source") or "").strip() == key)

    log = []
    totals = {c: sum(1 for cat, _ in deal_rows if cat == c) for c in CATS}
    with_deal = {c: sum(1 for cat, r in deal_rows if cat == c and truthy(r.get("has_deal"))) for c in CATS}

    for name, frag in YEAR_ROUND.items():
        n = attributed(name)
        sev = "warning" if n == 0 else "info"
        log.append(
            dict(
                run_date=run_date,
                severity=sev,
                category="meal_deals",
                step="STEP2_deals_source",
                issue_type="deal_source_yield",
                item=name,
                description=(
                    f"{name} ({frag}) contributed {n} rows. "
                    + (
                        "ZERO from a year-round source. Four causes, in the order worth checking: "
                        "(1) the fetch succeeded but nothing was merged into standing_deals.csv - "
                        "the most common and least obvious; (2) the source_url in that CSV does "
                        "not contain this source's URL fragment, so rows exist but are "
                        "unattributable; (3) the URL moved; (4) the step did not run. "
                        "See deal-source-registry.md."
                        if n == 0
                        else "OK."
                    )
                ),
            )
        )

    for label, group in (("NON-TABLE", NON_TABLE), ("RETIRED", RETIRED)):
        for name, why in group.items():
            log.append(
                dict(
                    run_date=run_date,
                    severity="info",
                    category="meal_deals",
                    step="STEP2_deals_source",
                    issue_type="deal_source_" + label.lower().replace("-", "_"),
                    item=name,
                    description=f"{name} contributed {attributed(name)} rows; {label} - {why}",
                )
            )

    win = ",".join(str(m) for m in sorted(months))
    for name in SEASONAL:
        n = attributed(name)
        live = in_season(name, months)
        if not live:
            sev, note = "info", (
                f"out of season for the WHOLE window (months {win} vs season "
                f"{SEASONAL[name]}) - zero is CORRECT, not a failure."
            )
        else:
            sev = "warning" if n == 0 else "info"
            note = (
                f"IN SEASON somewhere inside the window (months {win} vs season "
                f"{SEASONAL[name]}). The window is what this feed publishes, so a zero here "
                "is a real finding even when the source is out of season TODAY."
            )
        log.append(
            dict(
                run_date=run_date,
                severity=sev,
                category="meal_deals",
                step="STEP2_deals_source",
                issue_type="deal_source_yield",
                item=name,
                description=f"{name} contributed {n} rows; {note}",
            )
        )

    # Structural tripwire: standing venue deals should reach parks and events, not just food.
    if with_deal["parks"] == 0:
        log.append(
            dict(
                run_date=run_date,
                severity="warning",
                category="parks",
                step="STEP4.35_deals_overlay",
                issue_type="no_park_deals",
                item="parks",
                description=(
                    f"0 of {totals['parks']} park rows carry a deal. The standing-deal overlay "
                    "did not run or matched nothing - see deals_overlay.py."
                ),
            )
        )

    with open("_deals_yield.json", "w", encoding="utf-8") as fh:
        json.dump({"rows": log, "with_deal": with_deal, "totals": totals}, fh, indent=1)

    warn = sum(1 for r in log if r["severity"] == "warning")
    print(f"deals yield check: {len(log)} log rows, {warn} warnings")
    for r in log:
        mark = "WARN" if r["severity"] == "warning" else "ok  "
        print(f"  [{mark}] {r['item']:28s} {r['description'][:88]}")
    print(f"  has_deal by category: {with_deal}")


if __name__ == "__main__":
    main()
