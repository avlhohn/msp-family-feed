"""Regression suite for run_tribe_rest() / _tribe_venue() / the generalised span detector.

Added 2026-09-11, when eight WordPress "The Events Calendar" CVB + nature-center sources
were moved off their `?ical=1` exports (which serialize only the current LIST-VIEW PAGE)
onto the plugin's WP REST endpoint.

Every case below is a REAL observed value or a real failure, not a synthetic example:

  * the empty-LIST venue is the shape that actually raised AttributeError during the probe;
  * the colon-bearing timestamp is the bug this suite caught before it shipped -- it made
    ical_time() return "" for every single Tribe row, with no error anywhere;
  * the Grand Rapids MICHIGAN coordinate is the exact centroid event-source-calendars.md §4
    records for the `grpl` dead end, reused here because a venue coordinate written by this
    fetcher is one STEP 4.9 will never re-check;
  * the span-detector cases are this run's own measured counts.

Run:  python3 test_tribe_rest.py        (needs no network; MSP_TODAY/MSP_END are set below)
Must report: 41 passed, 0 failed
"""
import os
import re
import importlib.util

os.environ.setdefault("MSP_TODAY", "2026-09-11")
os.environ.setdefault("MSP_END", "2026-10-31")

_spec = importlib.util.spec_from_file_location(
    "ff", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_feeds.py"))
ff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ff)

PASS = FAIL = 0


def ck(label, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1
        print(f"  ok   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}\n         got  {got!r}\n         want {want!r}")


def conv(s):
    return ff.ical_time(re.sub(r"[-:\s]", lambda m: "T" if m.group() == " " else "", s))


status = ff.span_status          # the real function, not a copy of its logic


print("_tribe_venue -- payload shapes that must not raise")
ck("dict venue -> street, city, state, zip",
   ff._tribe_venue({"venue": {"address": "1701 Charlton Street", "city": "West St. Paul",
                              "state": "MN", "zip": "55118", "phone": "651-455-4531",
                              "geo_lat": 44.8949219, "geo_lng": -93.0982894,
                              "venue": "Main Property"}}),
   ("1701 Charlton Street, West St. Paul, MN 55118", "651-455-4531",
    "44.894922", "-93.098289", "Main Property"))
ck("EMPTY LIST venue -- the observed AttributeError case",
   ff._tribe_venue({"venue": []}), ("", "", "", "", ""))
ck("missing venue key", ff._tribe_venue({}), ("", "", "", "", ""))
ck("venue: null", ff._tribe_venue({"venue": None}), ("", "", "", "", ""))
ck("list-WRAPPED dict venue",
   ff._tribe_venue({"venue": [{"address": "1 Main St", "city": "Winona", "state": "MN"}]}),
   ("1 Main St, Winona, MN", "", "", "", ""))
ck("city only, no street -> still a usable city string",
   ff._tribe_venue({"venue": {"city": "Willmar", "state": "MN"}})[0], "Willmar, MN")
ck("venue name present but address empty -> name returned separately",
   ff._tribe_venue({"venue": {"venue": "Fuller Farm"}}), ("", "", "", "", "Fuller Farm"))

print("\nMN bounding box -- STEP 4.9 SKIPS populated coordinates, so a wrong pin is forever")
ck("Grand Rapids MICHIGAN centroid REJECTED",
   ff._tribe_venue({"venue": {"geo_lat": 42.9649, "geo_lng": -85.6660}})[2:4], ("", ""))
ck("Florida REJECTED",
   ff._tribe_venue({"venue": {"geo_lat": 27.9, "geo_lng": -82.4}})[2:4], ("", ""))
ck("Chicago REJECTED (the Lakefront Park failure)",
   ff._tribe_venue({"venue": {"geo_lat": 41.88, "geo_lng": -87.63}})[2:4], ("", ""))
ck("Minneapolis ACCEPTED",
   ff._tribe_venue({"venue": {"geo_lat": 44.97, "geo_lng": -93.26}})[2:4],
   ("44.970000", "-93.260000"))
ck("Bemidji ACCEPTED (northern edge)",
   ff._tribe_venue({"venue": {"geo_lat": 47.47, "geo_lng": -94.88}})[2:4],
   ("47.470000", "-94.880000"))
ck("null coords -> blank, no crash",
   ff._tribe_venue({"venue": {"geo_lat": None, "geo_lng": None}})[2:4], ("", ""))
ck("string coords -> parsed",
   ff._tribe_venue({"venue": {"geo_lat": "44.97", "geo_lng": "-93.26"}})[2:4],
   ("44.970000", "-93.260000"))
ck("junk coords -> blank, no crash",
   ff._tribe_venue({"venue": {"geo_lat": "n/a", "geo_lng": ""}})[2:4], ("", ""))
ck("0,0 null-island REJECTED",
   ff._tribe_venue({"venue": {"geo_lat": 0, "geo_lng": 0}})[2:4], ("", ""))

print("\nstart_date -> time. Colons made ical_time() return '' on EVERY row, silently.")
ck("10:00:00 -> 10:00 AM", conv("2026-09-11 10:00:00"), "10:00 AM")
ck("17:00:00 -> 5:00 PM", conv("2026-09-14 17:00:00"), "5:00 PM")
ck("00:00:00 -> 12:00 AM", conv("2026-09-18 00:00:00"), "12:00 AM")
ck("12:30:00 -> 12:30 PM", conv("2026-10-01 12:30:00"), "12:30 PM")
ck("empty -> blank", conv(""), "")

print("\nspan detector -- a count at a limit is ONE tell; the span is the reliable one")
ck("30 @ 2026-09-12 -> CAPPED (visit_winona, 49 days short)",
   status(30, "2026-09-12"), "CAPPED")
ck("500 @ 2026-10-09 -> CAPPED (washco_libcal, the original 500 cap)",
   status(500, "2026-10-09"), "CAPPED")
ck("11 @ 2026-09-26 -> SHORT, not OK (visit_bemidji: a cap that is NOT round)",
   status(11, "2026-09-26"), "SHORT")
ck("17 @ 2026-09-24 -> SHORT (krls: was a silent OK before the generalisation)",
   status(17, "2026-09-24"), "SHORT")
ck("page-ceiling hit -> CAPPED regardless of count/span",
   status(1500, "2026-10-31", ceiling_hit=True), "CAPPED")
ck("19 @ 2027-02-05 -> OK (visit_faribault, span runs PAST end)",
   status(19, "2027-02-05"), "OK")
ck("30 @ 2026-10-31 -> OK (round count that REACHES END is not a cap)",
   status(30, "2026-10-31"), "OK")
ck("0 events -> OK, not SHORT (an empty feed is not a truncated one)", status(0, ""), "OK")

print("\n  ...and the margin, which exists so an ordinary quiet tail is not a permanent WARN")
ck("12 @ 2026-10-30 -> OK (1 day short: no event booked on the last day)",
   status(12, "2026-10-30"), "OK")
ck("57 @ 2026-10-25 -> OK (6 days short, inside the margin)",
   status(57, "2026-10-25"), "OK")
ck("57 @ 2026-10-24 -> SHORT (7 days short, at the boundary)",
   status(57, "2026-10-24"), "SHORT")
ck("30 @ 2026-10-30 -> OK (round count but only 1 day short -- NOT a cap)",
   status(30, "2026-10-30"), "OK")
ck("malformed date -> OK, no crash", status(10, "not-a-date"), "OK")

# ---------------------------------------------------------------------------------------
# month_urls() -- added 2026-09-12.  A WordPress "My Calendar" ICS export is MONTH-SCOPED
# and its default serves only the CURRENT month, so `krls` returned 17 VEVENTs ending
# 2026-09-24 against an END of 2026-10-31: a plausible, stable, correctly-parsed number
# with the whole back half of the window structurally invisible.  Fourth instance of the
# truncation class, and the SPAN detector above is what caught it -- the count (6 in-window)
# was unremarkable and no count-based check would have fired.
print("\nmonth_urls -- the export is month-scoped; the month arg is a START, not an interval")
mu = ff.month_urls
ck("bare url is fetched first (default == current month, but only observed, not guaranteed)",
   mu("https://krls.org/feed/my-calendar-ics/", "2026-09-12", "2026-10-31")[0],
   "https://krls.org/feed/my-calendar-ics/")
ck("Sep->Oct window fetches Sep, Oct AND Nov (one month PAST end)",
   mu("https://x/f/", "2026-09-12", "2026-10-31"),
   ["https://x/f/", "https://x/f/?month=9&yr=2026",
    "https://x/f/?month=10&yr=2026", "https://x/f/?month=11&yr=2026"])
# The extra month is not belt-and-braces: `month=10` came back spanning 09-25..10-17 while
# the 2026-10-30 Park Rapids storytime appeared ONLY under `month=11`.  Stopping at END's
# own month leaves a hole in exactly the tail the export was already truncating.
ck("December end rolls the year over correctly",
   mu("https://x/f/", "2026-12-05", "2026-12-31"),
   ["https://x/f/", "https://x/f/?month=12&yr=2026", "https://x/f/?month=1&yr=2027"])
ck("a url already carrying a query gets & not ?",
   mu("https://x/f/?src=p", "2026-09-12", "2026-09-30")[1],
   "https://x/f/?src=p&month=9&yr=2026")
ck("single-month window still fetches the following month",
   len(mu("https://x/f/", "2026-09-12", "2026-09-30")), 3)
try:
    mu("https://x/f/", "2026-10-31", "2026-09-12")
    ck("reversed window RAISES rather than returning []", "no raise", "ValueError")
except ValueError:
    ck("reversed window RAISES rather than returning []", "ValueError", "ValueError")
# A silently-empty url list would mean zero fetches and a zero-row source -- the quiet
# failure this whole class is made of.  Made to fail on purpose before being trusted.
ck("MONTH_LOOP_ICAL names no source absent from ICAL_FEEDS",
   ff.MONTH_LOOP_ICAL - {n for n, _, _ in ff.ICAL_FEEDS}, set())

print(f"\n{PASS} passed, {FAIL} failed")
raise SystemExit(1 if FAIL else 0)
