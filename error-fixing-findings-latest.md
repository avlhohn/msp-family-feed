# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-09-05** (derived from the GitHub API `Date` response header, not the sandbox clock). Finished 04:53 America/Chicago.

## Summary

Open queue at start: **21 rows** — 6 `unresolved_website`, 15 `unresolved_image` — covering 20 distinct items. One of those 20, `688 rows`, is an aggregate roll-up diagnostic rather than a fixable venue, so 19 items were actually worked.

Resolved this run: **2** — 1 website, 1 image. The image split is `og_image` 0, `facebook` 0, `stock_openverse_specific` 0, `site_photo` 1.

Left open: **19 rows** (5 `unresolved_website`, 14 `unresolved_image`), rolling to tomorrow.

Yield was low, and deliberately so. Every candidate the research pass surfaced was checked against the relevance filter by direct fetch rather than accepted on the researcher's confidence rating, and five plausible-looking candidates were rejected on inspection — including one the research pass had rated "high" confidence. The bar exists because a wrong image or URL reaching a family is worse than a row waiting another day.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Minneapolis Parks Volunteer Programming | image | `site_photo` — body photo from the item's own MPRB deep-link page `minneapolisparks.org/volunteer-and-give/`, self-hosted at `/wp-content/uploads/2018/11/Lyndale-Garden-Volunteers_2.jpg`, captioned "Volunteer Weeding Flowerbed at Lyndale Garden". Verified by direct fetch. Not an og:image (WebFetch strips `<head>`), not a hero banner, not a logo. |
| Bump & Putt Family Fun Center | website | `confirmed no site` — venue is **open**; identity verified as Bump'N'Putt Family Fun Park, 29107 State Highway 371, Pequot Lakes MN, which is ~4 mi north of Nisswa and matches the logged address. No official website exists; presence is third-party directories only (Yelp listing updated 2026-08). A prior run found the old URL dead. Negative resolution — should not be re-queued. |

### A note on the `site_photo` token

The task's three named image routes are `og_image`, `facebook` and `stock_openverse_specific`. The Minneapolis Parks resolution came via a fourth route this pipeline has used before: a photo in the page **body**, which survives WebFetch's markdown conversion even though the `<head>` (and therefore the og:image tag) does not. Rather than mislabel it `og_image`, it is recorded as `site_photo` — a value already in the project's documented `image_source` vocabulary — so real-vs-stock resolutions stay separable in the log. Flagging the choice here because it is a judgement call made without a human present.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Rubio's Rewards Thursday Kids Free Meal | image | **Not a Minnesota entity** — see Diagnostics. Should be dropped, not image-fixed. |
| Mission Branch Library Community Garden - Monday Nights | image | **Not a Minnesota entity** — see Diagnostics. Should be dropped, not image-fixed. |
| Bowlero Brooklyn Park (Lucky Strike) | image | Only brand-wide marketing stock available (`family-bowling.jpg` on a Contentful CDN, reused across Lucky Strike locations). Venue itself confirmed at 7545 Brooklyn Blvd; the Bowlero→Lucky Strike rebrand is real. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Chain-wide item spanning Apple Valley, Coon Rapids and Plymouth. A photo of one location cannot stand for all three — that is the chain-collapse error in image form. |
| Denny's Thursday Kids Eat Free | image | National chain promotion, not a venue. Official site 403s; only logos and marketing graphics exist. |
| Perkins Tuesday Kids Eat Free | image | National chain promotion; site is JavaScript-rendered with no fetchable image. Same structural problem as Denny's. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Only an artist headshot on an aggregator (Songkick) — neither a venue nor an event photo. Venue's own site 403s, Ticketmaster 401s. |
| Music in the Park Thursdays - Mankato | image | The one specific photo found is a Mankato Free Press news photograph — third-party copyrighted, not venue self-hosted. Rejected on licensing. |
| Moorhead Summer Splash Event | image | Only city parks-department promotional graphics of the pool facility, not the event; the pools deep-link page 404s. |
| Winona Parks & Rec Summer Activities | image | Umbrella "summer activities" category rather than one event; only department-level promotional graphics exist. |
| Movies in the Park - Mankato | image | No official web presence found on either Mankato or North Mankato parks sites; may be an informal community program. |
| Maplewood Celebrate Summer | image | Event-specific pages 404; the city events index carries no image tied to this event. |
| Lake Ann Park | image | Official Chanhassen park page confirmed (1456 W 78th St) but returns 403 to fetch; Openverse unavailable this run. |
| Cameron Park (Bemidji) | image | Visit Bemidji listing confirms the park (2504 Birchmont Dr NE) but carries no photo; the city RecDesk facility page errors. |
| Toddler Tuesday - ECFE | website | Anoka-Hennepin's ECFE page was **rejected**: it names neither "Toddler Tuesday" nor 10 Coon Rapids Blvd, so it fails the "page must specifically name the item" rule despite being the right district. |
| Summer Outdoor Festival - Brainerd | website | Title too generic to resolve (2 open rows). The Brainerd Lakes area has several real summer festivals — Lakes Jam, Lakes Area Music Festival, Iconic Fest — but nothing matches this name. Likely needs renaming at source rather than a URL. |
| Pizza King Station | website | No Minnesota entity confirmed. Pizza King Station is an Indiana chain; the nearby-sounding Station Pizzeria in Minnetonka is a different business. The logged address is only "Minnesota". |
| 688 rows | website | **Aggregate roll-up, not a fixable item** — a count of rows lacking a website (657 of them municipal neighbourhood parks with no individual page). Cannot be resolved by lookup; consider closing it as a known-permanent structural gap so it stops presenting as an open work item. |

## Diagnostics

**Openverse unavailable.** `api.openverse.org/v1/images/` returned read timeouts and then an explicit **HTTP 504 Gateway Timeout** on repeated attempts. Route 3 (`stock_openverse_specific`) was therefore impossible this run, which disproportionately affects the two park items (Lake Ann Park, Cameron Park) where a place-specific CC photo is the most likely remaining source. Worth retrying next run.

**Two non-Minnesota rows — data-quality escalation.** These are not image problems and no amount of image-fixing will help; a future build should drop them:
- *Rubio's Rewards Thursday Kids Free Meal* — Rubio's Coastal Grill operates only in Arizona, Southern California and Nevada. Zero Minnesota locations.
- *Mission Branch Library Community Garden - Monday Nights* — no "Mission Branch Library" exists in the Hennepin County system (whose Minneapolis branches are Arvonne Fraser, East Lake, Franklin, Hosmer, Linden Hills, Central, Nokomis, North Regional, Northeast, Pierre Bottineau, Roosevelt, St. Anthony, Sumner, Walker, Washburn, Webber Park). Mission Branch Library is a San Francisco Public Library location.

**`log_base_rejected`:** none. The base passed both guards — exact 10-column header, 2,640 rows (up from 2,545 on 2026-09-04, so growing monotonically as expected) — and was **byte-identical to the GitHub remote by git blob SHA-1** (`66a443a2…`), confirming no owner edits were missed and no stale local copy was carried.

**`no_run_summary_today`:** not triggered. The build stage's `run_summary` marker for 2026-09-05 was present, so the queue was current.

**Publish:** `error_log.csv` succeeded on the first attempt — local 802,167 b, remote 802,167 b, sha changed to `244811e71240`. No retries needed. No AI-ineligibility skips (the one-time Drive fallback did not fire; the GitHub raw read succeeded).

**Row-integrity guard:** a column-level diff against the pre-run base confirmed exactly 2 pre-existing rows changed, both previously blank, and in only the three resolution columns. No already-resolved row was reopened, edited or deleted.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
