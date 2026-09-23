# Agents and Workflows — project instructions

## MSP Family Guide daily build

Before STEP 2 and STEP 8 of any `msp-family-guide-daily` run, read these three files in this
folder. They **supersede** parts of the uploaded `SKILL.md`:

- **`msp-city-coverage-spec.md`** — city resolution and the coverage check. (2026-08-19)
- **`event-source-calendars.md`** — the verified event-feed list, with dead ends recorded. (2026-08-19)
- **`deal-source-registry.md`** — the verified deal/discount source list, corrected URLs,
  dead ends, and the standing-deal rule. (2026-08-22)

The supersessions:

| No longer do this | Do this instead |
|---|---|
| Parse a city with a regex requiring a literal `", MN"` | `mn_city_resolve.py` + `mn_city_gazetteer.json` |
| STEP 8's "cities where event count was low (< 3 events found)" | `mn_coverage.py` population-tiered check |
| Rediscover feeds ad hoc each run | `event-source-calendars.md` |
| Apply the two-month date window to standing deals | Exempt them; run `deals_overlay.py` as STEP 4.35 |
| Rediscover deal sources ad hoc each run | `deal-source-registry.md` |
| Rely on STEP 4.3's rules to catch title-phrasing variants | Run `dedup_titles.py` last in 4.3 |
| Take the run date from the sandbox clock or `currentDate` | Derive it from a server-side timestamp (§ below) |
| Pull LibCal via `api_events.php?date=…&days=…` | It silently serves only today's events — use `ical_subscribe.php?src=p&cid=<id>` **read raw** (2026-08-28) |
| Trust a per-category dedup pass to have found everything | Run a whole-dataset exact sweep after it (§ below) |
| Write the STEP 3 compile inline or into `.runNNNN/` | Run root `compile_step3.py` (carries the window, stale-date and `tagify()` rules) |
| Assume the fetcher's cancelled-flag drop catches every non-event | Run `closure_filter.py` as the 4.3 **tail** pass (§ below) |
| Skip STEP 4.5 because this file's image chain never named it | Run STEP 4.5 between 4.35 and 4.8: `python3 step45_site_photo.py --select N`, `--dnr`, `--apply`. It MUST write `_image_backfill.json`, which `errlog_step7.py` asserts (§ below) |
| Re-probe MN DNR `/state_parks/` pages for an image | They are JavaScript redirect stubs WebFetch cannot follow — use the calendar API's `location_tag` via `dnr_banner_map()`, and byte-check the JPEG (the API's own `image` field 404s) |

### STEP 1: never take the run date from the sandbox clock

The sandbox clock and the injected `currentDate` have **both been wrong, and wrong in
agreement**, on two consecutive runs — by ~34h on 2026-08-25 and by two full days on
2026-08-26. Because they agree with each other, cross-checking one against the other proves
nothing.

This is not cosmetic. `RUN_APIFY` is gated on the weekday. On 2026-08-26 the skewed clock read
2026-08-24, a **Monday**, so taking it at face value would have fired a paid Apify actor on a
day the spec says to skip it. The wrong date also silently shifts the whole rolling window.

Derive `TODAY` from a server-side timestamp instead — an HTTP `Date` header, or the commit
timestamps on `avlhohn/msp-family-feed` — and record the correction in `params.txt`. Helpers
that stamp their own dates (`deals_yield.py`) must be **restamped** at STEP 7, or the error log
carries two different dates for one run.

**Better than restamping: delete the literal (adopted 2026-09-08).** "Restamp it every run" is a
rule that has to be obeyed perfectly, forever, by hand — and the copied-forward
`_errlog_NNNN*.py` family shows what that is worth: `_errlog_0907_feeds.py` hardcodes
`RUN = "2026-09-07"`, so running it unchanged on 2026-09-08 files the whole run under yesterday,
silently. It is superseded by **`errlog_step7.py`** (folder root, undated), which takes the run
date as `argv[1]` and **hard-fails** on a missing or malformed one rather than defaulting to
anything. `fetch_feeds.py`'s window got the same treatment the same day — it now reads
`MSP_TODAY`/`MSP_END` from the environment and raises if either is absent, instead of carrying a
literal. The generalisation: **a date a helper can guess is a date it will guess wrong.** Where a
value must come from STEP 1, make its absence a crash, not a default. Do not restamp the
`_errlog_NNNN*.py` files; do not copy them forward.

**And a third one was caught the same day, in the worst possible place — the feed's own header.**
`build_guide.py` line 2 read `TODAY="2026-09-07"; END="2026-10-31"; DOW="Monday"`, and the restamp
was missed. Every category list, every count, all 6,661 rows were correct and current — while
`msp_family_guide.json` announced itself as **Monday 2026-09-07**, covering a window that had
already started. It published, blob-verified, and passed every count check in this file. Four
things to carry:

* **Verify the HEADER, not just the counts.** Every tripwire the pipeline has looks at rows. The
  header is the one part of the feed no row-level check can see, and it is what a consumer reads
  to decide whether the feed is fresh — so a stale header is worse than a stale row: it is a false
  claim about the whole artifact. It was found only by printing `generated_date` at final
  verification.
* **`DOW` is now DERIVED from `TODAY`, never passed separately.** Two values that must agree,
  supplied independently, will eventually disagree — and the weekday is what `RUN_APIFY` gates on,
  so a hand-maintained `DOW` is a paid-actor misfire waiting to happen, reached from a *different*
  direction than the 2026-08-26 clock skew.
* **Make a new guard FAIL on purpose before trusting it to pass** — the same discipline the
  `LIBRARY_SRC` assertion needed. The three cases exercised here were empty, malformed (`2026-9-8`),
  and a reversed window.
* **The rebuild's control was the 5 CSVs coming back byte-identical** (blob SHA-1, pre vs post),
  which proves the defect was confined to the JSON header *and* that the build actually ran — the
  build's own stdout being the second half of that proof, per the stderr rule below. Re-run
  `end_date_pass.py` after any rebuild: `build_guide.py` rebuilds rows from `BASE` and destroys
  `end_date`.

### Deleting the date LITERAL does not delete the stale run-scoped INPUT (found 2026-09-09)

`errlog_step7.py` is the file this project built to end date literals: the run date is `argv[1]` and
a missing or malformed one is a hard failure. That fix is real, and it is **only about the control
flow**. The script's two run-scoped *input* artifacts — `_findings.json` and `_run_summary.json` —
sit at the folder root under undated names and are simply **left there by the previous run**. A run
that does not regenerate one silently re-reads yesterday's file and re-stamps it with today's
`run_date`. Same defect as the `_errlog_NNNN*.py` family, arriving through the inputs instead of
through the code.

Both were stale this run, and **they failed differently, which is the finding**:

* `_run_summary.json` **was** caught — but only incidentally. The marker's counts assertion happened
  to disagree (claimed `events=4964` against a built 4950). Had the two runs' counts coincidentally
  matched, yesterday's *prose* would have published as today's marker and nothing would have
  objected. An assertion that catches a stale file only when its numbers differ is not a freshness
  check; it is a coincidence with good manners.
* `_findings.json` was **not caught at all.** All 31 of the previous run's findings were appended
  under `run_date=2026-09-09`, including a row asserting *"today is Tuesday"* (it was Wednesday) and
  a `willmar` 401 that did not occur — `willmar` returned OK. The wrong weekday is the same class as
  the `build_guide.py` `DOW` defect, and it landed in the log that exists to prove the run happened.

Three things to carry:

1. **Prose is unasserted by construction.** Every guard in this pipeline checks rows, counts, or
   bytes. A hand-written sentence inside a log row is invisible to all of them, so it is where a
   stale claim survives longest — exactly the argument the feed-header finding already makes, one
   level down.
2. **Assert freshness two ways, because content and mtime fail independently.** `errlog_step7.py`
   now requires `_findings.json` to carry exactly one `run_date_verified` finding whose item equals
   `argv[1]`, **and** requires all three run-scoped inputs — `_findings.json`, `_run_summary.json`
   and (added 2026-09-13) `_image_backfill.json` — to be newer than `_feedpull_all.json`, which every
   run necessarily regenerates, so it is a reliable "this run started" watermark. Content catches a
   file copied forward and edited; mtime catches one left untouched. `_image_backfill.json` gets a
   third branch on top of these — an existence check — because a MISSING marker is the STEP 4.5-skip
   case the guard exists to catch, distinct from a stale one.
3. **A run-scoped artifact under an undated name at a stable path is a stale-input hazard**, and the
   folder-root promotion rule that fixed helper stranding is what created it. The two rules do not
   conflict — *helpers* should be undated and stable, *run outputs* consumed by a later step must be
   proven fresh. All three new branches were made to FAIL on purpose before being trusted, and they
   fire before any append, so a failure leaves `error_log.csv` untouched.

### De-duplication: the inverted blocking key (adopted 2026-08-22)

All four existing dedup passes (`_dedup0822.py`, `_dedup2_0822.py`, `_dedup3_0822.py`,
`_dedup4_0822.py`) **block on an exact normalized title** and then compare place. They are
therefore structurally incapable of seeing *same place, same date, different title phrasing* —
which is how two `Live at the Rog: Alligations` cards reached the live app. Run this last:

```bash
python3 dedup_titles.py _compiled_work.json --dry-run   # report only
python3 dedup_titles.py _compiled_work.json             # apply
python3 test_dedup_titles.py                            # must report 16 passed, 0 failed
```

Four rules that fail silently:

1. **Only two merge rules are safe: `city_suffix` and `reordered`.** A general subset rule
   eats `Minnesota Zoo` into `Minnesota Zoo Wanderlight Trail`. A Jaccard threshold was
   measured and rejected — 0.85 already contained a false positive. **A missed duplicate is
   cosmetic; a wrong merge silently deletes a real venue.** Near-misses go to a `REVIEW`
   report, never to an auto-merge.
2. **"Geographic token" means the resolved city name plus state words — never the whole
   address.** Harvesting all address tokens made neighborhood and street names droppable and
   merged two locations of one chain (`Red Cow` / `Colossal Cafe`), which SKILL.md forbids.
3. **The survivor and the surviving title are chosen separately.** Richest row survives; the
   *longer* title wins and is copied onto it. Log the original titles before the rename or the
   report prints both sides identically and hides what merged.
4. **`_dedup3_0822.py`'s `city_of` regex requires a literal comma before the city**, so a
   bare `Maple Grove, MN` address yields an empty key and the row is skipped entirely. Fixing
   the same bug in `dedup_titles.py` took its real-data collapses from 25 to 40. `_dedup3` is
   still defective — fix or retire it, don't copy from it.

### De-duplication: every pass is blind ACROSS categories (found 2026-08-28)

`dedup_titles.py` fixed the blocking key but every pass still iterates **one category at a
time**, so a venue present in both `events` and `parks` is invisible to all of them. A plain
exact-match sweep over the whole dataset — normalized title + date + normalized address —
removed **95 rows that five dedup passes had just declared clean** (5291 → 5196), and **608
more on 2026-08-29** (6771 → 6163). Run `dupsweep.py` after `dedup_titles.py`. Two things make
it work:

1. **Normalize `Saint` → `St` and strip the MN ZIP and the bare `mn` state token from the
   address.** Without the `Saint` fold alone, 79 of the 95 stayed hidden: feeds disagree on
   `Saint Paul` vs `St. Paul` for the same street address, and every pass that compares
   addresses literally treats those as two places. Time is a *separator*, not part of the key
   — two sessions of one storytime at 10am and 2pm are genuinely two rows.
2. **A cross-category merge must follow SKILL.md's declared route for that venue, never a
   heuristic.** The first dry run proposed moving *Como Park Zoo* and *Science Museum of
   Minnesota* out of `events` into `parks`. Cause: the route parser let a
   `(route to \`parks\`)` sub-line leak past the next `### ` heading, so museums inherited
   it. Reset the section route at every heading, and let a bullet's own route win. Two pairs
   with no declared route (`lake superior zoo`, `northland arboretum`) went to REVIEW rather
   than being merged — per the precision rule above. **Always dry-run this pass**; the bug was
   caught only because the dry run named its survivors.

### De-duplication: run NO `_dedup*_0822` pass — `_dedup4` eats weekly series (found 2026-09-03)

This file previously singled out `_dedup3_0822.py` as defective, which reads as an implicit
endorsement of the other three. It is not. **All four legacy `_dedup*_0822` passes are now out
of the chain**, and the run that put them back in deleted ~1,706 real event rows before publish.

`_dedup4_0822.py` collapses same-title / same-city rows whose dates sit within 7 days, on the
theory that they are one multi-day festival. But it clusters **consecutively**:

```python
clusters=[[rs[0]]]
for r in rs[1:]:
    if (dt(r)-dt(clusters[-1][-1])).days<=7: clusters[-1].append(r)
    else: clusters.append([r])
```

Each new row is compared to the *last row already in the cluster*, not to the cluster's first.
So a **weekly** program — exactly 7 days apart, forever — chains without limit. Its own log named
the victim: `Conversation Circle for English Language Learners | 15 rows | 2026-09-09..2026-10-21`
merged to one. Running the legacy chain took events 5,388 → 3,682 (−32%). Library storytimes are
the single largest thing in this dataset and they are all weekly, so this is not a corner case.

**This contradicts a principle `dupsweep.py` already states: time is a SEPARATOR, not part of the
key.** Two sessions of one storytime at 10am and 2pm are genuinely two rows — and by the identical
argument, two *weeks* of one weekly program are two rows. A family opening the app on October 14th
needs the October 14th occurrence to exist. The rule generalises: **no pass may merge rows that
differ in `date` unless a source states the event spans those dates.** Proximity is not evidence
of spanning.

`_dedup0822.py` and `_dedup2_0822.py` are not dangerous, just redundant — they block on exact
normalized title, which `dedup_titles.py` inverts and `dupsweep.py` subsumes whole-dataset. Neither
has a test file. The documented chain is, and is only:

```
entity_fix.py         (44 passed)   PRE-pass -- runs BEFORE everything below (2026-09-10)
dedup_events_0828.py  (exact identity: event_url + date)
dedup_titles.py       (16 passed)   -> dupsweep.py (46 passed) -> closure_filter.py (35 passed)
                                    -> closed_venue_denylist.py (22 passed)
sports_dedup.py       (27 passed)   TAIL pass, added 2026-09-21 -- collapses carried free-text
                                    sports rows into their structured ESPN anchors (§ below)
```

Two things to carry: (1) **an unreferenced helper sitting in the folder is not a sanctioned pass.**
Presence is not endorsement; if CLAUDE.md does not name it in the chain, it does not run. (2) **A
large drop is a defect signal, not a productivity signal.** −32% was visible in the pass logs and
looked like thorough deduplication. What caught it was checking a known-weekly title's row count
against its distinct-date count — cheap, and worth doing after any dedup change:

```python
rs=[r for r in ev if r["title"]=="Family Storytime"]
len(rs), len({r["date"] for r in rs})    # 374 rows / 54 dates — healthy
```

### De-duplication: every pass is blind to SAME ADDRESS / DIFFERENT TITLE (found 2026-09-06)

`dedup_titles.py` exists because every earlier pass blocked on an exact normalized title, and
`dupsweep.py` then extended matching across categories. Both fixes are real, and together they read
as if the duplicate problem is now covered. It is not. **Every pass still requires the TITLE to
match before it will compare place** — `dupsweep` keys on title AND address AND date — so the
mirror-image case, *one venue written up N ways by N sources*, collides with nothing. **Sovereign
Grounds, a single coffeehouse per SKILL.md 407, was carrying 7 rows.** 16 rows collapsed to 7 across
7 groups (`step8_venue_repair.py`, folder root; idempotent, a warm re-run drops 0).

**This must stay a HAND TABLE, never a rule.** The automatic version was measured and is wrong: a
scan for "same normalized address, differing titles sharing a distinctive token" over
restaurants+parks returned 7 groups, **2 of them false positives** a rule would have merged —
`Chipotle Mexican Grill Mankato` / `Noodles & Company Mankato` (two different chains sharing a mall
address at 1600 Warren St) and `Lake Phalen Beach` / `Phalen Regional Park` (a beach inside a park;
a family searching for the beach wants the beach). Both live in `KEEP_APART` so a later reader does
not "fix" them. The standing asymmetry is unchanged: a missed duplicate is cosmetic, a wrong merge
silently deletes a real venue.

**Red Cow is the case that proves it.** Nine rows, and a genuine multi-location chain — merging on
the name is exactly the chain-collapse error. Only two pairs merged, each on evidence that is *not*
the name: `3624 W 50th St` appearing verbatim on two rows, and two rows both resolving to the
venue's own per-location URL `redcowmn.com/st-paul-selby-avenue/` (Selby Ave is in Cathedral Hill).
Uptown, North Loop, Wayzata and Rochester correctly stay four separate rows.

**The survivor can be the row with the WRONG address.** Survivors are chosen by field
`completeness()`, not by address correctness, so the richest row may carry a bad address — and its
lat/lon was geocoded *from* that address. Sovereign Grounds had exactly such a row (`2400 Third
Avenue South`, sourced from a `minnesotaparent.com` listicle sitting in the `website` field).
Because **STEP 4.9 skips populated coordinates**, a corrected address with an uncorrected pin never
self-heals on any later run. Blank `latitude`/`longitude` whenever the survivor's own address
differs from the canonical one, then re-geocode.

Two smaller items from the same finding:

* **`dupsweep.na()` maps `ste`→`st` but leaves `suite` untouched**, so `15670 Edgewood Dr Ste 120`
  and `15670 Edgewood Dr, Suite 120` normalize differently and the two Littles and Lattes rows could
  never collide. **FIXED 2026-09-07** — `ste`→`st` is gone (it was wrong twice over: it folded a
  SUITE marker into STREET *and* left the spelled form alone), and `na()` now strips
  suite/ste/unit/apt/rm/room/bldg/building/floor designators entirely. `test_dupsweep.py` 30 →
  **42 passed**. Two things the fix turns on: **order is load-bearing** — `#120` must be handled
  *before* punctuation becomes whitespace, or it degrades into a bare `120` indistinguishable from a
  house number; and **the `NA_DIFFER` half of the suite is the half that matters** — a suite number
  is droppable because it does not identify the BUILDING, while a house number is the opposite, so a
  rule that ate digits generally would merge `15670` and `15680 Edgewood Dr`. That is the wrong-merge
  error that silently deletes a real venue, reached from the normalizer instead of the merge rule.
* **A count-only tripwire hides the defect it should surface.** `play_cafe_low` read 19 against a
  floor of ~12 and passed — but 6 of the 19 were duplicate Sovereign Grounds rows and 1 was a closed
  venue, so the margin was fragmentation, not coverage. Reading the *titles* is what found both
  defects; the post-repair count is 13, one above the floor. **DONE 2026-09-07** — the check now
  prints distinct venue titles alongside the count.

**The hand table needs four more entries, and the probe that finds them must be WIDER than the name
(2026-09-08).** Reading the play-café titles again — the check that found Sovereign Grounds —
surfaced four more fragmented venues, −5 rows: `peak_cafe_edinborough`, `edinborough_playpark`,
`rebes_play_cafe`, `kids_empire_bloomington`. Three lessons, all about how they were found and how
the predicates are written:

* **Two of the four were invisible to my first probe and appeared only when I widened the pattern.**
  A second `Rebe's Play Cafe` row and the whole Peak Café group surfaced only after loosening the
  search string to `peak caf`. A fragmentation probe is searching for rows that *disagree about how
  to spell the venue* — so a probe keyed to one spelling is structurally blind to the thing it is
  looking for. Probe on the shortest distinctive stem, then read every hit by hand.
* **A "second location" can be a wrong-CITY defect wearing a location's clothes.**
  `Peak Cafe Adventure Peak - White Bear Lake` carries the address `Edinborough Park, White Bear
  Lake, MN`. Edinborough Park is in **Edina**, ~30 km away: the address string names the real venue
  and the city field is simply wrong. Read as a chain, this row must be kept apart; read as an
  address, it is the same café. **The address is the evidence, and it outranks the city token in the
  title** — the same precedence `mn_city_resolve` already applies, arriving here through the merge
  table.
* **Evidence that is not the name, one kind per group.** `edinborough_playpark` merged on
  `7700 York Ave S` appearing verbatim *and* both rows resolving to the city's own
  `edinamn.gov/.../PlayPark` path (the Red Cow Selby standard). `kids_empire_bloomington` merged on
  **coordinates agreeing to 4 decimal places** — a new evidence kind, and safe here only because
  Bloomington is currently Kids Empire's single MN location; the entry carries a comment saying it
  must gain an address qualifier the moment a second appears, or it becomes the chain-collapse
  error. `rebes_play_cafe`'s predicate is deliberately **address-qualified** rather than a bare
  title match, because a bare match also catches the `meal_deals` row *"Rebe's Play Cafe - Playtime
  with Food"* and would perform a cross-category merge on a heuristic — which `joins()` matching
  across all categories makes easy to do by accident.

Three more `KEEP_APART` entries were added alongside, for the near-misses these probes turned up.
The table only stays trustworthy if the rejected candidates are recorded next to the accepted ones.

**The `restaurants` / `meal_deals` fragmentation cluster is RECORDED AND DELIBERATELY NOT MERGED
(2026-09-09).** The same title-reading probe that found Sovereign Grounds and the Peak Café group,
pointed at restaurants, surfaces roughly 15 venues carrying 4–10 rows each. It looks like the
largest remaining fragmentation in the dataset and it is tempting for exactly that reason. **The
only evidence available per group is name similarity plus a CITY-CENTROID coordinate**, and the
centroid is worthless here: `44.9497487,-93.0931028` is shared by The Nook, Shamrocks, Gabe's *and*
Bennett's — four genuinely different Saint Paul restaurants. That is `centroid_circular`, which
`msp-city-coverage-spec.md` already says must never count as evidence, and it is the same reasoning
that keeps the `Good Times Park` pair apart. Merging this cluster would be the wrong-merge error at
scale: a missed duplicate is cosmetic, a wrong merge silently deletes a real venue. Do not "finish
the job" next run without evidence that is not the name — a verbatim street address, a per-location
URL, or non-centroid coordinates agreeing to 4 dp.

**Buried inside it is a different defect class that should NOT be fixed by merging.** Several
`X - Kids Eat Free <Day>` rows carry street addresses that look wrong for the venue named: The Nook
at `495 Selby Avenue`, Mill Valley Kitchen at `5500 Wheat Road`, Bennett's at `625 Smith Avenue
South`. A fragmentation probe finds these because they fragment, but the remedy is the
wrong-ADDRESS remedy — take the address from **the venue's own page**, never from a sibling row or
from memory, then blank `latitude`/`longitude` and re-geocode, because STEP 4.9 skips populated
coordinates and a corrected address with an uncorrected pin never self-heals. Collapsing them into
a survivor instead would pick the richest row by `completeness()` and can preserve precisely the
bad address.

### De-duplication: an HTML ENTITY is a duplicate the whole chain cannot see (found 2026-09-10)

`dedup_titles.py`'s REVIEW list surfaced two pairs that were the SAME row written twice:

```
St. Paul Farmer&#39;s Market              +  St. Paul Farmer's Market
League of Women Voters Roseville Area&#160;  +  League of Women Voters Roseville Area
```

Several feeds (RSS especially) emit HTML-escaped text into fields we publish verbatim. The
cosmetic harm — a family reading the literal characters `&#39;` in a venue name — is real but
self-reporting. **The structural harm is the one that matters: every dedup pass in this project
normalizes and compares TEXT, and `&#39;` and `'` normalize differently, so an escaped row can
never collide with its unescaped twin.** Same class of blindness as `Saint`/`St` (dupsweep) and
`Suite`/`Ste` (`na()`), reached through the character encoding instead of through the vocabulary.

`entity_fix.py` (folder root, undated) therefore runs as a **STEP 4.3 PRE-pass, before the dedup
chain, not after it** — decoding afterwards leaves the duplicate pair sitting in the dataset for
another run. Proven end to end this run: `dupsweep.py` then collapsed 4 previously-invisible
duplicates and the REVIEW list fell 16 → 12.

```bash
python3 entity_fix.py _compiled_work.json --dry-run   # report only
python3 entity_fix.py _compiled_work.json             # apply
python3 test_entity_fix.py                            # must report 44 passed, 0 failed
```

Four rules, each of which fails silently if got wrong:

1. **The double-escape guard REVERTS; it never half-decodes.** `&amp;#39;` means "display the
   characters `&#39;`", and one `html.unescape` leaves `&#39;` behind — which tomorrow's run,
   meeting the same carried row, would decode again into an apostrophe. **One level per day until
   the text is silently destroyed.** A correctly double-escaped string and an accidentally
   double-escaped one are indistinguishable, so ambiguous input is returned untouched. This is the
   standing merge asymmetry — a cosmetic miss beats a silent corruption — applied to *text* rather
   than to merges, and **idempotence is load-bearing precisely because rows carry forward**. The
   loop-based first draft failed exactly this case, which is how the guard came to exist.
2. **URLs are NOT touched.** A `&amp;` inside a query string is a legitimately escaped separator in
   some feeds, and unescaping it can break the link. Scope is the five human-readable fields only:
   `title`, `description`, `address`, `venue_name`, `location`.
3. **NBSP handling is half the fix and is invisible.** `&#160;` is the actual observed case; decode
   it to U+00A0 and stop, and the trailing-NBSP twin STILL fails to collide — the pass would *look*
   like it worked while leaving the duplicate in place. Unicode spaces collapse to U+0020 and the
   field is stripped.
4. **A bare `&` is not an entity.** "Milk & Cookies" must not count as a hit or the change report
   over-states what happened — which matters because the pass reports **BY KIND**, not as one
   total: the raw total is ~330 while the entity decodes it is named for are ~9. A bare "330 rows
   changed" reads like a mass rewrite and invites either alarm or a shrug; breaking it out is
   this file's re-measure-a-large-number rule performed once inside the pass, so the next reader
   does not have to reconstruct it by hand.

### An adult-only claim in the DESCRIPTION is unreachable by a TITLE-ONLY filter (found 2026-09-10)

`Magnet Senior Center` carried **16 rows**, and `adult_events_filter.py` has had a `55+` rule the
whole time. It could never fire: the rule matches on the title, and these rows announce their
audience only in the description. The filter's title-only scope is **deliberate and was not
widened** — description matching was measured previously and produced a real false positive
("Fiesta Latina"). So the remedy is the one this project already uses for the bar-trivia rows whose
bar-ness lives in the address: hand review plus a **proper-noun** `DROP_PHRASES` entry, not a
scope change.

A second title dropped the same way (`Dealing with Grief and Other Emotional Challenges Through
Meditation` — an adult library meditation talk). **`grief` stays a `REVIEW_PHRASE` and must not
become a DROP:** Children's Grief Connection runs real *family* grief camps in Minnesota, and a
bare `grief` keyword would delete them. Suite **137 → 145 passed**; the 4 new KEEP cases (family
caregiver consultations, a family support group, `Family Fun Night at the Eagan Senior Center`,
and two children's grief camps) are what pin the false-positive surface down for the next reader.

The general shape, and it is the third instance: **a vocabulary or scope gap in a safety filter
looks exactly like a source that has nothing to catch** — no error, no warning, just a quiet zero.
The `brewery`/`brewing` gap read the same way. Re-read the filter's reach against live titles each
run; do not infer from "no drops" that there was nothing to drop.

### A venue SKILL.md declares CLOSED rides the carried base forward (found 2026-09-06)

`MiniSota Play Cafe` (Maple Grove) was present in 2 rows — one `events`, one `restaurants` —
despite SKILL.md 404 declaring it permanently closed 2026-04-29 with an explicit *"do NOT re-add
it"* and an instruction to log `dropped_closed_venues`. **Nothing in the pipeline reads SKILL.md's
closed-venue declarations.** `closure_filter.py` cannot help: it reads a row's own title for a
cancellation notice, and a venue name announces nothing. So the row entered the carried base once
and then survived every run.

Build a standing closed-venue denylist from SKILL.md's declarations. Until that exists, check by
hand each run — and note that what surfaced it was reading the play-café *titles*, not any
automated guard.

**BUILT 2026-09-07 as `closed_venue_denylist.py` (folder root, undated name), run as the STEP 4.3
tail after `closure_filter.py`.** It dropped **0 rows** on its first run, which is the goal state —
last run's manual removal held — and the 22-case `test_closed_venue_denylist.py` passing immediately
beforehand is what distinguishes a goal-state zero from a no-op. Four rules built into it:

* **It is a HAND TABLE, not a parser over SKILL.md's prose.** The declarations sit in five sections
  in five phrasings ("permanently closed", "confirmed CLOSED", "appears to have closed its
  locations", "deliberately NOT listed"), and the failure mode of a mis-firing regex is *deleting a
  real venue*. Same discipline as `step8_venue_repair.KEEP_APART` and its merge table. (This line
  read `dupsweep.KEEP_APART` until 2026-09-09; `grep -c KEEP_APART dupsweep.py` returns 0 and the
  STEP 1 feature list already assigns `KEEP_APART` to `step8_venue_repair.py`, where it is present.
  `dupsweep`'s contribution to that finding is the suite-designator strip in `na()`, not a
  keep-apart table. A grep miss on a name this file asserts is a prose error at least as often as
  it is a stranding recurrence — open the file before concluding anything.)
* **Every row cites its SKILL.md line**, so a later reader re-verifies the claim at its source
  rather than trusting this file. That is the only thing that keeps a denylist from ossifying.
* **Contiguous token subsequence, never a loose subset** — the rule `seeds_reassert.py` already
  uses. `Safari Adventure Restaurant Week`, `Wildlife Safari Day at the Minnesota Zoo` and `Ice
  Cream Social at Izzy's Park` are all real rows a subset match would have eaten.
* **A `city` qualifier is REQUIRED where only one location closed.** SKILL.md 688 closes the
  *Burnsville* Abdallah shop; Abdallah is a live Minnesota chain, so a bare `abdallah` entry would
  silently delete every surviving location. **This is the chain-collapse error in denylist form**,
  and it is why the suite carries Apple Valley and Edina KEEP cases. Where the whole brand is gone
  (Betty Danger's, Fasika, Keg and Case) `city` is `None`.

Both new files are at the folder root and are deliberately **NOT** in the repo — it holds the
artifacts plus only the 4 safety-critical helper/test files the owner uploads by hand — so a later
STEP 1 audit must not read their `MISSING_REMOTE` as stranding. Add them to the STEP 1 feature grep.

### A signal nothing ASSERTS lapses silently, and the lapse is invisible (found 2026-09-07)

SKILL.md:840 mandates one `ical_feed_pull` info row **per feed** at STEP 7 and calls it "our
verification signal — always write it". Counting the rows by `run_date` in `error_log.csv` shows it
degrading in two stages: 4–34 rows per run through 2026-08-27, then **exactly 1** roll-up row per
run from 2026-08-28, then **zero** on every run 2026-09-01 through 2026-09-06. The per-source
`deal_source_yield` rows lapsed the same way after 2026-08-27. Nobody noticed either, for six runs.

This is the *same failure* as the `run_summary` marker lapse of 2026-09-05, and the fix is the same
one: **assert the signal by content inside the STEP 7 script.** `_errlog_0907_feeds.py` now asserts
one `ical_feed_pull` row per dispatched source, that the feed-name sets match, and that no row's
description is empty — before it will exit 0. Three things generalise:

1. **A mandated log is not self-enforcing.** SKILL.md saying "always write it" produced six runs of
   silence, because a missing row raises nothing. If a signal matters, something has to fail when it
   is absent.
2. **Degradation can be gradual and still total.** The 34→1→0 slide never looked like a break at any
   single step. Counting a mandated artifact *by run_date across runs* is what makes it visible;
   looking at one run's log tells you nothing.
3. **Build the per-feed rows from the run's own fetch report, never by hand.** `_errlog_0907_feeds.py`
   reads `_feedpull_all.json`'s `report` list, so the log cannot drift from what actually dispatched
   — which is precisely how a hand-written roll-up row decayed into a fiction in the first place.

**The `run_summary` marker describes the feed as of STEP 7, not as of the final push.** The
2026-09-06 marker records `restaurants=476`; the artifact actually published that day has **462**,
because that run's STEP 8 venue repair removed 14 rows in a follow-up commit (`c5bc9b34`). Both
numbers are honest — the marker is just written one step too early. Taking it as the carried
baseline shows a phantom −14 delta on the next run and sends someone hunting a dedup bug that does
not exist. **So compute run-over-run deltas from the published BLOBS, not from the marker**, and
verify rather than assume: `restaurants.csv` is 476 rows at `9a4d07a9` and 462 at `c5bc9b34`, which
is a two-request check. The durable fix is to move the marker after STEP 8, or to have it name the
step it describes.

**Related: `publish_feed.py` takes the COMMIT MESSAGE as `argv[1]`** and reads its token from
`github_token.txt`. Passing a token-shaped value there is silently accepted and lands a commit with
a nonsense message (the first `error_log.csv` commit on 2026-09-07 read "MISSING"). Content is still
blob-verified, so this is cosmetic — but the script cannot fail loudly on a mis-typed invocation.

**CLOSED 2026-09-08 — the marker's ordering problem is fixed by REORDERING THE RUN, not by moving
the write.** The two remedies floated above are not equivalent. Having the marker "name the step it
describes" keeps it honest but still publishes a number nobody can use as next run's baseline;
moving the write later leaves STEP 7 dependent on a step that has already published. What actually
resolves it: **run `step8_venue_repair.py` BEFORE `build_guide.py`**, so the repair's row removals
are inside the build rather than a follow-up commit, and the marker written at STEP 7 necessarily
describes the published artifacts. The repair never needed to run after the build — it operates on
`_compiled_work.json`, and running it post-build is what forced the second commit in the first
place. `errlog_step7.py` then **asserts** the marker's counts against the built CSVs row-by-row
and refuses to exit 0 on a mismatch, so the class cannot silently return. Verified this run:
marker and all five CSVs agree at 4964 / 823 / 147 / 268 / 459. Continue to compute run-over-run
deltas from the published blobs anyway — the assertion makes the marker trustworthy, but the blobs
are the thing being measured.

### A PREFIX-matched assertion turns a free-text field into a reserved namespace (found 2026-09-13)

`errlog_step7.py 2026-09-13` failed with `AssertionError: deal yield rows 11 != 10 sources`. All ten
real rows were correct (`deal_source_yield` ×6, `deal_source_non_table` ×1, `deal_source_retired` ×3).
The eleventh was a **hand-written finding** in `_findings.json` describing the yield check itself,
which I had named `deal_source_yield_check` — and the assertion matches by prefix:

```python
yields = [r for r in mine if r["issue_type"].startswith("deal_source_")]
assert len(yields) == len(yrows), f"deal yield rows {len(yields)} != {len(yrows)} sources"
```

Renamed to `deals_yield_check`; the run exited 0 with all three ASSERTED lines and the marker/CSV
count assertion passing. Four things to carry:

1. **Three `issue_type` values are RESERVED and nothing says so.** `ical_feed_pull`, anything
   beginning `deal_source_`, and `run_summary` are counted by STEP 7's signal assertions. The field
   reads as free text everywhere else in `_findings.json`, so enrolling a finding in a mandated
   signal by accident costs nothing and warns about nothing. Name a check `<thing>_check`, never
   `<signal>_check`. This is the **registry-drift class inverted** — not two lists disagreeing, but
   one list accidentally enrolling itself in the other.
2. **This file's own claim about `errlog_step7.py` was wrong, and this is the correction.** The
   2026-09-09 section says the new branches "fire before any append, so a failure leaves
   `error_log.csv` untouched." That is true of the **section-0 freshness** branches only. The
   **section-5 signal assertions run AFTER `open(LOG,"a")`**, so each failed attempt left **94 rows
   already written**. A STEP 7 assertion failure is therefore a **partial-write** failure: before
   retrying, count `run_date == <today>` rows and roll them back, or the retry double-appends.
3. **The rollback needs a byte-identical CONTROL before it filters anything.** Read the raw bytes,
   round-trip the *untouched* file through `csv.reader` → `csv.writer(lineterminator='\r\n')`, and
   assert the result equals the original (1,081,339 bytes, 3,451 CRLF, 0 bare LF on 2026-09-13).
   Only then filter and rewrite (→ 3,356 data rows, blob `500b9b24f3ba`). Without that control you
   cannot distinguish "my filter removed 94 rows" from "my writer silently rewrote every line" —
   the same reason `publish_feed.py` uploads bytes verbatim.
4. **Write the fix-up as a `.py` file, not a heredoc.** The first attempt at this rename died on
   `SyntaxError: closing parenthesis ')' does not match opening parenthesis '['` inside a long
   description string — and because it was chained `&& python3 errlog_step7.py`, **the shell ran the
   retry anyway**, appending a second 94 rows. That is the stderr/exit-status rule from 2026-09-06
   reaching the same outcome from the opposite direction: there the `&&` suppressed a run that should
   have happened, here it permitted one that should not have.

### A count-only tripwire can be flat while the underlying number moved (found 2026-09-08)

`mn_coverage.tiered_coverage` returned **46 warnings** this run, against **20 `coverage_shortfall`
rows** in the previous run's `error_log.csv`. That reads as a 130% regression and sends you hunting
a coverage collapse. It is not one: the 2026-09-06 and 2026-09-07 `coverage_summary` descriptions
**both also say 46**. The 20 was a *logging cap* — the error-log backlog rule truncates how many
shortfall rows get written — so the count in the log and the count from the checker are measuring
different things and were never comparable.

The generalisation is the mirror of the `play_cafe_low` finding: there, a count passed while the
underlying titles were rotten; here, a count looked alarming while the underlying reality was flat.
**Compare a tripwire against the same tripwire's own prior reading, never against a downstream
artifact that may be capped, sampled, or rolled up.** The `coverage_summary` row exists precisely
because it carries the uncapped number; read it before reacting to the row count. And when a
capped log and an uncapped checker disagree, the discrepancy is a fact about the logging, not about
the data.

### Registry drift, third instance: `compile_step3.LIBRARY_SRC` ↔ the fetcher's dispatch (found 2026-09-08)

`tagify()` stamps the `library` tag from a `LIBRARY_SRC` set of source keys. Wiring `sppl` into
`fetch_feeds.py` on 2026-09-07 added the single largest library source in the dataset — and
`LIBRARY_SRC` was not updated, so **669 SPPL rows arrived with no `library` tag**, which is exactly
the untagged state that once paired a bilingual storytime with a fire-truck photo. Nothing warned:
a source missing from a tag registry produces correctly-shaped rows that are merely less useful.

This is the same shape as `deals_yield` ↔ `deals_overlay.SOURCE_KEYS` and the adult filter's
`brewery`/`brewing` gap. **Two lists naming the same sources, in two files, with nothing enforcing
agreement, will drift — and the drift is always silent, because the second list's job is
enrichment, not validation.** The fix is not vigilance. `compile_step3.py` now carries
`_assert_library_src_covers_fetcher()`, which parses the `LIBCAL`/`BIBLIO` dispatch tables out of
`fetch_feeds.py` and **fails the compile** if any dispatched library source is absent from
`LIBRARY_SRC`. Post-fix, 3,605 events carry the tag.

One implementation note worth keeping: the first parser used a line-oriented regex and mis-read
the tables, because the entries span lines and carry nested parentheses. It needs a
**bracket-depth scan** to find each table's true extent. A registry-sync assertion that silently
under-reads the registry it is checking is worse than none — it manufactures the confidence it was
supposed to earn. Verify a new assertion by making it FAIL on purpose before trusting it to pass.

### A geocode pass reporting ZERO API calls is not automatically broken (found 2026-09-08)

`geocode_pass.py` printed `api_ok=0, api_none=0, api_err=0, elapsed_s=1.9` — the exact signature
of a pass that no-opped, and the "nothing changed vs nothing ran" ambiguity this file warns about.
Three checks settled it without touching the helper, and they are the right order:

1. **Make the accounting add up.** 18 `cache_hit` + 170 `cache_negative` + 64 unusable-key = 252,
   which is every candidate row. There was no silently skipped remainder — the pass considered
   everything and had a cached answer for all of it.
2. **Prove nothing real was suppressed.** The worry is a good address being dropped as an
   "unusable key". **Zero** of the 223 unresolved rows match `^\s*\d+\s+\S` — i.e. not one of them
   is a street address at all; they are venue names and city-only strings, which is what
   `cache_negative` correctly holds.
3. **Confirm the API path is live, later in the same run.** The post-repair re-geocode (the merged
   survivors whose lat/lon was blanked) returned `api_ok=1`. The geocoder does reach Nominatim; it
   simply had nothing new to ask.

Carry the shape, not the numbers: **a zero is a claim about the INPUT until you have shown the
code path can still fire.** The negative geocache is designed to produce exactly this output on a
converged dataset — the same way the Wikimedia layer's 0-applied run is the expected result, not a
regression. Reflexively "fixing" it means re-querying Nominatim for thousands of cached addresses
at ~1 req/s and spending the whole budget rediscovering what is on disk.

### A control that suppresses stderr turns a crash into a false PASS (found 2026-09-06)

Establishing a before/after control for the STEP 8 repair, I ran
`build_guide.py >/dev/null 2>&1 && end_date_pass.py`. `build_guide.py` takes its source as
`argv[1]` and **defaults to `_compiled_base.json`, which does not exist** (STEP 5 passes
`_compiled_work.json` explicitly), so it raised `FileNotFoundError`, the `&&` short-circuited, and
**neither script ran**. The artifacts were therefore untouched, the blob comparison reported SAME
for all six, and the control looked like a clean PASS while proving nothing.

Re-run as `build_guide.py .pre_step8_compiled.json` with stderr visible, it genuinely reproduced
every published blob — which is what made the subsequent −15 attributable. **In any control or
verification step: do not redirect stderr to /dev/null, check exit status explicitly rather than
relying on a silent `&&` short-circuit, and be suspicious of a control that passes with no
observable side effect** — "nothing changed" and "nothing ran" produce identical evidence.

### A row can announce its own non-occurrence in its TITLE (found 2026-08-31)

30 rows were closure/cancellation **notices carried as events**: `CANCELED: Baby Storytime`,
`LIBRARY CLOSED: Labor Day`, `SCL Branches Closed - Labor Day`, `City Hall Closed - Labor Day`.
A family opening the app saw these as things to go to.

Every existing guard missed them for one reason. `fetch_feeds.py` drops LibCal/BiblioCommons rows
carrying a machine-readable **cancelled status flag** (14 dropped on 2026-08-31), but these rows
carry the cancellation in the **title text**, so there is no flag to test. They then enter the
carried base and survive every later run: no dedup pass looks at meaning, and
`adult_events_filter.py` screens for adult *audience*, not for non-occurrence. Run
`closure_filter.py` (folder root) as the **tail** of STEP 4.3, after `dupsweep.py`:

```bash
python3 closure_filter.py _compiled_work.json --dry-run   # report only
python3 closure_filter.py _compiled_work.json             # apply
python3 test_closure_filter.py                            # must report 35 passed, 0 failed
```

**The standing merge asymmetry inverts here, so do not import it.** For merges a missed duplicate
is cosmetic while a wrong merge silently deletes a real venue. That does not transfer: the row's
own title is the evidence, and the source is stating the event will not occur, so dropping it
removes a claim the source already retracted. The risk runs the other way — toward a false
*positive* that drops a real event whose title merely contains "closed". Hence both patterns are
deliberately narrow and anchored, and **must not be loosened to raise recall**:

* `CANCELLED` only as an explicit marker — string-initial, `**`-wrapped, or immediately followed
  by `:` / ` - `. A bare mid-sentence "cancelled" does NOT match, because "rain or shine, never
  cancelled" is not a cancellation.
* `CLOSED` only when preceded by an institution word (library / branch / office / city hall /
  center / museum / pool / building / service center / all locations), or as the noun `closure`.
  This is what keeps `Closed Captioning Workshop`, `Closed Loop Recycling` and `Close Reading
  Book Club` alive — all real programming shapes — and what lets `Fall Festival at the Ramsey
  County Library` and `Family Night at City Hall` survive despite containing an institution word.

Idempotent (a warm re-run drops 0) and it prints every dropped title, so a wrong drop is visible
rather than silent — the same standard `dupsweep.py` is held to. **Review the drop list**; 29 of
30 were dropped on 2026-08-31 after individual review. Every DROP case in the test file is a real
observed title and every KEEP case is a false positive a looser pattern would have produced.

### `is_seed` does not survive the schema round-trip either (found 2026-08-28)

`is_seed` arrived **False on all 5,291 carried rows**, so every dedup pass this run had been
choosing survivors with no seed precedence at all. Same mechanism as `deal_source` above:
`is_seed` is not one of the 19 BASE fields and `build_guide.py:22` rebuilds each row as
`{k: it.get(k,'') for k in BASE}`, so the marker is created, consumed, and destroyed inside a
single run. **Re-derive it before STEP 4.3, every run** (`seeds_reassert.py`: 0 → 357 rows
marked on 2026-08-28, 0 → 359 on 2026-08-29).

It reports seed-list drift against `seed_names_snapshot.json` (at the folder root since
2026-08-29; previously stranded in `.run0822/`). **Refresh that snapshot once you have reviewed
the drift** — otherwise the same delta is re-reported every run and stops being read. The snapshot
had been frozen at 182 names since 2026-08-22, so the same `+20 / −2` delta was re-reported on
every run in between. It was refreshed to **200** on 2026-08-30, to 233, and to **257** on
2026-09-10; drift is `+0 / −0` again and **257 is the current baseline**. The 2 "removals" seen on
2026-08-30 were never removals — they were `Eagan Community Center` and `Plymouth Community Center`
with qualifiers appended (`— The Blast`, `— K.U.B.E. Indoor Playground`). Read a drift report
before acting on it. The 24 names added on 2026-09-10 were likewise not a pipeline event: they map
one-to-one onto the owner's between-run commits `9c8d7bce` / `4149d05c` / `79d3b327` / `0450c5b9`,
which is the same owner work the blob-vs-marker gap independently showed — **two unrelated
directions agreeing is what makes a drift number safe to absorb.**

**The banner reporting this drift carried a HARDCODED snapshot date until 2026-09-10**, and it had
been wrong for 19 days: it read "vs 2026-08-22 snapshot" long after the 2026-08-30 refresh, so a
reader was told they were diffing against a file that had already moved. Fixed by deleting the
literal — the date is now read from the snapshot file's own mtime. Same class as the
`_errlog_NNNN` family, and the same remedy: **a date a helper can guess is a date it will guess
wrong.** Note that `seeds_reassert.py` imports `os as _os`, so the call is `_os.path.getmtime`.

Regenerating the snapshot has exactly one correct form, and the file has three plausible ones:

```python
names, _span = m.parse_skill_names()      # returns a (names, span) TUPLE, not a list
snap = [{"name": n, "slug": " ".join(m.toks(n))} for n in sorted(set(names))]
```

`seed_key()` is the wrong function here: it returns a `(tokens, mode)` **tuple**, and it *keeps*
parentheses for single-token names, while the helper's own self-check at line 102 compares against
`" ".join(toks(name))` with parentheses **stripped**. So `CAMP (Minneapolis)` stores as `camp`,
not `camp minneapolis`. Getting this wrong fails loudly (`NORMALIZER MISMATCH on N seeds`) — good.
Run the self-check and require 200/200 before writing. A seed the dataset is missing entirely (Brunson's Pub, 2026-08-29) is
invisible to every yield check, because there is nothing to count; take its address from the
venue's own page, never from memory, then geocode and bbox-validate before seeding.

As with `deal_source`, **do not fix this by adding `is_seed` to `BASE`** — Base44 reads the
21-column contract. Treat "a boolean that is False everywhere" as suspicious on sight; that is
the signature of a field lost at build, not of a genuinely empty attribute.

Two matching rules that matter when re-asserting seeds:

* Match a **contiguous token subsequence**, never a loose subset — a subset match pulls
  unrelated venues in. Single-token seed names need an exact or parenthetically-qualified
  match. Parse the seed span from `SKILL.md` at runtime and diff it against the previous
  snapshot, so drift in the list is reported (+19 / −2 this run) rather than silently absorbed.
* Re-assert **seed coordinates** too, but only where the row title *equals* the seed's and
  exactly one row matches. Seed venues can carry a correct address with a wrong coordinate,
  and STEP 4.9's geocode pass skips populated coordinates, so those never self-correct: the
  Bell Museum's pin sat on the campus it left in **2018**, 3.3 km from the door. Do not
  generalise to variant titles — `Sky Zone`, `Urban Air` and `Candyland` variants are
  different locations of a chain, and stamping one coordinate on all of them is the
  chain-collapse error in coordinate form.

### A MISSING seed is invisible to every count — read the `missing:` line, not the marked total (found 2026-09-21)

`seeds_reassert.py` reported **257/257 self-check, drift +0/−0, 372 rows marked** — three healthy
numbers — and, on a line nothing asserts, **`missing: 2`**. Both were must-include fall
orchard/farm seeds (SKILL.md 758, 761) in **peak season** inside a window ending 2026-10-31:
**Afton Apple Orchard** and **Joyer Adventure Farm at Waldoch Farm**. This is the Brunson's Pub
class restated with a year's more evidence behind it: **a seed the dataset lacks ENTIRELY is
invisible to every yield and coverage check, because there is nothing to count** — and the drift
report cannot see it either, since drift compares the SKILL.md list against the *snapshot*, not
against the dataset. A `+0/−0` drift and a missing seed are perfectly compatible.

Emitted as standing seasonal rows with a **blank date** (SKILL.md 757's declared route for an
in-season orchard). Three rules held in the writing of them:

* **The 21-key contract is COPIED from a live row, never typed**, with an assert rejecting any
  key not in it — the `deal_source`/`is_seed` lesson applied at the point of creation rather than
  discovered at the build.
* **Address and phone come from the VENUE'S OWN PAGE**, never from memory or a sibling row.
  Waldoch's page gives `8174 Lake Drive, Lino Lakes, MN 55014` and `(651) 780-1207`, and it also
  moves Fall Fun's start from SKILL.md 761's *Sept 20* to **Sept 19** — **the page wins over the
  spec's recollection of the page.**
* **Neither description asserts a price or an hour that was not verified** — the
  `deal_description` standard, which is about factual claims a family acts on, not about deals.

**`aftonapple.com` is a JavaScript shell and a permanent dead route**, not a retry case: WebFetch
sees page-structure identifiers and GCS script references, no address, hours, prices or image
URLs. Same class as the MN DNR `/state_parks/` stubs and the parked `larl` domain — recorded here
so a later run does not re-probe it cold, and so STEP 4.5 does not book it as "a site with no
photo." Afton's seed therefore falls back to SKILL.md 758's own declared address and coordinates.

**The same stem probe then found ONE festival written THREE ways, all dated 2026-09-26, invisible
to the entire dedup chain.** `dedup_titles` blocks on an exact normalized title and neither safe
rule (`city_suffix`, `reordered`) spans *Afton Apple Festival* ↔ *Afton Apple **Fall** Festival*;
`dupsweep` keys on title AND address AND date, so the differing titles defeat it **before the
identical address is ever compared**. Rows 1–2 merge on the street address **verbatim** (and it is
SKILL.md 758's declared address); row 3 carries only `Afton, MN` with that city's centroid pin —
`centroid_circular`, never evidence — and joins on the Sovereign Grounds standard instead, SKILL.md
758 declaring exactly **one** Afton Apple so a title match carries no chain-collapse risk. Its city
token is **wrong** (the orchard is in Denmark Township/Hastings): the Peak Café / White Bear Lake
shape again. `force_recoord`, because the three rows carried three mutually inconsistent pins (the
outer two ~18 km apart) and SKILL.md asserts a fourth matching none. Both predicates were made to
FAIL ON PURPOSE **using the real `joins()`, not a reconstruction** — dropping the word-`festival`
qualifier pulls the new *standing* seed row into a *dated* merge (4 hits, not 3), and dropping the
second predicate loses the `Fall Festival` row, since `afton apple festival` is not a substring of
`afton apple fall festival`. The seed/festival pair is in `KEEP_APART` so a later reader does not
collapse them.

**The pin was then reconciled against the spec rather than against the geocoder.** Re-geocoding the
merged festival's verbatim address disagreed with SKILL.md 758's declared coordinate for that *same
verbatim address* by **8.85 km**. Resolved in favour of the declaration: the spec's coordinate is a
hand-verified claim about a named seed venue, while the geocoder's is a lookup over a rural address
in a township whose name the postal address does not carry — and STEP 4.9 skips populated
coordinates, so the wrong one would never self-heal. **When a declared seed coordinate and a fresh
geocode disagree, the declaration wins and the disagreement gets logged**; it is the inverse of the
Bell Museum case, where the declaration was the stale side, which is exactly why the gap must be
*recorded* rather than silently resolved either way.

**Registry drift, fourth form: prose in one file asserting a row in another.** SKILL.md 761 states
Joyer Adventure Farm's image is a hand-pinned owner-supplied photo (`image_source: curated`) that
the image pipeline must not overwrite — and `curated_images.csv` carries **no entry** for
waldoch/joyer. The instruction names an asset the registry cannot supply, so the row could not be
restored with it. Same shape as `LIBRARY_SRC` ↔ the fetcher's dispatch and `deals_yield` ↔
`SOURCE_KEYS`, one level up: there, two code registries drifted; here, a *sentence* and a registry
did, with nothing able to enforce agreement between them. The seed was emitted with a **blank**
`image_source` deliberately, which puts it inside STEP 4.5's `GATE` so the tested site-photo path
can resolve it from `waldochfarm.com` — rather than fabricating a curated URL, which would launder
a guess into `REAL_PHOTO_SOURCES`, where it never self-heals.

### `price_type` and stale dates: two unvalidated fields the carried base preserves

Nothing in the pipeline validates `price_type` against its schema enum
(`Free | Paid | Varies`), so a bad value survives forever. **Fill blanks from a source, never
from a guess** — library and DNR sources are declared free by SKILL.md, a quoted dollar amount
means `Paid`, and **everything else is `Varies`, not `Free`**. Municipal and CVB feeds publish
free and ticketed events side by side; stamping `Free` on them ships a claim no source made.
`Donation`/sliding-scale is `Varies`. (282 fixed on 2026-08-28.)

Separately, every out-of-window row this run was dated **exactly the previous run's `TODAY`**.
That is an "as-of" stamp a recurring row picked up when written, which ages out one day later.
`build_guide.py` already blanks `date` for `restaurants` and `parks` for this reason; the same
leak is unhandled in `meal_deals` and `volunteer_opportunities`. Roll the date forward **only**
if the row's own text states a range still covering today; otherwise blank it. Never roll
forward unconditionally — that asserts an event is still running on the strength of nothing but
its having existed yesterday. Implemented 2026-08-30 as `covers_today()` in `compile_step3.py`:
an out-of-window `events` row is dropped, but an out-of-window `meal_deals` /
`volunteer_opportunities` row has its date **blanked and the row kept**. A blank date also means
a standing/recurring attraction (SKILL.md 546, 610) and must never be aged out.

### Publishing: verify by git blob SHA-1, not by size

`gh_publish_feed.py` hardcodes one path and verifies with `size >= 50000`. That check is both
too weak (last run's copy passes if the PUT no-ops) and too strong (it produced the known false
`parks.csv` publish FAIL, because an idempotent PUT leaves the sha unchanged). Use
`publish_feed.py`, which computes `sha1("blob <len>\0" + bytes)` locally — exactly what the
contents API reports in `sha` — and compares. An idempotent publish is then a PASS and a stale
remote an unambiguous FAIL. It ships all six artifacts; `error_log.csv` is a seventh call after
STEP 7, and `--only <file>` ships a single one. Upload bytes verbatim: the published CSVs are
CRLF (what `csv.DictWriter` emits), and rewriting line endings churns every line of every file
for no benefit.

An idempotent PASS is worth reading rather than skimming past. On 2026-08-29 `parks.csv` and
`deals.csv` were both byte-identical to the remote — genuine, because both categories arrived
from the carried base already fully enriched (no blank `price_type`, no blank `image_url`, no
rows collapsed), so every pass correctly had nothing to change. Confirm that story before
accepting it: an identical artifact can equally mean a pass silently no-opped.

### Helpers live at the folder ROOT, under undated names (adopted 2026-08-29)

Every helper this file names now sits at the folder root with a stable, undated name:
`dupsweep.py`, `seeds_reassert.py`, `publish_feed.py`, `pricetype_fix.py`, `fabguard.py`,
`geocode_pass.py`, (since 2026-08-30) `compile_step3.py` plus `run_decc()` inside the root
`fetch_feeds.py`, (since 2026-09-07) `closed_venue_denylist.py` plus Saint Paul Public Library
inside the root `fetch_feeds.py`, (since 2026-09-08) `errlog_step7.py`, (since 2026-09-11)
`run_tribe_rest()` / `_tribe_venue()` / `span_status()` inside the root `fetch_feeds.py` with
`test_tribe_rest.py` beside it, (since 2026-09-14) `step45_site_photo.py` with its
`dnr_banner_map()`, and (since 2026-09-12) `month_urls()` / `MONTH_LOOP_ICAL` in the
same file and the same suite, (since 2026-09-19) `sports_coverage.py`, (since 2026-09-20)
`espn_sports.py`, and (since 2026-09-21) `sports_dedup.py` — add each new suite to the STEP 1
test-baseline list, which is now **12** suites, every count below RE-READ live on 2026-09-22:

| suite | 2026-09-22 |
|---|---|
| `test_adult_events_filter.py` | **175** |
| `test_entity_fix.py` | 44 |
| `test_dedup_titles.py` | 16 |
| `test_dupsweep.py` | 46 |
| `test_closure_filter.py` | 35 |
| `test_closed_venue_denylist.py` | 22 |
| `test_end_date_pass.py` | 20 |
| `test_city_resolve.py` | 22 |
| `test_tribe_rest.py` | 41 |
| `test_sports_coverage.py` | **34** |
| `test_espn_sports.py` | 75 |
| `test_sports_dedup.py` | **36** |

Three counts moved on 2026-09-22 and **all three are numbers this file itself asserted wrongly one
run earlier**, which is worth more than the counts are. The adult filter 169 → **175** and
`test_sports_coverage` 15 → **34** are this run's own work (the `bar crawl` vocabulary completion
and the shortfall-attribution softening, both § below). `test_sports_dedup` 27 → **36** is the
instructive one: the suite was **already 36 when the 2026-09-21 table was written**, because that
cell was filled in from the prose section that *built* the helper rather than from the suite
itself — the table created to end stale pass-count claims was seeded with one. Re-reading a
count from a sibling paragraph is not re-reading it. Total across the 12 suites: **566 passed,
0 failed.**

**The prose list this table replaces was stale in BOTH directions at once, which is the argument
for the table.** It read "**9** suites: 145 / 44 / 16 / 42 / 35 / 22 / 20 / 22 / **41**" — three
counts low (adult filter 145 vs 169, dupsweep 42 vs 46, and `test_espn_sports` 58 vs 75) and two
suites missing entirely (`test_sports_coverage.py` added 2026-09-19, `test_espn_sports.py` added
2026-09-20, both by sections *in this same file* that never came back to amend this line). A
count that is too LOW is the benign direction — someone improved the helper — but a *missing
suite* is not benign at all: a suite absent from the baseline list is a suite STEP 1 never runs,
so a regression in it is invisible. (`test_tribe_rest.py` was **34** when written on 2026-09-11
and gained 7 `month_urls` cases on 2026-09-12.) The rule is unchanged and is why the table
carries a date: a pass-count claim has to be re-read against reality each run or it decays into
the stale tripwire it was written to prevent. Report paths resolve at runtime from `MSP_RUNDIR`
(default `.`), so nothing is pinned to one run's scratch directory.

**Grep for the feature as it is actually spelled, and read the file before concluding it is
missing (2026-09-08).** This file told STEP 1 to grep `fetch_feeds.py` for **`run_sppl`**, and
`grep -c run_sppl` returns **0** — which reads exactly like the stranding recurrence that caused
DECC and `tagify()` to be built twice, and invites a second re-implementation of a 669-row
source. It is not one. SPPL is a BiblioCommons system like `rclreads`, so it is correctly wired
as a row in the `BIBLIO` list (`fetch_feeds.py:291` — `("sppl", "Saint Paul Public Library")`)
and dispatched by the existing `run_biblio()`; a bespoke `run_sppl()` would duplicate the
pagination and the `/locations` address join. The grep target is now `sppl`. Generalising:
**a feature grep asserts a NAME, and the name is the fragile part** — the honest check is
"does this source dispatch?", so when a grep misses, open the file and look for the feature
under another shape before rebuilding it. Fixing the target costs one line; rebuilding a wired
source costs a day and can regress it.

The STEP 1 feature grep should therefore look for, at minimum: `run_decc`, `sppl`, and — added
2026-09-11 — `run_tribe_rest`, `TRIBE_FEEDS` plus `span_status`, and — added 2026-09-12 —
`month_urls` plus `MONTH_LOOP_ICAL`
(`fetch_feeds.py`), `tagify` and `covers_today` (`compile_step3.py`), `wikimedia` and
`_wiki_prime_cache` (`image_upgrades.py`), `_compound_drop` (`adult_events_filter.py`), `ntime` and
the suite-designator strip in `na()` (`dupsweep.py`), `KEEP_APART` (`step8_venue_repair.py`),
`DENYLIST` (`closed_venue_denylist.py`), `pumpkintrail` (`deals_overlay.py`), the blob SHA-1
verify (`publish_feed.py`), and — added 2026-09-10 — `RX_ENTITY` plus the double-escape guard
(`entity_fix.py`) and `magnet senior center` (`adult_events_filter.py`), and — added 2026-09-13 —
`_image_backfill.json` plus `image_backfill` (`errlog_step7.py`, the STEP 4.5-ran guard), and —
added 2026-09-14 — `dnr_banner_map` plus `MAX_FANOUT` (`step45_site_photo.py`, the STEP 4.5 helper
itself) and `force_recoord` (`step8_venue_repair.py`), and — added 2026-09-16 —
`stillwater_libcal` (`fetch_feeds.py`, the washco sub-calendar fan-out) plus **`run_date` in BOTH
`step45_site_photo.py` and `errlog_step7.py`**, which are one assertion in two halves and are
worthless apart: the helper stamps the marker, the logger checks it, and either half alone passes
on a stale value, and — added 2026-09-18 — **`__rejected__`, `REJECT_SEED` and `load_seen`** (all
three in `step45_site_photo.py`). Those three are also one mechanism in parts and a miss on any of
them is silent in a distinctive way: without `load_seen` the pass still *works*, it just re-buys
answers it owns and reports a healthy-looking `deadline`; without `__rejected__`/`REJECT_SEED` it
re-fetches pages already proven to have no valid photo. **Both failures present as a converged pass
under budget pressure, which is the hardest shape in this file to tell from success.** And — added
2026-09-19 — **`TEAMS` plus `coverage` (`sports_coverage.py`, the STEP 8 sports tripwire)**, whose
absence is the exact silent-failure class it was built to close: a named team can drop to zero rows
with nothing warning, and — added 2026-09-20 — **`run_espn_sports` (`fetch_feeds.py`) plus `TEAMS`
and `schedule_url` (`espn_sports.py`, the STEP 2 structured sports SOURCE)**, whose absence would
silently return sports to the free-text-only path the tripwire exists to catch.
And — added 2026-09-21 — **`_to_local_date_time` plus `timeValid` (`espn_sports.py`, the
unannounced-kickoff placeholder guard)**, whose absence silently refiles evening games a day early
with a fabricated 11 PM start; **`MIN_ANCHOR_TOKENS` plus `find_groups` (`sports_dedup.py`, the
STEP 4.3 structured-vs-free-text collapse)** — and note that the *first draft of this very line*
named `ANCHOR_SRC` and `one_home_game_per_day`, neither of which exists, so the audit it was
written for would have reported a stranding recurrence for a helper sitting right there: **a
feature grep asserts a NAME, and the name is the fragile part**, confirmed once more by writing
the list from memory instead of from the file; and **`minnesota` inside `dupsweep.na()`**, the
trailing-only spelled-state strip — note that target is a *substring of ordinary data*, so unlike
every other entry on this list a bare grep hit does not prove the feature is present. Open `na()`
and confirm the strip is **trailing-only**; a hit on an over-broad variant is the wrong-merge
error passing an audit designed to catch its absence.

`closed_venue_denylist.py`, `step45_site_photo.py`, `sports_coverage.py`, `espn_sports.py`,
`sports_dedup.py`, `entity_fix.py` and their tests are **not** in the repo by design — do not read
their `MISSING_REMOTE` as stranding. The repo holds the 7 artifacts, `curated_images.csv`,
`_wiki_cache.json`, and only the 4 safety-critical helper/test files the owner uploads by hand.

This replaces the recurring stranding bug: helpers were repeatedly left in the *previous* run's
`.runNNNN/` folder while this file told the *next* run to execute them, and several carried
absolute `/sessions/<name>/` paths from sessions that no longer existed. Two rules follow.

1. **Never write a helper the next run needs into `.runNNNN/`.** That folder is scratch, private
   to one run. Write it to the root.
2. **A helper that derives a path from `__file__`'s parent breaks the moment it is relocated.**
   `geo0826.py` did exactly this: run from the root it looked for `_geocache.json` one level too
   high, found nothing, and would have re-queried Nominatim for all 2,261 cached addresses at
   ~1 req/s — the whole budget spent rediscovering what was on disk, with no error. Pin absolute
   paths, or resolve from an env var. Make a helper location-independent *before* promoting it.

**The rule was written on 2026-08-29 and broken the same day.** On 2026-08-30, `grep -ci decc`
over the root fetcher returned **0** again and `tagify()` was gone too: both had been implemented
on 2026-08-29, both into `.run0829/`, and both were lost. Two mandated features were therefore
built twice. Writing the rule down is not the same as following it, so make this a STEP 1 check
with teeth: before starting, grep the root for each feature this file claims exists, and treat a
miss as a stranding recurrence rather than as a feature that was never requested. Their permanent
homes are now `compile_step3.py` (STEP 3 compile + `tagify()`, resolves every path at runtime,
hardcodes no date) and `fetch_feeds.py::run_decc()`.

Two further STEP 1 audits, both of which caught real damage on 2026-08-29:

* **Compare every helper against its committed copy by git blob SHA-1, not by size.** The local
  `adult_events_filter.py` was 8,316 b against 12,034 b in the repo, and its test reported
  **39 passed** where the committed test then reported **70** — 31 test cases' worth of adult-content
  rules missing. (The committed test reported **85 passed** after the 2026-08-31 vocabulary
  hardening; the owner hardened it again on 2026-09-01 to **131 passed**, and `test_dupsweep.py`
  gained a suite the same day at **30 passed**. Both were raised again on 2026-09-07 to **137** and
  **42**; the adult filter moved again on 2026-09-10 to **145**, so the current baselines are
  **145** and **42**; see the note at the end of this section.) Running it leaks adult events into a
  family guide. A test pass-count that differs from the documented one is itself a stale-helper
  signal. Preserve the local as
  `.local_*`; never overwrite blind. Expect the drop count to *rise* after restoring a correct
  filter (574 vs the ~230 tripwire) — that is the fix working, not a regression.
* **Restamp every helper that stamps its own date, and grep for the previous run's date digits
  separately from bare paths.** `_staledate*.py` carried a stale `TODAY` and reported "0 rows
  repaired" while printing the wrong date; restamped, it found 4. And a copied-forward fetcher
  kept `f"_feedpull_{which}_0828.json"` — the date literal sat *inside an f-string*, so a
  path-rewriting pass missed it, and the run would have overwritten the prior run's artifacts
  and read them back as fresh.

**The audit runs in BOTH directions — decide which side is stale, don't restore reflexively
(found 2026-09-01).** The remedy written above is "preserve the local, restore from committed,"
because on 2026-08-29 the local was the stale copy. On 2026-09-01 the direction was **inverted**:
local `adult_events_filter.py` was 13,580 b carrying the 2026-08-31 vocabulary hardening with its
test reporting the documented **85 passed**, while the committed copy was 12,034 b and
pre-hardening — the 2026-08-31 work had never been pushed. Applied mechanically, "restore from
committed" would have overwritten a hardened safety filter with a weaker one and logged it as a
fix. So a DIFFER is not by itself a verdict: compare **test pass-counts against the documented
baseline** (and check whether the newer side's documented features actually fire — the compound
bar-trivia rule firing in STEP 4.3 confirmed the hardened filter was the one running). Then
publish the winning side, or the next run's audit re-opens the same DIFFER and can regress it.
Note also that CLAUDE.md's own pass-count claims go stale the moment local work is left unpushed;
a claim about "the committed test" is only true after the push lands.

**CLOSED 2026-09-02: the push landed, and the baseline moved again.** The 2026-09-01 DIFFER is
resolved — `adult_events_filter.py` (17,224 b) and `dupsweep.py` (13,366 b) and both their tests are
now **byte-identical local vs committed**, so there was no stale-helper defect this run. The owner
hardened both further on 2026-09-01 (adult filter 85 → 131 passed, dupsweep → 30 passed,
gaining `ntime()` clock canonicalization after 350 time-format duplicates were found live). Two
things worth carrying:

* **The pass-count baseline is the thing that drifts, not just the bytes.** This file asserted 85
  while both sides said 131. A pass-count claim that is *lower* than what the suite reports is the
  benign direction (someone improved the helper); a claim that is *higher* is the dangerous one.
  Either way the assertion has to be re-read against reality each run, or it decays into the stale
  tripwire it was written to prevent.
* **The repo is a PUBLISH TARGET, not a helper backup.** It holds the 7 artifacts plus
  `curated_images.csv`, `_wiki_cache.json`, and only the 4 safety-critical helper/test files the
  owner uploads by hand. The other 24 root helpers return MISSING_REMOTE **by design** — do not read
  that as stranding and do not "restore" them. Only the 6 files actually present in the repo are in
  scope for the bidirectional audit.

### The owner edits the live artifacts between runs — carry from the REMOTE, not from memory

On 2026-09-01, *after* the daily run finished, the owner pushed manual cleanup commits: 43 adult rows
removed from `events.csv` and 350 time-format duplicates removed. A run that carries a local base
predating those commits silently resurrects everything the owner just deleted, and the deletion looks
like it "didn't take" for reasons nobody can reproduce. At STEP 1, verify the local artifacts match
the remote by blob SHA-1 before trusting them as the carried base (they did on 2026-09-02). Check the
commit log for `Add files via upload` and hand-written dedup/removal messages — those are owner edits,
not pipeline output.

### A yield checker and its attribution map can drift apart (found 2026-09-02)

`deals_yield.py` classified `great_pumpkin_trail` as an in-season table contributor and reported
**0 rows, WARN** — for the fourth-ish run. The row was fine: The Great Pumpkin Trail existed in
`events`, `standing_deals.csv:98` carried its deal, and the overlay had stamped it correctly. What was
broken was only *attribution*: `deals_overlay.SOURCE_KEYS` maps a `source_url` fragment to a source
key, and it had no entry for `pumpkintrail.com`, so the row resolved to `"other"` and the yield check
counted zero. Fixed by adding `("pumpkintrail.com", "great_pumpkin_trail")` to `SOURCE_KEYS` in
`deals_overlay.py` and to the fallback tuple in `deal_provenance_restore.py`; warnings 1 → 0.

Three things generalise:

1. **Two registries name the same sources and nothing keeps them in sync.** `deals_yield.py` has a
   source→season/role registry; `deals_overlay.py` has a url-fragment→source map. A key present in the
   first and absent from the second warns forever. Diff them: every key `deals_yield` knows must be
   producible by `source_key()`. `ice_castles` and `marcus_kids_dream` are also unmappable but have no
   table rows at all and are out of season, so they report 0 correctly — which is exactly why this
   went unnoticed. **Audit by scanning `standing_deals.csv` for `source_url`s that `source_key()`
   sends to `"other"`** — that returned exactly one row and named the bug immediately.
2. **`"other"` is a silent bucket.** `deal_provenance_restore.py` skips any row that already carries a
   `deal_source`, so once a row is stamped `"other"` the mis-attribution is sticky across runs and
   re-running the pass cannot heal it. Clear `deal_source == "other"` before re-running, and treat a
   nonzero `"other"` count in the restore report as a defect to investigate rather than a residual.
3. **A permanent WARN is worse than no WARN** — the registry already says this, and this is the third
   instance. The failure was not that the check was wrong but that it had been *correct and ignored*.

### `standing_deals.csv` has no `source` column

Provenance is derived from `source_url` alone, via `SOURCE_KEYS`. Columns are exactly
`venue_match, deal_description, deal_expiry, source_url, verified_date`. Anything reaching for
`row["source"]` is reading a field that does not exist. This is why adding a deal row for a **new**
source requires touching `SOURCE_KEYS` too — adding the CSV row by itself creates an `"other"`.

### Adult filter: bar/brewery trivia needs a COMPOUND rule, not a keyword (added 2026-08-31)

Several adult-only titles were found **stale in the live app** and removed directly: estate
planning, dementia, member happy hour, a retirement party, a blood drive, and bar/brewery trivia.
Most became flat `DROP_PHRASES` (`estate planning`, `dementia`, `happy hour`, `retirement party`,
`blood drive`, `pub trivia`, `bar trivia`) — each essentially never names a kids event.

**Trivia is the one that must NOT be a flat keyword.** Libraries and state parks run all-ages
trivia — `Trivia Night with Trivia Mafia` @ Galaxie Library (All ages) and four State Park trivia
walks are real family KEEPs. So `_compound_drop()` drops such a title **only when it also carries
an alcohol word-boundary token**. The rule has two sides and they were completed on different
dates: the ACTIVITY side is `\b(trivia|bingo|karaoke)\b` **as of 2026-09-21** — it read `trivia`
alone until then, and the 17-row leak that gap allowed is recorded in the FOURTH-instance § below
— and the ALCOHOL side is, as of 2026-09-07,
`\b(beer|brewery|brewing|brewpub|brewhouse|taproom|distillery|pub|bar|cider|winery)\b`.
Word boundaries are load-bearing: `\bpub\b` must not fire inside "public", `\bbar\b` must not fire
inside "library"/"barn", and `\bpub\b` does not fire inside "brewpub" — which is why `brewpub` is
listed in its own right. This is title-only, so a bar-trivia row whose bar-ness lives only in the
*address* (e.g. `Tuesday Night Trivia` @ Wellington's Pub, `Trivia Night by The Power Loon`) won't
auto-catch — accepted, remove those by hand. Test suite is now **169 passed** (145 after the
2026-09-21 bingo/karaoke activity completion, 137 after the
2026-09-07 `brewing` completion, 131 after the 2026-09-01 hardening, 85 after the 2026-08-31 one,
70 before it); every new
DROP is a real stale title and every new KEEP (library trivia, `Brewery Oktoberfest` with no
"trivia", "Public Library") is a false positive a looser rule would have produced.

**The list carried `brewery` but not `brewing` until 2026-09-07, and the gap was invisible.** Two
real rows — `Smart Alex Trivia at Copper Trail Brewing` and `Intuit-To-Win-It Trivia at Intuition
Brewing` — could never fire the compound rule. Three things to carry: (1) **a vocabulary gap in a
safety filter looks exactly like a source that has nothing to catch** — no error, no warning, just
a quiet zero — so the token list has to be re-read against live titles rather than assumed
complete. (2) **Distinguish completing a rule's VOCABULARY from loosening its SHAPE.** Adding
`brewing` leaves the compound requirement and the title-only scope untouched, which makes it this
task's call; going title+address is a shape change and is the owner's. (3) **Measure the
false-positive surface BEFORE the edit, not after**: 13 dataset titles carry `\bbrewing\b` and
exactly the 2 trivia rows also carry `\btrivia\b`, so the change was provably zero-FP on real data.
The 4 new KEEP cases (`Live Music at 22 Northmen Brewing`, `Driftless Revelers at Bent Paddle
Brewing Company`, and two State Park trivia walks) are what pin that down for the next reader.

### Adult filter: the activity vocabulary was `trivia` ALONE — FOURTH instance of the class (found 2026-09-21)

STEP 8 verification found **17 live event rows across 7 titles** at bars, breweries and American
Legion posts sitting in a family guide, every existing guard having passed them: `Bar Bingo` ×6
(929 Beer House & Grill, progressive jackpots), `Karaoke with DJ Rhumpshaker` ×6 (No Name Bar —
its description reads literally **"9pm-1am Free | 21+"**), `Karaoke at Willy T's`, `Thirsty
Thursdays Karaoke at the New London Legion`, `Gun Bingo` (American Legion Post #167, a
$50/ticket **firearms raffle**), `Y Cares Black Tie Bingo` (a black-tie fundraiser gala) and
`Wild Cocktails` (a class on making alcoholic drinks).

This file already records the class three times — the `brewery`/`brewing` gap, the
`55+`-in-the-description gap, and bar-trivia-whose-bar-ness-is-in-the-address. **A vocabulary or
scope gap in a safety filter looks exactly like a source with nothing to catch: no error, no
warning, just a quiet zero.** `_compound_drop()` has been correct in *shape* since 2026-08-31
and its activity side was the single token `trivia`, so `Bar Bingo` — a title that carries an
alcohol token *and* an adult bar game, i.e. precisely what the compound rule was built for —
could never fire. What found it was what found Sovereign Grounds and the Peak Café group:
**reading live titles by hand.**

**The fix is in two halves, both measured on real titles BEFORE the edit** (`_measure_fp.py`),
per the 2026-09-07 rule:

1. **A VOCABULARY completion, not a SHAPE change** — `trivia` → `trivia|bingo|karaoke`. The
   alcohol co-occurrence requirement and the title-only scope are both untouched, which is what
   makes this the task's call rather than the owner's. Measured: **30** dataset titles carry
   `\bbingo\b`, exactly **6** also carry an alcohol token, and all 6 are the same real title, so
   net-new is 1 title / 6 rows with **provably zero false positives**; `karaoke` adds nothing on
   its own (13 titles, **0** with an alcohol token) and is included because the gap is the
   vocabulary, not the row count.
2. **Six PROPER NOUNS pinned in `DROP_PHRASES`**, for venues that declare their bar only in the
   DESCRIPTION — which a title-only rule can never reach. This is the `magnet senior center`
   precedent and it is deliberately **NOT** a widening of scope to descriptions, which was
   measured previously and produced a real false positive.

**THE LINE DRAWN IS AN EXPLICIT ADULT SIGNAL — an age gate, a bar or legion venue with
late-night hours, or an activity that IS alcohol — never venue vibe. `Plant Bingo` is why.** It
runs at Two Fathoms **BREWING** and its own description says *"we welcome all ages"*: a rule
keyed on the brewery would have deleted a real family event. Three titles are therefore
deliberately KEPT and recorded here as borderline, so the next reader does not "finish the job":
`Two Fathoms Karaoke Night` (same all-ages-welcoming brewery, no age gate — **atmosphere prose
is not evidence**), `Fun Friday: Music Bingo` at Minnesota Beer Co. (no alcohol token in the
TITLE, and the title-only scope is working as designed), and `Singo! Music + Bingo at the
Gambler` (bar venue, progressive jackpot, but free to play with no age statement — **a venue
name alone is not evidence**).

`test_adult_events_filter.py` **145 → 169 passed**, and **both halves were made to FAIL ON
PURPOSE** before the green was trusted: 3 fails when the activity regex is reverted to bare
`trivia`, 7 when the proper nouns are removed. Two smaller items worth carrying:

* **One test case legitimately failed on the first run, and it was a bad CASE, not a bad rule.**
  `Black Tie Family Gala` dropped on the long-standing `gala` phrase, so it never tested the
  "black tie" boundary it claimed to — it would have passed for years while asserting nothing.
  **Isolate the phrase under test**; replaced with `Black Tie Skate Night`.
* **`norm()` does not fold U+2019.** The live `Karaoke at Willy T's` title carries a curly
  apostrophe, so the DROP phrase stops before it (`karaoke at willy t`) and the suite pins
  *both* apostrophe forms. A phrase written with the ASCII apostrophe would have matched nothing
  and, per the class above, reported a quiet zero.

**Fixing this POST-STEP-7 costs a full cascade, and that cost is the argument for finding it
earlier.** `events` moved 5075 → 5058, which forced a second `build_guide.py`, a second STEP 5.5
(`end_date` 33, `added=0` on the warm pass — so none of the dropped rows carried one), a
re-stamped `_run_summary.json`, and a **verified rollback of today's 97 `error_log.csv` rows** to
the pre-STEP-7 baseline (md5 `c11e187656dea67b80c80f5ea17589d3`, byte-identity control passing
first) before `errlog_step7.py` could be re-run without double-appending.

### `end_date`: parsed from text, JSON-only, precision-first (added 2026-08-29)

Base44's Event entity carries an `end_date` and `dailyJsonImport` now reads `r.end_date`
(app-side Fix 4). Our source rows have **no** structured end date — only a single `date` — so
`end_date_pass.py` (folder root) parses it from each row's own title/description at **STEP 5.5**,
after `build_guide.py` and before publish. Four things that are easy to get wrong:

1. **It writes to `msp_family_guide.json` ONLY, never the CSVs.** `end_date` is deliberately kept
   out of `build_guide.py`'s `BASE`/`COLS` so the **21-column CSV contract is unchanged** — same
   discipline as `deal_source`/`is_seed`. `dailyJsonImport` reads the JSON, so that is the only
   place the value must reach. Because `build_guide.py:23` rebuilds rows from `BASE`, the pass
   MUST run *after* the build (on the feed JSON), not before — run it before and the value is
   destroyed at build.
2. **Only two self-anchored signals emit**, both keyed off the row's own start `date`: a bare
   `YYYY-MM-DD` in the text that is `> date` and `≤ 15 months` out, or a spelled
   `through|until|ends <Month> <Day>[, Year]` with a real numeric day. Everything else stays
   blank *on purpose*. `through winter` / `through end of September` / `through preschoolers` /
   `through late September` are the actual false positives in `test_end_date_pass.py` (20 cases,
   must pass) — do not loosen the rule to raise recall, because a wrong `end_date` claims an
   event is still running when it isn't (the STEP 1 roll-forward failure class).
3. **Dated categories only** (`events`, `meal_deals`, `volunteer_opportunities`); parks and
   restaurants are evergreen (their `date` is blanked at build).
4. **Idempotent**; never overwrites an existing `end_date`. Yield was ≈130 rows on the 2026-08-29
   feed (75 ISO-anchored + 58 spelled), **89 on 2026-09-05**, **74 on 2026-09-10** and **52 on
   2026-09-15** (51 events + 1 volunteer). A collapse
   to ~0 means a stale helper or a changed feed shape — investigate, don't ship a range-less feed.
   The continued slide 130 → 89 → 74 → 52 is the same feed-composition effect described just below,
   now further along: the window is deeper into weekly library programming, which is single-date
   by nature. The three checks were run again at 74 and all three agreed the helper is healthy.

   **That number is a property of the FEED, not of the helper, so do not read a decline as a
   defect before checking the helper (2026-09-05).** At 89, three independent signals said the
   pass was healthy: the helper was byte-identical to its committed copy, its 20-case suite
   passed, and a `--dry-run` reported `added=0 kept_existing=89`. What changed was the window's
   composition — September–October is dominated by weekly library programming, which is
   single-date by nature, where late August carried more multi-day festival rows whose own text
   spells out a range. Run those three checks (**blob SHA-1, pass-count, dry-run**) before
   touching anything; only if they disagree is it a stale helper. And never raise the number by
   loosening the two self-anchored signals — a wrong `end_date` claims an event is still running
   when it isn't.

### Feeds: diff the mandated source list against the fetcher's dispatch table

SKILL.md line 832 mandates the DECC Duluth feed. On 2026-08-29 `grep -ci decc` over the fetcher
returned **0** — the source had never been implemented. A mandated source that is *absent*
rather than *broken* raises no error and is invisible to every yield and coverage check, since
those only inspect sources they already know about. At STEP 2, diff the list of sources SKILL.md
mandates against what the fetcher actually dispatches; do not assume a named source is wired up.
DECC is WordPress REST, not iCal: `https://decc.org/wp-json/wp/v2/events?per_page=100`, dates as
`YYYYMMDD` in `event_start_date` (**not** ISO — reformat before the window test). It is now wired
as `run_decc()` in the root `fetch_feeds.py`. `featured_image_url` is the organizer's own photo
served by their own API, so it is a real `site_photo`, not a curated fallback.

**It happened again on 2026-09-07, and the missing source was the biggest one in the spec.** The
mandated Saint Paul Public Library calendar had no dispatch entry, so `sppl` had contributed **zero
rows on every run to date** while raising nothing. Wired on the BiblioCommons pattern
`rclreads` already uses — as a `BIBLIO` row dispatched by `run_biblio()`, **not** as a bespoke
`run_sppl()`; see the grep-target correction above, this file named a function that never existed:
1,801 events fetched, 14 branches joined, 21 cancelled-flag rows dropped,
**669 in-window** — the second-largest source after `hclib`, and essentially the whole of that run's
+519 events. Two corrections to how the DECC lesson was written: (1) **do the diff EVERY run, not
once** — one audit found DECC and stopped, and a second mandated source sat unwired for days after.
(2) **"expect almost nothing net-new" is a DECC property, not a rule.** DECC overlapped hand-found
festival rows; SPPL is a metro library system whose weekly programming nothing else carries, so it
was a 14% dataset increase. Judge a newly wired source by whether its rows are present and correctly
attributed — but do not use "low net-new is fine" to wave past a source that should be large.

**Expect DECC to add almost nothing net-new, and do not read that as a failure.** On 2026-08-30 it
returned 86 events, 17 in-window; 1 was dropped by the adult filter and 14 collapsed into richer
rows the guide already had from earlier hand discovery (Applepalooza, Duluth Oktoberfestival, Lake
Superior Harvest Festival, Gourd Days). That is the correct outcome: the point of wiring a
mandated source is converting a hand-discovered set into a structured one that catches new
postings automatically, not a one-run row-count bump. Judge a newly wired source by whether its
rows are *present and correctly attributed*, not by net additions.

Retired the other direction on 2026-08-30: **`winona_library` is out of `ICAL_FEEDS`.** It returned
403 on three consecutive runs and `event-source-calendars.md` §4 already listed it as a dead end,
but the fetcher kept dispatching it, so it logged an identical ERROR every run — the
permanent-warning failure mode. `visit_winona` (29 in-window) still covers the city. A registry
entry marking a source dead is only half the retirement; delete the dispatch too.

### A low-yield feed is usually the source's silence, not our parser (checked 2026-08-30)

> **RETRACTED IN PART, 2026-09-11 — the first two bullets were TRUNCATION, not silence.** The
> *method* below (read the raw `DTSTART`s) is still right; the conclusion drawn from it was wrong,
> because the raw values were themselves a truncated sample. `?ical=1` on The Events Calendar
> serializes **only the current list-view page**, so Dodge Nature and Bemidji were never quiet —
> we were reading one screen of their calendars. On the plugin's WP REST endpoint they return
> **57** and **26** in-window events, not 1 and 1. See `event-source-calendars.md` §1.1. Keep this
> section for its method and for the `visit_faribault` 503 rule; **do not cite its Dodge/Bemidji
> conclusions.** What survives is stronger than what it replaces: *a content-gap verdict is only as
> good as the completeness of the fetch it rests on, so establish that the fetch is complete before
> concluding the source is silent* — and note that a truncated feed is MORE stable run-over-run
> than real content, so stability is not evidence of correctness.

Before "fixing" a feed that returned 1 or 2 rows, read its **raw** `DTSTART` values and count them
by month. Three of this run's low yields were all source-side:

* **`dodge_nature`** returned 49 VEVENTs, 1 in-window: 17 dated 2026-07, 32 dated 2026-08, and
  **zero in September or later**. Dodge Nature Center has simply published nothing past August. It
  is a mandated seed venue, so the guide carries one Dodge event for the whole window — worth
  re-probing each run, but there is no parse bug to chase.
* **`visit_bemidji`** has shrunk to 11 `DTSTART`s scattered across 2025-03 to 2027-11 — annual
  placeholders, 1 in-window, against 15 recorded on 2026-08-19.
* **`visit_faribault`** returned its first-ever 503. One 503 is not a dead end; re-probe before
  retiring it (three consecutive failures is the `winona_library` bar).

The distinction matters because the two diagnoses lead opposite ways: a parse failure is ours to
fix, while a content gap should be recorded and re-probed, and "fixing" it means inventing rows.

**There is a THIRD diagnosis, and it hides behind a healthy-looking number: the source truncated us
(found 2026-09-09).** `washco_libcal` and `dakota_libcal` each returned **exactly 500 VEVENTs** —
and exactly-500 is the tell — with spans ending `2026-10-09` and `2026-10-16`, both **before**
`END_DATE=2026-10-31`. They contributed 257 and 318 in-window rows, which are large, healthy yields
that no low-yield check would ever flag. But the cap bites *inside the window*, so every event those
two systems publish in the last three weeks of October is structurally invisible, and the feed
silently understates two of the larger metro library systems. They are logged `CAPPED` rather than
`OK`, and the two `ical_feed_pull` rows are `warning`, not `info`.

Two things to carry. **A round number at the boundary of a limit is a truncation signal, not a
yield** — check the returned span's END against `END_DATE` for every iCal source, because a feed
that sorts ascending from ~4 weeks in the past spends its cap on the past before it reaches the
window's tail. And this is a **content gap in the recording sense but a fetch defect in the remedy
sense**: unlike Dodge Nature (which has genuinely published nothing) the events exist and we are
failing to ask for them, so the fix is a date-bounded endpoint or paging, and it is the one case in
this section where "there is no parse bug to chase" would be the wrong conclusion.

**GENERALISED 2026-09-11 — and the Dodge Nature contrast drawn just above turned out to be
BACKWARDS.** That sentence held Dodge up as the honest-silence case against the LibCal truncation
case. Dodge was truncated too; it just truncated to a number too small and unround to look like a
cap. So **the round-number tell is the weaker half of the signal and it was doing most of the
work.** The reliable half is the **span**: `span_status(count, span_end, ceiling_hit=False)` in
`fetch_feeds.py` returns

* `CAPPED` — a page/ceiling hit, or a round count (30/50/100/500/1000) whose span ends short;
* `SHORT` — any span ending **more than 6 days** before `END_DATE`, round count or not;
* `OK` — otherwise, including a span that reaches or passes `END_DATE`, and **0 events**, because
  an empty feed is not a truncated one.

The 6-day margin exists so an ordinary quiet tail is not a permanent WARN — the failure mode this
file already names twice. It caught `visit_bemidji` at **11 events**, a cap that is not round at
all, and `krls` at 17, which had been reading as a silent `OK`. Every source now logs its status
with its span, and `CAPPED`/`SHORT` rows are `warning`, not `info`.

Two corrections to how the rule above was written: (1) **check the span for EVERY source, not just
iCal ones** — the same truncation arrives through REST pagination; (2) **"low yield" and
"truncated" are not alternatives to be chosen between.** They present identically and the only way
to tell them apart is to ask a date-bounded endpoint and compare. Pinned by `test_tribe_rest.py`
(**41 passed**), whose span cases are this run's own measured counts.

**FOURTH INSTANCE, 2026-09-12 — a WordPress "My Calendar" ICS export is MONTH-SCOPED, and the
span detector is what found it.** `krls` was the source `span_status` flagged `SHORT` last run
(17 VEVENTs ending 2026-09-24 against `END_DATE=2026-10-31`) and the diagnosis was taken no
further. It was not a quiet outstate library system: the bare `/feed/my-calendar-ics/` path
serves **only the current month**. Fetched month by month it returns 33 VEVENTs and **16
in-window** against the previous 6, span 2026-09-01..2026-11-19, and it now logs `OK` honestly
rather than `SHORT`. Handling is `month_urls()` + `MONTH_LOOP_ICAL` in `fetch_feeds.py`; the
mechanics and the four ways it fails silently are in `event-source-calendars.md` §1.2. Four
things to carry, none of them about this source:

1. **The `month` argument is a START, not an interval — so fetch ONE MONTH PAST `END_DATE`.**
   `month=10` came back spanning 09-25..10-17 while the 2026-10-30 Park Rapids storytime appeared
   **only** under `month=11`. Stopping at END's own month leaves a hole in exactly the tail the
   export was already truncating, which would have looked like a successful fix.
2. **De-duplicate overlapping month fetches on `(UID, DTSTART)`, never on `UID` alone.** A weekly
   series shares one UID across every occurrence, so a UID-only key collapses a weekly program to
   a single row — the `_dedup4_0822` defect reached through the *fetcher* instead of through a
   dedup pass, and it would have been invisible to the weekly-series health check because the rows
   would never have existed to be counted.
3. **This is the second source in two runs where the span was the only signal.** The in-window
   count was 6 — unremarkable, not round, nowhere near a limit — so no count-based check could
   ever have fired. That is the argument for the span half of the detector made again on
   independent data, and it is why `SHORT` must be **investigated**, not merely logged: last run
   correctly flagged `krls` and the flag sat there for a day.
4. **A truncated feed is MORE stable run-over-run than real content**, because the same fixed
   slice is being re-read. The `?ical=1` retraction above already says this; four instances in,
   treat run-over-run stability in a small feed as mildly *suspicious* rather than reassuring.

**Negative result from the same run, recorded so it is not re-probed: LibCal
`ical_subscribe.php` accepts NO date bounds.** `washco_libcal` (500 VEVENTs, span ends
2026-10-09) and `dakota_libcal` (500, ends 2026-10-16) are still `CAPPED` inside the window. The
natural move after the KRLS fix is to look for the same trick — a query parameter that shifts the
served range — and there isn't one: `start`, `start_date`, `date`, `from`, `days` and `cal_date`
were each probed and returned **byte-identical** 500-VEVENT responses, i.e. accepted and ignored,
which is the same shape as the BiblioCommons `startDate`/`endDate` behaviour this file already
documents. So the remedy differs by platform even within one truncation class: KRLS needed a loop
over an existing parameter, while LibCal needs a **different endpoint or real paging**. Both stay
`warning` until then. **Comparing the bytes is what makes this a finding rather than a guess** —
a parameter that is ignored looks exactly like a parameter that worked if you only read the row
count.

### Tag library rows at compile, not later

Rows from LibCal and BiblioCommons arrive with venue plumbing only — 1,898 of them on
2026-08-29 carried no `library` tag and nothing describing what the event *is*. The image
chooser matches on content tags, so with venue tags alone it has nothing to work with; that is
the state that once paired a bilingual storytime with a fire-truck photo. Tag during the STEP 3
compile — this is `tagify()` in `compile_step3.py` (2,074 rows tagged on 2026-08-30): the
source-derived `library` tag for every LibCal/BiblioCommons source, plus
title/description rules (story-time, baby, toddler, teen, stem, crafts, music, reading, games,
bilingual, movie, outdoors, animals, play, sensory, food, skating, farmers-market).

### STEP 4.5 is IN the chain now, and its absence is a HARD FAILURE (added 2026-09-13)

For weeks the nightly never ran STEP 4.5. Diagnosis (`project_step45_ogimage_capture_broken.md`):
the step works when invoked — the corrected gate keys on `image_source` and yields 4,791 eligible
rows, and a manual run on 2026-09-10 landed 13 of 40 upgrades — but **this file's documented image
chain ran `4.3 → 4.35 → 4.8 → 4.9` and never named 4.5**, so the nightly, which treats CLAUDE.md as
the running order, skipped it every night. Nothing warned, because a skipped step raises nothing.
This is the *exact* failure class as the six-run `ical_feed_pull` lapse and the `run_summary` lapse:
**a mandated action that produces no error when absent is invisible.** SKILL.md:1171 mandated 4.5 the
whole time; a mandate is not self-enforcing.

The chain is therefore now, explicitly, **`4.3 → 4.35 → 4.5 → 4.8 → 4.9`**. STEP 4.5 is the
`og:image` + body/hero `site_photo` backfill: for every row whose `image_source` is
`curated_category`/`stock`/`openverse_named`/blank AND that carries a `website`, WebFetch the page
and take the largest non-logo body/hero `<img>` as a real `site_photo`. It shares SKILL.md's single
20-minute enrichment budget (`ENRICH_DEADLINE`) with 4.6–4.8, so on a cold cache 4.8 can starve it —
which is why the marker below records *why* it stopped.

**The enforcement is the point, and it is the `ical_feed_pull` / `run_summary` pattern.** STEP 4.5
must write `_image_backfill.json` at the folder root — a run-scoped marker, shaped like:

```json
{"item": "site_photo_pass", "attempted": 812, "upgraded": 41,
 "stop_reason": "completed", "description": "…one line naming counts and why it stopped…"}
```

`stop_reason` is `"completed"` (the eligible set was exhausted) or `"deadline"` (the 20-min budget
hit first). `errlog_step7.py` now:

1. **asserts the marker EXISTS**, in section 0 **before any append**, so a *skipped* 4.5 — the whole
   point of the guard — leaves `error_log.csv` untouched (the 2026-09-13 partial-write lesson);
2. **asserts it is FRESH** (mtime ≥ `_feedpull_all.json`), so yesterday's marker cannot pose as
   today's — the same stale-input hazard as `_findings.json` / `_run_summary.json`;
3. **asserts `stop_reason` is one of the two legal values**, so a budget-starved pass is
   distinguishable from a converged one *and* from a skip — otherwise the fix just moves the silent
   failure one level down;
4. **appends one `image_backfill` row** (info when `completed`, warning when `deadline`) and asserts
   in section 5 that exactly one exists and is non-empty.

Three things to carry. **`image_backfill` is now a RESERVED `issue_type`** alongside
`ical_feed_pull`, `deal_source_*` and `run_summary`; per the 2026-09-13 prefix-collision finding,
name any *check* of it `<thing>_check`, never `image_backfill*`, or the check enrolls itself in the
assertion. **Add `_image_backfill.json` to the STEP 1 run-scoped-freshness audit** next to
`_findings.json` and `_run_summary.json`. And **the guard was proven to FAIL on absence before it was
trusted to pass** — the same discipline every new guard in this file gets: a hard failure that has
never been seen to fail is just an assertion you hope is wired up.

### STEP 4.5 now has a HELPER, and the guard's first live run exposed three things (2026-09-14)

The 2026-09-13 section wired the *guard*; there was still no helper, so the first run under the guard
had to build one. It is **`step45_site_photo.py`** (folder root, undated, `MSP_RUNDIR`-resolved,
`--select N | --dnr | --apply`). First completed 4.5 in the project's history: **36 sites resolved,
205 rows** moved off a generic category image (events 191, volunteer 14), `site_photo` 949 → 1154.
Four findings, none of which is about photographs.

**1. A dead route is not a retry case — `/state_parks/` URLs are JavaScript redirect stubs.** Every
MN DNR park page returned effectively nothing to WebFetch, which reads as "this source has no usable
image" and invites re-probing it forever. The page body is written by a client-side redirect WebFetch
cannot follow, so no number of attempts would have changed the answer. The remedy was a **different
route**: the DNR calendar API already carries a `location_tag` per event, and that resolves
deterministically to the park's banner image. 25 of the 36 sites came from this path, and every
banner was **byte-checked as a real JPEG** before being accepted — a deterministic path that
verifies is still a claim until the bytes are read. `dnr_banner_map()` holds it. Note the near-miss:
the API's own `image` field 404s, and taking it on faith would have stamped 25 broken URLs into the
feed. Logged `dnr_js_redirect_stub` and `dnr_image_field_404`.

**2. Two routes in one pass means the marker's PROSE must name both.** The first description said
4.5 "fetched 36 venue pages". False for 25 of them, which were never fetched at all. Nothing in the
pipeline would ever have contradicted it — this file's own rule is that **prose is unasserted by
construction**, and a method claim is exactly the kind of prose that later gets cited as evidence
about how a number was produced. The description now names both routes explicitly. Generalising: a
marker describes a *method* as well as a count, and only the count has a guard.

**3. The pass had a latent idempotence defect that would have turned success into a permanent false
zero.** `do_apply()` originally counted only rows still inside `GATE`. But applying the photo moves
a row's `image_source` to `site_photo`, i.e. **out of** `GATE` — so a warm re-run finds nothing
eligible, reports `upgraded: 0`, and **overwrites the marker with that zero**. The guard built
yesterday to prove 4.5 ran would then have been carrying a passing assertion that 4.5 did nothing.
Fixed with a `warm` counter: a row already carrying *this pass's* photo still counts, so a warm
re-run reproduces the cold result (verified: 205 again, dataset byte-identical). The standard is the
one `closure_filter.py` and `entity_fix.py` already meet — but note the new twist: **a
non-idempotent pass that WRITES A MARKER is worse than a non-idempotent pass, because the second run
does not merely no-op, it retracts the first run's evidence.** Any future pass that reports into a
marker must be checked for this specific shape. Logged `backfill_idempotence_defect`.

**4. Both guards were made to FAIL ON PURPOSE in a scratch `MSP_RUNDIR`** (missing marker, stale
marker), and the load-bearing detail is that **neither failure wrote a marker** — so a failed 4.5
cannot leave a file behind that poses as success on the next run's freshness check. Logged
`backfill_guards_fail_on_purpose`.

### A marker's METADATA can be stale while the marker FILE is fresh (found 2026-09-15)

The 2026-09-13 guard asserts `_image_backfill.json` **exists**, is **newer than `_feedpull_all.json`**,
and carries a **legal `stop_reason`**. All three passed this run and all three would have passed on a
false claim. `step45_site_photo.do_dnr()` merges into an existing `_step45_results.json` and
**preserves its `__meta__` across runs**, and `do_apply()` reads `stop_reason` out of that `__meta__`
— so today's marker inherits **yesterday's verdict about why 4.5 stopped**. Yesterday's `__meta__`
held `{'stop_reason': 'deadline'}`; today's would have been stamped `deadline` whether or not today's
pass converged.

This is the stale-input hazard reaching a guard the hazard was written to close, through a door the
guard cannot see: **the freshness check tests the FILE's mtime, and the file is genuinely fresh — it
is one FIELD inside it that is carried.** Content-freshness and mtime-freshness were adopted on
2026-09-09 precisely because they fail independently; this is a third mode neither covers. Three
things to carry:

1. **A pass that merges its own prior output must decide, per field, what carries and what resets.**
   The website→photo map *should* carry (it is a cache, and re-fetching it would spend the budget
   rediscovering what is on disk — the `geo0826.py` lesson). `stop_reason`, `run_date` and any count
   describe **one run** and must be re-stamped or cleared. The durable fix is for `do_dnr()` to reset
   `__meta__` rather than merge it; mitigated this run by stamping `stop_reason`, `routes`,
   `run_date` and `fetched_this_run` explicitly at merge time.
2. **`run_date` inside a run-scoped marker is now the cheap tell.** A marker whose own `run_date`
   disagrees with `argv[1]` is stale no matter what its mtime says. Worth asserting next run —
   it is the `_findings.json` `run_date_verified` content check applied one level in.
3. This is the **fourth** instance of the same shape (`_errlog_NNNN` literals → `_findings.json` /
   `_run_summary.json` inputs → `__meta__` fields). The generalisation is now: **anything a run
   inherits under a stable name is stale until something proves otherwise, and "something" must be
   an assertion, not a habit.**

**CLOSED 2026-09-16 — and the FIRST cut of the fix was worse than the defect, which is the part
worth keeping.** The durable fix is in two halves that are worthless apart: `do_apply()` hard-fails
unless `__meta__.run_date == MSP_TODAY` and stamps `run_date` into `_image_backfill.json`, and
`errlog_step7.py` asserts that marker's `run_date` equals its own `argv[1]` — the cheap tell
nominated above, now wired. Both halves were made to FAIL ON PURPOSE before being trusted (missing
`__meta__`, stale `run_date`, unset `MSP_TODAY`, and a scratch marker stamped `2026-09-15`); each
exits 1, **writes no marker**, and the `errlog` half fires in **section 0 before `open(LOG,"a")`,
with `error_log.csv` md5-identical afterwards** — the partial-write discipline from 2026-09-13.

The overcorrection: `do_dnr()` first dropped `__meta__` **unconditionally**. That closes stale
inheritance and opens something worse — it also destroys a **fresh** `__meta__` that this run's own
WebFetch phase just wrote, so `--dnr` after the fetch phase deletes the run's metadata and
`do_apply()` then hard-fails. Observed live, minutes after the "fix". It made phase ORDER silently
load-bearing and undocumented, which is exactly the obey-it-perfectly-forever rule this project
keeps proving worthless. **The drop is now conditional on the value's OWN `run_date`** — yesterday's
goes, today's survives, and the phases commute again. Generalising: *when the remedy for a stale
inherited value is to delete it, the deletion needs the same freshness test the inheritance did*, or
you have replaced a silent wrong value with a silent missing one.

### A DEAD source can return HTTP 200 — read the BODY, never the status (found 2026-09-16)

`larl` (Lake Agassiz Regional Library, northwest MN) answers **HTTP 200** and is completely dead: the
domain is **parked**, and the 200 carries a Google domain-registrar page body. Every liveness check
this project has tests a status code or a row count, so a parked domain passes the first and returns
a quiet zero to the second — the two signals that would normally disagree both read "fine".

This is the silent-failure class arriving through the **transport layer**, and it is the inverse of
the `winona_library` 403: an honest error status got that source retired in three runs, while a 200
could have kept this one dispatched indefinitely. Two things to carry. **A source verdict requires
reading the response BODY** — the `<title>`, a byte count, anything content-shaped — because the
status line is the one part of a dead host that still works. And **a parked domain is a permanent
dead end, not a retry case**, like the DNR `/state_parks/` JavaScript stubs: no number of attempts
changes the answer, so it is recorded in `event-source-calendars.md` with the reason rather than left
to be re-probed cold next run.

### A 500-row cap is per-CALENDAR, so a capped LibCal can sometimes be FANNED OUT (found 2026-09-16)

`washco_libcal` has been logged `CAPPED` since 2026-09-09 — exactly 500 VEVENTs, span ending inside
the window — and the 2026-09-12 negative result established that `ical_subscribe.php` accepts no date
bounds (six parameters probed, all byte-identical responses). Both findings are correct, and together
they read as a dead end. They are not: Washington County exposes **Stillwater and Bayport as separate
calendar ids**, and dispatching those two directly added **103 in-window rows** (72 + 31) that the
capped county feed structurally could not reach. Both sub-feeds report `OK` with spans reaching 2027,
so they are not themselves truncated.

The rule: **the cap is per calendar, not per system.** So when a source is capped and accepts no date
bounds, the next question is not "is there another parameter" but "does this system expose
sub-calendars I can ask separately" — a different axis entirely, and the one that worked. Note the
shape this shares with the KRLS month-loop (2026-09-12) and the DNR `location_tag` route (2026-09-14):
in all three the remedy was **a different route to the same data**, never a retry of the blocked one.
Note also what it does NOT fix — `dakota_libcal` is still capped and has no sub-calendars to split,
so it stays a `warning` and the honest answer there remains a date-bounded endpoint or real paging.

### A FIXED `END_DATE` makes coverage counts drift upward all month (found 2026-09-16)

`mn_coverage` returned **57** warnings against the previous run's uncapped **46**. The cause was
diffed rather than assumed, and the two cheap checks that would normally explain a coverage move both
came back clean: **0 merges** this run (so it is not the 2026-09-14 `coverage_threshold_crossed_by_merge`
class) and **zero fetch errors** across 30 sources (so it is not a dead feed).

It is the window itself. The front advances every day while `END_DATE` stays pinned at the last day of
next month, so the window **shrinks by one day per run** with no compensating tail growth — 46 days
today against 47 yesterday. 19 of the 57 cities are short by **exactly 1**, and 33 are outstate cities
with zero events either way. Expect this number to keep climbing daily until the window rolls to
November, at which point it drops sharply. **It is a property of the window definition, not a
regression**, and it is the count-only-tripwire lesson in its third form: the first taught that a flat
count can hide rot, the second that an alarming count can be a logging cap, and this one that a moving
count can be the *measurement window* moving rather than the data. Before investigating a coverage
change, check what the window did.

**The prediction in that paragraph was too strong, and a FLAT reading proved it (2026-09-17).** It
says to expect the number "to keep climbing daily until the window rolls to November." It came back
**57 against 57** — identical, with identical sub-counts (19 cities short by exactly 1, 33 zero-event)
— while the window did shrink on schedule (46 → 45 days) and `events` fell 5,372 → 5,252. Both cheap
alternatives were ruled out first, in the order the 2026-09-16 entry prescribes: **0 merges** this run
(so not the `coverage_threshold_crossed_by_merge` class) and **0 fetch errors** across 30 dispatched
sources (so not a dead feed). The refinement: shrinking the window removes events, but a city only
changes state when its count crosses an *integer tier floor*, so the drift is **real over a month and
lumpy day to day**. **A flat reading is therefore not evidence the drift stopped, and a one-day jump
is not evidence of a regression** — which makes this a fourth form of the count-only-tripwire lesson:
a count can be flat *because the quantity is quantized*, not because the underlying pressure eased.
Compare across several runs before reading anything into a single delta.

### A byte-identity control over `_compiled_work.json` is INVALID (found 2026-09-17)

`step8_venue_repair.py` reported **+0 rows merged** — the documented goal state — while the file
shrank **6,468,292 → 6,454,074 bytes (−14,218)**. A 14 KB drop next to a "nothing changed" report is
exactly the shape this file tells you to investigate, and investigating it was right; the conclusion
was that the *control* was wrong, not the pass.

A **parsed** diff showed **0 rows and 0 top-level keys differing**. The bytes differ because the two
helpers disagree about JSON escaping: `geocode_pass.py` writes `ensure_ascii=True` (non-ASCII becomes
a 6-byte `\uXXXX` escape) and `step8_venue_repair.py` writes `ensure_ascii=False` (the same character
becomes its UTF-8 bytes). Pre-file: 4,400 `\u` escapes, 0 non-ASCII bytes. Post-file: 0 escapes,
12,182 non-ASCII bytes. **26,400 − 12,182 = 14,218**, the delta exactly.

Three things to carry. **Blob SHA-1 identity is the right control for a PUBLISHED artifact and the
wrong one for an intermediate**, because the published CSVs are written by one writer with fixed
settings while `_compiled_work.json` is rewritten by a dozen helpers that have never agreed on
serialization options. Compare an intermediate **parsed** — row count, per-row field diff, top-level
keys. **A byte delta that resolves to an exact arithmetic identity is a serialization artifact, not a
data change**; reproducing the number (26,400 − 12,182) is what turns "probably encoding" into a
finding. And note the near-miss in the *other* direction: had the two helpers happened to agree on
`ensure_ascii`, this control would have read SAME and been trusted — a control that passes for the
wrong reason is the `>/dev/null 2>&1 &&` failure reached through the data instead of the shell.

### A blank `price_type` reached the BUILD, and no guard saw it (found 2026-09-17)

**37 rows arrived at the first `build_guide.py` carrying a blank `price_type`** — not one of the
schema-v3.1 enum values (`Free | Paid | Varies`), and the carried base preserves a blank forever. It
was caught by *reading the built CSV's value distribution by hand*, not by any check. `pricetype_fix.py`
resolved it conservatively (36 → `Varies`, 1 → `Paid` on a quoted `$4`), which then forced a **rebuild**
— and because `build_guide.py` rebuilds rows from `BASE` and destroys `end_date`, **`end_date_pass.py`
had to be re-run** (43 restored). Final distribution: Paid 818 / Varies 4,080 / Free 2,081, zero blanks.

This is the 2026-09-16 `FREE_SRC` finding's neighbour, but the defect is different and worse: that one
is a *rule that cannot reach its rows*, this one is *a schema violation with no assertion at all*. The
pipeline asserts row counts, column counts, CRLF integrity, marker counts and registry agreement —
and does not assert that a closed-enum field holds a legal value. **An enum with no assertion is a
free-text field wearing a schema's clothes.** The durable fix is a build-time assertion over every
closed enum in `BASE`, failing the build rather than publishing the blank; until it exists, read the
distribution of `price_type` off the built CSV every run, and remember the rebuild ordering —
**any post-build fix that forces a rebuild must re-run STEP 5.5**, or the feed ships range-less.

### STEP 4.5: the rejection record lived only in `__meta__`, which the staleness fix now deletes (found 2026-09-17)

The 2026-09-15 finding requires STEP 4.5 to **record REJECTED candidates with reasons** next to the
accepted ones — that is what keeps the carried website→photo map trustworthy. The 2026-09-16 fix made
`do_dnr()` drop a `__meta__` whose own `run_date` is stale. Both are correct, and together they are a
defect: **the rejection list was stored inside `__meta__`, so the staleness fix silently destroys the
very record the trust rule depends on** — and destroys it on the *next* run, so the run that writes a
rejection never sees it disappear. Fixed in-run by persisting rejections outside `__meta__`, under a
key that carries deliberately (it is a cache of "do not re-fetch this", the `geo0826.py` argument).

The generalisation is about where two correct rules meet: **a freshness rule and a persistence rule
disagree about every field they both touch, and nothing forces them to be reconciled.** The 2026-09-15
entry already says a merging pass "must decide, per field, what carries and what resets" — this is that
sentence failing because a *later* field was added to the merged blob without the decision being made
for it. So: when adding a key to any structure a run inherits, state in the same edit which of the two
it is. A second, smaller item from the same helper: **`--dnr` requires `MSP_END`** to be exported,
because `dnr_banner_map()` imports `fetch_feeds`, whose module-level window read raises when it is
absent. That is the delete-the-date-literal rule working as designed — the crash is the feature — but
it means the three 4.5 phases are not independently invokable without the STEP 1 exports in the
environment. Export both for all three.

### STEP 4.5: `do_select` consulted the row gate and NOTHING ELSE, so it re-bought answers it owned (found 2026-09-18)

Every 4.5 finding so far has been about judging a candidate *well* — reject licensed stock, reject an
aggregator banner, reject a rotating slideshow, byte-check what you accept. This one is about which
candidates are offered at all, and it was wasting most of the budget those rules exist to spend.
`do_select` ranked sites purely by row count and consulted only the row `GATE`. It never opened
`_step45_results.json`. So **26 of one selection of 40 were sites the cache had already answered —
22 of them recorded as `None`** — and the 20-minute `ENRICH_DEADLINE` went on re-deriving what was
already on disk. `load_seen()` now ranks unseen sites first; the post-fix re-select reported
`0 already cached`.

Three things to carry.

1. **This is the `geo0826.py` failure with the cache present and simply unread.** There the helper
   looked for `_geocache.json` one level too high and would have re-queried Nominatim for 2,261
   cached addresses at ~1 req/s — the whole budget spent rediscovering what was on disk, with no
   error. Same outcome, different door: the file was found, parsed, and used for *writing* results
   while never being consulted for *choosing* work. A cache that is written but not read is
   indistinguishable, from the outside, from no cache at all — and it costs more, because it looks
   like diligence.
2. **Deprioritise, never exclude — and the distinction is load-bearing, not a nicety.** A site with
   no photo today may publish one next month, so hard-excluding a recorded miss rebuilds the one-way
   `curated_category` ratchet that `image_upgrades.py` had to be rescued from. The sort key is
   `(seen, -rows, site)`: unseen first, and a seen site still reachable once the unseen ones run out.
   The **rejection ledger is the opposite call and the difference is the reason** — a ledger entry
   says *this page will never yield a valid photo* (a JS stub, a stock CDN, an umbrella banner),
   which is a property of the page, while `None` says *no photo found today*, which is a property of
   the moment. Excluding on the first is correct; excluding on the second is the ratchet.
3. **A pass whose budget is time, not rows, has a SELECTION defect class all of its own**, and no
   count-based check can see it. Attempted, upgraded and rejected all looked healthy; the marker's
   `stop_reason: deadline` looked like honest budget pressure rather than self-inflicted waste. It
   surfaced only by cross-referencing the selection list against the results file by hand. Any future
   deadline-bounded pass should be asked the same question: *does it know what it already knows?*

### A helper with module-level side effects makes `import` a WRITE operation (found 2026-09-18)

`import pricetype_fix as P`, to read one constant, **executed the entire pass** against
`_compiled_work.json` — 410 blanks stamped `Varies`, 1 stamped `Paid`. The module does its work at
import time rather than under `if __name__ == "__main__":`. The outcome happened to be the correct
one (the fix was needed and was verified to have landed), which is luck, not a defence.

It also raised `TypeError: object of type 're.Pattern' has no len()` — **`FREE_SRC` is a compiled
regex, not a set**, so the section below describing it as a key set was wrong about its type while
being right about its reach. Both corrections stand.

This is the exact INVERSE of the 2026-09-15 finding that a helper whose argv is optional "fails as a
silent no-op": there, a helper invoked bare did nothing and exited 0 calling it success; here, a
helper merely *imported* did everything. **The two failures bracket the same missing discipline — a
helper must have exactly one way to be run, and inspecting it must not be that way.** Until the owner
guards these behind `__main__`, never `import` a pipeline helper to read a constant: `grep` it, or
parse the file with `ast`. Note how cheap the wrong move looks — reading a constant is the most
harmless-seeming thing one can do to a module.

### Two of my OWN probes under-read their data in one run (found 2026-09-18)

CLAUDE.md already records this class for the `LIBRARY_SRC` bracket-depth scanner, and the remedy
there was structural (an `ast` scan). The class is not confined to committed helpers — it is at its
most dangerous in the throwaway probes written to *check* the pipeline, because those carry no tests
and are trusted immediately.

* The coverage probe keyed on `expected` / `found` and the tier string `'core_metro'`. The real keys
  are `events` / `target` / `shortfall` and the tier is **`'core metro'` — with a space**. It
  reported *"0 core-metro shortfalls"* while the very first warning in the list it had just iterated
  was `{'city': 'Coon Rapids', 'events': 7, 'target': 8, 'tier': 'core metro'}`.
* A helper-structure probe missed a feature because it was spelled differently than assumed — the
  `run_sppl` / `sppl` lesson, recurring.

**What caught the first one was not the number but its SHAPE**: the probe claimed 53 of 53 warnings
were zero-event cities, and a distribution that degenerate is implausible on real data. That is the
only general defence available, since a probe reading the wrong key returns a clean-looking answer
rather than an error. So: **`.get()` on a dict you did not build is a silent `None`, and a filter
over silent `None`s returns a confident zero.** Assert the key set before trusting the loop, prefer
`[d[k] for k in ...]` over `.get()` in a probe, and treat any degenerate distribution — all-zero,
all-one, 53-of-53 — as a bug in the probe until proven otherwise.

### Do not RECONSTRUCT a helper's key in a probe — import it and CALL it (found 2026-09-21)

The 2026-09-18 entry ends at "assert the key set before trusting the loop." That is not enough,
and this run shows why. Measuring the false-positive surface of the `na()` spelled-state strip
(the discipline the 2026-09-07 `brewing` finding mandates: *measure before the edit*), my probe
rebuilt `dupsweep`'s bucket key **by hand** and omitted `ntime()`, which `dupsweep` applies as a
deliberate **separator** — two sessions of one storytime at 10am and 2pm are genuinely two rows.
It reported **131 net-new collisions**. The real number, measured with `dupsweep`'s own key
function, is **2**.

A probe that reconstructs a helper's key is not measuring the helper; it is measuring a second,
unreviewed implementation of it, and every divergence reads as a finding about the data. **The
remedy is sharper than the 2026-09-18 one: import the helper and call its key function.** Note
the apparent conflict with the 2026-09-18 rule that importing a pipeline helper can be a *write*
— both hold, and the reconciliation is the condition, not the verb: import is safe exactly when
the module has no import-time side effects (`dupsweep` does not; `pricetype_fix` does). Check
before importing, and never reconstruct as a way of avoiding the check.

**What caught it was the SHAPE, not the number** — the output listed pairs with *identical*
addresses that `dupsweep` had just run over without merging, which is impossible if the key were
the same key. The 2026-09-18 heuristic ("treat any degenerate or implausible distribution as a
bug in the probe until proven otherwise") is the only general defence here, because a probe
reading the wrong key returns a clean-looking answer rather than an error.

Two smaller probe traps from the same run, both of which cost more to diagnose than one line of
`print(type(obj), list(obj)[0])` would have cost to prevent. **`_findings.json` is a list of
LISTS**, contract `[severity, category, step, issue_type, item, description]`; `r["issue_type"]`
raises, which is the *lucky* shape, while `r[3]` against a differently-ordered row would return a
neighbouring column silently — so the `_add_*.py` helpers all assert `len(r) >= 4` before
indexing and a probe should too. And **`msp_family_guide.json` has no
`window_start`/`window_end`** — a header probe asking for them printed `window=None..None`, which
reads exactly like a build that failed to stamp the window; the real key is a single `date_range`
string and it was correct all along. A `.get()` miss on the **header** is worse than one on a row,
because the 2026-09-08 finding makes the header the one thing no row-level check can see, so a
false alarm there costs a real investigation.

### A fail-on-purpose run must check WHICH cases go red, not that the COUNT moved (found 2026-09-21)

This file has required new guards to be made to fail on purpose since 2026-09-08, and the
requirement has quietly been under-specified the whole time: *some* tests going red was taken as
proof the right ones did. Two cases this run show that inference is unsound, in opposite
directions.

* **Three `NA_DIFFER` cases written to pin the new trailing-only Minnesota strip passed under an
  OVER-BROAD mutant too.** They differed because of a surviving `university of` prefix, not
  because of the Minnesota token — so they were green for a reason that had nothing to do with
  what they claimed to test, and would have stayed green through exactly the regression they
  existed to catch. Replaced with `('Minnesota Zoo, Apple Valley', 'Zoo, Apple Valley')`,
  verified RED under the mutant.
* **`sports_dedup`'s guard-1 mutation goes red in the cases that were NOT written for it.**
  Removing the `_src` test promotes every row to anchor, and anchors skip each other, so the five
  MERGE cases go red while the `noanchor` KEEP case — the one written to pin guard 1 — stays
  green. The count moved convincingly; the pinning case did not.

Same shape as this run's `Black Tie Family Gala` test case, which dropped on the long-standing
`gala` phrase and so never tested the "black tie" boundary it named. **Isolate the thing under
test, and on a fail-on-purpose run read the list of failing case names against the list you
predicted** — a count is a summary, and a summary is where a test that passes for the wrong
reason survives longest.

### `pricetype_fix.FREE_SRC` keys on a `src:` tag only ~19% of library rows carry (found 2026-09-16)

The pipeline arrived at build with **210 blank `price_type`** values — not a schema enum value, and
the carried base preserves them forever. `pricetype_fix.py` normalized them conservatively (202 →
`Varies`, 8 → `Paid` on a quoted dollar amount, 0 → `Free`) and the feed now carries **no non-schema
value at all**: Paid 822 / Varies 4124 / Free 2153.

The zero is the finding. SKILL.md declares library programs free, and `FREE_SRC` implements that by
matching a **`src:<source>` token inside `tags`** — but only **689** event rows carry a `src:` token,
against **2,762** rows carrying the `library` content tag, so the library→`Free` rule is structurally
unreachable for roughly four-fifths of the rows it was written for. Same shape as
`LIBRARY_SRC` ↔ the fetcher's dispatch and `deals_yield` ↔ `SOURCE_KEYS`: **two ways of naming the
same source, one of which survives the round-trip and one of which does not.**

**Deliberately NOT fixed in-run, and the asymmetry is why.** `Varies` makes no false claim, while a
wrongly-stamped `Free` is a factual claim a family acts on at a ticket counter — the
`deal_description` standard. So the conservative value is the safe place to sit while the fix is
designed. The fix is to key `FREE_SRC` on the **`library` content tag**, which `tagify()` stamps
reliably and which is now assertion-protected — but that moves ~2,762 rows, so it needs a measured
false-positive check first (library rows whose own description states a fee) rather than a
same-run edit. Recorded here so the next run inherits the diagnosis, not just the symptom.

**MEASURED EXACTLY 2026-09-18, and the reach is worse than "roughly four-fifths."** The blank count
is now a rising series — **37 (09-17) → 210 (09-16) → 411 (09-18)** — and of this run's 411 blanks,
**ZERO carry a `src:` tag while 396 carry the `library` content tag.** So on the rows that actually
need the rule, `FREE_SRC` is not *mostly* unreachable, it is **entirely** unreachable: 0/411. The
approximation above was measured over all event rows, which flatters it, because the rows that
already carry a `src:` token are exactly the ones that already got stamped and never became blanks.
**Measure a rule's reach over the rows it would FIRE on, not over the corpus** — a denominator that
includes rows the rule has already handled hides a total failure as a partial one.

All 411 were stamped `Varies`; final distribution **Paid 808 / Varies 4,399 / Free 2,010**, no
non-schema value. The remedy is unchanged and still deliberately deferred, for the same asymmetry.
Two operational notes this run added: the fix forced a **rebuild**, so STEP 5.5 had to be re-run
(`end_date added=40`, 39 events + 1 volunteer — within the documented decline 130 → 89 → 74 → 52 →
40, not a collapse); and `import pricetype_fix` is itself a write, per the section above.

### STEP 4.5: on CivicPlus, a BODY photo is fine and a ROTATING SLIDESHOW banner is not (found 2026-09-18)

The 2026-09-15 rule is that "from the venue's own page" does not imply "a photo of the venue," and it
was written about licensed stock. The same rule has a second, less obvious form on municipal CMS
sites, where both candidates are genuine local photography served by the city itself:

* **Accept a described BODY image.** Maple Grove's `documentId=9075` carries the alt text *"Crowd at
  Town Green with musicians"* — it depicts the venue, and the description is what proves it.
* **Reject a site-wide ROTATING SLIDESHOW banner.** Maplewood's `documentID=25382` is one frame of a
  homepage carousel. It is a photo *of the city*, attached to no particular venue, and stamping it
  onto a row claims it depicts that row's location. That is the aggregator-banner error SKILL.md
  forbids, reached through a CMS instead of through a CVB — and `visitduluth.com`'s
  destination-marketing banner was rejected the same run on the identical reasoning.

The tell is **whether the image is addressed by the page or by the template**: a body image with its
own description belongs to that page, while a carousel frame belongs to every page on the site. Since
`site_photo` sits in `REAL_PHOTO_SOURCES` and never self-heals, the cost of guessing wrong is
permanent, so an undescribed hero on a CMS site is a reject, not a maybe.

### The rejection ledger persists; `__meta__` resets — state which, in the same edit (settled 2026-09-18)

The 2026-09-17 finding is that the rejection record lived inside `__meta__`, which the 2026-09-16
staleness fix deletes — two correct rules quietly destroying each other. It is now closed: rejections
live in `__rejected__`, a **top-level key that carries deliberately**, unioned at load time with a
hand-written `REJECT_SEED`. `--select` prints `known-bad sites skipped: N` with each reason, so the
ledger is read rather than merely stored. It stands at **9 entries** (5 added 2026-09-18) and
`_step45_results.json` holds 89 resolved sites (55 with a photo, 34 recorded as none).

Two implementation details that are easy to get wrong. `do_apply()` must **pop** `__rejected__`
before iterating, or the ledger is treated as a website and fetched. And only `do_dnr()` writes
`RESULTS`, so popping in `do_apply()` cannot lose it — verify that before copying the pattern to
another phase.

The rule this closes on is the per-field one: **when adding a key to a structure a run inherits,
state in the same edit whether it RESETS or CARRIES.** `__meta__` is run-scoped and resets (its
`stop_reason` and `run_date` describe one run). `__rejected__` and the website→photo map are caches
and carry (re-fetching them spends the budget rediscovering what is on disk — the `geo0826.py`
argument). Every defect in this area has come from a field being added without that decision being
made for it.

### The washco sub-calendar fan-out PAID OFF in coverage, and the payoff was attributed before it was banked (2026-09-18)

`mn_coverage` returned **53** warnings against **57** on both 2026-09-16 and 2026-09-17 — the first
fall in the series, and against the 2026-09-16 entry's prediction that a fixed `END_DATE` makes this
number drift *upward* daily (the window did shrink again, 45 → 44 days). A coverage number that
improves is exactly the kind nobody investigates, so it was attributed in the order that entry
prescribes before being accepted: **0 merges** this run (so not the `coverage_threshold_crossed_by_merge`
class) and **0 fetch errors** across **60** dispatched sources, status OK 55 / SHORT 1 / CAPPED 2 /
NOFEED 2 (so not a dead feed). Composition moved 19 → **16** cities short by exactly 1 and 33 → **32**
zero-event; by tier, core metro 1 / major suburb 10 / small city 42. **Cities served only by the
capped Washington County umbrella calendar that are still short: 0.** The 2026-09-16 fan-out accounts
for the whole improvement, and it beat the window drift rather than merely offsetting it.

Two things to carry. **A fan-out's payoff shows up a run or more LATER, in a different metric, and
will be misread as noise unless someone goes looking for it** — the fetch-side finding logged 103 new
in-window rows, which said nothing about whether any *city* crossed a floor. And **an improvement
deserves the same attribution discipline as a regression**: the two cheap checks cost one command
each, and without them "53, down from 57" is just a number that would have been quoted next run as
evidence for whatever theory was handy. The one remaining core-metro shortfall is **Coon Rapids
7/8**, the carried 2026-09-14 `coverage_threshold_crossed_by_merge` case — still not a content gap.

### A venue's OWN page can serve LICENSED STOCK as its hero photo (found 2026-09-15)

STEP 4.5's whole premise is that a photo taken from the venue's own page is a real `site_photo`.
`ccstcloud.org/volunteer` serves **Pexels and AdobeStock** images as its hero and body photos.
Accepting one would launder licensed stock into `site_photo` — **worse than leaving the row on
`curated_category`**, because `site_photo` is in `REAL_PHOTO_SOURCES`: every later layer defers to it
and it never self-heals. **"From the venue's own page" does not imply "a photo of the venue."**

So every 4.5 WebFetch must ask for the image **filenames**, not just the URLs, and reject
stock-CDN paths. 3 of this run's 13 rejections came from this check. Two companions found the same
way: `experiencerochestermn.com`'s events calendar returned a **Mayo Civic Center umbrella hero**
that would have been stamped onto 3 unrelated events (SKILL.md forbids an aggregator banner), and a
`boulderingproject.com` candidate was `summer-camp-2026-atx` — **Austin, Texas**. The wrong-city
catch is worth noting on its own: STEP 4.8's Wikimedia layer has a Minnesota bounding-box guard, but
**4.5 has no coordinate to check**, so the only defence is reading the candidate URLs by hand.
Record the REJECTED candidates with reasons next to the accepted ones — that is what keeps the
carried website→photo map trustworthy, the same discipline `KEEP_APART` gets. Byte-check every
accepted asset by magic number before writing it (9/9 this run), the discipline `dnr_banner_map()`
already applies after the DNR API's own `image` field was found to 404.

### A helper whose argv is OPTIONAL fails as a silent no-op (found 2026-09-15)

`frugal_scrub.py` invoked bare printed its module docstring and **exited 0 having done nothing**.
In every log that is indistinguishable from a converged pass — no error, no warning, no rows. It was
caught only because the expected report lines were absent, which is luck, not a guard.

This is the project's standing silent-failure class arriving through the **helper interface**, a
door none of the existing remedies cover: the stale-input guards watch inputs, the registry
assertions watch dispatch lists, the marker assertions watch outputs. Nothing watches *how the
helper was called*. The fix is the one `fetch_feeds.py`'s window and `errlog_step7.py`'s `argv[1]`
already have — **make the absence a crash, not a usage message**. Until the owner hardens it, invoke
every `_compiled_work.json`-consuming helper with the path explicit, `--dry-run` first, and **read
the report lines rather than the exit status**. Generalising the rule this file already states for
dates: *a value a helper can default is a value it will default wrongly* — and a no-op default is
the worst kind, because it defaults to doing nothing and calls it success.

### A LEGITIMATE merge can push a city under a coverage threshold (found 2026-09-14)

`mn_coverage` reported **Coon Rapids at 7 against the core-metro floor of 8** — the first core-metro
shortfall in the project's history, and exactly the shape that sends someone hunting a dead feed.
There is no content gap. This run's own `step8_venue_repair` merged two Urban Air rows on evidence
that is not the name (verbatim address + the venue's own per-location URL), which is the correct
merge; the city simply had 8 rows, one of which was a duplicate. **The count moved because the data
got more honest.**

Three things to carry. **A tiered-coverage warning is a claim about rows, and a dedup pass changes
rows** — so before investigating a shortfall, diff it against *this run's own merge log*, which is a
cheaper check than probing feeds. **Do not "fix" it by undoing the merge**; that restores the number
by restoring the defect, and it is the count-only-tripwire failure inverted — there a count passed
while the underlying titles were rotten, here a count fails while the underlying titles are right.
And **the floor is a floor on real venues, not on rows**, so a threshold crossed by deduplication is
a reporting artifact to be recorded, not a regression. Logged `coverage_threshold_crossed_by_merge`
so the next run does not re-open it.

### Images: the Wikimedia venue-photo layer + the curated_category ratchet (added 2026-08-29)

Why web images "never populated": every named venue arrives from the carried base stamped
`curated_category` (a generic category image), and *every* upgrade layer in `image_upgrades.py`
treated `curated_category` as final. So the first run that stamped a generic image on a blank
row **permanently** froze that venue out of ever getting a real photo — a one-way ratchet.
On 2026-08-29's feed, 5,154 of 5,895 rows were `curated_category` and only 4 were real photos.
og:image can't fix this: og:image lives in the HTML `<head>`, which WebFetch strips, and the
pipeline is policy-bound to WebFetch for web pages — so venue self-photos are uncapturable
within policy. Set og:image aside.

The fix is a fourth layer, `wikimedia`, committed into `image_upgrades.py` (commit `54e8a8f8`,
verified live by blob SHA-1). It is eligible on `curated_category` as well as blank/weak, and
pulls the venue's own photo from Wikipedia's REST summary API
(`https://en.wikipedia.org/api/rest_v1/page/summary/<name>` — a direct read-only API, allowed
exactly like the Openverse call, NOT scraping). It is ON by default; run STEP 4.8 with
`--no-openverse` (the Openverse layer is a timing-out no-op) and leave Wikimedia enabled.

Four precision guards, each catching a **real** observed wrong-match, not a synthetic one:

1. **Place-hint gate** — only venue-shaped titles (park/zoo/museum/lake/nature center/…) are
   queried. Generic activity titles ("Chess Club" → the concept page "Chess club") are never
   attempted. This is the discriminator; the overlap check alone can't tell a venue from a
   concept.
2. **Name/page token overlap** — the returned Wikipedia title must share a distinctive
   (non-stopword) token with the venue name.
3. **Minnesota bounding-box check on the article's coordinates** — `lat 43.0–49.6, lon
   −97.6 to −89.2`. This is the one that matters most: "Crooked Lake Park" resolved to a park
   in *Florida* and "Lakefront Park" to a defunct *Chicago* ballpark; both were rejected only
   because their coordinates fall outside MN. Coordinates are authoritative; the summary
   `description` string ("… in Florida") is the fallback when an article has no coordinates.
4. **Logo/wordmark/SVG screen** — a Wikipedia brand logo is not a venue photo. Mill City
   Museum, Somali Museum of Minnesota, Hmong Cultural Center Museum and Hennepin History Museum
   all resolved to logos and were dropped back to their curated fallback. Same standard as
   STEP 4.5's logo filter; without it those four shipped a wordmark as the "photo".

Disambiguation pages (10 on this feed — "Riverside Park", "Fall Festival", "Hidden Falls", …)
and 404s (341 small local venues with no article) resolve to nothing and keep their fallback.
Net on 2026-08-29's feed: ~50 event cards across ~29 marquee MN venues moved to the venue's
own photo; the layer is idempotent (a warm re-run applies 0) and never overwrites a self-photo
or a hand-picked `curated` override (`wikimedia` was added to `REAL_PHOTO_SOURCES`, so the
curated override defers to it).

Two things to carry forward:

* **`wikimedia` is now a fifth legitimate `image_source` value** alongside `openverse_named`,
  `curated_category`, `curated` (and the real-photo `facebook`/`og_image`/`site_photo`). It is
  NOT a reimplementation artifact like `curated_tag`. SKILL.md's "helper only ever writes …"
  guard was updated to list it.
* **The disk cache (`_wiki_cache.json`) warm-start is now WIRED (2026-08-29, helper blob
  `880b07f6edbe`).** The cache does not persist across daily sandboxes, so a cold run rebuilds
  it (~429 lookups inside the 240 s budget) and lands only ~41 on the first pass, converging to
  ~50 on a later run. Fix has two halves, both committed: (1) the helper **self-primes** —
  `_wiki_prime_cache()` runs at the top of the Wikimedia layer and, if no local
  `_wiki_cache.json` exists, GETs the published copy from
  `https://raw.githubusercontent.com/avlhohn/msp-family-feed/main/_wiki_cache.json` (public raw,
  no auth, soft-fail; a local copy always wins). (2) STEP 6 **re-publishes** the freshened cache
  after the run (`publish_feed.py "…" --only _wiki_cache.json`). Net: a fresh sandbox starts warm
  and hits ~50 in ONE pass (verified — cold local delete → `primed:411` → 50 applied in 40 s).
  Flags: `--no-wiki-cache-fetch` forces a cold rebuild for offline testing; deleting the repo's
  committed `_wiki_cache.json` forces a full refresh. The 411-entry warm cache is seeded in the
  repo (blob `f18f98330646`). One caveat: `publish_feed.py` reads the file relative to cwd and
  publishes to the same repo path, so the local `_wiki_cache.json` must sit in the folder you
  run it from.

**The Wikimedia layer has now reached its ceiling, and a 0-applied run is the expected result.**
On 2026-08-30 it applied 0 new photos against a warm 443-entry cache with 53 venue photos already
carried — correct and idempotent, not a regression. But images remain the weakest part of the
feed: 5,083 of 6,234 rows still carry a generic `curated_category` image, the whole feed has only
495 distinct image URLs, and **one image covers 1,437 rows**. What is left is library programming,
which has no venue photo to find, so no amount of re-running Wikimedia will move it. Do not spend
the enrichment budget re-running a layer that converged; if this number is to improve it needs a
different source, not another pass.

**RE-MEASURED 2026-09-15 — that different source turned out to be STEP 4.5, and the monoculture
numbers above are now materially out of date.** The feed carries **1,169 distinct image URLs** (was
495) and its most-used image covers **436 rows** (was 1,437); `site_photo` is **1,183** rows against
949 five days ago. What moved it is the 4.5 site-photo backfill finally running nightly, not another
Wikimedia pass — which applied **1** photo this run, exactly the converged behaviour described
above. Two things to carry: **the diagnosis in this section was right and its numbers went stale
anyway**, which is this file's own re-read-the-claim rule landing on a paragraph that *states* a
number rather than asserting one; and **4,880 rows do still sit on a generic category image**, so
the conclusion ("needs a different source") holds — 4.5 is that source and it stops on the 20-minute
budget every run against ~4.2k eligible distinct sites, so this improves gradually, run over run,
and never in one pass.

**2026-09-16: `site_photo` 1,223, `curated_category` 4,843** (curated 905, facebook 62, wikimedia 58,
og_image 8). Wikimedia applied **1** against a warm 761-entry cache — the converged behaviour again,
on a third consecutive run. The +40 came entirely from 4.5, which is the predicted gradient and not a
number to chase: **this paragraph is now a running series precisely because the prose above went
stale once**, and a series is cheaper to re-read than a claim is to re-verify.

**2026-09-17: `site_photo` 1,225, `curated_category` 4,728** (curated 902, facebook 59, wikimedia 57,
og_image 8). Distinct image URLs **1,180**; most-used image covers **429** rows. Wikimedia applied
**0** against a warm cache that grew 771 → 781 — converged behaviour on a fourth consecutive run.
The series is now doing work no single number could: `site_photo` moved only **+2** while
`curated_category` fell **−115**. Both are correct. 4.5 upgraded 280 rows but 263 of them were
*already* carrying this pass's photo (the `warm` counter), so its net effect shows up in the
category-image column, not the site-photo one. **Read the series as a pair** — `site_photo +2` alone
reads like 4.5 stalling, and it did not.

**2026-09-18: `site_photo` 1,212, `curated_category` 4,985** (curated 902, wikimedia 57, facebook 53,
og_image 8). Distinct image URLs **1,171**; most-used image covers **473** rows. Wikimedia applied
**0** against a warm cache — converged on a fifth consecutive run. **Every one of those numbers moved
the WRONG WAY, and none of it is a regression**, which is why the pair rule adopted yesterday is not
enough on its own. 4.5 upgraded 290 rows (277 warm, 13 new) and rejected nothing it should have
accepted. What moved the columns is the **dataset**: events grew 5,252 → 5,490 on a heavily
library-weighted intake, and library programming has no venue photo to find, so +238 rows land almost
entirely on `curated_category` and drag every ratio down. The −13 on `site_photo` and −6 on `facebook`
are rows *aging out* of the front of the window, not rows losing a photo.

So the series needs a **third number — the dataset size** — or growth in one category silently swamps
both image columns. The generalisation, and it is this file's count-only-tripwire lesson in a fifth
form: **a proportion reported as two absolute counts is not a proportion.** `site_photo −13` against
a fixed denominator would be a real regression; against a denominator that grew 238 it is noise. Read
all three, and when the denominator moved, say so before reading anything into the numerator.

**2026-09-21: `site_photo` 1,104, `curated_category` 4,719, dataset 6,784 rows** (curated 878,
wikimedia 52, facebook 26, og_image 5). Distinct image URLs **1,100**; most-used image covers
**475**. Every absolute count is down again, and the third number is what makes them readable: the
dataset fell **7,217 → 6,784 (−433)**, so as *shares* both columns are flat — `site_photo` 16.8% →
**16.3%**, `curated_category` 69.1% → **69.6%**. The denominator moved because the window shrank to
41 days, 17 adult rows were dropped, and this run's dedup passes merged real duplicates. STEP 4.5
reported `attempted 135 / upgraded 274 / stop_reason deadline`, with **266 of the 274 already
carrying this pass's photo** (the `warm` counter) — the 2026-09-17 pair-reading lesson again, and
the reason `site_photo` can fall while 4.5 is working exactly as designed. **The series has now run
long enough to state its own baseline expectation: flat shares, falling absolutes, `stop_reason
deadline` every run.** A departure from *that* is the signal; a departure from any single number in
it is not.

### Sports enter by free-text search and can drop to ZERO with nothing warning (built 2026-09-19)

Sports are IN scope (SKILL.md:44) and belong in `events` (no new CSV). SKILL.md:182-185 names 15
teams to search each run — but they enter via STEP 2 free-text WebSearch, an **untagged,
non-deterministic path**, so a team can silently contribute zero rows in a window where it plainly
has home games and nothing objects. Found live: **Minnesota United (MNUFC) had 0 rows on
2026-09-19**, mid-MLS-season, and only a user question surfaced it. Same silent-failure class as the
`ical_feed_pull` lapse — a mandated intake that raises nothing when it produces nothing.

`sports_coverage.py` (folder root, undated, `MSP_RUNDIR`/`MSP_TODAY`/`MSP_END`-driven) is the
tripwire. It runs at **STEP 8, after `build_guide.py` (it reads the built `events.csv`) and BEFORE
`errlog_step7.py`** so its findings reach `error_log.csv`. It appends to `_findings.json` — one
`info` `sports_coverage` summary row plus one `warning` `sports_shortfall` row per in-season team
with zero rows — idempotently (it strips its own prior `sports_*` rows first, preserving all other
findings). `sports_coverage`/`sports_shortfall` are **not** reserved errlog types, so no collision.

```bash
MSP_TODAY=$TODAY MSP_END=$END python3 sports_coverage.py events.csv --dry-run   # report only
MSP_TODAY=$TODAY MSP_END=$END python3 sports_coverage.py events.csv             # append findings
python3 test_sports_coverage.py                                                 # must be 15 passed, 0 failed
```

The one design decision that keeps it from becoming a permanent warning: a **window-overlap season
gate**. Each team carries `active_months`; a team is *guarded* only when the run window's months
intersect its season, so genuinely off-season teams (Saints/Aurora/Frost in October) stay **silent**
rather than warning every night — the failure mode this project forbids. Erring toward a NARROW
season is deliberate: a missed shoulder-week is cosmetic, a permanent false warning trains the reader
to skim the block. Four rules that matter:

1. **A shortfall is a prompt to VERIFY, not an assertion of failure.** The warning text says "likely
   a STEP 2 sourcing gap — add/verify a home-game search," because the tripwire cannot know whether
   a team is truly home this week; it knows only that a team that *should* be findable isn't there.
2. **Aliases are title-only lowercase substrings and must be DISTINCTIVE.** Mankato requires
   `mankato`, never bare `mavericks`/`minnesota state` — a loose alias false-matches an opponent or
   State Fair/State Parks and hides a real miss. A too-broad alias is worse than a missing team.
3. **The season gate is the anti-false-alarm mechanism and was proven to stay silent off-season**
   before being trusted — `test_sports_coverage.py`'s load-bearing pair is "in-season miss warns"
   AND "off-season miss stays silent," and the guard was made to FAIL on purpose (guard disabled →
   4 fails) before the green 15/0 was trusted.
4. **Expected live result 2026-09-19** (window Sept 19–Oct 31, months {9,10}): warns on United and
   Timberwolves (both have October home dates, both at 0 rows); all 10 other guarded teams covered;
   Saints/Aurora/Frost correctly off-season. A shortfall count that suddenly includes an
   *off-season* team means the gate or an alias drifted — check the season table, not the feed.

### Sports now have a STRUCTURED source, wired ADDITIVE + SOFT-FAIL (built 2026-09-20)

The 2026-09-19 tripwire only *detects* the sports gap; it does not close it. `espn_sports.py`
(folder root, undated, `MSP_TODAY`/`MSP_END`-driven) is the deterministic SOURCE — one JSON
schedule call per team against ESPN's hidden site API
(`https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{ref}/schedule`, free, no
key), home games only, in-window only, mapped to the same 20-key event-row shape every other
fetcher emits. It is wired into `fetch_feeds.py` as **`run_espn_sports()`**, dispatched under both
`all` and a new `sports` branch, so it runs every nightly. Registry `TEAMS` covers all six MN pros
the owner required — **Twins, Vikings, Timberwolves, Wild, Lynx, United (MLS ref `17362`)** — plus
the two D-I Gophers programs. Small colleges (UMD/SCSU/Mankato/Winona/Bemidji) stay on free-text
search + the tripwire by design.

```bash
MSP_TODAY=$TODAY MSP_END=$END python3 fetch_feeds.py sports   # ESPN source alone
python3 test_espn_sports.py                                   # must be 75 passed, 0 failed
```

Five design rules, each load-bearing (breaking one fails silently):

1. **ADDITIVE + SOFT-FAIL is why it could be wired before its reachability was proven.** ESPN's API
   is unofficial and 403s some non-browser agents. `fetch_all()` wraps every per-team fetch in
   try/except and returns `([], ERROR-note)` on ANY failure, and `run_espn_sports()` wraps even the
   `import` — so a total ESPN outage, an import error, or bad JSON contributes zero rows and CANNOT
   break the nightly. Worst case is "no worse than today," where sports entered only via WebSearch.
   Proven offline: with `http` forced to raise, the dispatch adds 0 rows and logs 8 `ERROR` reports
   without crashing.
2. **The FIRST NIGHTLY IS THE PROBE, and the sandbox cannot be.** This environment's WebFetch 403s
   ESPN and policy bars a curl/python fallback, so reachability from the pipeline UA is **unproven
   from here**. Production fetches server-side via `fetch_feeds.http` (urllib, custom UA, cloud IP),
   which is a different agent — so the go/no-go is the `espn_*` rows in the next run's feedpull
   `report`/`error_log`. `python3 espn_sports.py probe` prints a per-team reachability table for
   exactly this. If every team logs `ERROR`, ESPN is blocking the pipeline UA too and the source
   needs a header change — the tripwire keeps covering sports until then.
3. **HOME GAMES ONLY, resolved from ESPN's own `homeAway` flag** on the competitor matching this
   schedule's top-level `team` block — never guessed. An away game is not a local thing to attend.
4. **UTC → America/Chicago BEFORE the date test** (`zoneinfo`). A 7pm CT game is ~00:00–01:00 UTC
   the NEXT day, so a naive slice misfiles evening games — the off-by-one class this file documents
   for the run window. Tested at both the CDT and CST boundaries.
5. **`price_type = "Varies"`, never "Free"** — ticketed with no single quoted price; stamping Free
   is a claim a family acts on at a counter. `row_fn` is INJECTED (production passes `fetch_feeds.row`,
   tests pass a stub) so the 20-key contract has one source of truth, and the module NEVER fetches at
   import time (import must not be a write).

Add to the STEP 1 feature-grep list: **`run_espn_sports` (`fetch_feeds.py`) and `TEAMS` plus
`schedule_url` (`espn_sports.py`)**. Like `sports_coverage.py`, `espn_sports.py` and its test are
**not** in the repo by design — do not read their `MISSING_REMOTE` as stranding. And per the STEP 2
"diff the mandated source list against the fetcher's dispatch" discipline: sports are now a
DISPATCHED source, not a free-text-only one, so a team at zero rows is a *sourcing* question for
that team's ESPN endpoint, not a reason to re-add a WebSearch.

### ESPN's first nightly: reachable, and carrying a WRONG-DATE defect a row count cannot see (2026-09-21)

The 2026-09-20 go/no-go is **answered YES**. On its first nightly, `run_espn_sports()` reached
ESPN from the pipeline UA: all **8** registered teams returned parseable schedule JSON with
**zero `ERROR` reports**, yielding **10** in-window home rows; `mnufc` reported
`NO_HOME_IN_WINDOW` and `gophers_mbb` `EMPTY` (season starts November). The additive/soft-fail
wiring was never exercised, which is the outcome it was built for.

**And a defect was found live inside that success, by reading the ROWS rather than the count.**
ESPN emits a **full ISO timestamp even when a kickoff is unannounced**, flagging it
`timeValid: false` and using a midnight-Eastern placeholder. Rule 4 of the 2026-09-20 section —
"UTC → America/Chicago BEFORE the date test" — is correct for a real kickoff and **actively
harmful for a placeholder**: converting midnight Eastern to Central moves the date back one day.
Two Gophers football home games were filed **a day early**, each carrying a fabricated
**11:00 PM** kickoff. The date is now taken from the raw UTC prefix with **no conversion** when
`timeValid` is false, and `time` is left **empty** rather than invented.

Three things to carry. **A flag saying "this field is not real" must be read before the field
is transformed**, or the transformation manufactures precision the source explicitly disclaimed —
and an invented 11 PM start for a family-guide row is the `deal_description` standard failing:
a factual claim a family acts on. **The tz-conversion rule and the placeholder rule point
opposite ways on the same field**, so neither is safe stated alone; both are now in
`espn_sports.py` with the `timeValid` test first. And **every count-shaped check passed the
whole time** — 8 teams, 10 rows, 0 errors, the tripwire silent — because the rows existed, were
attributed, and were simply *wrong about when*. `test_espn_sports.py` **58 → 75 passed**.

### A STRUCTURED source and a FREE-TEXT one describe the same game, and no dedup pass could see it (built 2026-09-21)

Wiring ESPN created a duplicate class this project had not had before: the same home game
arriving twice, once from the structured source and once from a carried free-text WebSearch row,
under **different titles** (`Minnesota Twins vs. Detroit Tigers` against `Twins vs Tigers at
Target Field`). Every existing pass is blind to it for a reason already documented twice —
`dupsweep` requires a title match before it compares place, and `step8_venue_repair` is a hand
table keyed on venue, not on a game.

`sports_dedup.py` runs as a **STEP 4.3 pass** and collapsed **4** carried rows into their
structured ESPN anchors. Only a row whose `_src` begins `espn_` can be an **anchor** (guard 1),
and the survivor is always the anchor regardless of `completeness()` — it carries the source's own
`homeAway` flag and venue, so the usual richest-row rule is deliberately overridden. A candidate
joins the anchor when **the date is identical** (guard 2), **the anchor's title tokens are a
subset of the candidate's** (`Minnesota Twins vs. Detroit Tigers` ⊆ `Twins vs Tigers at Target
Field` fails; the containment runs anchor-into-candidate precisely because the structured title is
the terser, canonical one), and **the resolved city matches** (guard 4).

**A loose token subset is exactly what this file forbids elsewhere, and three things make it safe
HERE — none of which transfer.** `MIN_ANCHOR_TOKENS = 4` (guard 3) requires two team names before
a row may anchor anything, so a short generic title can never become a merge magnet. The identical
**date** requirement means it cannot chain a weekly series the way `_dedup4_0822` does. And a team
cannot play two home games on one calendar date, so the merge ultimately rests on **a fact about
the sport** rather than on string similarity — which is the Red Cow "evidence that is not the
name" standard, satisfied by a constraint rather than by an address. Move any one of those away
and the subset rule becomes the venue-eating error the dedup sections warn about.
`test_sports_dedup.py` **27 passed**.

One companion fix from the same work: **`dupsweep.na()` now strips a TRAILING spelled-out state
token**, so `… Minneapolis Minnesota` and `… Minneapolis, MN` normalize alike. `na()` already
stripped the bare `mn` token; the spelled form was the `Saint`/`St` and `Suite`/`Ste` blindness
arriving through a third spelling of the same idea. **Trailing-only is deliberate** — a general
strip would eat `Minnesota Zoo` and `Minnesota Landscape Arboretum`, which is the wrong-merge
error that silently deletes a real venue. `test_dupsweep.py` **42 → 46 passed**.

### A tripwire's FIXED WARNING TEXT becomes an over-claim the moment a better source is wired (found 2026-09-21)

`sports_coverage.py` warns that a shortfall is *"likely a STEP 2 sourcing gap, not an
off-season."* That sentence was true when written on 2026-09-19, because sports entered **only**
by free-text WebSearch and a zero genuinely could not be distinguished from a miss. Since
2026-09-20 eight teams carry a STRUCTURED source, so for those eight the sentence now **asserts
more than the tripwire knows**: the source's own report answers the question the tripwire can
only ask.

This run's three shortfalls resolve two different ways on the same evidence structure, and
recording both side by side is the point — *a shortfall block where every row means the same
thing is one nobody reads*:

* **Minnesota United is a TRUE NEGATIVE, not a gap.** `espn_mnufc` returned status
  `NO_HOME_IN_WINDOW` with the note *"13 home games total, 0 in [2026-09-21..2026-10-31]"* — the
  schedule **parsed** (13 home games found, which rules out a fetch failure presenting as a
  zero) and simply carries no home date in the window. A free-text intake finding nothing and a
  structured source finding the schedule and reporting no home date are **two independent paths
  agreeing**. Do not re-open this as a sourcing gap or add a WebSearch for it.
* **Mankato and St. Cloud State remain exactly what the tripwire says.** Neither is in the ESPN
  registry (small colleges stay on free-text by design), so nothing corroborates their zero and
  they stay a prompt to verify, unresolved this run.

Note the **asymmetry that makes this worth logging at all**: a structured source can only ever
DOWNGRADE a shortfall to a true negative, never confirm one, because a team absent from the
registry produces no report to read. The attribution is filed as
`shortfall_attribution_check` — and **`sports_coverage.py`'s prose should be softened at source**
for registry teams, because an attribution row written by hand each run is the
obey-it-perfectly-forever rule this file keeps proving worthless.

**The naming of that row is itself a small finding, and it is this file's "prose is unasserted by
construction" rule landing on a docstring.** `_add_sports_attrib.py` carried a paragraph claiming
the row was *"deliberately NOT prefixed `sports_`"* while the constant two lines below it read
`sports_shortfall_attribution` — the prose asserted the opposite of the code. It survived only
because `sports_coverage.py` strips its prior rows by **exact** match on
`("sports_coverage", "sports_shortfall")`, so the collision happened to be harmless; **that is
luck, not design**, since the strip is one edit away from being widened to a prefix. Renamed to
`shortfall_attribution_check` per the 2026-09-13 rule (`<thing>_check`, never `<signal>_check`),
with a `LEGACY_NAMES` set carrying the old spelling — because **renaming an idempotency key
silently breaks the idempotency it was keyed on**, and a re-run would otherwise leave the row it
already wrote sitting beside the new one.

### Deals: retired Frugal Mom codes hide in `deal_description`, not `deals.csv` (found 2026-08-29)

Twin Cities Frugal Mom was retired 2026-08-28 (her roundups carried codes EXCLUSIVE to her:
`TCFM`, `TCFMB$2OFF`, `FRUGALMOM25`, "mention the Frugal Mom post"). Retiring the source stops
new pulls but does **not** remove codes already baked into carried rows, so they resurfaced in
the live app on 2026-08-29. The trap: scanning `deals.csv` came back **clean** — the codes live
in the `deal_description` of ~20 **`events` and `restaurants`** rows (Children's Museum, Twins,
Works Museum, Zero Gravity, Hyderabad Grill), a field that carries forward every run. Scan
**every category's `deal_description`**, not just the deals table.

The standing guard is `frugal_scrub.py` (folder root), run in STEP 4.35 **after** the overlay so
it also catches codes the overlay just re-stamped from `standing_deals.csv`. It is surgical:
`deal_description` is a semicolon list of separate discounts, and it drops ONLY the offending
clause, keeping every other publicly-true deal (Children's Museum keeps First Free Sundays /
MELSA smARTpass / Play for All; the Twins keep student/military/senior deals). When the code was
the WHOLE deal it blanks `deal_description`/`deal_expiry` and clears `has_deal`. Two rules that
matter: (1) match on `TCFM`/`FRUGALMOM`/`frugal mom` tokens, **never bare "frugal"** — the
Renaissance Festival's own "Frugal Friday" promo must survive, and it does (9 rows kept). (2)
It is idempotent and handles the dict-shaped `_compiled_work.json` (skips the top-level `counts`
key). One-time live cleanup published 2026-08-29 (feed blob `31e9becf300f`, events `fb979d2b81e3`,
restaurants `1506e2fbc6eb`); `deals.csv` was already clean.

### Deals: a recurring deal is NOT gated on the run's weekday (corrected 2026-09-07)

`params.txt` carried a block headed *"MONDAY-GATED DEAL SEEDS ACTIVE TODAY"* listing nine venues as
"NOT active today (must NOT receive deal fields)". **That was a misreading, and acting on it would
have stripped true deal information from ~25 rows across 9 venues.** It nearly happened.

SKILL.md:435 gates **nothing** on the run's weekday. A named restaurant with a standing
kids-eat-free / family-night deal is routed to `restaurants` with `has_deal: true`, gets a mirrored
`meal_deals` row, and *"for recurring day-of-week deals, put the terms in `deal_description` and
leave `deal_expiry` blank (it recurs)"*. **The day lives in the TEXT.** The `[DAY_OF_WEEK]`
substitution elsewhere in SKILL.md is a **search-query variable** — it shapes what today's searches
ask for, not which venues carry deal fields.

The reasoning that settles it: a standing deal is an attribute of a venue (the rule below), so
*"Green Mill: kids eat free Tuesday"* is true and useful on a Monday — a family reads it to plan
Tuesday. Blanking it today and re-creating it tomorrow is pure churn with a real-data-loss window in
between. **When a note in `params.txt` and the spec disagree, the spec wins and the NOTE gets
corrected, not the data.** A carried scratch file is not a source of truth; re-derive its claims
from SKILL.md before acting on one that deletes fields.

**Separately, SKILL.md:435 requirement 3 — the MIRRORED row — was being violated silently.** Four
kids-meal seeds (Broders' Pasta Bar, Tamarack Tap Room, Skinner's Pub & Eatery, The Lookout) had a
`restaurants` row with `has_deal: true` and **no** `meal_deals` row; `meal_deals` 137 → 141 once
emitted. Copy the deal terms **verbatim** from the already-verified `restaurants` row so no new
factual claim is made, and leave `date`/`deal_expiry` blank per the recurring rule.

Finding it also re-proved a rule from the other direction: a first crude name-matcher reported **61**
missing mirrors, a distinctive-token matcher reported **8** (4 in scope). Over-reporting by 53, and
acting on the first number would have injected ~57 spurious rows. CLAUDE.md states "a large drop is
a defect signal" — **the same applies to a large ADDITION.** Re-measure with a second, differently
constructed matcher before acting on any large number, in either direction.

### Deals: the standing-deal rule (adopted 2026-08-22)

A standing deal is **an attribute of a venue, not a row of its own**. "Como Zoo is free" is
not an event; it is a fact about Como Zoo. So standing deals are applied as an **overlay
after compile** (STEP 4.35), never as STEP 2 search results:

```bash
python3 deals_overlay.py _compiled_work.json    # joins standing_deals.csv by venue name
python3 deals_yield.py  _compiled_work.json     # per-source yield check for STEP 7
```

Three rules here that fail silently:

1. **Standing deals have no date and must skip the date window.** SKILL.md used to apply the
   two-month window to them, which discarded the entire payload — 0 park deals of 815 rows.
2. **A blank `deal_expiry` is valid data**, meaning "runs indefinitely." Never warn on it and
   never age the row out. Only set it when the source states a real end date.
3. **The yield check must be per source, not aggregate.** Several sources are legitimately
   zero out of season (DNR free park days, Kids Bowl Free, Marcus Kids Dream); an aggregate
   hides a real failure behind those correct zeroes. Attribute via the `deal_source`
   provenance field — never by substring-scanning `deal_description`, which counts noise.
4. **A `deal_description` is a quotation, not a summary from memory.** A discount code or a
   percentage is a factual claim a family will act on at a ticket counter. Three rows written
   from plausibility on 2026-08-22 were all wrong, and one of them (Crayola Experience) would
   have shipped a discount the venue had discontinued. If the page will not fetch, write no row.
5. **Only put a source in `deals_yield.py`'s `YEAR_ROUND` if it actually publishes venue-level
   standing discounts.** A healthy, correctly-fetched source can contribute nothing to this
   table — Thrifty Minnesota is an events site. Misfiling one makes it warn every run forever,
   and a permanent warning is worse than none: it trains the reader to skim the block. Use
   `NON_TABLE` or `RETIRED`, both of which log without warning.

### Deals: `deal_source` does not survive the schema round-trip (found 2026-08-26)

`deals_overlay.py` writes a `deal_source` provenance key, but `deal_source` is **not one of
the 19 schema-v3.1 BASE fields**, and `build_guide.py:22` rebuilds every row as
`{k: it.get(k,'') for k in BASE}`. The field is created by the overlay, consumed in the same
run, and **destroyed at build**. It never reaches the published CSV, so the next run's carried
base arrives with it blank. Two silent failures follow:

1. The overlay's `owned` carve-out — which exists precisely so that edits to
   `standing_deals.csv` take effect on a re-run — tests `deal_source`, so it was `False` for
   every carried row. The overlay was a **no-op on exactly the rows it was written to
   refresh**. A corrected `deal_description` would never have reached the live app for any
   previously stamped venue. This is the trap the carve-out's own comment describes,
   reintroduced through the schema round-trip rather than through the provenance value.
2. `deals_yield.py` attributes by `deal_source`, so a source whose venues were all stamped on
   an earlier run reports 0 and warns forever. On 2026-08-26 that produced two false WARNs
   (`kids_bowl_free`, `frugalmom_kids_eat_free`) whose real yields are 21 and 9 — exactly the
   permanent-warning failure rule 5 above warns about.

Fix — run the restore pre-pass **before** the overlay:

```bash
python3 bycat_shim.py deal_provenance_restore.py   # STEP 4.35 pre-pass
python3 bycat_shim.py deals_overlay.py
python3 bycat_shim.py deals_yield.py
```

It reconstructs attribution by **whitespace-normalised full-string equality** against
`standing_deals.csv`. This is *not* the substring keyword scan rule 3 forbids: a stored
`deal_description` is a verbatim copy of a table row, so exact equality recovers the original
source. It refuses to guess — a description claimed by 2+ sources, or by none, is left blank.
Restored 131 rows on 2026-08-26; overlay stamping went 5 → 147 and yield warnings 2 → 0.

**Do not "fix" this by adding `deal_source` to `BASE`.** Base44 reads the 21-column contract,
so widening it is a breaking change for a consumer outside this repo. The pre-pass reaches the
same result with no contract change.

### Helper shape mismatch: CORRECTED 2026-08-29 — the file is a dict, and the shim is not needed

This section previously stated that `_compiled_work.json` is a **flat list** and that
`deals_overlay.py`, `deals_yield.py`, `dedup_titles.py`, `image_upgrades.py` and `geo0826.py`
must be bridged with `bycat_shim.py`. **Verified on disk 2026-08-29: the artifact is a DICT of
the five category lists**, and every one of those helpers — plus `_seeds` and `_dupsweep` —
indexes it by category natively. `bycat_shim.py` was not needed and was not used. Following the
old line wraps each helper in a needless reshape-and-flatten round trip.

Check the artifact's shape before reaching for the shim. Only wrap a helper that actually
raises `TypeError: list indices must be integers or slices, not str`. When a shim *is* needed
it must run the tool **verbatim as a subprocess** — editing a helper locally is how the
`curated_tag` vocabulary drift got into 83 live rows.

Also note `_compiled_work.json` gains a top-level `counts` key after `dedup_titles.py` **and
again after the fabricated-URL guard**, so any consumer iterating `d.items()` crashes on
`'str' object has no attribute 'get'`. Drop it after each pass, and iterate an explicit `CATS`
list.

Quick usage:

```python
import mn_city_resolve as M
import mn_coverage as C

by_name, cities = M.load_gazetteer()
city, source = M.resolve_city(row, by_name, cities)     # source carries provenance
rows, warnings = C.tiered_coverage(events, by_name, cities)
```

Four rules that are easy to get wrong and fail silently:

1. The **address wins over coordinates**. A gap beyond 25 km means the *coordinate* is
   wrong, not the city — the resolver returns `coord_city_mismatch`; log those for
   re-geocoding.
2. Check the **gazetteer before** the `_NOTACITY` word filter, or Brooklyn Park, Brooklyn
   Center, Saint Louis Park and Columbia Heights get thrown away.
3. **`centroid_circular` never counts as coverage** — the city was an input to that
   coordinate, so counting it as evidence is circular.
4. The coverage check **walks the gazetteer, not the dataset**. A city with zero events
   contributes zero rows, so a row-iterating check can never see the gap that matters most.

Run `python3 test_city_resolve.py` after touching the resolver; it must report
`22 passed, 0 failed`. Every case in it is a real observed failure, not a synthetic one.
(This line said 18 until 2026-08-25; four cases were added after it was written. When the
count drifts, update this line — a stale pass-count assertion eventually gets misread as
a regression.)

The gazetteer is **cached on disk** — do not re-query Overpass on every run.

### A fail-closed guard on the LOGGING step blacks out every OTHER signal the run produced (found 2026-09-22)

Today's build ran STEP 1–6 correctly and then **hard-failed at STEP 7**: `_run_summary.json` was
still the 2026-09-21 file (mtime 04:10:36) against a `_feedpull_all.json` watermark of
2026-09-22 03:17:50, so the section-0 freshness assertion fired at `errlog_step7.py:81-83`. **The
guard did exactly what it was built to do** — it fired *before* `open(LOG,"a")`, `error_log.csv`
was untouched, and no rollback was owed (the 2026-09-13 partial-write discipline working). The
stale marker itself is the 2026-09-09 stale-run-scoped-input class, unremarkable and already
documented.

**What is new is the blast radius, and it inverts the argument that motivated these assertions.**
The assertions exist because of the six-run `ical_feed_pull` lapse — a signal degrading 34 → 1 → 0
while nothing objected. That silence was *partial*: the run still logged, just less. A fail-closed
guard on STEP 7 makes the silence **total**, because STEP 7 is the step that writes the log. One
stale marker therefore suppressed 68 feed rows, 11 deal-yield rows, the image-backfill row, the
coverage rows and every finding — all of them fresh, correct, and already computed — in order to
prevent one stale row. A run that dies at STEP 7 publishes its artifacts and reports **nothing
about itself**, which is the exact condition the guards were written to make impossible.

Three things to carry. **A guard's severity should scale with what it protects, not with what it
detects**: a stale *marker* is one wrong row, while a blocked *append* is a whole run's evidence,
so the freshness miss is a candidate for a logged `warning` that still appends, not a hard exit.
**The cheaper structural fix is to stop the marker being inheritable at all** — have STEP 7 itself
regenerate `_run_summary.json` from the built CSVs at the top of the step (the counts are read
from the artifacts either way, so nothing is lost), which makes the staleness unreachable rather
than detected. And **this run only recovered because a human-shaped step followed the failure**;
an unattended nightly would have published seven correct artifacts and left no trace that it ran.
Recorded, deliberately not changed in-run — it is a SHAPE change to the logging contract and the
owner's call per 2026-09-07.

### The carried BASE is a run-scoped input too, and a stale one is shaped exactly like a fresh one (found 2026-09-22)

STEP 1 found that the local `_compiled_work.json` was the **previous run's post-build scratch**,
not the published artifacts. Every later step reads it, so the whole run would have been built on
top of yesterday's tail state. The base was rebuilt from the 5 published CSVs with
`base_from_csvs.py` before STEP 3, and the run proceeded clean.

The finding is not the staleness, it is the **indistinguishability**: a carried base that is merely
stale has the same shape, the same keys, the same five categories and entirely plausible counts as
a fresh one. Nothing in the pipeline can tell them apart by looking, which makes it the 2026-09-09
stale-run-scoped-input class reaching the one artifact *every* later step consumes — the largest
blast radius available to that class, and the one instance of it with no assertion at all.
`_findings.json`, `_run_summary.json` and `_image_backfill.json` are all now freshness-asserted;
`_compiled_work.json` is not. **Rebuild the base from the published CSVs at STEP 1 as a matter of
course rather than proving the carried one fresh** — the published artifacts are the only copy
whose provenance is verifiable (blob SHA-1 against the remote), and the rebuild is cheap.

`base_from_csvs.py` sits at the folder root, is undated, and is **undocumented** — it belongs in
the STEP 1 feature-grep list, which is the second time a helper this file depends on has been
discovered by needing it rather than by reading about it.

### Adult filter, FIFTH instance — and this one is STRUCTURAL, so no vocabulary converges on it (found 2026-09-22)

A **21+ bar crawl** was sitting in a published family guide: `Fari "BOO" Downtown Bar Crawl`
(Paradise Center for the Arts, Faribault, 2026-10-30), whose description states **"must be 21"**
*and* whose activity **is** alcohol — two independent explicit adult signals, so no judgement call
was needed against the 2026-09-21 line. Found the way all four predecessors were found: **reading
live alcohol-token titles by hand.** 11 distinct titles / 25 rows carry an alcohol word-boundary
token and **zero** were reached by `_compound_drop()`.

The previous four instances (`brewery`/`brewing`, `55+`-in-the-description, bar-trivia-in-the-
address, `trivia`-alone) were all gaps in a *list*. **This one is a gap in the rule's SHAPE, and
the distinction changes the remedy**: `_compound_drop()` requires an ACTIVITY token co-occurring
with an alcohol token, and **a bar crawl is not an activity, it is a route between bars.** No
extension of `(trivia|bingo|karaoke)` ever converges on it, so the fix is a flat `DROP_PHRASES`
entry — the `magnet senior center` precedent — not another vocabulary completion. When a fifth
instance of a known class does not respond to the known remedy, check whether it is the same class
at all.

FP surface measured on live titles **before** the edit, per 2026-09-07: `bar crawl` 1 title,
`pub crawl` 0, and bare `crawl` **2** titles — the second being `Winona Zombie Crawl *20 Years And
Crawling*`, **a real family Halloween event**. So the anchored two-word phrase is provably zero-FP
while the bare keyword would have deleted a family row, which is the direction that actually hurts.
The other 10 alcohol-token titles are **deliberate KEEPs** and are recorded in `_findings.json` so
a later reader does not "finish the job" (`Wildwood Sports Bar & Grill` is a KIDS BOWL FREE bowling
centre; the Oktoberfest and live-music brewery rows are venue vibe only; `Initials Game LIVE` is
trivia-shaped **only in the description**, title-only scope working as designed).
`test_adult_events_filter.py` **169 → 175 passed**, three fail-on-purpose mutants run and read
**by failing case name**, not by count.

**APPLIED PRE-BUILD, and that is the whole operational lesson.** No rebuild, no STEP 5.5 re-run,
no re-stamped marker, no error_log rollback — unlike 2026-09-21, where the same class of fix landed
post-STEP-7 and cost every one of those. Events 4991 → 4990.

**A second, separate defect surfaced while verifying that idempotence.** `adult_events_filter.py`'s
own docstring states *"STEP 7 reads the report to emit `adult_event_filtered` pipeline info rows."*
**It does not.** `grep -rln _adult_filter_report --include=*.py` returns only the filter itself and
two stale copies; `grep -n adult errlog_step7.py` returns nothing. The report has **no consumer**
and the prose asserts one — the same shape as the `_add_sports_attrib.py` docstring that contradicted
the constant two lines below it. It matters because a warm re-run **overwrites** the report with
`dropped 0`, which is the 2026-09-14 marker-retraction shape reached through a report instead of a
marker: the second run does not merely no-op, it **retracts the first run's evidence**. Harmless
today only because nothing reads the file — luck, not design. Mitigated in-run by restoring the
pre-filter snapshot and re-running the pass **cold**, with the cold and warm end states
**parsed-diffed** at 0 rows differing (byte-identity over `_compiled_work.json` being an invalid
control, 2026-09-17).

### STEP 4.9 surfaced a published-data defect it did not cause — and the PROBE HISTORY is the finding (found 2026-09-22)

**522 event rows carry a FIRST+LAST PERSONAL NAME as the leading comma-segment of `address` — 86
distinct individuals**, LibCal contact/presenter names leaking through the address join into a
published column. It is two defects in one shape: a named private individual in a public
family-guide address field, and a string with **no place token**, which the geocoder cannot resolve,
so the row falls through to the `city_centroid` that the coverage spec says must never count as
evidence. 514 of the 522 carry pins from earlier runs, so this is an **old** leak every run has
preserved.

**Deliberately NOT fixed in-run**, and the reason is that two predicates failed within minutes of
each other:

* Probe 1, a bare person-name-shaped regex over digit-free addresses, returned `Youth Services`,
  `Northtown Library`, `Coon Rapids`, `Maple Grove` — rooms, branches and cities.
* Probe 2 added a gazetteer-city exclusion and an institutional-token screen and **still** returned
  `Garfield Avenue`, `Downtown Duluth`, `Mitchell Auditorium`.

**Name shape is not a discriminator for personhood.** An English place name has the same shape as
an English person's name, so no tightening of the pattern converges — the third probe abandoned
shape entirely and required **evidence that is not the name** (the Red Cow standard): the row's
`website` must be a `*.libcal.com/event/` or `events.griver.org/event/` URL. That is what 522/86 is
measured on. A predicate that failed twice in minutes is not one to edit 522 published rows on, and
an over-broad strip is the **wrong-merge error class** — unrecoverable, because STEP 4.9 skips
populated coordinates, so a damaged address with an intact pin never self-heals. The fix belongs at
the LibCal address join in `fetch_feeds.py`, which is a SHAPE change and the owner's call. The
measurement that makes it cheap is recorded: **424 of the 522 carry a gazetteer city as their
SECOND comma-segment**, so stripping only the leading segment preserves city resolution exactly.

**I then re-demonstrated the trap myself, live, in the same run.** A quick follow-up probe written
to test whether the leak was depressing city coverage used `^[A-Z][a-z]+ [A-Z][a-z]+,` and returned
**878** rows against the evidence-based 522 — it had silently regressed to probe 1, matching
`Maple Grove,` as readily as a person. The careful predicate and the careless one differ by a factor
of 1.7 on the same data. **Knowing the rule does not protect you from it**; only asking for evidence
that is not the name does.

**The hypothesis that probe was testing is FALSIFIED and that is worth as much as the leak.** The
address leak is *not* suppressing city resolution: **825 of the 878 resolve fine** via
`address_gazetteer`, because the city sits in the second comma-segment and the resolver reads it;
only 53 are unresolved, and **zero of them name Coon Rapids**. A plausible causal story connecting
two of the run's own findings was wrong, and checking cost one command.

### `sports_coverage.py`'s prose is now COMPUTED AT SOURCE — 2026-09-21's standing request is CLOSED (2026-09-22)

The 2026-09-21 entry ends by asking that the tripwire's fixed sentence (*"likely a STEP 2 sourcing
gap"*) be softened at source for registry teams, because an attribution row written by hand each
run is the obey-it-perfectly-forever rule this file keeps proving worthless. Done:
`attribute_shortfall()` reads the run's own structured reports and the **asymmetry is encoded
structurally** rather than restated in prose —

* **no report → prose UNCHANGED** (a team absent from the ESPN registry corroborates nothing);
* **every registered key reporting `NO_HOME_IN_WINDOW` or `EMPTY` → DOWNGRADE to `info`**;
* **anything else → STRENGTHENED**, never softened.

`OK`-with-rows deliberately does **not** downgrade: a source that fetched in-window home games none
of which reached `events.csv` is a real defect, and softening it would use the fix to hide the thing
the tripwire is for. `SOURCE_KEYS` values are **tuples and ALL must report** — a football schedule
saying "no home game" says nothing about basketball, and a single-key map would have mis-attributed
the Gophers. This run's 3 shortfalls resolve two ways on one evidence structure: **Minnesota United
downgrades to `info`** on `espn_mnufc`'s `NO_HOME_IN_WINDOW` (*"13 home games total, 0 in window"* —
the schedule **parsed**, which rules out a fetch failure presenting as a zero), while **Mankato and
St. Cloud State stay warnings** because neither is in the registry and nothing corroborates their
zeros.

**`test_sports_coverage.py` 15 → 34 passed, and FOUR OF THE NEW CASES WERE INITIALLY GREEN FOR THE
WRONG REASON.** A fail-on-purpose pass predicted 7 red under the remove-the-downgrade mutant and
produced **4**. The cause is a shape worth naming: an assertion like `"ERROR" in desc` is satisfied
by **both** branches, because the downgraded prose cites the status too — so it could never fail
under the mutant its *name* claimed to pin. Exactly the 2026-09-21 `NA_DIFFER` and `Black Tie Family
Gala` shape, arriving through a *substring* rather than through an unrelated rule. Each was conjoined
with a **branch-discriminating** phrase (`"TRUE NEGATIVE" not in desc`, `"likely a STEP 2 sourcing
gap" not in desc`) and re-verified RED. Five mutants were then run and every one matched its
predicted case-name list. **Predict the list before running the mutant** — comparing 7 to 4 is what
found this, and a pass/fail count could not have.

### A fail-on-purpose harness that mutates a file IN PLACE can silently test the WRONG CODE (found 2026-09-22)

New to this project, and it undermines every in-place mutation harness the file recommends.
**CPython invalidates a `.pyc` on `(mtime_seconds, size)` only.** The `SOURCE_KEYS`-typo mutant is
**length-preserving** (`United` → `Untied`), so restoring the original produced a file of identical
size within the same second, and the stale bytecode was reused: the RESTORED line reported **25/9
on a file proven byte-identical to the passing original.**

It failed in the safe direction here — a spurious red on the control. **The dangerous direction is
available on the same mechanism**: a length-preserving mutant that runs against stale bytecode
reports **GREEN**, which reads as "the suite does not pin this" and invites deleting a test that was
fine. Re-run under `python3 -B`, all five mutants reproduced and RESTORED came back 34/0.

**Any in-place mutation harness must disable bytecode, or the control is a coincidence.** Note how
well this hides: the harness is *correct*, the tests are *correct*, the mutation is *correct*, and
the interpreter's cache invalidates on a heuristic that a careful mutant happens to defeat. It is
the 2026-09-06 `>/dev/null 2>&1 &&` finding — a control that passes (or fails) without observing
what it claims to observe — reached through the runtime instead of the shell.

### Coverage: Coon Rapids deepened to 5/8, and it is NOT the address leak (2026-09-22)

`mn_coverage` returned **57** warnings (small city 45, major suburb 11, core metro 1), attributed
in the order the 2026-09-16 entry prescribes before anything was read into it: **0 fetch errors
across 68 dispatched sources** rules out a dead feed. The sole core-metro shortfall is **Coon Rapids
at 5 against the floor of 8**, deepened from the carried 7/8 — its 5 rows are 4 evergreen venues
plus a single dated event. The obvious hypothesis (the LibCal person-name address leak, whose
highest-volume systems include `anokacounty`) was tested and **falsified**: zero of the unresolved
rows name Coon Rapids. Recorded as an open question for the next run rather than logged as a new
finding, because adding one post-STEP-7 would cost the full documented cascade for a row that
changes no artifact.

### Image monoculture series, 2026-09-22 — a departure in the GOOD direction (read as three numbers)

`site_photo` **1,131**, `curated_category` **4,626**, dataset **6,708** rows (curated 871,
wikimedia 52, facebook 23, og_image 5). Distinct image URLs **1,115**; most-used image covers
**471**. Against 2026-09-21 (1,104 / 4,719 / 6,784; distinct 1,100; most-used 475) that is
`site_photo` 16.3% → **16.9%** and `curated_category` 69.6% → **69.0%** — **up in share AND in
absolute while the denominator fell**, attributable to STEP 4.5's 284 upgrades.

The 2026-09-21 entry states the series' own baseline expectation as *"flat shares, falling
absolutes, `stop_reason deadline` every run"* and says a departure from **that** is the signal. This
is a departure, and it is benign — but it is worth logging precisely because the entry promised to
treat departures as signals, and a rule that only fires on bad news is not a rule. STEP 4.5 still
reported `stop_reason: deadline` (attempted 163, upgraded 284, of which the large majority were
already correct from an earlier invocation this run — the `warm` counter, 2026-09-17's pair-reading
lesson again), so the third clause of the expectation held.

Three further 4.5 findings were logged this run: a **permalink flood in selection**, a **UA 403 on
the asset byte-check** (the verification the 2026-09-14 entry mandates is itself reachable only by
an agent the host accepts), and the **rejection ledger keying on EXACT URLs**, so a site that serves
the same bad asset under a query-string variant is re-fetched forever. Wikimedia applied its
converged **0** for a sixth consecutive run.

### Corrections and retractions carried out of the 2026-09-22 run

* **RETRACTED — "a subagent silently substituted URLs."** That claim does not survive re-checking
  and should not be cited. The rule it was attached to (verify a subagent's outputs against the
  source) stands on its own evidence elsewhere in this file.
* **The 2026-09-21 claim that `sports_dedup.py`'s "survivor is always the anchor regardless of
  `completeness()`" is WRONG as written** — read the helper before relying on that sentence. This is
  the prose-is-unasserted-by-construction rule landing on a section written the same day as the code
  it describes.
* **`frugal_scrub.py`'s "Frugal Friday" KEEP count is 2, not 9.** The rule is unaffected (match
  `TCFM`/`FRUGALMOM`/`frugal mom`, never bare `frugal`); only the number was wrong.
* **`geocode_pass.py` takes NO argv.** It resolves `_compiled_work.json` from `MSP_WORKDIR` or its
  own folder, so the 2026-09-15 rule *"invoke every `_compiled_work.json`-consuming helper with the
  path explicit"* is **inapplicable to it** — a path passed there is silently ignored, which is the
  worse half of that finding wearing the remedy's clothes. Its `len(key) > 6` length floor is also
  what makes a 6-character address `Online` a legitimate NON-LOOKUP rather than a suppressed row.
* **`build_guide.py` writes `deals.csv` and `volunteer.csv`**, not `meal_deals.csv` /
  `volunteer_opportunities.csv`. The category *keys* carry the long names and the *files* do not;
  anything reading the artifacts by category name opens a file that does not exist.
* **`events.griver.org` is a self-hosted LibCal instance with ~30 undocumented `griver_*` branch
  cids.** Recorded so a later run does not re-derive them, and because the sub-calendar fan-out that
  fixed `washco_libcal` (2026-09-16) is the shape that applies here if it is ever capped.
* **The `ensure_ascii` byte-delta identity reproduced a second time** (3,979 × 6 − 10,999 = 12,875),
  which is the 2026-09-17 finding confirmed on independent data: a byte delta over an intermediate
  that resolves to an exact arithmetic identity is a serialization artifact, not a data change.
* **`_probe_sportsdedup.py` is a stranded scratch file at the folder root that could not be
  deleted.** It is NOT a sanctioned pass and not a stranding recurrence — presence is not
  endorsement. The next STEP 1 audit must not read it as either.
* **The owner edited `deals.csv` between runs (commit `47a661e0`) and the pipeline reproduced that
  edit BYTE-IDENTICALLY.** Two independent directions agreeing, and it is what makes the rebuilt
  base safe to trust after the STEP 1 rebuild above.

**STEP 1 feature-grep additions from this run:** `base_from_csvs.py` (as a helper, and its
existence); `bar crawl` and `_adult_filter_report` (`adult_events_filter.py`); `SOURCE_KEYS`,
`TRUE_NEGATIVE_STATUS` and `attribute_shortfall` (`sports_coverage.py`); `len(key) > 6` and
`city_centroid` (`geocode_pass.py`); `EVENT_PERMALINK`, `EVENT_PERMALINK_Q`, `is_event_permalink`,
`is_usable_image`, `BAD_TOKENS`, `GATE` and `apply_curated_override` (`step45_site_photo.py`).

### CLOSED 2026-09-23: STEP 7 now REGENERATES `_run_summary.json` instead of proving it fresh

The 2026-09-22 blast-radius entry ends with a recommendation rather than a fix: *"the cheaper
structural fix is to stop the marker being inheritable at all — have STEP 7 itself regenerate it
from the built CSVs at the top of the step (the counts are read from the artifacts either way, so
nothing is lost), which makes the staleness unreachable rather than detected."* Applied this run as
`_mk_run_summary_0923.py`, and it was not hypothetical: the carried marker was **2026-09-22
07:27:27** against a `_feedpull_all.json` watermark of **2026-09-23 03:13:08**, i.e. it *would*
have tripped the section-0 assertion and suppressed 68 feed rows, 11 deal-yield rows, the
image-backfill row, the coverage rows and all 64 findings in order to prevent one stale row.

**COUNTS ARE READ, NEVER TYPED**, and that is the load-bearing half. `errlog_step7.py` asserts the
marker's counts row-by-row against the same five CSVs, so a typed number is a hand-maintained
duplicate of a value already on disk — the 2026-09-06 phantom-delta shape. The generator opens
`events.csv` / `parks.csv` / `deals.csv` / `volunteer.csv` / `restaurants.csv` under the long
category KEYS (the 2026-09-22 filename correction) and counts rows. STEP 7 then exited 0 with all
four ASSERTED lines: `ical_feed_pull` 68 == 68 dispatched sources, `deal_source_yield` 11 == 11
sources, `image_backfill` exactly 1 (`stop=deadline`), `run_summary` exactly 1 with counts matching.
`error_log.csv` 4,262 → **4,407 (+145)**, 105 info / 40 warning, CRLF 4,408 / bare LF 0, blob
`aa06e3096b64`. Promote this into `errlog_step7.py` itself so the next run inherits the fix rather
than the diagnosis.

### The STEP 4.4 checkpoint is a FREE before/after control on the whole enrichment half (2026-09-23)

SKILL.md:1166 mandates a `feed_checkpoint` info row and — per the six-run `ical_feed_pull` lesson —
nothing enforces it, so it is the shape that lapses silently. Two things about how it was written
this run are worth more than the row.

**It was sourced from the REMOTE COMMIT HISTORY, not from this run's recollection of publishing.**
A run's own memory of having published is the weakest available evidence that it did; the commit
list is a two-request check. Checkpoint `c6b6b870db` at 08:34:40Z carries `msp_family_guide.json` at
blob `5554ffe2a40e`, **6,614,090 bytes** — a COMPLETE feed, not a stub, which is the property that
makes it a safety net (if the run dies during enrichment, that commit stays the live feed and Base44
stays fully served).

**And the checkpoint/final blob pair is a control nobody has to build.** Final publish `48facc481a`
at 09:24:22Z carries blob `f5972378c160`, 6,617,709 bytes. **THE TWO BLOBS DIFFER (+3,619), AND
THAT IS THE USEFUL PART**: a final feed byte-identical to its own checkpoint would mean every
enrichment pass between them no-opped — the "nothing changed vs nothing ran" ambiguity this project
keeps resolving after the fact. Note that byte comparison is **VALID here and invalid over
`_compiled_work.json`** (2026-09-17): both sides are the same published artifact written by one
writer with fixed settings, which is exactly the distinction that entry draws.

### Reading the play-cafe titles REDISCOVERED a settled question — and the table is why that was cheap (2026-09-23)

The stem probe that found Sovereign Grounds and the Peak Café group returned **four** Edinborough
rows this run — `Adventure Peak at Edinborough Park`, `Edinborough Park PlayPark`, `Edinborough
Park`, and `Edinborough Park - Indoor Playground` — three of them sharing `7700 York Ave S` and one
carrying a non-place address (`Edinborough Park, Twin Cities, MN`) with an `exploreminnesota.com`
listicle URL and blank coordinates. It reads exactly like unrepaired fragmentation.

It is not. `step8_venue_repair.KEEP_APART` **already settles all four by name**: the park plus two
distinct attractions with separate `edinamn.gov` pages (the Lake Phalen Beach precedent — same
address is not same destination), and the listicle stub held at REVIEW because its title does not
say WHICH attraction it means, so folding it either way asserts a fact the source does not state.
**This is the argument for recording rejected candidates next to accepted ones, paid off**: without
the table a later reader re-derives the judgement from scratch each run, and the cheap wrong answer
(same address → merge) is available every time. Reading the entry cost one grep; the wrong merge
would have silently deleted a real destination.

One genuinely open item inside it, carried not new: the PlayPark pin (44.8650, -93.3350) still sits
~1 km west of the other two (44.864, -93.32145) at the same street address. It persists because
**STEP 4.9 skips populated coordinates**, so a wrong pin on a correctly-separate row never
self-heals — already logged, still unfixed, and it needs a blanked lat/lon rather than a merge.

### Image monoculture series, 2026-09-23 — a SECOND consecutive benign departure

`site_photo` **1,118**, `curated_category` **4,517**, dataset **6,582** rows (curated 870, wikimedia
52, facebook 20, og_image 5). Distinct image URLs **1,109**; most-used image covers **460**; and
**ZERO blank `image_url` for the first time**. Against 2026-09-22 (1,131 / 4,626 / 6,708) that is
`site_photo` 16.9% → **17.0%** and `curated_category` 69.0% → **68.6%**.

The series' stated baseline expectation (2026-09-21) is *flat shares, falling absolutes,
`stop_reason deadline` every run*. This is the **second consecutive departure** from it, in the
benign direction, attributable to STEP 4.5's 288 upgrades — logged because **a rule that only fires
on bad news is not a rule**. The third clause held: `stop_reason: deadline`. Wikimedia applied 0 for
a **seventh** consecutive run against a warm 833-entry cache — the documented converged state; what
remains unphotographed is library programming, which has no venue article to find.

### `FREE_SRC` measured ENTIRELY unreachable for a fifth time, and the remedy stays deferred (2026-09-23)

**38 blank `price_type` values reached the build** — a schema-v3.1 violation, caught by reading the
built CSV's value distribution BY HAND, because nothing in the pipeline asserts a closed enum. Reach
was measured **over the rows the rule would fire on** rather than over the corpus (the 2026-09-18
denominator rule): **0 of 38** carry a `src:` token while **17 of 38** carry the `library` content
tag. Fifth measurement, same verdict — not *mostly* unreachable, **entirely**.

Remedy deliberately still deferred, for the standing asymmetry: `Varies` makes no false claim, while
a wrongly-stamped `Free` is a factual claim a family acts on at a ticket counter. Resolved
conservatively (32 `Varies`, 6 `Paid` on quoted amounts); final distribution **Paid 725 / Free 1,648
/ Varies 4,209**, no non-schema value. The fix forced a **rebuild**, which forced a **STEP 5.5
re-run** per the documented ordering: `end_date added=28`, continuing the declining series
130 → 89 → 74 → 52 → 40 → **28**, which is a property of the FEED (the window is deep into weekly
library programming, single-date by nature) and not a defect — confirmed by the three documented
health checks, suite 20/20 and a warm dry-run reporting `added=0 kept_existing=28`.

### The `ensure_ascii` byte-delta identity reproduced a THIRD time (2026-09-23)

STEP 8 venue repair applied **+0 merges** — the documented goal state, distinguished from a no-op by
all 13 hand-table groups reporting per-group counts (each matching exactly 1 row: last run's merges
held), 0 closed venues dropped. It then produced a **−12,495 byte** delta against those +0 merges,
exactly the shape 2026-09-17 says to investigate, and it resolved by **MEASUREMENT rather than
inference**: the parsed control returned TOTAL field-level differences **0** with all row counts and
top-level keys SAME, and the byte delta reproduced as an exact arithmetic identity
(**3,867 `\uXXXX` escapes × 6 − 10,707 non-ASCII bytes = 12,495**). Third independent reproduction
(2026-09-17, 2026-09-22, 2026-09-23). Byte-identity over `_compiled_work.json` remains an INVALID
control.
