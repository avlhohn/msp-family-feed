# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-07**, finished 09:51 UTC (04:51 America/Chicago). Run date derived from the GitHub API `Date` response header, not the sandbox clock.

## Summary

Open queue at start: **20 rows / 19 distinct items** — 6 rows (5 items + 1 roll-up) `unresolved_website`, 14 rows / 14 items `unresolved_image`.

Resolved this run: **0** — website 0; image 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0).

Left open: **20 rows**, rolling to tomorrow.

A zero-resolution run is the correct outcome here rather than a failure, and the reason is structural. A feed cross-check shows **only 7 of the 19 distinct items still exist in the published feed**; 12 have aged out of the 2026-09-06→2026-10-31 window and one (`688 rows`) is a category roll-up that was never a work item. Of the 7 still live, 4 are settled negatives or known bad seeds, so research was scoped to the **3 items that still had a genuinely untried route**. All three came back negative with specific evidence, and two of them are now closed questions rather than open searches — which is the real product of this run.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | image | In feed. All routes now closed: `chanhassenmn.gov` hard-403 (incl. CivicPlus FacilityDirectory), `chanrec.com` 301s back to it, and **`carvercountymn.gov` also hard-403s (new this run)**. No Explore MN listing. The last real photo found was licence-blocked (a realtor's page). |
| Cameron Park (Bemidji) | image | In feed. `visitbemidji.com` venue page returns 200 but carries zero body images. **City of Bemidji runs RecDesk, not CivicPlus — its facility endpoint returns organization-not-found (new this run)**, so the richest historical vein does not exist for this city. No Explore MN listing. |
| Bowlero Brooklyn Park (Lucky Strike) | image | In feed. **Now a settled negative on hard evidence** — all six images on the location page are shared Contentful brand assets recurring identically on the Blaine and Lakeville sibling pages. No venue-unique photo exists on the official site. |
| Denny's Thursday Kids Eat Free | image | In feed, but undepictable by construction — a national multi-location promo, not a place. |
| Perkins Tuesday Kids Eat Free | image | In feed, but undepictable by construction — a national multi-location promo, not a place. |
| Rubio's Rewards Thursday Kids Free Meal | image | In feed, but a **bad seed** — Rubio's has no Minnesota locations at all. See escalations. |
| Bump & Putt Family Fun Center | website | In feed. **Held open deliberately** — 6+ runs confirm no first-party site exists, but the row is the only thing keeping a live broken link visible. See escalations. |
| Maplewood Celebrate Summer | image | Aged out of the feed. |
| Mission Branch Library Community Garden - Monday Nights | image | Aged out; also a **bad seed** (no such branch in Hennepin County). |
| Moorhead Summer Splash Event | image | Aged out of the feed. |
| Movies in the Park - Mankato | image | Aged out. Fuzzy matches in the feed are Minnetonka and White Bear Township screenings — different events, not this row. |
| Music in the Park Thursdays - Mankato | image | Aged out of the feed. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of the feed. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out as a roll-up; the feed carries separate per-location rows instead. One location's photo cannot represent a chain-wide item. |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed. |
| Summer Outdoor Festival - Brainerd | website | Aged out; also no event of this name exists (Brainerd's real summer events are Lakes Jam and the Crow Wing Viking Festival). |
| Pizza King Station | website | Aged out; also a **bad seed** — no MN location; the name matches an Indiana chain. |
| Toddler Tuesday - ECFE | website | Aged out. The only feed row matching the title is a *Winona* Toddler Tuesday at the Minnesota Marine Art Museum — a different item. |
| 688 rows | website | A category **roll-up** the build writes, not a per-item work unit. Can never be searched closed. |

## Rejected candidate worth recording

A subagent reported a **"Bemidji Parks & Recreation" Flickr account** (`flickr.com/photos/197884014@N03`, 9 photos) as a live lead — attractive because a city's own Flickr album is clean on both provenance and licence, and that exact route resolved Lum Park in an earlier run. Direct verification of the account page shows it is actually **"Cameron Parks & Recreation"** — the parks department of a town named Cameron, not the Cameron Park in Bemidji. The search had matched on *Cameron* + *Parks* and the agent narrated it as the city's account.

This is the same name-collision class as the earlier Lake Bemidji State Park and Antioch-Illinois-marina traps, and it was caught only by fetching the account page rather than trusting the agent's label. It reinforces the standing rule: a subagent's verdict is a candidate, never a decision.

## Escalations for the build stage

These cannot be closed by searching. They need action elsewhere, and each has now been re-reported across multiple runs without being fixed.

- **Bowlero Brooklyn Park** — stored ZIP `55445` is wrong; the venue's own page states **55443**. Stored website `bowlero.com/location/bowlero-brooklyn-park` 301s to `luckystrikeent.com/location/lucky-strike-brooklyn-park`, which is the canonical URL to store.
- **Lake Ann Park** — stored address `6800 Birch Dr` is wrong; the park is at **1456 W 78th St, Chanhassen, MN 55317**. Blank the lat/lon when correcting, since the stored coordinate was geocoded from the bad address and STEP 4.9 skips populated coordinates.
- **Cameron Park (Bemidji)** — stored address is the vague `Lake Bemidji, Bemidji, MN`; the real address is **2504 Birchmont Dr NE, Bemidji, MN 56601**.
- **Bump & Putt Family Fun Center** — the feed still ships `brainerd.com/business/bump-n-putt-family-fun-park/`, a hard 404, for the **8th consecutive run**. Correct address is 29107 State Hwy 371, Pequot Lakes, MN 56472; phone 218-568-8833. The venue operates and is not closed — blank the dead URL rather than closing the row.
- **Rubio's Rewards Thursday Kids Free Meal** — bad seed; Rubio's operates only in AZ, CA and NV. This row advertises a kids-eat-free deal that does not exist in Minnesota, which is a factual claim a family would act on at a counter. Recommend dropping the row.
- **Mission Branch Library Community Garden** — bad seed; Mission Branch is a San Francisco Public Library location. Recommend dropping the row.
- **Highest-leverage structural fix, unchanged:** have the build **auto-close an unresolved row once its item has left the published feed**. Today that single change would drain **12 of the 20** open rows. The fixer cannot close them by searching, so they accrue indefinitely and dilute the queue.

## Diagnostics

- `log_base_rejected`: none. Base validated — exact 10-column header, 2751 rows, monotonic growth (2640 → 2750 → 2751), and the local mount copy was byte-identical to the GitHub remote by blob SHA-1 `9b0e3a54`.
- `no_run_summary_today`: **triggered**, and today it reflects a real condition rather than a merely missing marker. Max `run_date` in the base is 2026-09-06, the repo's last push was 2026-09-06T09:48Z, and the feed's `generated_date` is 2026-09-06 — **the day's build had not run yet, so the fixer ran before the build**, the reverse of the intended order. This run therefore worked yesterday's queue against yesterday's feed. That is safe for the queue (all 20 open rows predate today), but rows today's build adds were not seen here, and if the build later publishes from a base fetched before this commit, these two diagnostic rows could be overwritten.
- Openverse: not probed. It is a settled negative (0 hits across 2026-08-21, -28 and -29) and returned 504 Gateway Timeout on the two most recent attempts.
- Publish: log and findings both committed on the first attempt; no retries needed.
- **Housekeeping:** a stale `.ghtok` file (93 bytes, dated 2026-08-20) is sitting in the working folder from an old run. Nothing this run reads or publishes it, but a credential in a synced folder is worth deleting by hand.

## Files

- Error log: <https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv>
- Findings report: <https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md>
