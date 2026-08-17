# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-17** — finished 07:08 CDT (America/Chicago).

## Summary

Open queue at start: **35 rows** covering 34 unique items — 13 `unresolved_website` (12 unique) and 22 `unresolved_image` (22 unique).

Resolved this run: **3 rows / 3 unique items** — all 3 website. Images resolved: 0 (og_image 0, facebook 0, stock_openverse_specific 0).

Left open, rolling to tomorrow: **32 rows** — 10 `unresolved_website`, 22 `unresolved_image`.

Five website candidates came back from the parallel subagents; audit cut them to three. The rejected two were an aggregator event page offered as an official source and an unverifiable city fire-department landing page, and a third candidate (a `brainerd.com/business/...` directory listing) was replaced with the venue's own Facebook page rather than accepted as given. The image queue produced nothing: 22 items across up to five Openverse query passes each returned only wrong-place namesakes or city-level generics, none of which clear the place-specific bar.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| Maple Grove Sounds of Summer Movie - Ratatouille | unresolved_website | website: https://maplegrovemn.gov/672/Town-Green - official City of Maple Grove Town Green page; names the 'Sounds of Summer' series of free concerts and movies in the park and lists 7991 Main Street, matching the item address (individual movie titles live in the linked 2026 Sounds of Summer PDF) |
| Triangle Drive-In | unresolved_website | website: https://www.facebook.com/TriangleDriveInnTreatsllc - venue's own Facebook business page, title 'Triangle Drive Inn & Treats LLC / Brainerd MN'; 714 Mill Ave, Brainerd confirmed across independent listings, matching item address (no standalone domain exists) |
| 371 Diner | unresolved_website | website: https://www.facebook.com/371diner/ - venue's own Facebook business page, page title '371 Diner Baxter / Baxter MN'; name + city match to item address (14901 Edgewood Dr, Baxter, MN) |

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Maple Grove - Sounds of Summer Movie Night | unresolved_image | only generic-or-wrong-place stock - Maple Grove hits are a county boundary map, a Costco food court, and a Kansas cemetery headstone |
| Maplewood Celebrate Summer | unresolved_image | no specific image found - nearest MN hit is a rainy-night photo of the Maplewood Community Center, which is not a name match for this event |
| Kelley Park | unresolved_image | only generic-or-wrong-place stock - all Openverse hits are Kelley Park in San Jose, CA |
| Lake Ann Park | unresolved_image | only generic-or-wrong-place stock - hits are Chippenham Park (England), Central Park NY, and a Mora MN townscape |
| Lily Lake Park | unresolved_image | only generic-or-wrong-place stock - hits are lily-pond botanicals plus the Lily Pond Pothole at Interstate State Park, Taylors Falls (wrong place) |
| Pine Tree Pond Park | unresolved_image | only generic-or-wrong-place stock - best MN hit is the Como Ordway Japanese Garden, a different park |
| East Lake Park Bandshell | unresolved_image | no specific image found - single hit is the Jay Pritzker Pavilion in Chicago |
| Lum Park Recreation Area | unresolved_image | no specific image found - zero Openverse results across all query passes |
| Cameron Park (Bemidji) | unresolved_image | no specific image found - single hit is a Grand Canyon photo |
| Captain's Quarters | unresolved_website | ambiguous - every match is the Captain's Quarters Marina in Antioch, ILLINOIS; no MN venue of this name found |
| Niko Moon Concert - Vetter Stone Amphitheater | unresolved_image | no specific image found - zero Openverse results for the performer or the amphitheater |
| Music in the Park Thursdays - Mankato | unresolved_image | no specific image found - Sibley Park Mankato hits exist (algae, a peacock) but neither depicts the concert series and the venue is unconfirmed |
| Movies in the Park - Mankato | unresolved_image | no specific image found - Mankato hits are Reconciliation Park sculpture and Minneopa State Park, both wrong places |
| Moorhead Summer Splash Event | unresolved_image | no specific image found - zero Openverse results across all query passes |
| Winona Parks & Rec Summer Activities | unresolved_image | only generic-or-wrong-place stock - item is a city-wide program roll-up with no single depictable place; Winona hits are a lemonade stand and a Farmers Park merry-go-round |
| Winona Farmers Market | unresolved_image | no specific image found - zero Openverse results across all query passes |
| Urban Air Trampoline Parks - Minnesota Locations | unresolved_image | only generic-or-wrong-place stock - hits are trampoline parks in Memphis, San Francisco and Chandler AZ; item is a multi-location roll-up |
| Denny's Thursday Kids Eat Free | unresolved_image | no specific image found - a recurring national meal deal has no depictable specific place; zero Openverse results |
| Perkins Tuesday Kids Eat Free | unresolved_image | no specific image found - a recurring national meal deal has no depictable specific place; zero Openverse results |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | no specific image found - a recurring national meal deal has no depictable specific place; zero Openverse results |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | no specific image found - zero Openverse results for Bowlero or Lucky Strike in Brooklyn Park |
| Minneapolis Parks Volunteer Programming | unresolved_image | only generic-or-wrong-place stock - hits are unrelated Minneapolis arts/theatre photos; item is a program roll-up with no single place |
| Mission Branch Library Community Garden - Monday Nights | unresolved_image | only generic-or-wrong-place stock - hits are the Mission Branch of the SAN FRANCISCO Public Library and the Glencarlyn Library garden in Virginia |
| Summer Outdoor Festival - Brainerd | unresolved_website | ambiguous - Brainerd has named festivals (Lakes Area Music Festival, Lakes Jam, Iconic Fest) but nothing specifically named "Summer Outdoor Festival" |
| Brainerd Fire Department Golf Scramble | unresolved_website | no event page - only a Brainerd Lakes Chamber events calendar (rejected pattern) and the department's own landing page, which 403'd and does not name the scramble |
| Mighty Machines (Farmington) | unresolved_website | no specific page - Mighty Machines programs exist in other MN cities, but Farmington Parks & Rec never names it |
| St. Louis Park Outdoor Movie - A Minecraft Movie | unresolved_website | no specific page - the city runs Movies in the Park (calendar pages exist for Sonic 3, Inside Out 2) but none names the Minecraft screening; the familyfuntwincities.com aggregator page was rejected |
| Pizza King Station | unresolved_website | ambiguous - no MN venue found; matches are Pizza King Station in Indianapolis IN and Pizza Kings in SD/NY/MI |
| Toddler Tuesday - ECFE | unresolved_website | no specific page - only generic Anoka-Hennepin ECFE program landing pages; the item address (10 Coon Rapids Blvd) also conflicts with the actual Coon Rapids Family Place location |
| Bump & Putt Family Fun Center | unresolved_website | closed-or-no-site - identity confirmed as Bump 'N' Putt Family Fun Park, 29107 State Hwy 371, Pequot Lakes, but only directory listings exist; no official site or own Facebook page |
| 688 rows | unresolved_website | not actionable - this is a build-stage category roll-up row (parks 657, events 14, volunteer 9, restaurants 6), not a per-item work row |

## Diagnostics

**`no_run_summary_today` — triggered.** The base loaded at 06:38 CDT contained no `run_summary` row dated 2026-08-17 (latest build `run_date` was 2026-08-16), so the daily build had not yet published its end-of-run marker when this stage started. Logged as an `info` `pipeline` row and the carried-forward backlog was worked as normal. This is the same start-before-build ordering seen on 2026-08-16, when the build finished around 08:43; if the build lands later today it will carry this file forward as its base.

**`log_base_rejected` — none.** The base fetched from the GitHub canonical raw URL had the exact 10-column header and 963 data rows, up monotonically from the prior copies, and was byte-identical (md5 `94b74d36…`) to the local mount copy. No Drive fallback was needed and no copy was skipped for AI-ineligibility.

**og:image extraction — not used as a primary route.** `WebFetch` renders pages to markdown and strips `<head>`, so `og:image` meta tags are structurally unreadable, and raw HTTP page fetches are policy-blocked. Image work therefore went straight to the Openverse API, which is the documented fallback. This is a tooling limitation, not evidence that the images are absent.

**Openverse licence filtering — left off deliberately.** Queries were run unfiltered rather than with `license_type=all-cc,commercial`, which silently hides `by-nc`/`by-nc-sa` results. It made no difference this run, since no result passed the place-specificity check regardless.

**Item `688 rows` — not actionable.** This `unresolved_website` row is a build-stage category roll-up (parks 657, events 14, volunteer_opportunities 9, restaurants 6), not a per-item work item. It stays open because there is no single website to find for it.

**Publish** — see below; both files committed and verified by content MD5 against the local bytes.

## Files

- Updated error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- This report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
