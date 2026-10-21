#!/usr/bin/env python3
"""Regression tests for dedup_titles.py.

Every case here is a REAL row pair observed in _compiled_work.json on 2026-08-22, not a
synthetic one - same contract as test_city_resolve.py. The MUST-NOT-MERGE cases matter more
than the merge cases: a missed duplicate is cosmetic, a wrong merge silently deletes a real
venue or event from the guide.

Run after touching dedup_titles.py. Must report 0 failed.
"""
import dedup_titles as D

# (label, row_a, row_b, should_merge)
CASES = [
    # ---- the reported bug: trailing city qualifier -------------------------------------
    ("live at the rog (the shipped duplicate)",
     {"title": "Live at the Rog: Alligations - Roseville",
      "address": "Central Park - Frank Rog Amphitheatre, Roseville, MN 55113",
      "date": "2026-08-23", "start_time": "6:00 PM"},
     {"title": "Live at the Rog: Alligations",
      "address": "Central Park Frank Rog Amphitheatre, Roseville, MN",
      "date": "2026-08-23", "start_time": "6:00 PM"},
     True),
    ("maple maze city suffix",
     {"title": "Maple Maze", "address": "Maple Grove, MN"},
     {"title": "Maple Maze - Maple Grove", "address": "Maple Grove, MN"},
     True),
    ("city prefix, not suffix",
     {"title": "Day of the Dozers", "address": "Elk River, MN"},
     {"title": "Elk River Day of the Dozers", "address": "Elk River, MN"},
     True),

    # ---- pure reordering ---------------------------------------------------------------
    ("pinocchio reordered",
     {"title": "Children's Theatre Company: Pinocchio",
      "address": "2400 3rd Ave S, Minneapolis, MN", "date": "2026-09-08"},
     {"title": "Pinocchio - Children's Theatre Company",
      "address": "2400 3rd Ave S, Minneapolis, MN", "date": "2026-09-08"},
     True),
    ("ampersand vs the word and",
     {"title": "Loaves & Fishes Family Volunteer", "address": "Minneapolis, MN"},
     {"title": "Family Volunteer Loaves and Fishes", "address": "Minneapolis, MN"},
     True),

    # ---- MUST NOT MERGE: distinct things that merely share a token prefix ---------------
    ("zoo vs a distinct attraction inside it",
     {"title": "Minnesota Zoo", "address": "Apple Valley, MN"},
     {"title": "Minnesota Zoo Wanderlight Trail", "address": "Apple Valley, MN"},
     False),
    ("state fair volunteer shift vs a different shift",
     {"title": "Minnesota State Fair - Alphabet Forest",
      "address": "St. Paul, MN", "date": "2026-08-27"},
     {"title": "Minnesota State Fair - Alphabet Forest Photo Booth",
      "address": "St. Paul, MN", "date": "2026-08-27"},
     False),
    ("two locations of one chain, neighborhood qualifier",
     {"title": "Red Cow - St. Paul", "address": "St. Paul, MN"},
     {"title": "Red Cow St. Paul Cathedral Hill", "address": "St. Paul, MN"},
     False),
    ("chain with a street qualifier",
     {"title": "Colossal Cafe Grand Avenue", "address": "St. Paul, MN"},
     {"title": "Colossal Cafe", "address": "St. Paul, MN"},
     False),
    ("same brand, different street addresses",
     {"title": "Punch Pizza", "address": "3226 W Lake St, Minneapolis, MN"},
     {"title": "Punch Pizza - Minneapolis", "address": "802 Washington Ave, Minneapolis, MN"},
     False),
    ("same venue and day but different showtimes",
     {"title": "Summer Concert - Roseville", "address": "Roseville, MN",
      "date": "2026-08-23", "start_time": "2:00 PM"},
     {"title": "Summer Concert", "address": "Roseville, MN",
      "date": "2026-08-23", "start_time": "7:00 PM"},
     False),
    ("different dates are different occurrences",
     {"title": "Storytime - Roseville", "address": "Roseville, MN", "date": "2026-08-23"},
     {"title": "Storytime", "address": "Roseville, MN", "date": "2026-08-30"},
     False),
    ("different cities never merge",
     {"title": "Wild Rice Festival", "address": "Roseville, MN", "date": "2026-09-12"},
     {"title": "Roseville Wild Rice Festival", "address": "Duluth, MN", "date": "2026-09-12"},
     False),
    ("identical titles are left to the existing passes",
     {"title": "Touch a Truck", "address": "Edina, MN", "date": "2026-09-12"},
     {"title": "Touch A Truck", "address": "Edina, MN", "date": "2026-09-12"},
     False),
]


def merges(a, b):
    data = {"events": [dict(a), dict(b)]}
    return len(D.collapse(data, dry_run=True)) == 1


def main():
    passed = failed = 0
    for label, a, b, want in CASES:
        got = merges(a, b)
        if got == want:
            passed += 1
        else:
            failed += 1
            verb = "MERGED but should not have" if got else "did NOT merge but should have"
            print(f"  FAIL {label}: {verb}")
            print(f"       a={a['title']!r}")
            print(f"       b={b['title']!r}")

    # Title specificity: the qualifier must survive onto the kept row.
    data = {"events": [
        {"title": "Maple Maze", "address": "Maple Grove, MN", "website": "https://x.test"},
        {"title": "Maple Maze - Maple Grove", "address": "Maple Grove, MN"},
    ]}
    D.collapse(data)
    if data["events"][0]["title"] == "Maple Maze - Maple Grove":
        passed += 1
    else:
        failed += 1
        print(f"  FAIL specificity: kept title {data['events'][0]['title']!r}, "
              "expected the qualified one")

    # The richer row's data must survive even when the other row's title wins.
    if data["events"][0].get("website") == "https://x.test":
        passed += 1
    else:
        failed += 1
        print("  FAIL: the survivor lost its website when it inherited the better title")

    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
