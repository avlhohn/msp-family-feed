# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-23 · **Finished:** 09:57 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `aa06e3096b64` — 1,429,101 bytes, 4,407 data rows, 10-column
header exact, and **byte-identical to the GitHub remote**, so its provenance is verified rather
than assumed. **Published log:** blob `922ae436f560`, 1,440,026 bytes, 4,412 data rows, CRLF 4,413
and bare LF 0.

## Summary

The open-issue queue held **19 rows across 18 distinct items** (13 `unresolved_image`, 6
`unresolved_website`, dated 2026-07-08 to 2026-08-16). **Zero were resolved with a photo or a
website — an honest zero, not a pass that no-opped.** But the queue moved for the first time since
2026-09-10, because **13 of the 18 items turned out to have no row in any published artifact at
all**, and those rows were closed as non-actionable rather than left to occupy the queue forever.

The distinction matters and is preserved in the log itself: those 13 carry
`resolved_by = "error-fixer (closed: absent from feed)"` and a `resolution_note` that opens
**"CLOSED NON-ACTIONABLE (not a fix)"**. Nobody reading this log later should be able to mistake
them for image or website wins. By the fixer's own run history — distinct `run_date` values
carrying a `fixer_summary` row, counted after the last genuine queue resolution on **2026-09-10** —
this is the **twelfth** consecutive run with no actual fix. That number is *observed*, not carried
forward from the previous report.

The substantive output of this run is therefore two things: a diagnosis of *why* most of the queue
was unfixable, and **four escalation rows for defects discovered by the re-attempt** — including
one factually-wrong venue and one dead URL currently live in the feed.

## What was actually in the queue

Partitioning the 18 work units against the five published CSVs and the published feed JSON gave a
clean split: **6 items still have a live row** in a published artifact, and **12 do not**.

The 12 absent items were confirmed by a **four-stage probe**, not by a single lookup, because a
name-miss and a real absence look identical: exact-title match; token-overlap scoring across all
five published CSVs (events 4,864 / parks 849 / deals 140 / volunteer 268 / restaurants 461);
targeted inspection of every near-hit by hand; and a fourth pass over the published
`msp_family_guide.json` (6,582 rows) in case a row existed in the feed but not in a CSV. Every one
is an expired seasonal event that aged out of the rolling window — Maplewood Celebrate Summer,
Moorhead Summer Splash, Music in the Park Thursdays, Winona Parks & Rec Summer Activities, two
duplicate rows for Summer Outdoor Festival - Brainerd, and so on. No resolution can change a feed
that no longer contains the row.

**Three near-hits were rejected as different items, and each rejection is recorded on the row** so
a later reader does not re-derive the judgement:

- `Urban Air Trampoline Parks - Minnesota Locations` — events.csv carries three *per-location*
  Urban Air rows (Coon Rapids, Apple Valley, Plymouth). The queue row is the umbrella
  "Minnesota Locations" roll-up, which is gone; and an umbrella banner is a forbidden resolution
  anyway, so even a match would not have helped.
- `Toddler Tuesday - ECFE` — the events.csv "Toddler Tuesday" is **Winona** (800 Riverview Drive,
  already carrying a `site_photo`). The queue row is **Coon Rapids ECFE**.
- `Movies in the Park - Mankato` — the events.csv "Movies in the Park" is **Duluth** (Leif Erikson
  Park). Geography is not identity.

One further row, idx 947 `"688 rows"`, is not an item at all: its description is a per-category
count dictionary, overwhelmingly municipal neighbourhood parks with no individual page. It is a
**roll-up diagnostic** that was permanently occupying a queue slot no research could ever clear.
Closed on that basis and labelled as such.

## The 6 live rows: re-attempted, none met the bar

All six have a real row in a published CSV, all six were re-attempted this run, and none produced a
candidate that clears the verification bar. Leaving them open is the correct outcome, not a
shortfall.

**Lake Ann Park** (`unresolved_image`, open since 2026-07-08) is the most-probed row in the queue,
so this run recorded its **dead routes** explicitly to stop the next run paying for them again:
the venue's own `chanhassenmn.gov` page returns **HTTP 403 to WebFetch** — which is a *tooling
block, not proof the photo is absent*, and the difference is the whole point of writing it down;
Openverse returns `result_count = 0` for both "Lake Ann Park Chanhassen" and "Lake Ann Park
Chanhassen Minnesota", queried **parent-side**, because WebFetch cannot reach that API at all and a
subagent negative there is a search that never ran. Two candidates were offered and both
**rejected**: a TripAdvisor CDN image (third-party aggregator UGC is none of the three permitted
sources) and an Openverse "Chanhassen City Park" Flickr hit (a **different park** — geography is
not depiction).

**Bowlero Brooklyn Park (Lucky Strike)** yielded only chain-wide promotional imagery, which depicts
the brand rather than the location. **Denny's, Perkins and Rubio's** are multi-location umbrella
rows whose address field reads "Multiple Twin Cities locations" — there is no single place to
depict, so the demotion rule produces a null result by design rather than by failure.
**Bump & Putt** is a website row and is covered below.

## Escalations — four defects this run DISCOVERED

These are new open rows (`issue_type = fixer_escalation`, `resolved_date` blank) for problems the
re-attempt surfaced. The fixer does not rebuild CSVs, so it cannot act on any of them; they need
the build task or the owner.

**1 · Rubio's Rewards Thursday Kids Free Meal — DATA INTEGRITY (warning).** Rubio's Coastal Grill
operates only in Southern California (60), Arizona (17) and Nevada (5) — **82 US restaurants, zero
in Minnesota.** The row's address reads "Multiple Twin Cities locations", which no source
corroborates. This was corroborated **two independent ways** — the re-attempt research and a
separate parent-side web search — before being written, because a single source claiming a venue
does not exist is exactly the shape that should not move published data on its own. Recommend the
build task **remove this row**. It is not an image problem, and the image queue is where it has been
sitting.

**2 · Denny's Thursday Kids Eat Free — CLOSED-VENUE RISK (warning, single-source).** Research
reports that the Minnesota Denny's franchisee (M15 Inc.) abruptly closed five locations in early
September 2026 — Burnsville, Maplewood, Roseville, North Branch and Hudson WI — leaving roughly
eight in the state. **Flagged SINGLE-SOURCE; owner verification required before acting.** It
matters because the row points families at "Multiple Twin Cities locations". The promotion itself
is reported still active at participating locations.

**3 · Bump & Putt Family Fun Center — DEAD URL LIVE IN THE FEED (warning).** The website currently
stored on this row, `https://www.brainerd.com/business/bump-n-putt-family-fun-park/`, returns
**HTTP 404** ("that page doesn't seem to exist"). A 404 in the feed is worse than a blank field: it
sends a family to a broken page rather than to a search. No official website or official Facebook
page exists for this business — it appears only in third-party directories, which the spec forbids
as a resolution, so **a Yelp listing offered by the research pass was rejected**. The business does
appear to still operate (Pequot Lakes, 29107 State Hwy 371, 218-568-8833, consistent with the "four
miles north of Nisswa" description), though that evidence is modest. **Recommend blanking the dead
URL.**

**4 · Lake Ann Park — DEAD ROUTES RECORDED (info).** The four dead ends listed above, written to
the log so a later run does not re-probe them cold and does not mistake a 403 for an absence.

## Scope note: fixer-shaped rows the fixer cannot reach

After this run the log holds **3,858 open rows**, of which only **6** are selectable by the spec's
two-`issue_type` filter. Sitting just outside it are **300 `missing_website`**, **240
`generic_image`** and **26 `attempted_no_photo`** rows — 566 rows that are fixer-shaped work by any
plain reading, and structurally unreachable by the task built to drain them. A meaningful number of
them were written *by the fixer itself* on earlier runs.

This is recorded and **deliberately not acted on**. Widening the selection filter is a change to
the task's scope, and a scheduled task should not expand its own remit unilaterally — it needs an
owner decision. But the pattern this run demonstrates is the argument for making that decision:
two-thirds of the reachable queue turned out to be closable dead weight, which means the queue's
size has been overstating the amount of real work available to this task for weeks.

## Diagnostics

**The build/fixer race did not bite this run.** The known failure mode is that this task's base log
predates the day's build, so it never sees the build's own rows. Today it did: the base blob
`aa06e3096b64` is exactly the log the build published at 09:31:33Z (commit `6fa28a5d13`, +145
rows), and this task published on top of it at 09:56:38Z. Worth noting because the race is
documented as reliable, and today it was not — so the base must keep being verified by blob rather
than assumed stale.

**The byte-identity control passed before any edit.** The untouched file was round-tripped through
`csv.reader` → `csv.writer(lineterminator='\r\n')` and compared byte-for-byte against the original
(1,429,101 bytes, identical), which is what makes "my edit changed 13 rows" distinguishable from
"my writer silently rewrote every line". CRLF is preserved verbatim and bare LF is 0 on both sides.

**Every touched row was asserted before it was written** — item text matched against the expected
value to catch index drift, width held at 10 columns across all 4,412 rows, and rows already
carrying a `resolved_date` skipped rather than overwritten (0 were skipped; none had drifted).

**The publish was verified by read-back, and by status code.** `error_log.csv` PUT returned
**HTTP 200 — updated**, not 201; a 201 would mean a path that was not previously in the repo, which
on anything outside the sanctioned file list is a contract violation rather than a success. The
read-back blob matches the local blob exactly (`922ae436f560`, 1,440,026 bytes).

**Two research recommendations were rejected outright**, which is the reason a research pass is
treated as producing candidates rather than answers: the TripAdvisor CDN image for Lake Ann Park,
and the Yelp URL substitution for Bump & Putt. Both would have passed a naive "did the subagent
return a URL" check.

## A post-publish tree check, and the contract it was checked against was wrong

Yesterday's run accidentally published `CLAUDE.md` into the repo (HTTP **201 — CREATED**) and
reverted it, and the lesson recorded was that a 201 answers *"did the bytes land?"* but never
*"should this path exist?"*. So this run added a **tree check** after publishing: read the repo's
file list and compare it against the sanctioned set.

**It failed — and the repo was fine.** It flagged `image_upgrades.py` and `meal_deals.csv`.
Provenance settled it before anything was touched: both first appeared **2026-07-27**, were last
modified **2026-08-29** and **2026-08-25**, and have **zero commits today**. Neither came from this
run. What was wrong was my expected set, which I had built from CLAUDE.md's sentence *"only the 4
safety-critical helper/test files the owner uploads by hand"* — while the same document elsewhere
says the Wikimedia layer *"was committed into `image_upgrades.py` (commit `54e8a8f8`)"*. **Both
cannot be true, and the repo is the one telling the truth.** The contract prose undercounts: there
are five helper files, not four.

This matters more than a miscount, because the tree audit that yesterday's incident motivated
**derives its expected set from that prose**. An audit keyed to a wrong contract fails both ways —
it flags legitimate files, and it would wave through a stray one that happened to be named in the
prose. The guard built to catch an unsanctioned path is only as good as the list it checks against,
and that list is a paragraph nothing asserts.

Nothing was deleted. Both paths predate this run and sit outside this task's two sanctioned write
paths, and deleting a published file on the strength of a claim in prose is unrecoverable if the
claim is the thing that is wrong — which, here, it was.

**A second item falls out of it: `meal_deals.csv` is an orphan.** The build writes `deals.csv`; the
category *keys* carry the long names and the *files* do not. `meal_deals.csv` has not been touched
since **2026-08-25 — 29 days** — and sits in the repo beside the live `deals.csv`. Anything reading
the artifacts by category name opens the stale one. Not this task's to remove.

**Both halves of the check were proven to fail on purpose**, and the failing case was *predicted
before the mutant ran* rather than inferred from a count: the unexpected-path branch failed
naturally (above), and the blob-drift branch — the one that would catch a publish that did not
actually land — was mutated and went red naming exactly `error_log.csv blob drift`, with the
restored control green. Run under `python3 -B`, because a mutation harness that leaves bytecode
enabled can test the wrong code.

## Ledger

| | |
|---|---|
| Queue selected | 19 rows / 18 distinct items |
| Closed non-actionable | 13 (12 absent from feed, 1 roll-up diagnostic) |
| Left open (live row, bar not met) | 6 |
| Images resolved | **0** |
| Websites resolved | **0** |
| Escalation rows added | 4 (3 warning, 1 info) |
| `fixer_summary` rows added | 1 |
| Log rows | 4,407 → **4,412** |
| Published blob | `922ae436f560` (read-back verified) |
