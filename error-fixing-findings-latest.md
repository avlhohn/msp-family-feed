# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-25 · **Finished:** 09:57 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `80113fb08365` — 1,474,523 bytes, 4,528 data rows, 10-column
header exact, and **byte-identical to the GitHub remote**, so its provenance is verified rather than
assumed. **Published log:** blob `89ad9c463902`, 1,477,247 bytes, 4,530 data rows, CRLF 4,530 and
bare LF 0, confirmed by re-GET.

## Summary

The open-issue queue held **6 rows across 6 distinct items** (5 `unresolved_image`, 1
`unresolved_website`, dated 2026-07-08 to 2026-08-15) — down from 19 last run, because the
2026-09-23 run closed 13 items that had no row in any published artifact. What remains is the
residue: every one of these six *is* shipped in the feed, and every one was re-attempted first-hand
this run.

**None met the verification bar, so none were marked resolved.**

| | |
|---|---|
| Open rows examined | 6 (5 `unresolved_image`, 1 `unresolved_website`) |
| Resolved this run | **0** |
| — by `og_image` | 0 |
| — by `facebook` | 0 |
| — by `stock_openverse_specific` | 0 |
| — website URLs accepted | 0 |
| Left open | 6 |
| Rows appended | 2 (both `info`/`pipeline` diagnostics) |

A zero here is a claim about the sources, not about the effort — and it is a *newly measured* claim,
not an inherited one. The Openverse half was queried by the parent over the API, because WebFetch
cannot reach `api.openverse.org` and a subagent's Openverse verdict is therefore inadmissible; the
page half was fetched by subagents and re-checked by the parent wherever a result would have been
written. Three of the six are additionally **impossible by construction** rather than merely
unfound, which is a different and more useful verdict.

## Resolved this run

None. No row received a `resolved_date`, `resolved_by` or `resolution_note` value.

Writing a resolution that does not clear the bar is worse than leaving the row open: an
`image_source` in the `og_image`/`facebook`/`site_photo` family is treated as final by every later
enrichment layer and never self-heals, so a wrong accept is permanent. The two candidates that came
closest are recorded under Diagnostics with the reason each was rejected.

## Still open

**Lake Ann Park** — `unresolved_image`, `parks`, open since 2026-07-08.
The City of Chanhassen park page returns **403** to WebFetch; the park's Facebook presence loads but
renders no images; Openverse returns **0** for `Lake Ann Park Chanhassen`, and the 2 hits for
`Lake Ann Park Minnesota` depict a different place. A broader `Chanhassen Minnesota park` query
returns 57 hits, all rejected — a photo of *a* park in the city is not a photo of *this* park.
Geography is not depiction; a candidate must pass venue identity, geography **and** subject.

**Denny's Thursday Kids Eat Free** — `unresolved_image`, `meal_deals`, open since 2026-07-23.
The corporate site returned **403** on three separate attempts. More decisive than the 403: the
row's address is *"Multiple Twin Cities locations"*, and a row denoting no single place cannot carry
a place-specific photo **by construction**. Re-attempting it nightly cannot succeed.

**Perkins Tuesday Kids Eat Free** — `unresolved_image`, `meal_deals`, open since 2026-07-23.
One timeout and two **403**s. Same multi-location construction. Openverse's nearest hits for this
brand in Minnesota are two plates of food in Roseville — right brand, right state, wrong subject.

**Rubio's Rewards Thursday Kids Free Meal** — `unresolved_image`, `meal_deals`, open since
2026-07-23. The site fetched **200**, but WebFetch strips the `<head>`, so no `og:image` is
reachable within policy. Same multi-location construction. The only Openverse storefront hit for
this brand is in **Florida**.

**Bowlero Brooklyn Park (Lucky Strike)** — `unresolved_image`, `restaurants`, open since 2026-07-23.
The venue page now serves chain marketing imagery carrying no location-specific photograph.
Openverse returns **0** for both `Lucky Strike Brooklyn Park` and `Bowlero Brooklyn Park Minnesota`.
One external candidate was surfaced and rejected — see Diagnostics.

**Bump & Putt Family Fun Center** — `unresolved_website`, `restaurants`, open since 2026-08-15.
The shipped `website` (`brainerd.com/…`) returns **404**, verified by the parent this run for the
**fifth consecutive run**, and it is still live in the feed. No owned domain could be located, and
every directory carrying the business is blocked to this agent (Yelp 403, Manta 403, ABLocal 526,
fun4kids timeout). No URL could be accepted without fabricating or approximating one, which the
verification bar forbids.

## Diagnostics

**Today's build published its artifacts but never published `error_log.csv`.** Repo commits at
2026-09-25T09:00:42Z–09:01:03Z carry the daily refresh (*"6377 rows (events 4659, parks 849,
deals 140…)"*), yet the newest `error_log.csv` commit is `6862a9fc94` at **2026-09-24T14:18:15Z**,
and **zero** rows in the base carry `run_date` 2026-09-25. The build produced seven correct
artifacts and recorded nothing about itself. This is the fail-closed-guard blast-radius class
already documented on 2026-09-22: a hard failure at the logging step suppresses the *entire* run's
evidence — the feed-pull rows, deal-yield rows, image-backfill marker, coverage rows and all
findings — in order to prevent one stale row. Logged this run as an `info`/`pipeline` row
`no_run_summary_today`; the fixer proceeded on the 2026-09-24 base per the spec's soft-freshness
branch.

**A subagent's conditional accept was rejected on verification.** For Bowlero/Lucky Strike a
subagent surfaced Flickr photo `40926549203`, titled "Bowlero" and credited to the Brooklyn Park
EDA, and asked for confirmation. The parent fetched the Flickr page: **All Rights Reserved**, not
CC-licensed. Three independent grounds to reject — not CC-licensed, Flickr is not one of the three
permitted `image_source` tokens, and the subject was never visually verified as this venue. It also
corroborates the parent's own Openverse zero, since Openverse indexes CC-licensed Flickr and a CC
photo titled "Bowlero" would have surfaced there. **A subagent's conditional accept is a candidate,
not a result** — as is its rejection.

**A snippet-sourced address was held, not written.** A subagent reported
`29107 State Highway 371, Pequot Lakes, MN 56472` and `(218) 568-8833` for Bump & Putt as
corroborated, while **every page it cited was unfetchable** (403/526/timeout). Corroboration
assembled from search snippets is not a source. Held as an unverified lead and deliberately not
written, and recorded here so a later run re-opens it from a fetched page rather than re-deriving it
from the same snippets.

**Openverse was queried by the parent, over the API, as the architecture requires.** Eight terms.
The specific ones returned zero — `Lake Ann Park Chanhassen` 0, `Lucky Strike Brooklyn Park` 0,
`Bowlero Brooklyn Park Minnesota` 0, `Bump and Putt Nisswa` 0, `Nisswa Minnesota mini golf` 0 — and
the broad ones returned hits failing the identity or subject test. Subagents are WebFetch-only and
WebFetch cannot reach `api.openverse.org`, so an Openverse negative arriving from a subagent is
indistinguishable from a search that never ran.

**Three of the six rows are unresolvable by construction, not by difficulty.** Denny's, Perkins and
Rubio's all carry the address *"Multiple Twin Cities locations"*. A row that denotes no single place
cannot have a place-specific photograph, so re-attempting them nightly spends budget on an
impossibility and inflates the open-queue count with items no research can close. Routing
multi-location rows out of the image queue is a queue-design fix and the owner's call; noted here
rather than acted on.

**The standing structural finding is unchanged and still bounds what this task can achieve.** A
resolution written to `error_log.csv` has **no consumer** — nothing reads resolved rows back into
`_compiled_work.json` before the build — so even a resolved row would not correct the live feed. The
Bump & Putt 404 is the running proof: correctly logged for five consecutive runs and still shipped.
The missing piece is a pass that applies resolved `website`/`image_url` values to the compiled work
file. Until it exists, "resolve more rows" is not the improvement it looks like.

**Base and publish integrity.** Local base and remote were byte-identical at STEP 1, so no
local-vs-remote direction question arose. A byte-identity round-trip control was run before any
rewrite and passed, which is what distinguishes "two rows were appended" from "the writer silently
rewrote every line." The publish was a PUT **200** — an update to a sanctioned path, not a 201
create — and was verified by blob SHA-1 on re-GET rather than by size.

## Files

| File | State |
|---|---|
| `error_log.csv` | published, blob `89ad9c463902109345499631b5833462d2e728ab`, 1,477,247 bytes, 4,530 rows, 4,530 CRLF / 0 bare LF — verified by re-GET |
| `error-fixing-findings-latest.md` | this report |
| pre-edit backup | `error_log.pre.csv`, blob `80113fb0836523a463959852673760d85f7d5ce8` |

Category CSVs and the feed JSON were **not** touched — out of scope for this task.
