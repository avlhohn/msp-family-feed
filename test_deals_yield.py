#!/usr/bin/env python3
"""
test_deals_yield.py -- the season gate, and the WIRING that carries the window into it.

WHY THIS FILE EXISTS (2026-09-30):
    `deals_yield.py` scored `dnr_free_park_days` as "out of season - zero is CORRECT, not a
    failure" on a run whose window (2026-09-30 .. 2026-11-30) CONTAINS the Nov 27 free park
    day. The gate asked "is this source in season TODAY?" while the feed publishes a rolling
    62-day WINDOW. That is a FALSE OK, and this project rates a false PASS worse than a false
    negative: a shortfall gets investigated, an "OK" never does.

THE WIRING CASES ARE THE POINT, NOT THE UNIT CASES.
    The first version of this suite tested `window_months()` and `in_season()` directly and
    was GREEN against a mutant that reverted main() to `months = {int(run_date[5:7])}` -- i.e.
    green against the exact defect it was written to catch. Unit-testing both halves of a
    wire does not test the wire. The `end-to-end` block below runs the script as a
    subprocess and reads the VERDICT out of its own output.

Usage:
    python3 test_deals_yield.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
os.environ.setdefault("MSP_TODAY", "2026-09-30")
os.environ.setdefault("MSP_END", "2026-11-30")

import deals_yield as D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)) or "."
SCRIPT = os.path.join(HERE, "deals_yield.py")

CATS = ("events", "parks", "meal_deals", "volunteer_opportunities", "restaurants")

P = F = 0


def fixture(counts):
    """Build a SYNTHETIC input file. See the note in run_script for why this exists.

    `counts` maps a deal_source key -> how many rows carry it. Attribution is the `deal_source`
    provenance field, per the registry rule that it is NEVER a substring scan of
    deal_description. `has_deal` is also required: `deals_yield.py` only considers a row a deal
    row when `has_deal` is truthy or the row sits in `meal_deals`, so a fixture without it
    yields 0 for every source and every assertion below reads `warning` -- which is how the
    first draft of this fixture failed. The fixture has to satisfy the script's real gate, not
    a remembered version of it.
    """
    d = {c: [] for c in CATS}
    for key, n in counts.items():
        for i in range(n):
            d["parks"].append({"title": f"{key} row {i}", "date": "", "deal_source": key,
                               "has_deal": True, "deal_description": f"{key} deal {i}",
                               "city": "Saint Paul"})
    return d


def chk(label, got, want):
    global P, F
    if got == want:
        P += 1
    else:
        F += 1
        print(f"  FAIL  {label}: got {got!r} want {want!r}")


def raises(label, fn, exc):
    global P, F
    try:
        fn()
    except exc:
        P += 1
        return
    except Exception as e:  # wrong exception is a fail, not a pass
        F += 1
        print(f"  FAIL  {label}: raised {type(e).__name__}, wanted {exc.__name__}")
        return
    F += 1
    print(f"  FAIL  {label}: did not raise {exc.__name__}")


def run_script(today, end, flags=(), counts=None):
    """Run the real script in a THROWAWAY cwd, against a SYNTHETIC input.

    Two separate stale-artifact hazards, and the first version of this suite closed only one.

    OUTPUT side: `deals_yield.py` writes `_deals_yield.json` relative to cwd, and that file is
    a RUN-SCOPED artifact `errlog_step7.py` reads. A suite that runs the script in the repo
    folder would silently clobber the live run's copy with a test fixture's counts -- the
    stale-input hazard this project documents, manufactured by its own test. So cwd is a
    tempdir.

    INPUT side -- FIXED 2026-09-30, and this is the instructive half. The suite originally
    passed the LIVE `_compiled_work.json` as its fixture. That file is rewritten repeatedly by
    the pipeline, so the WIRING assertions below had no fixed answer: run at STEP 1 the DNR
    source has no `deal_source` stamp and the gate says `warning`, run again after the STEP
    4.35 overlay has stamped 213 DNR rows and the same assertion correctly reads `info`. The
    suite therefore reported 34/0 early in the 2026-09-30 run and 33/1 later, WITH NO CODE
    CHANGE -- a baseline whose value depends on when you execute it is not a baseline, and it
    is the shape this project keeps finding: two gates, one diagnosis, and only one closed.
    A test must own its inputs as well as its outputs.
    """
    e = dict(os.environ)
    e.pop("MSP_TODAY", None)
    e.pop("MSP_END", None)
    if today is not None:
        e["MSP_TODAY"] = today
    if end is not None:
        e["MSP_END"] = end
    tmp = tempfile.mkdtemp(prefix="dy_test_")
    work = os.path.join(tmp, "_fixture_work.json")
    with open(work, "w", encoding="utf-8") as fh:
        json.dump(fixture(counts if counts is not None else {}), fh)
    r = subprocess.run([sys.executable, "-B", SCRIPT, work] + list(flags),
                       capture_output=True, text=True, env=e, cwd=tmp)
    r.rows = []
    out = os.path.join(tmp, "_deals_yield.json")
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            r.rows = json.load(fh).get("rows", [])
    shutil.rmtree(tmp, ignore_errors=True)
    return r


def verdict(r, item):
    """('warning'|'info', full description) for one source, read from the JSON ARTIFACT.

    Deliberately NOT parsed out of stdout: the console line truncates the description at 88
    chars, which silently defeated an assertion on the window's month list. Read what the
    consumer reads.
    """
    for row in r.rows:
        if row.get("item") == item:
            return row.get("severity"), row.get("description", "")
    return None, None


# ---------------------------------------------------------------- window_months
chk("09-30..11-30 spans {9,10,11}", D.window_months("2026-09-30", "2026-11-30"), {9, 10, 11})
chk("a single month", D.window_months("2026-09-01", "2026-09-30"), {9})
chk("one day", D.window_months("2026-09-30", "2026-09-30"), {9})
chk("year cross 12-15..01-31", D.window_months("2026-12-15", "2027-01-31"), {12, 1})
chk("13 months is all 12", D.window_months("2026-01-05", "2027-02-01"), set(range(1, 13)))
raises("reversed window is a crash", lambda: D.window_months("2026-11-30", "2026-09-30"), SystemExit)

# ---------------------------------------------------------------- in_season
chk("DNR live on {9,10,11} -- Nov 27 is in the window",
    D.in_season("dnr_free_park_days", {9, 10, 11}), True)
chk("DNR silent on {9,10} -- November is NOT in the window",
    D.in_season("dnr_free_park_days", {9, 10}), False)
chk("great_pumpkin_trail live on {9,10,11}", D.in_season("great_pumpkin_trail", {9, 10, 11}), True)
chk("marcus_kids_dream silent on {9,10,11}", D.in_season("marcus_kids_dream", {9, 10, 11}), False)
chk("kids_bowl_free live on {9,10,11} (Sept tail)", D.in_season("kids_bowl_free", {9, 10, 11}), True)
chk("kids_bowl_free silent on {10,11}", D.in_season("kids_bowl_free", {10, 11}), False)
chk("an unknown source is never live", D.in_season("nope", set(range(1, 13))), False)

# ice_castles was NARROWED to [(1,2)] on 2026-09-30 -- see the comment in SEASONAL.
chk("ice_castles silent on {9,10,11}", D.in_season("ice_castles", {9, 10, 11}), False)
chk("ice_castles silent on {11,12} -- Nov never, Dec ~once a decade",
    D.in_season("ice_castles", {11, 12}), False)
chk("ice_castles live on {12,1}", D.in_season("ice_castles", {12, 1}), True)

# The OLD gate must be REJECTED LOUDLY, not silently honoured: `lo <= month <= hi` on an int
# is still valid Python, so a reverted caller would pass the old semantics through unnoticed.
raises("an int month raises TypeError", lambda: D.in_season("dnr_free_park_days", 9), TypeError)

# ---------------------------------------------------------------- STEP 1 dates: absence is a crash
for label, today, end in [("neither date supplied", None, None),
                          ("MSP_END missing", "2026-09-30", None),
                          ("MSP_TODAY missing", None, "2026-11-30"),
                          ("malformed MSP_TODAY", "2026-9-30", "2026-11-30"),
                          ("malformed MSP_END", "2026-09-30", "30-11-2026"),
                          ("empty MSP_TODAY", "", "2026-11-30")]:
    r = run_script(today, end)
    chk(f"{label} -> crash, never the sandbox clock",
        (r.returncode != 0 and "must come from STEP 1" in r.stderr), True)

r = run_script(None, None, flags=["--run-date", "2026-09-30", "--end-date", "2026-11-30"])
chk("flags supply both dates with no env", r.returncode, 0)
# and the input path is not eaten by a flag's value
chk("the positional path survives flag parsing", "deals yield check" in r.stdout, True)

# ---------------------------------------------------------------- END-TO-END: the wiring
# These are the cases a unit test of the two halves does NOT cover, and they are the ones
# that catch main() reverting to the run month.
r = run_script("2026-09-30", "2026-11-30")
chk("live run exits 0", r.returncode, 0)
sev, desc = verdict(r, "dnr_free_park_days")
chk("WIRING: DNR WARNS on a window reaching Nov 30", sev, "warning")
chk("WIRING: and says IN SEASON", "IN SEASON" in (desc or ""), True)
chk("WIRING: and prints the window's months, not the run month", "9,10,11" in (desc or ""), True)

# The in-season source that DOES have rows. This case was MISSING while the suite read the live
# `_compiled_work.json`, because the fixture supplied the answer instead of the assertion: once
# the STEP 4.35 overlay stamped 213 DNR rows, the "warns" case above silently became this one and
# reported a FAILURE. Both halves are now pinned, so neither can impersonate the other.
r = run_script("2026-09-30", "2026-11-30", counts={"dnr_free_park_days": 213})
sev, desc = verdict(r, "dnr_free_park_days")
chk("WIRING: an IN-SEASON source WITH rows does not warn", sev, "info")
# Asserted on the COUNT, not on the absence of the words "out of season". The healthy
# description legitimately contains that phrase inside its explanatory clause ("a zero here is
# a real finding even when the source is out of season TODAY"), so a loose negative substring
# check fails against correct output -- the documented isolate-the-phrase-under-test error,
# reproduced while writing this very case.
chk("WIRING: and reports the attributed row count", "213 rows" in (desc or ""), True)
chk("WIRING: and still names the window's months", "9,10,11" in (desc or ""), True)
chk("WIRING: a source at 0 in the SAME run still warns (per-source, never aggregate)",
    verdict(r, "kids_bowl_free")[0], "warning")

r = run_script("2026-09-30", "2026-10-31")
sev, desc = verdict(r, "dnr_free_park_days")
chk("WIRING: DNR stays SILENT on a window ending Oct 31", sev, "info")
chk("WIRING: and says out of season for the WHOLE window",
    "WHOLE window" in (desc or ""), True)

sev, _ = verdict(r, "ice_castles")
chk("WIRING: ice_castles silent on an autumn window", sev, "info")
r = run_script("2026-12-01", "2027-01-31")
sev, _ = verdict(r, "ice_castles")
chk("WIRING: ice_castles warns on a window reaching January", sev, "warning")

# A YEAR_ROUND source must not be reachable by the season gate at all.
r = run_script("2026-09-30", "2026-11-30")
sev, desc = verdict(r, "melsa_smartpass")
chk("year-round sources are scored without a season note", "season" in (desc or "").lower(), False)

print(f"\n{P} passed, {F} failed")
sys.exit(1 if F else 0)
