# MSP Family Guide — Error-Fixing Findings

**Run date:** 2026-09-21 (derived from the GitHub `Date` header, not the sandbox clock)
**Task:** `msp-family-guide-error-fixer`
**Base:** `error_log.csv` @ `avlhohn/msp-family-feed` — 4,139 data rows, header exact 10-column match, 0 wrong-width rows, local copy byte-identical to remote (md5 `fdf66ad3ef121d7937b0aa4ceb8410b6`)

---

## Summary

The open queue held **19 rows** — 13 `unresolved_image` and 6 `unresolved_website` — collapsing to **18 distinct items**. **Zero were resolved.** All 19 stay open and roll forward.

That is the honest outcome rather than a failure to try, and this run finally has first-hand evidence for why. Every still-live item was re-attempted, and the negative was established by the parent task over the Openverse API directly rather than inherited from a subagent's blocked fetch. Three facts, each independently sufficient to make resolution pointless or impossible:

**Eleven of the eighteen items are no longer in the feed.** The published `msp_family_guide.json` (generated 2026-09-21, 6,784 rows) was matched against the queue with an anchored contiguous-token matcher — 6 items present, 11 absent, 1 roll-up. The eleven absent items are summer programming that aged out of the rolling window weeks ago: Maplewood Celebrate Summer, the Niko Moon concert, Music in the Park and Movies in the Park (Mankato), Moorhead Summer Splash, Winona Parks & Rec Summer Activities, Urban Air MN Locations, Mission Branch Library Community Garden, Summer Outdoor Festival – Brainerd (2 rows), Pizza King Station, and Toddler Tuesday – ECFE. Resolving any of them would edit a log row describing a row that no longer exists.

**The six that remain cannot clear the strict bar.** Three of them — Denny's Thursday Kids Eat Free, Perkins Tuesday Kids Eat Free, Rubio's Rewards Thursday Kids Free Meal — carry the address *"Multiple Twin Cities locations."* A row that denotes no single place cannot have a place-specific photo, so the `stock_openverse_specific` route is closed to them by construction, not by a failed search. Lake Ann Park, Bowlero Brooklyn Park and Bump & Putt were each researched first-hand and returned nothing that meets the bar.

**And a resolution would not reach the feed anyway.** Nothing reads resolved rows back into `_compiled_work.json` before the build. This is now measurable: the Bowlero→Lucky Strike correction has been fully evidenced since 2026-08-28 and is **24 days unapplied**.

---

## Resolved this run

None.

---

## Still open

All 19 rows. The six whose items are still live, with what was actually attempted:

**Lake Ann Park** (`unresolved_image`, parks, open since 2026-07-08). The stored website is the full city deep-link `chanhassenmn.gov/departments/parks-recreation/parks-facilities/lake-ann-park`, which **403s to WebFetch**; the Facebook page returns 200 with no rendered images. Openverse, queried by this task over the API, returns **0 results** for "Lake Ann Park Chanhassen". A generic "Chanhassen City Park" Flickr photo exists and was rejected — a photo of *a* park in the city is not a photo of *this* park.

*Correction to a carried note:* the 2026-09-20 record says this row's `website` had degraded to a truncated index path and that the queue row therefore no longer described the feed row. **That is no longer true** — the live row carries the full deep-link. The item is a genuine image candidate again, and was researched as one.

**Bowlero Brooklyn Park (Lucky Strike)** (`unresolved_image`, restaurants). Openverse returns 0 for both "Lucky Strike Brooklyn Park" and "Bowlero Brooklyn Park Minnesota". The queued issue is the *image*; the redirect evidence gathered this run belongs to the website defect and is escalated below rather than used to close an image row.

**Denny's / Perkins / Rubio's** (`unresolved_image`, meal_deals). `dennys.com` 403s, `perkins.com` times out, `rubios.com/locations/` returns 200 but is JS-rendered with no Minnesota content visible. The Openverse hits are instructive and are recorded under Diagnostics.

**Bump & Putt Family Fun Center** (`unresolved_website`, restaurants). Escalated below. This row is deliberately kept open as a defect marker.

The remaining open rows are the eleven aged-out items plus the `688 rows` roll-up, which is a count and not a researchable item.

---

## Diagnostics

### An Openverse 403 reported by a subagent is a TOOL artifact, not a source verdict

Every subagent in this task is restricted to WebSearch and WebFetch, and all three reported Openverse as **403 Forbidden** this run. Queried from the parent over the direct API with an ordinary `User-Agent`, Openverse answered **200 every time**. The API is explicitly exempt from the no-HTTP-client rule; WebFetch simply cannot reach it.

The consequence is larger than one run. A subagent's "Openverse returned nothing" and "Openverse blocked me" are indistinguishable in a report, and both read as *the image does not exist* — so **every negative image verdict this task has ever inherited from a subagent may have been produced by the wrong client**. This is the project's standing silent-failure shape arriving through the tool layer: the search was never performed, and the absence of results was booked as a property of the world.

The correction is architectural, not a matter of care: **subagents do page research; the parent queries Openverse.** Applied this run, which is why the negatives above are first-hand.

### A geographically-specific stock photo is not a depictively appropriate one

The `stock_openverse_specific` route is defined as resolving when the photo depicts *the specific place*. Reading the actual hits shows how easily a matcher keyed on place-plus-name would fail:

- **Denny's + Minneapolis** returns *"Denny's restaurant, George Floyd protest, Minneapolis, MN, June 2020."* Correct city, correct brand, and a civil-unrest photograph on a kids-eat-free card.
- **Perkins + Minnesota** returns two Roseville photos that are **plates of food**, not a venue — and the row denotes every Twin Cities Perkins, not the Roseville one.
- **Rubio's** returns a **Florida** storefront (Dadeland).

The rule this run applies, and recommends be written down: a candidate must pass *venue identity*, *geography* **and** *subject* — and for a multi-location row the first test can never be satisfied, so those rows should be routed away from the image queue rather than re-attempted nightly.

### Three subagent claims were rejected for snippet-sourcing

Per the standing rule that search-result snippets are not a source and a report must be read for internal self-contradiction before its URLs are trusted:

- An address of *"1456 West 78th Street, Chanhassen"* for Lake Ann Park was offered as confirmed in the same report that recorded the city page as **403**. It is snippet-derived and is held as an **unverified lead only**. It carries the signature of a common confabulation shape — the address returned for a park is frequently the administering parks department's own office address, not the site's.
- Bump & Putt's address *"29107 State Highway 371"* and phone *"(218) 568-8833"* were attributed to Yelp "updated August 2026" with **no stated fetch**, and Yelp is on record in this project as returning 403/526 to this pipeline. Rejected as evidence.
- Rubio's per-state location counts came from a scrapehero search result rather than a fetched page. Rejected.

None was written into the log.

### Queue inflow remains dead

Last `unresolved_website` row written **2026-08-16** (36 days); last `unresolved_image` **2026-07-23** (60 days). Meanwhile roughly **566 fixer-shaped rows** — `missing_website`, `generic_image`, `attempted_no_photo` — sit open under `issue_type` values STEP 2's literal selector cannot match, against the **19** it can see. A drained queue and a queue nothing writes to are indistinguishable from inside the queue.

---

## Escalations

**1. Build a consumer for resolved rows.** A resolution written to `error_log.csv` is read by nothing. Until a pass exists that reads resolved rows and writes the corrected `website` / `image_url` into `_compiled_work.json` before the build, a resolution is a note and not a fix, and improving this task's resolution rate cannot improve the feed. The Bowlero case is the measurement: evidenced 2026-08-28, unapplied 24 days.

**2. Ship the Bowlero → Lucky Strike correction.** `bowlero.com/location/bowlero-brooklyn-park` 301-redirects to `luckystrikeent.com/location/lucky-strike-brooklyn-park`, which returns 200, names itself *Lucky Strike Brooklyn Park*, and states **ZIP 55443**. The feed row carries the dead `bowlero.com` URL and **ZIP 55445**. Both the URL and the ZIP are wrong in the published feed. Fetched first-hand again this run.

**3. Bump & Putt has shipped a 404 for five consecutive runs.** `brainerd.com/business/bump-n-putt-family-fun-park/` returns 404, confirmed first-hand. The row stays open deliberately: closing it as "confirmed closed" would be wrong (a prior run's `CONFIRMED_CLOSED` verdict was itself an error — absence under one spelling is not evidence of closure), and closing it at all removes the only thing keeping the broken link visible. Two settled negatives stand: **`goputtnbump.com` is a different business** ~180 km away in Detroit Lakes and must never be attached to this row despite ranking first, and **Nisswa Family Fun Center is not Bump & Putt**.

**4. Auto-close a queue row once its item has left the feed.** Eleven of eighteen items today describe rows that no longer exist. A row whose subject has aged out is not open work, and leaving it in the queue makes the backlog look like unfinished research when it is bookkeeping.

**5. Widen the queue at the source, not the selector.** The fix for the ~566 unreachable rows is to constrain the `issue_type` vocabulary so the writer and the selector cannot disagree. Re-pointing the selector would resolve a handful of rows and bury the defect.

---

## Files

| File | Published to | Status |
|---|---|---|
| `error_log.csv` | `avlhohn/msp-family-feed` @ `main` | 4,140 data rows (+1 `fixer_summary`), byte-prefix-identical to the base |
| `error-fixing-findings-latest.md` | `avlhohn/msp-family-feed` @ `main` | this report |

The five category CSVs and the feed JSON were **not** touched, per scope.
