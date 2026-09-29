# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-29 · **Finished:** 12:56 UTC (server-derived; weekday Tuesday cross-checks the date)

## Summary

The open queue held **5 rows / 5 distinct items** — 4 `unresolved_image`, 1 `unresolved_website`.
**0 were resolved.** All five roll forward, and every one of them was re-verified first-hand this run
rather than being carried on a previous run's negative.

That zero is a claim about the sources, not a claim that nothing was attempted. The queue now consists
entirely of items whose negatives have been settled and re-settled across many runs, so the useful work
was not another cold sweep — it was re-testing only those routes whose negatives can *expire*:

- **Feed presence** for all 5 items (a row absent from the published feed needs no image at all). All
  five are still live in the 5 published CSVs, 5,921 rows total — so that route is unavailable.
- **8 parent-side Openverse queries.** Openverse is reachable only from the parent process: subagents
  are WebFetch-only and WebFetch 403s that API, which means *every* subagent image negative on record
  is a tool artifact rather than a source negative. All 8 queries returned HTTP 200, so these are
  genuine source negatives for the first time.
- **3 first-hand page fetches** of the shipped URLs.

Four rows were appended to `error_log.csv`; the 4,779 carried rows are byte-identical and all 555
previously-resolved rows are untouched.

## Resolved this run

None this run.

## Still open

**Lake Ann Park** (`unresolved_image`, parks, open since 2026-07-08)
The city's deep link 403s today. Openverse returned 0 results. Roughly 36 candidate routes have now
been closed across prior runs, and what remains is licence-bound third-party rehosting, which the
acceptance bar excludes. Note the earlier "no photo exists" negative on this item was **retracted** on
a prior run — photos do exist, they are just not usable under the licence rule.

**Denny's Thursday Kids Eat Free** and **Rubio's Rewards Thursday Kids Free Meal**
(`unresolved_image`, meal_deals, open since 2026-07-23)
These are **unresolvable by construction**, not by exhaustion. Both items are multi-location chain
*promotions* rather than places, so there is no venue whose photo would be correct. Openverse
illustrates the hazard directly: the Denny's query returns a George Floyd protest photo and the Rubio's
query a Florida storefront. Both pass a naive keyword match and both fail the venue-identity +
geography + subject test. These belong in a permanent-exclusion list rather than a nightly retry queue.

**Bowlero Brooklyn Park (Lucky Strike)** (`unresolved_image`, restaurants, open since 2026-07-23)
The venue's own page returns 200, but all five body images are chain-wide Contentful CDN stock served
identically across locations — the recurring-image trap. Openverse returned 0. Separately, this venue
was re-branded Bowlero → Lucky Strike and that was evidenced **23 days ago and is still unshipped**,
which is the more significant defect here.

**Bump & Putt Family Fun Center** (`unresolved_website`, restaurants, open since 2026-08-15)
Approximately the 15th consecutive `NO_SITE_FOUND`. The shipped URL is dead and no replacement exists.
This row is deliberately **not** closed as "confirmed closed": the open row is currently the only thing
keeping the shipped 404 visible, so resolving it would hide a live defect in the feed.

## Diagnostics

**The build/fixer race recurred, and this was its most extreme instance — 4th on record.** The nightly
build's `lastRunAt` was 12:41:11Z and this fixer's 12:41:27Z: **16 seconds apart**. The gate intended to
serialise them did not hold at all. The absence of today's `run_summary` marker is *explained* by this
concurrency rather than indicating a failed build — a distinction worth stating because inferring
"the build failed" from a missing marker is a mistake made on 2026-09-25, and checking `lastRunAt`
before rating severity is what avoided repeating it. Publish safety was then established empirically
rather than assumed: yesterday the fixer published at 12:59 and the build at 13:51, and all 10 fixer
rows survived, which shows the build re-reads the log at its STEP 7. The remote sha was also re-read
immediately before the PUT and was unchanged, so the precondition held and the build's rows cannot have
been destroyed.

**9th subagent confabulation.** A subagent's OPERATING STATUS block for Bump & Putt quoted a Yelp
update date, a street address and a phone number drawn from a URL its *own* fetch table marked
`FAILED 403` — the same self-contradiction shape as the documented 7th instance. It was caught by a
free internal-consistency re-read of the report before any verification budget was spent. The
`NO_SITE_FOUND` verdict was kept, the fabricated evidence discarded, and the unverified address was
**not** written. The `goputtnbump.com` decoy was avoided by briefing the subagent on it by name, and it
correctly identified it as the decoy.

**Image-precision concern logged, not acted on.** Yesterday's single resolution — the only one in
roughly 15 runs — used a photo of a *dish* for Perkins Tuesday Kids Eat Free, a candidate shape
previously rejected on the subject test. It is flagged here and in the log for adjudication. The
resolved row was **not** modified, since editing resolution history is outside this task's scope.

**The >1MB contents-API trap re-confirmed.** The contents API returned `content: ""` for
`error_log.csv` again. Content was read via `raw.githubusercontent.com` and the read was *proven* not
to be CDN-stale by computing the local blob SHA-1 and matching it against the contents-API `sha` field.

## Files

- `error_log.csv` — https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
  4,783 rows (4,779 carried byte-identical + 4 appended). Published blob sha
  `dae48f2a06e87a502529878df9f0e50095ac13e8`, 1,574,930 b, commit `15a1906`.
- `error-fixing-findings-latest.md` — https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
- Local copy: `error_log.csv` in the Agents and Workflows folder.
