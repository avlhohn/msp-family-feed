# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-10 — finished 23:20 

## Summary

- Open queue at start: 16 `unresolved_website` rows (14 unique) + 32 `unresolved_image` rows (32 unique).
- Resolved this run: **3 total** — 3 website, 0 image (og_image 0 / facebook 0 / stock_openverse_specific 0).
- Left open (rolling to next run): 11 unique website + 32 unique image items.

## Resolved this run

| Item | Type | Resolution note |
|------|------|-----------------|
| Plymouth Kids Fest | website | website: https://www.plymouthmn.gov/Home/Components/News/News/4141/ — official City of Plymouth page names Kids Fest (Aug 20 2026, Hilde Performance Center) |
| Family Night on the Farm | website | website: https://visitwinona.com/events/family-night-on-the-farm-barkheim-farms/ — official Visit Winona event page, Barkheim Farms, Lewiston MN |
| International Falls County Fair | website | website: https://www.koochichingcountyfair.org/ — official Koochiching County Fair (county seat International Falls) |

## Still open

| Item | Type | Likely reason |
|------|------|---------------|
| Family Fun Night | website | ambiguous — title too generic to disambiguate a specific venue/event |
| Captain's Quarters | website | ambiguous — multiple MN venues share this name, no specific family event page |
| Summer Outdoor Festival - Brainerd | website | no specific official site found; no Brainerd festival by this exact name |
| Brainerd Fire Department Golf Scramble | website | only a chamber-of-commerce events-index listing found (rotating URL, not a stable dedicated page) |
| Plymouth Summerfest | website | no event by this exact name on city site (Plymouth's signature summer event is 'Music in Plymouth') |
| Mighty Machines (Farmington) | website | no Farmington-specific event page found |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | only a low-confidence 'appears to be' calendar entry — not confidently this exact film screening |
| Anoka Happy Days Festival | website | candidate page was City of Ramsey (different city) — name/city mismatch, left open |
| Movies on the Island - Jumanji | website | event is in Superior, WISCONSIN (out of MN scope) |
| Movies on the Island - Mufasa | website | event is in Superior, WISCONSIN (out of MN scope) |
| Heritage Day - Upsala | website | only a generic city calendar-index page ('copy-of-calendar-of-events', unstable URL), no dedicated event page |
| Maple Grove - Sounds of Summer Movie Night | image | event — only generic/topical stock available; og:image non-functional |
| Maplewood Celebrate Summer | image | event — only generic/topical stock available; og:image non-functional |
| Kelley Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Lake Ann Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Lily Lake Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Pine Tree Pond Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Chapel Trail at St. John's University | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| East Lake Park Bandshell | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Alexandria City Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Kiwanis Park (Brainerd) | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Cottage Grove Ravine Regional Park | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Lum Park Recreation Area | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Cameron Park (Bemidji) | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Family Dance Party - Rochester Public Library | image | generic/topical — no place-specific CC image available; og:image non-functional |
| Vadnais Heights Summer Concert Series | image | event — only generic/topical stock available; og:image non-functional |
| Badges & Bobbers Fishing Event - Lake George | image | park/venue — Openverse returned 0 place-specific matches (or off-topic/NC-only); og:image non-functional |
| Niko Moon Concert - Vetter Stone Amphitheater | image | event — only generic/topical stock available; og:image non-functional |
| Music in the Park Thursdays - Mankato | image | event — only generic/topical stock available; og:image non-functional |
| Movies in the Park - Mankato | image | event — only generic/topical stock available; og:image non-functional |
| Moorhead Summer Splash Event | image | event — only generic/topical stock available; og:image non-functional |
| Winona Parks & Rec Summer Activities | image | generic/topical — no place-specific CC image available; og:image non-functional |
| Winona Farmers Market | image | generic/topical — no place-specific CC image available; og:image non-functional |
| Alexandria Saturday Art Market | image | generic/topical — no place-specific CC image available; og:image non-functional |
| Urban Air Trampoline Parks - Minnesota Locations | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Denny's Thursday Kids Eat Free | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Perkins Tuesday Kids Eat Free | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Rubio's Rewards Thursday Kids Free Meal | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Bowlero Brooklyn Park (Lucky Strike) | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Bowlocity Entertainment Center Rochester | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| 56 Brewing Minneapolis | image | chain/deal listing — no place-specific CC image; og:image extraction non-functional |
| Minneapolis Parks Volunteer Programming | image | generic/topical — no place-specific CC image available; og:image non-functional |
| Mission Branch Library Community Garden - Monday Nights | image | generic/topical — no place-specific CC image available; og:image non-functional |

## Diagnostics

- `no_run_summary_today`: no build `run_summary` row dated 2026-08-10 was present at fixer load (latest build run_date was 2026-08-09). Proceeded on the carried-forward open queue.
- og:image extraction remains structurally non-functional this run (WebFetch converts HTML→markdown and strips `<head>`, so `og:image` meta tags are unreadable; raw HTTP fetches are policy-blocked). Image rows with websites could not be upgraded via og:image.
- Openverse yielded no valid place-specific resolutions: exact park queries returned 0 results; the few hits were off-topic (Alexandria 'City Park' → I-94 highway photos; 'Lake George' → George Floyd protest photos) or lacked a verifiable name match in title/tags and were NonCommercial-licensed (Cottage Grove Ravine Regional Park photoset).
- No `log_base_rejected`. Base loaded from local mount (identical to GitHub raw, 210054 bytes, 10-column header, 742 data rows — validation passed).
- No publish retries/failures at report-write time (see run summary for final publish status).

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
