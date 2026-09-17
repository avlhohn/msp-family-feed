# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-17 · **Finished:** 09:51 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

## Summary

Nineteen open rows were examined — six `unresolved_website` and thirteen `unresolved_image`, across
eighteen distinct items — and **none were resolved**. That is the ninth consecutive run at this exact
shape (19 rows / 18 items / 6 still live in the feed / 0 resolutions), and the shape itself remains
the finding: the queue is structurally blocked rather than under-worked. Twelve of the eighteen items
no longer exist in the published feed at all and are residue rather than active defects. Of the six
that still ship, five are settled negatives on first-hand evidence and the sixth needs the owner to
make a call that no amount of searching can make for it.

Two pieces of standing business closed cleanly. The lost-update escalation raised on 2026-09-16 —
opened because the build and this fixer dispatched one second apart and could each have clobbered the
other's write — is **verified CLEAR**. All seven of that run's fixer-authored rows are present in the
canonical log alongside the build's complete STEP 7 signal set for the same date (30 `ical_feed_pull`,
6 `deal_source_yield`, 1 `deal_source_non_table`, 3 `deal_source_retired`, 1 `image_backfill`, 1
`run_summary`), eighty rows for that date in total. Neither side lost anything; the optimistic-
concurrency PUT was sufficient and no repair was needed. And the scheduling that caused the scare has
returned to normal: `msp-family-guide-daily` ran at `2026-09-17T08:06:19Z` and this fixer at
`2026-09-17T09:40:20Z`, ninety-four minutes apart in the correct order. Yesterday's one-second
concurrent dispatch was a one-off late fire of both cron slots, not a standing defect. Today's run
therefore worked today's queue against today's feed — repo `pushed_at` 08:38:37Z, `generated_date:
2026-09-17`, counts 5252 / 849 / 150 / 268 / 460.

The run's one genuinely new finding is a confabulation shape this queue has not seen before, and it
is described under Diagnostics.

## Resolved this run

None — zero website resolutions and zero image resolutions (0 `og_image`, 0 `facebook`, 0
`stock_openverse_specific`). No website row produced a page specifically naming the exact venue and
city, and no image row produced a genuine Facebook photo, a deep-linked or self-branded `og:image`, or
a place-*specific* Openverse asset. Nothing was written in on partial evidence.

One candidate was deliberately held rather than shipped, and the reason is worth recording. A second
independent research pass surfaced the same Bump & Putt street address as the 2026-09-15 pass —
`29107 State Hwy 371, Pequot Lakes, MN 56472` — and it is still not written into the record. Both
passes read that address out of Yelp *search-result metadata* while the Yelp page itself returned 403
to our fetcher on both occasions. Two passes agreeing is not two sources agreeing when both are
reading the same snippet: agreement across passes measures the search index, not the world.

## Still open

All nineteen rows roll forward. Six items remain live in the published feed.

**Lake Ann Park (Chanhassen)** still has no usable image. The Openverse API was re-probed directly
today across six queries with a commercial-use licence filter, returning zero eligible assets. The two
hits for `Lake Ann Chanhassen Minnesota` are both the Eckankar temple — the same false positive this
queue has recorded since 2026-08-31 — and the four hits for `Chanhassen Minnesota park` are all Paisley
Park, Prince's studio, which is a collision on the word "Park" itself. This is consistent with 0 of 22
on 2026-08-21, -28 and -29 and 0 of 6 on 2026-09-10. The probe is cheap and the Creative Commons corpus
can grow, so it is worth repeating each run, but it has never yielded on this queue. The item is
licence-bound, not discovery-bound.

**Denny's, Perkins and Rubio's** are chain promotions with no single venue to photograph, which makes
them structurally unresolvable rather than merely unresolved. **Bowlero Brooklyn Park** remains a
settled negative: its imagery is brand-level Contentful assets shared across every location.

**Bump & Putt Family Fun Center** is the one that needs a human. Its record is wrong in four ways at
once. The website it actually ships — `https://www.brainerd.com/business/bump-n-putt-family-fun-park/`
— returns "Sorry! That page doesn't seem to exist" with no address, phone or hours, re-verified
first-hand today for the second consecutive run; so the feed is not missing a link, it is publishing a
dead one a family would click. Its address reads "Four miles north of Nisswa, MN", which can never
geocode. Its coordinate is a Nisswa city-centroid placeholder about 6.4 km from where that address
text points. And after eight research passes its operating status is still ambiguous. Unchanged across
fourteen runs. The single most promising untried route is
`fun4kidsmn.com/places/bump-n-putt-family-fun-park/`, which timed out for both the subagent and a
first-hand retry — recorded narrowly as a tooling or source-side timeout, explicitly **not** as
evidence that the listing lacks an address.

The remaining twelve items no longer appear in the feed at all, so two thirds of this queue is residue.
Fuzzy title matches were again not treated as evidence of presence. One observation worth carrying:
`Toddler Tuesday - ECFE` (Coon Rapids) fuzzy-matches a Winona row again, after the 2026-09-12 record
declared that collision gone because the Winona row had aged out. **A negative about feed *contents*
has a shelf life of one rolling window and must be re-derived**, unlike a negative about a source or a
licence, which is durable. `Movies in the Park - Mankato` matches Duluth and Osseo rows; same-state is
not a match. The `688 rows` item remains a roll-up label rather than a venue and is unworkable as
written.

## Diagnostics

**An eighth confabulation shape: a real source, correctly fetched and accurately quoted, about the
wrong business.** One research subagent was dispatched and its report was rejected on two independent
grounds. First it failed the cheap internal-consistency test adopted on 2026-09-16, returning
`VERIFIED` verdicts for two questions while its own evidence table marked the supporting Yelp URL
`FETCH FAILED (HTTP 403)`. Reading the report for self-contradiction *before* spending any verification
budget cost one re-read rather than a fetch, which is the whole point of that rule. Second, its single
substantive `FETCH OK` claim was verified first-hand and proved to be a `dl-online.com` article about
**Go-Putt-N-Bump in Detroit Lakes**, roughly 110 km northwest of Nisswa, published 2014-05-28 and
carrying no street address at all. Near-identical name, identical business type, both in a Minnesota
"lakes area" — considerably more seductive than the earlier wrong-state collisions. Every previous
instance on this queue was catchable by asking whether the source existed or whether it fetched; this
one is only catchable by asking whether the source names the **right entity in the right place**. Both
legs of the seasonality verdict are therefore void and Bump & Putt's operating status remains
ambiguous.

**The STEP 4.5 eligibility-gate gap, independently re-measured.** The 2026-09-16 reading carried a
caveat that it was arithmetic over the same artifact as 2026-09-15, because the build had not
republished in between. Today's feed is genuinely fresh, so the measurement is now independent. The
backfill gate admits `image_source` in `curated_category`, `stock`, `openverse_named` or blank, and
therefore **excludes** `curated`. Today there are 902 `curated` rows, of which 216 carry Pexels or
Unsplash stock imagery, of which 146 also carry a website — rows sitting on stock photos, holding the
one input the backfill needs, and structurally unreachable by the pass built to drain them. Against
yesterday's 222 / 152, the gap is real and slowly shrinking rather than converged. Those 216 rows share
only 36 distinct stock assets, an image monoculture inside the curated class. For scale, 4,114 in-gate
rows carry a website across 4,006 distinct sites, so STEP 4.5 is budget-bound and drains gradually.
Both of this queue's non-chain live image items — Bowlero Brooklyn Park and Bump & Putt — are
`image_source=curated` and thus out of gate entirely; no number of fixer runs closes them by that
route.

**Base integrity.** No `log_base_rejected` condition arose: the header is schema-exact at ten columns,
the row count was 3,799 and monotonic up from 3,719, and the local base was proven byte-identical to
the GitHub canonical by locally computed git blob SHA-1 (`ba3738fb0aa2…`) rather than by size. The
contents API returns empty content for files over 1 MB, so that local computation replaced a
re-download entirely. No `no_run_summary_today` condition: today's marker was present. Before
appending, the untouched file was round-tripped through the CSV reader and writer and asserted
byte-identical across all 3,800 lines, so "nine rows appended" is distinguishable from "the writer
silently rewrote every line"; a prefix assertion then proved not one carried byte was altered; and a
double-append guard confirmed no fixer rows already existed for today. All four guards fire before the
write, which is what made the first attempt safe — it aborted on a row-arity assertion and left the log
untouched, rather than leaving a partial append for a retry to duplicate.

**Publish.** `error_log.csv` went from 3,799 to 3,808 data rows and 1,209,230 to 1,217,782 bytes, with
all 536 previously-resolved rows preserved. It was published with optimistic concurrency, carrying the
`sha` read immediately beforehand so a conflicting build write would return 409 rather than clobber,
and verified on the first attempt: the returned size matched local exactly and the returned `sha`
equalled the locally computed blob `9c50ab9044952a49c671247fee0b78109fc542b8`.

## Files

- `error_log.csv` — https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
  (local: `Agents and Workflows/error_log.csv`)
- `error-fixing-findings-latest.md` — https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
  (local: `Agents and Workflows/error-fixing-findings-latest.md`)
