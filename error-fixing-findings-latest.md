# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-21 — finished 00:29 local time.

## Summary

Open queue at start: **31 rows / 30 unique items** — 9 rows (8 unique items) `unresolved_website`, 22 rows `unresolved_image`.

Resolved this run: **0** — website 0, image 0 (og_image 0, facebook 0, stock_openverse_specific 0).

Left open: **31 rows**, rolling to tomorrow.

Every open item was worked. One website candidate was returned by the research subagents and was **rejected on audit** rather than accepted, which is why the resolved count is zero rather than one. No image cleared the place-specific bar across 22 items x up to 3 Openverse query passes, plus a second looser pass on the 9 items judged most likely to be depictable.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Maple Grove - Sounds of Summer Movie Night | image | no specific image — event has no commons photo; city-level park hits only |
| Maplewood Celebrate Summer | image | only near-miss stock — "Maplewood Community Center" is a real MN photo but venue-substitution fails the name bar |
| Kelley Park | image | wrong-place stock only — all hits are Kelley Park, San Jose CA |
| Lake Ann Park | image | wrong-place stock only — Chippenham England gardens, Eckankar temple |
| Lily Lake Park | image | generic stock only — water-lily photos, no Stillwater park |
| Pine Tree Pond Park | image | wrong-place stock only — Como Ordway Japanese Garden, Drake Park OR |
| East Lake Park Bandshell | image | wrong-place stock only — Jay Pritzker Pavilion, Chicago |
| Lum Park Recreation Area | image | no specific image — zero name matches; Brainerd city-level hits only |
| Cameron Park (Bemidji) | image | no specific image — Bemidji city-level hits only (Babe the Blue Ox, BSU) |
| Captain's Quarters | website | ambiguous — no verifiable MN venue; the well-known Captain's Quarters Marina is in Antioch, IL |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific image — "Vetter" hits are photographer Kenneth Vetter, not the amphitheater |
| Music in the Park Thursdays - Mankato | image | no specific image — recurring series; hits were South Central MN Pride, wrong event |
| Movies in the Park - Mankato | image | no specific image — recurring series, no venue photo in the commons |
| Moorhead Summer Splash Event | image | no specific image — Moorhead city-level hits only |
| Winona Parks & Rec Summer Activities | image | structurally undepictable — program roll-up, not a place |
| Winona Farmers Market | image | no specific image — Winona city-level hits only |
| Urban Air Trampoline Parks - Minnesota Locations | image | structurally undepictable — multi-location roll-up |
| Denny's Thursday Kids Eat Free | image | structurally undepictable — national recurring meal promo |
| Perkins Tuesday Kids Eat Free | image | structurally undepictable — national recurring meal promo |
| Rubio's Rewards Thursday Kids Free Meal | image | structurally undepictable — national recurring meal promo |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific image — commercial venue, no commons photo |
| Minneapolis Parks Volunteer Programming | image | structurally undepictable — program roll-up, not a place |
| Mission Branch Library Community Garden - Monday Nights | image | no specific image — prior trap: Mission Branch Library hits are San Francisco PL |
| Summer Outdoor Festival - Brainerd | website | ambiguous — not an official event title; no page names it |
| Brainerd Fire Department Golf Scramble | website | no official page — event is real (Aug 15, Cragun's Legacy Courses) but only chamber/aggregator listings exist |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | candidate rejected on audit — city page 403s, evidence was a blog + aggregator, never a city page naming the movie |
| Pizza King Station | website | likely bad data — appears to be an Indiana chain; no MN location found |
| Toddler Tuesday - ECFE | website | ambiguous — Coon Rapids Family Place confirmed at the address, but no program by this exact name |
| Bump & Putt Family Fun Center | website | no site exists — located at 29107 State Hwy 371, Pequot Lakes (address in log says Nisswa); only Yelp/directory listings |
| 688 rows | website | not actionable — category roll-up row, not a per-item work unit |

## Diagnostics

- `no_run_summary_today` — **triggered.** No `run_summary` row dated 2026-08-21 was present when the fixer loaded its base. The local copy and the GitHub raw copy were byte-identical (1,863 rows, md5 `2038e4b6…`), meaning the day's build had not yet written the log. The fixer proceeded on the existing backlog, as specified. Per the known race condition, the local file was re-read immediately before publishing and had not grown, so no build merge needed reconciling and the `no_run_summary_today` row remains accurate as written.
- `log_base_rejected` — none. Base header matched the 10-column schema exactly and the row count (1,863) was consistent with recent days (1,617 on 2026-08-19 → 1,863 on 2026-08-20), so no truncation.
- Publish — `error_log.csv` verified on attempt 1 (497,814 bytes, md5 match against the Contents-API response). No retries needed.
- Drive AI-ineligibility skip — not applicable; the one-time Drive fallback did not fire.

### Notes worth carrying forward

- **The rejected website candidate.** `St. Louis Park Outdoor Movie - A Minecraft Movie` → `stlouisparkmn.gov/our-city/summer-concerts`. The screening is almost certainly real (Aug 27, Wolfe Park, 3700 Monterey Dr), but every corroborating source was either a `familyfuntwincities.com` aggregator listing or a real-estate marketing blog, both previously rejected as sources for this exact item. The city domain returns 403 on WebFetch, so the page could not be confirmed to name the movie. Held to the strict bar and left open.
- **`Pizza King Station` looks like a data-quality problem, not a missing website.** Research found no Minnesota location; the name matches an Indiana chain, and the nearest MN match is the unrelated Station Pizzeria in Minnetonka. Worth checking at the source rather than continuing to search for a URL that may not exist.
- **`Bump & Putt Family Fun Center` has a wrong address in the log.** It is at 29107 State Hwy 371, **Pequot Lakes**, not "four miles north of Nisswa." Still no official site or Facebook page, so it stays open, but the address is correctable.
- **`688 rows` is a roll-up row, not work.** It is a category-level count of website-less rows (657 of them municipal parks). It will never resolve as an individual item and inflates the open-queue count every run.
- **The image queue remains structurally near-undrainable.** Roughly 11 of the 22 items cannot have a place-specific commons photo by construction — national kids-eat-free promos, multi-location roll-ups, and program roll-ups. The wrong-place trap list was confirmed again this run and gained one entry: "Vetter Stone Amphitheater" returns photos by a photographer named Kenneth Vetter.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
