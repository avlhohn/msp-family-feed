# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-08-15 (finished 04:5x local time)

## Summary

- Open queue at start: **54 rows** (31 `unresolved_website` / 23 `unresolved_image`), covering 53 unique items.
- Resolved this run: **16 rows / 16 unique items** — website 15, image 1 (og_image 0, facebook 0, stock_openverse_specific 1).
- Left open: **38 rows** (16 website / 22 image), rolling to tomorrow.

The image queue remains structurally hard to drain: `og:image` extraction is non-functional (WebFetch converts pages to markdown and strips `<head>`, and raw HTTP page fetches are policy-blocked), so image work went straight to the Openverse API. Twenty-three unique image items across roughly three query passes each produced exactly one verified place-specific name match; everything else came back city-level, wrong-place, or generic/recurring stock and was correctly left open rather than force-closed.

Website subagent output was audited before anything was written to the log. Three parallel subagents returned 19 resolution candidates; 4 failed the strict bar on review and were rejected — a third-party business directory listing offered as an official site, a performer's Facebook page offered as an event site, a city homepage that does not mention the event, and a district program page that names neither the event nor its location.

## Resolved this run

| Item | Type | Resolution note |
| --- | --- | --- |
| Afton Apple Orchard - Corn Maze & Fall Festival | unresolved_website | website: https://www.aftonapple.com/fall-fun - orchard's own site; Fall Fun/Corn Maze pages confirmed, Afton Apple Orchard, Hastings MN |
| Andale Taqueria y Mercado | unresolved_website | website: https://andaletaqueriaymercado.com/ - restaurant's own site, verified name + 7700 Nicollet Ave S, Richfield MN |
| Hmong Village | unresolved_website | website: https://www.hmongvillage-mn.com/ - venue's own site, verified name + 1001 Johnson Pkwy, St. Paul MN |
| Hmongtown Marketplace | unresolved_website | website: https://hmongtownmarketplace.com/ - venue's own site, verified 217 Como Ave Ste 2-100, St. Paul MN |
| Mama Safia's Kitchen | unresolved_website | website: https://www.mamasafiakitchen.com/ - restaurant's own site, verified name + 720 E Lake St, Minneapolis MN |
| Animales BBQ | unresolved_website | website: https://animalesbbq.com/ - restaurant's own site, verified 241 Fremont Ave N, Minneapolis MN (Harrison) |
| Hen House Eatery | unresolved_website | website: https://www.henhouseeatery.com/ - restaurant's own site, verified 114 S 8th St, Minneapolis MN 55402 |
| Nowhere Entertainment | unresolved_website | website: https://www.nowhereentertainmentcenter.com/ - venue's own site, verified 5300 S Robert Trail, Inver Grove Heights MN 55077 |
| Adventure Zone | unresolved_website | website: https://www.adventurezoneduluth.com/ - venue's own site, verified 329 S Lake Ave, Canal Park, Duluth MN 55802 |
| Skatin' Place | unresolved_website | website: https://saintcloudskatinplace.com/ - venue's own site, verified 3302 Southway Dr, St Cloud MN 56301 |
| Choo Choo Restaurant and Bar | unresolved_website | website: https://www.choochooloretto.com/ - venue's own site, verified 160 W Railway St, Loretto MN 55357 |
| Minnesota Transportation Museum Pizza Train | unresolved_website | website: https://trainride.org/ - MTM's own site; Pizza Train named and described as one of its rides |
| Honored 2 Help Back 2 School BBQ | unresolved_website | website: https://www.honored2help.org/ - host org's own site (Honored 2 Help, Brooklyn Park MN) with its Free BBQ program section |
| St. Tim's Carnival | unresolved_website | website: https://churchofsttimothy.com/ - host parish's own site, verified Church of St. Timothy, 707 89th Ave NE, Blaine MN; annual carnival |
| Back-to-School Kids Day | unresolved_website | website: https://realsportscards.com/ - host venue's own site, Real Sportscards, Blaine MN location confirmed |
| Chapel Trail at St. John's University | unresolved_image | image: stock_openverse_specific - place-specific Openverse photo 'Stella Maris Chapel' (the chapel the Chapel Trail leads to at Saint John's University); name match verified in image metadata tags sju/saint/johns/stella/maris/chapel/minnesota; CC BY-NC-SA 2.0; https://live.staticflickr.com/2451/3654637380_a62436dc96_b.jpg |

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Maple Grove - Sounds of Summer Movie Night | unresolved_image | no specific image found - Openverse returns Elm Creek Park Reserve and unrelated Maple Grove photos |
| Maplewood Celebrate Summer | unresolved_image | wrong-place stock only - Openverse returns Maplewood State Park (Otter Tail County), not Maplewood city |
| Kelley Park | unresolved_image | no specific image found - Openverse returns zero results for Kelley Park, Apple Valley |
| Lake Ann Park | unresolved_image | wrong-place stock only - Openverse returns an Eckankar temple photo, not the Chanhassen park |
| Lily Lake Park | unresolved_image | generic stock only - Openverse returns water-lily botanical photos, not the Stillwater park |
| Pine Tree Pond Park | unresolved_image | generic stock only - Openverse returns unrelated pond photos |
| East Lake Park Bandshell | unresolved_image | no specific image found - Openverse returns zero results for the bandshell |
| Lum Park Recreation Area | unresolved_image | wrong-place stock only - Openverse returns Crow Wing State Park, a different Brainerd-area park |
| Cameron Park (Bemidji) | unresolved_image | wrong-place stock only - Openverse returns Lake Bemidji / BSU photos, not the park |
| Captain's Quarters | unresolved_website | ambiguous - multiple MN venues share the name, no single specific match |
| Niko Moon Concert - Vetter Stone Amphitheater | unresolved_image | no specific image found - Openverse returns zero results for the amphitheater |
| Music in the Park Thursdays - Mankato | unresolved_image | generic/city-level stock only - Reconciliation Park and Minneopa State Park, not the event |
| Movies in the Park - Mankato | unresolved_image | generic/city-level stock only - Mankato landmarks, not the event |
| Moorhead Summer Splash Event | unresolved_image | wrong-place stock only - best hits are Fargo ND pools and parks |
| Winona Parks & Rec Summer Activities | unresolved_image | generic/city-level stock only - vintage postcards and wildlife photos |
| Winona Farmers Market | unresolved_image | no specific image found - Openverse returns a school building and a city postcard |
| Urban Air Trampoline Parks - Minnesota Locations | unresolved_image | wrong-place stock only - only Openverse hit is the Tallahassee FL location |
| Denny's Thursday Kids Eat Free | unresolved_image | generic/recurring stock only - chain-wide deal; best Openverse hit is an unrelated protest photo |
| Perkins Tuesday Kids Eat Free | unresolved_image | generic/recurring stock only - chain-wide deal, no place-specific photo |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | generic/recurring stock only - Openverse hits are Miami and Spain locations |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | wrong-place stock only - Openverse hits are Bowlero NYC and Bethesda MD |
| Minneapolis Parks Volunteer Programming | unresolved_image | generic/topical stock only - org-level and city-level images, nothing depicting the program |
| Mission Branch Library Community Garden - Monday Nights | unresolved_image | no specific image found - Openverse hits are Mission Viejo CA and unrelated missions |
| Summer Outdoor Festival - Brainerd | unresolved_website | ambiguous - no event by this exact title has an official page |
| Brainerd Fire Department Golf Scramble | unresolved_website | no official page - event exists but has no dedicated site |
| Mighty Machines (Farmington) | unresolved_website | ambiguous - no business/venue by this name found in Farmington MN |
| St. Louis Park Outdoor Movie - A Minecraft Movie | unresolved_website | ambiguous - city runs Movies in the Park but this title is not on the verified schedule |
| Movies on the Island - Jumanji | unresolved_website | out of scope - event is in Superior, WI, not Minnesota |
| Movies on the Island - Mufasa | unresolved_website | out of scope - event is in Superior, WI, not Minnesota |
| Maple Grove Sounds of Summer Movie - Ratatouille | unresolved_website | ambiguous - official city calendar shows no Ratatouille screening in this series |
| Triangle Drive-In | unresolved_website | only candidate was a brainerd.com directory listing, not the venue's own site - rejected on audit |
| 371 Diner | unresolved_website | no official site - social media and third-party listings only |
| Pizza King Station | unresolved_website | ambiguous - no Minnesota location found (chain is Indiana-based) |
| Tableside Magician & Balloon Artist - Kids Eat Free | unresolved_website | only candidate was the performer's Facebook page, not the event or host venue's site - rejected on audit |
| Movie Night on the Barn | unresolved_website | only candidate was the brooklynpark.org homepage, which does not name the event - rejected on audit |
| Toddler Tuesday - ECFE | unresolved_website | only candidate was the Anoka-Hennepin ECFE program page, which names neither the event nor the Coon Rapids location - rejected on audit |
| Bump & Putt Family Fun Center | unresolved_website | no official site - business confirmed in Pequot Lakes MN but web presence is directory listings only |

## Diagnostics

- `no_run_summary_today` — **triggered.** The loaded base contains build rows dated 2026-08-15 but no `run_summary` end-of-run marker for today, so the build likely ran without writing its closing marker. Logged as an info-severity pipeline row and the run proceeded on the existing open queue.
- `log_base_rejected` — none. The base loaded from the local session copy (926 rows including header, 261,157 bytes) passed both the exact 10-column header check and the monotonic row-count check, and was byte-identical in size to the canonical GitHub raw copy fetched with a cache-buster.
- Drive fallback — not needed; the GitHub raw read succeeded, so no AI-ineligibility skips applied.
- Integrity check — every already-resolved row was compared against the base before publish: 16 resolution-column changes, zero mutations to non-resolution columns, and zero already-resolved rows touched.
- Publish — see below.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- This report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
