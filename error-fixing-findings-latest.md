# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-02 — finished 04:53 local time.

## Summary

- Open queue at start: 65 rows (18 `unresolved_website` / 47 `unresolved_image`); 58 unique items (11 website / 47 image).
- Resolved this run: 8 rows across 7 unique items — website 1, image 6 (og_image 6, facebook 0, stock_openverse_specific 0).
- Left open: 57 rows rolling to tomorrow.

## Resolved this run

| Item | Type | Resolution note |
| --- | --- | --- |
| National Night Out / Night to Unite (Twin Cities Metro) | website | website: https://www.mncrimeprevention.com/night-to-unite — MN Crime Prevention Assoc. official Night to Unite page, exact event name match, statewide/Twin Cities metro |
| Columbia Park | image | image: og_image — official Minneapolis Parks Columbia Park page, venue-specific photo (columbia_park_archery1.jpg), passed relevance filter |
| Nowhere Entertainment Inver Grove Heights | image | image: og_image — self-branded image from venue's own website (nowhereentertainmentcenter.com attractions page) |
| Second Harvest Heartland Food Bank - Food Packing Shifts | image | image: og_image — banner from Second Harvest's own volunteer portal page, depicts food-packing, passed relevance filter |
| Bloomington Parks Adopt-A-Park Program | image | image: og_image — official City of Bloomington parks page, adopt-a-park volunteer photo (adoptkids.jpg) |
| Saint Paul Citywide Cleanup Volunteer Events | image | image: og_image — official City of Saint Paul citywide-cleanup page, event-specific photo, passed relevance filter |
| Garden School Foundation Community Garden Day | image | image: og_image — self-branded community-garden photo from foundation's own website hero |

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Family Fun Night | website | ambiguous — generic title, no specific organizer/venue |
| Captain's Quarters | website | ambiguous — multiple MN venues by this name, no single definitive site |
| Summer Outdoor Festival - Brainerd | website | not found — no event by this exact name confirmed |
| Brainerd Fire Department Golf Scramble | website | not found — no dedicated official site |
| Mocha Momma's | website | no dedicated site — only aggregator listings |
| International Falls County Fair | website | approximate only — Koochiching County Fair (Northome) is a geographic/name approximation, not an exact match |
| Movies in the Park: Back to the Future (Maple Grove) | website | too generic — only city homepage, no event-specific page |
| Plymouth Summerfest | website | name mismatch — official summer event is 'Music in Plymouth', not this |
| Kids Summer Craft Camp (Anoka) | website | ambiguous — multiple craft camps, no single organizer |
| Eden Prairie Free Outdoor Movie at Staring Lake | website | too generic — only city homepage, no event-specific page |
| Maple Grove - Sounds of Summer Movie Night | image | only aggregator/tourism/thematic image found — no specific image |
| Maplewood Celebrate Summer | image | Openverse returned only generic/unrelated photos — no name match |
| Kelley Park | image | Openverse returned only generic/unrelated photos — no name match |
| Lake Ann Park | image | Openverse returned only generic/unrelated photos — no name match |
| Lily Lake Park | image | Openverse returned only generic/unrelated photos — no name match |
| Pine Tree Pond Park | image | Openverse returned only generic/unrelated photos — no name match |
| Sibley Park | image | Openverse returned only generic/unrelated photos — no name match |
| Staring Lake Park | image | Openverse returned only generic/unrelated photos — no name match |
| Wolfe Park | image | Openverse returned only generic/unrelated photos — no name match |
| Chapel Trail at St. John's University | image | only aggregator/tourism/thematic image found — no specific image |
| Lake Park (Winona) | image | only aggregator/tourism/thematic image found — no specific image |
| East Lake Park Bandshell | image | Openverse returned only generic/unrelated photos — no name match |
| Alexandria City Park | image | Openverse returned only generic/unrelated photos — no name match |
| Kiwanis Park (Brainerd) | image | Openverse returned only generic/unrelated photos — no name match |
| Cottage Grove Ravine Regional Park | image | only aggregator/tourism/thematic image found — no specific image |
| Hamline Park | image | Openverse returned only generic/unrelated photos — no name match |
| Lum Park Recreation Area | image | only aggregator/tourism/thematic image found — no specific image |
| Cameron Park (Bemidji) | image | Openverse returned only generic/unrelated photos — no name match |
| Family Dance Party - Rochester Public Library | image | only aggregator/tourism/thematic image found — no specific image |
| Vadnais Heights Summer Concert Series | image | generic/chain/ambiguous — no specific image available |
| Badges & Bobbers Fishing Event - Lake George | image | generic/chain/ambiguous — no specific image available |
| Niko Moon Concert - Vetter Stone Amphitheater | image | generic/chain/ambiguous — no specific image available |
| Music in the Park Thursdays - Mankato | image | generic/chain/ambiguous — no specific image available |
| Movies in the Park - Mankato | image | generic/chain/ambiguous — no specific image available |
| Moorhead Summer Splash Event | image | generic/chain/ambiguous — no specific image available |
| Winona Parks & Rec Summer Activities | image | generic/chain/ambiguous — no specific image available |
| Winona Farmers Market | image | Openverse returned only generic/unrelated photos — no name match |
| Alexandria Freedom Fun Run | image | generic/chain/ambiguous — no specific image available |
| Alexandria Saturday Art Market | image | generic/chain/ambiguous — no specific image available |
| Captain's Quarters Craft Program - BoatHouse | image | generic/chain/ambiguous — no specific image available |

…and 11 more still open.

## Diagnostics

- `log_base_rejected`: none — base loaded from canonical GitHub `error_log.csv` (452 data rows, valid 10-col schema).
- `no_run_summary_today`: not triggered — build's run_summary for today was present.
- Publish: log committed to GitHub; content verified byte-identical to local (post-publish GET). One transient 409 during the retry loop (stale sha between the first PUT and its verify) — resolved on retry; final remote matches local.
- og:image tooling: many municipal/park sites returned 403 to WebFetch or had `<head>` stripped, so og:image was frequently invisible (a known tooling limit, not proof of absence). Aggregator/tourism og:images (TripAdvisor, Minnesota Parent, Visit St Cloud, Visit Saint Paul, Explore MN/Flickr) were demoted per the relevance filter and left open.
- Openverse fallback: queried for 21 place-specific candidates; 0 returned a strict name-match in image title/metadata (results were generic city/unrelated photos), so none resolved — correctly left open rather than assigning generic stock.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
