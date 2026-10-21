#!/usr/bin/env python3
"""STEP 8 sports-coverage tripwire.

Sports are IN scope (SKILL.md:44) and enter the feed as `events` rows via STEP 2
free-text WebSearch — an untagged, non-deterministic path. So a named team can
silently drop to ZERO home-game rows in a window where it demonstrably has home
games (MNUFC did, 2026-09-19), and nothing warns. This helper is that warning.

It is deliberately shaped to AVOID the project's permanent-warning failure mode:
a team is only checked when the run window actually OVERLAPS its season, so a
genuinely out-of-season team (Saints/Aurora/Frost in October) stays silent
rather than warning every night forever.

Reads  : events.csv           (post-build, MSP_RUNDIR-relative)
Writes : _findings.json        (idempotent append; errlog_step7 turns each row
                                into an error_log.csv row at STEP 7)
Window : MSP_TODAY / MSP_END   (env; ABSENT IS A CRASH, per the delete-the-date-
                                literal rule — a date a helper can guess is a
                                date it will guess wrong)

Findings shapes (6-element lists, the _findings.json contract):
  ["info","events","STEP 8","sports_coverage","team_coverage","<summary>"]
  ["warning"|"info","events","STEP 8","sports_shortfall","<Team>","<why>"]

A shortfall's SEVERITY is no longer fixed (2026-09-22). Since 2026-09-20 some
teams also arrive from a structured source, whose per-team row in
`_feedpull_all.json` can prove a zero is a TRUE NEGATIVE rather than a sourcing
gap -- see the SOURCE_KEYS block below for the asymmetry that governs it. The
issue_type stays `sports_shortfall` in both cases, deliberately: the idempotent
strip at the bottom of this file keys on it by EXACT match, and renaming an
idempotency key silently breaks the idempotency it was keyed on.

`sports_coverage` / `sports_shortfall` do NOT collide with the reserved
error_log issue_types (`ical_feed_pull`, `deal_source_*`, `image_backfill`,
`run_summary`) — verified against errlog_step7 section 5.

Usage:
  MSP_TODAY=2026-09-19 MSP_END=2026-10-31 python3 sports_coverage.py [events.csv] [--dry-run]
"""
import os
import sys
import csv
import json
import datetime as _dt

RUNDIR = os.environ.get("MSP_RUNDIR", ".")


def _months_spanned(today, end):
    """Every calendar month touched by [today, end], inclusive, as a set of 1-12.

    Walks month by month so a window crossing a year boundary (e.g. Dec->Jan)
    is handled correctly."""
    if end < today:
        raise ValueError(f"MSP_END {end} precedes MSP_TODAY {today}")
    months = set()
    y, m = today.year, today.month
    while (y, m) <= (end.year, end.month):
        months.add(m)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return months


# (display name, tier, title-only lowercase substring aliases, active_months)
# active_months is the set of calendar months in which the team plays HOME games
# in a normal season. It is the season gate: a team is checked only when the run
# window's months intersect this set. Erring toward a NARROW season is correct —
# a missed shoulder-week is cosmetic, a permanent false warning trains the reader
# to skim the block (the project's standing rule).
TEAMS = [
    ("Minnesota Twins",        "pro", ["minnesota twins"],                                             {3, 4, 5, 6, 7, 8, 9, 10}),
    ("Minnesota Vikings",      "pro", ["minnesota vikings"],                                           {8, 9, 10, 11, 12, 1}),
    ("Minnesota Wild",         "pro", ["minnesota wild"],                                              {10, 11, 12, 1, 2, 3, 4}),
    ("Minnesota Timberwolves", "pro", ["timberwolves"],                                                {10, 11, 12, 1, 2, 3, 4}),
    ("Minnesota Lynx",         "pro", ["minnesota lynx"],                                              {5, 6, 7, 8, 9, 10}),
    ("Minnesota United",       "pro", ["minnesota united", "mnufc", "united fc"],                      {3, 4, 5, 6, 7, 8, 9, 10, 11}),
    ("St. Paul Saints",        "pro", ["st. paul saints", "saint paul saints", "st paul saints"],      {4, 5, 6, 7, 8}),
    ("Minnesota Aurora",       "pro", ["minnesota aurora"],                                            {5, 6, 7}),
    ("Minnesota Frost",        "pro", ["minnesota frost"],                                             {11, 12, 1, 2, 3, 4, 5}),
    ("Minnesota Gophers",      "college", ["gophers"],                                                 {9, 10, 11, 12, 1, 2}),
    ("Minnesota Duluth (UMD)", "college", ["minnesota duluth", "umd bulldogs"],                        {9, 10, 11, 12, 1, 2}),
    ("Minnesota State Mankato","college", ["mankato state", "minnesota state mankato", "mankato mavericks"], {9, 10, 11, 12, 1, 2}),
    ("St. Cloud State",        "college", ["st. cloud state", "st cloud state", "saint cloud state"],  {9, 10, 11, 12, 1, 2}),
    ("Winona State",           "college", ["winona state"],                                            {9, 10, 11, 12, 1, 2}),
    ("Bemidji State",          "college", ["bemidji state"],                                           {9, 10, 11, 12, 1, 2}),
]


# --- structured-source corroboration (added 2026-09-22) -------------------
#
# Since 2026-09-20 eight of the teams above also arrive from a STRUCTURED source
# (`espn_sports.py`, dispatched by `run_espn_sports()`), which writes a per-team
# row into `_feedpull_all.json`'s `report` list. For those teams a zero is no
# longer ambiguous: the source's own status says whether the schedule PARSED and
# simply carried no in-window home date, or whether the fetch failed.
#
# So this helper's fixed warning prose -- "likely a STEP 2 sourcing gap" -- had
# become an over-claim for registry teams, which is what CLAUDE.md 2026-09-21
# asked to be softened AT SOURCE rather than annotated by hand each run.
#
# THE ASYMMETRY IS THE WHOLE DESIGN. A structured report can only ever DOWNGRADE
# a shortfall to a true negative, never confirm one:
#   * no report (team not in the registry)  -> prose UNCHANGED, still a warning.
#   * NO_HOME_IN_WINDOW / EMPTY             -> DOWNGRADE to info; the schedule
#                                              parsed, so this is a true negative.
#   * ERROR / anything else                 -> STRENGTHENED, never softened; a
#                                              failed fetch presenting as a zero
#                                              is the exact thing being guarded.
#
# SOURCE_KEYS is a HAND TABLE, not an inference from the alias list -- the
# `DENYLIST` / `KEEP_APART` discipline. Guessing a source key from a display name
# would silently resolve to nothing and read as "no report", i.e. it would fail
# in the direction that keeps the warning, which is safe but invisible.
#
# Each value is a TUPLE, because one display name can span several structured
# sources: `Minnesota Gophers` covers both `espn_gophers_fb` and
# `espn_gophers_mbb`. A downgrade then requires EVERY registered key to have a
# report AND every one of them to be a true negative -- a football schedule
# saying "no home game" says nothing about basketball, so corroborating a team
# on one of its two sources would be the partial-evidence error.
SOURCE_KEYS = {
    "Minnesota Twins":        ("espn_twins",),
    "Minnesota Vikings":      ("espn_vikings",),
    "Minnesota Timberwolves": ("espn_timberwolves",),
    "Minnesota Wild":         ("espn_wild",),
    "Minnesota Lynx":         ("espn_lynx",),
    "Minnesota United":       ("espn_mnufc",),
    "Minnesota Gophers":      ("espn_gophers_fb", "espn_gophers_mbb"),
}

# Statuses that mean "the schedule was fetched and parsed, and carries no
# in-window home game". Anything else -- ERROR above all -- must not downgrade.
TRUE_NEGATIVE_STATUS = ("NO_HOME_IN_WINDOW", "EMPTY")


def load_structured_reports(path):
    """Read `_feedpull_all.json`'s `report` list into {source_key: row}.

    SOFT-FAIL by design: a missing, unreadable or differently-shaped feedpull
    file returns {}, which downgrades nothing and leaves every shortfall
    carrying its original warning. The corroboration is allowed to be absent;
    it is never allowed to be invented."""
    try:
        with open(path) as f:
            blob = json.load(f)
        rows = blob.get("report") or []
        out = {}
        for r in rows:
            if isinstance(r, dict) and r.get("source"):
                out[r["source"]] = r
        return out
    except Exception:
        return {}


def attribute_shortfall(name, tier, active, window_months, reports):
    """Pure: given one shortfall and the structured reports, return
    (severity, description). No I/O, so the test can drive it with an explicit
    reports dict."""
    base = (f"{tier} team {name} has 0 in-window rows but its season "
            f"({sorted(active)}) overlaps the run window {window_months}")
    keys = SOURCE_KEYS.get(name) or ()
    present = [(k, reports[k]) for k in keys if k in reports]

    if not keys or len(present) != len(keys):
        # No structured source for this team, or only SOME of its sources
        # reported -- the 2026-09-19 prose stands unchanged, because nothing
        # (or not enough) corroborates the zero.
        return "warning", (
            f"{base} — likely a STEP 2 sourcing gap, not an off-season. "
            f"Add/verify a home-game search for this team."
        )

    def _cite(k, r):
        note = str(r.get("note") or "").strip()
        return f"`{k}` {r.get('status')}" + (f' ("{note}")' if note else "")

    cites = "; ".join(_cite(k, r) for k, r in present)
    bad = [(k, r) for k, r in present
           if str(r.get("status") or "") not in TRUE_NEGATIVE_STATUS]

    if not bad:
        return "info", (
            f"{base} — but this is a TRUE NEGATIVE, not a sourcing gap. The "
            f"structured source reported {cites}. The schedule parsed, which "
            f"rules out a fetch failure presenting as a zero, and carries no "
            f"home date in the window. Do not re-open this as a sourcing gap "
            f"or add a WebSearch for it."
        )
    return "warning", (
        f"{base} — and the structured source did NOT corroborate it: {cites}. "
        f"A source that did not cleanly report an empty in-window schedule "
        f"cannot downgrade this zero; check that team's ESPN endpoint before "
        f"concluding anything about the feed."
    )


def coverage(events, teams, today, end):
    """Pure core: given event dicts + a team registry + the window, return
    (summary_dict, shortfalls). No I/O, so the test can drive it with explicit
    dates and a small fake registry.

    A team is `guarded` iff the window's months intersect its active_months.
    A guarded team with zero title-matching rows is a shortfall (the tripwire).
    An unguarded (off-season) team is reported for context but never warns."""
    window_months = _months_spanned(today, end)
    titles = [(e.get("title") or "").lower() for e in events]

    per_team = []
    shortfalls = []
    for name, tier, aliases, active in teams:
        n = sum(1 for t in titles if any(a in t for a in aliases))
        guarded = bool(window_months & active)
        per_team.append((name, tier, n, guarded))
        if guarded and n == 0:
            shortfalls.append((name, tier))

    covered = [name for name, tier, n, g in per_team if g and n > 0]
    offseason = [name for name, tier, n, g in per_team if not g]
    summary = {
        "window_months": sorted(window_months),
        "guarded": [name for name, tier, n, g in per_team if g],
        "covered": covered,
        "shortfalls": [name for name, tier in shortfalls],
        "offseason": offseason,
        "per_team": per_team,
    }
    return summary, shortfalls


def _load_events(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _load_findings(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def main(argv):
    dry = "--dry-run" in argv
    positional = [a for a in argv[1:] if not a.startswith("--")]
    events_path = positional[0] if positional else os.path.join(RUNDIR, "events.csv")

    t = os.environ.get("MSP_TODAY")
    e = os.environ.get("MSP_END")
    if not t or not e:
        sys.exit("sports_coverage: MSP_TODAY and MSP_END must both be set "
                 "(a date a helper can guess is a date it will guess wrong)")
    try:
        today = _dt.date.fromisoformat(t)
        end = _dt.date.fromisoformat(e)
    except ValueError as ex:
        sys.exit(f"sports_coverage: malformed MSP_TODAY/MSP_END: {ex}")

    events = _load_events(events_path)
    summary, shortfalls = coverage(events, TEAMS, today, end)

    # Human-readable report (always printed; the exit status is not the signal —
    # read the lines, per the stderr/no-op discipline in CLAUDE.md).
    print(f"sports_coverage: window {today}..{end} months={summary['window_months']}")
    for name, tier, n, g in summary["per_team"]:
        state = "OK" if (g and n > 0) else ("MISS" if g else "off-season")
        print(f"  {name:26} {tier:8} rows={n:3}  {state}")
    print(f"  -> guarded={len(summary['guarded'])} covered={len(summary['covered'])} "
          f"shortfalls={len(shortfalls)} offseason={len(summary['offseason'])}")

    # Build findings: one info summary + one warning per in-season miss.
    covered_s = ", ".join(summary["covered"]) or "none"
    short_s = ", ".join(summary["shortfalls"]) or "none"
    off_s = ", ".join(summary["offseason"]) or "none"
    summary_desc = (
        f"window {today}..{end}; guarded {len(summary['guarded'])} teams; "
        f"covered: {covered_s}; shortfalls: {short_s}; off-season (not checked): {off_s}"
    )
    new_findings = [["info", "events", "STEP 8", "sports_coverage", "team_coverage", summary_desc]]

    # Corroborate each shortfall against THIS run's own structured reports.
    # Soft-fail: a missing feedpull file yields {} and downgrades nothing.
    reports = load_structured_reports(os.path.join(RUNDIR, "_feedpull_all.json"))
    print(f"  structured reports loaded: {len(reports)} source(s)")
    for name, tier in shortfalls:
        active = next(a for nm, tr, al, a in TEAMS if nm == name)
        sev, desc = attribute_shortfall(name, tier, active,
                                        summary["window_months"], reports)
        print(f"  shortfall {name:26} -> {sev}")
        new_findings.append([sev, "events", "STEP 8", "sports_shortfall", name, desc])

    if dry:
        print("--dry-run: would write", len(new_findings), "findings:")
        for f in new_findings:
            print("   ", f)
        return

    # Idempotent append: strip any prior sports_* rows before adding this run's.
    findings_path = os.path.join(RUNDIR, "_findings.json")
    existing = _load_findings(findings_path)
    kept = [f for f in existing
            if not (isinstance(f, list) and len(f) >= 4
                    and f[3] in ("sports_coverage", "sports_shortfall"))]
    kept.extend(new_findings)
    with open(findings_path, "w") as f:
        json.dump(kept, f, indent=2)
    print(f"sports_coverage: wrote {len(new_findings)} findings to {findings_path} "
          f"(total now {len(kept)})")


if __name__ == "__main__":
    main(sys.argv)
