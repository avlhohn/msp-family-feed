# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-01**, finished 04:49 US/Central. Date derived from the `api.github.com` HTTP `Date` header, not the sandbox clock.

## Summary

Open queue at start: **28 rows** — 22 `unresolved_image`, 6 `unresolved_website` (27 distinct items plus one category roll-up).

Resolved this run: **2** — website 0, image 2. Image split: `og_image` 0, `facebook` 0, `stock_openverse_specific` 0, **`site_photo` 2**.

Left open: **26 rows** (25 distinct items), rolling to tomorrow.

The two resolutions came from a route that had never been tried. Five image routes were already settled negatives on this queue — og:image meta tags, Facebook, the Openverse API, the Wikipedia REST API, and Wikimedia Commons — and yesterday's run concluded the image backlog was undrainable by search. But the og:image failures all shared a single cause: `WebFetch` converts pages to markdown and discards `<head>`, which is where og:image lives. Images embedded in the page **body** survive that conversion, and nobody had looked there. Two city parks turned out to publish photo slideshows on their own facility pages.

Because these are body photos from the venue's own official page rather than `<head>` og:image tags, they are flagged **`site_photo`** — an existing token in the pipeline's `REAL_PHOTO_SOURCES` vocabulary — rather than being labelled `og_image`, which would have been inaccurate. This is a deliberate choice made autonomously and is flagged here for review.

Every candidate image was fetched and **visually inspected** before acceptance rather than being judged on its alt text. That mattered: a third candidate would have passed on metadata alone and was wrong (see Escalations).

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Kelley Park | image | `site_photo` — `https://www.applevalleymn.gov/ImageRepository/Document?documentID=22220`, from the city's own Kelley Park facility slideshow. Fetched and visually verified: an aerial photograph of the park showing the stage, lawn crowd, playground and splash area. Not a logo or site-wide banner. |
| Pine Tree Pond Park | image | `site_photo` — `https://www.cottagegrovemn.gov/ImageRepository/Document?documentID=136`, from the park's own facility slideshow, alt text "Pine Tree Pond". Fetched and visually verified as a genuine photograph taken in the park (memorial bench overlooking the pond). Modest subject, but real and place-specific. |

## Still open

| Item | Type | Likely reason |
|---|---|---|
| East Lake Park Bandshell | image | no specific image found — stored URL is a city-wide tourism page, not a bandshell deep link; body photos are generic Winona recreation imagery |
| Lake Ann Park | image | no specific image found — five API routes settled negative; body-photo route blocked (chanhassenmn.gov hard-403s) |
| Lily Lake Park | image | no specific image found — five API routes settled negative; body-photo route blocked (stillwatermn.gov hard-403s) |
| Maple Grove - Sounds of Summer Movie Night | image | aged out — no longer in the published feed (window rolled to 2026-09-01..10-31); left OPEN, not auto-closed |
| Maplewood Celebrate Summer | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Cameron Park (Bemidji) | image | no specific image found — visitbemidji.com venue page body carries only logos and partner branding |
| Lum Park Recreation Area | image | no specific image found — five API routes settled negative; body-photo route blocked (brainerdmn.gov hard-403s) |
| Bowlero Brooklyn Park (Lucky Strike) | image | only generic-or-recurring stock available — page images are Contentful lifestyle stock on a third-party CDN, not the Brooklyn Park location |
| Denny's Thursday Kids Eat Free | image | only generic-or-recurring stock available — national chain brand site; logos and brand marketing only |
| Minneapolis Parks Volunteer Programming | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Mission Branch Library Community Garden - Monday Nights | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Moorhead Summer Splash Event | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Movies in the Park - Mankato | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Music in the Park Thursdays - Mankato | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Niko Moon Concert - Vetter Stone Amphitheater | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Perkins Tuesday Kids Eat Free | image | only generic-or-recurring stock available — national chain brand site; logos and brand marketing only |
| Rubio's Rewards Thursday Kids Free Meal | image | only generic-or-recurring stock available — national chain brand site; logos and brand marketing only |
| Urban Air Trampoline Parks - Minnesota Locations | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Winona Farmers Market | image | no specific image found — official site located today (winonafarmersmarket.org) but its body carries only a wordmark logo |
| Winona Parks & Rec Summer Activities | image | aged out — no longer in the published feed; left OPEN, not auto-closed |
| Summer Outdoor Festival - Brainerd | website | aged out — no longer in the published feed; also no event of this name appears to exist; left OPEN |
| Pizza King Station | website | aged out — no longer in the published feed; no Minnesota location exists (name matches an Indiana chain); left OPEN |
| Bump & Putt Family Fun Center | website | closed-or-broken — no official site exists (4th confirmation); stored brainerd.com URL still 404s |
| Toddler Tuesday - ECFE | website | aged out — no longer in the published feed; item name and stored address describe different things; left OPEN |
| 688 rows | website | not a real item — category roll-up the build writes; never dispatched |

## Escalations — items the fixer cannot close, needing a build-stage or human fix

These are source-data defects, not missing websites or images. Re-searching them nightly can never succeed. Four are new this run.

**NEW — Kelley Park has the wrong address.** The feed stores `13001 Johnny Cake Ridge Rd, Apple Valley, MN 55124`. Kelley Park is at **6855 Fortino St, Apple Valley, MN 55124**, confirmed against the city's own facility page and independent sources. The item name and website are correct; only the address is wrong. This row's coordinates may be pinned to the wrong location as a result.

**NEW — Pine Tree Pond Park has the wrong city.** The feed stores `1485 Settlers Ridge Pkwy, Woodbury, MN 55125`. The park is in **Cottage Grove** — the city's own facility page gives `8300 Isleton Court S, Cottage Grove, MN 55016`. The stored website already points at cottagegrovemn.gov, so the row is internally inconsistent: right venue, right website, wrong city in the address. This is exactly the kind of mismatch the city-resolution and coverage checks would silently mis-attribute.

**NEW — Winona Farmers Market has no website stored.** Its `website` field is blank, which is precisely why no image could ever be found for it. The official site is **`https://www.winonafarmersmarket.org/`** (schema markup confirms Winona Farmers Market, 58 Center St, Winona, MN 55987). Populating this field would at least give a future run something to work from.

**NEW — a metadata-only image check would have shipped a CGI rendering.** Cottage Grove's Pine Tree Pond slideshow carries a second image (`documentId=3476`) captioned "New playground being installed 2023!". Caption and context both read as a genuine park photo, and any check based on alt or caption text would have accepted it. Fetching and looking at it showed a **3D architectural rendering of a proposed playground**, complete with CGI figures — not a photograph of anything that exists. Image acceptance should always include an actual visual check, not just a metadata name match.

**Bump & Putt Family Fun Center — ships a broken link.** Stored website `https://www.brainerd.com/business/bump-n-putt-family-fun-park/` returns 404 and should be blanked at the build stage. Stored address "Four miles north of Nisswa, MN" is wrong; the correct address is **29107 State Hwy 371, Pequot Lakes, MN 56472**, phone 218-568-8833. Re-confirmed today for the fourth time. No official website and no own Facebook page exists — only reject-list directories — so the website row itself is genuinely unresolvable, but the address and the dead link are both fixable.

**Toddler Tuesday - ECFE — the canonical venue-substitution trap.** The item name and stored address describe different things. The stored address `10 Coon Rapids Boulevard, Coon Rapids, MN` is the Urban Air Trampoline & Adventure Park retail location, which runs a commercial "Toddler Tuesday" open-play session. ECFE is a public-school program. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/` — that must be rejected, because attaching a paid trampoline-park URL to a row labelled ECFE misrepresents a sliding-fee district parenting class as a commercial jump session.

**Pizza King Station** — no Minnesota location exists; the name matches an Indiana chain. Almost certainly a bad seed row. **Summer Outdoor Festival - Brainerd** — no event of this name exists; Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival. Likely a misnamed row.

**Standing ask — auto-close rows whose item has left the feed.** 13 of the 27 distinct open items no longer exist in the published feed at all. The fixer has been re-searching content that no longer ships. "No longer in feed" is not a sanctioned resolution, so these stay OPEN by policy, but the build stage is the right place to retire them.

## Diagnostics

**`no_run_summary_today` — TRIGGERED.** The base log contains no `run_summary` row dated 2026-09-01, though the day's build plainly ran: 18 rows carry today's `run_date`, the repo's `pushed_at` is `2026-09-01T08:21:55Z`, and the feed's own `generated_date` is `2026-09-01`. Marker emission remains intermittent (present 08-31, absent 08-23 through 08-28), so this is a marker-emission gap rather than evidence of a missing build. Logged as an `info` row; the run proceeded normally.

**`log_base_rejected` — none.** The local base passed both guards: header exactly the 10-column schema, 2,452 data rows, growing monotonically (696 KB on 08-30 → 730 KB today). It was additionally verified byte-identical to the canonical GitHub copy by git blob SHA-1 (`b5bb5bc5…`), so local-versus-remote staleness was ruled out in both directions rather than assumed.

**Feed cross-check.** Run against the published `msp_family_guide.json` (7.6 MB; 5,876 events, 816 parks, 139 meal deals, 268 volunteer, 477 restaurants; window 2026-09-01 to 2026-10-31). 13 of 27 distinct items are gone, 13 still present, 1 is a roll-up. Two apparent matches were **false** and were caught by explicit verification: "Movies in the Park - Mankato" fuzzy-matched a Minnetonka screening, and "Minneapolis Parks Volunteer Programming" matched three unrelated, more specific Minneapolis Parks volunteer rows. Both are in fact gone. Fuzzy title matching alone is not evidence of presence.

**Publish.** No retries needed; both artifacts committed and verified by size and changed SHA.

**Drive AI-ineligibility skips.** Not applicable — the one-time Drive migration fallback did not fire.

## Files

- `error_log.csv` — https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- `error-fixing-findings-latest.md` — https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
