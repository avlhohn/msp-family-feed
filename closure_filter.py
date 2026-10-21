"""STEP 4.3 tail pass — drop rows whose OWN TITLE announces the thing is not happening.

Found 2026-08-31.  30 rows in the compiled dataset were closure / cancellation notices
carried as if they were events: `CANCELED: Baby Storytime`, `LIBRARY CLOSED: Labor Day`,
`SCL Branches Closed - Labor Day`, `City Hall Closed - Labor Day`.  A family opening the
app sees these as things to go to.

Why the existing guards miss them
---------------------------------
`fetch_feeds.py` already drops LibCal / BiblioCommons rows carrying a machine-readable
*cancelled status flag* (7 dropped per system on 2026-08-31).  These rows carry the
cancellation in the **title text** instead, so no status flag exists to test.  They then
enter the carried base and survive every subsequent run: no dedup pass looks at meaning,
and `adult_events_filter.py` screens for adult *audience*, not for non-occurrence.

Why dropping is precision-safe here, unlike a merge
---------------------------------------------------
CLAUDE.md's standing asymmetry is that a missed duplicate is cosmetic but a wrong merge
silently deletes a real venue.  That asymmetry does not transfer to this pass, because the
row's own title is the evidence: the source is stating the event will not occur.  Dropping
it removes a claim the source has already retracted.  The risk runs the other way — a
false *positive* would drop a real event whose title merely contains the word "closed".
So the patterns below are deliberately narrow and anchored:

* CANCELLED must appear as an explicit marker — string-initial, wrapped in `**`, wrapped in
  `--` (TWO or more hyphens; a single hyphen is NOT a marker, so `Non-cancelled Family Hike`
  survives), or immediately followed by `:` / ` - `.  A bare mid-sentence "cancelled" does
  NOT match, because a description like "rain or shine, never cancelled" is not a
  cancellation.  The `--`-wrapped alternative was added 2026-09-26 after two real rows
  (`Peering Thru the Earth --Cancelled--`, `St. Croix Sunrise -- Cancelled--`) were found
  live, unreachable by every alternative: the trailing-punctuation alternative requires
  whitespace AFTER the punctuation and these titles end at it, and no alternative handled a
  dash-wrapped marker even though the exactly analogous `**`-wrapped form was handled.  A
  VOCABULARY completion, not a SHAPE change — the explicit-marker requirement and the
  title-only scope are both untouched.
* CLOSED must be preceded by an institution word (library / branch / branches / office /
  offices / city hall / center / museum / park / pool / building), or appear as the noun
  "closure".  This is what keeps `Closed Captioning Workshop`, `Closed Loop Recycling`
  and `Close Reading Book Club` alive — all real programming shapes.
* CLOSED is ALSO a closure when it is the TERMINAL word of the title and is introduced by a
  colon or dash — `Pine River: CLOSED`.  Added 2026-10-02 after that exact row was found
  live in `events`, dated 2026-10-12, having passed every pass in the 4.3 chain.  The gap:
  the institution list holds CATEGORY words (library, branch, museum) and this title names
  the BRANCH ITSELF ("Pine River" is a Kitchigami Regional Library branch), so no
  institution word is present to anchor on and the row was structurally unreachable.
  This is the same VOCABULARY completion as the 2026-09-26 `--`-wrapped CANCELLED
  alternative above: it adds one anchored marker alternative and leaves the title-only
  scope and the deliberate narrowness untouched.  It is NOT a widening to bare `closed`.
  MEASURED BEFORE THE EDIT, and the measurement is the point: on this run's 7,829 titles
  bare `\bclosed\b` matches the SAME single row, so live data could not tell the safe rule
  from the dangerous one — the false positives the design protects were simply absent from
  the window.  The DOCUMENTED FP set is the real control, and against it bare `closed`
  wrongly drops 4 of 9 cases while this alternative drops 0.  Note `Closed Captioning:
  Workshop` stays alive precisely because the marker must be TERMINAL.

Idempotent.  Reports every dropped title so a wrong drop is visible rather than silent —
the same standard `dupsweep.py` is held to.
"""
import json, os, re, sys, collections

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
RUNDIR = os.environ.get("MSP_RUNDIR", ".")

# CANCELLED only as an explicit marker, never mid-sentence.
CANCEL = re.compile(
    r"^\s*\**\s*cancell?ed\b"           # string-initial: "CANCELED: X", "CANCELLED - X"
    r"|\*\*\s*cancell?ed\s*\**"          # bracketed marker: "**CANCELLED** - X"
    r"|-{2,}\s*cancell?ed\b"             # dash-wrapped marker: "X --Cancelled--", "X -- Cancelled--"
    r"|\bcancell?ed\s*[:\u2013\u2014-]\s", # "... CANCELED: X" / "... CANCELED - X"
    re.I)

# CLOSED only when an institution is what is closed.
INSTITUTION = (r"librar(?:y|ies)|branch(?:es)?|office(?:s)?|city hall|"
               r"community center|rec(?:reation)? center|museum|pool|building|"
               r"service center|all locations")
CLOSED = re.compile(
    r"\b(?:" + INSTITUTION + r")\b[^.;]{0,30}?\bclosed\b"    # "Library Closed", "SCL Branches Closed"
    r"|\bclosed\b[^.;]{0,20}?\b(?:" + INSTITUTION + r")\b"   # "Closed: All Libraries"
    r"|\bclosure\b"                                          # "Library Closure: Labor Day"
    r"|\bno storytime\b"                                     # "No Storytime, Library Closed"
    r"|[:\u2013\u2014-]\s*closed\s*$",                       # terminal marker: "Pine River: CLOSED"
    re.I)


def is_closure(title):
    t = (title or "").strip()
    if not t:
        return None
    if CANCEL.search(t):
        return "cancelled"
    if CLOSED.search(t):
        return "closed"
    return None


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "_compiled_work.json"
    dry = "--dry-run" in sys.argv
    d = json.load(open(src, encoding="utf-8"))

    reasons = collections.Counter()
    dropped = []
    for c in CATS:
        keep = []
        for r in d.get(c, []):
            why = is_closure(r.get("title"))
            if why:
                reasons[why] += 1
                dropped.append({"category": c, "reason": why,
                                "title": (r.get("title") or "")[:110],
                                "date": (r.get("date") or "")[:10]})
            else:
                keep.append(r)
        if not dry:
            d[c] = keep

    tag = "DRY RUN — " if dry else ""
    print(f"{tag}closure/cancellation filter: {len(dropped)} rows dropped {dict(reasons)}")
    for x in dropped:
        print(f"  DROP [{x['reason']:9s}] {x['date'] or '          '}  {x['title']}")

    if not dry:
        json.dump(d, open(src, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(dropped, open(os.path.join(RUNDIR, "_closure_filter_report.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"  report -> {os.path.join(RUNDIR, '_closure_filter_report.json')}")


if __name__ == "__main__":
    main()
