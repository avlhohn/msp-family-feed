# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-19 · **Finished:** 09:40 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `d9ce54339936` — 1,249,849 bytes, 3,915 data rows, 10-column
header exact, 3,916 CRLF / 0 bare LF. The local working copy matched the published blob
byte-for-byte. **Published log:** 3,925 data rows, 1,256,840 bytes.

## Summary

Nineteen open rows were examined, deduplicating to eighteen distinct items, one of which is a
non-actionable roll-up and was excluded — so **seventeen items** were worked across three parallel
research batches. **None were resolved.** That is the eleventh consecutive run at zero.

The 2026-09-18 run established why: the queue has had **no inflow**. This run confirms it and adds
the measurement from the log's own side. The newest `unresolved_image` row is dated 2026-07-23 and
the newest `unresolved_website` 2026-08-16 — 34 and 58 days old — while the build runs nightly.
Meanwhile the same defects are still being logged every night under issue_type names this task's
selector does not read: **300 open `missing_website`** rows and **240 open `generic_image`** rows.
The fixer is draining a nineteen-row pond beside a 540-row lake. What is left in the pond is the
residue ten previous runs already failed on, so an eleventh attempt at the same rows was never going
to clear them. The remedy is vocabulary alignment between the build's loggers and this task's
selector, not more fixer effort.

The one remaining resolution path is **structurally empty for this queue's venues**.
`stock_openverse_specific` returned `result_count=0` for every place-specific query attempted — Lake
Ann Park (Chanhassen), Vetter Stone Amphitheater, Wheeler Park (North Mankato), Moorhead municipal
pool. The two queries that did return results held only wrong-place generics. Openverse has
effectively no coverage of municipal and outstate Minnesota venues, so that path cannot drain an
image queue made of them. That zero is a property of the corpus, not of the query.

Today's daily build has **not yet run**; this fixer executed ahead of it, so the queue worked here is
yesterday's. Recorded as `no_run_summary_today`, and it reflects a genuinely absent build rather than
a missing marker.

What the run did produce is six corrections and data-quality escalations, including one that
overturns a research verdict and one near-miss that would have written a permanent wrong-venue error
into the feed. Those are under Diagnostics.

## Resolved this run

None.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Maplewood Celebrate Summer | unresolved_image | July event, now past; the city's event page has rolled over. Openverse returned only Maplewood **State Park** (Otter Tail County, ~300 km away) — rejected as wrong-place. |
| Lake Ann Park | unresolved_image | Chanhassen city page returned 403 to the fetcher. A tooling failure is not evidence an image is absent; re-probe. |
| Niko Moon Concert — Vetter Stone Amphitheater | unresolved_image | Only candidate found was a performer headshot from the artist's own site. A headshot is not a photo of the venue or the event. |
| Music in the Park Thursdays — Mankato | unresolved_image | Summer series, concluded. No place-specific image; Openverse zero for the venue. |
| Movies in the Park — Mankato | unresolved_image | Same series page, same outcome. |
| Moorhead Summer Splash Event | unresolved_image | Past event; the municipal pool has no published photo Openverse or the city site exposes. |
| Winona Parks & Rec Summer Activities | unresolved_image | Fetcher returned 404 on the Parks & Rec page. Tooling failure, not absence. |
| Urban Air Trampoline Parks — Minnesota Locations | unresolved_image | Multi-location roll-up. Only brand logos and franchise stock; no single location to photograph. |
| Denny's Thursday Kids Eat Free | unresolved_image | National chain promotion. Only coupon graphics and brand marks. |
| Perkins Tuesday Kids Eat Free | unresolved_image | As above. |
| **Rubio's Rewards Thursday Kids Free Meal** | unresolved_image | **Wrong-state item.** Rubio's Coastal Grill has zero Minnesota locations (~82 restaurants, CA/AZ/NV only). Unresolvable by construction — recommend the build DROP it. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Rebranded location; available imagery is chain marketing, not this venue. |
| **Mission Branch Library Community Garden — Monday Nights** | unresolved_image | **Wrong-state item.** Mission Branch Library is San Francisco Public Library, 1234 Valencia St. No Minnesota library of that name exists. Recommend DROP. |
| Summer Outdoor Festival — Brainerd (2026-07-24) | unresolved_website | Generic title naming no organiser; two open rows carry the same string. Nothing specific enough to verify against. |
| Summer Outdoor Festival — Brainerd (2026-07-31) | unresolved_website | As above. |
| **Pizza King Station** | unresolved_website | **Suspected wrong-state, not proven.** Every hit resolves to an Indianapolis restaurant. The row's own address is the bare string "Minnesota" with no city. Flagged for human review rather than auto-dropped. |
| Toddler Tuesday — ECFE | unresolved_website | ECFE is a statewide program run per district; no single canonical site, and the row names no district. |
| **Bump & Putt Family Fun Center** | unresolved_website | **Correction — the venue is NOT closed** (see Diagnostics). It operates as Bump 'N' Putt Family Fun Park, Pequot Lakes. It has no official website, only aggregator listings, so the row stays open — but the defect is the **name**, not the venue's existence. |
| 688 rows | unresolved_website | Non-actionable roll-up; the item field holds an aggregate count, not a venue. Can never resolve. Excluded from the work list. |

## Diagnostics

**A research verdict was overturned on verification.** A subagent returned `CONFIRMED_CLOSED` for
*Bump & Putt Family Fun Center*, on the basis that no evidence of the venue could be found under that
spelling. Widening the spelling found it trading as **Bump 'N' Putt Family Fun Park**, 29107 State
Hwy 371, Pequot Lakes MN 56472, ph 218-568-8833, operating since 1987, with listings updated August
2026. The logged address — "four miles north of Nisswa, MN" — points up Hwy 371 toward Pequot Lakes,
so the address was approximately right all along and the name was the defect. Absence of evidence for
one spelling is not evidence of closure, and a probe keyed to one spelling is structurally blind to a
venue that spells itself differently. Had the verdict been accepted, a false "permanently closed"
claim would have entered the permanent log.

**A wrong-venue near-miss, logged so it is not "fixed" later.** `goputtnbump.com` surfaces first for
the Pequot Lakes venue and must **not** be attached to it. That domain belongs to *Go-Putt-N-Bump
Amusement Park*, 15802 US Hwy 59, Detroit Lakes MN — roughly 180 km away. The two names are
anagram-close and aggregators cross-contaminate their details (both are described as "opened 1987"),
so a future website backfill searching for the Pequot Lakes venue will surface this domain first.
Attaching it would be the wrong-venue error, which never self-heals once a website is populated.

**Two rows are out of state and one is suspected to be.** Rubio's and Mission Branch Library are
unresolvable by construction — there is no Minnesota venue to photograph and no Minnesota deal to
honour — and are recommended for dropping rather than re-queuing. Same defect class as the Austin-TX
bouldering photo caught on 2026-09-15, except that here the whole **row** is out of state, not just
its image. Pizza King Station is flagged rather than dropped: no Minnesota location was found, but
absence of a web presence is not proof of absence, and the nearest Minnesota name-neighbour (Station
Pizzeria, Minnetonka) is a different restaurant that must not be matched to this row.

**Openverse has no place-specific coverage for this queue.** Four of six queries returned zero
results. The two that returned results held only wrong-place generics — notably Maplewood **State
Park** in Otter Tail County against the **City** of Maplewood, which a name-match rule would have
accepted, stamping a photo of a place 300 km away.

**Two items were blocked by fetch failures, not by absent images.** Lake Ann Park returned 403 and
Winona Parks & Rec returned 404. Those rows are left open on the explicit understanding that a
tooling failure is not evidence an image does not exist, and they are worth re-probing rather than
writing off.

**Recommended upstream fixes**, none of which are in this task's scope: align the vocabulary between
the build's STEP 4.5/4.6 loggers and this task's selector, so the 540 open rows currently logged as
`missing_website` and `generic_image` reach the queue that exists to work them; log aggregate
findings under a `*_summary` issue_type so roll-ups like "688 rows" are never selected as work items;
drop the two confirmed out-of-state rows and review the third.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
