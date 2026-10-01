# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-10-01 · **Finished:** 12:43 UTC (server-derived from the GitHub API `Date` response header — `Thu, 01 Oct 2026 12:43:05 GMT`; the weekday **Thursday** cross-checks the date, because the sandbox clock and the injected `currentDate` have both been wrong, and wrong in agreement, on this pipeline)

## Summary

The open queue held **5 rows / 5 distinct items** — 4 `unresolved_image`, 1 `unresolved_website`.
**0 were resolved** (website 0; image 0 — og_image 0, facebook 0, stock_openverse_specific 0).
All five roll forward.

Every item was re-attempted first-hand today rather than carried on a previous run's negative, and
all five were confirmed still live in the published feed, so the aged-out close path does not apply.
Four of the five now have a *mechanism* behind their negative rather than an absence of results, and
that is what ends re-probing: "its own page exists and provably carries no location-specific
photography" settles an item where "no image found" invites the identical search again tomorrow.

**The finding that matters this run is not in the queue — it is the queue.** The STEP 2 selector
reaches **5 of 4,455 open rows**, while **647 open rows** carry image or website vocabulary it cannot
see. That is a **130:1** ratio of unreachable to reachable fixer-shaped work. A near-empty in-scope
queue is not evidence of a clean feed; it is evidence of a selector that no longer matches what the
build writes.

## Resolved this run

None this run.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Lake Ann Park | unresolved_image | Licence-bound, not under-probed. ~36 closed routes have failed on *licence*, not absence; city page 403s to WebFetch, Facebook renders no images, Openverse 0 results (parent-verified today). More searching is the wrong spend. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Only generic/recurring stock available. Re-confirmed today: the venue page 200s, but its six body images are brand-wide Contentful assets that recur on the Blaine and Lakeville MN sibling pages — disqualified by the recurring-image trap, not unprobed. |
| Denny's Thursday Kids Eat Free | unresolved_image | Impossible by construction — the address is `Multiple Twin Cities locations`, and a row denoting no single place cannot carry a place-specific photograph. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | Impossible by construction (multi-location) — and see Escalations: the chain has no Minnesota presence at all. |
| Bump & Putt Family Fun Center | unresolved_website | No qualifying website exists, **and no closure evidence either**. Deliberately not closed as "confirmed closed" — absence of a website is not evidence of closure, and those are different findings. See Escalations. |

## Escalations

None of these is a research failure. Each needs a build-side or owner action, and no amount of
searching will close them.

**A resolution written to `error_log.csv` still has no consumer.** Nothing reads resolved rows back
into `_compiled_work.json` before the build, so even a correctly resolved row would not correct the
live feed. This is why "resolve more rows" is not the improvement to chase. All five items below are
**still shipped in the currently published feed**, carrying the exact defects logged against them.

**Leading escalation: no build publish has landed today.** See Diagnostics — re-checked at 12:43 UTC,
**4h32m** after the build started, the newest non-fixer commit in the repo is still
`2026-09-30T15:52:54Z`. Yesterday's publish lag was ~56 minutes.

- **Queue scope is the structural defect, and it is now quantified.** The selector's two issue types
  have had **no inflow for weeks** — the last `unresolved_image` row was written 2026-07-23 (70 days
  ago) and the last `unresolved_website` 2026-08-16 (46 days) — while the nightly build writes
  ~110–135 rows per run under *other* names. Meanwhile `issue_type` vocabulary has sprawled to **791
  distinct values**, up from 553 on 2026-09-18: that is +238 in under a fortnight, i.e. accelerating,
  not settling. Two lists naming the same work in two places with nothing enforcing agreement will
  drift, and this is what the drift looks like once it has run for two months. **The remedy is a
  selector change (or a vocabulary registry the build and the fixer share), not more searching.** As
  long as the selector enumerates literal issue-type strings, every new name the build invents is
  invisible to this task on the night it is coined, and silently so — the queue simply reads small.
- **Bump & Putt Family Fun Center — the correct address was verified FIRST-HAND today.**
  `29107 State Highway 371, Pequot Lakes, MN 56472`, phone `(218) 568-8833`, quoted verbatim from a
  page actually fetched (`lakesnwoods.com`), with the identical phone corroborated across four
  independent listings by search. **This upgrades the lead from snippet-only** — the state it was left
  in on previous runs — to an evidenced value a build-side fix can act on. The feed's stored address
  `Four miles north of Nisswa, MN` is degenerate, and the stored coordinates were geocoded *from* that
  wrong address, so the address and coordinate defects are one fix, not two. Note the city: the venue
  is in **Pequot Lakes**, not Nisswa. Separately, the shipped URL
  (`brainerd.com/business/bump-n-putt-family-fun-park/`) was re-fetched today and is a hard **404**;
  the previous report put the streak at 9 consecutive runs, making today at least the tenth — that
  ordinal is carried from that report rather than re-derived, and the fact that matters is that it is
  **still 404ing and still shipped**. Recommended build action: write the verified address, re-geocode
  from it, and **blank the dead `website`**. The row is deliberately left open because it is the only
  thing keeping the shipped broken link visible, and closing a row that is functioning as a defect
  marker buries the defect.
- **Bowlero Brooklyn Park (Lucky Strike)** — the image negative was re-confirmed first-hand today
  (six Contentful brand assets, recurring on MN siblings). The URL and ZIP corrections are **carried
  from prior runs, not re-verified today**: `bowlero.com/location/bowlero-brooklyn-park` 301s to
  `luckystrikeent.com/location/lucky-strike-brooklyn-park`, and the venue's own page states ZIP
  **55443** where the feed stores **55445**. A brand rename, not a change of operator. Evidenced since
  2026-08-28 and still unshipped — which is the no-consumer problem above, not a research gap.
- **Rubio's Rewards Thursday Kids Free Meal** — carried from the prior run's fetched evidence: the
  chain operates ~82 restaurants confined to California, Arizona and Nevada and closed its remaining
  out-of-state locations by 2020, so there are **zero Minnesota locations** and this row advertises a
  deal no family in the state can redeem. Recommended action: drop the row.
- **Denny's Thursday Kids Eat Free** — `dennys.com` has 403'd on every attempt, so the promotion has
  never been verified from the brand's own page. Secondary sources state that participation and terms
  **vary by location**. If the offer is kept, the row should disclose that caveat; as written it may
  send a family to a non-participating franchise.
- **Multi-location rows should be routed out of the image queue.** Denny's and Rubio's both carry
  `Multiple Twin Cities locations`. Re-attempting them spends budget on an impossibility and inflates
  the open count with items no research can ever close. That is a queue-design fix.

## Diagnostics

- **`log_base_rejected`: none.** The base passed both guards — header exactly the 10-column schema,
  **5,010 data rows**, 0 malformed, count growing monotonically (5,009 yesterday). No truncated base
  was carried forward. Backed up to a session-local copy before any edit.
- **`no_run_summary_today`: TRIGGERED, and logged with attribution rather than as a failure claim.**
  No end-of-run marker for 2026-10-01 was present when this task read the queue. The attribution was
  obtained **before** the row was written, because this project has a recorded instance of publishing
  a "build failed" diagnosis before making the one call that would have disproved it: today's build
  **did run**, at `08:11:08Z`, and this fixer released at `09:31:36Z` — but the newest commit in the
  repo was still `2026-09-30T15:52:54Z`, i.e. **no publish 80 minutes in**, against a ~56-minute
  publish lag yesterday. Stale-because-not-run and stale-because-still-running are byte-identical from
  the outside, so the row was worded as **a prompt to verify, not a build-failure claim**. It also
  means the completion gate did not hold: this fixer released with no build publish at all today —
  the build/fixer race in a new shape.
- **Re-checked at the end of the run, and the gap widened rather than closed.** At `12:43:05Z` — a
  second independent commit-history read, **4h32m** after the build started — the newest non-fixer
  commit is **still** `2026-09-30T15:52:54Z`. The only commit today is this task's own
  `error_log.csv` push at `12:39:01Z`. A 4.5-hour publish gap against a ~56-minute baseline is no
  longer comfortably explained by "still running," so this is the leading item for the owner. It is
  still **not** stated as a failure: what is established is the elapsed time and the absent artifact,
  and the cause requires the build's own log. The re-check is recorded because a single early reading
  would have under-stated this, and because the finding changed materially between the two calls —
  one measurement of a moving quantity is not a measurement.
- **The queue read is therefore of yesterday's feed.** Stated plainly because it bounds every
  conclusion above: the five items were confirmed live in the feed as last published, not as rebuilt
  this morning.
- **Two-writer reconciliation performed and clean.** Local and remote `error_log.csv` were
  byte-identical (blob `799624dd…`, 1,641,785 b) before the append — established with one trees-API
  call, not assumed. The contents API was deliberately not used: it returns `content:""` for files
  over 1 MB, which makes an empty read look like a successful one. Had the remote moved after the
  local copy was pulled, appending and publishing would have erased a fixer session with nothing
  reporting it.
- **The append was to raw bytes, and the carried bytes were proven identical** (`new[:len(old)] ==
  old`), so no previously-published row was rewritten — including the **555 rows carrying fixer
  resolutions**, re-counted after the edit and unchanged. The file is CRLF (`csv.DictWriter` output)
  and was written as such; rewriting line endings would churn every line of the file for no benefit.
- **Openverse was queried by the parent over the API, not by subagents**, and answered **200 on every
  one of 7 calls**. The distinction is load-bearing: `WebFetch` cannot reach `api.openverse.org` and
  403s every time, so in a subagent report "Openverse returned nothing" and "Openverse blocked me" are
  indistinguishable — and both read downstream as *the image does not exist*. A returned
  `result_count` is proof the search actually executed, so today's negatives are **genuine source
  negatives**, not the documented client artifact. Geography is not depiction: a candidate must pass
  venue identity, place **and** subject.
- **A subagent report was internally inconsistent and was not trusted.** It reported a Yelp-sourced
  detail while also reporting that Yelp 403'd it. Nothing from it was logged until the address was
  re-verified first-hand from a page this task fetched itself. A subagent's accept is a candidate; so
  is its rejection.
- **Subagent tooling failures, recorded so they are not mistaken for absence of evidence:**
  `fun4kidsmn` timed out, `manta` and Yelp returned 403, `ablocal` returned 526, `discoverourtown`
  returned 500. A blocked request is no evidence about the page.
- **A self-inflicted false negative was caught before it was logged.** A feed-presence check reported
  `volunteer_opportunities.csv` MISSING; listing the full repo tree showed the file is named
  `volunteer.csv`. That was **my filename error, not a repo anomaly**, and no defect row was written
  for it. Before believing a zero or an absence, confirm the name you asked for is the name that
  exists.
- **Publish:** `error_log.csv` committed on the **first attempt**, verified by an independent re-read
  rather than by the PUT's own response — the returned blob is `b79f88c7de86d9ef80405c4a9a0546598bd8a320`
  at **1,648,574 b**, matching the locally computed `sha1("blob <len>\0" + bytes)` exactly, which
  proves byte-identity rather than merely a size match. The **pre-upload sha was re-asserted as
  `799624dd…`** immediately before the PUT — the exact blob the reconciliation read earlier in the run
  — which closes the two-writer window from the other side: no fixer-app write landed between the
  compare and the publish, so nothing was overwritten.
- **5 rows appended** (all dated 2026-10-01, all three resolution columns blank), reusing existing
  `issue_type` names rather than minting new ones — consistent with the vocabulary sprawl being
  reported above. Exactly one `fixer_summary` row exists for today, verified after the edit.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
