# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-09 · finished ~00:09 CDT local time

## Summary

Open queue at start: 48 open rows — 16 `unresolved_website` + 32 `unresolved_image` (14 unique website items, 32 unique image items after de-duplication).

Resolved this run: 0 total (website=0, image=0 [og_image=0, facebook=0, stock_openverse_specific=0]).

Left open: 48 (16 website + 32 image), rolling to tomorrow.

Every open item received a second, unhurried attempt (6 parallel subagents for website verification and og:image/Facebook extraction, plus a full Openverse API pass run by the main task). Nothing cleared the strict "confident, specific match" bar this run, so the log stays trustworthy and the queue rolls forward intact.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Family Fun Night | website | ambiguous — title too generic to pin a specific venue |
| Captain's Quarters | website | ambiguous — multiple MN venues share the name |
| Summer Outdoor Festival - Brainerd | website | ambiguous — only candidate (Lakes Area Music Festival) is a name-mismatch guess |
| Brainerd Fire Department Golf Scramble | website | no dedicated site — event real but only on a blocked city domain |
| Plymouth Summerfest | website | ambiguous — no official page under this exact name |
| Mighty Machines (Farmington) | website | only a generic Dakota County Library kids-programs page, not event-specific |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | no event-specific page; city calendar access blocked |
| Anoka Happy Days Festival | website | name mismatch — nearest match is "Ramsey Happy Days," different city |
| International Falls County Fair | website | title/city mismatch — nearest is Koochiching County Fair, Northome |
| Movies on the Island - Jumanji | website | out of state — nearest match is Superior, WI |
| Movies on the Island - Mufasa | website | out of state — nearest match is Superior, WI |
| Plymouth Kids Fest | website | only a generic Plymouth Parks & Rec department page, not event-specific |
| Heritage Day - Upsala | website | no dedicated site; city site lacks an event page |
| Family Night on the Farm | website | ambiguous — recurring event across locations, no single official site |
| Maple Grove - Sounds of Summer Movie Night | image | og:image not extractable via WebFetch (\<head\> stripped) |
| Maplewood Celebrate Summer | image | og:image not extractable via WebFetch |
| Kelley Park | image | no specific image — Openverse "Kelley Park" hits are San Jose CA, wrong place |
| Lake Ann Park | image | og:image not extractable (site returned 403); no specific image found |
| Lily Lake Park | image | og:image not extractable (site returned 403) |
| Pine Tree Pond Park | image | og:image not extractable via WebFetch |
| Chapel Trail at St. John's University | image | og:image not extractable (site returned 403) |
| East Lake Park Bandshell | image | only a tourism-bureau (Visit Winona) image, not a self-branded own-page og:image |
| Alexandria City Park | image | no specific image — Openverse "Alexandria city park" hit is Alexandria VA, wrong place |
| Kiwanis Park (Brainerd) | image | og:image not extractable via WebFetch |
| Cottage Grove Ravine Regional Park | image | og:image not present; no specific CC image found |
| Lum Park Recreation Area | image | og:image not present; no specific CC image found |
| Cameron Park (Bemidji) | image | og:image not present; no specific CC image found |
| Family Dance Party - Rochester Public Library | image | only generic disco-ball stock; nothing event-specific |
| Vadnais Heights Summer Concert Series | image | og:image not extractable; no specific image found |
| Badges & Bobbers Fishing Event - Lake George | image | og:image not extractable via WebFetch |
| Niko Moon Concert - Vetter Stone Amphitheater | image | og:image not extractable; no accessible own-page Facebook photo |
| Music in the Park Thursdays - Mankato | image | og:image not extractable via WebFetch |
| Movies in the Park - Mankato | image | og:image not extractable via WebFetch |
| Moorhead Summer Splash Event | image | og:image not extractable via WebFetch |
| Winona Parks & Rec Summer Activities | image | og:image not extractable; city-wide page (generic anyway) |
| Winona Farmers Market | image | og:image not extractable; no accessible own-page Facebook photo |
| Alexandria Saturday Art Market | image | og:image not extractable via WebFetch |
| Urban Air Trampoline Parks - Minnesota Locations | image | corporate multi-location page; no place-specific image |
| Denny's Thursday Kids Eat Free | image | og:image not extractable (403); national chain, no place-specific image |
| Perkins Tuesday Kids Eat Free | image | og:image not extractable via WebFetch |
| Rubio's Rewards Thursday Kids Free Meal | image | og:image not extractable via WebFetch |
| Bowlero Brooklyn Park (Lucky Strike) | image | og:image not extractable via WebFetch |
| Bowlocity Entertainment Center Rochester | image | og:image not extractable; only a logo found |
| 56 Brewing Minneapolis | image | og:image not extractable via WebFetch |
| Minneapolis Parks Volunteer Programming | image | og:image not extractable; city-wide page (generic anyway) |
| Mission Branch Library Community Garden - Monday Nights | image | source questionable — no "Mission Branch" in Hennepin County Library system |

## Diagnostics

- `no_run_summary_today`: no `run_summary` row dated 2026-08-09 was present in the loaded base — the daily build has not yet published today. Proceeded on the carried-forward open queue (logged as an info/pipeline row).
- `log_base_rejected`: none. The GitHub canonical `error_log.csv` (730 rows incl. header, 10-column schema) passed both header and row-count validation and was used as the base.
- Openverse false positives caught: "Kelley Park" (San Jose, CA) and "Alexandria city park" (Alexandria, VA) were the only exact name-token matches returned but are wrong-city collisions — correctly rejected under the exact-place bar.
- Publish: `error_log.csv` and this findings report committed to GitHub via the contents API (see below).

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
