"""STEP 4.35 pre-pass: restore `deal_source` on carried rows. Adopted 2026-08-26.

WHY THIS EXISTS
---------------
`deals_overlay.py` writes a `deal_source` provenance key on every row it stamps, and its
`owned` carve-out re-stamps rows it recognises as its own so that edits to
`standing_deals.csv` actually take effect on a re-run. That carve-out is correct and its
comment says exactly why.

But `deal_source` is not one of the 19 schema-v3.1 BASE fields, and `build_guide.py:22`
rebuilds every row as `{k: it.get(k,'') for k in BASE}`. So the field is created by the
overlay, consumed by the yield check in the same run, and then **destroyed at build**. It
never reaches the published CSV, so next run's carried base arrives with it blank.

Two failures follow, and both are silent:

1. `owned` is therefore False for every carried row, so the carve-out never fires. The
   overlay is a no-op on exactly the rows it was written to refresh: change a
   `deal_description` in `standing_deals.csv` and it will never reach the live app for any
   venue stamped on a previous run. This is the trap the carve-out's own comment describes,
   reintroduced through the schema round-trip rather than through the provenance value.

2. `deals_yield.py` attributes by `deal_source`, so a source whose venues were all stamped
   in an earlier run reports 0 and warns forever. On 2026-08-26 that produced two false
   WARNs -- `kids_bowl_free` and `frugalmom_kids_eat_free` -- whose real yields are 21 and
   9. A permanent warning is worse than no warning: it trains the reader to skim the block.
   (CLAUDE.md, deals rule 5.)

THE RECONSTRUCTION IS EXACT, NOT A GUESS
----------------------------------------
A prior run copied `deal_description` verbatim out of `standing_deals.csv`, so the stored
text is an exact copy of a table row, and the table row carries the `source_url`. Matching
on whitespace-normalised full-string equality therefore recovers the original attribution.

This is NOT the substring-scan of `deal_description` that CLAUDE.md forbids. That rule
bans scanning the text for source-ish keywords, which counts noise. This is full-string
equality against a known table entry, and it refuses to guess:

  * a description matching table entries from 2+ different sources is left blank (measured
    2026-08-26: 51 distinct descriptions, 0 ambiguous -- but the check stays, because an
    edit to the table could introduce one);
  * a description matching nothing in the table is left blank. Those are row-level deals
    that STEP 2 found itself and that no standing-deal source can claim. On 2026-08-26 that
    was 259 of 390 rows -- correctly unattributed, not a shortfall.

A row that already carries a `deal_source` is never touched.

Run BEFORE deals_overlay.py:
    python3 bycat_shim.py deal_provenance_restore.py
"""
import csv
import json
import re
import sys
from collections import Counter, OrderedDict

TABLE = "standing_deals.csv"
TARGET_CATS = ("events", "parks", "meal_deals", "volunteer_opportunities", "restaurants")

# Must stay identical to deals_overlay.SOURCE_KEYS -- imported rather than copied so the two
# can never drift apart into disagreeing attributions.
try:
    from deals_overlay import SOURCE_KEYS, source_key
except Exception:  # pragma: no cover - only if the overlay is absent
    SOURCE_KEYS = (
        ("twin-cities-discount-guide", "frugalmom_discount_guide"),
        ("kids-eat-free-list", "frugalmom_kids_eat_free"),
        ("smartpass.melsa.org", "melsa_smartpass"),
        ("thriftyminnesota.com", "thrifty_minnesota"),
        ("upparent.com", "upparent"),
        ("dnr.state.mn.us", "dnr_free_park_days"),
        ("kidsbowlfree.com", "kids_bowl_free"),
    ("pumpkintrail.com", "great_pumpkin_trail"),
    )

    def source_key(url):
        u = (url or "").lower()
        for frag, key in SOURCE_KEYS:
            if frag in u:
                return key
        return "other"


def norm_desc(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def truthy(v):
    return str(v).strip().lower() in ("true", "yes", "1")


def build_index(path=TABLE):
    """description -> set of source keys. A description claimed by 2+ sources is ambiguous."""
    idx = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = norm_desc(row.get("deal_description"))
            if not d:
                continue
            idx.setdefault(d, set()).add(source_key(row.get("source_url")))
    return idx


def restore(data, idx, dry_run=False):
    stats = Counter()
    restored = Counter()
    for cat in TARGET_CATS:
        for row in data.get(cat, []):
            if not truthy(row.get("has_deal")):
                continue
            stats["has_deal"] += 1
            if (row.get("deal_source") or "").strip():
                stats["already_attributed"] += 1
                continue
            keys = idx.get(norm_desc(row.get("deal_description")))
            if not keys:
                stats["no_table_match"] += 1          # row-level deal; correctly unattributed
                continue
            if len(keys) > 1:
                stats["ambiguous"] += 1               # refuse to guess
                continue
            key = next(iter(keys))
            if not dry_run:
                row["deal_source"] = key
            restored[key] += 1
            stats["restored"] += 1
    return stats, restored


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = args[0] if args else "_compiled_work.json"
    dry_run = "--dry-run" in sys.argv

    data = json.load(open(src, encoding="utf-8"))
    idx = build_index()
    stats, restored = restore(data, idx, dry_run=dry_run)

    if not dry_run:
        json.dump(data, open(src, "w"), ensure_ascii=False)

    print("deal provenance restore" + ("  [DRY RUN]" if dry_run else ""))
    print(f"  table descriptions   : {len(idx)}  "
          f"(ambiguous: {sum(1 for v in idx.values() if len(v) > 1)})")
    print(f"  has_deal rows        : {stats['has_deal']}")
    print(f"  already attributed   : {stats['already_attributed']}")
    print(f"  RESTORED             : {stats['restored']}")
    for k, v in restored.most_common():
        print(f"      {v:>4}  {k}")
    print(f"  no table match       : {stats['no_table_match']}  "
          f"(row-level deals - correctly unattributed, not a shortfall)")
    print(f"  ambiguous, left blank: {stats['ambiguous']}")

    report = OrderedDict(
        table_descriptions=len(idx),
        ambiguous_descriptions=sum(1 for v in idx.values() if len(v) > 1),
        has_deal_rows=stats["has_deal"],
        already_attributed=stats["already_attributed"],
        restored_total=stats["restored"],
        restored_by_source=dict(restored),
        no_table_match=stats["no_table_match"],
        ambiguous_left_blank=stats["ambiguous"],
        dry_run=dry_run,
    )
    json.dump(report, open("_deal_provenance_report.json", "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
