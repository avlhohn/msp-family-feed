"""Regression tests for closure_filter.py.

Every DROP case is a real title observed in a compiled dataset — the 2026-08-31 one except
for the two `--Cancelled--` rows, which are from 2026-09-26 and are marked as such.
Every KEEP case is either a real title from the same dataset or a near-miss that the
narrow-pattern rationale in the module docstring is specifically written to protect —
the false positives that a looser `\bclosed\b` or a bare `cancelled` would produce.
"""
from closure_filter import is_closure

DROP = [
    # --- real observed cancellations ---
    ("CANCELED - Contraption Club (3D Printing) at Cottage Grove Service Center", "cancelled"),
    ("CANCELED: Baby Storytime", "cancelled"),
    ("CANCELED:Teen Volunteer Opportunity: Peer Buddy for Adaptive Cooking Class", "cancelled"),
    ("CANCELED: Adaptive Teen Cooking: Mini Apple Crisps", "cancelled"),
    ("CANCELED: MakerTeen", "cancelled"),
    ("**CANCELLED** - Friends of the Chaska Library Pop-up Book Sale", "cancelled"),
    ("Cancelled - Toddler Time", "cancelled"),
    # --- real observed 2026-09-26, dash-WRAPPED marker (the gap this pinned) ---
    ("Peering Thru the Earth --Cancelled--", "cancelled"),
    ("St. Croix Sunrise -- Cancelled--", "cancelled"),
    # --- real observed closures ---
    ("LIBRARY CLOSED: Labor Day", "closed"),
    ("No Storytime, Library Closed", "closed"),
    ("SCL Branches Closed - Labor Day Weekend", "closed"),
    ("SCL Branches Closed - Staff Development Day", "closed"),
    ("New Prague Branch Closed - Dozinky Festival", "closed"),
    ("Library Closed", "closed"),
    ("All Libraries Closed for Holiday", "closed"),
    ("Library Closure: Labor Day", "closed"),
    ("Labor Day - City Offices Closed", "closed"),
    ("Holiday City Offices Closed", "closed"),
    ("City Hall Closed - Labor Day", "closed"),
]

KEEP = [
    # The false positives the narrow patterns exist to prevent.
    "Closed Captioning Workshop for Caregivers",
    "Close Reading Book Club",
    "Closed Loop Recycling: Family Science Night",
    "Rain or shine, this hike is never cancelled",
    # A SINGLE hyphen is not a marker — pins `-{2,}` against being widened to `-{1,}`.
    "Non-cancelled Family Hike",
    "Storytime at the Library",
    "Labor Day Family Picnic",
    "Open Play at the Community Center",
    "Baby Storytime",
    "Friends of the Chaska Library Pop-up Book Sale",
    "MakerTeen: Bead Creativity Studio",
    "Contraption Club (3D Printing)",
    # A venue whose NAME contains an institution word must survive.
    "Fall Festival at the Ramsey County Library",
    "Family Night at City Hall",
    "Science Museum of Minnesota: Dinosaur Discovery",
    "Teen Volunteer Opportunity: Peer Buddy for Adaptive Cooking Class",
    "Adaptive Teen Cooking: Mini Apple Crisps",
    # --- controls for the terminal-marker CLOSED alternative (added 2026-10-02) ---
    # Each pins one half of the anchor.  Without these the three DROP cases below would
    # ALSO pass under a dangerous bare-`\bclosed\b` rule, and the suite would prove nothing:
    # on this run's 7,829 live titles bare `closed` matched the same single row, so live
    # data could not distinguish the safe rule from the broad one.
    "Closed Captioning: Workshop",        # marker present but NOT terminal
    "Learn How Circuits Are Closed",      # terminal but NO colon/dash marker
    "",
]

# Terminal-marker closures.  `Pine River: CLOSED` was found live in `events` on 2026-10-02,
# dated 2026-10-12, having passed every pass in the 4.3 chain.  The institution list holds
# CATEGORY words (library / branch / museum) and this title names the BRANCH ITSELF, so no
# institution word is present to anchor on and the row was structurally unreachable.
DROP += [
    ("Pine River: CLOSED", "closed"),
    ("Hackensack: Closed", "closed"),
    ("Pine River - CLOSED", "closed"),
]

def main():
    p = f = 0
    for title, want in DROP:
        got = is_closure(title)
        if got == want:
            p += 1
        else:
            f += 1
            print(f"FAIL drop  want={want!r:12s} got={got!r:12s}  {title}")
    for title in KEEP:
        got = is_closure(title)
        if got is None:
            p += 1
        else:
            f += 1
            print(f"FAIL keep  got={got!r:12s}  {title}")
    print(f"\n{p} passed, {f} failed")
    return 1 if f else 0


if __name__ == "__main__":
    raise SystemExit(main())
