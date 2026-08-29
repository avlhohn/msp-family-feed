# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-29** (derived from the GitHub API `Date` response header — `Sat, 29 Aug 2026 09:40:14 GMT` — not the sandbox clock). Finished ~04:5x AM CDT.

## Summary

| | Count |
|---|---|
| Open queue at start | **31 rows / 30 unique items** |
| — `unresolved_website` | 9 rows / 8 unique items (+1 is a category roll-up, not per-item work) |
| — `unresolved_image` | 22 rows / 22 unique items |
| **Resolved this run** | **2** |
| — website | 2 |
| — image | 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0) |
| Left open (rolling to tomorrow) | **29 rows** |

The queue has been frozen at these same 31 rows since 2026-07-08 (oldest row), with 0 resolutions on 2026-08-21 and 2026-08-28. This run broke the streak on the website side; the image side remains structurally undrainable — see Diagnostics.

## Resolved this run

| Item | Type | Resolution note |
|---|---|---|
| St. Louis Park Outdoor Movie - A Minecraft Movie | unresolved_website | `website: https://westopolis.org/events/movies-in-the-park-ainsworth/` — dedicated single-event page on the official St. Louis Park / Golden Valley DMO site, naming the exact movie, Ainsworth Park, 7700 28th St W, St. Louis Park MN 55426, 2026-08-27 8:15–10:00 pm. Independently corroborated by the identical `discoverstlouispark.com` event path. The city's own domain `stlouisparkmn.gov` hard-403s WebFetch, so the DMO event page is the best verifiable source. This is materially stronger evidence than the candidate rejected on 2026-08-21 (a 403'd `.gov` path backed only by an aggregator listing and a real-estate blog). |
| Brainerd Fire Department Golf Scramble | unresolved_website | `website: https://www.facebook.com/BrainerdFireMN/` — the organizer's own official page. WebFetch returned the readable page title `Brainerd Fire Department \| Brainerd MN`, confirming organization and city. The event was independently corroborated (2026 Golf Scramble, Sat 2026-08-15, The Legacy at Cragun's). No dedicated event page exists and `brainerdmn.gov` 403s WebFetch. |

## Still open

| Item | Type | Likely reason |
|---|---|---|
| East Lake Park Bandshell | unresolved_image | Openverse returns Jay Pritzker Pavilion, Chicago — wrong place |
| Kelley Park | unresolved_image | Zero Openverse results for the Apple Valley park; bare name resolves to San Jose CA |
| Lake Ann Park | unresolved_image | Openverse returns the Eckankar temple — wrong place |
| Lily Lake Park | unresolved_image | Only generic water-lily photos and an Interstate State Park pothole |
| Maple Grove - Sounds of Summer Movie Night | unresolved_image | Only the Maple Grove city flag and unrelated local photos |
| Maplewood Celebrate Summer | unresolved_image | Best hit is a real "Maplewood Community Center" photo, but that is venue-substitution for an event, not a name match; other hits are Maplewood **State Park**, Ottertail County — a different place |
| Pine Tree Pond Park | unresolved_image | Openverse returns Como Ordway Japanese Garden and Drake Park, Oregon — wrong places |
| Cameron Park (Bemidji) | unresolved_image | No park-specific CC photo; only Bemidji-generic imagery |
| Lum Park Recreation Area | unresolved_image | Zero Openverse results |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | No specific photo; only an unrelated restaurant match |
| Denny's Thursday Kids Eat Free | unresolved_image | National chain promo — no place-specific photo can exist; best hit is a George Floyd protest image, an off-topic trap |
| Minneapolis Parks Volunteer Programming | unresolved_image | Agency-wide program roll-up — not depictable by construction |
| Mission Branch Library Community Garden - Monday Nights | unresolved_image | Zero Openverse results |
| Moorhead Summer Splash Event | unresolved_image | Only city-generic photos; nearest pool photo is Island Park, Fargo ND |
| Movies in the Park - Mankato | unresolved_image | Only Reconciliation Park / Dakota memorial imagery — wrong subject |
| Music in the Park Thursdays - Mankato | unresolved_image | Zero Openverse results |
| Niko Moon Concert - Vetter Stone Amphitheater | unresolved_image | Zero results; the name also traps on photographer "Kenneth Vetter" |
| Perkins Tuesday Kids Eat Free | unresolved_image | National chain promo — not depictable by construction |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | National chain promo; name also traps on politician Marco Rubio |
| Urban Air Trampoline Parks - Minnesota Locations | unresolved_image | Multi-location roll-up — not depictable by construction |
| Winona Farmers Market | unresolved_image | Only downtown-Winona generic photos, no market photo |
| Winona Parks & Rec Summer Activities | unresolved_image | Program roll-up; nearest hits (Lake Winona, generic "Lemonade Stand") are not the named program |
| Captain's Quarters | unresolved_website | Ambiguous — the well-known venue is a marina in Antioch, **Illinois**; a Lake City MN vacation rental exists but is not a confident match |
| Summer Outdoor Festival - Brainerd | unresolved_website | No event of this name exists; likely a misnamed row (Brainerd's real events are Lakes Jam and the Crow Wing Viking Festival) |
| Pizza King Station | unresolved_website | No Minnesota location exists — see Escalations |
| Toddler Tuesday - ECFE | unresolved_website | Anoka-Hennepin ECFE pages do not name "Toddler Tuesday" or the 10 Coon Rapids Blvd site; a bare district homepage fails the bar |
| Bump & Putt Family Fun Center | unresolved_website | Venue confirmed real, but no official site and no own-Facebook page; only directory listings (Yelp/Manta/ABLocal), all on the reject list. Address correction found — see Escalations |
| 688 rows | unresolved_website | Category roll-up (parks 657, events 14, volunteer 9, restaurants 6, meal_deals 2), not per-item work |

Note: the subagent working the second website batch reported Bump & Putt as "resolved" while returning **no URL**, and reported the Anoka-Hennepin ECFE homepage for Toddler Tuesday while itself noting the page names neither the class nor the address. Both were rejected on audit — the recurring over-resolution pattern.

## Diagnostics

- **`no_run_summary_today` — logged, but a KNOWN FALSE POSITIVE.** The build stopped emitting `issue_type=run_summary` rows after 2026-08-23, so this soft freshness check now fires on every run regardless of build health. The build demonstrably ran today: 37 rows carry `run_date` 2026-08-29, including two STEP6 `publish` rows plus `build`, `compile`, `city_resolution` and `deals_yield`; the repo's `pushed_at` is 2026-08-29T08:37:08Z. **Durable fix needed:** either restore the marker in the build, or retarget the fixer's freshness check at the STEP6 `publish` row. A check that always fires trains the reader to skim it.
- **`log_base_rejected` — none.** The base passed both guards: exact 10-column header, 2356 rows (monotonic growth), and the local mount copy was byte-identical (md5 `39156fac…`) to the GitHub raw copy.
- **No Drive AI-ineligibility skip** — the one-time Drive fallback did not fire; the GitHub raw read succeeded.
- **og:image route remains structurally non-functional.** WebFetch converts HTML to markdown and strips `<head>`, so `og:image` is unreadable, and raw HTTP page fetches are policy-blocked. No subagent effort was spent re-attempting it. Known hard-403 domains: `chanhassenmn.gov`, `stillwatermn.gov`, `brainerdmn.gov`, `stlouisparkmn.gov` (every path), `dennys.com`, `vetterstoneamphitheater.com`.
- **Openverse route: 0 of 22.** Three query variants per item (exact name, name + city, landmark variant), 188 hits, queried **unfiltered by license** (a `license_type` filter silently hides `by-nc`/`by-nc-sa` results). Not one hit depicted the exact named place. This matches 2026-08-21 (0/22) and 2026-08-28 (0/22); small municipal Minnesota parks have essentially no CC-licensed coverage.

### Escalations (data-quality bugs, not missing websites)

1. **Pizza King Station** — no Minnesota location exists; the name matches an Indiana chain (`bluffroad.theoriginalpizzaking.com`). Confirmed independently on 2026-08-21 and again today. This is almost certainly a bad seed row and should be fixed or dropped at the build stage rather than re-searched nightly. Left OPEN rather than closed as "confirmed gone", because absence of search results is not positive proof of closure.
2. **Bump & Putt Family Fun Center** — the logged address "Four miles north of Nisswa, MN" is wrong. The correct address is **29107 State Hwy 371, Pequot Lakes, MN 56472** (phone 218-568-8833), confirmed across multiple independent listings. The address is correctable at the build stage even though no website exists.
3. **~11 image rows cannot be resolved by construction** — national kids-eat-free chain promos (Denny's, Perkins, Rubio's), multi-location roll-ups (Urban Air), and agency/program roll-ups (Minneapolis Parks Volunteer Programming, Winona Parks & Rec Summer Activities). These are generic *by nature*; no place-specific photo can exist for them. Recommend retiring them from the queue rather than requeueing nightly. Draining the rest needs a `<head>`-preserving fetch path or an image source with municipal-park coverage.

## Files

- Error log: <https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv>
- This report: <https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md>
