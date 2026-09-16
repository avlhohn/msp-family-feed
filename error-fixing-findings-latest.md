# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-16 · **Finished:** 07:35 local (12:35 UTC)

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

## Summary

Nineteen open rows were examined — six `unresolved_website` and thirteen `unresolved_image`, across
eighteen distinct items — and **none were resolved**. That is the eighth consecutive run at this
exact shape (19 rows / 18 items / 6 still live in the feed / 0 resolutions), and the shape itself is
now the finding: the queue is not under-worked, it is structurally blocked. Eleven of the eighteen
items no longer exist in the published feed at all and are residue rather than active defects. Of
the six that do still ship, five are settled negatives on first-hand evidence and the sixth needs the
owner to make a call that no amount of searching can make for it.

The more consequential discovery this run has nothing to do with the queue. The scheduler dispatched
`msp-family-guide-daily` at `2026-09-16T12:21:46.593Z` and this error-fixer at
`2026-09-16T12:21:47.307Z` — **one second apart**, against cron slots of 03:06 and 04:40 local. Both
fired roughly four hours late, together. The fixer is therefore not completion-gated in practice: it
ran *concurrently with* the build rather than after it. Every downstream observation follows from
that. Repo HEAD was still 2026-09-15, `msp_family_guide.json` still carried
`generated_date: 2026-09-15`, and no `run_summary` row for today existed — so this run necessarily
worked yesterday's queue against yesterday's feed, and did so without any of those three signals
being a defect in its own right.

## Resolved this run

None. Zero website rows and zero image rows were resolved — no `og_image`, no `facebook`, no
`stock_openverse_specific`. Two research subagents were dispatched, both reading their item lists
from briefs written to disk programmatically rather than hand-typed, and neither produced a candidate
that met the verification bar.

Nothing was written into the data on the strength of a subagent's word. One candidate address for
Bump & Putt was again rejected — see Diagnostics.

## Still open

Nineteen rows roll forward. Six items still ship in the published feed; the other twelve rows
(eleven items) point at rows the feed no longer contains.

**Lake Ann Park, Chanhassen** — image. Discovery is exhausted across roughly thirty-eight closed
routes over nine runs. The city's own park page at `chanhassenmn.gov` was re-tested today and still
returns a hard 403, which is the single richest source that could exist for this item. The remaining
real photographs of this park are all third-party rehosts and therefore all-rights-reserved by
default, so the block is now a licence block rather than a discovery one.

**Denny's Thursday Kids Eat Free · Perkins Tuesday Kids Eat Free · Rubio's Rewards Thursday Kids Free
Meal** — image. These are chain *promotions*, not venues. There is no single place to photograph, so
no image route can succeed by construction. They should be closed as unresolvable rather than
re-attempted.

**Bowlero Brooklyn Park (Lucky Strike)** — image. Its six location-page images are Contentful brand
assets shared verbatim with the Blaine and Lakeville Minnesota siblings, so they identify the chain
rather than this location. Settled negative.

**Bump & Putt Family Fun Center** — website. This one is genuinely actionable and needs the owner.
The site the feed actually ships, `brainerd.com/business/bump-n-putt-family-fun-park/`, was
re-verified first-hand today and returns a 404 page with no address, phone or hours. That is worse
than the `unresolved_website` filing implies: the feed is not missing a website, it is publishing a
dead link a family would click. The row carries three further defects unchanged after thirteen runs —
an address of `Four miles north of Nisswa, MN` that can never geocode, a coordinate that is a Nisswa
city-centroid placeholder about 6.4 km from where that address text points, and an operating status
that is genuinely ambiguous. No first-party site or Facebook page for the business could be verified.

Fuzzy title matching was again not treated as evidence of presence. `Toddler Tuesday - ECFE` (Coon
Rapids) still fuzzy-matches a Winona row and `Movies in the Park - Mankato` still matches Duluth and
Minneapolis rows; same-state is not a match, and both items are in fact gone.

## Diagnostics

Seven rows were appended to `error_log.csv`, all dated 2026-09-16.

**`build_fixer_concurrent_dispatch`** (warning) is the primary finding, described in the Summary
above. Its practical danger is a lost update: the build loads its `error_log.csv` base at its own
STEP 1 and appends at STEP 7, so whichever of the two tasks publishes second overwrites the other's
rows. This run mitigated its own half by publishing with optimistic concurrency — the PUT carries the
`sha` read immediately beforehand, so a conflicting build publish returns 409 and this run re-applies
onto the new base rather than clobbering it. That protects the build from *us*; it does not protect
us from the build, whose publisher does not use the same scheme. As of this report the build has
still published nothing today, so its STEP 7 write is yet to come and our seven rows are at risk.
**The next run must verify that both this run's rows and the build's own 2026-09-16 STEP 7 rows are
present in the canonical log.** If either set is missing, a lost update occurred and can be repaired
from this report.

**`no_run_summary_today`** (info) records the absent marker, with the explicit note that the usual
reading does not apply — the build was in flight, not missing. The base loaded was the canonical
GitHub copy (blob `c3322eca880d…`, 3,633 data rows, header schema-exact, row count monotonically up
from 3,538), so both validation gates passed and no `log_base_rejected` was filed.

**`shipped_website_404`** (warning) records the dead Bump & Putt URL described above.

**`subagent_confabulation_seventh`** (warning) is the seventh confabulation on this queue and a new
shape: the report **contradicted itself within one document**. Its Q3 stated that Yelp, Manta and
ABLocal all returned access errors — 403, 526, 403 — and its Q4 then cited that same Yelp URL as
"URL fetched", quoted a street address and phone from it, and marked the verdict VERIFIED. Checked
first-hand, the Yelp URL returns 403, so nothing could have been read from it. The prior six
instances were all about external sources or about our own data; this one was internally checkable
at zero cost. The lesson worth keeping: read a subagent report for internal consistency *before*
spending any verification budget on the URLs it cites — a report that calls a source blocked in one
answer and quotes it in another is self-invalidating, and catching that costs one re-read rather than
one fetch. Note also that a previous run logged a different invented-looking phone number for this
same row; two distinct fabricated numbers on one item is itself a signal.

**`step45_gate_gap_persists`** (info) re-states that STEP 4.5's eligibility gate admits `image_source`
in `{curated_category, stock, openverse_named, blank}` and therefore excludes `curated`. The
published feed carries 908 `curated` rows, of which 222 are Pexels or Unsplash stock and 152 of those
also carry a `website` — rows that sit on stock imagery, have the one input the backfill needs, and
are structurally unreachable by the pass built to drain them. Two of this queue's six live image
items, Bowlero and Bump & Putt, are `curated` and thus out of gate entirely, so no number of fixer
runs can close them via 4.5. **Measurement caveat, stated because an identical number normally means
a converged pass:** the build had not republished when this was measured, so this is arithmetic on
the *same artifact* as 2026-09-15, not an independent re-measurement confirming persistence.
Re-measure once today's build lands.

**`queue_aged_out_residue`** (info) records the eleven aged-out items and the fuzzy-match rejections.

**`fixer_summary`** (info) is the mandated STEP 4 summary row.

## Files

`error_log.csv` was published to `avlhohn/msp-family-feed` on `main` at commit `5400f698`, moving
from blob `c3322eca880d` to `ee818ab58f4d` — 3,633 to 3,640 data rows, 1,145,643 to 1,153,676 bytes.
The append was guarded four ways before it ran: a hard failure on a missing or malformed run date
rather than a default, a byte-identical round-trip control on the untouched file (so "I appended
seven rows" is distinguishable from "my writer silently rewrote every line"), a double-append guard,
and an assertion that the output byte string starts with the original bytes so no carried row could
be altered. All seven new `issue_type` values were checked against the reserved namespace
(`ical_feed_pull`, `deal_source_*`, `run_summary`, `image_backfill`) so that none accidentally
enrolls itself in a mandated signal count.

No category CSV was rebuilt or republished. This stage touches `error_log.csv` and this report only.

This report is published as `error-fixing-findings-latest.md` in the same repository.
