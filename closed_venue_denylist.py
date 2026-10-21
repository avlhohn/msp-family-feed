#!/usr/bin/env python3
"""closed_venue_denylist.py — STEP 4.3 tail pass (added 2026-09-07)

WHY THIS EXISTS
---------------
On 2026-09-06 `MiniSota Play Cafe` (Maple Grove) was found live in 2 rows despite SKILL.md:404
declaring it permanently closed on 2026-04-29 with an explicit "do NOT re-add it". Nothing in
the pipeline reads SKILL.md's closed-venue declarations, and `closure_filter.py` structurally
cannot help: it reads a row's own title for a *cancellation notice*, and a venue name announces
nothing. So a closed venue enters the carried base once and then survives every subsequent run
forever. Last run's catch was MANUAL. This is the standing denylist CLAUDE.md carried forward.

WHY IT IS A HAND TABLE, NOT A PARSER
------------------------------------
The declarations are prose scattered across five SKILL.md sections in five different phrasings
("permanently closed", "confirmed CLOSED", "appears to have closed its locations", "deliberately
NOT listed"). A regex over that prose is far more likely to mis-fire than a reviewed table, and
the failure mode is deleting a real venue. Same discipline as `dupsweep.KEEP_APART` and
`step8_venue_repair`'s merge table: hand-maintained, with the SKILL.md line cited for every row
so a later reader can re-verify the claim at its source rather than trusting this file.

TWO MATCHING RULES THAT MATTER
------------------------------
1. CONTIGUOUS TOKEN SUBSEQUENCE, never a loose subset — the same rule `seeds_reassert.py` uses.
   A subset match pulls unrelated venues in.
2. A `city` qualifier is REQUIRED where only one location closed. SKILL.md:688 closes "the
   Burnsville Abdallah shop" — Abdallah is a live Minnesota chain, so a bare "abdallah" entry
   would silently delete every surviving location. This is the chain-collapse error in denylist
   form. Where the whole brand is gone (Betty Danger's, Fasika) `city` is None.

Dropped rows are logged as `dropped_closed_venues`, the issue_type SKILL.md:1316 already
reserves for exactly this. Idempotent: a warm re-run drops 0.
"""
import json
import re
import sys

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# (venue name, city or None if the whole brand is closed, SKILL.md line, note)
DENYLIST = [
    ("minisota play cafe",        "maple grove", 404, "permanently closed 2026-04-29; 'do NOT re-add it'"),
    ("betty dangers country club", None,         464, "confirmed CLOSED; deliberately NOT listed"),
    ("keg and case market",        None,         616, "confirmed CLOSED; deliberately NOT listed"),
    ("fasika ethiopian",           None,         616, "confirmed CLOSED; deliberately NOT listed"),
    ("safari restaurant",          None,         616, "confirmed CLOSED; deliberately NOT listed"),
    ("harry singhs caribbean",     None,         616, "confirmed CLOSED; deliberately NOT listed"),
    ("lyndens soda fountain",      None,         688, "confirmed CLOSED; deliberately NOT listed"),
    ("abdallah",                   "burnsville", 688, "the BURNSVILLE shop only — chain is live elsewhere"),
    ("izzys ice cream",            None,         456, "closed its locations; deliberately NOT listed"),
]


def toks(s):
    """Lowercase token list, punctuation and possessives folded away."""
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[\u2018\u2019']", "", s)      # curly + straight apostrophes -> Betty Danger's
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.split()


def contiguous(hay, needle):
    """True if `needle` appears as a CONTIGUOUS run inside `hay` (not a loose subset)."""
    if not needle or len(needle) > len(hay):
        return False
    return any(hay[i:i + len(needle)] == needle for i in range(len(hay) - len(needle) + 1))


def match(row, name, city):
    """A row matches only if the NAME is a contiguous run in its title AND, when the entry is
    location-qualified, the city token also appears in the row's city/address."""
    if not contiguous(toks(row.get("title")), toks(name)):
        return False
    if city is None:
        return True
    where = toks(" ".join(str(row.get(f) or "") for f in ("city", "address", "location_name")))
    return contiguous(where, toks(city))


def run(path, dry_run=False):
    with open(path) as fh:
        data = json.load(fh)

    dropped = []
    for cat in CATS:
        keep = []
        for row in data.get(cat, []):
            hit = next((e for e in DENYLIST if match(row, e[0], e[1])), None)
            if hit:
                dropped.append({"category": cat, "title": row.get("title", ""),
                                "city": row.get("city", ""), "address": row.get("address", ""),
                                "venue": hit[0], "skill_line": hit[2], "note": hit[3]})
            else:
                keep.append(row)
        if cat in data:
            data[cat] = keep

    tag = "DRY RUN — " if dry_run else ""
    print(f"{tag}closed-venue denylist: {len(dropped)} rows dropped "
          f"({len({d['venue'] for d in dropped})} distinct venues)")
    for d in dropped:
        print(f"  DROP [{d['category']}] {d['title']!r} ({d['city'] or d['address'][:40]})")
        print(f"       -> SKILL.md:{d['skill_line']} — {d['note']}")
    if not dropped:
        print("  (none — every SKILL.md-declared closed venue is absent, which is the goal)")

    if not dry_run:
        with open(path, "w") as fh:
            json.dump(data, fh, ensure_ascii=False)
    with open("_closed_venue_report.json", "w") as fh:
        json.dump({"dry_run": dry_run, "dropped": dropped}, fh, indent=2, ensure_ascii=False)
    print("  report -> _closed_venue_report.json")
    return dropped


if __name__ == "__main__":
    args = sys.argv[1:]
    target = next((a for a in args if not a.startswith("--")), "_compiled_work.json")
    run(target, dry_run="--dry-run" in args)
