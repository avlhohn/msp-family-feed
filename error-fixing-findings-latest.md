# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-22 · **Finished:** 12:37 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `4c240fc82719` — 1,329,106 bytes, 4,140 data rows, 10-column
header exact. **Published log:** blob `a368656b90ac`, 1,376,688 bytes, 4,262 data rows. The gap
between those two numbers is not all mine: the daily build appended 108 rows *while this task was
running*, which is this run's principal finding.

## Summary

The open-issue queue held **19 rows across 18 distinct items** (13 `unresolved_image`, 6
`unresolved_website`, all dated 2026-07-08 to 2026-08-16). **None were resolved.** By the
fixer's own run history this is the **eleventh** consecutive run at zero — the last genuine
queue resolution was stamped **2026-09-10**, and the fixer has run on 09-11, 09-12, 09-14,
09-15, 09-16, 09-17, 09-18, 09-19, 09-20, 09-21 and today since. That number is *observed*
(distinct `run_date` values carrying a `fixer_summary` row, filtered to those after the last
`resolved_date` on a queue row), not carried forward: the previous report claimed "twelfth
consecutive" on **2026-09-20**, which by the same count was the ninth. See Diagnostics.

**The substantive output of this run is not queue work. It is a retraction.** Earlier today I
logged a `critical` row asserting that the daily build had hard-failed at STEP 7 and stranded
its findings. That was wrong, and it was wrong in a specific way worth naming: I inferred a
**mechanism I never observed** from two accurate observations. The build had simply not
reached STEP 7 yet — it was still running, 2h44m of overlap with this task — and it went on to
complete normally at 12:28 UTC. Both rows are retracted in place, the real defect is logged,
and the process failure that produced them is logged against myself.

Queue integrity was confirmed rather than assumed: the build's 108 new rows contained **0**
new `unresolved_website` / `unresolved_image` rows, so the queue computed against the
pre-build log was already complete and is still 19 rows / 18 items after the build landed.

## Resolved this run

**Zero queue rows were resolved.**

Four rows dated 2026-09-22 now carry a `resolution_note`, and none of them is queue work —
all four are rows this run wrote and then corrected:

| issue_type | disposition |
|---|---|
| `build_step7_assertion_fired` | **RETRACTED** — asserted a mechanism that was never observed |
| `build_findings_stranded` | **RETRACTED** — consequence claim resting on the above; nothing was stranded |
| `no_run_summary_today` | **PARTIAL** — the observation stands; the cause named in its last sentence is retracted |
| `fixer_summary` | **CORRECTED** — queue findings stand; the failure claim in its last sentence is withdrawn |

The re-attempt pass ran against the queue as normal. Every item either resolved to a page
that does not specifically name the venue, to no image that survives the aggregator /
umbrella / logo demotion rules, or to a source that is structurally unreachable from this
task (see below). Nothing was accepted on a weaker standard to move the number.

## Still open

19 rows, 18 distinct items. Grouped by why they are still here:

| # | item | type | first seen | why still open |
|---|---|---|---|---|
| 1 | Lake Ann Park | image | 2026-07-08 | **Live and reachable.** The facility-detail page exists; STEP 4.5 has never fetched it (see Diagnostics) |
| 2 | Bowlero Brooklyn Park (Lucky Strike) | image | 2026-07-23 | **Live and evidenced.** Rebrand confirmed 23 days ago; no consumer ships the evidence |
| 3 | Bump & Putt Family Fun Center | website | 2026-08-15 | **Live.** Prior URL dead; replacement needs an owner decision, not a fixer guess |
| 4–12 | Maplewood Celebrate Summer; Moorhead Summer Splash; Movies in the Park – Mankato; Music in the Park Thursdays – Mankato; Niko Moon Concert – Vetter Stone Amphitheater; Winona Parks & Rec Summer Activities; Summer Outdoor Festival – Brainerd (×2 rows); Toddler Tuesday – ECFE | image / website | 07-08 … 08-15 | **Aged out of the feed.** These are summer 2026 rows; the events no longer exist to carry an image or a link |
| 13–15 | Denny's Thursday Kids Eat Free; Perkins Tuesday Kids Eat Free; Rubio's Rewards Thursday Kids Free Meal | image | 2026-07-23 | **Known false fuzzy matches.** National chain promos; any photo found is a brand asset, not a depiction of a local venue |
| 16–18 | Urban Air Trampoline Parks – Minnesota Locations; Mission Branch Library Community Garden – Monday Nights; Pizza King Station | image / website | 07-23 … 08-14 | **Chain / multi-location promotion.** One row standing for N locations cannot take one venue's photo or URL without the chain-collapse error |
| 19 | `688 rows` | website | 2026-08-16 | **A roll-up, not an item.** Names a count, so there is nothing to re-attempt against |

Three of the 18 (rows 1–3) are genuinely actionable and are the ones worth an owner's
attention. The remaining 15 are not fixer-solvable in their current form: nine describe
events that no longer exist, three are chain promotions, three are national-brand fuzzy
matches, and one is a roll-up. **A queue whose open rows are mostly unsolvable by
construction reports the same zero as a queue nobody is working** — that distinction is the
point of this section.

## Diagnostics

**1. `build_step7_assertion_fired` and `build_findings_stranded` — RETRACTED, same run.**

At 09:44 UTC I observed two true things: `_run_summary.json` was stale, and its counts
disagreed with the built CSVs. From those I inferred that `errlog_step7.py`'s section-0
freshness assertion had *fired* and aborted the build's logging, and logged it `critical`,
naming specific lines of a specific file.

The scheduler settles it. `msp-family-guide-daily` fired **08:05:56Z**; this fixer fired
**09:43:58Z**; the build's STEP 7/8 then ran to completion at **12:24–12:28Z**
(`_findings.json` 12:24:28, `_run_summary.json` 12:27:27, `error_log.csv` appended 12:28:03
with 108 rows, published 12:28:13 as commit `338576bf`). STEP 7 had **not been reached** when
I read the marker. The assertion never fired; nothing was stranded. Verified after the build
completed: `_findings.json` holds 27 rows across 25 distinct `issue_type`s, and **zero** of
those 25 are absent from today's log.

**The generalisation, logged as `unobserved_mechanism_inference_check`:** a file that is stale
because a step *has not run yet* and a file that is stale because a step *rejected it* are
**byte-for-byte identical**. No amount of corroboration between the mtime and the counts adds
information, because both are downstream of the same unwritten file. What distinguishes them
is the scheduler's `lastRunAt` — one call, not made. CLAUDE.md's standing rule ("a zero is a
claim about the INPUT until you have shown the code path can still fire") applies unchanged to
a stale marker, and this project's own memory says in terms: *check lastRunAt before blaming a
missing run_summary*. Both were available; neither was consulted. **Rule: before attributing a
missing artifact to a guard, establish that the step owning that guard has RUN. Prefer
"artifact X absent as of HH:MM" — which is observed — over "guard Y fired", which is a claim
about code that did not execute.** The severity inflation is the compounding error: `critical`
on an inferred mechanism is louder than `info` on a true one.

**2. `fixer_gate_releases_midbuild` — the real root cause, logged as a `warning`.**

This task is described as completion-gated, waiting for the day's build/publish to finish. The
gate in fact releases on the **feed/CSV publish — STEP 6** — not on build completion. Measured
today: build published feed + CSVs 09:41:49–09:42:10Z, this fixer fired 09:43:58Z (108s
later), and the build did not finish until 12:28:13Z. **Overlap: 2h44m.** Three structural
consequences:

- The fixer's base `error_log.csv` necessarily **lacks the entire current day's build rows** —
  today it was missing all 108, so the queue was computed against a log one full day stale.
- Any freshness reading the fixer takes on `_run_summary.json` / `_findings.json` /
  `_image_backfill.json` mid-build is **structurally invalid**, because those markers are
  written at STEP 7 and are *expected* to be stale before it. That is the trap finding 1 fell
  into, and it will be there every run until the gate moves.
- The fixer's 12 rows survived **only because** `errlog_step7.py` appends to the same *local*
  file. Had the build re-read the published remote as its base, those rows would have been
  silently overwritten by the 12:28 publish.

**Today's outcome was benign and should not be read as safe.** Remedy: gate on the
`run_summary` row for *today* appearing in the published `error_log.csv` (the STEP 8 marker),
not on the feed/CSV commits — or move this task's schedule late enough to clear the build's
observed STEP 7/8 tail.

**3. STEP 4.5 ranks by row count, so umbrella pages outrank facility pages.** (Unaffected by
the retractions above; stands as logged.) `do_select` orders candidate sites by how many rows
reference them. The Chanhassen parks **index** page carries 2 rows and gets fetched — returning
`null`, as an index page must — while `.../lake-ann-park`, the facility-detail page that would
actually resolve queue item 1, carries 1 row and appears in **neither** the candidate list nor
the results file. Secondary defect: the umbrella was stored as `null` (meaning "no photo
today", so it is retried forever) rather than in `__rejected__` (meaning "this page will never
yield one"), unlike the structurally identical `alexandriamn.city/city-parks-trails/` and
`winonamn.gov/780/Outdoor-Recreation`, which are correctly ledgered. A page whose *kind*
guarantees no venue photo belongs in the ledger, not in the retry pool.

**4. `openverse_pagesize_probe_underread` — my own probe, again.** An Openverse query at
`page_size=50` returns **401**, and my handler swallowed it into `result_count: None`, which
reads exactly like a clean zero — "this search found nothing" rather than "this search never
ran". Diagnosed by re-issuing the request bare, outside the try/except, then re-run at
`page_size=20` with explicit paging. Same class as the `.get()`-on-a-dict-you-did-not-build
trap: **a probe that fails inside an exception handler returns a confident answer about data
it never saw.**

**5. The consecutive-zero counter was drifting in prose.** The 2026-09-20 report asserts
"twelfth consecutive run at zero"; the observable count on that date was **nine**. It was a
hand-maintained number in a sentence, which is this project's "prose is unasserted by
construction" rule landing on a report rather than on a log row. Today's figure — eleventh —
is derived from the log each run instead of incremented, which is the only form of it that
cannot drift.

**Publish-path note.** The first `error_log.csv` PUT **aborted with exit 2**: the remote had
moved off this run's base sha because the build published underneath at 12:28:13. That is the
optimistic-concurrency guard working as designed. Rather than re-applying and clobbering, I
inspected the new remote, found my 12 rows already present and preserved inside the build's
append, and re-based onto the new sha. The correction was then written as a **full rewrite**
guarded by a byte-identity control (round-trip the untouched file through the same
reader/writer and assert byte equality before writing), so "my edit changed 4 cells and added
2 rows" is distinguishable from "my writer rewrote every line."

## Files

| file | location |
|---|---|
| `error_log.csv` | https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv |
| `error-fixing-findings-latest.md` | https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md |
| local log | `Agents and Workflows/error_log.csv` |
| local report | `Agents and Workflows/error-fixing-findings-latest.md` |

Published log: **4,262 data rows**, 122 dated 2026-09-22 (12 written by this task, 108 by the
build, 2 by this correction), 4 carrying a resolution note. Blob
`a368656b90acdb06f8765610ce30cb0b086e1ab9`, commit `8b814ebdfc76`, size and sha verified
against the local bytes.
