#!/usr/bin/env python3
"""test_closed_venue_denylist.py (added 2026-09-07)

Every DROP case is a venue SKILL.md explicitly declares closed. Every KEEP case is a false
positive a looser rule WOULD have produced — which is the half that matters, because a wrong
denylist entry silently deletes a real venue and no later pass can restore it.

The Abdallah pair is the point of the whole suite: SKILL.md:688 closes the BURNSVILLE shop
only, so an unqualified "abdallah" entry would delete a live Minnesota chain. That is the
chain-collapse error in denylist form.
"""
import closed_venue_denylist as D

# (title, city, address, expect_dropped)
CASES = [
    # ---- must DROP: declared closed in SKILL.md ----
    ("MiniSota Play Cafe", "Maple Grove", "12500 Elm Creek Blvd, Maple Grove, MN", True),
    ("MiniSota Play Cafe & Coffee", "", "Maple Grove, MN", True),
    ("Betty Danger's Country Club", "Minneapolis", "2501 Marshall St NE", True),
    ("Keg and Case Market", "St. Paul", "928 W 7th St", True),
    ("Fasika Ethiopian Restaurant", "St. Paul", "510 Snelling Ave N", True),
    ("Safari Restaurant", "Minneapolis", "3010 4th Ave S", True),
    ("Harry Singh's Caribbean Restaurant", "Minneapolis", "", True),
    ("Lynden's Soda Fountain", "St. Paul", "1341 Pascal St N", True),
    ("Izzy's Ice Cream", "Minneapolis", "1100 S 2nd St", True),
    ("Abdallah Candies", "Burnsville", "3501 County Rd 42 W, Burnsville, MN", True),

    # ---- must KEEP: the location-qualified entries must not collapse a live chain ----
    ("Abdallah Candies", "Apple Valley", "7166 W 153rd St, Apple Valley, MN", False),
    ("Abdallah Chocolates", "Edina", "3939 W 50th St, Edina, MN", False),
    ("MiniSota Play Cafe", "Rochester", "100 1st Ave, Rochester, MN", False),  # different city

    # ---- must KEEP: contiguous-run rule must not match a loose subset ----
    ("Safari Adventure Restaurant Week Kickoff", "Minneapolis", "", False),
    ("Wildlife Safari Day at the Minnesota Zoo", "Apple Valley", "", False),
    ("Safari Story Time", "St. Paul", "", False),
    ("Ice Cream Social at Izzy's Park", "Bloomington", "", False),
    ("Keg and Case Farmers Market Vendor Fair", "St. Paul", "", False),

    # ---- must KEEP: ordinary venues sharing a single token ----
    ("Singh's Indian Kitchen", "Eagan", "", False),
    ("Soda Fountain Museum Tour", "Duluth", "", False),
    ("Country Club Park Playground", "Edina", "", False),
    ("Ethiopian Cultural Festival", "Minneapolis", "", False),
]


def main():
    passed = failed = 0
    for title, city, addr, expected in CASES:
        row = {"title": title, "city": city, "address": addr}
        hit = next((e for e in D.DENYLIST if D.match(row, e[0], e[1])), None)
        got = hit is not None
        if got == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL {title!r} (city={city!r}): expected dropped={expected}, got {got}"
                  f"{' via ' + hit[0] if hit else ''}")
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
