#!/usr/bin/env python3
"""
ical_time_repair.py -- adopt THIS RUN's correctly-parsed iCal time onto rows that carried the
pre-fix value forward.  Folder root, undated, MSP_RUNDIR-resolved, --dry-run available.

WHY THIS FILE EXISTS (2026-09-30) -- THE THIRD RATCHET
======================================================
On 2026-09-29 `_ical_parse()` was fixed: LibCal stamps DTSTART in UTC, and the old code sliced
the raw hour digits out and formatted them verbatim, so every UTC-stamped event displayed +5h
(CDT) / +6h (CST) late and any evening event crossing midnight was filed on the WRONG DAY.
The fix is correct and this run PROVES it at the source -- `_feedpull_all.json` carries
`Family Craft Night: Painting Pumpkins!` at **6:30 PM**, which is the time the user reported as
correct.

The published feed carried it at **11:30 PM** anyway.

The fix never reached the row.  The carried base is rebuilt each run from the PUBLISHED CSVs,
which hold the old wrong string; the dedup chain then picks a survivor by RICHNESS, and the
carried row -- enriched over many runs with an image, coordinates, a website -- is richer than
the freshly-parsed one.  So the merge keeps the enriched row and discards the corrected time.

That is the SECOND-RATCHET class this project already documents twice:

  * `image_upgrades.WIKI_UPGRADEABLE` was widened to include `curated_category` while the
    identical gate in `WEAK_SOURCES` was not, so editing `curated_images.csv` reached zero live
    rows (found 2026-09-29, remediated by `curated_repoint.py`).
  * The same shape one layer down: `espn_sports.py`'s first stub-supplement draft deduped on an
    `id` field the producer never emits, so the supplement contributed a SILENT +0.

Generalised, and this is the transferable part: **fixing a PARSER does not fix the ROWS that
parser already produced.**  A correction applied upstream of a carried artifact is inert for
every row already in that artifact, and it is inert SILENTLY -- the fix's own test suite is
green, its source output is correct, and the defect survives in the feed.  Any parser fix whose
output is carried forward needs a remediation pass, or it is a fix in name only.

WHAT IS AND IS NOT REPAIRED
===========================
Eligibility is a GROUP-LEVEL EXACT SET MATCH at one of the two REAL America/Chicago UTC offsets,
never a per-row nearest match:

    for one (title, date) key, take every published row's time and every fresh row's time.
    Shift EVERY published time back by the offset.  Repair only if the resulting SET is
    exactly the fresh SET.

The set equality is what makes this non-judgemental.  A storytime at 10 AM and 2 PM is genuinely
two rows (CLAUDE.md: "time is a SEPARATOR, not part of the key"), so a per-row match could adopt
the wrong session's time.  Requiring the whole group to shift as one means a partial or
coincidental match repairs nothing.

THE OFFSET CONTROL IS THE EVIDENCE, and it was run BEFORE this file was written.  Groups matching
at each candidate offset on this run's real data:

        +60 min :     1 group        +300 min :  1123 groups  <-- CDT
       +120 min :     1 group        +360 min :     0 groups  <-- CST
       +180 min :     0 groups       +420 min :     0 groups
       +240 min :     2 groups       -300 min :     0 groups

1123 against 0-2.  The signature is the defect's fingerprint, not a curve fit -- which is the
measurement this project requires before an edit, and the thing a plausible-looking repair pass
would not have. (+360 is 0 because the carried rows were all fetched during CDT; it is retained
because a run in November will need it.)

DATE ROLL.  A UTC evening event crossing midnight was filed a day late, so it cannot join on
(title, date) at all.  Those rows are matched against the PREVIOUS day's fresh group under the
identical set rule and have BOTH date and time corrected.  Measured this run: 5 rows, every one
published `12:00 AM` on day D against a single fresh `7:00 PM` on day D-1.  A wrong DAY is worse
than a wrong time -- a family arrives to a dark building -- so these are repaired even though
they are few.

FOUR RULES THAT FAIL SILENTLY IF BROKEN
=======================================
1. **The fresh pull is the AUTHORITY and the carried value is a stale derivative of the same
   source.**  This is not a merge of two independent opinions; it is one source, re-read
   correctly.  That is what removes the judgement call, exactly as `curated_repoint.py`'s
   "absence from the file is positive proof the mapping was retired" removed one there.
2. **A group that does not match EXACTLY keeps what it has.**  This is a repair, not a cleaner.
   Unparseable times, missing fresh counterparts and already-correct groups are all left alone,
   and each is counted separately so a collapse in the numbers is visible rather than inferred.
3. **Only the two real offsets are candidates.**  Admitting arbitrary offsets would turn a
   fingerprint into a curve fit and would silently "repair" the +30/+60 deltas that are genuine
   source changes.
4. **`date` is only ever moved BACKWARD, and only from the 12:00-5:59 AM band.**  The defect can
   only ever have pushed an event later; a pass that could also move a date forward could invent
   an occurrence, which is the roll-forward failure class STEP 1 forbids.

WHAT THE MUTANT HARNESS FOUND, AND WHY ONE GUARD CANNOT BE KILLED
================================================================
8 mutants, graded behind a defensive `assert baseline is clean` and read BY MESSAGE rather than
by count.  7 were killed.  The one that SURVIVED is `pm[0] >= 360` -- the 12:00-5:59 AM band
check on the date roll -- and it survived because it is **redundant by arithmetic**, not because
it is unwired.  The roll target is `pm + 1440 - off`, and requiring that to be a legal
minute-of-day (`<= 1439`) already forces `pm <= off - 1 <= 359`.  Proven exhaustively over the
whole domain rather than argued: 0 of 1440x2 (pm, offset) pairs with `pm >= 360` can produce an
in-range target, and the suite now asserts that sweep directly so the claim is CHECKED instead of
written down.

That is worth stating rather than quietly deleting the line.  A surviving mutant is normally a
guard that is not wired up; this one is a guard that states an invariant the arithmetic already
enforces, so it is a readable restatement of the rule, kept deliberately.  The distinction only
became knowable by running the mutants -- assuming either answer would have been wrong, and the
tempting response (delete the "dead" condition) would have removed the only place the rule is
written in a form a reader can see.

Usage:
    python3 ical_time_repair.py _compiled_work.json --dry-run   # report only
    python3 ical_time_repair.py _compiled_work.json             # apply
    python3 test_ical_time_repair.py                            # must be 26 passed, 0 failed
"""
import collections
import datetime
import json
import os
import re
import sys

ROOT = os.environ.get("MSP_RUNDIR", os.path.dirname(os.path.abspath(__file__)) or ".")
WORK = os.path.join(ROOT, "_compiled_work.json")
PULL = os.path.join(ROOT, "_feedpull_all.json")

# The only two UTC offsets America/Chicago ever has.  Not a tunable.
OFFSETS = (300, 360)

RX_TIME = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", re.I)


def mins(t):
    """'6:30 PM' -> 1110.  Anything else -> None (and None never matches anything)."""
    m = RX_TIME.match((t or "").strip())
    if not m:
        return None
    h = int(m.group(1)) % 12
    if m.group(3).upper() == "PM":
        h += 12
    mi = int(m.group(2))
    if mi > 59:
        return None
    return h * 60 + mi


def fmt(n):
    """1110 -> '6:30 PM'.  Inverse of mins() over the whole legal range."""
    n %= 1440
    h, mi = divmod(n, 60)
    ap = "AM" if h < 12 else "PM"
    hh = h % 12 or 12
    return f"{hh}:{mi:02d} {ap}"


def key(r):
    return ((r.get("title") or "").strip().lower(), (r.get("date") or "").strip())


def index_fresh(rows):
    """(title, date) -> list of raw time strings, from THIS RUN's feed pull."""
    out = collections.defaultdict(list)
    for r in rows:
        t, d = key(r)
        if t and d:
            out[(t, d)].append((r.get("time") or "").strip())
    return out


def plan(published, fresh):
    """Return (repairs, stats).

    `repairs` is a list of (index, new_date, new_time, why).  Nothing is mutated here -- the
    planner is pure so the suite can assert the DECISION without a file on disk, and so
    --dry-run and --apply are guaranteed to agree rather than being two code paths that
    resemble each other.
    """
    groups = collections.defaultdict(list)
    for i, r in enumerate(published):
        groups[key(r)].append(i)

    repairs, stats = [], collections.Counter()

    for kk, idxs in groups.items():
        title, date = kk
        if not title or not date:
            stats["skip_no_key"] += 1
            continue

        pm = [mins(published[i].get("time")) for i in idxs]
        if any(x is None for x in pm):
            stats["skip_unparseable_time"] += 1
            continue

        # ---- same-day repair ------------------------------------------------------
        fm = [mins(t) for t in fresh.get(kk, [])]
        if fresh.get(kk) is not None and not any(x is None for x in fm) and fm:
            if set(pm) == set(fm):
                stats["skip_already_correct"] += 1
                continue
            for off in OFFSETS:
                if {x - off for x in pm} == set(fm):
                    for i, a in zip(idxs, pm):
                        repairs.append((i, date, fmt(a - off),
                                        f"group set-match at -{off}min (UTC->Central)"))
                    stats[f"repaired_time_{off}"] += len(idxs)
                    break
            else:
                stats["skip_no_offset_match"] += 1
            continue

        # ---- date-roll repair: published 12:00-5:59 AM against the PREVIOUS day ----
        # Only ever backward, and only out of the small-hours band the defect can produce.
        if len(idxs) != 1 or pm[0] >= 360:
            stats["skip_no_fresh_key"] += 1
            continue
        try:
            prev = (datetime.date.fromisoformat(date) - datetime.timedelta(days=1)).isoformat()
        except ValueError:
            stats["skip_bad_date"] += 1
            continue
        pfm = [mins(t) for t in fresh.get((title, prev), [])]
        pfm = [x for x in pfm if x is not None]
        if len(set(pfm)) != 1:
            stats["skip_no_fresh_key"] += 1
            continue
        want = pfm[0]
        for off in OFFSETS:
            if (pm[0] + 1440 - off) == want:
                repairs.append((idxs[0], prev, fmt(want),
                                f"date roll-BACK + time at -{off}min (UTC crossed midnight)"))
                stats[f"repaired_dateroll_{off}"] += 1
                break
        else:
            stats["skip_no_fresh_key"] += 1

    return repairs, stats


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    work = argv[0] if argv else WORK
    if not os.path.isabs(work):
        work = os.path.join(ROOT, work)

    # A missing or empty feed pull would make EVERY row look like it has no fresh counterpart,
    # i.e. the pass would report a serene "0 repaired" while doing nothing -- the quiet-zero
    # class.  `zero is a claim about the INPUT`: make the absence a crash.
    if not os.path.exists(PULL):
        raise SystemExit(f"ical_time_repair: {PULL} is absent -- cannot repair against a feed "
                         "pull that does not exist.  A missing authority is a crash, never a "
                         "silent 0 repaired.")
    with open(PULL, encoding="utf-8") as fh:
        pull = json.load(fh)
    rows = pull.get("rows", []) if isinstance(pull, dict) else pull
    if not rows:
        raise SystemExit("ical_time_repair: feed pull carries 0 rows -- refusing to conclude "
                         "that every carried time is unverifiable.")

    with open(work, encoding="utf-8") as fh:
        w = json.load(fh)
    ev = w.get("events", [])

    fresh = index_fresh(rows)
    repairs, stats = plan(ev, fresh)

    print(f"\nical_time_repair: {len(ev)} published events vs {len(rows)} freshly-parsed rows")
    print(f"  ROWS REPAIRED : {len(repairs)}")
    for k2 in sorted(stats):
        print(f"    {k2:26} {stats[k2]}")

    for i, nd, nt, why in repairs[:12]:
        r = ev[i]
        od, ot = r.get("date"), r.get("time")
        arrow = f"{od} {ot}  ->  {nd} {nt}"
        print(f"    {arrow:44}  {r.get('title','')[:40]}")
    if len(repairs) > 12:
        print(f"    ... and {len(repairs)-12} more")

    if dry:
        print("\nDRY RUN -- nothing written.")
        return 0
    if not repairs:
        print("\nNothing to do (converged).")
        return 0

    for i, nd, nt, _why in repairs:
        ev[i]["date"] = nd
        ev[i]["time"] = nt
    with open(work, "w", encoding="utf-8") as fh:
        json.dump(w, fh, ensure_ascii=False)
    print(f"\nwrote {work}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
