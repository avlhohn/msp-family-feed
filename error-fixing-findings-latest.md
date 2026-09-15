# MSP Family Guide — Error Fixing (Latest)

Run date **2026-09-15**, finished **04:56 US Central (09:56 UTC)**. Run date derived from the GitHub API `Date` response header (`Tue, 15 Sep 2026 09:56:49 GMT`), not the sandbox clock.

## Summary

Open queue at start: **19 rows / 18 distinct items** — 6 `unresolved_website` and 13 `unresolved_image`.

Resolved this run: **0** — website 0; image 0 (`og_image` 0, `facebook` 0, `stock_openverse_specific` 0).

Left open: **19 rows / 18 items**, rolling to tomorrow. No regressions: the base loaded byte-identical to the remote (blob `599a3ab0cdab`), all 3,625 carried rows are preserved unchanged, and no previously-resolved row was touched.

The run was scoped before any research was dispatched, which is what keeps a zero-resolution run cheap. Only **6 of the 18 items still exist in today's published feed**; the other 12 have aged out of the window and are queue residue rather than live defects — there is no live row for a resolution to enrich, so no amount of searching can close them. Of the 6 that do still ship, every one is a settled negative: two are chain-promotion image rows that are structurally unresolvable, one fails the recurrence test, one is a bad seed with no Minnesota presence, one is licence-bound, and one has no first-party web presence after twelve runs. That left exactly **one item with any discovery left** — Lake Ann Park — and this run spent nearly the whole research budget closing its last two genuinely untried routes.

Zero is the correct outcome here rather than a shortfall of effort. Lowering the verification bar is the only thing that would move the number, and the standing rule is not to; a settled negative is worth more to this pipeline than a guess. What the run produced instead is **Lake Ann Park now closed on discovery as well as on licence**, and **six diagnostics**, three of which describe defects in the pipeline itself rather than in any venue record: a gate that structurally cannot reach two of the items on this very queue, a freshness mitigation implemented one level short of the file it was meant to protect, and a sixth subagent fabrication in a shape this queue has not seen before.

## Resolved this run

None this run. No row's `resolved_date`, `resolved_by` or `resolution_note` was written, and all nineteen open rows carry forward untouched.

## Still open

**19 rows / 18 items.**

**Lake Ann Park (Chanhassen)** absorbed most of this run's budget and is now exhausted on discovery as well as bound on licence. Two routes had never been attempted. The first was Flickr searched *directly* and filtered to a CC or public-domain licence — a genuinely different question from Openverse, whose index of Flickr is incomplete and which had already returned 0 across six queries. The second was Wikimedia Commons browsed *by geographic category* rather than by name, a name search having previously returned only the Lake Ann Michigan and Arkansas collisions. Both closed NOT RESOLVED across fifteen documented probes. No City of Chanhassen and no Chanhassen Parks & Rec account exists on Flickr; the account-name literal check that caught the Cameron/Bemidji container collision on an earlier item was applied and found no candidate container to check at all. On Commons, `Category:Chanhassen, Minnesota` (34 media files), `Category:Parks in Carver County, Minnesota` and `Category:Lakes of Carver County, Minnesota` hold no Lake Ann Park photograph.

One Flickr probe returned page structure only, with dynamic content not captured by WebFetch. That is recorded **narrowly as a tooling limitation and explicitly not as a content negative** — an over-broad post-mortem is itself a way to lose a real finding, and this queue has already had one mischaracterised negative. The item remains licence-bound: real photographs of the right park exist, but on third-party rehosts we may not redistribute. Further search budget here is the wrong spend. What it needs is a licence route — a first-party upload — not more queries.

**Bowlero** is a settled recurrence-test negative from prior runs and, separately, sits inside the set STEP 4.5 structurally cannot reach (see Diagnostics).

**Denny's** and **Perkins** are structurally unresolvable in their present shape. Both are `meal_deals` rows, and a `meal_deals` row describes a *promotion*, not a venue — so there is no single venue page to point a website at and no single venue photograph to find. Closing these needs a schema decision, not research.

**Rubio's** is a bad seed: the chain has no Minnesota presence at all, so there is nothing in-state to resolve to.

**Bump & Putt Family Fun Center** has no first-party web presence after twelve runs, and this run re-framed it from a missing-website item into a four-part record defect; details in Diagnostics.

The twelve aged-out items are left open deliberately. Each row records a real historical failure, and clearing it would erase that record while enriching nothing a consumer reads.

## Diagnostics

**The curated-stock gate gap persists and is widening.** STEP 4.5's eligibility gate admits `curated_category`, `stock`, `openverse_named` and blank, but excludes `image_source = curated`. Of the 908 curated rows, **222 are stock-hosted — up from 221 yesterday** — across 36 distinct assets with reuse concentrated at 48, 36, 26, 11 and 10 rows per asset, and **152 of them (up from 151) carry a website** and are therefore mechanically fixable but unreachable. Two items on this open queue, Bowlero and Bump & Putt, sit inside that excluded set: the pass built to drain this queue structurally cannot touch them. The gap widens by a row or two per run because `curated` is a terminal state nothing re-examines. This is logged as a **persistence-plus-delta rather than a duplicate warning**, because a permanent identical warning trains the reader to skim the block. The remedy is a gate change — admit curated rows whose `image_url` resolves to a known stock CDN — not more fixer search.

**The marker `run_date` mitigation stops one level short of the guard it was written for.** Yesterday's finding was that a *fresh marker file can carry a stale field*, and the recommended tell was to assert that the marker's own `run_date` agrees with the run date passed on the command line. `step45_site_photo.py` now does stamp `run_date` into `_step45_results.json`'s `__meta__` — verified present as `2026-09-15`. But `_image_backfill.json`, the file `errlog_step7.py` actually reads, carries only `item`, `attempted`, `upgraded`, `rejected_logo`, `stop_reason` and `description`. There is no `run_date` on it, so the proposed assertion **cannot be wired**, and a carried `stop_reason` would still satisfy all three existing checks. The value is already in scope at the point of failure: line 200 binds `meta`, which holds it, and line 258 builds the marker dict without it — a one-line fix, after which `errlog_step7.py` can gain the assertion. Today's marker reads `stop_reason=deadline`, `attempted=58`, `upgraded=228`, `rejected_logo=1`, with an mtime of 03:33:39 against `_feedpull_all.json` at 03:13:27, so the file genuinely is fresh; it is one field inside it that remains unproven.

**A sixth subagent fabrication on this queue, in a new shape.** The five prior fabrications were all claims about *external* sources: an invented image description, an invented Flickr account identity, an invented hostname, bare filenames offered as URLs, and a mischaracterised negative. This one inverted the direction and asserted a value in **our own record** — "Your record shows 218-963-8833" — when the subagent has no access to the feed and the row's `phone` field is in fact the empty string. It was caught only by checking the claim against the feed row. The generalisation worth carrying: a brief that opens by quoting the item *as it appears in the feed* invites an agent to echo data back as though it had read it, so an agent's claim **about our data** must be verified against our data exactly as an external claim is verified against a fetch.

**Bump & Putt is a four-part record defect, every part verified first-hand this run.** The shipped `website` returns **404** — `brainerd.com/business/bump-n-putt-family-fun-park/` renders "Sorry! That page doesn't seem to exist." The `address` is a **relative-directions string**, "Four miles north of Nisswa, MN", not a street address, so it can never geocode. The stored coordinate `46.520522,-94.288609` sits **0.125 km from the Nisswa municipal centroid** and 9.312 km from Pequot Lakes — it is a city centroid, which the coverage spec says can never count as evidence of a venue's location, and it lies roughly 6.4 km *south* of where our own address string places the venue. Operating status is genuinely **ambiguous**: after twelve runs there is no dated evidence in either direction. A candidate real address surfaced (29107 State Hwy 371, Pequot Lakes) and has deliberately **not** been written into the record — taking an address from a lead rather than from the venue's own page is a defect class this project already logs. This one needs owner adjudication, not more search.

**Two name collisions re-confirmed**, recorded so a later run does not resolve them onto the wrong venue. "Toddler Tuesday" resolves to 800 Riverview Drive in **Winona**, not the Coon Rapids ECFE item on this queue; "Movies in the Park" resolves to Leif Erikson Park in **Duluth**, not the Mankato item. Both are generic program titles used verbatim by many Minnesota municipalities, so a same-state match is not a match — the city has to agree before either can close.

## Files

**`error_log.csv`** — 3,633 data rows after this run, up 8. The base loaded byte-identical to the remote (1,137,267 bytes, blob `599a3ab0cdab`), so there was no owner-edit divergence to reconcile and no `log_base_rejected`. A byte-identical round-trip control was established before anything was appended, the carried bytes were asserted unchanged in the output, and all nineteen open rows were re-counted after the write. Eight rows were added: seven diagnostics and one `info`-severity `fixer_summary`. Every new `issue_type` was asserted to sit outside the reserved namespace (`ical_feed_pull`, `deal_source_*`, `run_summary`, `image_backfill`) so that none of them enrols itself in a STEP 7 signal assertion. No open row's resolution columns were touched.

**`error-fixing-findings-latest.md`** — this report.

No category CSV was rebuilt or republished. This stage touches `error_log.csv` and this report only.
