# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-16** — finished 08:44 

## Summary

Open queue at start: **38 rows** (16 `unresolved_website` / 22 `unresolved_image`), covering 37 unique items.

Resolved this run: **4 rows / 4 unique items** — website 4, image 0 (og_image 0, facebook 0, stock_openverse_specific 0).

Left open: **34 rows** (12 `unresolved_website` / 22 `unresolved_image`), rolling to tomorrow.

Five website candidates came back from the research pass; one was rejected on audit (a chamber-of-commerce `/events` calendar offered as an event page). The image queue produced zero resolutions: two Openverse passes across all 22 items returned only wrong-place or generic stock, and the og:image route was unavailable because the log does not carry source website URLs.

## Resolved this run

| Item | Type | Resolution note |
| --- | --- | --- |
| Tableside Magician & Balloon Artist - Kids Eat Free | website | `https://www.broadwaypizza.com/blaine/blaine` — official Broadway Pizza Blaine page names "Tableside Magician Every 1st Monday of the Month" and "Monday Family Night 5–7:30pm Kids Eat Free"; address 11822 Aberdeen St NE, Blaine MN 55449 matches the logged address exactly. |
| Movies on the Island - Jumanji | website | `https://www.dcdrugprevention.com/movies-on-the-island/` — organizer (Douglas County Drug Prevention Coalition) series page names the Jumanji screening at Barker's Island Festival Park. Same URL this log already accepted for the item on 2026-08-06. Venue is Superior WI — flagged for build-stage scope review. |
| Movies on the Island - Mufasa | website | `https://www.dcdrugprevention.com/movies-on-the-island/` — same organizer series page, names the Mufasa screening. Venue is Superior WI — flagged for build-stage scope review. |
| Movie Night on the Barn | website | `https://www.brooklynpark.org/event/movie-on-the-barn-a-minecraft-movie/` — official City of Brooklyn Park event page for the "Movie on the Barn" series at Historic Eidem Farm. **Data correction:** the venue is Brooklyn Park (4345 101st Ave N), not Coon Rapids as logged. |

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Maple Grove - Sounds of Summer Movie Night | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Maplewood Celebrate Summer | image | only venue-adjacent stock available (a Maplewood Community Center photo does not depict the named event) - rejected |
| Kelley Park | image | no specific image found - Openverse returns Kelley Park in San Jose CA only |
| Lake Ann Park | image | no specific image found - Openverse returns an Eckankar temple / UK garden photos, wrong place |
| Lily Lake Park | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Pine Tree Pond Park | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| East Lake Park Bandshell | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Lum Park Recreation Area | image | no specific image found - zero Openverse results across all query variants |
| Cameron Park (Bemidji) | image | no specific image found - Openverse returns Cameron Park Zoo in Waco TX only |
| Captain's Quarters | website | ambiguous - multiple MN/IL venues named Captain's Quarters, no event context to disambiguate |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific image found - zero Openverse results; venue site 403s on WebFetch |
| Music in the Park Thursdays - Mankato | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Movies in the Park - Mankato | image | only generic/topical stock available (Sibley Park algae and zoo peacock photos do not depict the event) - rejected |
| Moorhead Summer Splash Event | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Winona Parks & Rec Summer Activities | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Winona Farmers Market | image | no specific image found - zero Openverse results across all query variants |
| Urban Air Trampoline Parks - Minnesota Locations | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Denny's Thursday Kids Eat Free | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Perkins Tuesday Kids Eat Free | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Rubio's Rewards Thursday Kids Free Meal | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific image found - zero Openverse results across all query variants |
| Minneapolis Parks Volunteer Programming | image | no specific image found - 2 Openverse passes returned only wrong-place or generic/topical stock (rejected per strict bar); og:image path unavailable (no source website in log, WebFetch strips <head>) |
| Mission Branch Library Community Garden - Monday Nights | image | no specific image found - Openverse returns Mission Branch Library in San Francisco only |
| Summer Outdoor Festival - Brainerd | website | ambiguous - no event by this exact title exists in Brainerd (only Lakes Jam / Lakes Area Music Festival / Iconic Fest) |
| Brainerd Fire Department Golf Scramble | website | only a chamber-of-commerce /events calendar found (rejected on audit - not an event page) |
| Summer Outdoor Festival - Brainerd | website | ambiguous - no event by this exact title exists in Brainerd (only Lakes Jam / Lakes Area Music Festival / Iconic Fest) |
| Mighty Machines (Farmington) | website | not found - absent from Farmington city calendar and web search |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | unverified - stlouispark.org blocked (403); series exists at Fern Hill Park but this screening not confirmed on an official page |
| Maple Grove Sounds of Summer Movie - Ratatouille | website | unverified - series confirmed at Town Green but only a calendar-category page; PDF schedule inaccessible |
| Triangle Drive-In | website | no official site - business operates seasonally with Facebook only; all candidates were directory/aggregator listings |
| 371 Diner | website | no official site - Facebook presence only; all candidates were directory/aggregator listings |
| Pizza King Station | website | ambiguous/out-of-state - Pizza King Station locations found only in Indiana; no MN location confirmed |
| Toddler Tuesday - ECFE | website | unverified - Anoka-Hennepin ECFE site confirms the program area but never names 'Toddler Tuesday' |
| Bump & Putt Family Fun Center | website | address mismatch - Bump 'N' Putt Family Fun Park sits in Pequot Lakes, not 'four miles north of Nisswa'; no official site found |

## Diagnostics

- `no_run_summary_today` — **triggered, then superseded.** At base-load time (05:40) the GitHub log had no `run_summary` dated 2026-08-16 (the latest was 2026-08-13), so the fixer worked the pre-existing backlog. The daily build finished later, at ~08:43, and its 2026-08-16 rows merged into the file before the fixer published — no fixer resolutions were lost, and the published log contains both. The diagnostic row is retained (with corrected wording) because the ordering is worth seeing: today the fixer ran ahead of the build, so items the build logged today were never in the fixer's queue.
- Build's new open row — the one `unresolved_website` row the build added today is a category roll-up (`688 rows`, overwhelmingly municipal neighbourhood parks with no individual page), not a per-item work item, so it added nothing actionable to drain.
- `log_base_rejected` — none. The base validated cleanly: exact 10-column header, 927 data rows (monotonic growth vs. prior days), byte-identical to the local mount copy.
- og:image extraction — **structurally unavailable this run.** The error log carries no per-item source website URL, so there was no page to fetch for the image queue. The known WebFetch limitation (HTML→markdown conversion strips `<head>`, hiding `og:image`) applies regardless; two probes (Vetter Stone Amphitheater, Brooklyn Park Eidem) returned 403/404. The build independently logged the same blocker today as `ogimage_extraction_unavailable`.
- Openverse — queried unfiltered by license (per the prior finding that a commercial-license filter silently hides valid `by-nc` results). Two passes per item across all 22 items; place identity checked against result tags rather than titles. Zero place-specific matches.
- Publish — `error_log.csv` and this report both committed on attempt 1, verified by MD5 of the base64-decoded Contents-API response against local bytes (match). The log was re-published after the build merge and the diagnostic correction.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- This report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
