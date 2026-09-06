# MSP Family Guide — Error Fixing (Latest)

Run date: **2026-09-06** — finished 09:46 UTC (04:46 America/Chicago). Run date derived from the GitHub API `Date` response header, not the sandbox clock.

## Summary

| | Count |
|---|---|
| Open queue at start | **20 rows / 19 unique items** |
| — `unresolved_website` | 6 rows (5 unique items + 1 category roll-up) |
| — `unresolved_image` | 14 rows / 14 unique items |
| **Resolved this run** | **0** |
| — website | 0 |
| — image | 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0) |
| Left open (rolling to tomorrow) | **20** |

A zero-resolution run is the correct outcome here rather than a failure. Two genuine, on-topic photographs were located this run and both were rejected — not for relevance but for **provenance and licence**. Details under Escalations. The standing rule holds: do not lower the bar to move the number.

**Feed cross-check (one fetch, run every time):** only **7 of the 19 open items still exist in the published 2026-09-06 feed** (window 2026-09-06 → 2026-10-31). The other **12 have aged out** — they were summer 2026 events — so no amount of searching can ever resolve them. They are not merely hard, they are moot. They remain open because "no longer in the feed" is not a sanctioned resolution.

Still in the feed: Lake Ann Park, Cameron Park (Bemidji), Denny's Thursday Kids Eat Free, Perkins Tuesday Kids Eat Free, Rubio's Rewards Thursday Kids Free Meal, Bowlero Brooklyn Park (Lucky Strike), Bump & Putt Family Fun Center.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | image | Real park photos exist but only on a commercial realtor's site (no licence grant); `chanhassenmn.gov` still hard-403 on every path incl. its CivicPlus facility directory |
| Cameron Park (Bemidji) | image | Only found photo is a copyrighted Bemidji Pioneer staff photograph; the venue's own DMO listing page carries no body images |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled reject — location page carries only shared Contentful brand assets, re-confirmed this run |
| Denny's Thursday Kids Eat Free | image | National-chain umbrella row ("Multiple Twin Cities locations") — no specific place to photograph; `dennys.com` 403 |
| Perkins Tuesday Kids Eat Free | image | National-chain umbrella row — no specific location, only brand marketing assets available |
| Rubio's Rewards Thursday Kids Free Meal | image | **Bad seed** — chain has no Minnesota locations at all (see Escalations); recommend the build drop the row |
| Mission Branch Library Community Garden - Monday Nights | image | **Bad seed** — no such branch in Hennepin County; it is a San Francisco library. Also gone from feed |
| Maplewood Celebrate Summer | image | Aged out of feed (summer event) |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of feed; `vetterstoneamphitheater.com` is a hard-403 domain |
| Music in the Park Thursdays - Mankato | image | Aged out of feed |
| Movies in the Park - Mankato | image | Aged out of feed |
| Moorhead Summer Splash Event | image | Aged out of feed |
| Winona Parks & Rec Summer Activities | image | Aged out of feed |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out of feed (umbrella row; individual Urban Air location rows exist separately and carry images) |
| Bump & Putt Family Fun Center | website | No first-party site after 7 runs; deliberately kept open as a defect marker for the dead URL it ships (see Escalations) |
| Summer Outdoor Festival - Brainerd | website | No event of this name exists; misnamed row. Aged out of feed |
| Pizza King Station | website | **Bad seed** — no Minnesota location exists; name matches an Indiana chain. Gone from feed |
| Toddler Tuesday - ECFE | website | Item name and logged address describe different things; the plausible URL is a trap (see Escalations). Gone from feed |
| 688 rows | website | Category **roll-up**, not a per-item work unit — never dispatch research on it |

## Escalations

These need a build-stage or human fix; the fixer cannot close them by searching, and re-searching them nightly can never succeed.

**NEW — Lake Ann Park has the wrong stored address.** The feed stores `6800 Birch Dr, Chanhassen, MN 55317`. The park is actually at **1456 W 78th St, Chanhassen, MN 55317** — agreed by Yelp, Waze, Bipper Media, and the City of Chanhassen's own parks site (`chanrec.com/284/Lake-Ann-Park`, which 301s into `chanhassenmn.gov`). The item name and website are both correct, so this is the wrong-address-on-an-otherwise-correct-row class found previously on Kelley Park, Pine Tree Pond Park and Bowlero. Per standing practice, blank `latitude`/`longitude` when correcting the address — STEP 4.9 skips populated coordinates, so a corrected address with an uncorrected pin never self-heals.

**NEW — Cameron Park (Bemidji) has a real street address available.** Stored value is the vague `Lake Bemidji, Bemidji, MN`. The venue's own Visit Bemidji listing states **2504 Birchmont Dr NE, Bemidji, MN 56601**. Populating it is a straight improvement and would also let the coverage/city-resolution passes attribute the row properly.

**Two image candidates rejected on licence, not relevance.** Both were on-topic photographs of the correct venue; neither fits a sanctioned route (`site_photo` = the venue's own page body, `og_image`, `facebook`, or CC-licensed `stock_openverse_specific`):

- *Lake Ann Park* — a genuine iPhone photograph (`i0.wp.com/dansalamonerealtor.com/.../img_9065.jpg`, alt "Paddleboarding on Lake Ann") on a commercial realtor's community-profile page. Third-party rehost, all-rights-reserved by default, not the venue's own page. Same provenance class as the Wanderlog rejects.
- *Cameron Park (Bemidji)* — a Bemidji Pioneer staff photograph on `cdn.forumcomm.com`, credited to Annalise Braught, caption "Cameron Park features a swimming beach and bathhouse…". A copyrighted newspaper photo with no redistribution licence, served through an unstable `dims4` transform URL.

If the project wants either of these, the correct route is to seek permission or a licensed copy — not to hotlink.

**Bump & Putt Family Fun Center — the feed is shipping a broken link, 7th consecutive confirmation.** `https://www.brainerd.com/business/bump-n-putt-family-fun-park/` returned a hard **404** again today ("Sorry! That page doesn't seem to exist"). The build should blank that URL. The stored address `Four miles north of Nisswa, MN` is also wrong; correct is **29107 State Hwy 371, Pequot Lakes, MN 56472**, phone **218-568-8833**. No first-party site or own Facebook page exists after seven runs. Status is **open, seasonal closure possible** — an outdoor attraction in September — but there is *no evidence of permanent closure*, so this must not be closed as "confirmed closed". This row is deliberately kept OPEN because closing it would bury the dead-link defect it is currently the only marker for.

**Bowlero Brooklyn Park — wrong ZIP and a stale canonical URL, re-confirmed first-hand.** The venue's own page states **7545 Brooklyn Blvd, Brooklyn Park, MN 55443**; the feed stores `55445`. `bowlero.com/location/bowlero-brooklyn-park` returns **301 → `https://www.luckystrikeent.com/location/lucky-strike-brooklyn-park`**, which is the URL to store. Venue is open and operating normally. Its image row is a settled reject: the location page's photos are shared Contentful brand assets, proven again this run by identical alt text ("Family smiling and holding bowling balls together in a vibrant bowling center with neon lighting") appearing verbatim on the Chicago and Denver location pages.

**Rubio's Rewards Thursday Kids Free Meal — bad seed, and the most serious of these.** Rubio's Coastal Grill operates only in AZ, Southern CA and NV; there are **no Minnesota locations**. This `meal_deals` row advertises a kids-eat-free deal that does not exist in this state — a factual claim a family would act on at a counter. Recommend the build **drop the row** rather than keep seeking an image for it.

**Mission Branch Library Community Garden — bad seed.** No "Mission Branch Library" exists in the Hennepin County system; it is a San Francisco Public Library location. Recommend the build drop the row.

**Toddler Tuesday - ECFE — the canonical venue-substitution trap.** The logged address `10 Coon Rapids Boulevard, Coon Rapids MN 55448` is the **Urban Air Trampoline & Adventure Park** retail location, not an ECFE site. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/`; **reject it** — attaching a paid trampoline-park URL to a row labelled ECFE misrepresents a sliding-fee district parenting class as a commercial jump session. Build fix: retitle the row, or correct the address to the real Anoka-Hennepin ECFE site.

**The highest-leverage fix remains structural, not per-item:** have the build **auto-close an unresolved row once its item has left the published feed**. That single change would drain **12 of the 20 open rows** today. The fixer cannot close them by searching, so they accrue forever and train the reader to skim the queue.

## Diagnostics

- **Run date**: derived from the GitHub API `Date` header (`Sun, 06 Sep 2026 09:40:25 GMT`), not the sandbox clock, per the standing rule that the local clock and the injected date have both been wrong *in agreement*. They happened to agree with the server today.
- **Token**: fetched and validated at STEP 1 (fail-fast gate) — 93 chars, `github_pat_` prefix, no whitespace; an authenticated GET succeeded before any research work began.
- **Base validation**: PASS. Header is exactly the 10-column schema; 2750 rows, consistent with monotonic growth (2545 on 09-04 → 2640 on 09-05 → 2750 today). The local `error_log.csv` was **blob-SHA1-identical** to the GitHub remote (`a3014f05…`), so there were no unmerged owner edits to preserve. No `log_base_rejected`.
- **Freshness**: `run_summary` row dated 2026-09-06 **present** — the day's build completed (repo `pushed_at` 08:32 UTC). No `no_run_summary_today`.
- **Row integrity**: all 2750 prior rows preserved byte-identically; exactly one `fixer_summary` row appended. No resolved row was re-opened, edited or deleted.
- **Routes probed this run**: `chanhassenmn.gov` hard-403 on the parks path, on the CivicPlus `FacilityDirectory/10/532` path, and via the `chanrec.com` alias (301 back into the 403 host). `visitbemidji.com/venue/cameron-park/` fetched successfully but carries no body images. `bemidjimn.recdesk.com` 404, `findbemidji.com` connection refused, Yelp 403. The five settled negatives (og:image, Facebook albums, Openverse, Wikipedia REST, Wikimedia Commons) were **not** re-probed, per standing guidance.
- **Verification discipline**: both subagent "candidate found" results were independently checked before being written to the log, and both were overturned. Consistent with the standing finding that a subagent's RESOLVED is a candidate, not a verdict.
- **Publish**: log and findings both committed to GitHub and verified by size + changed `sha` (see below).

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
