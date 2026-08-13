# MSP Family Guide - Error Fixing (Latest)

Run date: 2026-08-13 - finished 00:56 local

## Summary

Open queue at start: 45 rows (13 unresolved_website / 32 unresolved_image), covering 11 unique website items and 32 unique image items.

Resolved this run: 10 rows across 9 items - website 3 rows (2 items); image 7 rows (7 items: og_image 1, facebook 6, stock_openverse_specific 0).

Left open: 35 rows rolling to tomorrow.

## Resolved this run

| Item | Type | Resolution note |
| --- | --- | --- |
| Heritage Day - Upsala | website | website: cityofupsala.com calendar - official City of Upsala site names the event |
| Plymouth Summerfest | website | website: plymouthmn.gov Parks & Rec events - official city page hosts Summerfest |
| Vadnais Heights Summer Concert Series | image (og_image) | og_image from official Music-in-the-Park page - self-branded event photo |
| Alexandria City Park | image (facebook) | facebook - venue's own page photo |
| Kiwanis Park (Brainerd) | image (facebook) | facebook - venue's own page photo |
| Cottage Grove Ravine Regional Park | image (facebook) | facebook - park's own page photo |
| Alexandria Saturday Art Market | image (facebook) | facebook - event's own page photo |
| Bowlocity Entertainment Center Rochester | image (facebook) | facebook - venue's own page photo |
| 56 Brewing Minneapolis | image (facebook) | facebook - brewery's own page photo |

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Maple Grove - Sounds of Summer Movie Night | image | og present but image URL not extractable (tooling) |
| Maplewood Celebrate Summer | image | no specific event image found |
| Kelley Park | image | no specific image; Openverse returned off-topic results |
| Lake Ann Park | image | only city parks-dept umbrella FB page, not venue-specific |
| Lily Lake Park | image | only a Friends-of advocacy page, not the venue's own |
| Pine Tree Pond Park | image | no specific image found |
| Chapel Trail at St. John's University | image | only umbrella Outdoor-U page, not trail-specific |
| East Lake Park Bandshell | image | search conflates with Lake Harriet Bandshell; unverified |
| Lum Park Recreation Area | image | no specific image found (og stripped by tooling) |
| Cameron Park (Bemidji) | image | no specific image; only tourism-site branding |
| Family Dance Party - Rochester Public Library | image | only generic/aggregator (disco-ball) imagery available |
| Family Fun Night | website | ambiguous - generic name used across many MN venues |
| Captain's Quarters | website | ambiguous - no confident MN venue match |
| Badges & Bobbers Fishing Event - Lake George | image | no specific event photo available |
| Niko Moon Concert - Vetter Stone Amphitheater | image | only copyrighted artist promo; venue site blocked |
| Music in the Park Thursdays - Mankato | image | event image present but URL not extractable (tooling) |
| Movies in the Park - Mankato | image | event image present but URL not extractable (tooling) |
| Moorhead Summer Splash Event | image | event page 404; no image extractable |
| Winona Parks & Rec Summer Activities | image | umbrella program page, not event-specific |
| Winona Farmers Market | image | only a header logo available (rejected per filter) |
| Urban Air Trampoline Parks - Minnesota Locations | image | chain umbrella item; only a single-location page |
| Denny's Thursday Kids Eat Free | image | national chain promo; only generic chain branding |
| Perkins Tuesday Kids Eat Free | image | national chain promo; only generic chain branding |
| Rubio's Rewards Thursday Kids Free Meal | image | no MN locations exist; chain promo only |
| Bowlero Brooklyn Park (Lucky Strike) | image | only generic chain hero image reused across locations |
| Minneapolis Parks Volunteer Programming | image | no specific image found |
| Mission Branch Library Community Garden - Monday Nights | image | no specific image found |
| Summer Outdoor Festival - Brainerd | website | ambiguous - no single festival confirmed |
| Brainerd Fire Department Golf Scramble | website | only third-party chamber calendar found, no authoritative page |
| Mighty Machines (Farmington) | website | closed-or-broken / no specific Farmington event page found |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | no specific screening page; only generic 'Movies in the Parks' |
| Anoka Happy Days Festival | website | name/location mismatch (event appears to be Ramsey, MN) |
| Movies on the Island - Jumanji | website | no specific screening page confirmed |
| Movies on the Island - Mufasa | website | no specific screening page confirmed |

## Diagnostics

- `no_run_summary_today`: no run_summary row dated 2026-08-13 in the base at fixer start (latest was 2026-08-12); today's build had not published yet. Proceeded on the existing open queue; logged as an info/pipeline row.

- `log_base_rejected`: none - GitHub base validated (10-col schema, 797 rows, matched local copy).

- Openverse: queried 11 place-specific park/venue items; zero returned a verifiable name-match (results were off-topic, e.g. Interstate-94 and Como-garden photos), so none resolved via stock_openverse_specific.

- Publish: error_log.csv committed and verified on attempt 1 (gh_size 224712 = local, sha changed).

## Files

- error_log.csv: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- error-fixing-findings-latest.md: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
