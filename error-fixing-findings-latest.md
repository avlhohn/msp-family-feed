# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-10**, finished 04:51 US Central (09:51 UTC). Run date derived from the GitHub API `Date` response header, not the sandbox clock.

## Summary

Open queue at start: **20 rows / 19 distinct items** — 14 `unresolved_image`, 6 `unresolved_website`. Cross-checked against the feed published this morning: **7 of the 19 still ship**; 12 have aged out.

Resolved this run: **1** — website 0; image 1 (`site_photo` 1; og_image 0, facebook 0, stock_openverse_specific 0).

Left open: **19 rows** (6 website, 13 image). Zero regressions — exactly one carried row changed, and only in its three resolution columns.

The resolution overturns a negative that five consecutive runs had recorded as settled. It is worth reading the next section rather than the count.

## Resolved this run

| Item | Type | Route | Evidence |
|---|---|---|---|
| Cameron Park (Bemidji) | image | `site_photo` | The City of Bemidji's **own** official park-photo gallery on `ci.bemidji.mn.us`, asset `…/uploads/Cameron_Park_Play_Area.jpg`. Fetched and viewed first-hand: a real photograph (Canon EOS 5D Mk III EXIF, dated 2016-08-31, 756 KB full-res) showing the play structure with climbing wall on wood chips. In-frame signage reads **"BEMIDJI ROTARY CLUB"**, which independently confirms the city from inside the image rather than from its filename. |

Flagged `site_photo` rather than `og_image` per `REAL_PHOTO_SOURCES`: it is a page-**body** image, not a `<head>` tag.

## Why this was missed for five runs — and three corrections

**The gallery is not linked from `/parksandtrails`.** Every prior run checked the parks-and-trails landing page, found only template chrome, and generalised "not linked from the department page" into "the city publishes no park photos." The gallery lives at an unlinked GUID URL (`index.asp SEC=3A34E0DD-C320-46BF-BFA9-0921FA9B2F65`). **Absence from a navigation menu is not absence from a site.**

**Correction 1 — the 2026-09-08 "fabricated asset" finding was half wrong.** Memory records that run as having invented `Cameron_Park_Swimming_Beach_Web.jpg` and `Cameron_Park_Boat_Access_Web.jpg` on a non-resolving host. The *filenames were real*; only the hostname was wrong (`bemidjimn.gov`, which genuinely does not resolve, instead of `ci.bemidji.mn.us`). Both assets exist verbatim on the real host. This matters because "that agent fabricates" is a much stronger prior than "that agent got a hostname wrong," and the stronger prior is what closed the route. Record the narrow error, not the broad one.

**Correction 2 — a licence rejection can itself be wrong.** This run's research subagent found the gallery and then rejected it, citing the site's "All Rights Reserved" footer. That is the wrong bar for this pipeline: every municipal `.gov` carries such a footer, and Kelley Park, Pine Tree Pond, Winona Bandshell and Maple Grove Town Green were all accepted from exactly that kind of page. The licence rule targets **third-party rehosts**, not a venue's own official site. A subagent's REJECTED is a candidate verdict, the same as its RESOLVED.

**Correction 3 — the agent gave bare filenames, not working URLs**, against an explicit instruction. That is what triggered independent verification, which is what produced the resolution. Treat a format violation as a reason to check the substance.

## Still open (19 rows)

| Item | Type | Reason |
|---|---|---|
| Lake Ann Park | image | Licence/access-bound. `chanhassenmn.gov` re-tested today: still hard-403. `chanrec.com` 301s back into it; `carvercountymn.gov` also 403. Openverse re-probed today across 6 queries: 0 results. |
| Denny's Thursday Kids Eat Free | image | Settled negative. A promotion, not a venue — no specific photo exists; chain-wide brand graphics fail the recurrence test. |
| Perkins Tuesday Kids Eat Free | image | Settled negative. MN location pages 403; only chain-wide product shots that recur on out-of-state siblings. |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled negative on hard evidence — all location-page images are Contentful brand assets appearing identically on the Blaine and Lakeville MN pages. |
| Rubio's Rewards Thursday Kids Free Meal | image | Bad seed — see Escalations. No image should be sought for a row that should not exist. |
| Bump & Putt Family Fun Center | website | No first-party site exists (9th confirmation). Kept open deliberately as the defect marker for the dead link it ships. |
| Maplewood Celebrate Summer | image | Aged out of the feed. |
| Niko Moon Concert - Vetter Stone Amphitheater | image | Aged out of the feed. |
| Music in the Park Thursdays - Mankato | image | Aged out of the feed. |
| Movies in the Park - Mankato | image | Aged out of the feed. |
| Moorhead Summer Splash Event | image | Aged out of the feed. |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed. |
| Urban Air Trampoline Parks - Minnesota Locations | image | Aged out (umbrella row; only per-location rows remain). |
| Mission Branch Library Community Garden - Monday Nights | image | Aged out, and a bad seed — no such branch exists in Hennepin County (it is a San Francisco library). |
| Summer Outdoor Festival - Brainerd | website (×2 rows) | Aged out; no event of this name exists. |
| Pizza King Station | website | Aged out; no Minnesota location — the name matches an Indiana chain. |
| Toddler Tuesday - ECFE | website | Aged out; item name and logged address describe different things — see Escalations. |
| 688 rows | website | Aggregate roll-up written by the build, never researched as an item. |

## Escalations

Each was **re-verified first-hand today**, not carried from memory.

**Bump & Putt Family Fun Center — shipping a broken link, 9th consecutive run.** `brainerd.com/business/bump-n-putt-family-fun-park/` fetched again today: hard 404. Stored address `Four miles north of Nisswa, MN` is still wrong; correct is **29107 State Hwy 371, Pequot Lakes, MN 56472** (phone 218-568-8833). The stored coordinates were geocoded *from* the wrong address, so the pin is wrong too — address fix and coordinate blanking are one fix, not two, because STEP 4.9 skips populated coordinates. No evidence of closure **and** no evidence of current operation; those are separate findings and the row must not be closed as "confirmed closed."

**Bowlero Brooklyn Park — wrong ZIP, non-canonical URL.** `bowlero.com/location/bowlero-brooklyn-park` still 301s to `luckystrikeent.com/location/lucky-strike-brooklyn-park`, whose own page states **7545 Brooklyn Blvd, Brooklyn Park, MN 55443**. The feed stores **55445**. Correct both the URL and the ZIP at the build stage.

**Rubio's Rewards Thursday Kids Free Meal — bad seed, and the most serious of these.** Re-confirmed today: Rubio's Coastal Grill operates in **California, Arizona and Nevada only** — no Minnesota locations. Sharpening last run's wording: the promotion itself is real, it is simply **unredeemable in this state**, and the row is addressed "Multiple Twin Cities locations." A `deal_description` is a factual claim a family acts on at a counter. Recommend the build **drop the row**.

**Cameron Park (Bemidji) — the address field still holds a lake.** The image is now resolved; the address is not. Stored value is `Lake Bemidji, Bemidji, MN`. Public sources disagree on the street address (`2504` vs `2609 Birchmont Dr NE`), so no correction should be asserted from search results — this field needs a first-party source. Note the city's own gallery, newly found, may be the route to one.

**Toddler Tuesday - ECFE — venue-substitution trap.** The logged address `10 Coon Rapids Boulevard` is the Urban Air trampoline park. A research pass will confidently propose `urbanair.com/minnesota-coon-rapids/`; reject it — attaching a paid trampoline-park URL to a row labelled ECFE misrepresents a sliding-fee district parenting class as a commercial jump session.

**Structural ask, 7th run.** Have the build **auto-close an unresolved row once its item has left the published feed**. Twelve of today's 19 remaining rows are for items that no longer ship. The fixer cannot close them by searching, so they accrue indefinitely.

**New, bounded opportunity.** The Bemidji gallery is a real municipal photo library and it resolved one item today. It is worth one pass against the other Minnesota municipal items in the queue — but as a *bounded* check of whether a given city runs an unlinked photo gallery, not as a general re-opening of settled negatives.

## Diagnostics

- `log_base_rejected`: **not triggered.** Header exactly the 10-column schema; 3,136 rows in, 3,137 out (+1 `fixer_summary`).
- Base provenance: local copy byte-identical to the GitHub remote by git blob SHA-1 (`52e48c2f8a6fcfc6c77dc17e2d4b8bcd8f72da9b`, 976,747 bytes) — no stale-base or owner-edit divergence.
- `no_run_summary_today`: **not triggered.** The build's `run_summary` marker for 2026-09-10 is present, so the fixer ran after the build and worked a current queue.
- Run date derived from the GitHub API `Date` response header. The date guard in the apply script was **made to fail on purpose** on four branches (empty, malformed `2026-9-10`, non-numeric, out-of-range year) before being trusted to pass.
- Negatives re-probed rather than assumed: Openverse across 6 queries → 0 results; `chanhassenmn.gov` → still hard-403.
- Regression guard: exactly **1** of 3,136 carried rows changed, and only in `resolved_date` / `resolved_by` / `resolution_note`. No resolved row was re-opened, edited or deleted.
- Line endings: 3,138 CRLF, 0 bare LF — published bytes preserve the CSV writer's output verbatim.
- Source-trust note: the image subagent's verdict (REJECTED on licence) was **overridden** after first-hand verification. Its citation also pattern-matched a documented prior confabulation; the chain was verified end to end rather than accepted or rejected on that resemblance.

## Files

- Error log: https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- Findings report: https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
