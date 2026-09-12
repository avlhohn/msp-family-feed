# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-12**, finished **04:52 US Central (09:52 UTC)**. Run date derived from the GitHub API `Date` response header (`Sat, 12 Sep 2026 09:41:10 GMT`), not the sandbox clock; the sandbox clock agreed this run.

## Summary

Open queue at start: **19 rows / 18 distinct items** — 6 `unresolved_website` (one of which is the `688 rows` category roll-up, never dispatchable) and 13 `unresolved_image`.

Resolved this run: **0** — website 0; image 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0).

Left open: **19 rows / 18 items**, rolling to tomorrow. No regressions: all 3,355 carried rows are byte-identical to the base, and all 536 previously-resolved rows are preserved untouched.

The run was scoped before any research was dispatched, which is what kept a zero-resolution run cheap. Only **6 of the 18 items still exist in today's published feed**; 12 have aged out. Of those 6, five are settled negatives on first-hand evidence from earlier runs — two are chain-promotion image rows that are structurally unresolvable, and three are data defects wearing a website/image row's clothes. That left exactly **one item with a genuinely untried route** (Lake Ann Park), and it closed. One subagent was dispatched.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | image | Licence-bound, not discovery-bound. ~25 routes now closed. The one untried route this run — the Wayback Machine, to get behind the `chanhassenmn.gov` hard-403 — turned out to be blocked to our fetcher at the tool level (see Diagnostics). |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled negative. All six images on the venue page are Contentful chain assets recurring on the Blaine and Lakeville MN sibling pages. Re-confirmed today: the four body photos are generic brand marketing (grand-opening party, birthday candles, "family unlimited bowling", holiday bowling). The real defect on this row is the stale URL and wrong ZIP — see Escalations. |
| Denny's Thursday Kids Eat Free | image | Structurally unresolvable. A `meal_deals` row is a promotion, not a venue, so there is no "photo of this exact thing" to find. `dennys.com` 403s both the og:image and page-body routes; its only Facebook asset is a chain-wide brand graphic. Do not re-queue for search. |
| Perkins Tuesday Kids Eat Free | image | Structurally unresolvable, same reason. `perkins.com` times out, MN location pages 403, and `eatatperkins.com` carries only menu product shots that recur on ND/KS/FL siblings. The deal itself is genuine — this is an image gap only. |
| Rubio's Rewards Thursday Kids Free Meal | image | Bad seed, not an image gap. See Escalations. |
| Bump & Putt Family Fun Center | website | No first-party site exists after 10 runs, but the row is deliberately kept open as a defect marker for the dead URL it still ships. See Escalations. |
| Maplewood Celebrate Summer | image | Aged out of the feed. |
| Mission Branch Library Community Garden - Monday Nights | image | Aged out. Also a bad seed — no "Mission Branch Library" exists in the Hennepin County system; it is a San Francisco Public Library location. |
| Moorhead Summer Splash Event | image | Aged out of the feed. |
| Movies in the Park - Mankato | image | Aged out of the feed. |
| Music in the Park Thursdays - Mankato | image | Aged out of the feed. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of the feed. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out. The umbrella row is gone; the four surviving per-location rows are different items and must not be merged into it. |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed. |
| Pizza King Station | website | Aged out. Bad seed — no Minnesota location exists; the name matches an Indiana chain. |
| Summer Outdoor Festival - Brainerd | website (x2 rows) | Aged out. No event of this name exists; Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival. |
| Toddler Tuesday - ECFE | website | Aged out. Its prior false fuzzy match to a Winona row is now gone too. The item name and its logged Coon Rapids address describe different things; a research pass will confidently propose the Urban Air URL and that must be rejected. |
| 688 rows | website | Category roll-up written by the build, not a per-item work item. Never dispatch research on it. |

## Escalations

These are not missing websites or missing images. Re-searching them nightly can never succeed, so they are surfaced here for the build stage or a human to act on once. All three live ones were re-verified **first-hand today**, not recalled from memory.

**Bump & Putt Family Fun Center — 10th consecutive confirmation.** `https://www.brainerd.com/business/bump-n-putt-family-fun-park/` returns a hard **404** ("Sorry! That page doesn't seem to exist."). The feed has now shipped this broken link for ten runs. The stored address `Four miles north of Nisswa, MN` is wrong — the venue is at **29107 State Hwy 371, Pequot Lakes, MN 56472** (phone 218-568-8833) — and the stored coordinates **46.520522 / -94.288609** were geocoded *from* the wrong address, so the address fix and the pin fix are one fix, not two. Blank `latitude`/`longitude` when correcting the address, because STEP 4.9 skips populated coordinates and a corrected address with an uncorrected pin never self-heals. No evidence of closure and no evidence of current operation were found — those are different findings, and the row must not be closed as "confirmed closed".

**Bowlero / Lucky Strike Brooklyn Park — wrong ZIP, stale URL.** `bowlero.com/location/bowlero-brooklyn-park` still **301s** to `https://www.luckystrikeent.com/location/lucky-strike-brooklyn-park`, which is the canonical URL to store. That page states **7545 Brooklyn Blvd, Brooklyn Park, MN 55443**; the feed stores **55445**. The chain has rebranded Bowlero → Lucky Strike, so the stored URL is a redirect rather than a canonical address.

**Rubio's Rewards Thursday Kids Free Meal — bad seed, and the most serious of the three.** Reconfirmed today: Rubio's Coastal Grill operates **82 restaurants across California, Arizona and Nevada only** — no Minnesota locations at all. MN businesses trading as "Rubio's" are unaffiliated independents. This `meal_deals` row therefore advertises a kids-eat-free deal that cannot be honoured at any counter in the state, which is worse than a missing image: a `deal_description` is a factual claim a family will act on. Recommend the build **drop the row** rather than keep seeking an image for it.

**New this run — the publish target carries two meal_deals artifacts, one of them 18 days stale.** `deals.csv` (150 rows) is the live artifact and matches `msp_family_guide.json`'s `meal_deals` exactly, 150 of 150 titles. But an orphaned **`meal_deals.csv` (56 rows)** also sits at the repo root, last committed **2026-08-25**, and **25 of its 56 titles no longer exist in the feed**. Any consumer that resolves the category by its obvious filename gets month-old data. Nothing can currently see this: the build's own publish row names `deals.csv` and never touches `meal_deals.csv`, so the six-artifact blob-SHA-1 verification passes while the stale seventh file sits beside it. This is the same "two things naming one source, nothing enforcing agreement" class the pipeline already documents for `LIBRARY_SRC` and `SOURCE_KEYS`, reached through the publish target instead of through code. Recommend deleting `meal_deals.csv` from the repo, or making it the single canonical path and retiring `deals.csv`.

**Standing structural ask, 5th run running — auto-close an unresolved row once its item leaves the published feed.** Twelve of today's eighteen items no longer exist in the feed. The fixer cannot close them by searching, so they accrue forever and train the reader to skim the queue. This one change would drain 12 of 18 rows today and is by far the highest-leverage fix available.

## Diagnostics

**Base validation — clean.** The session-local `error_log.csv` was byte-identical to the GitHub canonical (blob `102de9f4db5b410a9554d0127010a0289c0f2b5d`, 1,047,587 bytes, 3,355 rows). Header matched the 10-column schema exactly, no malformed rows, and row count grew monotonically from 3,057 on 2026-09-09. No `log_base_rejected`.

**Freshness — clean.** A `run_summary` row dated 2026-09-12 was present, so the day's build had already run. No `no_run_summary_today`.

**New route closure, structural and pipeline-wide: the Wayback Machine is unavailable to this pipeline.** `web.archive.org` is blocked to our fetcher at the **tool level** — the error is "Claude Code is unable to fetch from web.archive.org", not a site-side 403. This matters because the subagent reported it as a Wayback 403, which would have left the route looking like a transient site problem worth retrying. Verified directly rather than accepted, in line with the standing rule that a subagent's negative is also only a candidate verdict. The consequence is general: the archive route can **never** be used to get behind the hard-403s on `chanhassenmn.gov`, `carvercountymn.gov` or `brainerdmn.gov`, and it should not be proposed again for any of them.

**Five further Lake Ann Park routes closed**, none of them previously tried: `sandee.com` (returns an empty images array), `mindtrip.ai` (a placeholder og:image only), two `cdn1.sportngin.com` PDFs (field maps and diagrams, no photographs), the `chanhassenmn.gov` PhotoAlbum component paths and the Lake Ann Park Preserve project page (both hard 403), and Wikimedia Commons (which has Lake Ann in Michigan and Arkansas, wrong state). The unlinked-photo-gallery route that broke the Cameron Park case open in Bemidji does not generalise to Chanhassen — the gallery paths exist but 403 like the rest of the host.

**Publishing.** Both files verified by blob SHA-1 and by contents-API `size` and `sha` change on the first attempt. No retries.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
