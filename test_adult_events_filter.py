#!/usr/bin/env python3
"""
test_adult_events_filter.py — real observed cases for adult_events_filter.py

Every DROP case is a title seen on the live 2026-08-25 feed. Every KEEP case is a real
family event that a naive keyword filter got wrong (Fiesta Latina, caregiver-attended
storytimes, kids' book clubs). Run after any edit to adult_events_filter.py:
    python3 test_adult_events_filter.py
Must report: all passed, 0 failed.
"""
import adult_events_filter as A

# (title, category, expected_verdict, is_seed)
CASES = [
    # ---- must DROP (real adult-service titles from the live feed) ----
    ("Career Services", "events", "drop", False),
    ("Job Search Assistance", "events", "drop", False),
    ("Job Search Assistance: Goodwill-Easter Seals", "events", "drop", False),
    ("In-Person Job Club", "events", "drop", False),
    ("LGBTQIA+ Job Seeker Workshop", "events", "drop", False),
    ("Seasoned Job Seeker Roundtable", "events", "drop", False),
    ("Medicare Counseling", "events", "drop", False),
    ("Medicare 101 with Minnesota Aging Pathways", "events", "drop", False),
    ("Medicare and Medicaid 101 OPEN HOUSE", "events", "drop", False),
    ("MNsure Help and Enrollment", "events", "drop", False),
    ("Learn About MNsure and MinnesotaCare", "events", "drop", False),
    ("1:1 Tech Help", "events", "drop", False),
    ("Drop-in Tech Help", "events", "drop", False),
    ("Tech Help for Seniors", "events", "drop", False),
    ("One-to-One Computer and Tech Help by Appointment", "events", "drop", False),
    ("Tech Drop-in Session", "events", "drop", False),
    ("Resume Writing", "events", "drop", False),
    ("Drop-in Job Search and R\u00e9sum\u00e9 Assistance", "events", "drop", False),  # accented
    ("Resume Review with Career Force", "events", "drop", False),
    ("Virtual Interviewing Workshop", "events", "drop", False),
    ("City of Minneapolis Small Business Support", "events", "drop", False),
    ("Drop-in Business Consultations", "events", "drop", False),
    ("Employer of the Day: Terracon", "events", "drop", False),
    ("Community Partner of the Day: Urban League Twin Cities", "events", "drop", False),
    ("Employment Resource Fair", "events", "drop", False),
    ("Minneapolis Works: CAPI", "events", "drop", False),
    ("Work Wednesday: Job Training and Resources", "events", "drop", False),

    # ---- must KEEP (family events a naive keyword filter wrongly flags) ----
    ("Fiesta Latina", "events", None, False),                       # desc mentions a job booth; title clean
    ("Family Storytime", "events", None, False),                    # "caregiver" only in desc
    ("Baby Storytime", "events", None, False),
    ("Library Book Club - Where Rivers Part", "events", None, False),  # book club NOT filtered
    ("Short Story Book Club (Final Session)", "events", None, False),  # kids' book club
    ("Toddler Open Gym", "events", None, False),
    ("Teen Career Exploration Night", "events", None, False),        # a real teen program stays (no drop phrase)
    ("Fall Harvest Orchard Opening Weekend", "events", None, False), # earlier "55+" substring misfire

    # ---- category guard: adult-sounding title outside events is untouched ----
    ("Small Business Saturday Market", "restaurants", None, False),
    ("Job Corps Volunteer Day", "volunteer_opportunities", None, False),

    # ---- REVIEW tier (borderline, never auto-dropped) ----
    ("Magnet Senior Center", "events", "review", False),

    # ---- seed guard: a seed matching a drop phrase is reviewed, never dropped ----
    ("Career Services", "events", "review", True),
]


def main():
    passed = failed = 0
    for title, cat, expected, is_seed in CASES:
        row = {"title": title, "category": cat}
        if is_seed:
            row["is_seed"] = True
        verdict, phrase = A.classify(row)
        ok = verdict == expected
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  {title!r} ({cat}, seed={is_seed}): "
                  f"expected {expected!r}, got {verdict!r} [{phrase}]")
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
