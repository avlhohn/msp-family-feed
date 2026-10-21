#!/usr/bin/env python3
"""STEP 1 findings writer -- emits `_findings.json` for errlog_step7.py to consume.

HISTORY, because both halves of it are load-bearing
---------------------------------------------------
Promoted to this undated root name on 2026-09-26, retiring the `_findings_init_NNNN.py`
family that had reached three instances and whose newest member carried
`assert RUN == "2026-09-25"` as a hard date literal.  That promotion took the run date from
`MSP_TODAY` and made a missing or malformed one a CRASH rather than a default -- CLAUDE.md's
"a date a helper can guess is a date it will guess wrong".

IT WAS NOT ENOUGH, AND THE WAY IT FAILED IS THE FINDING (2026-09-27)
--------------------------------------------------------------------
The promotion deleted the date from the FILENAME and from the `run_date_verified` ITEM, and
left the run's entire eight-paragraph NARRATIVE frozen in `rows()` as string literals.  So on
2026-09-27 this helper ran clean and produced a `_findings.json` that:

  * passed all of its own contract assertions,
  * passed errlog_step7.py's `run_date_verified == argv[1]` assertion,
  * carried `run_date_verified = 2026-09-27` in the one interpolated field, and
  * described the 2026-09-26 RUN in every description body -- "TODAY=2026-09-26 (Saturday)",
    an HTTP Date header of `Sat, 26 Sep 2026 08:12:53 GMT`, and a test baseline of
    "closure_filter 35 / 577 passed" when the suites had been re-read live at 38 / 580.

That is WORSE than the `_errlog_0907_feeds.py` case it replaced.  That one filed a whole run
under YESTERDAY'S DATE, which is visibly wrong the moment anyone reads the log.  This one files
the WRONG RUN under the RIGHT DATE, and nothing downstream can see it: every row-shape check
passes, the count is plausible, the date is correct, and the prose is a lie about which run
produced it.  It is the `build_guide.py` stale-header defect in a second artifact -- a false
claim about the whole file that no row-level tripwire can reach.

The generalisation for CLAUDE.md: **deleting a date literal from a helper's NAME and from its
one derived field does not make the helper undated if its BODY is a frozen snapshot of one
run.**  Per-run CONTENT does not belong in a durable helper at all.  A durable helper carries
the CONTRACT; the run supplies the content.

WHAT THIS FILE NOW DOES
-----------------------
The narrative lives in `_findings_step1.json`, which the run writes and this helper READS.
That file carries its own `run_date`, and a mismatch against `MSP_TODAY` is a hard failure --
the same existence + freshness discipline already proven on `_image_backfill.json`.  So a
carried-forward narrative is now a CRASH instead of a silent stale publish.

Contract assertions preserved from the 2026-09-26 version (all made to fail on purpose):
  * the 6-field row shape `[severity, category, step, issue_type, item, description]`
  * severity in {info, warning}
  * the RESERVED `issue_type` namespaces -- `ical_feed_pull`, `run_summary`, `image_backfill`
    exactly, and `deal_source_` by PREFIX.  errlog_step7.py counts these, so a row that
    borrows one enrols itself in STEP 7's signal assertions and fails the run
    (2026-09-13 prefix-collision finding).  Name a CHECK of a signal `<thing>_check`.
  * exactly one `run_date_verified` row, whose item equals MSP_TODAY

NEW guards, and what they DO NOT cover
--------------------------------------
Two narrow stale-narrative guards, both measured against real data before being added:

  1. `TODAY=<date>` anywhere in any description must name the run date.  `TODAY=` is ALWAYS a
     claim about the current run, so this is zero-false-positive by construction.
  2. An HTTP-Date string (`Sun, 27 Sep 2026 ...`) must name the run date AND its weekday name
     must be that date's real weekday.  Also always a claim about the current run.

FALSE-POSITIVE SURFACE MEASURED FIRST: the 2026-09-26 narrative carried 29 date literals, of
which 27 are HISTORICAL CITATIONS ("~34h on 2026-08-25", "the 2026-09-13 prefix-collision
finding") that a naive "no date but the run date" rule would have flagged as stale.  Those must
never trip -- a findings narrative that cannot cite a past incident is useless.  Only the two
self-referential FORMS above are checked.  Note `generated_date=` is deliberately NOT checked:
it legitimately names the CARRIED BASE's older date, which is a different run by design.

WHAT THESE GUARDS DO NOT COVER, stated in the same breath per CLAUDE.md: a stale narrative
written in prose that happens to use neither form -- "the baseline is 577 passed" with no date
attached -- still passes.  The `run_date` field on `_findings_step1.json` is the real defence;
these two guards are the backstop for the specific shapes that actually shipped.  And, exactly
as the 2026-09-26 note said of `run_date_verified`, the run date's CORRECTNESS comes from
elsewhere entirely: the server-side derivation at STEP 1, cross-checked by errlog_step7.py's
independently-supplied argv[1].

Usage:
    MSP_TODAY=YYYY-MM-DD python3 findings_init.py            # writes _findings.json
    MSP_TODAY=YYYY-MM-DD python3 findings_init.py --check     # verify only, write nothing

`import findings_init` is safe -- main() is behind __main__ and nothing here writes at import
time (the 2026-09-18 side-effect check, performed rather than assumed; pricetype_fix.py remains
the counter-example where importing IS a write).
"""
import datetime
import json
import os
import re
import sys

RUN = os.environ.get("MSP_TODAY", "")
if not re.fullmatch(r"20\d\d-\d\d-\d\d", RUN):
    raise SystemExit(
        f"findings_init.py: MSP_TODAY missing or malformed: {RUN!r}. "
        "This is deliberately a CRASH and not a default -- a date this helper could guess "
        "is a date it would guess wrong, and the whole run files under it.")
try:
    datetime.date.fromisoformat(RUN)
except ValueError:
    raise SystemExit(f"findings_init.py: MSP_TODAY is not a real calendar date: {RUN!r}")

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNDIR = os.environ.get("MSP_RUNDIR", ROOT)
CONTENT = os.path.join(ROOT, "_findings_step1.json")
OUT = os.path.join(RUNDIR, "_findings.json")

RESERVED_EXACT = ("ical_feed_pull", "run_summary", "image_backfill")
RESERVED_PREFIX = ("deal_source_",)

# EXEMPT FROM THE STALE-NARRATIVE GUARDS, and this is an ALLOWLIST OF ONE, not a loosened rule.
# The finding that DOCUMENTS the stale-narrative defect has to QUOTE the stale strings as its
# evidence -- it says, in as many words, that the previous body carried `TODAY=2026-09-26` and an
# HTTP Date of `Sat, 26 Sep 2026`.  A guard keyed on a string FORM cannot tell a quotation of that
# form from an assertion of it, which is the same trap CLAUDE.md records for dupsweep.na()'s
# `minnesota` target: a grep target that is a substring of ordinary data.
#
# WHY NOT A GENERAL "backticked text is a quotation" ESCAPE, which was the first idea: measured
# against the narrative that ACTUALLY shipped stale on 2026-09-27, `Sat, 26 Sep 2026 08:12:53 GMT`
# WAS inside backticks and `TODAY=2026-09-26` was NOT.  So a backtick escape would have let half
# the real defect through -- it would have caught only the TODAY= half of the exact case these
# guards exist for.  A named, row-scoped exemption keeps the guards at full strength on all 18
# other rows and puts the exception where a reader can see it.
#
# Adding an issue_type here disables a real safety check for that row.  Do not grow this set to
# silence a complaint; reword the row instead.
QUOTES_STALE_DATES = frozenset({"stale_findings_narrative_check"})

RX_TODAY_ASSIGN = re.compile(r"\bTODAY\s*=\s*(20\d\d-\d\d-\d\d)")
RX_HTTP_DATE = re.compile(
    r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*(\d{1,2})\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d\d)")
_MON = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def rows(run, path=None):
    """Load this run's findings narrative.  The CONTENT is per-run and lives OUTSIDE this
    helper; see the module docstring for why a frozen body is the defect this closes."""
    path = path or CONTENT
    if not os.path.exists(path):
        raise SystemExit(
            f"findings_init.py: {os.path.basename(path)} is ABSENT. The per-run findings "
            "narrative is an INPUT this helper does not own and must not invent -- writing a "
            "plausible one is exactly the frozen-body defect of 2026-09-27. Write the run's "
            "own findings to that file first.")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    got = doc.get("run_date")
    if got != run:
        raise SystemExit(
            f"findings_init.py: {os.path.basename(path)} carries run_date={got!r} but "
            f"MSP_TODAY={run!r}. This is a CARRIED-FORWARD NARRATIVE -- the 2026-09-27 defect "
            "where the date field was right and every description body described the previous "
            "run. Regenerate the narrative for this run; do not restamp the field.")
    return [list(r) for r in doc["rows"]]


def stale_narrative(body, run):
    """Complaints about self-referential dates in one description.  Returns a list of
    strings, empty when clean.  Only the two ALWAYS-self-referential forms are checked;
    historical citations are legitimate and must never trip (see docstring)."""
    out = []
    for m in RX_TODAY_ASSIGN.finditer(body):
        if m.group(1) != run:
            out.append(f"`TODAY={m.group(1)}` names a run that is not {run}")
    for m in RX_HTTP_DATE.finditer(body):
        wd, day, mon, yr = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        try:
            d = datetime.date(yr, _MON[mon], day)
        except ValueError:
            out.append(f"HTTP-Date {m.group(0)!r} is not a real calendar date")
            continue
        if d.isoformat() != run:
            out.append(f"HTTP-Date {m.group(0)!r} names {d.isoformat()}, not the run date {run}")
        elif d.strftime("%a") != wd:
            out.append(f"HTTP-Date {m.group(0)!r} weekday is wrong; "
                       f"{d.isoformat()} is a {d.strftime('%a')}")
    return out


def check(F, run):
    """Every contract assertion, as a list of complaints rather than a bare assert, so a
    caller (and a fail-on-purpose mutant) can read WHICH one fired rather than a count."""
    bad = []
    for r in F:
        if len(r) != 6:
            bad.append(f"row is not the 6-field contract ({len(r)} fields): {r[:2]}")
            continue
        sev, _cat, _step, itype, _item, body = r
        if sev not in ("info", "warning"):
            bad.append(f"bad severity {sev!r} on {itype!r}")
        for p in RESERVED_PREFIX:
            if itype.startswith(p):
                bad.append(f"reserved issue_type PREFIX {p!r}: {itype!r} -- this row would "
                           "enrol itself in STEP 7's signal assertions; name a check "
                           "<thing>_check")
        if itype in RESERVED_EXACT:
            bad.append(f"reserved issue_type {itype!r} -- errlog_step7.py appends and counts "
                       "this one itself")
        if not str(body).strip():
            bad.append(f"empty description on {itype!r}")
        if itype not in QUOTES_STALE_DATES:
            for c in stale_narrative(str(body), run):
                bad.append(f"STALE NARRATIVE in {itype!r}: {c}")
    verified = [r for r in F if len(r) == 6 and r[3] == "run_date_verified"]
    if len(verified) != 1:
        bad.append(f"exactly one run_date_verified row is mandatory; found {len(verified)}")
    elif verified[0][4] != run:
        bad.append(f"run_date_verified item is {verified[0][4]!r}, expected {run!r}")
    return bad


def main():
    F = rows(RUN)
    bad = check(F, RUN)
    if bad:
        for b in bad:
            print("FINDINGS CONTRACT VIOLATION:", b, file=sys.stderr)
        raise SystemExit(f"findings_init.py: {len(bad)} contract violation(s); nothing written.")

    if "--check" in sys.argv:
        print(f"findings_init.py --check OK: {len(F)} rows, run_date_verified={RUN}")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(F, fh, ensure_ascii=False, indent=1)
    sev = {}
    for r in F:
        sev[r[0]] = sev.get(r[0], 0) + 1
    print(f"findings_init.py -> {OUT}  rows={len(F)}  {sev}  run_date_verified={RUN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
