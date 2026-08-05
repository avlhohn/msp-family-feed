# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-05 — finished 04:49 local.

## Summary

- Open queue at start: **54** rows (unresolved_website 13, unresolved_image 41).
- Resolved this run: **4** (website 1, image 3 — og_image 3, facebook 0, stock_openverse_specific 0).
- Left open (rolling to tomorrow): **50** (website 12, image 38).

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Alexandria Freedom Fun Run | image | image: og_image from event's own RunSignUp registration page (self-branded race banner), passed relevance filter — https://d368g9lw5ileu7.cloudfront.net/races/races-144xxx/144232/raceBanner-ItIqjzS9-bOBbC-.jpg |
| Captain's Quarters Craft Program - BoatHouse | image | image: og_image — event-specific promo graphic from Legacy of the Lakes Museum calendar (deep-link, self-branded) — https://legacyofthelakes.org/wp-content/uploads/2026/06/Captains-Quarters-2-232x300.png |
| Topgolf Monthly Membership | image | image: og_image — venue photo from Topgolf's own official gallery (self-branded, real venue photo not logo), passed relevance filter — https://s3.topgolf.com/gallery/51549/11355_1655926334_full.jpg |
| Mocha Momma's | website | website: https://mocha-mommas-coffee.menustic.com/ — verified venue-specific page for Mocha Momma's coffee (Minneapolis Central Library, 300 Nicollet Mall); exact name+city match |

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Maple Grove - Sounds of Summer Movie Night | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Maplewood Celebrate Summer | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Kelley Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Lake Ann Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Lily Lake Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Pine Tree Pond Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Sibley Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Staring Lake Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Wolfe Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Chapel Trail at St. John's University | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Lake Park (Winona) | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| East Lake Park Bandshell | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Alexandria City Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Kiwanis Park (Brainerd) | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Cottage Grove Ravine Regional Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Hamline Park | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Lum Park Recreation Area | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Cameron Park (Bemidji) | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Family Dance Party - Rochester Public Library | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Vadnais Heights Summer Concert Series | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Family Fun Night | website | ambiguous — generic title, multiple unrelated events |
| Captain's Quarters | website | ambiguous — multiple MN venues share the name |
| Badges & Bobbers Fishing Event - Lake George | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Niko Moon Concert - Vetter Stone Amphitheater | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Music in the Park Thursdays - Mankato | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Movies in the Park - Mankato | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Moorhead Summer Splash Event | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Winona Parks & Rec Summer Activities | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Winona Farmers Market | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Alexandria Saturday Art Market | image | og:image not extractable via WebFetch + no specific CC photo (Openverse rejected) |
| Urban Air Trampoline Parks - Minnesota Locations | image | only generic corporate/municipal image; no specific photo |
| Denny's Thursday Kids Eat Free | image | only generic corporate/municipal image; no specific photo |
| Perkins Tuesday Kids Eat Free | image | only generic corporate/municipal image; no specific photo |
| Rubio's Rewards Thursday Kids Free Meal | image | only generic corporate/municipal image; no specific photo |
| Bowlero Brooklyn Park (Lucky Strike) | image | venue photo referenced but no verifiable image URL extracted |
| Bowlocity Entertainment Center Rochester | image | only generic corporate/municipal image; no specific photo |
| 56 Brewing Minneapolis | image | only generic corporate/municipal image; no specific photo |
| Can Can Wonderland St. Paul | image | only generic corporate/municipal image; no specific photo |
| Minneapolis Parks Volunteer Programming | image | only generic corporate/municipal image; no specific photo |
| Mission Branch Library Community Garden - Monday Nights | image | item may not exist / no matching MN library branch found |
| Summer Outdoor Festival - Brainerd | website | no dedicated official website exists |
| Brainerd Fire Department Golf Scramble | website | no dedicated official website found |
| International Falls County Fair | website | no dedicated official website (county fair, no site) |
| Movies in the Park: Back to the Future (Maple Grove) | website | only a generic city homepage found, no event-specific page |
| Plymouth Summerfest | website | no event by this exact name found (Music in Plymouth differs) |
| Mighty Machines (Farmington) | website | no official website found |

## Diagnostics

- Base log loaded from local session copy; header (10-col schema) and row count validated OK — no `log_base_rejected`.
- Build's `run_summary` row for 2026-08-05 present — queue is current; no `no_run_summary_today`.
- Openverse: queried ~18 named parks/venues; all results rejected (generic/off-topic or no exact name-match in title/metadata) — 0 stock_openverse_specific resolutions.
- og:image extraction failed for most park/venue sites due to the known WebFetch `<head>`-stripping limitation and 403s — not proof images are absent; carried forward.
- No AI-ineligibility skips (no Drive fallback needed this run).

## Files

- error_log.csv: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- error-fixing-findings-latest.md: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
