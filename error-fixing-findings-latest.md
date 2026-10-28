# MSP Family Guide — Error Fixing (Latest)

Run date: 2026-10-28 (finished ~16:40 UTC)

## Summary
- Open queue at start: 5 (1 unresolved_website, 4 unresolved_image)
- Resolved this run: 0 (website 0; image 0 — og_image 0 / facebook 0 / stock_openverse_specific 0)
- Left open (rolling to tomorrow): 5

## Resolved this run
None this run.

## Still open
| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | unresolved_image | og:image not visible via WebFetch; Openverse API unreachable this run |
| Denny's Thursday Kids Eat Free | unresolved_image | og:image not visible; chain homepage is generic |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | chain site; no specific image verifiable |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Openverse unreachable; no specific image verified |
| Bump & Putt Family Fun Center | unresolved_website | no official site confirmed in search results (only travel aggregators/articles) |

## Diagnostics
- `no_run_summary_today`: no run_summary row dated 2026-10-28 in base (latest 2026-10-26).
- Token Drive file id in prompt (12-gYyeDis...) was not found; token located by title in the same archive folder.
- Openverse API timed out from both cloud and local shells.
- GitHub API is blocked from the cloud sandbox; publish done via the local device shell.

## Files
- https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
