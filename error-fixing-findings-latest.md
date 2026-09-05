# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-09-05** (derived from the GitHub API `Date` response header, not the sandbox clock). Finished 04:55 America/Chicago.

## Summary

Open queue at start: **21 rows** — 6 `unresolved_website`, 15 `unresolved_image` — covering 20 distinct items. One of those 20, `688 rows`, is an aggregate roll-up diagnostic rather than a fixable venue, so 19 items were actually worked.

Resolved this run: **1** — 0 website, 1 image. The image split is `og_image` 0, `facebook` 0, `stock_openverse_specific` 0, `site_photo` 1.

Left open: **20 rows** (6 `unresolved_website`, 14 `unresolved_image`), rolling to tomorrow.

Yield was low, and deliberately so. Every candidate the research pass surfaced was re-checked by direct fetch rather than accepted on the researcher's confidence rating, and six plausible-looking candidates were rejected on inspection — including two the research pass had rated "high" confidence. The bar exists because a wrong image or URL reaching a family is worse than a row waiting another day.

**One resolution was made and then deliberately withdrawn** — see *A closure that was reverted* below. It is recorded here rather than quietly dropped, because the reasoning matters more than the count.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Minneapolis Parks Volunteer Programming | image | `site_photo` — body photo from the item's own MPRB deep-link page `minneapolisparks.org/volunteer-and-give/`, self-hosted at `/wp-content/uploads/2018/11/Lyndale-Garden-Volunteers_2.jpg`, captioned "Volunteer Weeding Flowerbed at Lyndale Garden". Verified by direct fetch. Not an og:image (WebFetch strips `<head>`), not a hero banner, not a logo. |

### A closure that was reverted

**Bump & Putt Family Fun Center** was provisionally resolved as `confirmed no site`, then reverted to OPEN before publish. The research holds up — the venue is operating as Bump'N'Putt Family Fun Park at 29107 State Hwy 371, Pequot Lakes MN 56472 (phone 218-568-8833), and it genuinely has no first-party website, only third-party directories. That is now the sixth independent confirmation.

The reason for reverting is that closing the row would have **buried a live defect**. The feed still carries `brainerd.com/business/bump-n-putt-family-fun-park/` for this venue, and that URL has been a hard 404 on repeated checks. While the row is open, the broken link stays visible; once closed, it stops being surfaced and the feed keeps shipping it. The queue entry is doing useful work as a defect marker even though no search will ever close it. The standing project guidance also records that this row must not be closed as "confirmed gone" — absence of a website is not evidence of closure, and the venue is in fact open.

The right fix is at the build stage: blank the dead URL, and auto-close unresolved rows once their item leaves the published feed.

### A note on the `site_photo` token

The task's three named image routes are `og_image`, `facebook` and `stock_openverse_specific`. The Minneapolis Parks resolution came via a fourth route this pipeline has used before: a photo in the page **body**, which survives WebFetch's markdown conversion even though the `<head>` — and therefore the og:image tag — does not. Rather than mislabel it `og_image`, it is recorded as `site_photo`, a value already in the project's documented `image_source` vocabulary, so real-vs-stock resolutions stay separable in the log. Flagging the choice here because it is a judgement call made without a human present.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Rubio's Rewards Thursday Kids Free Meal | image | **Not a Minnesota entity** — escalation, should be dropped rather than image-fixed. |
| Mission Branch Library Community Garden - Monday Nights | image | **Not a Minnesota entity** — escalation, should be dropped rather than image-fixed. |
| Bowlero Brooklyn Park (Lucky Strike) | image | Only brand-wide marketing stock available (`family-bowling.jpg` on a Contentful CDN, reused across Lucky Strike locations). Venue confirmed at 7545 Brooklyn Blvd; note stored ZIP `55445` disagrees with the venue's own `55443`. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Chain-wide item spanning Apple Valley, Coon Rapids and Plymouth. A photo of one location cannot stand for all three — the chain-collapse error in image form. |
| Denny's Thursday Kids Eat Free | image | National chain promotion, not a venue. Official site 403s; only logos and marketing graphics exist. |
| Perkins Tuesday Kids Eat Free | image | National chain promotion; JavaScript-rendered site with no fetchable image. Same structural problem as Denny's. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Only an artist headshot on an aggregator (Songkick) — neither venue nor event photo. The venue's own site 403s, Ticketmaster 401s. |
| Music in the Park Thursdays - Mankato | image | The one specific photo found is a Mankato Free Press news photograph — third-party copyrighted, not venue self-hosted. Rejected on licensing. |
| Moorhead Summer Splash Event | image | Only city parks-department promotional graphics of the pool facility, not the event; the pools deep-link page 404s. |
| Winona Parks & Rec Summer Activities | image | Umbrella "summer activities" category rather than one event; only department-level promotional graphics exist. |
| Movies in the Park - Mankato | image | No official web presence on either Mankato or North Mankato parks sites; may be an informal community program. |
| Maplewood Celebrate Summer | image | Event-specific pages 404; the city events index carries no image tied to this event. |
| Lake Ann Park | image | Official Chanhassen park page confirmed (1456 W 78th St) but returns 403 to fetch; Openverse unavailable this run. |
| Cameron Park (Bemidji) | image | Visit Bemidji listing confirms the park (2504 Birchmont Dr NE) but carries no photo; the city RecDesk facility page errors. |
| Bump & Putt Family Fun Center | website | No first-party site exists (6th confirmation). Held open deliberately as a marker for the dead `brainerd.com` URL still in the feed — see above. |
| Toddler Tuesday - ECFE | website | Anoka-Hennepin's ECFE page **rejected**: it names neither "Toddler Tuesday" nor 10 Coon Rapids Blvd. The known venue-substitution trap — attaching the Urban Air Coon Rapids URL, which does advertise a commercial "Toddler Tuesday" — was recognised and not taken. |
| Summer Outdoor Festival - Brainerd | website | Title too generic to resolve (2 open rows). The Brainerd Lakes area's real summer events are Lakes Jam, Lakes Area Music Festival and Iconic Fest; none matches this name. Needs renaming at source, not a URL. |
| Pizza King Station | website | No Minnesota entity confirmed. Pizza King Station is an Indiana chain; the similar-sounding Station Pizzeria in Minnetonka is a different business. Logged address is only "Minnesota". |
| 688 rows | website | **Aggregate roll-up, not a fixable item** — a count of rows lacking a website (657 municipal neighbourhood parks with no individual page). Cannot be closed by lookup. |

## Diagnostics

**Openverse unavailable.** `api.openverse.org/v1/images/` returned read timeouts and then an explicit **HTTP 504 Gateway Timeout** on repeated attempts. Route 3 (`stock_openverse_specific`) was impossible this run, which disproportionately affects the two park items — Lake Ann Park and Cameron Park — where a place-specific CC photo is the most likely remaining source. Worth retrying next run.

**Escalations — items no amount of searching will close.** These need action at the build stage:
- *Rubio's Rewards Thursday Kids Free Meal* — Rubio's Coastal Grill operates only in Arizona, Southern California and Nevada; **zero Minnesota locations**. This is worse than a missing image: the row advertises a kids-eat-free deal that does not exist in this state, and a `deal_description` is a claim a family will act on at a counter. Recommend dropping the row.
- *Mission Branch Library Community Garden - Monday Nights* — no "Mission Branch Library" exists in the Hennepin County system. It is a San Francisco Public Library branch. Recommend dropping the row.
- *Bowlero Brooklyn Park* — stored ZIP `55445`; the venue's own page states `55443`.
- *Bump & Putt Family Fun Center* — stored `brainerd.com` URL is a dead 404 and should be blanked.
- *The structural fix,* which would drain more of this queue than any night of research: **auto-close an unresolved row once its item has left the published feed.** These rows accrue indefinitely because the fixer cannot close them by searching.

**`log_base_rejected`:** none. The base passed both guards — exact 10-column header, 2,640 rows (up from 2,545 on 2026-09-04, growing monotonically as expected) — and was **byte-identical to the GitHub remote by git blob SHA-1** (`66a443a2…`), confirming no owner edits were missed and no stale local copy carried forward.

**`no_run_summary_today`:** not triggered. The build stage's `run_summary` marker for 2026-09-05 was present, so the queue was current.

**Publish:** `error_log.csv` and this report both succeeded, no retries needed. No AI-ineligibility skips — the one-time Drive fallback did not fire, as the GitHub raw read succeeded.

**Row-integrity guard:** a column-level diff against the pre-run base confirms exactly **1** pre-existing row changed, previously blank, and only in the three resolution columns. No already-resolved row was reopened, edited or deleted.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
