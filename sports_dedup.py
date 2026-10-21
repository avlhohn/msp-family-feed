#!/usr/bin/env python3
"""
sports_dedup.py -- collapse carried free-text sports rows into the STRUCTURED
ESPN schedule row for the same game.  STEP 4.3, runs AFTER dupsweep.py and
BEFORE closure_filter.py.

WHY THIS EXISTS (found 2026-09-21, the first run after espn_sports.py was wired)
-------------------------------------------------------------------------------
Wiring a structured source does not replace the free-text rows already in the
carried base -- it lands BESIDE them, and every dedup pass in this project is
structurally blind to the pair, because the two sources disagree about BOTH
names at once:

    carried  "Minnesota Wild vs Dallas Stars (Preseason)"  @ 199 Kellogg Blvd W
    carried  "Minnesota Wild vs Dallas Stars"              @ Xcel Energy Center
    ESPN     "Minnesota Wild vs. Dallas Stars"             @ Grand Casino Arena

One game, three rows, same date.  dedup_titles blocks on an exact normalized
title ("vs." != "vs"), and dupsweep keys on title AND address -- and the venue
has been RENAMED (Xcel Energy Center -> Grand Casino Arena), so even the address
half can never collide.  A family opening the app sees the same game three times.

THE EVIDENCE THAT IS NOT THE NAME
---------------------------------
ESPN's schedule endpoint states, per team, exactly ONE home game per calendar
date.  That is a scheduling fact, not a similarity score.  So for an ESPN anchor
row, any OTHER row on that same date naming those same teams in that same city
is a duplicate OF IT.  This is the `step8_venue_repair` standard (merge only on
evidence that is not the name) reached through a schedule instead of through a
street address.

FOUR GUARDS, each of which makes a wrong merge impossible; removing any one
re-opens the "subset rule eats Minnesota Zoo into Minnesota Zoo Wanderlight
Trail" failure CLAUDE.md warns about:

  1. The anchor MUST be an ESPN row (`_src` starts "espn_").  A subset rule with
     an arbitrary anchor is the forbidden one; this anchor is a structured
     schedule entry.
  2. Same EXACT date.  Never a window, never proximity -- CLAUDE.md: no pass may
     merge rows differing in `date` unless a source states a span.
  3. Anchor title must carry >= 4 distinctive tokens (two team names).  This is
     what stops a short/generic anchor from absorbing unrelated rows.
  4. Same city.  This is what keeps an AWAY-GAME WATCH PARTY in another suburb
     from being eaten -- e.g. "Week 3: Vikings @ Buccaneers" at a Maple Grove
     restaurant is a real local event and must survive.

Survivor = richest row by field completeness; every blank field on the survivor
is then filled from the rows being dropped, so the ESPN row's authoritative
`time` and schedule URL are preserved even when a carried row survives.

Idempotent: a warm re-run collapses 0.  Prints every merge, so a wrong merge is
visible rather than silent.

    python3 sports_dedup.py _compiled_work.json --dry-run
    python3 sports_dedup.py _compiled_work.json
    python3 test_sports_dedup.py        # must report 27 passed, 0 failed

All four guards were made to FAIL ON PURPOSE before the green run was trusted.
Guards 2, 3 and 4 each produce exactly one targeted failure.  Guard 1 is
different and the difference is recorded rather than smoothed over: removing the
`_src` test promotes EVERY qualifying row to anchor status, and anchors skip each
other, so the degenerate result is that the 5 MERGE cases go red while the
`noanchor` KEEP case stays green -- i.e. the case written to pin guard 1 passes
COINCIDENTALLY under that mutation.  The removal is still detected (21/6), but a
later reader must not cite `noanchor` as the thing that catches it.
"""
import json
import re
import sys

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# Tokens that carry no identifying weight in a matchup title.
STOP = {
    "vs", "v", "at", "the", "and", "a", "an", "of", "game", "games",
    "presented", "by", "home",
}

MIN_ANCHOR_TOKENS = 4          # guard 3: two team names

# Fields the ESPN ANCHOR is authoritative about, which therefore OVERWRITE the
# survivor rather than merely backfilling its blanks.  (found 2026-09-22)
#
# `merge()` originally filled a survivor field only when it was blank, and the
# survivor is the richest row, which is usually a carried free-text row.  So on
# real data ESPN's time was DISCARDED, and the suite's own line-73 assertion --
# "ESPN's authoritative time is preserved onto the survivor" -- was green only
# because its synthetic carried rows leave `time` blank, so the conflict it
# names was never exercised.  Observed live on all three 2026-09-22 groups:
#
#     espn_twins 3:10 PM  vs carried 15:10     (same instant, 24h format)
#     espn_wild  7:00 PM  vs carried 8:00 PM   (+1h)
#     espn_lynx  7:00 PM  vs carried 8:00 PM   (+1h)
#
# Two rows off by exactly +1h in the same direction is the ET/CT confusion
# signature, and the Twins pair agreeing on the instant is what rules out "the
# carried times are just wrong generally".  ESPN resolves UTC -> America/Chicago
# and leaves `time` EMPTY when `timeValid` is false, so a non-empty ESPN time is
# an announced, tz-correct kickoff; a free-text WebSearch time is neither.
# An invented start time is a factual claim a family acts on -- the
# `deal_description` standard, and the same class as the fabricated 11 PM
# kickoff fixed in espn_sports.py on 2026-09-21.
#
# DELIBERATELY NARROW -- `time` ONLY.  Three fields that must NOT be added:
#   price_type -- ESPN stamps a conservative "Varies" that states nothing, and
#                 the suite explicitly asserts the carried "Paid" wins (line 74).
#   address    -- ESPN gives a venue NAME ("Target Center"), the carried rows a
#                 real STREET address ("600 First Avenue North ... 55403"), and
#                 this project's address doctrine prefers the street address.
#   title      -- the suite asserts the richer promo title survives (line 85).
# `date` cannot conflict: guard 2 already requires it to be identical.
ANCHOR_AUTHORITATIVE = ("time",)


def toks(s):
    """Lowercase distinctive token set. Punctuation -> space, stopwords dropped."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return {t for t in s.split() if t and t not in STOP}


def city_of(addr):
    """Best-effort city token from a free-text address.

    Folds Saint -> St (feeds disagree on 'Saint Paul' vs 'St. Paul' for one
    address -- the same fold dupsweep.na() needs) and strips the state token and
    ZIP so 'Minneapolis, MN 55403' and 'Minneapolis, Minnesota' agree.
    """
    a = (addr or "").lower()
    a = re.sub(r"\b(\d{5})(-\d{4})?\b", " ", a)          # ZIP
    a = re.sub(r"[^a-z0-9,]+", " ", a)
    parts = [p.strip() for p in a.split(",") if p.strip()]
    # drop a trailing state token
    while parts and parts[-1].strip() in ("mn", "minnesota"):
        parts.pop()
    if not parts:
        return ""
    city = parts[-1].strip()
    city = re.sub(r"^saint\b", "st", city)
    city = re.sub(r"\bsaint\b", "st", city)
    return " ".join(city.split())


def completeness(r):
    return sum(1 for v in r.values() if v not in ("", None, False, []))


def find_groups(rows):
    """Return [(anchor_idx, [dup_idx, ...]), ...] over a list of event rows."""
    anchors = [
        i for i, r in enumerate(rows)
        if str(r.get("_src") or "").startswith("espn_")          # guard 1
        and r.get("date")
        and len(toks(r.get("title"))) >= MIN_ANCHOR_TOKENS       # guard 3
    ]
    groups = []
    claimed = set()
    for ai in anchors:
        a = rows[ai]
        at = toks(a.get("title"))
        ac = city_of(a.get("address"))
        dups = []
        for i, r in enumerate(rows):
            if i == ai or i in claimed or i in anchors:
                continue
            if r.get("date") != a.get("date"):                   # guard 2
                continue
            if not at <= toks(r.get("title")):
                continue
            if ac and city_of(r.get("address")) != ac:           # guard 4
                continue
            dups.append(i)
        if dups:
            claimed.update(dups)
            groups.append((ai, dups))
    return groups


def merge(rows, groups):
    """Collapse groups; return (new_rows, log)."""
    drop = set()
    log = []
    for ai, dups in groups:
        members = [ai] + dups
        # survivor = richest row
        si = max(members, key=lambda i: (completeness(rows[i]), -i))
        surv = dict(rows[si])
        for i in members:
            if i == si:
                continue
            for k, v in rows[i].items():
                if surv.get(k) in ("", None) and v not in ("", None):
                    surv[k] = v
        # The anchor OVERWRITES the survivor on the fields it is authoritative
        # about -- blank-only backfill silently kept a wrong carried time.
        overrides = []
        for k in ANCHOR_AUTHORITATIVE:
            av = rows[ai].get(k)
            if av in ("", None):
                continue                      # anchor states nothing -> claim nothing
            if surv.get(k) not in ("", None) and surv.get(k) != av:
                overrides.append((k, surv.get(k), av))
            surv[k] = av
        rows[si] = surv
        for i in members:
            if i != si:
                drop.add(i)
        log.append({
            "date": rows[ai].get("date"),
            "anchor": rows[ai].get("title"),
            "anchor_src": rows[ai].get("_src"),
            "survivor": surv.get("title"),
            "survivor_was_espn": str(rows[si].get("_src") or "").startswith("espn_"),
            "dropped": [rows[i].get("title") for i in members if i != si],
            "addresses": [rows[i].get("address") for i in members],
            "anchor_overrides": overrides,
        })
    return [r for i, r in enumerate(rows) if i not in drop], log


def run(path, dry=False):
    d = json.load(open(path))
    rows = d["events"]
    groups = find_groups(rows)
    new_rows, log = merge(list(rows), groups)
    collapsed = len(rows) - len(new_rows)
    tag = " (DRY RUN)" if dry else ""
    print(f"sports dedup{tag}: {len(rows)} -> {len(new_rows)} ({collapsed} collapsed)")
    for g in log:
        print(f"  {g['date']}  KEEP  {g['survivor']!r}"
              f"{'  [espn]' if g['survivor_was_espn'] else ''}")
        for t in g["dropped"]:
            print(f"               drop  {t!r}")
        for a in g["addresses"]:
            print(f"               addr  {a!r}")
    if not dry:
        d["events"] = new_rows
        d.pop("counts", None)
        json.dump(d, open(path, "w"), ensure_ascii=False)
        json.dump({"collapsed": collapsed, "groups": log},
                  open("_sports_dedup_report.json", "w"), indent=1)
        print("  report -> _sports_dedup_report.json")
    return collapsed, log


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: sports_dedup.py _compiled_work.json [--dry-run]", file=sys.stderr)
        sys.exit(2)          # absence is a CRASH, not a silent no-op
    run(args[0], dry="--dry-run" in sys.argv)
