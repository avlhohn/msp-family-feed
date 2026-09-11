# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-11**, finished **08:15 US Central (13:15 UTC)**. Run date derived from the GitHub API `Date` response header, not the sandbox clock.

## Summary

Open queue at start: **19 rows / 18 distinct items** — 13 `unresolved_image`, 6 `unresolved_website`. Cross-checked against the published feed: **6 of the 17 real items still ship**; 11 have aged out. (The 18th label, `688 rows`, is a category roll-up, not an item.)

Resolved this run: **0** — website 0; image 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0).

Left open: **19 rows** (6 website, 13 image). Zero regressions — all 3,171 carried rows verified byte-identical.

Zero resolutions is the correct outcome here, not a shortfall. The remaining image queue is **licence- and access-bound rather than discovery-bound** — a diagnosis now confirmed across four consecutive runs — and the verification bar was deliberately not lowered to move the number. The useful work this run was closing five further routes on the only in-feed municipal item, and re-verifying the three standing escalations first-hand so they carry today's evidence instead of reading as repeated boilerplate.

## Resolved this run

None this run.

## Still open

All 19 rows roll forward. Grouped by *why*, because "still open" alone invites the identical search tomorrow.

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park (Chanhassen) | image | Licence/access-bound; 5 NEW routes closed today. Real photos exist, none redistributable. **In feed** |
| Denny's Thursday Kids Eat Free | image | Structurally unresolvable — a *promotion*, not a venue, so there is no "photo of this exact thing". **In feed** |
| Perkins Tuesday Kids Eat Free | image | Same structural reason. The deal itself is genuine; only the image is missing. **In feed** |
| Rubio's Rewards Thursday Kids Free Meal | image | Bad seed — no MN locations at all (see Escalations). **In feed** |
| Bowlero Brooklyn Park (Lucky Strike) | image | Settled negative — all 6 location-page images are Contentful brand assets recurring on the Blaine and Lakeville MN sibling pages. **In feed** |
| Bump & Putt Family Fun Center | website | No first-party site after 9 runs; kept open deliberately as the marker for a broken link the feed still ships. **In feed** |
| Maplewood Celebrate Summer | image | Aged out of the feed |
| Niko Moon Concert – Vetter Stone Amphitheater | image | Aged out of the feed |
| Music in the Park Thursdays – Mankato | image | Aged out of the feed |
| Movies in the Park – Mankato | image | Aged out of the feed |
| Moorhead Summer Splash Event | image | Aged out of the feed |
| Winona Parks & Rec Summer Activities | image | Aged out of the feed |
| Urban Air Trampoline Parks – MN Locations | image | Aged out of the feed |
| Mission Branch Library Community Garden | image | Aged out **and** a bad seed (it is a San Francisco library) |
| Summer Outdoor Festival – Brainerd (×2 rows) | website | Aged out; no event of this name exists — misnamed row |
| Pizza King Station | website | Aged out; no MN location exists (name matches an Indiana chain) |
| Toddler Tuesday – ECFE | website | Aged out; item name and logged address describe different things |
| `688 rows` | website | Category **roll-up label**, not a work item — never dispatch research on it |

### Routes closed on Lake Ann Park this run

One bounded subagent, aimed at the single genuinely untried angle: a city publishing official park photos at an **unlinked** URL or on a **separate host** — the route that resolved Cameron Park in Bemidji last run. All five below are new; none re-probes a settled negative.

- **City of Chanhassen Instagram** — account is genuinely official, but renders as CSS/JS with no fetchable asset.
- **2024 Parks & Rec Annual Report (FlippingBook)** — text extracted; no reachable embedded image URLs.
- **Chanhassen ArcGIS StoryMaps** — the fetch returned content for *Tempe*, a URL/host mismatch. Treated as unverified and discarded rather than narrated as a finding.
- **ActiveNet recreation portal** (`anc.apm.activecommunities.com/chanhassen/`) — metadata only, and its photos are credited to a third-party photographer, so licence-rejected regardless.
- **Carver County Historical Society** — no Lake Ann Park photo archive.

## Escalations

Each re-verified **first-hand today**, not recalled from prior runs. These are source-data defects the fixer cannot close by searching; they need a build-stage fix.

- **Bump & Putt Family Fun Center** — `brainerd.com/business/bump-n-putt-family-fun-park/` returned a hard **404** again today (*"Sorry! That page doesn't seem to exist."*), the **9th consecutive run**; the feed is actively shipping a broken link. Stored address `Four miles north of Nisswa, MN` is wrong — correct is **29107 State Hwy 371, Pequot Lakes, MN 56472**. The stored coordinates (46.520522, −94.288609) were geocoded *from* the wrong address, so the pin must be blanked and re-geocoded as part of the same fix — the address defect and the coordinate defect are one fix, not two. No evidence of closure and no evidence of current operation; those are different findings, and the row must not be closed as "confirmed closed".
- **Bowlero Brooklyn Park (Lucky Strike)** — the venue's own page states ZIP **55443**; the feed stores **55445**. The stored URL `bowlero.com/location/bowlero-brooklyn-park` is a redirect since the Bowlero→Lucky Strike rebrand; the canonical URL is `https://www.luckystrikeent.com/location/lucky-strike-brooklyn-park`.
- **Rubio's Rewards Thursday Kids Free Meal** — reconfirmed today: Rubio's Coastal Grill operates **82 units across CA, AZ and NV only, with no Minnesota presence**. This `meal_deals` row therefore advertises a kids-eat-free deal that cannot be honoured at any counter in the state. A `deal_description` is a factual claim a family will act on at a counter — recommend the build **drop the row** rather than keep seeking an image for it.
- **Mission Branch Library Community Garden** — same bad-seed class: no such branch exists in the Hennepin County system; Mission Branch Library is a San Francisco Public Library location. Recommend dropping.
- **Structural, and the highest-leverage of these:** have the build **auto-close an unresolved row once its item has left the published feed**. That single change would drain **11 of the 19** rows today. The fixer cannot close them by searching, so they accrue indefinitely and dilute the queue.

## Diagnostics

- **`log_base_rejected`** — the local session copy of `error_log.csv` (978,672 b, mtime 2026-09-10) was rejected as the carry-forward base. It held **3,137 rows against the GitHub canonical 3,171**, short by 34 rows all dated 2026-09-10 (24 `attempted_no_photo`, 3 `wrong_website`, plus step-4.5 and WebFetch diagnostics). A row-set diff confirmed the local copy was a **strict subset** — 0 rows present only in local — i.e. a mid-run snapshot rather than divergent history, so adopting it would have silently deleted 34 rows of published history. Both copies passed the 10-column header check; the GitHub copy was used.
- **`no_run_summary_today`** — no `run_summary` row dated 2026-09-11 (latest is 2026-09-10). Corroborated two independent ways: the published `msp_family_guide.json` carries `generated_date: 2026-09-10`, and the repo's last push was 2026-09-11T01:08Z (2026-09-10 evening CT). So this is a genuinely **absent build**, not merely a missing marker, and the fixer worked yesterday's queue against yesterday's feed. Safe, but the ordering is worth noting.
- **Date derivation** — `TODAY` taken from the GitHub API `Date` header (`Fri, 11 Sep 2026 13:07:33 GMT`). The sandbox clock happened to agree this run, but was not trusted as the source.
- **Integrity** — all **3,171 carried rows verified byte-identical** after the edit; 536 previously-resolved rows preserved untouched; 0 re-opens; +3 new rows (2 diagnostics, 1 `fixer_summary`).
- No base copy was skipped for AI-ineligibility (the one-time Drive fallback did not fire). No publish retries were required.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
