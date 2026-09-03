# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-03 (derived from the GitHub API `Date` response header, not the sandbox clock) — finished 09:52 UTC.

## Summary

Open queue at start: **26 rows / 25 distinct items** — 20 `unresolved_image`, 5 `unresolved_website` (one of which, `688 rows`, is a build roll-up and is never researched).

Resolved this run: **4 items / 4 rows**, all images.

| Resolution route | Count |
|---|---|
| `og_image` | 0 |
| `facebook` | 0 |
| `stock_openverse_specific` | 0 |
| `site_photo` (page-BODY route) | **4** |
| website | 0 |

Left open: **21 distinct items / 22 rows**, rolling to tomorrow.

**The finding that matters most: only 11 of the 25 open items still exist in the published feed.** The remaining 14 have aged out — the feed window is now 2026-09-03 → 2026-10-31 and these were summer events. The fixer has been re-searching content that no longer ships. This is unchanged from the 2026-08-31 cross-check and the escalation ask is now repeated for a fourth run: **have the build auto-close an unresolved row once its item has left the feed.**

All four resolutions came from the page-BODY image route (images embedded in page bodies survive `WebFetch`'s markdown conversion, whereas `<head>` og:image tags do not). The five older routes — og:image, Facebook, Openverse, Wikipedia REST, Wikimedia Commons — remain settled negatives and were not re-probed.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| East Lake Park Bandshell | `unresolved_image` | `site_photo` — `winonamn.gov/ImageRepository/Document?documentID=159`, from the City of Winona facility page `/facilities/facility/details/Bandshell-28`. Fetched and **visually verified**: real photograph of the historic bandshell at dusk, mid-concert, with municipal band and audience. Page confirms Lake Park (East Lake Winona), Lake Park Drive, Winona MN 55987 — matches the stored address. |
| Lily Lake Park | `unresolved_image` | `site_photo` — `images.dnr.state.mn.us/recreation/fishing/fin/kidsponds/lily.jpg`, from the MN DNR Fishing-in-the-Neighborhood page. **Wrong-lake risk checked and cleared**: the DNR page names Lily Lake, Stillwater, Washington County (Greeley St S & Churchill St W). Visually verified: real photograph of the lake and its fishing pier. *Caveat: low-res 350×250 and a winter/snow scene — a human may prefer to override.* |
| Lum Park Recreation Area | `unresolved_image` | `site_photo` — `live.staticflickr.com/8164/7316670888_838f991c0d_b.jpg`, from Visit Brainerd's (official DMO) Flickr album "Lum Park Brainerd MN". Visually verified: real photograph of the park's RV campground, matching the row's `camping` tag. `brainerdmn.gov` 403 still holds. *Caveat: photo license not stated on the album page.* |
| Winona Farmers Market | `unresolved_image` | `site_photo` — Explore Minnesota **venue-specific listing** photo from `/event/winona-farmers-market/39288` (a listing image, not a tourism-bureau hero banner). Visually verified: real photograph of the market in operation under the Levee Park archway, vendor tents and shoppers visible. |

### One subagent "resolved" claim was rejected

A research pass returned **Bowlero Brooklyn Park** as RESOLVED with `images.ctfassets.net/…/03_FAMILY_BOWLING_290.jpg`, describing it as "venue-specific, location-appropriate". It is not. Fetching the location page showed that image is **1 of 16 generic Contentful brand assets** (alt text: "Family smiling and holding bowling balls together in a vibrant bowling center") reused across every Lucky Strike location page — exactly the recurring-stock case the rules reject. The row stays OPEN. Worth recording as a pattern: a plausible venue page plus a plausible-sounding photo description is not sufficient; the recurrence test (does this asset appear on a sibling location's page?) is what settles it.

## Still open

| Item | Type | Logged | Likely reason |
|---|---|---|---|
| Lake Ann Park | `unresolved_image` | 2026-07-08 | chanhassenmn.gov 403 confirmed; no fetchable DMO/county page carries a body photo |
| Maple Grove - Sounds of Summer Movie Night | `unresolved_image` | 2026-07-08 | aged out of the feed - no longer published, so nothing to attach an image to |
| Maplewood Celebrate Summer | `unresolved_image` | 2026-07-08 | aged out of the feed - no longer published, so nothing to attach an image to |
| Cameron Park (Bemidji) | `unresolved_image` | 2026-07-09 | visitbemidji venue page has no body image; city parks page 404; source absence, not a parse failure |
| Bowlero Brooklyn Park (Lucky Strike) | `unresolved_image` | 2026-07-23 | only generic national Lucky Strike brand assets (recur across all locations) - rejected |
| Denny's Thursday Kids Eat Free | `unresolved_image` | 2026-07-23 | dennys.com hard-403; no location/promotion-specific deep-link page; logo-only otherwise |
| Minneapolis Parks Volunteer Programming | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Mission Branch Library Community Garden - Monday Nights | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Moorhead Summer Splash Event | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Movies in the Park - Mankato | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Music in the Park Thursdays - Mankato | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Niko Moon Concert - Vetter Stone Amphitheater | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Perkins Tuesday Kids Eat Free | `unresolved_image` | 2026-07-23 | perkins.com fetch timeout; no location/promotion-specific deep-link page |
| Rubio's Rewards Thursday Kids Free Meal | `unresolved_image` | 2026-07-23 | BAD SEED - Rubio's Coastal Grill has no Minnesota locations (see Escalations) |
| Urban Air Trampoline Parks - Minnesota Locations | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Winona Parks & Rec Summer Activities | `unresolved_image` | 2026-07-23 | aged out of the feed - no longer published, so nothing to attach an image to |
| Summer Outdoor Festival - Brainerd | `unresolved_website` | 2026-07-24 | no event of this name exists; likely a misnamed row (see Escalations); also aged out of feed |
| Pizza King Station | `unresolved_website` | 2026-08-14 | no Minnesota location exists; name matches an Indiana chain (see Escalations); also aged out of feed |
| Bump & Putt Family Fun Center | `unresolved_website` | 2026-08-15 | no official site exists; directory-only presence (reject-list); stored URL is a dead 404 (see Escalations) |
| Toddler Tuesday - ECFE | `unresolved_website` | 2026-08-15 | item name and stored address describe different things (see Escalations); also aged out of feed |
| 688 rows | `unresolved_website` | 2026-08-16 | category ROLL-UP written by the build, not a per-item work unit - never researched |

## Escalations

These are **source-data defects, not missing websites/images**. Re-searching them nightly can never succeed; they need a build-stage or human fix. Left OPEN deliberately (absence of search results is not positive proof of closure).

- **Rubio's Rewards Thursday Kids Free Meal — BAD SEED, newly established this run.** Rubio's Coastal Grill operates only in Arizona, Southern California and Nevada; it has **no Minnesota locations**. The Minnesota businesses trading as "Rubio's" are unaffiliated independent Mexican restaurants. This row therefore advertises a kids-eat-free deal that does not exist in this state — a factual claim a family would act on at a counter. Recommend removing the row at the build stage rather than continuing to seek an image for it.
- **Bump & Putt Family Fun Center — ships a broken link.** Stored website `https://www.brainerd.com/business/bump-n-putt-family-fun-park/` re-confirmed **DEAD (404)** today. No official site or own Facebook page exists; only reject-list directories. Address confirmed for a fourth time from an independent source as **29107 State Hwy 371, Pequot Lakes, MN 56472**, phone **218-568-8833** (a 218-963-8833 listing is stale) — the stored "Four miles north of Nisswa, MN" is vague. No positive evidence of closure; Yelp shows an August 2026 update, so the business appears to still operate. Build fix: blank the dead website, correct the address.
- **Bowlero Brooklyn Park — ZIP mismatch (new this run).** Stored address ends `MN 55445`; the venue's own page states `MN 55443`. Same wrong-address-on-an-otherwise-correct-row class as Kelley Park and Pine Tree Pond Park. Also note the chain has rebranded Bowlero → Lucky Strike and `bowlero.com` now redirects to `luckystrikeent.com`.
- **Winona Farmers Market — `website` field is blank**, which is why its image row could never resolve through the normal route. Official site verified again this run: **`https://www.winonafarmersmarket.org/`** (58 Center St, Winona, MN 55987). Populating it would let the build enrich this row normally.
- **Pizza King Station** — no Minnesota location exists; the name matches an Indiana chain. Reconfirmed previously on 2026-08-21 and 2026-08-29. No longer in the feed.
- **Summer Outdoor Festival - Brainerd** — no event of this name exists; Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival. Likely a misnamed row. No longer in the feed.
- **Toddler Tuesday - ECFE** — the item name and the stored address describe different things. The stored address is the Urban Air Trampoline Park retail location, which runs a commercial "Toddler Tuesday" open-play session; ECFE is a public-school program. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/` — **that must be rejected**, as it would misrepresent a sliding-fee district parenting class as a paid jump session. No longer in the feed.
- **`688 rows`** — a category roll-up the build writes, not a per-item work unit. Never dispatched for research. It would be cleaner for the build to log roll-ups under a distinct `issue_type` so they never enter this queue.

## Diagnostics

- **Base validated.** Header is exactly the 10-column schema; 2,506 rows, consistent with monotonic growth (2,387 on 08-30 → 2,476 on 09-02 → 2,506 today). No `log_base_rejected`.
- **Local base was byte-identical to the remote** (git blob SHA-1 `ca37add32513bf1e3f1082d2a1153300c92312ec`), so there were no unmerged owner edits to carry forward this run.
- **Freshness: OK.** A `run_summary` row dated 2026-09-03 is present, so the day's build completed. No `no_run_summary_today`.
- **Run date derived server-side** from the GitHub API `Date` header (`Thu, 03 Sep 2026`). The sandbox clock agreed this run, but was not trusted on its own.
- **Token fetched at STEP 1** (fail-fast gate) and validated against the contents API before any research work began. No retries needed.
- **Log integrity checked after editing:** 524 previously-resolved rows preserved unchanged, zero mutations to any immutable column, exactly 4 rows newly resolved plus 1 `fixer_summary` row appended.
- No publish retries or failures.
- Drive was used only to fetch the GitHub token; the one-time Drive base fallback did not fire.

## Files

- Error log: <https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv>
- This report: <https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md>
