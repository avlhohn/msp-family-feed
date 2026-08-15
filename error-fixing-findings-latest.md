# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-14** (finished 20:4x UTC — see commit timestamp).

## Summary

Open queue at start: **51 rows / 50 unique items** — 26 rows `unresolved_website` (25 unique) and 25 rows `unresolved_image` (25 unique).

Resolved this run: **19 rows / 19 unique items** — 17 website, 2 image. Image split: `og_image` 0, `facebook` 0, `stock_openverse_specific` 2.

Left open: **32 rows / 31 unique items** rolling to tomorrow — 8 website, 23 image.

## Resolved this run

| Item | Type | Resolution note |
| --- | --- | --- |
| Family Dance Party - Rochester Public Library | image | image: stock_openverse_specific - place-specific Openverse photo of Rochester Public Library (Rochester, MN), verified name match in image title 'Rochester, Minnesota Public Library.jpg', CC BY https://upload.wikimedia.org/wikipedia/commons/9/97/Rochester%2C_Minnesota_Public_Library.jpg |
| Family Fun Night | website | website: https://loringpark.org/events/family-fun-night/ - verified: Citizens For A Loring Park Community event page names 'Family Fun Night' at Loring Park, 1382 Willow St, Minneapolis MN |
| Badges & Bobbers Fishing Event - Lake George | image | image: stock_openverse_specific - place-specific Openverse photo of Lake George, St. Cloud MN, verified name+city match in image title 'Lake George, Saint Cloud, MN.', CC BY https://live.staticflickr.com/7443/9130544973_f7d901281f_b.jpg |
| Anoka Happy Days Festival | website | website: https://www.cityoframseymn.gov/recreation-culture/events/happy-days-festival/ - verified: item is the Ramsey Happy Days Festival (venue 7550 Sunwood Dr NW, Anoka MN 55303 ZIP); official City of Ramsey event page, Sept 12 2026 |
| Wayzata Car Show | website | website: https://wayzata.com/wayzata-car-show/ - verified: official Wayzata community page names the Wayzata Car Show in downtown Wayzata MN |
| St. Paul Park Heritage Days | website | website: https://stpaulpark.org/community/explore_st_paul_park/heritage_days_festival.php - verified: official City of St. Paul Park page for Heritage Days Festival, Heritage Park, St. Paul Park MN |
| Blue Heron Days (Lino Lakes) | website | website: https://www.linolakes.gov/407/Blue-Heron-Days - verified: official City of Lino Lakes page for Blue Heron Days, Aug 13-16 2026 |
| Bloomington Street Arts Festival | website | website: https://www.bloomingtonmn.gov/bloomingtonstreetartsfest - verified: official City of Bloomington page for the Street Arts Festival, Bloomington MN |
| Chroma Zone Mural & Art Festival | website | website: https://www.chromazone.net/ - verified: official Chroma Zone festival site, Creative Enterprise Zone, Saint Paul MN |
| St. Cloud Pride - Pride in the Park | website | website: https://stcpride.org/stcloud-pride-week/ - verified: official St. Cloud Pride site names Pride in the Park at Lake George, St. Cloud MN |
| St. Paul Movies in the Parks - Encanto | website | website: https://stpaul.gov/departments/parks-recreation/activities/summer-activities/movies-parks - verified: official St. Paul Parks & Rec program page; Encanto listed at El Rio Vista Rec Center |
| Plymouth Kids Fest | website | website: https://www.plymouthmn.gov/departments/parks-recreation-/events - verified: official City of Plymouth Parks & Rec Special Events page names Kids Fest at Hilde Performance Center, 3500 Plymouth Blvd |
| Cars and Caves - German Cars | website | website: https://chanhassenautoplex.com/event/cars-and-caves-september-2024/ - verified: venue's own Cars and Caves page, Chanhassen AutoPlex 8150 Audubon Rd; German-car (Oktoberfest) edition described |
| Raymond Harvest Festival | website | website: https://raymond-minnesota.com/raymond-harvest-festival - verified: official Raymond MN page, Raymond Harvest Festival Aug 21-23 2026 |
| Family Night on the Farm | website | website: https://www.winonachamber.com/post/family-night-on-the-farm-2024 - verified: Winona Chamber post specific to Family Night on the Farm at Barkheim Farms, Lewiston MN |
| La Crescent Apple Fest | website | website: https://applefestusa.com/ - verified: official Applefest USA site for La Crescent MN annual Applefest |
| Hmong Village | website | website: https://www.visitsaintpaul.com/directory/hmong-village-shopping-center/ - verified: no standalone official site exists; specific directory entry names Hmong Village Shopping Center at 1001 Johnson Pkwy, St. Paul MN 55106 |
| Hmongtown Marketplace | website | website: https://hmongtownmarketplace.com/ - verified: official site, address 217 Como Ave Suite 2-100, St. Paul MN 55103 matches |
| Mama Safia's Kitchen | website | website: https://www.mamasafiakitchen.com/ - verified: official restaurant site, 720 E Lake St, Minneapolis MN 55407 matches |

## Still open

| Item | Type | Likely reason |
| --- | --- | --- |
| Maple Grove - Sounds of Summer Movie Night | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Maplewood Celebrate Summer | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Kelley Park | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Lake Ann Park | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Lily Lake Park | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Pine Tree Pond Park | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Chapel Trail at St. John's University | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| East Lake Park Bandshell | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Lum Park Recreation Area | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Cameron Park (Bemidji) | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Captain's Quarters | website | ambiguous — several unrelated Captain's Quarters venues (Lake City MN rental, out-of-state restaurants); no specific MN item identifiable |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Music in the Park Thursdays - Mankato | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Movies in the Park - Mankato | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Moorhead Summer Splash Event | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Winona Parks & Rec Summer Activities | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Winona Farmers Market | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Urban Air Trampoline Parks - Minnesota Locations | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Denny's Thursday Kids Eat Free | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Perkins Tuesday Kids Eat Free | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Rubio's Rewards Thursday Kids Free Meal | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Minneapolis Parks Volunteer Programming | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Mission Branch Library Community Garden - Monday Nights | image | no specific image found — og:image extraction structurally unavailable (WebFetch strips `<head>`); Openverse returned only generic/city-level or wrong-place stock |
| Summer Outdoor Festival - Brainerd | website | ambiguous — no Brainerd-area festival carries this exact name (Lakes Jam / Crow Wing Viking Festival are distinct events) |
| Brainerd Fire Department Golf Scramble | website | only a generic chamber events calendar found; no event-specific official page — held to the strict bar |
| Mighty Machines (Farmington) | website | ambiguous — Dakota County Library runs Mighty Machines events but no 2026 Farmington instance confirmed |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | only aggregator listings (Thrifty Minnesota, Family Fun Twin Cities); no official City of St. Louis Park page for this screening |
| Movies on the Island - Jumanji | website | out of scope / no MN page — event is at Barkers Island Festival Park, Superior WI |
| Movies on the Island - Mufasa | website | out of scope / no MN page — event is at Barkers Island Festival Park, Superior WI |
| Maple Grove Sounds of Summer Movie - Ratatouille | website | series confirmed on official Maple Grove site but the Ratatouille title appears only on aggregators |

## Diagnostics

- `log_base_rejected`: none. The base loaded from `https://raw.githubusercontent.com/avlhohn/msp-family-feed/main/error_log.csv` (228,027 bytes, 817 rows incl. header) was byte-identical (md5 `0ac74f4a07c26a9484df10f17f07b349`) to the local mount copy and passed both validation checks — exact 10-column schema and plausible monotonic row count.
- `no_run_summary_today`: **triggered.** The base contained no `run_summary` row dated 2026-08-14, so the daily build had not yet published today's end-of-run marker when this fixer ran. Proceeded on the existing open queue; logged as an `info`-severity `pipeline` row.
- Image tooling: og:image extraction was attempted and remains structurally unavailable — `WebFetch` converts pages to markdown and strips `<head>`, and raw HTTP page fetches are policy-blocked. This is a tooling limitation, not proof the images are absent. Fell through to the Openverse API for all 25 image items across three query passes (exact name, name + city, and landmark-specific variants); only 2 returned photos that specifically depict the exact named venue with a metadata name match. The remainder returned city-level or wrong-place stock (e.g. a Maple Grove city flag, a Kelley Park in San Jose CA, Eckankar temple for Lake Ann Park, Lake Bemidji for Cameron Park) and were correctly left open rather than resolved with generic stock.
- Website bar enforcement: 4 candidate URLs returned by the search pass were **rejected on audit** and left open rather than accepted — an aggregator page (thriftyminnesota.com) for the St. Louis Park movie, a generic chamber events calendar for the Brainerd golf scramble, and two Wisconsin events out of MN scope. One candidate (Anoka Happy Days) was accepted only after confirming the item is the Ramsey Happy Days Festival at an Anoka-ZIP address, and its URL was upgraded to the current official City of Ramsey event page.
- Publish: see commit status below.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
