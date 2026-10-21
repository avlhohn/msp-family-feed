"""Tests for fetch_feeds.ical_date / ical_time timezone handling (added 2026-09-29).

Root cause these pin: LibCal (and any iCal source) may stamp DTSTART in UTC
(`...T233000Z`).  The pre-2026-09-29 code formatted the raw hour digits verbatim, so a
6:30 PM Central event printed as "11:30 PM" downstream in Base44, and late-evening events
that cross midnight in UTC were filed on the WRONG DAY (which also fed a wrong `date` to the
in_window filter).  Every case below is a real observed shape from the MN LibCal feeds
(anokacounty / washcolib / ecrlib .libcal.com) or a boundary that must NOT regress.

Import must not require MSP_TODAY/MSP_END, so set them before importing fetch_feeds.
Run: python3 test_ical_time.py   (must report "N passed, 0 failed")
"""
import os
os.environ.setdefault("MSP_TODAY", "2026-09-29")
os.environ.setdefault("MSP_END", "2026-10-31")

import fetch_feeds as F

passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {label}: got {got!r}, want {want!r}")


# ---- THE BUG: UTC-stamped evening event must convert UTC -> Central (CDT, -5) ----
# 23:30 UTC on Oct 1 == 6:30 PM CDT on Oct 1.  Same calendar day, corrected clock time.
check("utc_evening date", F.ical_date("20261001T233000Z"), "2026-10-01")
check("utc_evening time", F.ical_time("20261001T233000Z"), "6:30 PM")
check("utc_evening date w/param", F.ical_date("20261001T233000Z", "VALUE=DATE-TIME"), "2026-10-01")

# The literal event from the user report: "Family Craft Night: Painting Pumpkins" 6:30 PM.
check("painting_pumpkins", F.ical_time("20261001T233000Z"), "6:30 PM")

# ---- UTC that crosses midnight: date must roll BACK a day, not forward ----
# 01:00 UTC on Oct 2 == 8:00 PM CDT on Oct 1.  Old code said Oct 2 / 1:00 AM (both wrong).
check("cross_midnight date", F.ical_date("20261002T010000Z"), "2026-10-01")
check("cross_midnight time", F.ical_time("20261002T010000Z"), "8:00 PM")
# 04:59 UTC == 11:59 PM CDT previous day (still previous day).
check("late_night date", F.ical_date("20261002T045900Z"), "2026-10-01")
check("late_night time", F.ical_time("20261002T045900Z"), "11:59 PM")
# 05:00 UTC == 12:00 AM (midnight) CDT the SAME UTC calendar day.
check("midnight_boundary date", F.ical_date("20261002T050000Z"), "2026-10-02")
check("midnight_boundary time", F.ical_time("20261002T050000Z"), "12:00 AM")

# ---- TZID=America/Chicago: already local, must be UNCHANGED (no double shift) ----
check("tzid_chicago date", F.ical_date("20261001T183000", "TZID=America/Chicago"), "2026-10-01")
check("tzid_chicago time", F.ical_time("20261001T183000", "TZID=America/Chicago"), "6:30 PM")

# ---- Floating (no Z, no TZID): treat as local wall time, UNCHANGED (Tribe path relies on this) ----
check("floating time", F.ical_time("20261001T183000"), "6:30 PM")
check("floating date", F.ical_date("20261001T183000"), "2026-10-01")
# Backward-compat: the Tribe REST path calls ical_time() with ONE argument.
check("one_arg_compat", F.ical_time("20260911T100000"), "10:00 AM")

# ---- All-day / date-only (VALUE=DATE): a date, and an EMPTY time ----
check("allday date", F.ical_date("20261001", "VALUE=DATE"), "2026-10-01")
check("allday time", F.ical_time("20261001", "VALUE=DATE"), "")
check("bare_date date", F.ical_date("20261001"), "2026-10-01")
check("bare_date time", F.ical_time("20261001"), "")

# ---- DST correctness: zoneinfo must pick CST (-6) in winter, CDT (-5) in summer ----
# 23:30 UTC on Jan 15 == 5:30 PM CST (Central Standard, -6).
check("winter_cst time", F.ical_time("20260115T233000Z"), "5:30 PM")
check("winter_cst date", F.ical_date("20260115T233000Z"), "2026-01-15")
# 23:30 UTC on Jul 15 == 6:30 PM CDT (Central Daylight, -5).
check("summer_cdt time", F.ical_time("20260715T233000Z"), "6:30 PM")

# ---- AM/PM and 12-hour boundaries (Central-side clock formatting) ----
# 17:00 UTC == 12:00 PM (noon) CDT.
check("noon", F.ical_time("20261001T170000Z"), "12:00 PM")
# 14:05 UTC == 9:05 AM CDT (minute zero-padding).
check("morning_padding", F.ical_time("20261001T140500Z"), "9:05 AM")
# Local floating noon / midnight format correctly.
check("local_noon", F.ical_time("20261001T120000"), "12:00 PM")
check("local_midnight", F.ical_time("20261001T000000"), "12:00 AM")

# ---- Unknown / malformed TZID must NOT crash and must NOT shift (assume local) ----
check("unknown_tzid", F.ical_time("20261001T183000", "TZID=Bogus/Zone"), "6:30 PM")

# ---- Garbage / empty in -> empty out (no exceptions) ----
check("empty date", F.ical_date(""), "")
check("empty time", F.ical_time(""), "")
check("none date", F.ical_date(None), "")
check("none time", F.ical_time(None), "")
check("junk date", F.ical_date("not-a-date"), "")
check("junk time", F.ical_time("not-a-date"), "")

print(f"{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
