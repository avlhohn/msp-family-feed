#!/usr/bin/env python3
"""test_dupsweep.py — regression tests for dupsweep.py's time canonicalizer and the
whole-dataset exact sweep.

The load-bearing case is the 2026-09-01 discovery: the same event was ingested twice, once
with the time as 24-hour "17:00" and once as 12-hour "5:00 PM". 350 such twins survived every
dedup pass because `time` was compared as a raw string. `ntime()` is supposed to fold both
spellings into one bucket so the sweep collapses them.

The bug that made it WORSE than a no-op: `ntime()` applied `int(hour) % 12` unconditionally,
so a bare 24-hour "17:00" became "05:00" (5 AM). That not only failed to match its "5:00 PM"
twin, it corrupted every unambiguous 24-hour time into the wrong minute-bucket — which could
merge two genuinely different sessions or split a real twin. So the ntime cases below assert
BOTH directions: twins must converge, and a bare 24-hour string must be preserved verbatim.

Every value here is a real shape seen on the live feed. Run after any edit to dupsweep.py:
    python3 test_dupsweep.py
Must report: all passed, 0 failed.
"""
import json, os, tempfile, subprocess, sys
import dupsweep as D

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1) ntime() unit cases — (input, expected canonical 24-hour "HH:MM" or "")
# ---------------------------------------------------------------------------
NTIME_CASES = [
    # --- the twin pair that started this: both must land on 17:00 ---
    ("17:00", "17:00"),          # bare 24-hour — MUST be preserved, not mangled to 05:00
    ("5:00 PM", "17:00"),        # 12-hour twin of the above
    ("5:00PM", "17:00"),         # no space
    ("5:00 pm", "17:00"),        # lowercase marker

    # --- more 24h/12h twins seen paired in the feed ---
    ("19:30", "19:30"),          # bare 24-hour preserved
    ("7:30 PM", "19:30"),        # its 12-hour twin
    ("09:30", "09:30"),          # bare 24-hour morning preserved (not turned into 21:30)
    ("9:30 AM", "09:30"),        # 12-hour AM twin
    ("14:00", "14:00"),
    ("2:00 PM", "14:00"),

    # --- noon / midnight, the classic 12-vs-24 traps ---
    ("12:00 PM", "12:00"),       # noon stays 12, not 24
    ("12:00 AM", "00:00"),       # midnight becomes 00, not 12
    ("00:00", "00:00"),          # bare midnight preserved
    ("12:00", "12:00"),          # bare noon preserved (no marker -> already 24h)

    # --- single-digit hour, early morning ---
    ("9:00 AM", "09:00"),
    ("9:00", "09:00"),           # bare -> already 24h, just zero-padded

    # --- blanks / junk -> empty string (untimed) ---
    ("", ""),
    (None, ""),
    ("All Day", ""),
    ("TBD", ""),
]


def run_ntime():
    passed = failed = 0
    for raw, expected in NTIME_CASES:
        got = D.ntime(raw)
        if got == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  ntime({raw!r}): expected {expected!r}, got {got!r}")
    # cross-check: every twin pair must be EQUAL after canonicalization
    twin_pairs = [("17:00", "5:00 PM"), ("19:30", "7:30 PM"),
                  ("09:30", "9:30 AM"), ("14:00", "2:00 PM")]
    for a, b in twin_pairs:
        if D.ntime(a) == D.ntime(b) and D.ntime(a) != "":
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  twin mismatch: ntime({a!r})={D.ntime(a)!r} "
                  f"!= ntime({b!r})={D.ntime(b)!r}")
    return passed, failed


# ---------------------------------------------------------------------------
# 2) end-to-end: a time-format twin pair must collapse; genuine two-session
#    rows (10am + 2pm) must survive; a blank-time twin folds into the timed row.
# ---------------------------------------------------------------------------
def _row(title, date, addr, time, **extra):
    r = {"title": title, "date": date, "address": addr, "time": time,
         "category": "events", "description": "", "image_url": "", "tags": ""}
    r.update(extra)
    return r


def run_e2e():
    passed = failed = 0
    data = {c: [] for c in D.CATS}
    data["events"] = [
        # -- TWIN: same event, 24h vs 12h -> must collapse to ONE row --
        _row("Family Story Time", "2026-09-10", "100 Main St, Saint Paul, MN 55102", "17:00",
             description="A twenty minute lap-sit story time for babies and toddlers." * 3),
        _row("Family Story Time", "2026-09-10", "100 Main St, St. Paul, MN", "5:00 PM"),

        # -- GENUINE two sessions of one storytime, 10am AND 2pm -> must stay TWO rows --
        _row("Toddler Open Gym", "2026-09-11", "200 Oak Ave, Bloomington, MN", "10:00 AM"),
        _row("Toddler Open Gym", "2026-09-11", "200 Oak Ave, Bloomington, MN", "2:00 PM"),

        # -- BLANK-time twin of a timed row -> the re-scrape signature; must fold in --
        _row("Baby Rhyme Time", "2026-09-12", "300 Elm St, Minneapolis, MN", "10:30 AM"),
        _row("Baby Rhyme Time", "2026-09-12", "300 Elm St, Minneapolis, MN", ""),

        # -- unrelated single row, no duplicate -> untouched --
        _row("Nature Walk", "2026-09-13", "400 Pine Rd, Stillwater, MN", "9:00 AM"),
    ]
    data["counts"] = {c: len(data[c]) for c in D.CATS}

    with tempfile.TemporaryDirectory() as td:
        work = os.path.join(td, "_compiled_work.json")
        json.dump(data, open(work, "w"))
        env = dict(os.environ, MSP_RUNDIR=td)
        # run dupsweep as a subprocess against this synthetic work file
        proc = subprocess.run([sys.executable, os.path.join(HERE, "dupsweep.py")],
                              cwd=td, env=env, capture_output=True, text=True)
        if proc.returncode != 0:
            print("  FAIL  dupsweep.py exited nonzero:\n", proc.stderr)
            return passed, failed + 1
        out = json.load(open(work))
        titles_dates = [(r["title"], r["date"], D.ntime(r.get("time")))
                        for r in out["events"]]

        checks = [
            # the 24h/12h twin collapsed to exactly one Family Story Time
            ("twin collapsed",
             sum(1 for t, dt, _ in titles_dates
                 if t == "Family Story Time" and dt == "2026-09-10") == 1),
            # both genuine Toddler Open Gym sessions survive (10am + 2pm)
            ("two genuine sessions kept",
             sum(1 for t, dt, _ in titles_dates
                 if t == "Toddler Open Gym" and dt == "2026-09-11") == 2),
            # blank-time twin folded into the timed Baby Rhyme Time -> one row
            ("blank-time twin folded",
             sum(1 for t, dt, _ in titles_dates
                 if t == "Baby Rhyme Time" and dt == "2026-09-12") == 1),
            # unrelated row untouched
            ("unrelated row kept",
             sum(1 for t, _, _ in titles_dates if t == "Nature Walk") == 1),
            # total: 7 in -> 5 out (2 collapses: one 24h/12h twin, one blank-fold)
            ("total row count", len(out["events"]) == 5),
        ]
        for name, ok in checks:
            if ok:
                passed += 1
            else:
                failed += 1
                print(f"  FAIL  e2e: {name}  (rows now: {titles_dates})")

        # idempotence: a warm re-run must drop 0
        proc2 = subprocess.run([sys.executable, os.path.join(HERE, "dupsweep.py")],
                               cwd=td, env=env, capture_output=True, text=True)
        out2 = json.load(open(work))
        if len(out2["events"]) == len(out["events"]):
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  e2e: not idempotent, warm re-run changed count "
                  f"{len(out['events'])} -> {len(out2['events'])}")
    return passed, failed


def main():
    p1, f1 = run_ntime()
    p2, f2 = run_e2e()
    passed, failed = p1 + p2, f1 + f2
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
