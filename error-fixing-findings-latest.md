# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-27 · **Finished:** ~09:55 UTC

Run date derived from the GitHub API `Date` response header (`Sun, 27 Sep 2026 09:44:39 GMT`), with the weekday cross-checked against the date — not taken from the sandbox clock, which has previously been wrong *in agreement* with the injected `currentDate` by up to two days.

**Base log:** `error_log.csv` at blob `e9be7c0ba5b73fecc95cec1f94180adc357b0ed9` — 1,515,093 bytes, 4,643 data rows, 10-column header exact, CRLF 4,644 / bare LF 0, and **byte-identical to the GitHub remote**, so no fixer-vs-build divergence existed and nothing was at risk of being overwritten. **Published log:** blob `bb8b12534284515ffedcae2e6ddd4834c4cf17cb`, 1,517,742 bytes, 4,644 data rows, confirmed by re-GET.

## Summary

Open queue at start: **6 rows / 6 distinct items** — no de-duplication collapse, no cap applied.

- `unresolved_website` — 1
- `unresolved_image` — 5

Resolved this run: **0** — website 0; image 0 (og_image 0, facebook 0, stock_openverse_specific 0).

Left open, rolling to tomorrow: **6**, all aged 2026-07-08 to 2026-08-16. Every item was re-attempted this run and none met the verification bar. All six are genuinely shipped in the live feed (confirmed by reading `meal_deals.csv`, `restaurants.csv` and `parks.csv` from the published repo), so none is a phantom row.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Denny's Thursday Kids Eat Free | unresolved_image | **Impossible by construction** — live `meal_deals.csv` gives the address as `Multiple Twin Cities locations`. A row denoting no single place cannot carry a place-specific photograph. |
| Perkins Tuesday Kids Eat Free | unresolved_image | Impossible by construction — same `Multiple Twin Cities locations` address, re-verified against the live feed this run. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | Impossible by construction — same `Multiple Twin Cities locations` address, re-verified against the live feed this run. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Only generic/recurring stock available — **new first-hand evidence this run**, see below. |
| Lake Ann Park | unresolved_image | No specific image found. Chanhassen city page still 403s to WebFetch; the park's Facebook page 200s but renders no extractable images; Openverse returns 0. |
| Bump & Putt Family Fun Center | unresolved_website | No site exists that can be evidenced. No official domain resolves and no candidate page could be fetched. |

### Where the picture changed this run

**Bowlero Brooklyn Park (Lucky Strike) — now a settled negative with a stated mechanism.** The venue's own deep link (`luckystrikeent.com/location/lucky-strike-brooklyn-park`) was fetched directly by the parent and returns 200. It carries eight body images and every one is brand-wide stock served from a shared Contentful CDN (`images.ctfassets.net`) — a child blowing out birthday candles, generic lanes-and-drinks shots, an AMF food spread — reused across all Lucky Strike locations. That is exactly the recurring-image trap, so the row is *disqualified* rather than merely unprobed. This matters because it converts the row from "not yet properly attempted" into a negative with a reason, so future runs stop re-spending budget on it. The previously noted Flickr photo `40926549203` remains All Rights Reserved and unusable on licensing grounds alone.

**Bump & Putt Family Fun Center — no website exists, and the one the feed ships is dead.** Both plausible domains (`bumpnputt.com`, `bumpandputt.com`) refuse connection. Every directory page that might carry a website field was unfetchable: Yelp 403, Manta 403, Nextdoor 404, ABLocal 526, Fun4Kids timeout. The business appears active in search snippets, but **snippets are not a source** — no fetched page supports either an official URL or a closure, so the row correctly stays open rather than being closed as "confirmed closed". Separately confirmed first-hand this run: the website the feed currently ships, `brainerd.com/business/bump-n-putt-family-fun-park/`, returns a **404** ("Sorry! That page doesn't seem to exist"). Sixth consecutive run verified.

### On the Openverse zeros

Openverse was queried **parent-side, directly against the API**, for every image item — `Lake Ann Park Chanhassen`, `Lake Ann Park Minnesota`, `Lucky Strike Brooklyn Park`, `Bowlero Brooklyn Park`, and both Bump & Putt spellings. All returned 0 results. Because a zero from this API has previously been a client-side artifact rather than a real absence, three control queries were run on the same code path: `Minnehaha Falls`, `Como Park Zoo` and `Chanhassen Minnesota` each returned 240 results. The path demonstrably fires, so these zeros are genuine negatives rather than searches that never ran.

## Diagnostics

- `log_base_rejected` — **not triggered.** The base passed both checks: header exactly the 10-column schema, and 4,643 rows, consistent with recent growth rather than a collapse.
- `no_run_summary_today` — **not triggered.** The build's end-of-run marker for 2026-09-27 is present, so the queue is current.
- **Two-writer check — clean.** Local base and remote were byte-identical, so publishing over the remote could not erase fixer work. Checked via the git trees/blobs API, not the contents API, which returns empty content for files over 1 MB.
- **Publish** — log and findings both committed on the first attempt, each verified by byte size and by a changed blob SHA-1. No retries.
- **No prior row was modified.** The published file is the base bytes plus one appended row — verified as a strict byte prefix, which proves all 554 previously resolved rows are untouched.

### The queue's inflow is dead — the significant finding this run

The log holds **4,089 unresolved rows, of which only 6 are reachable** by this task's queue definition (`issue_type` in `unresolved_website` / `unresolved_image`). The build has emitted no new `unresolved_website` row since **2026-08-16 (42 days)** and no new `unresolved_image` since **2026-07-23 (66 days)**.

Meanwhile the build is writing large volumes of rows that are semantically exactly this task's work, under different names:

| issue_type | unresolved rows |
|---|---|
| `missing_website` | 300 |
| `generic_image` | 240 |
| `attempted_no_photo` | 26 |
| `curated_bad_url` | 24 |

So roughly **590 fixer-shaped rows sit permanently out of reach** while this task reports a 6-item queue and a clean drain. The small queue is not evidence of a healthy backlog — it is evidence that the intake stopped matching the filter. A queue that only ever shrinks because nothing can enter it looks identical, from the summary line, to one that is being worked down.

Also noted: `unresolved_geocode` (386 unresolved) and `geocode_unresolved` (43) are two spellings of one concept — registry drift that will split any future count of that class.

**Deliberately not fixed in-run.** Widening the queue definition changes what this task is scoped to do and would multiply its workload by roughly 100×; that is a task-spec decision and the owner's call, not something to reshape minutes before publish.

These diagnostics were **not** re-logged as new `error_log.csv` rows. Prior runs already logged `fixer_queue_inflow_check` and `shipped_website_404`, and appending them again every night produces a permanent warning — which trains the reader to skim the block and is worse than no warning at all. They are folded into this run's `fixer_summary` row and stated here instead, in a file that overwrites in place so nothing accumulates.

### Standing structural note

A resolution written to `error_log.csv` still has **no consumer**. Nothing reads resolved rows back into `_compiled_work.json` before the build, so even a correctly resolved row would not correct the live feed. Bowlero → Lucky Strike was fully evidenced on 2026-08-28 and the feed still ships the old `bowlero.com` URL a month later; Bump & Putt's 404 has been logged correctly six runs running and never applied. Until a pass exists that applies resolved rows to the feed, **"resolve more rows" is not the improvement** — a resolution is a note, not a fix.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
