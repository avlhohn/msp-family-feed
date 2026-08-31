# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-31** — finished 09:47 UTC (date derived from the GitHub API `Date` response header, not the sandbox clock).

## Summary

Open queue at start: **29 rows / 28 unique work units** — 22 `unresolved_image`, 7 `unresolved_website`. Oldest open rows date to 2026-07-08.

Resolved this run: **1** — website 1, image 0. Image split: og_image 0, facebook 0, stock_openverse_specific 0.

Left open: **28** — 22 image, 6 website.

The headline of this run is not the single resolution. It is two structural findings that change what should happen to this queue. First, the last untried image route was probed and closed, so all five image routes are now settled negatives and the 22 image rows are undrainable by search. Second, a cross-check against the published feed found that **13 of the 27 real open items no longer exist in the guide at all** — their source rows aged out when the summer window closed on 2026-08-31. Those rows are being re-searched nightly on behalf of content that no longer ships. Both findings point the same way: this backlog needs a retirement decision, not another route.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Captain's Quarters | unresolved_website | `website: https://legacyofthelakes.org` — the row's full title in the feed is *Captain's Quarters Preschool Program* and its stored address is *Legacy of the Lakes Museum – Boathouse, Alexandria, MN*. The museum's own site confirms Legacy of the Lakes Museum, 205 3rd Ave W, Alexandria, MN 56308 and its attached BoatHouse venue; the program is documented as a free Wednesday 10–11am BoatHouse craft-and-learning hour for preschool through 2nd grade. Address match is exact against our own record. |

The reason this resolved after weeks of failing is worth recording: every prior pass searched the bare string *"Captain's Quarters"* and landed on a marina in Antioch, **Illinois**, which was correctly rejected. Reading the item's own feed row — full title plus address — supplied the venue outright. **Lesson for future runs: before searching an `item`, look it up in the published feed and search the full title plus stored address, not the truncated log label.** Four other open website items are logged under equally lossy labels.

One honest caveat on this resolution: the program's summer Wednesday run ended in August, so it is not on the museum's live upcoming-events calendar, and the program description was corroborated through search results rather than read off a live page fetch. The organization identification is unambiguous and the address matches exactly, which is what the resolution rests on.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Kelley Park | unresolved_image | No specific image found — all five routes closed; Commons/Openverse both return out-of-state or unrelated hits |
| Lake Ann Park | unresolved_image | No specific image found — nearest CC photos are the Eckankar temple, a recurring false positive |
| Lily Lake Park | unresolved_image | No specific image found — nearest CC photos are Stillwater Carnegie Library |
| Pine Tree Pond Park | unresolved_image | No specific image found; also an address/website city conflict (Cottage Grove site, Woodbury address) |
| East Lake Park Bandshell | unresolved_image | No specific image found — nearest CC photos are Winona Masonic Temple |
| Lum Park Recreation Area | unresolved_image | No specific image found — nearest CC photos are Brainerd Carnegie Library; `brainerdmn.gov` hard-403s |
| Cameron Park (Bemidji) | unresolved_image | No specific image found — nearest CC photos are Watermark Art Center |
| Winona Farmers Market | unresolved_image | Only generic/recurring stock available; no website on the row |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | No specific image found — nearest CC photos are a library and protest photos |
| Denny's Thursday Kids Eat Free | unresolved_image | Generic by construction — national chain promo, no place-specific photo exists; `dennys.com` hard-403s |
| Perkins Tuesday Kids Eat Free | unresolved_image | Generic by construction — national chain promo |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | Generic by construction — national chain promo |
| Maple Grove - Sounds of Summer Movie Night | unresolved_image | **Item no longer in feed** (aged out) |
| Maplewood Celebrate Summer | unresolved_image | **Item no longer in feed** (aged out) |
| Niko Moon Concert - Vetter Stone Amphitheater | unresolved_image | **Item no longer in feed** (aged out) |
| Moorhead Summer Splash Event | unresolved_image | **Item no longer in feed** (aged out) |
| Winona Parks & Rec Summer Activities | unresolved_image | **Item no longer in feed** (aged out) |
| Urban Air Trampoline Parks - Minnesota Locations | unresolved_image | **Item no longer in feed**; also a multi-location roll-up, generic by construction |
| Minneapolis Parks Volunteer Programming | unresolved_image | **Item no longer in feed**; also an agency program roll-up, generic by construction |
| Mission Branch Library Community Garden - Monday Nights | unresolved_image | **Item no longer in feed** (aged out) |
| Music in the Park Thursdays - Mankato | unresolved_image | **Item no longer in feed** (aged out) |
| Movies in the Park - Mankato | unresolved_image | **Item no longer in feed** (aged out) |
| Bump & Putt Family Fun Center | unresolved_website | No official site or own Facebook page exists; the DMO link the feed now carries is dead (see Escalations) |
| Pizza King Station | unresolved_website | Source-data defect — no Minnesota location exists; **item no longer in feed** |
| Summer Outdoor Festival - Brainerd | unresolved_website | Source-data defect — no event of this name exists; **item no longer in feed** (2 rows) |
| Toddler Tuesday - ECFE | unresolved_website | Source-data defect — title and address describe different things; **item no longer in feed** |
| 688 rows | unresolved_website | Category roll-up, not a per-item work unit — never dispatchable |

## Escalations

These will never close by searching. They need a build-stage fix or a retirement decision.

**1. Retire the 13 aged-out rows.** Every open item marked *item no longer in feed* above was checked against the published `msp_family_guide.json` for the 2026-08-31 → 2026-09-30 window: 13 of the 27 real items have no row there at all. They were summer events, and the window has moved past them. Recommended action: retire these open rows, or better, have the build auto-close an `unresolved_website` / `unresolved_image` row once its item has left the feed. They were not auto-closed here because "no longer in feed" is not one of this task's sanctioned resolutions — closing them would have meant inventing a resolution type.

**2. Bump & Putt Family Fun Center — dead link plus a wrong address.** The website the feed now carries for this row, `https://www.brainerd.com/business/bump-n-putt-family-fun-park/`, returns the Brainerd DMO's 404 page ("Sorry! That page doesn't seem to exist."), verified twice this run. So the row simultaneously ships a broken link and sits in the unresolved-website queue. The stored address *"Four miles north of Nisswa, MN"* is also still wrong; the correct address is **29107 State Hwy 371, Pequot Lakes, MN 56472**, phone **218-568-8833** — third independent confirmation. Recommended action: blank the dead website and correct the address at the build stage. No official site or own Facebook page exists, so the website row itself will not close.

**3. The image backlog is now closed on all five routes.** With Wikimedia Commons probed and closed this run, there is no remaining search route for the 22 image rows. Recommended action is one of: a `<head>`-preserving fetch path (which would unblock og:image, the only route with real coverage of municipal parks); an image source with municipal-park coverage; or retiring the roughly 11 rows that are generic *by construction* — national chain kids-eat-free promos and multi-location or agency roll-ups, which have no place-specific photo to find because they describe no single place.

## Diagnostics

**Image route probed and closed — Wikimedia Commons.** This was the one route not previously attempted on this queue. Both `list=search` over the File namespace on exact venue name plus city, and `list=geosearch` for CC-licensed files within 1500 m of each item's stored coordinates, were run against the 9 venue-shaped items that still exist in the feed (with backoff after HTTP 429 on the first four). Result: **0 eligible photos**. No returned file title contained the target venue name. Every geosearch hit was a nearby but unrelated landmark: Lake Ann Park → the Eckankar temple (the same false positive Openverse produced), East Lake Park Bandshell and Winona Farmers Market → Winona Masonic Temple, Lily Lake Park → Stillwater Carnegie Library, Lum Park → Brainerd Carnegie Library, Cameron Park → Watermark Art Center, Bowlero Brooklyn Park → Rockford Road Library and protest photos, Kelley Park → a 1929 nursery catalogue PDF. Commons therefore joins og:image (WebFetch strips `<head>`), Facebook (albums unreadable), Openverse (0/22 on three prior runs) and the Wikipedia REST summary API (probed 2026-08-30) as a settled negative.

**Openverse was deliberately not re-run.** It returned 0 of 22 on three consecutive prior runs across three query variants and 188 hits. A fourth identical pass would have consumed the run's budget to reproduce a known result, so the effort went to the untried Commons route and to the feed cross-check instead. This is a deliberate choice, recorded so it is not mistaken for an omission.

**`log_base_rejected`: none.** The base passed both guards. The local copy was byte-identical to the remote — local git blob SHA-1 `ca97d79eceeac7e760f8a79c8ef136865a82be15` matched the contents API `sha` exactly — the header was exactly the 10-column schema, and the row count was 2430 data rows against 720,612 bytes, up from 644,815 bytes on 2026-08-28. Growth is monotonic, so no truncation.

**`no_run_summary_today`: not triggered.** The build's `run_summary` marker for 2026-08-31 is present in the base log, alongside 37 other pipeline rows from today's build. Worth noting because this check has been a false positive in the recent past when the build stopped emitting the marker; it is emitting again.

**Publish:** see below — both files committed and verified.

**Run date:** derived from the GitHub API `Date` response header (`Mon, 31 Aug 2026 09:40:28 GMT`). The sandbox clock agreed on this run, but was not relied on.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
