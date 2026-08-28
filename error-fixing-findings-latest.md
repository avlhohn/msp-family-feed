# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-28** — finished 17:26 CDT (run date derived from the GitHub API `Date` header, `Fri, 28 Aug 2026 22:17:28 GMT`, not the sandbox clock).

## Summary

Open queue at start: **31 rows / 30 unique items** — 9 rows `unresolved_website` (7 unique real items, one of which has 2 rows, plus 1 aggregate diagnostic row) and 22 rows `unresolved_image`.

Resolved this run: **0** — website 0, image 0 (og_image 0, facebook 0, stock_openverse_specific 0).

Left open: **31 rows**, all rolling to tomorrow.

**This queue has not moved in at least a week.** The previous findings report, dated 2026-08-21, records the identical figures — the same 31 rows / 30 unique items and the same 0 resolutions — and the oldest open rows go back to 2026-07-08. So this is not a bad day; it is a backlog that is structurally undrainable by this task in its current form, and it should be escalated rather than retried nightly. The diagnosis is in Diagnostics below, and it is the real output of this run.

Two Openverse candidates name-matched and were deliberately **rejected as wrong-place**: `Summer's End, Maplewood State Park, Ottertail County` is not the Maplewood suburb the row refers to, and `Lemonade Stand` is generic stock. Both would have passed a naive keyword match, and accepting either would have shipped a wrong photo to families.

Seven diagnostic rows were appended to the log capturing what the research did turn up — four suspected bad addresses, two rows that appear not to exist at all, and one stale redirect. Those byproducts are worth more this run than the empty fix list.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| East Lake Park Bandshell | image | og:image not extractable (WebFetch strips `<head>`); no Openverse coverage |
| Kelley Park | image | og:image not extractable; no Openverse coverage |
| Lake Ann Park | image | chanhassenmn.gov returns 403 to WebFetch; no Openverse coverage |
| Lily Lake Park | image | stillwatermn.gov returns 403 to WebFetch; no Openverse coverage |
| Pine Tree Pond Park | image | og:image not extractable; address/city also wrong (see Diagnostics) |
| Cameron Park (Bemidji) | image | og:image not extractable on visitbemidji.com venue page |
| Lum Park Recreation Area | image | brainerdmn.gov returns 403 to WebFetch |
| Maple Grove - Sounds of Summer Movie Night | image | no per-event deep-link page exists; only the Town Green venue page |
| Maplewood Celebrate Summer | image | both city event URLs 404; only generic/wrong-place stock available |
| Bowlero Brooklyn Park (Lucky Strike) | image | og:image not extractable; stored URL is also a stale redirect |
| Denny's Thursday Kids Eat Free | image | dennys.com returns 403; chain promo has no place-specific image |
| Perkins Tuesday Kids Eat Free | image | perkins.com timed out; chain promo, no place-specific image |
| Rubio's Rewards Thursday Kids Free Meal | image | rewards page carries no og:image; chain promo |
| Urban Air Trampoline Parks - Minnesota Locations | image | multi-location row — a single-location photo would misrepresent it |
| Minneapolis Parks Volunteer Programming | image | agency-wide program page, not a specific venue — generic by nature |
| Mission Branch Library Community Garden - Monday Nights | image | item does not appear to exist in MN (see Diagnostics) |
| Moorhead Summer Splash Event | image | event real, but its city calendar deep-link now 404s |
| Movies in the Park - Mankato | image | no such Mankato program found (see Diagnostics) |
| Music in the Park Thursdays - Mankato | image | detail page 404s; only the city-wide events page remains |
| Niko Moon Concert - Vetter Stone Amphitheater | image | venue page 403s; Ticketmaster requires login |
| Winona Farmers Market | image | site has no og:image; Facebook album not extractable via WebFetch |
| Winona Parks & Rec Summer Activities | image | umbrella city-department page — generic by nature |
| Captain's Quarters | website | ambiguous — several unrelated MN venues share the name |
| Brainerd Fire Department Golf Scramble | website | one-off past event; no page on any official Brainerd site |
| Summer Outdoor Festival - Brainerd | website | title matches no real named festival (2 open rows) |
| St. Louis Park Outdoor Movie - A Minecraft Movie | website | event verified real, but stlouisparkmn.gov 403s every path |
| Pizza King Station | website | no MN venue by this name; nearest match is in Indiana |
| Bump & Putt Family Fun Center | website | directory listings only (Yelp/ABLocal/Manta) — no official site |
| Toddler Tuesday - ECFE | website | district-wide ECFE overview page names no such class |
| 688 rows | website | aggregate diagnostic row, not a per-item fixable target |

## Diagnostics

**Image path yield is structurally zero for this queue — this is the headline.** Route 1 (og:image) failed on all 22 items: WebFetch strips `<head>`, and five first-party sites additionally returned 403 (chanhassenmn.gov, stillwatermn.gov, brainerdmn.gov, dennys.com, vetterstoneamphitheater.com). Route 2 (Facebook) is unusable because WebFetch cannot read photo albums. Route 3 (Openverse) name-matched 0 of 17 queries — small municipal Minnesota parks have no CC-licensed coverage. The queue is now roughly 90% municipal parks, chain promotions and umbrella program pages, which is exactly the shape all three routes fail on. Combined with the identical 2026-08-21 result, the conclusion is that more fixer runs cannot drain this backlog. It needs one of: a fetch path that preserves `<head>`, a licensed image source with municipal-park coverage, or a decision to retire the rows that are generic by nature (agency-wide programs, multi-location chain rows) rather than leaving them queued forever.

**`no_run_summary_today` — triggered, but it is now a permanent false positive.** No `run_summary` row dated 2026-08-28 exists, yet the build clearly completed: 33 rows carry today's date, including the STEP6 publish row and the STEP8 coverage rows. The build stopped emitting `run_summary` after 2026-08-23, so this check can never pass again. Either restore the marker or retarget the freshness check at the STEP6 publish row — a check that always fires is one that stops being read.

**`log_base_rejected` — none.** The base validated cleanly: exact 10-column header, 2,312 rows, zero malformed rows, and the local copy was md5-identical to the GitHub canonical copy (`c2e5818188921ae6a295bd29e5ccd52b`), so there was no local/remote divergence to adjudicate.

**Four park rows carry a suspected wrong address (new finding).** Pine Tree Pond Park is self-contradicted inside our own data — stored address `1485 Settlers Ridge Pkwy, Woodbury` against a stored `cottagegrovemn.gov` website. The park is in **Cottage Grove**, so the city is wrong, not merely the street; that one is safe to act on. Kelley Park (`13001 Johnny Cake Ridge Rd` vs `6855 Fortino St`), Lake Ann Park (`6800 Birch Dr` vs `1456 W 78th St`) and Lily Lake Park (`1003 S Greeley St` vs `1208 Greeley St S`) also disagree with directory sources, but those rest on Yelp/Waze rather than a city page, so they are logged as *suspected* and should be re-verified at STEP 4.9 before anything is edited.

**Two rows appear not to exist at all.** `Mission Branch Library Community Garden - Monday Nights` — no Mission Branch Library exists in the Minneapolis, Hennepin or Ramsey systems; the only one found is in San Antonio, TX. `Movies in the Park - Mankato` — no such Mankato program was found, and our own feed attaches the title to Leif Erikson Park in **Duluth**. Both should be validated for existence and dropped or re-sourced rather than worked as image items again.

**One stale redirect.** `bowlero.com/location/bowlero-brooklyn-park` now redirects to the rebranded `luckystrikeent.com/location/lucky-strike-brooklyn-park`. The venue is open and real (48 lanes plus arcade), so this is a refresh, not a dead link.

**Three website candidates rejected on the bar, deliberately.** Bump & Putt exists (29107 State Hwy 371, Pequot Lakes) but has only directory listings, and a directory is not the venue's own site. Toddler Tuesday - ECFE is served by Anoka-Hennepin ECFE, but no page names this class — only the district-wide overview — so it fails the "specifically names the item" test at medium confidence; the registration catalog was checked directly and its class list is not exposed to fetch. The third, a subagent-supplied St. Louis Park calendar URL, was rejected because its reported date (Sept 2) is contradicted by two independent listings (2026-08-27, Ainsworth Park) and the site's blanket 403 made it impossible to adjudicate — an unverifiable URL carrying a contradicted detail is the exact shape of a fabricated one. Note that the St. Louis Park screening has now passed, so that row may be better retired than resolved.

**Publish:** log and findings both published to GitHub and verified by post-publish size and sha change.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
