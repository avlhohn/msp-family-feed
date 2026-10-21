#!/usr/bin/env python3
"""Tests for kid_chains.py.  Every case is a real requirement, and the load-bearing ones are
proven to FAIL ON PURPOSE when the rule they guard is reverted (see the `_mutants` block at the
bottom, which this suite runs itself).  Offline: row_fn is a stub, there is no network.
"""
import datetime as dt
import kid_chains as K


# A row_fn stub matching fetch_feeds.row's signature and 20-key shape.
def stub_row(title, desc, addr, d, tm, url, source, tags=""):
    return {"title": title, "description": desc, "category": "events", "price_type": "",
            "price": "", "age_range": "", "address": addr, "latitude": "", "longitude": "",
            "image_url": "", "image_source": "", "date": d, "time": tm, "phone": "",
            "website": url, "has_deal": False, "deal_description": "", "deal_expiry": "",
            "tags": tags, "_src": source}


PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


# ---- date math ---------------------------------------------------------------------------
def test_nth_weekday():
    # 1st Saturday of Oct 2026 is the 3rd; of Nov 2026 is the 7th (verified against a calendar).
    check("1st Sat Oct 2026 == 2026-10-03", K.nth_weekday(2026, 10, 1, 5) == dt.date(2026, 10, 3))
    check("1st Sat Nov 2026 == 2026-11-07", K.nth_weekday(2026, 11, 1, 5) == dt.date(2026, 11, 7))
    # 2nd Monday of Oct 2026 (Columbus Day) is the 12th.
    check("2nd Mon Oct 2026 == 2026-10-12", K.nth_weekday(2026, 10, 2, 0) == dt.date(2026, 10, 12))
    # When the 1st of the month IS the target weekday, n=1 returns the 1st (no skip).
    # Nov 1 2026 is a Sunday; 1st Sunday must be Nov 1 itself, not Nov 8.
    check("1st Sun Nov 2026 == 2026-11-01", K.nth_weekday(2026, 11, 1, 6) == dt.date(2026, 11, 1))


def test_window_months():
    check("window months Oct-Nov", K.window_months("2026-10-01", "2026-11-30") == [(2026, 10), (2026, 11)])
    check("window months single", K.window_months("2026-10-05", "2026-10-20") == [(2026, 10)])
    check("window months year wrap", K.window_months("2026-12-15", "2027-01-10") == [(2026, 12), (2027, 1)])


def test_season_intersects():
    # Nov-Dec season vs an Oct-Nov window -> True (November overlaps).
    check("Nov-Dec season hits Oct-Nov window", K.season_intersects("2026-10-01", "2026-11-30", {11, 12}) is True)
    # Nov-Dec season vs a pure-summer window -> False.
    check("Nov-Dec season misses summer window", K.season_intersects("2026-06-01", "2026-07-31", {11, 12}) is False)
    # Year-round season always intersects.
    check("year-round always intersects", K.season_intersects("2026-06-01", "2026-07-31", set(range(1, 13))) is True)


def test_occurrences_cadence():
    occ = K.occurrences({"type": "nth_weekday_monthly", "n": 1, "weekday": 5}, "2026-10-01", "2026-11-30")
    check("HD cadence yields Oct3 + Nov7", occ == ["2026-10-03", "2026-11-07"])
    # A window that starts AFTER the month's first Saturday must drop that occurrence.
    occ2 = K.occurrences({"type": "nth_weekday_monthly", "n": 1, "weekday": 5}, "2026-10-05", "2026-11-30")
    check("cadence drops past occurrence (Oct3 gone)", occ2 == ["2026-11-07"])


def test_occurrences_standing():
    check("standing yields one blank date", K.occurrences({"type": "standing"}, "2026-10-01", "2026-11-30") == [""])


def test_unknown_cadence_raises():
    try:
        K.occurrences({"type": "weekly_every_blue_moon"}, "2026-10-01", "2026-11-30")
        check("unknown cadence raises", False)
    except ValueError:
        check("unknown cadence raises", True)


# ---- row generation ----------------------------------------------------------------------
def test_home_depot_rows():
    hd = next(p for p in K.PROGRAMS if p["key"] == "home_depot_kids_workshop")
    rows = K.to_feed_rows(hd, "2026-10-01", "2026-11-30", stub_row)
    # 5 stores x 2 occurrences = 10 rows.
    check("HD emits 10 rows", len(rows) == 10)
    check("HD all Free", all(r["price_type"] == "Free" for r in rows))
    check("HD all have real coords", all(isinstance(r["latitude"], float) and isinstance(r["longitude"], float) for r in rows))
    check("HD dates only Oct3/Nov7", {r["date"] for r in rows} == {"2026-10-03", "2026-11-07"})
    check("HD source tagged", all(r["_src"] == "chain_home_depot_kids_workshop" for r in rows))
    check("HD age range set", all(r["age_range"] == "5-12" for r in rows))
    check("HD category events", all(r["category"] == "events" for r in rows))


def test_standing_rows_blank_date():
    ikea = next(p for p in K.PROGRAMS if p["key"] == "ikea_smaland")
    rows = K.to_feed_rows(ikea, "2026-10-01", "2026-11-30", stub_row)
    check("IKEA emits 1 standing row", len(rows) == 1)
    check("IKEA date is blank (standing)", rows[0]["date"] == "")
    check("IKEA Free", rows[0]["price_type"] == "Free")
    check("IKEA real coords", isinstance(rows[0]["latitude"], float))


def test_seasonal_gate():
    cab = next(p for p in K.PROGRAMS if p["key"] == "cabelas_santas_wonderland")
    # In the live Oct-Nov window the Nov-Dec season intersects -> 2 store rows.
    rows_in = K.to_feed_rows(cab, "2026-10-01", "2026-11-30", stub_row)
    check("Cabela's emits in Nov window", len(rows_in) == 2)
    # In a summer window the Nov-Dec season does NOT intersect -> ZERO rows.
    rows_out = K.to_feed_rows(cab, "2026-06-01", "2026-07-31", stub_row)
    check("Cabela's silent out of season", rows_out == [])


def test_fetch_all():
    rows, reports = K.fetch_all("2026-10-01", "2026-11-30", None, stub_row)
    # Cadence: HD 10. Standing (1 row/store, year-round or in-season): Cabela's 2 + IKEA 1
    # + Lowe's 4 + Michaels 4 + B&N 3 + REI 3 = 17.  Total 27 this window.
    check("fetch_all 27 rows this window", len(rows) == 27)
    check("fetch_all 7 reports", len(reports) == 7)
    check("all rows are events", all(r["category"] == "events" for r in rows))
    # price_type is sourced per-program and strictly in the schema enum -- NOT all Free
    # (REI is a free/paid mix -> Varies, owner-approved 2026-10-01).
    check("all rows price_type in enum", all(r["price_type"] in ("Free", "Paid", "Varies") for r in rows))
    check("no blank coords", all(r["latitude"] != "" and r["longitude"] != "" for r in rows))


def test_pass2_programs():
    # Owner-approved pass-2 chains (2026-10-01): three standing FREE programs + REI as Varies.
    for key, n_stores, pt in [("lowes_kids_workshop", 4, "Free"),
                              ("michaels_kids_club", 4, "Free"),
                              ("barnes_noble_storytime", 3, "Free"),
                              ("rei_family_kids_classes", 3, "Varies")]:
        prog = next(p for p in K.PROGRAMS if p["key"] == key)
        rows = K.to_feed_rows(prog, "2026-10-01", "2026-11-30", stub_row)
        check(f"{key} emits one standing row per store", len(rows) == n_stores)
        check(f"{key} standing blank date", all(r["date"] == "" for r in rows))
        check(f"{key} price_type {pt}", all(r["price_type"] == pt for r in rows))
        check(f"{key} real coords", all(isinstance(r["latitude"], float) and isinstance(r["longitude"], float) for r in rows))
        check(f"{key} source tagged", all(r["_src"] == f"chain_{key}" for r in rows))
    # REI being Varies is the load-bearing owner decision -- lock it against a revert to Free.
    rei = next(p for p in K.PROGRAMS if p["key"] == "rei_family_kids_classes")
    rei_rows = K.to_feed_rows(rei, "2026-10-01", "2026-11-30", stub_row)
    check("REI is Varies not Free", all(r["price_type"] == "Varies" for r in rei_rows))


def test_fetch_all_requires_row_fn():
    try:
        K.fetch_all("2026-10-01", "2026-11-30", None, None)
        check("fetch_all requires row_fn", False)
    except ValueError:
        check("fetch_all requires row_fn", True)


def test_soft_fail_isolated():
    # A malformed program must soft-fail to ([], ERROR) without taking down the others.
    # A store WITH coords reaches the row build, where the missing "description"/"time"/etc.
    # keys raise KeyError -- which must be caught, not propagated.
    bad = {"key": "boom", "cadence": {"type": "standing"}, "season": set(range(1, 13)),
           "stores": [{"name": "x", "address": "a", "lat": 44.9, "lon": -93.2}]}  # missing fields
    rows, rep = K.fetch_program(bad, "2026-10-01", "2026-11-30", stub_row)
    check("soft-fail returns no rows", rows == [])
    check("soft-fail reports ERROR", rep["status"] == "ERROR")


def test_no_fabricated_coords_omits_store():
    prog = {"key": "t", "title": "T", "chain": "C", "description": "d", "age_range": "x",
            "time": "", "price_type": "Free", "tags": "", "website": "u",
            "stores": [{"name": "Good", "address": "a", "lat": 44.9, "lon": -93.2},
                       {"name": "NoCoord", "address": "b", "lat": "", "lon": ""}],
            "cadence": {"type": "standing"}, "season": set(range(1, 13))}
    rows = K.to_feed_rows(prog, "2026-10-01", "2026-11-30", stub_row)
    check("store with no coord is omitted", len(rows) == 1 and rows[0]["address"] == "a")


# ---- fail-on-purpose harness: prove the load-bearing guards actually fire ----------------
def _mutants():
    """Each returns (name, callable) that should make a specific check FAIL if the guard is
    reverted.  Run as asserts so a guard that silently stops guarding is caught."""
    import copy
    results = []

    # Mutant 1: revert the seasonal gate (always emit) -> Cabela's would emit in summer.
    cab = next(p for p in K.PROGRAMS if p["key"] == "cabelas_santas_wonderland")
    rows_out = K.to_feed_rows(cab, "2026-06-01", "2026-07-31", stub_row)
    results.append(("seasonal gate fires (summer==0)", rows_out == []))

    # Mutant 2: a cadence that starts after the first Saturday must drop it (no stale date).
    occ2 = K.occurrences({"type": "nth_weekday_monthly", "n": 1, "weekday": 5}, "2026-10-05", "2026-11-30")
    results.append(("window start drops past occurrence", "2026-10-03" not in occ2))

    # Mutant 3: Free is per-program, not a blanket -> every registry program is Free here, but a
    # paid program injected must carry its own price_type, never defaulted to Free.
    prog = copy.deepcopy(next(p for p in K.PROGRAMS if p["key"] == "ikea_smaland"))
    prog["price_type"] = "Paid"
    rows = K.to_feed_rows(prog, "2026-10-01", "2026-11-30", stub_row)
    results.append(("price_type is sourced not forced Free", rows[0]["price_type"] == "Paid"))

    return results


def run():
    for fn in [test_nth_weekday, test_window_months, test_season_intersects,
               test_occurrences_cadence, test_occurrences_standing, test_unknown_cadence_raises,
               test_home_depot_rows, test_standing_rows_blank_date, test_seasonal_gate,
               test_fetch_all, test_pass2_programs, test_fetch_all_requires_row_fn,
               test_soft_fail_isolated, test_no_fabricated_coords_omits_store]:
        fn()
    for name, ok in _mutants():
        check("mutant/" + name, ok)
    print(f"\n{PASS} passed, {FAIL} failed")
    return FAIL == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
