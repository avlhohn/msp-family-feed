#!/usr/bin/env python3
"""Tests for the sports-coverage tripwire.

The load-bearing test is `test_in_season_miss_warns`: a team that HAS a home
game in the window but zero rows must produce a shortfall. If that ever stops
firing, the tripwire is decorative. Every fixture below is a real shape from the
2026-09-19 feed, not a synthetic one.
"""
import datetime as _dt
import sports_coverage as S

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


def ev(title):
    return {"title": title}


# A small fake registry so the test does not depend on the live TEAMS list.
# (name, tier, aliases, active_months)
FAKE = [
    ("Test United", "pro", ["test united", "tufc"], {3, 4, 5, 6, 7, 8, 9, 10, 11}),
    ("Test Saints", "pro", ["test saints"], {4, 5, 6, 7, 8}),
    ("Test Gophers", "college", ["test gophers"], {9, 10, 11, 12, 1, 2}),
]

OCT = (_dt.date(2026, 9, 19), _dt.date(2026, 10, 31))   # months {9,10}
JAN = (_dt.date(2027, 1, 5), _dt.date(2027, 2, 28))     # months {1,2}


# --- the load-bearing test: an in-season team with zero rows MUST warn ---
def test_in_season_miss_warns():
    events = [ev("Test Gophers Football vs Iowa")]  # United + Saints absent
    summary, shorts = S.coverage(events, FAKE, *OCT)
    names = [n for n, t in shorts]
    check("in-season miss (United) warns", "Test United" in names)
    check("in-season covered team (Gophers) does NOT warn", "Test Gophers" not in names)


# --- the anti-false-alarm test: an off-season team with zero rows stays SILENT ---
def test_offseason_miss_silent():
    events = [ev("Test United vs Portland"), ev("Test Gophers Hockey")]
    summary, shorts = S.coverage(events, FAKE, *OCT)  # Saints season ends Aug
    names = [n for n, t in shorts]
    check("off-season team (Saints) stays silent in Oct", "Test Saints" not in names)
    check("off-season Saints listed as offseason", "Test Saints" in summary["offseason"])


def test_present_team_covered():
    events = [ev("Test United vs Portland Timbers"), ev("Test Saints baseball")]
    summary, shorts = S.coverage(events, FAKE, *OCT)
    check("United with a row is covered", "Test United" in summary["covered"])
    check("United with a row not in shortfalls", "Test United" not in [n for n, t in shorts])


def test_alias_matching_is_substring_titleonly():
    events = [ev("Big TUFC Watch Party Downtown")]  # alias 'tufc', different case
    summary, shorts = S.coverage(events, FAKE, *OCT)
    check("alias matches case-insensitively as substring",
          "Test United" in summary["covered"])


def test_window_crossing_year_boundary():
    # Dec->Jan window should include a Jan-only-season team as guarded.
    winter = (_dt.date(2026, 12, 20), _dt.date(2027, 1, 20))
    check("months span Dec+Jan", S._months_spanned(*winter) == {12, 1})
    events = []  # nobody present
    summary, shorts = S.coverage(events, FAKE, *winter)
    names = [n for n, t in shorts]
    check("Gophers (Jan in season) warns in winter window", "Test Gophers" in names)
    check("United (Nov end) not guarded in Dec-Jan", "Test United" not in summary["guarded"])


def test_months_spanned_single_month():
    same = (_dt.date(2026, 10, 1), _dt.date(2026, 10, 31))
    check("single-month window is that month", S._months_spanned(*same) == {10})


def test_reversed_window_raises():
    try:
        S._months_spanned(_dt.date(2026, 10, 31), _dt.date(2026, 9, 1))
        check("reversed window raises", False)
    except ValueError:
        check("reversed window raises", True)


def test_empty_events_all_guarded_teams_warn():
    summary, shorts = S.coverage([], FAKE, *OCT)
    names = set(n for n, t in shorts)
    # In Oct, United + Gophers are guarded; Saints is off-season.
    check("empty feed warns United", "Test United" in names)
    check("empty feed warns Gophers", "Test Gophers" in names)
    check("empty feed does NOT warn off-season Saints", "Test Saints" not in names)


# --- structured-source corroboration (added 2026-09-22) -------------------
#
# The asymmetry under test: a structured report may only ever DOWNGRADE a
# shortfall to a true negative. It may never confirm one, and it may never
# soften one it did not cleanly answer.

ACTIVE = {9, 10}
WM = [9, 10]


def _attr(name, reports):
    return S.attribute_shortfall(name, "pro", ACTIVE, WM, reports)


def test_uncorroborated_shortfall_prose_unchanged():
    # A team with no structured source keeps the original 2026-09-19 prose.
    sev, desc = _attr("Minnesota State Mankato", {})
    check("no-report shortfall stays a warning", sev == "warning")
    check("no-report shortfall keeps sourcing-gap prose",
          "likely a STEP 2 sourcing gap" in desc)


def test_true_negative_downgrades_to_info():
    reports = {"espn_mnufc": {"source": "espn_mnufc", "status": "NO_HOME_IN_WINDOW",
                              "in_window": 0, "note": "13 home games total, 0 in window"}}
    sev, desc = _attr("Minnesota United", reports)
    check("NO_HOME_IN_WINDOW downgrades to info", sev == "info")
    check("downgraded prose says TRUE NEGATIVE", "TRUE NEGATIVE" in desc)
    # Each of the two below is deliberately CONJOINED with an info-branch-only
    # phrase. Asserted alone they are satisfied by the warning branch too, so
    # they would stay green under the mutant that removes the downgrade -- a
    # test whose NAME is a lie about what it pins (CLAUDE.md 2026-09-21).
    check("downgraded prose tells the reader not to re-open it",
          "Do not re-open this as a sourcing gap" in desc
          and "likely a STEP 2 sourcing gap" not in desc)
    check("downgraded prose quotes the source's own note",
          "13 home games total" in desc and "TRUE NEGATIVE" in desc)


def test_empty_status_also_downgrades():
    reports = {"espn_mnufc": {"source": "espn_mnufc", "status": "EMPTY", "in_window": 0}}
    sev, _ = _attr("Minnesota United", reports)
    check("EMPTY downgrades to info", sev == "info")


def test_error_status_never_downgrades():
    reports = {"espn_mnufc": {"source": "espn_mnufc", "status": "ERROR",
                              "in_window": 0, "note": "HTTP 403"}}
    sev, desc = _attr("Minnesota United", reports)
    check("ERROR stays a warning", sev == "warning")
    check("ERROR prose says NOT corroborated", "did NOT corroborate" in desc)
    # `"ERROR" in desc` alone can NEVER fail -- the downgraded branch cites the
    # status too. Conjoined with the absence of the true-negative claim, it
    # becomes a real assertion about which branch produced this prose.
    check("ERROR prose quotes the status without claiming a true negative",
          "ERROR" in desc and "TRUE NEGATIVE" not in desc)


def test_ok_status_with_zero_rows_never_downgrades():
    # The source fetched in-window home games and none reached events.csv.
    # That is a REAL defect and must not be softened.
    reports = {"espn_mnufc": {"source": "espn_mnufc", "status": "OK", "in_window": 2}}
    sev, desc = _attr("Minnesota United", reports)
    check("OK-with-rows stays a warning", sev == "warning")
    check("OK-with-rows prose says NOT corroborated", "did NOT corroborate" in desc)


def test_multi_source_team_needs_ALL_sources():
    # Gophers span football + basketball. One true negative is not enough.
    half = {"espn_gophers_fb": {"source": "espn_gophers_fb", "status": "EMPTY"}}
    sev, desc = _attr("Minnesota Gophers", half)
    check("partial multi-source report does NOT downgrade", sev == "warning")
    check("partial multi-source keeps sourcing-gap prose",
          "likely a STEP 2 sourcing gap" in desc)

    both = dict(half, **{"espn_gophers_mbb": {"source": "espn_gophers_mbb",
                                              "status": "NO_HOME_IN_WINDOW"}})
    sev2, desc2 = _attr("Minnesota Gophers", both)
    check("complete multi-source report downgrades", sev2 == "info")
    check("complete multi-source cites both keys in the DOWNGRADED prose",
          "espn_gophers_fb" in desc2 and "espn_gophers_mbb" in desc2
          and "TRUE NEGATIVE" in desc2)

    mixed = dict(half, **{"espn_gophers_mbb": {"source": "espn_gophers_mbb",
                                               "status": "ERROR"}})
    sev3, _ = _attr("Minnesota Gophers", mixed)
    check("one bad source among two blocks the downgrade", sev3 == "warning")


def test_source_keys_names_are_real_teams():
    # A typo'd display name in SOURCE_KEYS resolves to nothing and reads as
    # "no report" -- safe, but permanently invisible. Pin it.
    live = {nm for nm, tr, al, a in S.TEAMS}
    unknown = [k for k in S.SOURCE_KEYS if k not in live]
    check("every SOURCE_KEYS name exists in TEAMS", not unknown)


def test_load_structured_reports_soft_fails():
    check("missing feedpull file yields {}",
          S.load_structured_reports("/nonexistent/_feedpull_all.json") == {})


if __name__ == "__main__":
    for fn in list(globals().values()):
        if callable(fn) and getattr(fn, "__name__", "").startswith("test_"):
            fn()
    print(f"{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)
