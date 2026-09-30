# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-30 · **Finished:** 09:51 UTC (server-derived from the GitHub API `Date` header; weekday Wednesday cross-checks the date)

## Summary

The open queue held **5 rows / 5 distinct items** — 4 `unresolved_image`, 1 `unresolved_website`.
**0 were resolved** (website 0; image 0 — og_image 0, facebook 0, stock_openverse_specific 0).
All five roll forward to tomorrow.

That zero is a claim about the sources, not a claim that nothing was attempted. Every item was
re-attempted first-hand today rather than carried on a previous run's negative. The queue is residue:
the oldest item has been open since 2026-07-08 and the newest since 2026-08-15, and four of the five
now have a *mechanism* behind their negative rather than a mere absence of results. That distinction
is what ends re-probing — "its own page exists and provably has no location-specific photography"
settles an item, where "no image found" invites the same search again next run.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | unresolved_image | No specific image found. City page 403s to WebFetch; Facebook renders no images; Openverse 0 results (parent-verified today). A subagent's TripAdvisor candidate was overridden — see Diagnostics. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Only generic/recurring stock available. The venue's own page 200s but all 8 body images are brand-wide Contentful stock reused chain-wide — disqualified by the recurring-image trap, not unprobed. |
| Denny's Thursday Kids Eat Free | unresolved_image | Impossible by construction — the address is "Multiple Twin Cities locations", and a row denoting no single place cannot carry a place-specific photo. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | Impossible by construction (multi-location) — and see Escalations: the chain has no Minnesota presence at all. |
| Bump & Putt Family Fun Center | unresolved_website | Closed-or-broken. Stored URL a hard 404 for the 9th consecutive run; no first-party site or own Facebook page. Deliberately left open — see Escalations. |

## Escalations

None of these is a research failure. Each needs a build-side or owner action, and no amount of
searching will close them.

**A resolution written to `error_log.csv` still has no consumer.** Nothing reads resolved rows back
into `_compiled_work.json` before the build, so even a correctly resolved row would not correct the
live feed. This is why "resolve more rows" is not the improvement to chase. All five items below are
**still shipped in today's feed**, carrying the exact defects logged against them.

- **Bump & Putt Family Fun Center** — the feed ships `https://www.brainerd.com/business/bump-n-putt-family-fun-park/`,
  re-fetched today and a hard **404** for the 9th consecutive run. The stored address
  `Four miles north of Nisswa, MN` is unusable, and the stored coordinates (46.520522, −94.288609)
  were geocoded *from* that wrong address — so the pin is wrong too, and the address and coordinate
  defects are one fix rather than two. The lead address `29107 State Hwy 371, Pequot Lakes, MN 56472`
  (phone 218-568-8833) is held but remains **snippet-only**: today's research again could not fetch a
  page stating it (Yelp 403, ABLocal 526, Fun4KidsMN timed out), so it is deliberately not written.
  Recommended build action: blank the dead `website` and the wrong `address`/coordinates.
  **Deliberately NOT closed as "confirmed closed/no site"** even though it qualifies on the "no site"
  half — the open row is the only thing keeping the shipped broken link visible, and closing a row
  that is functioning as a defect marker buries the defect. There is no evidence of closure and none
  of current operation; those are different findings and neither supports closing it.
- **Bowlero Brooklyn Park (Lucky Strike)** — re-confirmed first-hand today:
  `bowlero.com/location/bowlero-brooklyn-park` **301s** to
  `https://www.luckystrikeent.com/location/lucky-strike-brooklyn-park`, which is the canonical URL to
  store. The venue's own page states ZIP **55443**; the feed stores **55445**. A brand rename, not a
  change of operator. Both corrections have been evidenced since 2026-08-28 and remain unshipped.
- **Rubio's Rewards Thursday Kids Free Meal** — re-verified today from a fetched page: the chain
  operates ~82 restaurants confined to California, Arizona and Nevada, having closed its remaining
  out-of-state locations by 2020. There are **zero Minnesota locations**, so this row advertises a
  deal no family in the state can redeem at any counter. Recommended action: drop the row. Caveat
  stated plainly — the confirming fetch was Wikipedia; `rubios.com` itself returned only page
  infrastructure.
- **Denny's Thursday Kids Eat Free** — `dennys.com` **403'd** today, so the promotion could not be
  verified from the brand's own page. Secondary sources describe kids 12-and-under eating free on
  Thursdays 4–10 PM with an adult entrée purchase, but state that **participation and terms vary by
  location**. Those are coupon and deal blogs, which are leads rather than sources. If the offer is
  kept, the row should disclose the location-variance caveat; as written it may send a family to a
  non-participating franchise.
- **Multi-location rows should be routed out of the image queue.** Denny's and Rubio's both carry
  `Multiple Twin Cities locations`. Re-attempting them nightly spends budget on an impossibility and
  inflates the open-queue count with items no research can ever close. That is a queue-design fix.

## Diagnostics

- **`log_base_rejected`: none.** The base passed both guards — header exactly the 10-column schema,
  5,009 data rows with 0 malformed, and the count growing monotonically (4,645 on 09-28, 4,784 on
  09-29). No truncated base was carried forward.
- **`no_run_summary_today`: not triggered.** The build's end-of-run marker for 2026-09-30 was present,
  so the queue read was current.
- **Two-writer reconciliation performed and clean.** Local and remote `error_log.csv` were
  byte-identical (blob `2104dc1b…`, 1,639,971 b) before the append — established with one trees-API
  call, not assumed. The contents API was deliberately not used for this check: it returns
  `content:""` for files over 1 MB, which would make an empty read look like a successful one. Had the
  remote moved after the local copy was pulled, appending and publishing would have erased a fixer
  session with nothing reporting it.
- **Openverse was queried by the parent over the API, not by subagents**, and answered **200 on every
  call**. The distinction is load-bearing: `WebFetch` cannot reach `api.openverse.org` and 403s every
  time, so in a subagent report "Openverse returned nothing" and "Openverse blocked me" are
  indistinguishable — and both read downstream as *the image does not exist*. Today's negatives are
  therefore genuine source negatives: 0 results for `Lake Ann Park Chanhassen`,
  `Lake Ann Beach Chanhassen`, `Lucky Strike Brooklyn Park`, `Bowlero Brooklyn Park Minnesota`,
  `Lucky Strike bowling Minnesota`, and both Bump & Putt spellings. Broader phrasings returned only
  wrong-place hits — bare `Lake Ann Park` returns English gardens (Chippenham Park), `Lake Ann
  Minnesota` returns a Montana mansion, and `Dennys restaurant Minnesota` returns a George Floyd
  protest photograph. A candidate must pass venue identity, geography **and** subject; geography alone
  is not depiction.
- **One subagent ACCEPT was overridden by the parent.** For Lake Ann Park a subagent proposed a
  TripAdvisor user-submitted photo
  (`dynamic-media-cdn.tripadvisor.com/media/photo-o/0d/64/d9/6d/photo0jpg.jpg`). Rejected on three
  independent grounds: it is not one of the three permitted `image_source` tokens (`og_image` /
  `facebook` / `stock_openverse_specific`); user-submitted review-site content is not CC or
  public-domain licensed; and the subject was never visually verified, the filename being opaque. A
  subagent's accept is a candidate, not a result — and so is its rejection.
- **The website research was honest about its own evidence, which is recorded here as a good
  outcome.** The Bump & Putt address lead was reported explicitly as snippet-based rather than
  upgraded into a confirmation. This task has previously been handed an address marked "CORROBORATED"
  when every page cited was unfetchable.
- **Queue inflow remains the structural problem.** The in-scope queue is 5 rows, but the log holds
  **4,449 open rows of other issue types**, including **300 `missing_website`** and **240
  `generic_image`** — fixer-shaped work that this task's scope (`unresolved_website` /
  `unresolved_image` only) cannot reach. Nothing new has entered the in-scope queue since 2026-08-15.
  A near-empty queue here is not evidence of a clean feed.
- **Publish:** `error_log.csv` committed on the first attempt, verified by an independent re-read
  rather than by the PUT's own response — the returned blob is `799624dd…` at 1,641,785 b, matching
  the locally computed `sha1("blob <len>\0" + bytes)`. The **pre-upload sha was still `2104dc1b…`**,
  the exact blob the reconciliation read earlier in the run, which closes the two-writer window from
  the other side: no fixer-app write landed between the compare and the publish, so nothing was
  overwritten. No Drive fallback fired (the GitHub raw read succeeded), so no base copy was skipped
  for AI-ineligibility.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
