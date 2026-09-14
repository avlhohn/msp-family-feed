# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-14**, finished **04:52 US Central (09:52 UTC)**. Run date derived from the GitHub API `Date` response header (`Mon, 14 Sep 2026 09:52:39 GMT`), not the sandbox clock.

## Summary

Open queue at start: **19 rows / 18 distinct items** — 5 `unresolved_website` (one of which is the `688 rows` category roll-up, never dispatchable) and 13 `unresolved_image`.

Resolved this run: **0** — website 0; image 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0).

Left open: **19 rows / 18 items**, rolling to tomorrow. No regressions: all 3,535 carried rows are byte-identical to the base, and all 536 previously-resolved rows are preserved untouched.

The run was scoped before any research was dispatched, which is what keeps a zero-resolution run cheap. Only **6 of the 18 items still exist in today's published feed**; 12 have aged out and are queue residue rather than live defects. Of those 6, five are settled negatives on first-hand evidence — two are chain-promotion image rows that are structurally unresolvable, one fails the recurrence test, one is a bad seed, and one is licence-bound. That left exactly **one item with any discovery left** (Lake Ann Park); one subagent was dispatched, closed 11 further routes, and returned a clean negative.

Zero is the correct outcome here. Lowering the verification bar is the only thing that would move the number, and the standing rule is not to. What the run produced instead is **one new structural finding** — a gap in the STEP 4.5 image-backfill gate, which went live in the nightly for the first time today, that makes the Bowlero row unreachable by the very pass built to drain it — plus **three escalations re-verified first-hand** rather than restated from the last report.

## Resolved this run

None this run.

Two rows were **appended**, both dated 2026-09-14, step `STEP4_fixer`: the mandated `fixer_summary` (info), whose open-queue census is recomputed from the log file itself at write time so it cannot drift from this report; and `curated_stock_gate_gap` (warning), the new finding under Diagnostics. No existing row was modified.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | image | Licence-bound, not discovery-bound. ~36 routes now closed, 11 of them today. The city's own photos sit behind a hard 403 and every fetchable copy is a third-party rehost. |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled negative on the recurrence test — its imagery is Contentful brand assets that appear identically on the Blaine and Lakeville MN sibling pages, i.e. marketing, not a photo of this venue. The real defect on this row is the wrong ZIP; see Escalations. **Also newly shown to be unreachable by STEP 4.5 — see Diagnostics.** |
| Denny's Thursday Kids Eat Free | image | Structurally unresolvable. A `meal_deals` row is a promotion, not a venue, so there is no "photo of this exact thing" to find. `dennys.com` 403s both the og:image and page-body routes; its only Facebook asset is a chain-wide brand graphic. Do not re-queue for search. |
| Perkins Tuesday Kids Eat Free | image | Structurally unresolvable, same reason. `perkins.com` times out, MN location pages 403, and `eatatperkins.com` carries only menu product shots that recur on ND/KS/FL siblings. The deal itself is genuine — this is an image gap only. |
| Rubio's Rewards Thursday Kids Free Meal | image | Bad seed, not an image gap — the chain has no Minnesota presence. See Escalations. |
| Bump & Putt Family Fun Center | website | No first-party site exists after 11 runs, but the row is deliberately kept open as a defect marker for the dead URL it still ships. See Escalations. |
| Maplewood Celebrate Summer | image | Aged out of the feed. |
| Mission Branch Library Community Garden - Monday Nights | image | Aged out. Also a bad seed — no "Mission Branch Library" exists in the Hennepin County system; it is a San Francisco Public Library location. |
| Moorhead Summer Splash Event | image | Aged out of the feed. |
| Movies in the Park - Mankato | image | Aged out of the feed. |
| Music in the Park Thursdays - Mankato | image | Aged out of the feed. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of the feed. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out. The umbrella row is gone; the surviving per-location rows are different items and must not be merged into it. |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed. |
| Pizza King Station | website | Aged out. Bad seed — no Minnesota location exists; the name matches an Indiana chain. |
| Summer Outdoor Festival - Brainerd | website (x2 rows) | Aged out. No event of this name exists; Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival. |
| Toddler Tuesday - ECFE | website | Aged out. The item name and its logged Coon Rapids address describe different things; a research pass will confidently propose the Urban Air URL and that must be rejected. |
| 688 rows | website | Category roll-up written by the build, not a per-item work item. Never dispatch research on it. |

**Bump & Putt is deliberately NOT closed.** Closing it with a negative resolution would bury the fact that the feed actively ships a broken link to families. That closure was made once before and explicitly reverted; it stays open as a defect marker until the row is either repaired or dropped from the feed.

### Escalations — re-verified first-hand this run

These three are data defects, not image-search failures, and each was checked against the source today rather than restated from the previous report. They are recorded here rather than as recurring log rows, because a warning that can never be resolved trains the next reader to skim the block.

1. **Bump & Putt Family Fun Center — the stored website is a hard 404, for the eleventh consecutive run.** `brainerd.com/business/bump-n-putt-family-fun-park/` returns exactly *"Sorry! That page doesn't seem to exist."* The feed ships this link live. The remedy is to blank the `website` field or drop the row, not to keep searching for a photo of a venue whose only recorded URL is dead.

2. **Bowlero Brooklyn Park (Lucky Strike) — ZIP mismatch.** The venue's own page states *7545 Brooklyn Blvd., Brooklyn Park, MN **55443***; the feed stores **55445**. Per the standing rule, a corrected address means `latitude`/`longitude` must be blanked and re-geocoded — STEP 4.9 skips populated coordinates, so a corrected address with an uncorrected pin never self-heals.

3. **Rubio's Rewards Thursday Kids Free Meal — the chain has no Minnesota presence.** Confirmed **82 restaurants across California (60), Arizona (17) and Nevada (5) only**. The `meal_deals` row advertises a deal that cannot be honoured at any Minnesota counter. This is a bad seed and should be dropped, not image-backfilled. (`rubios.com/locations` returns only CSS/JS to WebFetch; the count came from search.)

## Diagnostics

**STEP 1 was clean.** The local `error_log.csv` was byte-identical to the remote (blob `332df94e920570cde7ae4ec1ab3691e0773ffbfa`), so there was no owner-edit divergence and no `log_base_rejected`. Today's build marker was present (`Run 2026-09-14 (Monday) COMPLETE … 7,157 rows`), so no `no_run_summary_today` row was written. The header matched the 10-column contract exactly and row growth remains monotonic across runs. The GitHub token was fetched and validated at the *start* of the run, before any research, so a stale credential could not discard completed work at publish time.

**NEW — the STEP 4.5 gate excludes 221 rows it should reach, and one of them is in this queue.** STEP 4.5 ran inside the nightly for the first time in the project's history today (marker: 36 sites resolved, 205 rows upgraded, `stop_reason: deadline`). Its eligibility gate admits `image_source ∈ {curated_category, stock, openverse_named, blank}` and therefore **excludes `curated`**. That is right for a hand-picked override — and wrong for **221 of the 907** `curated` rows, which carry generic stock (`images.pexels.com`) rather than a chosen photo. Those 221 rows share just **36 distinct assets**, and **25 assets are reused across 210 rows**: one pexels photo covers 48 unrelated bar-and-grill rows, another 36 unrelated pizza rows, another 26 farmers-market rows. **151 of the 221 carry a website**, so they would be 4.5-eligible if the gate could tell the two senses of `curated` apart.

This is not cosmetic for this queue. **`Bowlero Brooklyn Park (Lucky Strike)` has an open `unresolved_image` row and sits inside the excluded set**, so the backfill pass built to drain rows like it can never reach it — and the gap presents as "nothing to do" rather than as an error, which is the same silent-zero shape this project has already hit with a skipped step, a lapsed log signal and a filter vocabulary gap.

Suggested fix: treat `curated` as eligible when `image_url`'s host is a stock provider (pexels / unsplash / pixabay). That preserves the genuine hand-picked overrides the exclusion exists to protect, while freeing the mislabelled rows. Logged as `curated_stock_gate_gap` (warning).

**Eleven further Lake Ann Park routes closed.** All attempted first-hand this run, all negative: Yelp (403), Wheree (403), Lake-Link (403), stevepemberton.com (text only, no images), Christa Reed Photography (family portraits taken *at* the park — not photographs *of* the park), Adam Johnson Minnesota Photography (no Lake Ann images), the 2024 Parks & Rec report on FlippingBook (re-confirmed text-only), the Chanhassen Historical Society gallery (no park images), Explore Minnesota (park not featured), RPBCWD (watershed diagram only, no photograph), and the Wikipedia article *Lake Ann (Minnesota)* (explicitly carries no image). Combined with the ~25 routes closed on prior runs, this item is licence-bound and further searching is the wrong spend.

**Method notes.** The feed cross-check uses exact normalized-title equality. A token-overlap matcher at 0.6 was tried first and returned 96 "matches" for Lake Ann Park, 100 for Denny's and 99 for Perkins — matching on generic words like *lake*, *park*, *kids* and *free*, and resurfacing the known Toddler-Tuesday/Winona and Movies-in-the-Park/Minneapolis false positives. It is not evidence of presence and was discarded. The research subagent read its item list from a file on disk rather than from a hand-typed prompt, and its brief named prior confabulations explicitly (an invented image description, a non-resolving domain, a Flickr account belonging to a different town); it returned specific URLs with per-route outcomes and no fabrications.

**Reserved-namespace check.** `errlog_step7.py` section 5 counts `ical_feed_pull`, `deal_source_*` (prefix match), `image_backfill` and `run_summary`, scoped by `run_date` — so rows this fixer writes dated 2026-09-14 share a namespace with the build's own assertions, and a carelessly named finding would fail tomorrow's build. Both new `issue_type` values were checked against that set before writing, and the append script asserts it independently.

**Append control.** With zero resolutions the write is a pure append, so byte-preservation is verifiable directly: the first 1,107,477 bytes are identical before and after, which distinguishes "appended 2 rows" from "my writer silently rewrote every line". Final file is **1,108,641 bytes, 3,537 data rows, 3,538 CRLF, 0 bare LF**. The script also hard-fails on a malformed run date, refuses to run twice for the same date, and asserts CRLF termination before appending.

## Files

- `error_log.csv` — https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- `error-fixing-findings-latest.md` — https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
- Local: `Agents and Workflows/error_log.csv`
- Local: `Agents and Workflows/error-fixing-findings-latest.md`
