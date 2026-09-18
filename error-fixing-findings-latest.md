# MSP Family Guide — Error Fixing (Latest)

**Run date:** 2026-09-18 · **Finished:** 12:26 UTC

Run date and finish time are both derived from a server-side `Date` header, not from the sandbox
clock. The sandbox clock and the injected `currentDate` have previously been wrong *in agreement*
by up to two days, so neither is used here.

## Summary

Nineteen open rows were examined, deduplicating to eighteen distinct items, and **none were
resolved**. That is the tenth consecutive run at zero, and for the first nine the explanation given
was that the queue consists of settled, licence-bound negatives. That explanation is true of the six
items still in the feed and it is **incomplete**.

This run asked the next question — not "why did these items fail again?" but "why does this queue
never change?" — and the answer is the substantive output of the run: **the queue has had no inflow
for weeks.** The build stopped writing rows in the two issue_types this task drains, 57 and 33 days
ago respectively, while the underlying gap those rows exist to track grew to 4,728 rows on a generic
image and 1,013 rows with no website. The fixer has been draining a pond with no inflow while the
lake goes unmeasured. Details under Diagnostics.

Today's daily build has **not yet run**; this fixer executed ahead of it, so the queue worked here is
yesterday's. That is recorded as `no_run_summary_today`, and it reflects a genuinely absent build
rather than a missing marker.

## Resolved this run

None.

- Website resolutions: 0
- Image resolutions: 0 — og_image 0, facebook 0, stock_openverse_specific 0

No row's `resolved_date`, `resolved_by` or `resolution_note` was written. All 536 previously-resolved
rows were preserved unchanged, asserted byte-for-byte before the file was written.

## Still open

All nineteen rows remain open. Six of the eighteen items still ship in the feed; each is a negative
for a specific recorded reason, not for lack of effort.

**Lake Ann Park (Chanhassen)** — roughly 36 discovery routes have now been closed across prior runs.
It is exhausted on discovery *and*, separately, bound on licence, so it fails twice over. Feed
presence was re-confirmed this run by targeted substring match rather than by fuzzy title match:
exactly one genuine row, `[parks] Lake Ann Park | 6800 Birch Dr, Chanhassen, MN 55317`. A fuzzy pass
returned 75 hits, every one of them a different "…Lake…Park…" venue — the documented trap behaving
exactly as documented, which is why the confirmation step exists.

**Denny's and Perkins (chain kids-eat-free promotions)** — structurally unresolvable rather than
merely difficult. A promotion is not a venue, so no photograph of this exact thing exists to be
found; and the recurrence test rejects every candidate by construction, because any asset a chain
publishes for a promotion necessarily also appears on its sibling locations.

**Rubio's Coastal Grill** — not an image problem at all. A bad seed. Escalated below.

**Bowlero Brooklyn Park** — settled on hard evidence rather than on exhausted effort: all six
candidate assets are Contentful brand images that also appear on the Blaine and Lakeville Minnesota
sibling pages. A shared CDN plus generic alt text is the documented tell. Its website and ZIP are
actionable and are escalated below.

**Bump & Putt Family Fun Park (Brainerd)** — deliberately held open. Escalated below.

The remaining eleven items no longer appear in the published feed. Re-attempting an item that does
not ship cannot change the artifact, so they are recorded and left open rather than worked. The
eighteenth item is the `688 rows` roll-up placeholder, which must never be dispatched.

### Escalations for the owner

All three were re-verified first-hand this run rather than repeated from memory. Re-verification is
cheap, and an escalation carried forward unchecked reads as boilerplate the moment one of its claims
goes stale.

**Rubio's Coastal Grill — recommend the build DROP the row.** Rubio's has zero Minnesota locations.
Wikipedia states the chain operates 17 restaurants in Arizona, 60 in Southern California and 5 in
Nevada. No amount of image or website research can fix a venue that is not in the state.

**Bowlero Brooklyn Park — stale website plus a ZIP conflict.**
`bowlero.com/location/bowlero-brooklyn-park` now 301-redirects to
`luckystrikeent.com/location/lucky-strike-brooklyn-park` following a chain rebrand. The destination
page states ZIP **55443**; the feed row carries **55445**. Both halves belong to the build rather
than to this fixer.

**Bump & Putt Family Fun Park — the feed ships a 404, and the row is held open on purpose.** The
stored website `brainerd.com/business/bump-n-putt-family-fun-park/` still returns that site's 404
body ("Sorry! That page doesn't seem to exist."). The venue's operating status remains **UNVERIFIED**
— no authoritative source was found either way, and the research agent correctly returned UNVERIFIED
rather than guessing, which is the behaviour the brief asks for. Resolving this row would bury the
fact that a dead link is being published, so it stays open as a defect marker.

## Diagnostics

### The queue has had no inflow for weeks — this run's real finding

The fixer is scoped to exactly two issue_types. Both have gone quiet:

| issue_type | last written | days silent |
|---|---|---|
| `unresolved_image` | 2026-07-23 | 57 |
| `unresolved_website` | 2026-08-16 | 33 |

Over the same period the build has continued writing roughly 80–95 error_log rows per night, so it is
not silent in general — it has simply stopped writing rows in the two categories this task drains.
And STEP 4.5 has been reporting real nightly progress throughout: `image_backfill` markers show
36 → 58 → 71 → 88 venue sites resolved on 09-14, 09-15, 09-16 and 09-17, every one of them at
`warning` severity, meaning budget-bound rather than converged.

Meanwhile the gap those two issue_types exist to track is enormous and almost entirely unlogged. The
published feed carries **4,728 rows on a generic `curated_category` image** and **1,013 rows with a
blank website**, against an open queue of **19 rows**, eleven of whose eighteen items have left the
feed altogether.

Nine consecutive post-mortems concluded the queue was licence-bound settled negatives. That diagnosis
was locally correct and globally wrong: the reason the queue never changes is that nothing writes to
it.

### The mechanism: issue_type vocabulary drift

Twenty-six rows were written on 2026-09-10 under the issue_type **`attempted_no_photo`**, and all
twenty-six are still unresolved. Their descriptions read "STEP 4.5 fetched this item's website and
found no relevance-passing photo" — they are precisely fixer-shaped work items, produced by the very
step whose leftovers this task exists to pick up. But STEP 2 selects on
`issue_type in ('unresolved_website','unresolved_image')` literally, so the fixer is structurally
blind to them and has walked past them for eight days without raising anything.

The sprawl is measurable: **553 distinct issue_types** in the log, **383 of them (69%) used on exactly
one date**. Of the 53 issue_types in the image/website family, 37 are one-off.

This is the same registry-drift class the project has already hit twice — `LIBRARY_SRC` against the
fetcher's dispatch table, which left 669 rows untagged, and `deals_yield` against
`deals_overlay.SOURCE_KEYS`, which warned falsely for four runs. Two lists naming the same things in
two files, with nothing enforcing agreement, will drift; and the drift is always silent, because the
second list's job is remediation rather than validation, so its failure mode is producing nothing
rather than producing an error.

**Deliberately not fixed in-run.** The spec defines this queue as exactly those two issue_types.
Widening the selector to sweep up `attempted_no_photo` would resolve twenty-six rows tonight and bury
the defect, which is the opposite of useful. The fix belongs to the owner and has two possible shapes:
have the build emit `unresolved_image` / `unresolved_website` again for the rows STEP 4.5 cannot
serve, or re-point the fixer's selector and constrain the issue_type vocabulary so it cannot drift
again. The second is the durable one — the first leaves two lists still free to disagree.

### Base log integrity

The local `error_log.csv` was **byte-identical to the remote** by git blob SHA-1
(`9c50ab9044952a49c671247fee0b78109fc542b8`) before any modification, so there was no stale-base
defect and no `log_base_rejected`. The header matched the ten-column schema exactly: 3,808 data rows,
3,809 CRLF, 0 bare LF.

The append was written through two controls, both of which were made to **fail on purpose** before
being trusted. A round-trip control proves the CSV writer reproduces the untouched file
byte-for-byte, so "I appended eight rows" cannot be confused with "my writer silently rewrote every
line". A carried-row control asserts the new file's first 1,217,782 bytes are identical to the old
file, and that the set of rows carrying a `resolved_date` is unchanged. Four failure cases were
exercised before the real run: missing run date, malformed run date, corrupted header, and bare-LF
line endings. All four failed as intended; the clean case passed.

### Today's build has not run

Three independent signals agree, which is what distinguishes an absent build from a missing marker:
no `run_summary` row dated 2026-09-18 exists (the latest is 2026-09-17); the repository's `pushed_at`
is 2026-09-17T09:53:19Z; and the published `msp_family_guide.json` carries
`generated_date: 2026-09-17`.

## Files

- `error_log.csv` — 3,808 → **3,816 data rows** (+8 diagnostic rows, 0 resolutions); 1,217,782 →
  1,223,645 bytes; CRLF preserved, 0 bare LF. Published to `avlhohn/msp-family-feed`.
- `error-fixing-findings-latest.md` — this report. Published to `avlhohn/msp-family-feed`.

The five category CSVs and the feed JSON were **not** touched — out of scope for this task.
