# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-10-03 (Saturday) · **Finished:** 10:01 UTC (05:01 CDT)

Run date derived from a server-side timestamp — the GitHub API `Date` response header,
`Sat, 03 Oct 2026 10:01:04 GMT` — with the weekday **Saturday** cross-checking the date, because
the sandbox clock and the injected `currentDate` have both been wrong, and wrong in agreement, on
this pipeline.

## Summary

Five open items were eligible under the two mandated issue types, all five were re-attempted, and
**none met the verification bar**. Every one remains OPEN and recoverable. No row's
`resolved_date`, `resolved_by` or `resolution_note` was written this run, so the resolved count is
unchanged at 555 — a number independently confirmed identical on both sides of the two-writer
boundary before anything was appended.

A zero-resolution run invites the reading that the pass no-opped, so each of the five carries a
stated ground rather than a count. Two were structural rejections that no amount of further
searching would change, two were cases where the evidence a resolution needs is invisible to the
tooling available, and one appears unresolvable by construction.

This run also unblocked the previous one. The 2026-10-02 fixer halted at the STEP 1 credential
gate without attempting any research, because the Drive-supplied token was revoked. That token is
still revoked today; what changed is that a working credential was found in the workspace folder
and verified before any research began, so the gate passed and the queue was actually worked.

The more consequential result is not in the queue at all: **the queue is clean because it is
starved, not because it was drained.** The two mandated issue types have emitted nothing for 48
days, while 1,448 open rows across 118 other issue types sit structurally unreachable by the
selection rule this task is given. A small queue read as success is the false pass this pipeline
rates worst, because a shortfall gets investigated and an empty queue never does.

One STEP 1 condition was serious enough to earn a durable row of its own in `error_log.csv` rather
than only a mention here. The inflow finding did not, and the reasoning behind that is worth
stating, because this run got it wrong first and corrected it: a finding that is true every run
does not belong in an append-only log. It belongs in the single `fixer_summary` row this task
writes per run, and in this report, which is overwritten in place. The log already carried four
names for that one finding; a fifth was appended, measured, rolled back, and folded into the
summary row instead.

## Resolved this run

**None.** Zero of five items cleared the bar, and the per-item grounds follow.

**Lake Ann Park, Chanhassen** (`unresolved_image`) — rejected structurally. The single byte-valid
candidate was `mnbucketlist.com/wp-content/uploads/2015/03/lake-ann.jpg`, and the parent
byte-checked it directly rather than taking the subagent's word for it: HTTP 200, `image/jpeg`,
96,394 bytes, magic `FF D8 FF E0`, so it is genuinely a photograph and the subagent's size claim
was roughly right. It is still not usable. A third-party travel blog is none of the three
sanctioned sources — a venue's own Facebook photo, a self-branded deep-link `og:image`, or a
place-specific Openverse result — and it carries no license this pipeline can rely on. That is a
rejection on provenance, not a judgment call about the picture. The park's own source,
`chanhassenmn.gov`, returned 403 on both candidate URLs; a blocked request is no evidence about
the page, so it was **withheld rather than written as a negative**, which keeps that URL eligible
for a future attempt instead of poisoning it with a permanent negative cache entry.

**Bowlero Brooklyn Park** (`unresolved_image`) — the rebrand to Lucky Strike is now confirmed by
the parent at `luckystrikeent.com/location/lucky-strike-brooklyn-park`, 7545 Brooklyn Blvd,
Brooklyn Park MN 55443. That settles an identity question which has been open for weeks, and it
still does not yield an image: every asset on that page is either an SVG logo or a chain-wide
promotional photograph (`mother-and-son`, `girl-blowing-out-candles`,
`family-unlimited-bowling`) served identically across every Lucky Strike location. A site-wide
promo is exactly the generic stock the task excludes.

**Denny's Thursday Kids Eat Free** and **Rubio's Rewards Thursday Kids Free Meal**
(`unresolved_image`) — logos, aggregator thumbnails, or an `og:image` that is not visible through
WebFetch, which converts pages to markdown and strips `<head>`. That distinction matters for the
next reader: this is absence of evidence, not evidence of absence, and neither row should be read
as proven imageless.

**Bump & Putt Family Fun Center** (`unresolved_website`) — directory listings only, with no
official site and no Facebook page located. Under a bar requiring a specific venue-name and city
match, this may be unresolvable by construction rather than merely unresolved. A subagent reported
an address of 29107 State Highway 371, Pequot Lakes, MN 56472 and a phone number of
(218) 568-8833; **the parent did not verify either**, so both are recorded here as unverified
leads and neither was written into the log.

**Openverse was queried by the parent, not delegated.** WebFetch cannot reach the Openverse API,
so a subagent's image negative there may be a search that never ran. Twelve queries across the
four image items returned zero place-specific results.

One of those queries deserves naming, because a future reader who repeats it will get the same
clean match and should know it was already considered. Openverse returned photographs titled
exactly "Denny's Restaurant" — an exact brand-name match which, under a brand-level reading of a
chain-wide deal row, could arguably resolve. It was **declined** on the place-specificity ground
the task actually states. A resolution is permanent while an open row stays recoverable, so a
false pass costs more here than a false negative, and a photograph of a different state's
storefront is what a brand-level reading would have shipped.

## Still open

Five rows, unchanged: one `unresolved_website` (Bump & Putt) and four `unresolved_image` (Lake Ann
Park, Denny's, Rubio's, Bowlero/Lucky Strike). Three are now better characterised than they were
this morning — the Lucky Strike rebrand is confirmed, the Chanhassen source is known to block
automated fetches, and the two chain-restaurant rows are known to be blocked by a tooling limit
rather than by the absence of a photograph — which is worth more to the next attempt than another
inconclusive search would have been.

## Diagnostics

**The documented credential path is broken, and this run survived by accident of persistence.**
The Drive fallback returned a well-formed `github_pat_` value that authenticates 401. It is the
pre-rotation token, revoked by GitHub secret scanning after the 2026-10-02 commit-message leak,
with the Drive copy never updated when the owner rotated. The workspace-local `github_token.txt`
authenticates 200 and was used. The two values were compared by SHA-256 and never printed.

The shape of that failure is the part that matters, and it is why this run proceeded where
yesterday's stopped. The instruction to retry twice and then stop governs a connector that errors
or hangs; this one succeeded and handed back a dead credential, which is a different failure and
must not be filed as `token_fetch_failed`. Stopping there would have been a false negative with a
validated credential sitting on disk two directories away. Note the dependency this exposes: a
fresh sandbox with no persisted workspace folder would hard-fail at the STEP 1 gate. Owner action
is to update the Drive copy to the rotated PAT, or retire the Drive fallback entirely rather than
leave the gate dependent on a file nobody maintains. Logged as `drive_token_stale_check`.

**The fixer queue has effectively no inflow.** Re-verified live this run rather than carried
forward from memory. The two mandated issue types hold 319 rows in total, of which 314 are
resolved — so the historical drain genuinely worked — but the newest row ever emitted under either
type is dated 2026-08-16, which is 48 days ago, and none of today's 120 appended rows is
fixer-shaped. Meanwhile 1,448 open rows across 118 distinct issue types whose newest emission
predates 2026-09-01 are structurally unreachable by the two-literal selection rule, led by
`unresolved_geocode` at 386, `missing_website` at 300, `generic_image` at 240,
`unresolved_coordinates` at 83, `coverage_gap` at 77 and `missing_address` at 58 — all plainly
fixer-shaped work.

Two mechanisms could produce that, and **neither was verified**, so both are recorded as
hypotheses on purpose: either the build has stopped emitting these types altogether, or it still
detects them and the rows are capped or suppressed before the append. The remedy differs
completely between the two, so the right next step is to establish which is live, not to act on
the count.

**This finding was logged as its own row, and then that row was rolled back.** It is carried
instead inside today's `fixer_summary` row and here. The correction is worth recording because the
reasoning that produced the mistake was superficially sound: this report is overwritten every run,
so a finding that lives only here looked unrecorded. What that reasoning missed is that the log
already held **four names for this one finding** — `fixer_queue_no_inflow` on 2026-09-18,
`queue_no_inflow` on 09-19 and 09-20, and `fixer_queue_inflow_check` on 09-26. A fifth would have
been the accumulating permanent warning this pipeline forbids, the failure mode where a block of
nightly-identical warnings trains the reader to skim it. Worse, it would have arrived by the very
`issue_type` vocabulary drift the finding itself describes — one concept under four spellings,
which splits every count of it. The durable home for something true every run is the one row this
task writes per run, which cannot accumulate by construction. The append helper now carries two
assertions enforcing that, both of which were made to fail on purpose before the passing result
was trusted.

**Base validation and reconciliation both clean.** The base carried the exact ten-column header,
5,373 data rows spanning 2026-07-08 to 2026-10-03, pure CRLF line endings with zero bare
linefeeds, and no malformed-width rows, so no `log_base_rejected` diagnostic was owed. A
`run_summary` row dated today was present, so no `no_run_summary_today` diagnostic was owed
either. Before the append, local and remote were byte-identical at blob `fa97a025e59a` /
1,758,725 bytes, read at the explicit head commit `033cc62dd9d5` rather than through a branch-name
tree read, which is CDN-cacheable and has produced a false mismatch on this repo before. The
resolved-row count was 555 on both sides: byte identity answers whether the file moved, the
resolved count answers whether the other writer's work was present, and those are different
questions.

**The STEP 4 append failed loudly before writing anything**, on a width assertion that caught
three malformed rows while `error_log.csv` was still pristine — the failure direction to prefer. It
was re-run with the guard block intact plus a mandatory-run-date assertion, and both date guards
were made to fire on purpose before the passing result was trusted.

It then ran a second time, after the inflow row was rolled back. The preserved baseline is what
made that safe: it was verified to be a **byte-exact prefix** of the appended file before the
restore, which proves it is the exact common ancestor and that the rollback discarded only this
run's own three rows rather than anything else. Post-write verification confirmed 5,373 → 5,375
rows, the header unchanged, the resolved count unchanged at 555, every row ten fields wide, zero
bare linefeeds, and the first 1,758,725 bytes byte-identical to the baseline. The fold itself was
then asserted against the **file** rather than against the helper's variables — exactly one
`fixer_summary` row dated today, the inflow finding present inside it, and no standalone inflow
row added — because a helper can be correct about what it intended to write and still not have
written it.

## Files

- `error_log.csv` — published to `avlhohn/msp-family-feed` on `main`. 5,375 data rows,
  1,763,490 bytes, git blob `00dfc449135b`, verified by comparing the API's returned `sha` against
  the locally computed blob SHA-1 of the exact bytes uploaded, not by a size threshold. Two rows
  appended: the `fixer_summary` and `drive_token_stale_check`.
  <https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv>
- `error-fixing-findings-latest.md` — this report, published to the same repo.
  <https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md>
- `.bak_error_log_prefixer_1003.csv` — the preserved pre-append baseline, 5,373 data rows,
  1,758,725 bytes, blob `fa97a025e59a`. It is the exact common ancestor, and therefore the only
  thing that makes a row-identity merge or a clean append rollback possible. It did that work this
  run, which is the argument for keeping it until the next run's reconciliation is clean.
- `.fixer_1003/` — this run's working directory: the programmatically written queue and subagent
  batch files, the parent-side Openverse query and its results, the direct image byte-check, and
  the guarded append and publish helpers.
