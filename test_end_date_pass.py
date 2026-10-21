#!/usr/bin/env python3
"""Tests for end_date_pass.compute_end_date. Every case is a real observed pattern —
the REJECT cases are actual false-positive phrasings seen in the compiled feed."""
from end_date_pass import compute_end_date as ced

CASES = [
    # (start, text, expected_end, label)
    # --- Signal 1: bare ISO end (all real feed rows) ---
    ('2026-09-12', 'Edina Fall Into the Arts Festival runs through 2026-09-13', '2026-09-13', 'iso_next_day'),
    ('2026-09-05', 'Big Springs Farm Pumpkins & Corn Maze open through 2026-09-12', '2026-09-12', 'iso_week'),
    ('2026-08-31', 'Minnesota Twins vs. Detroit Tigers series 2026-08-31 to 2026-09-01', '2026-09-01', 'iso_pick_later'),
    ('2026-09-15', 'Some fest 2026-09-19 details 2026-09-17 more', '2026-09-19', 'iso_pick_furthest'),
    # --- Signal 2: spelled "through <Month> <Day>[, Year]" ---
    ('2026-09-02', 'Apple Valley Farmers Market - Fall Season, through October 7, 2026', '2026-10-07', 'spell_with_year'),
    ('2026-09-22', 'Artist Reception open through September 28', '2026-09-28', 'spell_no_year'),
    ('2026-09-14', 'Community Ed class runs through January 22, 2027', '2027-01-22', 'spell_cross_year_explicit'),
    ('2026-09-04', 'North St. Paul Friday Night Car Show through Sept 18, 2026', '2026-09-18', 'spell_abbrev'),
    ('2026-12-15', 'Winter market until March 1', '2027-03-01', 'spell_year_rollforward'),
    # --- REJECT: vague / false-positive phrasings (must return None) ---
    ('2026-09-01', 'Kindermusik classes offered through preschoolers ages 3-5', None, 'reject_through_noun'),
    ('2026-09-01', 'Monkey Junction open through winter', None, 'reject_through_season'),
    ('2026-09-10', 'Conservation Carousel runs through end of September, weather permitting', None, 'reject_no_day'),
    ('2026-09-01', 'Stages Theatre through Stages Theatre Company in Hopkins', None, 'reject_through_word'),
    ('2026-09-01', 'Minnesota Twins Home Games through late September 2026', None, 'reject_through_adjective'),
    # --- REJECT: bad anchors / no signal ---
    ('2026-09-20', 'One-day event, tickets $5-10, doors 6-8pm', None, 'reject_price_time_ranges'),
    ('', 'Festival through 2026-09-13', None, 'reject_no_start'),
    ('2026-09-20', 'Event with earlier date 2026-09-01 mentioned', None, 'reject_iso_before_start'),
    ('2026-09-20', 'Season pass valid through 2028-09-13', None, 'reject_iso_out_of_window'),
    ('2026-09-20', 'Storytime every Tuesday', None, 'reject_no_end_signal'),
    ('2026-09-20', 'Runs 2026-09-20 only', None, 'reject_same_as_start'),
]


def main():
    passed = failed = 0
    for start, text, expected, label in CASES:
        got = ced(start, text)
        if got == expected:
            passed += 1
        else:
            failed += 1
            print(f"FAIL [{label}] start={start!r} expected={expected!r} got={got!r}")
    print(f"{passed} passed, {failed} failed")
    return failed


if __name__ == '__main__':
    raise SystemExit(1 if main() else 0)
