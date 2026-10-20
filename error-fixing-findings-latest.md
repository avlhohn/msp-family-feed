# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-10-20 (finished 13:07 UTC)

## Summary
- Open queue at start: 5 (unresolved_website 1, unresolved_image 4)
- Resolved this run: 0 (website 0; image 0 — og_image 0 / facebook 0 / stock_openverse_specific 0)
- Left open: 5

## Resolved this run
None this run.

## Still open
| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | unresolved_image | og:image not retrievable via WebFetch; no place-specific image verified |
| Denny's Thursday Kids Eat Free | unresolved_image | only generic/topical imagery available |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | only generic/topical imagery available |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | no specific image verified |
| Bump & Putt Family Fun Center | unresolved_website | search returned no confident official site (Nisswa MN) |

## Diagnostics
- no_run_summary_today triggered
- Token file id in task prompt was renamed to *OLD-REVOKED*; used current msp_feed_gh_token.txt (id 1QYKN4Ge7kUEQ8M1j0Ze6t3jXnrwRd4Rm). Task prompt should be updated.
- Cloud sandbox GitHub API was blocked; publish done from local device shell.

## Files
- https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
