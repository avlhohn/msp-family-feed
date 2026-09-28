# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-28 · **Finished:** 07:59:42 CDT (Mon, 28 Sep 2026 12:59:42 GMT)

Run date derived from the GitHub API `Date` response header, with the weekday cross-checked against the date — not taken from the sandbox clock, which has previously been wrong *in agreement* with the injected `currentDate` by up to two days.

**Base log:** `error_log.csv` at blob `bb8b12534284515ffedcae2e6ddd4834c4cf17cb` — 1,517,742 bytes, 4,644 data rows, 10-column header exact, CRLF 4,645 / bare LF 0, and **byte-identical to the GitHub remote**, so no fixer-vs-build divergence existed and nothing was at risk of being overwritten. **Published log:** blob `f91e7a038d1de0483f22f974ebb9030f47ff7b4c`, 1,527,852 bytes, 4,654 data rows, commit `4a04cd8fb8e1`, confirmed by re-GET on the first attempt.

## Summary

Open queue at start: **6 rows / 6 distinct items** — no de-duplication collapse, no cap applied.

- `unresolved_website` — 1
- `unresolved_image` — 5

Resolved this run: **1** — website 0; image 1 (og_image 0, facebook 0, **stock_openverse_specific 1**).

Left open, rolling to tomorrow: **5**. Every item was re-attempted this run. All six are genuinely shipped in the live feed (confirmed by reading `meal_deals.csv`, `restaurants.csv` and `parks.csv` from the published repo via the blobs API), so none is a phantom row.

## Resolved this run

**Perkins Tuesday Kids Eat Free** — `unresolved_image`, resolved with `stock_openverse_specific`.

Openverse id `0e8c0c35-0401-425f-847f-249566631f08`, CC BY-SA 2.0, byte-checked as a real JPEG. The photo was shot at a **named Roseville, Minnesota Perkins** — that is what makes it place-specific rather than topical, and it is the whole basis for the resolution.

**This is flagged as a reversible judgment call.** The row's address is `Multiple Twin Cities locations`, and this file has recorded for several runs that such rows are "impossible by construction" — a row denoting no single place cannot carry a place-specific photograph. That reasoning remains sound *for a photograph of the place*. What it did not cover is a photograph taken at a specific Minnesota location of that same chain, which is what Openverse returned. So the prior finding is **narrowed, not overturned**, and the narrowing does **not** extend to Denny's or Rubio's — both were queried on the identical code path this run and neither has an equivalent asset.

### The route was never actually queried until now — that is the finding

The three multi-location rows had been dismissed *a priori* on construction grounds, which meant **the Openverse route for them was never run**. Dismissing a row by reasoning about it is not the same as probing it, and the two are indistinguishable in a summary line: both report "not resolved, reason known". One of the three turned out to have an asset sitting there the entire time. Where a cheap deterministic route exists, spend it before recording the negative — an argument from construction is a prediction, and this one was 1-for-3 wrong.

## Still open

| Item | Type | Likely reason |
|---|---|---|
| Denny's Thursday Kids Eat Free | unresolved_image | Openverse queried directly this run: the only Minnesota-tagged asset is a **George Floyd protest photograph** outside a Denny's — which is verbatim the spec's own rejection example. Nothing place-appropriate exists. |
| Rubio's Rewards Thursday Kids Free Meal | unresolved_image | Openverse 0 for every spelling. Address remains `Multiple Twin Cities locations`; no MN-specific asset. |
| Bowlero Brooklyn Park (Lucky Strike) | unresolved_image | Settled negative with a stated mechanism — every body image on the venue's own page is brand-wide Contentful stock. Openverse 0. |
| Lake Ann Park | unresolved_image | Chanhassen city page still 403s to WebFetch; Facebook 200s but renders no extractable images; Openverse 0/0 on both spellings. |
| Bump & Putt Family Fun Center | unresolved_website | No official domain resolves and no candidate page could be fetched. Openverse 0/0. |

### On the Openverse zeros

Openverse was queried **parent-side, directly against the API** — WebFetch cannot reach it at all, so a subagent's Openverse negative is a search that never ran and does not count as evidence. Control queries on the same code path returned hundreds of results, so the path demonstrably fires and these zeros are genuine absences.

One distinction worth keeping: the broader `Lake Ann Chanhassen` query *does* return hits, and they are all the **Eckankar Temple**, which sits near the lake. **Geography is not depiction** — a photo taken nearby is not a photo of the park.

### Two named traps avoided

The Bump & Putt brief spelled out `nisswafallsminigolf.com` and `goputtnbump.com` as known wrong-business lookalikes, and neither was accepted. Separately, a subagent researching Perkins fetched **`eatatperkins.com`** — an unrelated single-franchisee Wix site — and returned a confident "no promotional imagery" negative. That negative was **discarded rather than recorded**: it is the right-source/wrong-business confabulation shape, and recording it would have created a false settled negative, which this project has already established is the most expensive kind. The canonical chain domain is `perkinsrestaurants.com`, which returned 403 to the parent — logged as blocked-by-tooling, not as absence.

## Defects logged that have NO open queue row

Five defects were logged this run that **this task can never drain**, because no `unresolved_website` / `unresolved_image` row exists for them. They are recorded so they are visible to the owner:

1. **Bump & Putt's shipped `website` still 404s** — `brainerd.com/business/bump-n-putt-family-fun-park/`, verified first-hand again, now roughly fifteen consecutive runs. Correctly logged every run, never applied.
2. **Bowlero Brooklyn Park ships a stale URL and a wrong ZIP** — the rename to Lucky Strike was fully evidenced 31 days ago, and the row carries **55445** where the venue is in **55443**.
3. **Perkins ships a non-canonical domain** — the feed's `website` is not `perkinsrestaurants.com`.
4. **`price_type = 'kids_free_with_adult'`** — outside the schema enum (`Free | Paid | Varies`). Nothing in the pipeline validates this field, so a bad value survives indefinitely.
5. **Denny's Minnesota closure report now twice corroborated** — but still not from a first-party source, so it is held as a lead and deliberately **not written**. Snippets are not a source.

## Diagnostics

- `log_base_rejected` — **not triggered.** Header exactly the 10-column schema; 4,644 rows, consistent with monotonic growth.
- `no_run_summary_today` — **triggered**, logged at `info`. No build `run_summary` row dated 2026-09-28 was present, so this queue may not reflect a completed nightly build. Proceeded as the spec directs.
- **Two-writer check — clean.** Local base and remote byte-identical, so publishing could not erase fixer work. Checked via the git **trees/blobs** API, never the contents API, which returns `content:""` for files over 1 MB while still returning HTTP 200 — a defect that once made a re-apply guard claim 4,041 rows as its own when the truth was 9.
- **Fail-fast token gate — passed at STEP 1**, before any research. This ordering exists because the gate used to run at publish time roughly fifteen minutes in, where a wedged connector threw away every completed piece of research.
- **Diff control — passed.** Changed pre-existing rows: **1** (the single resolution). Previously-resolved rows reopened or blanked: **0**. All appended rows dated 2026-09-28 with blank resolution columns: **true**. Row count moved 4,644 → 4,654 with no deletions.
- **Publish** — log committed and verified on the first attempt by changed blob SHA-1, not by size. No retries.
- **A compile-time crash was contained.** The first application script failed with a `SyntaxError` before executing a single line. Because its purpose was to mutate `error_log.csv`, the log was re-hashed and proven still at the base blob before retrying — a crash that happens at compile time leaves no partial write, but that is a fact to establish rather than assume.

### The queue's inflow is still dead

The build has emitted no new `unresolved_website` row since **2026-08-16** and no new `unresolved_image` since **2026-07-23** — now 44 and 67 days. Meanwhile roughly **590 fixer-shaped rows** sit permanently out of reach under other names (`missing_website`, `generic_image`, `attempted_no_photo`, `curated_bad_url`).

A small queue is not evidence of a healthy backlog. **A queue that only ever shrinks because nothing can enter it looks identical, from the summary line, to one being worked down.** Widening the queue definition is a task-spec change and the owner's call.

Related: the three `Multiple Twin Cities locations` rows should be **routed out of the image queue** by design rather than re-attempted nightly — though as of this run that is 1-for-3 rather than 3-for-3, so the routing rule wants a carve-out for chain-location assets.

## The bound on this run's value

A resolution written to `error_log.csv` still has **no consumer**. Nothing reads resolved rows back into `_compiled_work.json` before the build, so **today's Perkins resolution will not change the live feed.** Bowlero → Lucky Strike was evidenced 31 days ago and the old URL still ships; Bump & Putt's 404 has been logged correctly for around fifteen runs and never applied.

Until a pass exists that applies resolved rows to the feed, **"resolve more rows" is not the improvement** — a resolution is a note, not a fix. That is the honest ceiling on this task's output, and it is stated here rather than left implicit in a 1-of-6 headline.

## Files

- [`error_log.csv`](https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv)
- [`error-fixing-findings-latest.md`](https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md)
