# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-04 — finished ~07:07 local.

## Summary

Open queue at start: **58 open rows** (52 distinct items) — `unresolved_website` 17 rows / 11 items, `unresolved_image` 41 rows / 41 items.

Resolved this run: **4 rows / 2 items**, all website (image: 0 — og_image 0, facebook 0, stock_openverse_specific 0).

Left open: **54 rows / 50 items** rolling to tomorrow.

## Resolved this run

| Item | Type | Resolution note |
|------|------|-----------------|
| Kids Summer Craft Camp (Anoka) | website | website: https://www.appleberrysatticcrafts.com/ — verified venue (Appleberry's Attic, 228 E. Main St, Anoka, MN); exact event name + Aug 3–7 camp match |
| Eden Prairie Free Outdoor Movie at Staring Lake | website | website: https://www.edenprairiemn.gov/Home/Components/Calendar/Event/20008/ — verified official City of Eden Prairie event at Staring Lake Amphitheater |

## Still open

| Item | Type | Likely reason |
|------|------|---------------|
| Maple Grove - Sounds of Summer Movie Night | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Maplewood Celebrate Summer | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Kelley Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Lake Ann Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Lily Lake Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Pine Tree Pond Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Sibley Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Staring Lake Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Wolfe Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Chapel Trail at St. John's University | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Lake Park (Winona) | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| East Lake Park Bandshell | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Alexandria City Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Kiwanis Park (Brainerd) | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Cottage Grove Ravine Regional Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Hamline Park | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Lum Park Recreation Area | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Cameron Park (Bemidji) | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Family Dance Party - Rochester Public Library | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Vadnais Heights Summer Concert Series | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Family Fun Night | website | ambiguous — title too generic to disambiguate a specific venue |
| Captain's Quarters | website | ambiguous — multiple venues share the name; no specific MN site confirmed |
| Badges & Bobbers Fishing Event - Lake George | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Music in the Park Thursdays - Mankato | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Movies in the Park - Mankato | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Moorhead Summer Splash Event | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Winona Parks & Rec Summer Activities | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Winona Farmers Market | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Alexandria Freedom Fun Run | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Alexandria Saturday Art Market | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Captain's Quarters Craft Program - BoatHouse | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Urban Air Trampoline Parks - Minnesota Locations | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Denny's Thursday Kids Eat Free | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Perkins Tuesday Kids Eat Free | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Rubio's Rewards Thursday Kids Free Meal | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Topgolf Monthly Membership | image | only generic/recurring stock available (chain/recurring program or no specific photo) |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| Bowlocity Entertainment Center Rochester | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |
| 56 Brewing Minneapolis | image | no specific image found — og:image not surfaceable and no CC name-matched Openverse photo |

…and 10 more still open.

## Diagnostics

- `no_run_summary_today`: no `run_summary` row dated 2026-08-04 was present in the base at fixer load time (the day's build had not yet published its end-of-run marker). Proceeded on the existing open queue; logged as an info/pipeline row.
- `log_base_rejected`: none — base loaded from GitHub (`error_log.csv`, 546 rows, valid 10-col schema, byte-identical to local carry-forward).
- Publish: `error_log.csv` PUT returned 409 on attempt 1 (stale sha), succeeded on attempt 2; post-publish GET confirmed size 161091 == local and sha changed.
- Image resolutions: subagents surfaced images only from third-party aggregator/tourism/news sources (TripAdvisor, Flickr, tourism bureaus, local news), not true `og:image` from each item's own page — rejected per the strict bar. Openverse returned no confident CC-licensed, name-matched photos of the specific named places. Hence 0 image resolutions.

## Files

- error_log.csv: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- error-fixing-findings-latest.md: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
