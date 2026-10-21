#!/usr/bin/env python3
"""
STEP 4.35 - standing-deal overlay.

Joins the verified standing discounts in `standing_deals.csv` onto rows that already exist
in the compiled dataset, by normalized venue name.

WHY THIS EXISTS
---------------
Cluster (b) of SKILL.md's "Deals & discounts" section is almost entirely *standing programs*
with no date: Como Zoo is always free, Mia is always free, smARTpass runs year round. STEP 2's
two-month date window discards anything without an in-window date, so the cluster was
capturing ~nothing (0 park deals of 815, 9 event deals of 2181, as of 2026-08-22).

A standing deal is an ATTRIBUTE OF A VENUE, not a row of its own. So it is applied as an
overlay after compile, exactly like the image overlay - not as a STEP 2 search result.

`deal_expiry` is intentionally blank for most rows. Blank means "runs indefinitely" and is
VALID DATA. Never warn on it, never age the row out.

Usage:
    python3 deals_overlay.py _compiled_work.json [--dry-run]
"""
import csv
import json
import re
import sys
from collections import OrderedDict

TABLE = "standing_deals.csv"
CATS = ("events", "parks", "meal_deals", "volunteer_opportunities", "restaurants")
# Venue discounts only make sense on these three. Never stamp a volunteer shift.
TARGET_CATS = ("events", "parks", "restaurants")


def norm(s):
    """Casefold and strip punctuation. 'Children's Theatre Co.' -> 'childrens theatre co'."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (s or "").lower())).strip()


# Dropped when comparing venue names: middle initials and corporate suffixes vary between
# the deal source and the feed. Found the hard way - "Oliver Kelley Farm" failed to match the
# feed's "Oliver H. Kelley Farm" under plain substring matching, so a venue that WAS present
# got reported as a missing seed.
_NOISE = {"the", "a", "of", "inc", "llc", "co", "company"}


def tokens(s):
    return [t for t in norm(s).split() if t not in _NOISE and not (len(t) == 1 and t.isalpha())]


def name_matches(venue, text):
    """True if every meaningful token of `venue` appears in `text`.

    Token-subset rather than substring: tolerates middle initials, punctuation and trailing
    qualifiers ('Minnesota Zoo' matches 'Minnesota Zoo Jack-O'-Lantern Spectacular') while
    still refusing false friends - 'Bell Museum' does NOT match 'Campbell Museum', because
    'campbell' is a single token and never equals 'bell'.
    """
    tv = tokens(venue)
    if not tv:
        return False
    tt = set(tokens(text))
    return all(t in tt for t in tv)


def truthy(v):
    return str(v).strip().lower() in ("true", "yes", "1")


# Short provenance key per source URL. Written to `deal_source` on every stamped row so the
# STEP 7 yield check can attribute a deal to the source that produced it. Without this,
# attribution has to guess by substring and produces garbage counts.
SOURCE_KEYS = (
    ("twin-cities-discount-guide", "frugalmom_discount_guide"),
    ("kids-eat-free-list", "frugalmom_kids_eat_free"),
    ("smartpass.melsa.org", "melsa_smartpass"),
    ("thriftyminnesota.com", "thrifty_minnesota"),
    ("upparent.com", "upparent"),
    ("dnr.state.mn.us", "dnr_free_park_days"),
    ("kidsbowlfree.com", "kids_bowl_free"),
    ("pumpkintrail.com", "great_pumpkin_trail"),
    # Venue-direct kids-eat-free pages verified 2026-09-21 (Andiamo, Ze's, Tipsy Steer, Smashburger).
    # All four share one provenance key: the deal is quoted verbatim from each venue's own page.
    ("andiamomn.com", "venue_direct_kids_eat_free"),
    ("zesdiner.com", "venue_direct_kids_eat_free"),
    ("tipsysteer.com", "venue_direct_kids_eat_free"),
    ("smashburger.com", "venue_direct_kids_eat_free"),
    # Re-verified 2026-09-23 off each venue's own specials page, migrated off the retired
    # twincitiesfrugalmom.com kids-eat-free-list. Deals quoted verbatim; aggregator hours were
    # wrong for Mill Valley Kitchen (3pm-close, not 4-8pm) and Patrick's (5pm, not 5:30pm).
    ("jerseysbar.com", "venue_direct_kids_eat_free"),
    ("gabesmn.com", "venue_direct_kids_eat_free"),
    ("millvalleykitchen.com", "venue_direct_kids_eat_free"),
    ("patricksbakerycafe.com", "venue_direct_kids_eat_free"),
    ("willymccoys.com", "venue_direct_kids_eat_free"),
    ("mchughspublichouse.com", "venue_direct_kids_eat_free"),
    # Outback Steakhouse added 2026-10-01, verified verbatim off outback.com/specials
    # ("Join us for Kids Eat Free Mondays..."). National chain with ~12 MN locations.
    ("outback.com", "venue_direct_kids_eat_free"),
    # Museum free-admission programs quoted verbatim from the institution's own visit page.
    # Walker added 2026-09-23 (walkerart.org/visit: kids 18 and under free, Free Thursday
    # Nights, Free First Saturday). Distinct from melsa_smartpass, which is the library-card
    # program, not the venue's own standing free-admission policy.
    ("walkerart.org", "venue_direct_museum_free"),
)


def source_key(url):
    u = (url or "").lower()
    for frag, key in SOURCE_KEYS:
        if frag in u:
            return key
    return "other"


def load_table(path=TABLE):
    with open(path, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("venue_match") or "").strip()]
    # Longest venue name first, so "Minnesota Children's Museum" wins over "Minnesota".
    rows.sort(key=lambda r: -len(r["venue_match"]))
    return rows


def apply_overlay(data, table, dry_run=False):
    """Returns (stats, unmatched). Mutates `data` unless dry_run."""
    stats = OrderedDict()
    unmatched = []

    for deal in table:
        venue = deal["venue_match"].strip()
        nv = norm(venue)
        if not nv:
            continue
        hits = []
        for cat in TARGET_CATS:
            for row in data.get(cat, []):
                if name_matches(venue, row.get("title")) or name_matches(venue, row.get("address")):
                    hits.append((cat, row))

        if not hits:
            unmatched.append(venue)
            continue

        applied = skipped = 0
        for cat, row in hits:
            # Never clobber a more specific, row-level deal that STEP 2 already found.
            #
            # But DO refresh a row this overlay stamped on a previous run - identified by its
            # `deal_source` being one of ours. Without that carve-out the overlay is a silent
            # no-op on every re-run, so edits to standing_deals.csv would never take effect.
            # This is the exact trap the image overlay hit with `curated_category`: a
            # provenance value that is not "weak" makes the step skip its own prior output.
            owned = (row.get("deal_source") or "").strip() in {k for _f, k in SOURCE_KEYS}
            if truthy(row.get("has_deal")) and (row.get("deal_description") or "").strip() and not owned:
                skipped += 1
                continue
            if not dry_run:
                row["has_deal"] = True
                row["deal_description"] = deal["deal_description"]
                # Provenance, so STEP 7 can attribute the deal. Never write source_url into
                # `website` - the source is a blog, not the venue's own site.
                row["deal_source"] = source_key(deal.get("source_url"))
                # Blank expiry is meaningful: the program runs indefinitely. Leave it blank.
                if (deal.get("deal_expiry") or "").strip():
                    row["deal_expiry"] = deal["deal_expiry"].strip()
            applied += 1
        stats[venue] = {"matched": len(hits), "applied": applied, "skipped_existing": skipped}

    return stats, unmatched


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    path = args[0] if args else "_compiled_work.json"

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    def deal_counts():
        return {c: sum(1 for r in data.get(c, []) if truthy(r.get("has_deal"))) for c in CATS}

    before = deal_counts()
    table = load_table()
    stats, unmatched = apply_overlay(data, table, dry_run=dry)
    after = deal_counts()

    if not dry:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)

    total_applied = sum(s["applied"] for s in stats.values())
    report = {
        "table_rows": len(table),
        "venues_matched": len(stats),
        "venues_unmatched": len(unmatched),
        "unmatched": unmatched,
        "rows_stamped": total_applied,
        "has_deal_before": before,
        "has_deal_after": after,
        "per_venue": stats,
        "dry_run": dry,
    }
    with open("_deals_overlay_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)

    print(f"{'DRY RUN ' if dry else ''}standing-deal overlay")
    print(f"  table rows      : {len(table)}")
    print(f"  venues matched  : {len(stats)}  unmatched: {len(unmatched)}")
    print(f"  rows stamped    : {total_applied}")
    for c in CATS:
        if before[c] != after[c]:
            print(f"    {c:24s} has_deal {before[c]:4d} -> {after[c]:4d}")
    if unmatched:
        print("  NO ROW TO ATTACH TO (add as seed venues):")
        for v in unmatched:
            print(f"    - {v}")


if __name__ == "__main__":
    main()
