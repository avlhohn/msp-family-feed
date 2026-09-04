# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-04** — finished 04:53 US/Central (date derived from the GitHub API `Date` header, not the sandbox clock).

## Summary

Open queue at start: **22 rows / 21 distinct items** — 16 `unresolved_image`, 6 `unresolved_website`.

Resolved this run: **1 row** — 1 image (`site_photo` 1, `og_image` 0, `facebook` 0, `stock_openverse_specific` 0), 0 website.

Left open: **21 rows**, rolling to tomorrow.

The headline finding is not the single resolution. A feed cross-check shows **only 8 of the 21 distinct items still exist in the published feed**: 12 have aged out with the summer window and 1 (`688 rows`) is a roll-up, not a work item. The fixer has been re-searching content that no longer ships. Separately, **2 of the 3 image resolutions proposed by research subagents were wrong and were rejected on independent verification** — see Rejected candidates.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Maple Grove - Sounds of Summer Movie Night | unresolved_image | `site_photo` — real photograph of the Town Green Park bandshell during a Sounds of Summer performance, from the City of Maple Grove's own venue page (`maplegrovemn.gov/672/Town-Green`, asset `ImageRepository/Document?documentId=3648`). Image was fetched and **visually inspected**: genuine photo (curved-roof bandshell, performers on stage, audience on the lawn, pond behind), not a logo, render or stock asset. City/venue confirmed — the page states 7991 Main Street, Maple Grove. |

## Rejected candidates (subagent said RESOLVED; verification said no)

Both rejections came from the standing rule that a subagent's RESOLVED is a *candidate*, not a verdict.

| Item | Proposed | Why rejected |
|---|---|---|
| Cameron Park (Bemidji) | MN DNR photo `…/state_parks/virtual_tours/lake_bemidji/…/lb_14.jpg` | **Wrong venue.** The asset is from Lake Bemidji *State Park*'s virtual tour; the item is Cameron Park, a City of Bemidji park. Also decisive: the agent described this image as having *"blue slides, red/pink tunnels, blue rubber safety surfacing"* — the actual file shows a **green/tan playground on wood chips**. The description was confabulated from the other item's image. |
| Lake Ann Park | `itin-dev.wanderlogstatic.com/freeImage/…` | **Provenance.** Wanderlog is a third-party trip-planning aggregator that re-hosts images of unknown origin and licence; it is not one of the sanctioned routes. The image is a real playground but contains no landmark, signage or lake view that confirms it is the Chanhassen park. |

The confabulated image description is the reusable lesson: it was caught only by fetching the image and looking at it. Metadata, captions and agent prose all passed.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Maplewood Celebrate Summer | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Lake Ann Park | unresolved_image | In feed. Only candidate was a Wanderlog aggregator CDN image — provenance and licence unverifiable, and no landmark in it confirms Chanhassen. City site chanhassenmn.gov still hard-403s. |
| Cameron Park (Bemidji) | unresolved_image | In feed. Candidate rejected as WRONG VENUE — a MN DNR Lake Bemidji *State Park* virtual-tour photo, which is a different place from this Bemidji **city** park. |
| Niko Moon Concert - Vetter Stone Amphitheater | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Music in the Park Thursdays - Mankato | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Movies in the Park - Mankato | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Moorhead Summer Splash Event | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Winona Parks & Rec Summer Activities | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Urban Air Trampoline Parks - Minnesota Locations | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Denny's Thursday Kids Eat Free | unresolved_image | In feed, but address is 'Multiple Twin Cities locations' — there is no single venue to photograph; only generic national-brand marketing assets exist. |
| Perkins Tuesday Kids Eat Free | unresolved_image | In feed, but address is 'Multiple Twin Cities locations' — no specific venue to photograph; only generic brand assets. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | In feed but BAD SEED — Rubio's has no Minnesota locations at all (see Escalations). Seeking an image is the wrong fix. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | In feed. Chain/franchise: its location pages serve generic shared-CDN brand assets reused across sibling locations, which the recurrence rule rejects. |
| Minneapolis Parks Volunteer Programming | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Mission Branch Library Community Garden - Monday Nights | unresolved_image | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Summer Outdoor Festival - Brainerd | unresolved_website | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Pizza King Station | unresolved_website | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Toddler Tuesday - ECFE | unresolved_website | Aged out — no longer present in the published feed (window is now 2026-09-04 to 2026-10-31), so re-searching it cannot help. |
| Bump & Putt Family Fun Center | unresolved_website | In feed. No first-party website or venue-owned Facebook page exists (5th confirmation); stored brainerd.com URL re-confirmed DEAD 404 today. |
| 688 rows | unresolved_website | Not a work item — a category ROLL-UP the build writes. Never dispatch research on it. |

## Escalations — rows the build should act on (the fixer cannot close these by searching)

Each of these is a **data defect**, not a missing website or image. They have been requeued nightly for weeks; a standing unresolvable row trains the reader to skim the queue.

| Item | Defect | Recommended build action |
|---|---|---|
| Bowlero Brooklyn Park (Lucky Strike) | Stored ZIP **55445** is wrong — the venue's own page states **55443**. Stored `bowlero.com` URL now **301-redirects** (chain rebranded Bowlero → Lucky Strike). | Correct the ZIP and repoint the website to `https://www.luckystrikeent.com/location/lucky-strike-brooklyn-park`; blank the derived coordinate so it re-geocodes. |
| Bump & Putt Family Fun Center | Stored URL `brainerd.com/business/bump-n-putt-family-fun-park/` re-confirmed **DEAD (404) today** — the feed has shipped a broken link for several runs. Stored address "Four miles north of Nisswa, MN" is wrong; real address **29107 State Hwy 371, Pequot Lakes, MN 56472** (5th confirmation), phone 218-568-8833. | **Blank the dead website** and correct the address. No first-party site exists, so the website row stays open — but the broken link is shipping now and is separately fixable. No evidence of closure, so do not drop the row. |
| Rubio's Rewards Thursday Kids Free Meal | **Bad seed.** Rubio's Coastal Grill operates only in AZ, Southern CA and NV — no Minnesota locations. The row advertises a kids-eat-free deal that does not exist in this state. | **Drop the row.** A `deal_description` is a factual claim a family will act on at a counter; this one cannot be honoured anywhere in MN. Higher priority than any image fix. |
| Maple Grove Sounds of Summer Movies | `website` field is **blank**, which is why its image never resolved by the normal route. | Populate `https://maplegrovemn.gov/672/Town-Green`; the page also states the precise address (7991 Main Street) against the stored "Town Green Park, Maple Grove, MN". |
| Toddler Tuesday - ECFE | Item name and logged address describe **different things** — the address is the Urban Air Coon Rapids retail location. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/`; **that is the venue-substitution trap** and must be rejected. Item is no longer in the feed. | Retitle to *Toddler Tuesday – Urban Air Coon Rapids*, or correct the address to the real Anoka-Hennepin ECFE site. |
| Pizza King Station / Summer Outdoor Festival - Brainerd | Neither exists in Minnesota (Pizza King is an Indiana chain; Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival). Both have left the feed. | Likely misnamed or bad seed rows — drop or correct at source. |
| 12 aged-out items (see Still open) | No longer present in the published feed, so no fixer pass can ever close them. | **Have the build auto-close an unresolved row once its item has left the feed.** This is the single highest-leverage change: it would drain 12 of the 21 remaining rows and stop the queue growing on content that no longer ships. |
| `688 rows` | A category **roll-up** the build writes into the `item` column, not a per-item work unit. | Emit roll-ups under a distinct `issue_type` so they never enter the fixer's work queue. |

## Diagnostics

**`no_run_summary_today` — triggered (logged as an `info` pipeline row).** No `run_summary` row dated 2026-09-04 was present in the carried base. The day's build did run — repo commits `Daily feed 2026-09-04` and `Error log 2026-09-04` landed 08:19–08:21Z and the feed's own `generated_date` is 2026-09-04 — so the queue is current and only the end-of-run marker row is missing. Worth noting because this marker was previously missing 08-23→08-28 and then resumed; it has gone quiet again.

**`log_base_rejected` — none.** The base passed both guards: header matched the 10-column schema exactly, and the row count (2,545) is consistent with monotonic growth (2,476 → 2,507 → 2,545). The local copy was also **byte-identical to the GitHub remote by git blob SHA-1** (`f19e0c31…`), so there was no owner-edit drift or stale-carry-forward this run.

**Openverse — timed out on every query**, as on prior runs. Combined with 0 eligible results across three earlier sweeps (0/22), it remains a settled negative; no `stock_openverse_specific` resolution was available.

**Route status.** og:image, Facebook, Openverse, Wikipedia REST and Wikimedia Commons all remain settled negatives. The page-BODY (`site_photo`) route produced this run's only resolution, again from a **city's own CivicPlus-style venue page** — still the richest vein.

**Publish:** see below; no retries were needed.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- This report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
