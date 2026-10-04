# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-10-04 (Sunday) · **Finished:** ~15:05 UTC (10:05 CDT). Date taken from the GitHub API `Date` header (`Sun, 04 Oct 2026 14:54:16 GMT`).

## Summary

- **Open queue at start:** 5 items. 1 `unresolved_website` and 4 `unresolved_image`. These are the same five as on 2026-10-03.
- **Resolved this run:** 0 (website 0, image 0, of which og_image 0, facebook 0, stock_openverse_specific 0).
- **Left open:** 5, rolling to tomorrow.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park (Chanhassen) | unresolved_image | No specific image found. `chanhassenmn.gov` facility and news pages still block fetches. The park-project page has text only. Openverse has no place-specific match (2 results, both off-topic). |
| Denny's Thursday Kids Eat Free | unresolved_image | Only generic or logo images. **Possible stale row:** the subagent says Denny's own FAQ gives "days and participation vary by location" and never says Thursday. Not verified by the parent. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | The og:image is a logo SVG and the body art is chain-wide. **Possible stale row:** the subagent says Rubio's weekly-deals page lists no Thursday kids offer. Not verified by the parent. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | The og:image is the chain's share card and every page photo is a chain-wide promo. The venue's own Facebook page (`facebook.com/LuckyStrikeBrooklynPark/`) is linked from the location page but can't be fetched by the tooling, so someone should check it by hand. |
| Bump & Putt Family Fun Center | unresolved_website | Directory listings only (Yelp, Manta and others). They agree on 29107 State Hwy 371, Pequot Lakes MN 56472, but no official site or venue Facebook page was found. |

## Diagnostics

- **`no_run_summary_today` (info, logged).** Today's daily build was **running while the fixer ran**. It started at 09:53 CDT and was writing `_compiled_work.json` at 09:56. Nothing had been published to GitHub yet, so the base was the remote `main` at commit `fbee64f46ba2`: 5,375 rows, blob `00dfc449135b`, valid 10-column header.
- **Race handling.** The fixer did **not** overwrite the workspace `error_log.csv`, because the in-flight build is using it. The fixer added 2 rows to the remote only, after checking that the remote blob had not changed since it was read. The build's STEP 7 two-writer check will find the remote 2 rows ahead and must merge rather than overwrite. Otherwise these two info rows are lost. They are the only loss possible: no resolutions were made.
- **Credential.** The Drive `msp_feed_gh_token.txt` still holds the revoked pre-rotation token (401). The workspace `github_token.txt` (200, push access) was used, and no token value was printed. This is the same finding as `drive_token_stale_check` (2026-10-03), so it was folded into the summary row instead of being added again. **Owner action is still outstanding:** update the Drive file.
- **Inflow.** Neither mandated issue type has gained new rows. Yesterday's starvation finding stands.
- No `log_base_rejected` this run. Publish succeeded on the first attempt: blob `3d57cf90fc80`, 1,765,210 bytes, matched the local SHA-1.

## Files

- error_log.csv: <https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv>
- error-fixing-findings-latest.md: <https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md>
- Local copies are in `Agents and Workflows/.fixer_1004/`: `error_log_fixer_1004.csv`, `base_remote_1004.csv` (the common ancestor) and `queue.json`.
