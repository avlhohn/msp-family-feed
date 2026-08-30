# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-08-30** (derived from the GitHub API `Date` header, not the sandbox clock). Finished 04:49 local.

## Summary

- **Open queue at start:** 29 rows / 28 unique items — 6 `unresolved_website` (7 rows), 22 `unresolved_image` (22 rows). Oldest open rows date to 2026-07-08.
- **Resolved this run:** 0 (website 0; image 0 — og_image 0, facebook 0, stock_openverse_specific 0).
- **Left open:** 29 rows, rolling to tomorrow.

A zero-resolution run is the correct outcome here, not a failure to try: every remaining item was re-attempted and each failed the acceptance bar for a specific, documented reason. The value delivered this run is diagnostic — one image route newly closed off, and two data-quality escalations that no amount of further searching will fix. See **Escalations**.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| 688 rows | website | not a work item — a category roll-up the build writes; should be excluded from the queue |
| Bump & Putt Family Fun Center | website | no site exists — only reject-list directories (address corrected, see Escalations) |
| Captain's Quarters | website | bad source row — name resolves to a marina in Antioch, ILLINOIS; no confident MN venue |
| Pizza King Station | website | bad source row — an Indianapolis, INDIANA restaurant; no MN location exists |
| Summer Outdoor Festival - Brainerd | website | bad source row — no event of this name exists; title likely garbled |
| Toddler Tuesday - ECFE | website | item name and logged address disagree — see Escalations; not resolvable as written |
| Bowlero Brooklyn Park (Lucky Strike) | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Cameron Park (Bemidji) | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Denny's Thursday Kids Eat Free | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |
| East Lake Park Bandshell | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Kelley Park | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Lake Ann Park | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Lily Lake Park | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Lum Park Recreation Area | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Maple Grove - Sounds of Summer Movie Night | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Maplewood Celebrate Summer | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Minneapolis Parks Volunteer Programming | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |
| Mission Branch Library Community Garden - Monday Nights | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Moorhead Summer Splash Event | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Movies in the Park - Mankato | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Music in the Park Thursdays - Mankato | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Niko Moon Concert - Vetter Stone Amphitheater | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Perkins Tuesday Kids Eat Free | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |
| Pine Tree Pond Park | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Rubio's Rewards Thursday Kids Free Meal | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |
| Urban Air Trampoline Parks - Minnesota Locations | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |
| Winona Farmers Market | image | no specific image found — 404 on Wikipedia, no CC-licensed Openverse photo of this exact place |
| Winona Parks & Rec Summer Activities | image | generic by construction — a chain promo or multi-site roll-up with no single place to photograph |

## Escalations — rows that cannot be fixed by searching

These need a build-stage correction or a retirement decision. Re-searching them nightly can never succeed, and a permanently open row trains the reader to skim the queue.

**1. `Toddler Tuesday - ECFE` — item name and address disagree (NEW this run).** The logged address, 10 Coon Rapids Boulevard, Coon Rapids MN 55448, is the **Urban Air Trampoline & Adventure Park** retail location — verified on the venue's own page, which advertises a commercial "Toddler Tuesday" open-play session 9–11am and never uses the term ECFE. ECFE (Early Childhood Family Education) is a public-school program; Anoka-Hennepin runs a Coon Rapids ECFE site at a different address. A research pass proposed `urbanair.com/minnesota-coon-rapids/` as the fix and it was **deliberately rejected**: attaching a paid trampoline-park URL to a row labelled ECFE would tell a family that a sliding-fee district parenting class is a commercial jump session. Build fix — either retitle the row to *Toddler Tuesday – Urban Air Coon Rapids* (in which case `https://www.urbanair.com/minnesota-coon-rapids/` is the correct website and the row closes immediately), or correct the address to the genuine Anoka-Hennepin ECFE Coon Rapids site.

**2. `Bump & Putt Family Fun Center` — logged address is wrong (reconfirmed).** Logged as "Four miles north of Nisswa, MN". Correct: **29107 State Hwy 371, Pequot Lakes, MN 56472**, phone 218-568-8833. The website is genuinely unresolvable — no official site and no own Facebook page exist, only reject-list directories — but the address is fixable at the build stage and should be corrected there.

**3. Three phantom rows — reconfirmed independently this run.** `Captain's Quarters` is a marina in Antioch, **Illinois**. `Pizza King Station` is an Indianapolis, **Indiana** restaurant (`bluffroad.theoriginalpizzaking.com`); no MN location exists. `Summer Outdoor Festival - Brainerd` matches no real event — Brainerd's actual summer events are Lakes Jam and the Lakes Area Music Festival block party. All three are left **OPEN** rather than closed as "confirmed gone", because a name collision with an out-of-state business is not positive proof of closure. They should be retired or corrected at source.

**4. `688 rows` is not a work item.** It is a category roll-up the build writes (`{'events': 14, 'parks': 657, …}`). It should be excluded from the fixer queue rather than dispatched for research.

## Image backlog — the last untried route is now closed

The 22 `unresolved_image` rows have now returned zero resolutions on four consecutive runs. All routes were re-attempted this run and each fails structurally, not incidentally:

- **og:image** — `WebFetch` converts pages to markdown and strips `<head>`, so the meta tag is never visible; raw HTTP fetches are policy-blocked. Several of these domains (`chanhassenmn.gov`, `stillwatermn.gov`, `brainerdmn.gov`, `dennys.com`, `vetterstoneamphitheater.com`) also hard-403.
- **Facebook** — `WebFetch` cannot read photo albums.
- **Openverse** — re-probed all 22 items: 13 results returned, **0** passing the exact-name bar. The same false positives recur (Lily Lake Park → a basalt pothole, Pine Tree Pond Park → Como Ordway Japanese Garden, Lake Ann Park → a Montana governor's mansion). Small municipal Minnesota parks simply have no CC-licensed coverage.
- **Wikipedia REST summary API — newly probed this run.** This is the venue-photo source added to the build's `image_upgrades.py` on 2026-08-29 and it had not previously been tried against this queue. Result: **0 eligible photos.** Every small municipal park 404s; the only article hits were out-of-state (`Kelley Park` → California) or disambiguation pages (`Cameron Park`, `East Lake`, `Lily Lake`, `Lake Ann`), and `Vetter Stone Amphitheater` redirects to the *city* article for Mankato — all correctly rejected by the Minnesota bounding-box and token-overlap guards.

With that route closed, no available image source can drain this backlog. **Recommendation:** retire the ~11 rows that are generic *by construction* — national chain kids-eat-free promos (Denny's, Perkins, Rubio's), multi-location roll-ups ("Urban Air Trampoline Parks - Minnesota Locations"), and agency program roll-ups ("Minneapolis Parks Volunteer Programming") have no single place to photograph and will never have a specific image. The remaining ~11 municipal parks should be parked behind a `<head>`-preserving fetch path rather than requeued nightly.

## Diagnostics

- **`log_base_rejected`:** none. Base validated — header exactly the 10-column schema, 2387 rows / 696,754 bytes, and the local copy was byte-identical to the GitHub canonical copy.
- **`no_run_summary_today`:** fired, and logged — but it is a **known false positive**. The build stopped emitting the `run_summary` marker after 2026-08-23, so this check has fired every run since. Today's build did run (the base carries 22 rows dated 2026-08-30). Recommend retiring the check or restoring the marker in the build.
- **Token fetch:** succeeded on the first attempt at STEP 1 and was validated against the GitHub API before any research work began.
- **Publish:** see below.
- **AI-ineligible base copies:** not applicable — the one-time Drive fallback did not fire.
- **Resolved-row integrity:** all 514 previously resolved rows preserved byte-for-byte; no row was re-opened, edited or deleted.

## Files

- `error_log.csv` — https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- `error-fixing-findings-latest.md` — https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md