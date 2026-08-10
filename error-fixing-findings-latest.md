# MSP Family Guide - Error Fixing (Latest)

Run date: 2026-08-09 - finished 23:08 local.

## Summary

- Open queue at start: 16 `unresolved_website` rows + 32 `unresolved_image` rows (14 unique website items, 32 unique image items).
- Resolved this run: 5 items (2 website, 3 image; image split og_image=3/facebook=0/stock_openverse_specific=0).
- Left open (rolling to tomorrow): 12 website + 29 image = 41 items.

## Resolved this run

| Item | Type | Resolution note |
|------|------|-----------------|
| Moorhead Summer Splash Event | image | image: og_image from official Moorhead Parks & Rec page (moorheadmn.gov), event-specific pool photo, passed relevance filter - https://www.moorheadmn.gov/media/zh4fihhg/img_2461.jpg |
| Urban Air Trampoline Parks - Minnesota Locations | image | image: og_image - self-branded attraction photo from Urban Air's own official site (urbanair.com) - https://www.urbanair.com/images/UA_Climbing_4-min-3.jpg |
| Bowlocity Entertainment Center Rochester | image | image: og_image - venue-specific photo credited to Bowlocity (self-branded) - https://assets.simpleviewinc.com/simpleview/image/upload/crm/rochestermn/Credit-Bowlocity-d19b03a85056a36_d19b07c3-5056-a36a-09dd507a6c717b58.jpg |
| Plymouth Kids Fest | website | website: https://www.plymouthmn.gov/Home/Components/Calendar/Event/15514/18 - verified official City of Plymouth event page (Hilde Performance Center, Plymouth MN); name+city match |
| Heritage Day - Upsala | website | website: https://www.cityofupsala.com/copy-of-upsala-heritage-festival - verified official City of Upsala page for Upsala Heritage Days (Upsala, Morrison County MN); name+city match |

## Still open

| Item | Type | Likely reason |
|------|------|---------------|
| Maple Grove - Sounds of Summer Movie Night | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Maplewood Celebrate Summer | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Kelley Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Lake Ann Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Lily Lake Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Pine Tree Pond Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Chapel Trail at St. John's University | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| East Lake Park Bandshell | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Alexandria City Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Kiwanis Park (Brainerd) | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Cottage Grove Ravine Regional Park | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Lum Park Recreation Area | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Cameron Park (Bemidji) | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Family Dance Party - Rochester Public Library | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Vadnais Heights Summer Concert Series | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Family Fun Night | website | ambiguous - generic title, no city to disambiguate |
| Captain's Quarters | website | ambiguous - generic title, no specific venue |
| Badges & Bobbers Fishing Event - Lake George | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Music in the Park Thursdays - Mankato | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Movies in the Park - Mankato | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Winona Parks & Rec Summer Activities | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Winona Farmers Market | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Alexandria Saturday Art Market | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Denny's Thursday Kids Eat Free | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Perkins Tuesday Kids Eat Free | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Rubio's Rewards Thursday Kids Free Meal | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| 56 Brewing Minneapolis | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Minneapolis Parks Volunteer Programming | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Mission Branch Library Community Garden - Monday Nights | image | no specific photo found (og:image not extractable / only generic-or-recurring stock available) |
| Summer Outdoor Festival - Brainerd | website | no specific official site found |
| Brainerd Fire Department Golf Scramble | website | only a chamber events-calendar index (aggregator), no dedicated page |
| Plymouth Summerfest | website | low-confidence match (cultural-society event, weak name match) |
| Mighty Machines (Farmington) | website | could not confirm Farmington-specific page |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | no dedicated event page confirmed |
| Anoka Happy Days Festival | website | likely mislabeled (event is in Ramsey, not Anoka) |
| International Falls County Fair | website | no fair by this exact name (Koochiching County Fair differs) |
| Movies on the Island - Jumanji | website | event is in Superior WI, not MN |
| Movies on the Island - Mufasa | website | event is in Superior WI, not MN |

...and 1 more still open.

## Diagnostics

- No `log_base_rejected`: base (local == GitHub canonical, 743 rows, 10-col schema) validated.
- `run_summary` for 2026-08-09 present in base - no `no_run_summary_today` diagnostic.
- No AI-ineligibility skips (GitHub raw read succeeded; Drive fallback not triggered).
- Publish: see status recorded at run end.

## Files

- error_log.csv: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- error-fixing-findings-latest.md: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
