# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-07 — finished 04:53 CDT

## Summary

- Open queue at start: 48 unique items (10 `unresolved_website`, 38 `unresolved_image`).
- Resolved this run: 8 items — website 2, image 6 (og_image 1, facebook 0, stock_openverse_specific 5).
- Left open (rolling to tomorrow): 40 (8 website, 32 image).

## Resolved this run

| Item | Type | Resolution note |
|------|------|-----------------|
| Sibley Park | image | image: stock_openverse_specific — place-specific photo 'South Central Minnesota Pride 2008 at Sibley Park' (Mankato), name match in title, CC BY 2.0 (commons.wikimedia.org) |
| Staring Lake Park | image | image: stock_openverse_specific — place-specific Openverse/Flickr photo 'A Walk Around Staring Lake' (Eden Prairie), name match, CC BY-NC 2.0 (flickr.com) |
| Wolfe Park | image | image: stock_openverse_specific — place-specific Openverse/Flickr photo 'Morning on Wolfe Lake' (Wolfe Lake within Wolfe Park, St. Louis Park), name match, CC BY-NC-ND 2.0 (flickr.com) |
| Lake Park (Winona) | image | image: og_image — specific park-trail photo of Lake Park from visitwinona.com (lakeparkpatheastfallmf.jpg); depicts the named park path, not a generic banner |
| Hamline Park | image | image: stock_openverse_specific — place-specific photo 'Hamline Playground' (Hamline Park, St. Paul), name match, CC BY-SA 3.0 (commons.wikimedia.org) |
| Can Can Wonderland St. Paul | image | image: stock_openverse_specific — place-specific Openverse/Flickr photos titled 'Can Can Wonderland' tagged saintpaul/minnesota, name match, CC BY-NC-ND 2.0 (flickr.com) |
| International Falls County Fair | website | website: https://koochichingcountyfair.org/ — verified official county fair site (International Falls is the Koochiching county seat); name+dates match |
| Movies in the Park: Back to the Future (Maple Grove) | website | website: https://maplegrovemn.gov/Calendar.aspx?EID=1219 — verified official Maple Grove city calendar deep-link; event at Town Green Park |

## Still open

| Item | Type | Likely reason |
|------|------|---------------|
| Family Fun Night | website | ambiguous — title too generic, no city to disambiguate a specific venue |
| Captain's Quarters | website | ambiguous — multiple same-name venues, no MN venue confirmed |
| Summer Outdoor Festival - Brainerd | website | no official site found — no event by that exact name in Brainerd |
| Brainerd Fire Department Golf Scramble | website | only a generic chamber events-index listing (no dedicated event page) |
| Plymouth Summerfest | website | no official site found — Plymouth's summer event is 'Music in Plymouth', not 'Summerfest' |
| Mighty Machines (Farmington) | website | no official site found — event by this name not confirmed in Farmington, MN |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | no official site found — specific screening not confirmed in schedules |
| Anoka Happy Days Festival | website | city mismatch — only Ramsey (not Anoka) Happy Days Festival found |
| Maple Grove - Sounds of Summer Movie Night | image | only generic/topical stock or no specific image found |
| Maplewood Celebrate Summer | image | only generic/topical stock or no specific image found |
| Kelley Park | image | only generic/topical stock or no specific image found |
| Lake Ann Park | image | only generic/topical stock or no specific image found |
| Lily Lake Park | image | only generic/topical stock or no specific image found |
| Pine Tree Pond Park | image | only generic/topical stock or no specific image found |
| Chapel Trail at St. John's University | image | only generic/topical stock or no specific image found |
| East Lake Park Bandshell | image | only generic/topical stock or no specific image found |
| Alexandria City Park | image | only generic/topical stock or no specific image found |
| Kiwanis Park (Brainerd) | image | only generic/topical stock or no specific image found |
| Cottage Grove Ravine Regional Park | image | only generic/topical stock or no specific image found |
| Lum Park Recreation Area | image | only generic/topical stock or no specific image found |
| Cameron Park (Bemidji) | image | only generic/topical stock or no specific image found |
| Family Dance Party - Rochester Public Library | image | only generic/topical stock or no specific image found |
| Vadnais Heights Summer Concert Series | image | only generic/topical stock or no specific image found |
| Badges & Bobbers Fishing Event - Lake George | image | only generic/topical stock or no specific image found |
| Niko Moon Concert - Vetter Stone Amphitheater | image | only generic/topical stock or no specific image found |
| Music in the Park Thursdays - Mankato | image | only generic/topical stock or no specific image found |
| Movies in the Park - Mankato | image | only generic/topical stock or no specific image found |
| Moorhead Summer Splash Event | image | only generic/topical stock or no specific image found |
| Winona Parks & Rec Summer Activities | image | only generic/topical stock or no specific image found |
| Winona Farmers Market | image | only generic/topical stock or no specific image found |
| Alexandria Saturday Art Market | image | only generic/topical stock or no specific image found |
| Urban Air Trampoline Parks - Minnesota Locations | image | only generic/topical stock or no specific image found |
| Denny's Thursday Kids Eat Free | image | only generic/topical stock or no specific image found |
| Perkins Tuesday Kids Eat Free | image | only generic/topical stock or no specific image found |
| Rubio's Rewards Thursday Kids Free Meal | image | only generic/topical stock or no specific image found |
| Bowlero Brooklyn Park (Lucky Strike) | image | only generic/topical stock or no specific image found |
| Bowlocity Entertainment Center Rochester | image | only generic/topical stock or no specific image found |
| 56 Brewing Minneapolis | image | only generic/topical stock or no specific image found |
| Minneapolis Parks Volunteer Programming | image | only generic/topical stock or no specific image found |
| Mission Branch Library Community Garden - Monday Nights | image | only generic/topical stock or no specific image found |

## Diagnostics

- Base log loaded from GitHub (`error_log.csv`); header valid (10-column schema) and row count plausible (690 base rows) — no `log_base_rejected`.
- `run_summary` row for 2026-08-07 present — build ran; no `no_run_summary_today` diagnostic.
- Log publish to GitHub: succeeded on attempt 1; post-publish verify passed (remote size 195,887 B matches local; sha changed 7e46991669→18a4600f6a).

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
