#!/usr/bin/env python3
"""
test_ical_time_repair.py -- the group set-match rule, and the CONTROLS that prove it is narrow.

The load-bearing cases are NOT "a shifted row gets repaired".  They are:

  * the CONTROL -- a two-session group (10 AM / 2 PM) where only ONE row is shifted must repair
    NOTHING, because a per-row nearest match would adopt the wrong session's time and silently
    move a real event.  This is the case the whole set-match design exists for, and a
    "repair the closest fresh time" implementation passes every other test in this file while
    failing this one.
  * the OFFSET control -- a +30min or +240min delta is a genuine source change or noise and must
    stay silent.  Admitting arbitrary offsets turns a fingerprint into a curve fit.
  * the DIRECTION control -- a date is only ever moved BACKWARD, out of the small-hours band.
    A pass that could move a date forward could invent an occurrence.
  * the INPUT control -- an absent or empty feed pull must CRASH, not report 0 repaired.

`plan()` is pure, so every case below asserts the DECISION rather than a file on disk, and
--dry-run cannot disagree with --apply.

Usage:
    python3 test_ical_time_repair.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import ical_time_repair as R  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)) or "."
P = F = 0


def chk(label, got, want):
    global P, F
    if got == want:
        P += 1
    else:
        F += 1
        print(f"  FAIL  {label}: got {got!r} want {want!r}")


def ev(title, date, time):
    return {"title": title, "date": date, "time": time}


def run(published, freshrows):
    return R.plan(published, R.index_fresh(freshrows))


# ---------------------------------------------------------------- mins / fmt round trip
chk("mins 6:30 PM", R.mins("6:30 PM"), 1110)
chk("mins 11:30 PM", R.mins("11:30 PM"), 1410)
chk("mins 12:00 AM is midnight, not noon", R.mins("12:00 AM"), 0)
chk("mins 12:00 PM is noon", R.mins("12:00 PM"), 720)
chk("mins 10:30 AM", R.mins("10:30 AM"), 630)
chk("a range is NOT a single time", R.mins("10:00 AM - 4:00 PM"), None)
chk("empty time", R.mins(""), None)
chk("None time", R.mins(None), None)
chk("a 24h string is not our format", R.mins("18:30"), None)
chk("minute overflow rejected", R.mins("6:99 PM"), None)
chk("fmt round-trips midnight", R.fmt(0), "12:00 AM")
chk("fmt round-trips noon", R.fmt(720), "12:00 PM")
chk("fmt round-trips 6:30 PM", R.fmt(1110), "6:30 PM")
chk("fmt/mins are inverse over the day",
    all(R.mins(R.fmt(n)) == n for n in range(0, 1440)), True)

# ---------------------------------------------------------------- the real defect
# The user-reported row: published 11:30 PM, freshly parsed 6:30 PM, same day.
pub = [ev("Family Craft Night: Painting Pumpkins!", "2026-10-01", "11:30 PM")]
fr = [ev("Family Craft Night: Painting Pumpkins!", "2026-10-01", "6:30 PM")]
rep, st = run(pub, fr)
chk("the reported row repairs", [(r[1], r[2]) for r in rep], [("2026-10-01", "6:30 PM")])
chk("and is counted under the CDT offset", st["repaired_time_300"], 1)

# CST, for a November run.  Retained even though this run measured 0 of them.
rep, _ = run([ev("Winter Storytime", "2026-12-02", "4:30 PM")],
             [ev("Winter Storytime", "2026-12-02", "10:30 AM")])
chk("a -360min group repairs too (CST)", [(r[1], r[2]) for r in rep],
    [("2026-12-02", "10:30 AM")])

# A whole group shifting together is the healthy multi-session case.
pub = [ev("Storytime", "2026-10-05", "3:30 PM"), ev("Storytime", "2026-10-05", "7:00 PM")]
fr = [ev("Storytime", "2026-10-05", "10:30 AM"), ev("Storytime", "2026-10-05", "2:00 PM")]
rep, _ = run(pub, fr)
chk("a 2-row group that shifts AS ONE repairs both",
    sorted(r[2] for r in rep), ["10:30 AM", "2:00 PM"])

# ---------------------------------------------------------------- THE CONTROL
# Two genuine sessions, and ONLY ONE published row is shifted.  The set match fails, so nothing
# is repaired.  A per-row nearest match would rewrite the 2:00 PM row to 10:30 AM and delete a
# real session's time.  THIS IS THE CASE THE DESIGN EXISTS FOR.
pub = [ev("Storytime", "2026-10-05", "3:30 PM"), ev("Storytime", "2026-10-05", "2:00 PM")]
fr = [ev("Storytime", "2026-10-05", "10:30 AM"), ev("Storytime", "2026-10-05", "2:00 PM")]
rep, st = run(pub, fr)
chk("CONTROL: a partially-shifted group repairs NOTHING", rep, [])
chk("CONTROL: and is counted as no-offset-match, not as correct",
    st["skip_no_offset_match"], 1)

# ---------------------------------------------------------------- offset controls
for label, delta, ptime, ftime in [
        ("+30min is a source change, not the defect", 30, "11:00 AM", "10:30 AM"),
        ("+60min stays silent", 60, "11:30 AM", "10:30 AM"),
        ("+240min stays silent", 240, "2:30 PM", "10:30 AM"),
        ("+420min stays silent", 420, "5:30 PM", "10:30 AM"),
        ("a NEGATIVE delta stays silent", -300, "5:30 AM", "10:30 AM")]:
    rep, _ = run([ev("X", "2026-10-05", ptime)], [ev("X", "2026-10-05", ftime)])
    chk(f"OFFSET CONTROL: {label}", rep, [])

# ---------------------------------------------------------------- already correct / absent
rep, st = run([ev("X", "2026-10-05", "10:30 AM")], [ev("X", "2026-10-05", "10:30 AM")])
chk("an already-correct row is left alone", rep, [])
chk("and is counted as already_correct", st["skip_already_correct"], 1)

rep, st = run([ev("Carried Only", "2026-10-05", "11:30 PM")], [ev("Other", "2026-10-05", "6:30 PM")])
chk("a row with NO fresh counterpart keeps what it has", rep, [])

rep, st = run([ev("X", "2026-10-05", "10:00 AM - 4:00 PM")], [ev("X", "2026-10-05", "6:30 PM")])
chk("an unparseable published time is never guessed at", rep, [])
chk("and is counted as unparseable", st["skip_unparseable_time"], 1)

# ---------------------------------------------------------------- date roll
rep, st = run([ev("Club Book presents: Lisa Unger", "2026-10-07", "12:00 AM")],
              [ev("Club Book presents: Lisa Unger", "2026-10-06", "7:00 PM")])
chk("a midnight-crossed row rolls the date BACK and fixes the time",
    [(r[1], r[2]) for r in rep], [("2026-10-06", "7:00 PM")])

# DIRECTION control: an evening published row must never be dragged onto the previous day.
rep, _ = run([ev("Evening Thing", "2026-10-07", "7:00 PM")],
             [ev("Evening Thing", "2026-10-06", "2:00 PM")])
chk("DIRECTION CONTROL: a row outside the 12-5:59 AM band never rolls date", rep, [])

# The band check `pm >= 360` SURVIVED mutation, and this is why: it is redundant by arithmetic.
# The roll target is pm + 1440 - off, and requiring that to be a legal minute-of-day already
# forces pm <= off - 1 <= 359.  Asserted as an exhaustive sweep rather than left as a comment --
# a redundancy claim is still a claim, and this file's whole argument is that claims get checked.
chk("the 12-5:59 AM band check is REDUNDANT by arithmetic (0 counterexamples in 1440x2)",
    [(pm, off) for pm in range(1440) for off in R.OFFSETS
     if pm >= 360 and 0 <= pm + 1440 - off <= 1439], [])

# Ambiguous previous-day group: two distinct fresh times, so the roll is not determined.
rep, _ = run([ev("Ambig", "2026-10-07", "12:00 AM")],
             [ev("Ambig", "2026-10-06", "7:00 PM"), ev("Ambig", "2026-10-06", "9:00 PM")])
chk("an AMBIGUOUS previous-day group rolls nothing", rep, [])

# ---------------------------------------------------------------- INPUT control: absence crashes
def _run_cli(tmp, pull_payload):
    w = os.path.join(tmp, "_compiled_work.json")
    with open(w, "w", encoding="utf-8") as fh:
        json.dump({"events": [ev("X", "2026-10-05", "11:30 PM")]}, fh)
    if pull_payload is not None:
        with open(os.path.join(tmp, "_feedpull_all.json"), "w", encoding="utf-8") as fh:
            json.dump(pull_payload, fh)
    e = dict(os.environ, MSP_RUNDIR=tmp)
    return subprocess.run([sys.executable, "-B", os.path.join(HERE, "ical_time_repair.py"),
                           w, "--dry-run"], capture_output=True, text=True, env=e, cwd=tmp)

with tempfile.TemporaryDirectory() as tmp:
    r = _run_cli(tmp, None)
    chk("INPUT CONTROL: an ABSENT feed pull crashes, never 0 repaired",
        (r.returncode != 0 and "is absent" in r.stderr), True)
with tempfile.TemporaryDirectory() as tmp:
    r = _run_cli(tmp, {"rows": []})
    chk("INPUT CONTROL: an EMPTY feed pull crashes too",
        (r.returncode != 0 and "0 rows" in r.stderr), True)
with tempfile.TemporaryDirectory() as tmp:
    r = _run_cli(tmp, {"rows": [ev("X", "2026-10-05", "6:30 PM")]})
    chk("a well-formed pull exits 0 and reports the repair",
        (r.returncode == 0 and "ROWS REPAIRED : 1" in r.stdout), True)

print(f"\n{P} passed, {F} failed")
sys.exit(1 if F else 0)
