# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-26 · **Finished:** 10:12 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement* by
up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `89ad9c463902` — 1,477,247 bytes, 4,529 data rows, 10-column
header exact, CRLF 4,530 and bare LF 0, and **byte-identical to the GitHub remote**
(md5 `29b2c7517794178b4e2540d2dab1c917`), so its provenance is verified rather than assumed. That
blob is precisely what the 2026-09-25 run published, so the chain is continuous with no intervening
edit. **Published log:** blob `38ee1d6c726c`, 1,484,234 bytes, 4,535 data rows, CRLF 4,536 and bare
LF 0, confirmed by re-GET.

One reconciliation note, since it would otherwise read as a regression: last run's report described
its published log as "4,530 data rows" while also reporting CRLF 4,530 with bare LF 0. Those two are
only consistent if the 4,530 counted the header line, i.e. 4,529 data rows — which is exactly what
this run measured as its base. There is no missing row.

## Summary

The open-issue queue held **6 rows across 6 distinct items** (5 `unresolved_image`, 1
`unresolved_website`, dated 2026-07-08 to 2026-08-15), unchanged from last run. Every one is shipped
in the live feed and every one was re-attempted first-hand this run.

**None met the verification bar, so none were marked resolved.**

| | |
|---|---|
| Open rows examined | 6 (5 `unresolved_image`, 1 `unresolved_website`) |
| Resolved this run | **0** |
| — website | 0 |
| — image by `og_image` | 0 |
| — image by `facebook` | 0 |
| — image by `stock_openverse_specific` | 0 |
| Left open | **6** |
| Rows appended to the log | 6 (diagnostics + escalations + summary; no existing row touched) |

This is roughly the fifteenth consecutive zero-resolution run, and the important point is that **it
is not a clean queue**. Two separate things produce the zero, and they need different fixes.

First, the six rows that *are* in the queue are largely unresolvable as written. Three of the five
image rows carry the address `Multiple Twin Cities locations` with blank coordinates, so a
*place-specific* photograph cannot exist for them **by construction** — there is no single place to
photograph. The other two were probed directly and the corpus genuinely has nothing.

Second, and larger: **the queue has no inflow.** The last row of either queue type was written 41 and
65 days ago, while roughly 590 fixer-shaped rows sit in the log under `issue_type` values this task
does not match. A drained queue and a queue nothing writes to look identical from inside the queue.
That is the finding this run is actually reporting, and it is recorded rather than worked around.

Every Openverse query was issued **by the parent process**, not delegated, and every one returned
**HTTP 200**. That distinction is load-bearing: subagents here are WebFetch-only and WebFetch cannot
reach the Openverse API, so an image negative inherited from a subagent may be a search that never
ran. These eight negatives are measurements, not silences.

The single `unresolved_website` row stays open, but the run still advanced it — its dead URL was
re-verified and the venue's correct name, address and phone were established and escalated.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| _(none)_ | — | No row met the confidence bar this run. |

Nothing was resolved, deliberately. The one candidate for the skill's "confirmed closed / no site"
path is an **operating business**, and that clause is conditioned on a positively confirmed permanent
closure. Closing the row on a partial negative would also have removed the only artifact that
currently surfaces a dead URL still shipping in the feed — burying the defect rather than fixing it.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | `unresolved_image` | Openverse returned **0** candidates at HTTP 200 — a real search that found nothing, not a failed call. A small municipal park with no freely-licensed photograph in the corpus. A previous negative on this item was retracted once before, so it was re-probed rather than inherited. |
| Denny's Thursday Kids Eat Free | `unresolved_image` | **Impossible by construction** — address is `Multiple Twin Cities locations`, lat/lon blank. Openverse returned 48 hits, all failing the bar: a jazz quartet and a funeral, i.e. wrong identity *and* wrong subject. |
| Perkins Tuesday Kids Eat Free | `unresolved_image` | **Impossible by construction** (multi-location row, blank coordinates). 2 Openverse hits, both plates of food in Roseville — right geography, wrong subject. A photograph of a meal is not a photograph of a venue. |
| Rubio's Rewards Thursday Kids Free Meal | `unresolved_image` | **Impossible by construction** (multi-location row). 2 Openverse hits, both **Miami, Florida** — fails geography outright. |
| Bowlero Brooklyn Park (Lucky Strike) | `unresolved_image` | Openverse **0** candidates. New first-hand finding this run: the venue's own page (`luckystrikeent.com`, reached via a 301 from `bowlero.com`) carries only chain-wide brand marketing photography, not documentation of this location — so the site cannot supply a `site_photo` either. Rejected on the same reasoning that rejects a tourism-board hero banner. |
| Bump & Putt Family Fun Center | `unresolved_website` | No replacement URL found that names this venue. The shipped `brainerd.com` URL re-verified **404** today. Four candidate sources failed in transport this run (HTTP 500, HTTP 526, HTTP 403, and one 60 s timeout), so the negative is **incomplete on transport grounds** rather than settled — a transport failure is a property of the moment, not of the page. Escalated with corrected details instead; see Diagnostics. |

All 6 rows shown; none omitted.

## Diagnostics

**Base log validated before use.** Exact 10-column header, 4,529 data rows all of width 10, CRLF
4,530 / bare LF 0, 554 rows carrying a `resolved_date`, 69 distinct run dates spanning 2026-07-08 →
2026-09-25, and byte-identical to the GitHub canonical copy. No `log_base_rejected` was owed.

**Soft freshness check FIRED, and is logged as `info` per the skill.** No `run_summary` row dated
2026-09-26 was present, there was no 2026-09-26 commit, and the repo's own `pushed_at` read
`2026-09-25T10:04:58Z` — while local build artifacts for today *did* exist (`_feedpull_all.json`
03:57, `add_step2.py` 04:37). Today's build therefore ran locally and had not published when this
task started: the documented build/fixer race, in which the gate releases on the build's *publish*
rather than on its completion. Proceeded anyway, as mandated.

One caveat for whoever reads this next: `pushed_at` now reads `2026-09-26T10:11:45Z`, which is **this
task's own push**. That corroboration is no longer independently checkable after the fact — the
evidence was captured in the appended log row *before* the push overwrote it.

**The 2026-09-25 build published its CSVs and logged NOTHING.** Commit `66a3690805` ("Daily refresh
2026-09-25: 6377 rows") landed, yet `error_log.csv` carries **zero** rows dated 2026-09-25 — against
150 rows on 09-23 and 115 on 09-24. That is the STEP 7 blast-radius shape: a fail-closed freshness
assertion on the *logging* step suppresses an entire run's evidence in order to prevent one stale
row, so the artifacts publish correctly and nothing records that the run happened. Logged as a
`warning` for the build's owner. The likely site is `errlog_step7.py` exiting non-zero on a
section-0 assertion before `open(LOG,"a")`.

**The fixer queue has no inflow — this is the substantive finding.** The last `unresolved_website`
row was written **41 days** ago (2026-08-16); the last `unresolved_image` row **65 days** ago
(2026-07-23). Only 319 rows carrying either type exist across the log's entire history. Meanwhile
roughly **590 fixer-shaped rows are structurally unreachable** by this task because they were written
under other `issue_type` values: `missing_website` (300), `generic_image` (240),
`attempted_no_photo` (26), `curated_bad_url` (24). STEP 2 matches two literal strings, so the two
vocabularies have drifted apart with nothing enforcing agreement — the same registry-drift shape this
project has hit repeatedly, here between a *writer* and a *reader* of the same field.

**Deliberately not fixed by widening the selector.** Doing so would drain a 590-row backlog in a
single run while burying the drift that caused it, and would silently change what this task is for.
Reconciling the two vocabularies — at the writer, or by an explicit alias table — is the owner's call.

**Escalation — Bump & Putt Family Fun Center.** The shipped URL
`https://www.brainerd.com/business/bump-n-putt-family-fun-park/` returned **HTTP 404** again today
("Sorry! That page doesn't seem to exist."), as it has for roughly fifteen consecutive runs. The
venue is *operating*, not closed. Corrected details, corroborated two independent ways — a directory
read and a separate parent-side search keyed on the phone number: **Bump 'N' Putt Family Fun Park,
29107 State Hwy 371, Pequot Lakes, MN 56472, (218) 568-8833**, with a listing updated as recently as
August 2026. Not confirmable on the venue's own page, because no venue-owned page was found, so this
is escalated for a human to confirm rather than written into the feed.

`goputtnbump.com` was explicitly **rejected** and is recorded here as a near-miss so it is not
"found" again next run: that is Go-Putt-N-Bump in **Detroit Lakes**, roughly 180 km away, and itself
listed as closed since July 2026. Resolving to it would have been a match on name similarity alone.

**Escalation — Bowlero Brooklyn Park (Lucky Strike).** `bowlero.com` now **301**s to
`luckystrikeent.com`; the venue trades as **Lucky Strike Brooklyn Park**, 7545 Brooklyn Blvd,
Brooklyn Park, MN **55443**, 763-503-2695. The feed still ships ZIP **55445**. This rebrand has been
evidenced in the log for 23+ days and remains unshipped, which is the standing "resolutions have no
consumer" defect: nothing reads resolved rows back into `_compiled_work.json` before the build, so
resolving a row produces a note, not a fix. Worth stating plainly, because it bounds what this task
can achieve at all.

**Image method.** All 8 Openverse queries were issued by the parent and every one returned **HTTP
200**, so each zero is a claim about the corpus rather than about the client. Candidates were judged
on three tests together — **venue identity, geography, and subject** — and failing any one is a
rejection.

**Integrity of this run's write.** Six rows were appended and **no existing row was touched**. A
byte-identity control confirmed the untouched rows round-trip identically to the original before
anything was appended; post-write assertions confirmed rows carrying a `resolved_date` unchanged at
**554** and the open queue unchanged at **6**. Data rows 4,529 → **4,535**; bare LF **0**. Neither
appended row uses a reserved `issue_type` (`ical_feed_pull`, `run_summary`, `image_backfill`, or
anything prefixed `deal_source_`), so the build's STEP 7 signal assertions are unaffected. The
publish returned **HTTP 200** — an update to a sanctioned path, not a 201 create — with the blob
`sha` moving `89ad9c46…` → `38ee1d6c…` and remote size matching local bytes exactly at 1,484,234.

## Files

- `https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv`
- `https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md`

Local copies: `Agents and Workflows/error_log.csv` and
`Agents and Workflows/error-fixing-findings-latest.md`.
