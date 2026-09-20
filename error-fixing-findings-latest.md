# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-20 · **Finished:** 09:58 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

**Base log:** `error_log.csv` at blob `df8cb0b5e214` — 1,288,032 bytes, 4,031 data rows, 10-column
header exact, 4,032 CRLF / 0 bare LF. The local working copy matched the published blob
byte-for-byte. **Published log:** blob `44fc64861848`, 4,041 data rows, 1,301,573 bytes (+10).

## Summary

Nineteen open rows were examined, deduplicating to eighteen distinct items, one of which is a
non-actionable roll-up (`688 rows`) and was excluded. **None were resolved.** That is the
**twelfth consecutive run at zero**.

Twelve of the eighteen items have **aged out of the rolling window entirely** and no longer
appear in the published feed, so re-attempting them cannot change anything a family sees. Of the
six that still ship: three are chain kids-eat-free **promotions** (Denny's, Perkins, Rubio's)
that are structurally unresolvable for images, because a recurring multi-location promotion is
not a venue and no photograph of that exact thing exists; one (Lake Ann Park) is licence-bound
after roughly thirty-six closed routes against a host that hard-403s every fetch; one (Bowlero
Brooklyn Park) is a settled image negative; and one (Bump & Putt) was the single item worth
dispatching a research subagent for, which returned NOT RESOLVED and was then verified
first-hand.

The value of this run is in the findings. Three are structural and concern the pipeline rather
than any venue — the queue has **no inflow**, the log has **no consumer**, and this task is
itself a **source of the vocabulary sprawl** that hides work from its own selector. A fourth was
found while publishing: this task's own concurrency guard would have **doubled the log** on a
409, and was fixed in-run.

## Resolved this run

None this run.

Website resolutions: 0. Image resolutions: 0 — `og_image` 0, `facebook` 0,
`stock_openverse_specific` 0.

No row was resolved on anything weaker than a confident, specific match. For this queue that is
the correct outcome rather than a failure to be corrected: inventing a resolution would move the
number while leaving the feed wrong, and would retire a row that still describes a real defect.

## Still open

Nineteen rows, eighteen distinct items. Twelve items no longer appear in the published feed.

| # | Item | Type | Category | First logged | Ships? | Likely reason it stays open |
|---|---|---|---|---|---|---|
| 1 | Maplewood Celebrate Summer | image | events | 2026-07-08 | no | Aged out; a past summer event |
| 2 | Lake Ann Park | image | parks | 2026-07-08 | **yes** | Licence-bound; `chanhassenmn.gov` hard-403s every path, ~36 routes closed |
| 3 | Niko Moon Concert — Vetter Stone Amphitheater | image | events | 2026-07-23 | no | Aged out; a single past concert date |
| 4 | Music in the Park Thursdays — Mankato | image | events | 2026-07-23 | no | Aged out; recurring series, no venue-specific photo |
| 5 | Movies in the Park — Mankato | image | events | 2026-07-23 | no | Aged out; same recurring-series shape |
| 6 | Moorhead Summer Splash Event | image | events | 2026-07-23 | no | Aged out |
| 7 | Winona Parks & Rec Summer Activities | image | events | 2026-07-23 | no | Aged out; an activity roll-up, not a venue |
| 8 | Urban Air Trampoline Parks — Minnesota Locations | image | events | 2026-07-23 | no | Aged out; a multi-location chain roll-up, so no single venue to photograph |
| 9 | Denny's Thursday Kids Eat Free | image | meal_deals | 2026-07-23 | **yes** | **Structurally unresolvable** — a recurring chain promotion is not a venue |
| 10 | Perkins Tuesday Kids Eat Free | image | meal_deals | 2026-07-23 | **yes** | **Structurally unresolvable** — same |
| 11 | Rubio's Rewards Thursday Kids Free Meal | image | meal_deals | 2026-07-23 | **yes** | Structurally unresolvable, and a wrong-state row: Rubio's has zero Minnesota locations (logged 2026-09-19) |
| 12 | Bowlero Brooklyn Park (Lucky Strike) | image | restaurants | 2026-07-23 | **yes** | Settled image negative; separately its stored website is a 23-day-old stale redirect (below) |
| 13 | Mission Branch Library Community Garden | image | volunteer | 2026-07-23 | no | Aged out, and a wrong-state row — this is San Francisco Public Library (logged 2026-09-19) |
| 14 | Summer Outdoor Festival — Brainerd *(2 rows)* | website | events | 2026-07-24 | no | Aged out; a generic title with no identifiable single source |
| 15 | Pizza King Station | website | restaurants | 2026-08-14 | no | Aged out |
| 16 | Toddler Tuesday — ECFE | website | events | 2026-08-15 | no | Aged out; a generic program name shared across many districts |
| 17 | Bump & Putt Family Fun Center | website | restaurants | 2026-08-15 | **yes** | Shipped URL 404s (4th run); the one replacement address found remains **unverified** (below) |
| 18 | `688 rows` | website | data | 2026-08-16 | n/a | A **roll-up placeholder**, not an item — must never be dispatched to a subagent |

## Diagnostics

### 1. The queue has no inflow — 35 and 59 days dry

The newest `unresolved_website` row is dated **2026-08-16 (35 days ago)** and the newest
`unresolved_image` row **2026-07-23 (59 days ago)**, while the build writes 80–110 error-log rows
every night and did so today (106 rows dated 2026-09-20).

Against that silence, the gap those two issue types exist to track stands at **4,742 rows carrying
a generic `curated_category` image** and **953 rows with a blank website**, in a 6,854-row feed
with only 1,119 distinct image URLs.

The queue is therefore not converged, it is unfed. The load-bearing point, first made on
2026-09-18, is that **a drained queue and a queue nothing writes to are indistinguishable from
inside the queue**. The diagnostic is to measure inflow — the last write date per scoped issue
type — against the size of the underlying gap in the artifact, and never to read zero resolutions
as a clean queue.

This remains deliberately **not fixed in-run**. Widening STEP 2's selector would resolve rows and
bury the defect. The owner fix is to constrain the issue-type vocabulary so the writer's list and
the selector's list cannot disagree.

### 2. The log has no consumer — correct diagnoses never reach the feed

Two items make this concrete, both re-verified first-hand today.

**Bump & Putt Family Fun Center.** The website this row actually ships,
`brainerd.com/business/bump-n-putt-family-fun-park/`, has now been logged as returning the site's
404 body on **four consecutive runs** — 2026-09-16, -17, -18 and today — and the feed still ships
it unchanged. The venue itself is real and trading; one stored URL is wrong.

**Bowlero Brooklyn Park.** The stored website `bowlero.com/location/bowlero-brooklyn-park` returns
**301 Moved Permanently** to `luckystrikeent.com/location/lucky-strike-brooklyn-park`, which
fetches 200 as a live page naming itself verbatim *"Lucky Strike Brooklyn Park"* at *"7545
Brooklyn Blvd. Brooklyn Park, MN 55443"*. First logged 2026-08-28 and again 2026-09-18; it is now
**23 days old** and the feed still ships the pre-rebrand URL.

Both diagnoses are correct, cheap to apply, and have no path back into the feed, because **no
pipeline step reads `error_log.csv` as an input**. This is a second and independent reason the
queue cannot drain, distinct from the inflow failure: even a perfectly worked item stays broken.
The Bowlero case is a 301, so no family is blocked — which is precisely why nothing forces it to
be fixed, and why it should be recorded rather than re-discovered a fourth time.

### 3. This task is a source of the sprawl that blinds it — 112 of its own rows are unreachable

The 2026-09-18 finding was that twenty-six build-written rows sat under `attempted_no_photo`,
where STEP 2's literal match on `('unresolved_website','unresolved_image')` could not see them.
The same mechanism runs through **the fixer's own output**.

Measured today: **112 open rows written by `STEP*_fixer*` steps carry an issue type this task's
own selector cannot read.** Among them, three `shipped_website_404` rows (2026-09-16/17/18) and
two `website_stale_redirect` rows (2026-08-28, 2026-09-18) describe exactly fixer-shaped work and
are structurally invisible to the selector that would otherwise pick them up.

The number is worth stating carefully, because the first estimate was wrong in an instructive way.
Enumerating the two issue-type names I already knew gave **5**; scanning by *step* rather than by
name gave **112**. Measuring a rule's reach by the rows you can already name understates it — the
same error as measuring `FREE_SRC`'s reach over all event rows instead of over the rows it would
fire on.

The wider picture, from the same scan: the log holds **599 distinct issue types, 403 of them used
exactly once (67%)**. Open rows that are fixer-shaped but unreachable include **300
`missing_website`**, **240 `generic_image`** and **26 `attempted_no_photo`** — some 566 rows —
against the **19** the selector can see.

The log also demonstrates the drift on itself: it currently holds **both `queue_no_inflow`
(2026-09-19) and `fixer_queue_no_inflow` (2026-09-18)** as one-off names for a single finding,
coined by consecutive runs of this task one day apart.

Today's rows deliberately **reuse existing issue-type names rather than coin new ones**, because
coining is the defect being reported. But reuse is a habit, not an assertion, and this project's
standing rule is that a habit is not a guard. The owner fix is a closed issue-type vocabulary
enforced at write time.

### 4. The concurrency guard would have doubled the log on a 409 — fixed in-run

Found while publishing today. The 2026-09-16 concurrent-dispatch finding requires `error_log.csv`
to be published with optimistic concurrency, repairing a 409 by re-applying our own rows onto the
new base, identified by exact full-row equality. That guard read the remote base from the contents
API's `content` field.

`error_log.csv` is now **1,299,503 bytes**, and GitHub's contents API returns `content` as an
**empty string above 1 MB** while still returning correct metadata and HTTP 200. The base
therefore decoded to zero bytes, and the guard computed **4,041 rows as "mine" when the true
answer was 9**. No 409 occurred today, so no damage was done — but had one occurred, the repair
would have appended the entire file onto the new base and roughly doubled the log. *The guard
written to prevent a lost update would instead have caused mass duplication, which is the worse of
the two failures.*

The same bug produced a false verification FAIL on a publish that had in fact landed correctly on
the first attempt, causing two further no-op PUTs; GitHub correctly treated them as idempotent and
exactly one commit was created (`80c856015e`).

Fixed two ways: identity is now checked against the contents API's `sha` field, which **is** the
git blob SHA-1 and is returned at any size; and bytes are fetched from the git **blobs** API with
the raw media type, the result asserted to hash back to that sha. A sanity gate now refuses any
re-apply claiming more than 10% of the file as "own rows".

The generalisation is this project's own rule reaching the transport layer: **a 200 with a
structurally empty body passes every status check**, exactly like the parked-domain source logged
2026-09-16 — and a guard that has never been made to fail on purpose is an assertion you merely
hope is wired up. This one had never fired, because the log only crossed 1 MB recently.

### 5. A ninth confabulation shape — snippet agreement asserted as corroboration

The candidate address `29107 State Hwy 371, Pequot Lakes, MN 56472` (phone `(218) 568-8833`)
surfaced for the **third consecutive run** and has again been **deliberately not written into the
data**.

The research subagent labelled this lead **"CORROBORATED"** while its own evidence table lists
every one of the four cited sources as unfetchable: Yelp 403, ABLocal 526, Manta 403, fun4kidsmn
timeout. The corroboration was assembled entirely from **search-result snippets**, with no cited
page ever read.

This is distinct from the eight earlier shapes on this queue (invented asset, invented container,
invented host, a fabricated value in our own record, mischaracterised negative, self-contradicting
report, real source about the wrong business in the wrong city). Nothing here is invented — the
snippets are real and they do agree. The defect is that **agreement among snippets was treated as
corroboration**. Snippets from aggregator directories are copies of one another, so their
agreement is one source counted four times.

The operative rule stands: a subagent's REJECTED is a candidate verdict exactly as its RESOLVED
is, and a verdict whose every citation is unfetchable is unverified regardless of the word
attached to it. The address may well be correct; it is not written in, because writing an
unverified street address into a family-facing feed sends a family to a door that may not exist.

### 6. Two settled negatives, named so a later run does not adopt them

**`brainerd.com/nisswa-family-fun-center/` is a different business.** It fetches 200 on the same
host as Bump & Putt's dead URL, in the same town named in Bump & Putt's address field ("Four miles
north of Nisswa, MN"), and is therefore the single most plausible-looking replacement URL
available. It is not the venue: the page names itself *"Nisswa Family Fun Center"*, gives its
address verbatim as *"4871 Co Rd 77 Nisswa, MN 56468"* and its phone as `218-820-3046`, and does
not contain the words "Bump" or "Putt" anywhere. Geographic and host proximity is not identity
evidence — the standard is the page naming the venue.

**Lake Ann Park's stored record has changed underneath the queue item.** The stored `website` is
now the truncated *index* path `chanhassenmn.gov/departments/parks-recreation/parks-facilities/`
rather than the deep per-park path earlier runs recorded, and the address is now a real street
address, *"6800 Birch Dr, Chanhassen, MN 55317"*. The item's status is unchanged — the host
hard-403s us on every path — but the truncated index path is a new, separate, small defect: it is
a **live URL that does not point at this park**, so it will never 404 and no link-liveness check
can ever surface it. Re-read an open item's current feed row before re-attempting it; the queue
stores a title, and everything else about the row moves underneath it.

### 7. Method note — a probe that under-read its own data

The feed cross-check nearly produced a wrong answer. A fuzzy token-overlap pass returned **75
candidate matches for "Lake Ann Park"**, because the probe's own `len(token) > 3` filter silently
dropped "Ann", leaving every *"X Lake Park"* row scoring a perfect 1.0. An exact-substring pass
found exactly **one** real row.

A probe that under-reads its data returns a confident, clean-looking number rather than an error.
A degenerate distribution — 75 perfect matches, or all-zero, or N-of-N — is a bug in the probe
until proven otherwise. The 5-versus-112 correction in finding 3 is the same lesson caught a
second time in the same run.

### 8. STEP 1 gates — all clear

- **Token:** fetched and auth-probed successfully on the first attempt; no Drive fallback needed.
- **Log base:** accepted — 1,288,032 bytes, blob `df8cb0b5e214`, exact 10-column header, 4,031
  data rows, 4,032 CRLF / 0 bare LF, and **byte-identical to the remote**, so there was no
  stale-base divergence and no row-set reconciliation to perform. `log_base_rejected` **not
  triggered**.
- **Freshness:** today's `run_summary` row is present — *"MSP Family Guide daily refresh 2026-09-20
  (Sunday), window 2026-09-20..2026-10-31 (42 days). Published 6854 rows: events 5127, parks 849,
  meal_deals 150, volunteer_opportunities 268, restaurants 460."* — so `no_run_summary_today`
  **not triggered**.
- **Scheduler ordering:** verified rather than assumed, per the 2026-09-16 concurrent-dispatch
  finding. Repo `pushed_at` 2026-09-20T08:35:14Z against this run's 09:40:35Z start — about 65
  minutes apart, so the fixer worked **today's** queue against **today's** feed. Not a repeat of
  the one-second dispatch, and no lost-update risk to escalate.
- **Row preservation:** all 4,031 carried rows verified byte-identical after each append, via a
  round-trip control that required the untouched file to re-serialise to the same bytes before any
  row was written. The resolved-row count held at **536** throughout, and all 19 open rows were
  left open on purpose.

## Files

- **Error log (local):** `Agents and Workflows/error_log.csv`
- **Error log (published):** https://github.com/avlhohn/msp-family-feed/blob/main/error_log.csv
- **Findings (local):** `Agents and Workflows/error-fixing-findings-latest.md`
- **Findings (published):** https://github.com/avlhohn/msp-family-feed/blob/main/error-fixing-findings-latest.md
