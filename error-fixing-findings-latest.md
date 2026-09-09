# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-09**, finished 04:49 US Central (09:49 UTC). Run date derived from the GitHub API `Date` response header, not the sandbox clock.

## Summary

Open queue at start: **20 rows / 19 distinct items** — 14 `unresolved_image`, 6 `unresolved_website`. One of the 19 (`688 rows`) is an aggregate roll-up the build writes, not a fixable item, so the real work list was 18.

Resolved this run: **0** (website 0; image 0 — og_image 0, facebook 0, site_photo 0, stock_openverse_specific 0).

Left open: **20**, rolling to tomorrow. Zero regressions — all 3,057 carried rows were preserved byte-identically and one `fixer_summary` row was appended.

A zero-resolution run is the correct outcome here rather than a failure to try. The queue was scoped by first cross-checking every open item against the published feed, then asking which items still have an *untried* route; the two that did were probed and both closed as new settled negatives. The remaining image items are blocked by image **licensing**, not by discovery, so more searching is the wrong spend — a diagnosis now confirmed on a third consecutive run. Lowering the bar to move the number would put a wrong or all-rights-reserved photo into a published family feed.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Denny's Thursday Kids Eat Free | image | **New settled negative.** `dennys.com` 403s the page-body route as well as og:image; MN Yelp pages 403; the only Facebook asset is a chain-wide brand graphic that fails the recurrence test. It is a promotion, not a venue — no specific photo exists. |
| Perkins Tuesday Kids Eat Free | image | **New settled negative.** `perkins.com` times out; `stores.perkinsrestaurants.com` MN location pages 403; `eatatperkins.com` carries only chain-wide menu product shots that recur on ND/KS/FL siblings. |
| Lake Ann Park | image | Licence-bound. Every real photograph found across 10+ routes was rejected on licence, none on absence. `chanhassenmn.gov`, the `chanrec.com` alias and `carvercountymn.gov` all hard-403. |
| Cameron Park (Bemidji) | image | Licence-bound. `visitbemidji.com` venue page returns 200 with zero images; the city runs RecDesk (org-not-found), not CivicPlus; the one genuine photo is an all-rights-reserved newspaper staff image. |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled negative on hard evidence — all six location-page images are Contentful brand assets appearing identically on the Blaine MN and Lakeville MN sibling pages. |
| Rubio's Rewards Thursday Kids Free Meal | image | Bad seed — see Escalations. No image should be sought for a row that should not exist. |
| Bump & Putt Family Fun Center | website | No first-party site exists (8th confirmation). Deliberately kept open as the defect marker for the dead link it ships — see Escalations. |
| Maplewood Celebrate Summer | image | Aged out of the feed. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of the feed. |
| Music in the Park Thursdays - Mankato | image | Aged out of the feed. |
| Movies in the Park - Mankato | image | Aged out of the feed (prior "present" verdicts were false fuzzy hits on Minnetonka / White Bear Township / Duluth screenings). |
| Moorhead Summer Splash Event | image | Aged out of the feed. |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out of the feed (umbrella row; only per-location rows remain). |
| Mission Branch Library Community Garden - Monday Nights | image | Aged out of the feed, and a bad seed — no such branch exists in Hennepin County. |
| Summer Outdoor Festival - Brainerd | website (×2 rows) | Aged out; no event of this name exists. Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival. |
| Pizza King Station | website | Aged out; no Minnesota location exists — the name matches an Indiana chain. |
| Toddler Tuesday - ECFE | website | Aged out; item name and logged address describe different things — see Escalations. |
| 688 rows | website | Aggregate roll-up written by the build, never researched as an item. |

## Escalations

These are source-data defects the fixer cannot close by searching. Each was **re-verified first-hand today** against the feed published this morning, and each is still present.

**Bump & Putt Family Fun Center — shipping a broken link, 8th consecutive run.** The stored website `brainerd.com/business/bump-n-putt-family-fun-park/` was fetched again today and returns a hard 404 ("Sorry! That page doesn't seem to exist."). The stored address `Four miles north of Nisswa, MN` is also wrong; the correct address is **29107 State Hwy 371, Pequot Lakes, MN 56472** (phone 218-568-8833). The stored coordinates were geocoded *from* the wrong address, so the pin is wrong too — the address fix and the coordinate blanking are one fix, not two, because STEP 4.9 skips populated coordinates and a corrected address with an uncorrected pin never self-heals. There is no evidence of closure and no evidence of current operation; those are different findings, and the row must not be closed as "confirmed closed". It is kept open deliberately: it is the only thing making the broken link visible.

**Bowlero Brooklyn Park — wrong ZIP, non-canonical URL.** `bowlero.com/location/bowlero-brooklyn-park` 301s to `luckystrikeent.com/location/lucky-strike-brooklyn-park`, and the venue's own page states **7545 Brooklyn Blvd, Brooklyn Park, MN 55443**. The feed stores ZIP **55445**. Both the URL and the ZIP should be corrected at the build stage.

**Rubio's Rewards Thursday Kids Free Meal — bad seed, and the most serious of these.** Rubio's Coastal Grill operates roughly 82 restaurants across California, Arizona and Nevada only; it has **no Minnesota locations**. The feed carries this as a `meal_deals` row addressed "Multiple Twin Cities locations". A `deal_description` is a factual claim a family will act on at a counter, so this is worse than a missing image. Recommend the build **drop the row**.

**Cameron Park (Bemidji) — the address field holds a lake, not an address.** Stored address is `Lake Bemidji, Bemidji, MN`. Public sources disagree on the real street address (`2504` vs `2609 Birchmont Dr NE`), so no correction should be asserted from search results — this field needs a first-party source rather than a guess.

**Toddler Tuesday - ECFE — venue-substitution trap.** The item name and the logged address (`10 Coon Rapids Boulevard`) describe different things; that address is the Urban Air trampoline park. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/` — that must be rejected, because attaching a paid trampoline-park URL to a row labelled ECFE misrepresents a sliding-fee district parenting class as a commercial jump session.

**Structural ask, now raised for the 6th run.** Have the build **auto-close an unresolved row once its item has left the published feed**. Eleven of today's 20 open rows are for items that no longer ship; the fixer cannot close them by searching, so they accrue indefinitely. This single change drains 11 of 20 rows. A permanently unresolvable row that never leaves the queue trains the reader to skim the block.

One positive note: **Perkins' Tuesday kids-eat-free promotion was independently corroborated as still active** at Minnesota locations, so unlike Rubio's that row is a genuine deal with only an image gap.

## Diagnostics

- `log_base_rejected`: **not triggered.** The base passed both guards — header exactly the 10-column schema, and 3,057 rows, up monotonically from 2,983 (09-08) and 2,640 (09-05).
- Base provenance: the local copy was byte-identical to the GitHub remote by git blob SHA-1 (`d0d2003f82022bc7b5068660100ec45d5f13bfd9`, 951,760 bytes), so there was no stale-base or owner-edit divergence to resolve this run.
- `no_run_summary_today`: **not triggered.** The build's `run_summary` marker for 2026-09-09 is present, and the published feed's `generated_date` is 2026-09-09, so the fixer ran *after* the build and worked a current queue (unlike 2026-09-07, when the ordering was inverted).
- Run date was derived from the GitHub API `Date` response header rather than the sandbox clock, per the standing rule that the sandbox clock and the injected date have both been wrong, and wrong in agreement.
- Drive was used only to fetch the publish token, at the start of the run (fail-fast gate). No AI-ineligibility skips occurred; the one-time Drive base fallback did not fire.
- Regression guard: the 3,057 carried rows were compared against the pre-run base and are identical; no resolved row was re-opened, edited or deleted.
- Source-trust note: one research subagent cited `twincitiesfrugalmom.com` as corroboration. That source was retired from this pipeline on 2026-08-28; it was not relied on for any claim written to the log, and the Perkins promotion was corroborated independently.
- Publish: both artifacts verified post-PUT by returned size and by SHA change — see Files.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
