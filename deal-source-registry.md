# Deal & discount source registry

Companion to `event-source-calendars.md`, same contract: **this file is the verified list.**
Do not rediscover deal sources ad hoc each run, and do not re-probe the dead ends.

Adopted 2026-08-22 after a diagnostic run found the discount-activity cluster
(SKILL.md §"Deals & discounts", part (b)) producing effectively nothing:
0 park deals of 815 rows, 9 event deals of 2,181, 36 restaurant deals of 394.

---

## The bug that made this file necessary

SKILL.md lines 236 and 257 instruct: *"Use the same two-month date window as the rest of
STEP 2"* and *"Apply the same MN-geo and date-window guards."*

Applied to cluster (b) that instruction is self-defeating. Cluster (b) is **almost entirely
standing programs with no date** — Como Zoo is always free, Mia is always free, smARTpass
runs year-round, Museums for All is year-round, the Science Museum's $3 military rate has no
end date. None of these have a date inside any two-month window, so the window guard
discards precisely what the cluster was written to find.

**Rule: standing deals are exempt from the STEP 2 date window.** They follow the same
pattern SKILL.md already uses for "standing/recurring attraction" seed rows (lines 546, 610):
carried every run, no date required, `deal_expiry` blank meaning *runs indefinitely*.

A blank `deal_expiry` is **valid data, not a defect.** Never warn on it, never age the row
out. Only populate it when the source states an actual end date.

---

## Source roles — a source can be healthy and still contribute nothing here

Not every good source belongs in `standing_deals.csv`. Three distinct roles, and `deals_yield.py`
treats them differently on purpose:

| Role | Meaning | Zero rows means |
|---|---|---|
| **Table contributor** (`YEAR_ROUND`) | Publishes venue-level standing discounts | **Real failure — warn** |
| **Non-table** (`NON_TABLE`) | Fetched every run, but feeds STEP 2 events or corroborates another source | Expected — never warn |
| **Retired** (`RETIRED`) | No longer fetched; historical rows keep resolving | Expected — never warn |

Filing a non-contributor under `YEAR_ROUND` makes it warn on **every run forever**, and a
permanent warning is worse than no warning — it teaches the reader to skim past the whole
block, which is precisely how the original silent failure survived unnoticed for months. Two
sources were misfiled this way on the day the check was written and both are now reclassified:
Upparent (403) and Thrifty Minnesota (an events site, not a discount list).

---

## Verified live sources

| Source | URL | Fetch | Yields |
|---|---|---|---|
| Twin Cities Frugal Mom — discount guide | `twincitiesfrugalmom.com/twin-cities-discount-guide-families/` | **RETIRED 2026-08-28 — do NOT fetch** | See "Retired sources" below. |
| Twin Cities Frugal Mom — kids eat free | `twincitiesfrugalmom.com/deals-events-calendar/kids-eat-free-list/` | **RETIRED 2026-08-28 — do NOT fetch** | See "Retired sources" below. |
| MELSA smARTpass | `smartpass.melsa.org` | OK, static | ~45 partner venues; family-relevant: Children's Theatre Co, Stages Theatre, Circus Juventas, Mia, ASI, Hennepin History, Walker |
| Thrifty Minnesota | `thriftyminnesota.com` | OK, static — **NON-TABLE** | Dated events (free outdoor movies, indoor playgrounds, Cars & Caves). Route these to STEP 2, not the overlay. Probed 2026-08-22: yields **no** venue-level standing discounts. |
| Thrifty MN — free state park days | `thriftyminnesota.com/free-admission-to-minnesota-state-parks/` | OK — **NON-TABLE** | Only mirrors the four DNR dates, which `dnr_free_park_days` already covers. Useful as independent corroboration (it confirmed all four 2026 dates), not as a source of rows. |
| MN DNR free entrance days | `dnr.state.mn.us/state_parks/free-entrance-days-minnesota-state-parks.html` | OK | 4 dates/yr |
| Kids Bowl Free | `kidsbowlfree.com` | Landing OK; center list at `/all_centers.php` needs a state filter | 2 free games/day, summer season |

### Retired sources — do not fetch, do not re-add

- **Twin Cities Frugal Mom** — both URLs (`/twin-cities-discount-guide-families/` and
  `/deals-events-calendar/kids-eat-free-list/`). **Retired 2026-08-28 at the owner's (Aimee's)
  request.** Reason: her roundups mix two very different things. Most of it is *publicly-true
  venue facts she merely aggregated* — Como Zoo is free, Mia is free, the Museums-for-All /
  MNHS income-qualifying rates, the Sunday/Tuesday kids-eat-free restaurant nights — none of
  which originate with her. But a handful of rows were deals **exclusive to her**: her own
  branded, negotiated discount codes (`TCFM`, `FRUGALMOM25`, `TCFMB$2OFF`), which were reaching
  the live app and should never have been republished. Rather than police the mix every run, we
  stop fetching her entirely. The public facts already captured **stay in `standing_deals.csv`**
  and keep being applied by the overlay; source any NEW venue discounts or kids-eat-free nights
  from the venue / its CVB directly. The four branded-code clauses were stripped from
  `standing_deals.csv` on 2026-08-28 (Zero Gravity Adventure Park, whose only deal was her code,
  was removed outright). In `deals_yield.py` both keys were moved from `YEAR_ROUND` to `RETIRED`
  so historical rows still resolve but no fetch is expected and no warning fires.

### URLs corrected 2026-08-22
- `twincitiesfrugalmom.com/kids-eat-free-twin-cities/` → **404.** Correct path is
  `/deals-events-calendar/kids-eat-free-list/`. The old URL was in SKILL.md and failed
  silently every run.
- `dnr.state.mn.us/state_parks/free_park_days.html` → **404.** Correct page is
  `free-entrance-days-minnesota-state-parks.html` (hyphens, not underscores).

### Dead ends — do not retry
- **museums4all.org** — returns **403** to `WebFetch`. Cannot be used directly. Get Museums
  for All participation second-hand from the Frugal Mom discount guide, which records it
  per-venue (it is the "$4 adults / free under 17 if income-qualifying" line on the MNHS
  sites, and the Science Museum's $3 rate).
- **familyfuntwincities.com** — JavaScript-rendered, already recorded in SKILL.md.
- **upparent.com** — returns **403** to `WebFetch` (probed 2026-08-22; it was listed as a
  live source earlier the same day on the strength of the URL alone, before anyone actually
  fetched it). Its kids-eat-free coverage overlaps the Frugal Mom kids-eat-free list, which
  fetches fine, so nothing is lost by dropping it. `upparent` stays in `deals_yield.py`'s
  `SOURCE_KEYS` only so historical rows keep resolving; it is **not** a nightly fetch and
  must not be listed as one.

---

## 2026-10-01 kids-eat-free scrape (TC metro + greater MN)

Ran a fresh scrape for net-new kids-eat-free / discounted restaurant deals across the metro
and outstate (Rochester, Duluth, St. Cloud, Mankato), excluding the ~29 kids-eat-free venues
already in `standing_deals.csv`. Every candidate was checked on the **venue's own page** under
the quotation rule — aggregator listings (`twincitieskidsclub.com`, `kidseatfree.io`,
`familyfuntwincities.com`, `upparent.com`, `how2mom.com`, Yelp, `rochesterlocal.com`,
`kroc.com`) were used only to find candidates, never as a source of terms.

**Exactly one net-new deal survived own-page verification: Outback Steakhouse.** Added to
`standing_deals.csv` and to `SOURCE_KEYS` in `deals_overlay.py` (`outback.com` →
`venue_direct_kids_eat_free`), quoted verbatim from `outback.com/specials`:
*"Join us for Kids Eat Free Mondays, Tuesday Tails, Walkabout Wednesdays, and $5 Bevvy
Thursdays."* Blank `deal_expiry` (standing program).

**The invisible-deal gap was CLOSED 2026-10-01 — 6 Outback MN locations seeded as restaurant
rows.** This was the Kids Bowl Free pattern again: `deals_overlay.py` only stamps existing rows
and reported Outback under *"NO ROW TO ATTACH TO (add as seed venues)"*, creating nothing —
*a deal with no venue row is invisible.* The 6 real MN locations (Bloomington, Coon Rapids,
Inver Grove Heights, Rochester, Hermantown, Maplewood) were pulled from the official
`locations.outback.com` locator, Census-geocoded, MN-bbox-validated (never fabricated), and
appended to `restaurants.csv` (461 → 467 data rows, CRLF preserved, existing bytes untouched).
Each is `price_type=Varies`, `image_source=curated_category` (restaurant-pool URLs already in
`curated_images.csv`, so `curated_repoint.py` won't flag them as orphaned), `has_deal=False`
with a blank `deal_description` — the overlay stamps those at the nightly. `restaurants.csv`
published to the live repo and verified by git blob SHA-1 (`205b9e8398ae`) keyed on the explicit
head commit `8575ec5d34fc`.

Dry-run and real-run of `deals_overlay.py` against the new file both confirm the attach:
`matched: 6, applied: 6`, Outback no longer in the unmatched list, and the stamped
`deal_description` is the verbatim `outback.com/specials` quote with `deal_source=
venue_direct_kids_eat_free`. The deal goes fully live at the next nightly, when
`base_from_csvs.py` rebuilds the carried base from the published CSVs, the STEP 4.35 overlay
stamps the 6 rows, and `build_guide.py` writes them into `msp_family_guide.json` (the artifact
Base44 ingests). No mid-day full-build cascade was run — seeding into the carried base and
letting the nightly attach the deal is lower-risk than an unattended build.

### Dead ends from this scrape — do not retry without a primary-source change

These were checked on their own pages and produced **no verifiable current deal**, so per the
quotation rule no row was written:

- **Perkins** (`perkinsrestaurants.com`) — own pages return **403** to WebFetch; the
  "kids eat free" claim lives only on aggregators. Unverifiable.
- **Denny's** (`dennys.com`) — **403** to WebFetch. Unverifiable.
- **Old Chicago** — own specials page **404**.
- **IKEA** (Småland / restaurant) — own pages fetch but state **no kids-eat-free term**.
- **Famous Dave's** — own site's kids-eat-free promo is **WA/UT locations only**, not MN.
- **Hy-Vee** — "kids eat free" is store/market-specific, not a current standing MN-wide term
  on the corporate page; aggregator claims are stale.
- **Own sites silent / no current term:** Tamarack Tap Room, Crooked Pint Ale House,
  Cowboy Jack's, Victoria's Ristorante, Big Louie's. Each has a kids-eat-free claim on
  aggregators but nothing quotable on its own page.

---

## Seasonality — expect legitimate zeroes

Some cluster (b) items are genuinely absent from an Aug–Sep window. A zero here is correct
and must not be treated as a failure:

- **MN DNR free park days 2026:** Jan 19, Apr 25, Jun 13, Nov 27. None fall in Aug–Sep.
- **Marcus "Kids Dream"** is a summer film series; over by late August.
- **Kids Bowl Free** is a summer program.
- **Ice Castles** (Nov–Feb), **Great Pumpkin Trail** (Sep–Oct).

This is exactly why the yield check must be **per source**, not one aggregate number. An
aggregate hides "smARTpass returned nothing" behind "the seasonal ones are legitimately zero."

### Kids Bowl Free — RESOLVED 2026-08-25

`kids_bowl_free` warned on every run from 2026-08-23 to 2026-08-25. The cause was not a
fetch failure: `standing_deals.csv` had held 40 verified center rows since 2026-08-23 with
a correctly quoted description and a blank expiry. What was missing was **a venue row for
the overlay to attach each deal to**, so a fully-populated source contributed zero. *A deal
with no venue row is invisible* — check the join before re-probing the source.

`standing_deals.csv` stores **names only** (`venue_match,deal_description,deal_expiry,
source_url,verified_date`), and the §4 trust rule forbids taking an address map from a
fetch summarizer. So each center name was resolved through **Nominatim**, a primary
structured source. That doubles as the fabrication check: a venue that does not exist does
not resolve inside the MN bbox. **19 of 40 resolved and were seeded** with Nominatim's own
`display_name`-derived address; the source now contributes 19 rows and `deals_yield.py`
reports **0 warnings** for the first time.

**21 centers remain unseeded** and must not be given invented addresses: Drkula's 32 Bowl,
Bogart's Entertainment Center, Prairie Grill & Bowl, McPete's Sports Bar & Lanes, Blackduck
Lanes, Blainbrook Bowl, Incline Station, Bowlmor Lanes, J-Mo's Bowl, Tuttle's Eat Bowl Play,
Isle Bowl & Pizza, Bennington's Entertainment Center, Wow Zone, Medina Lanes, Mermaid Lanes,
Sparetime Entertainment, Trailhead Grill & Lanes, Bowlocity, Country Club Lanes, Tracy
Lanes, Splitrocks. They are real businesses that OSM does not carry under that exact name —
next attempt should pull street addresses from `all_centers.php?state=MN` and geocode
those, rather than geocoding a bare trade name.

### Open gaps — one source still warns, correctly (updated 2026-08-25)

`kids_bowl_free` and `marcus_kids_dream` were both **in season in August and contributing
zero rows.** Those warnings were the check working, not noise. Do not silence them — fetch
them.

- **`kids_bowl_free` — closed 2026-08-25.** See the section above. Note the diagnosis was
  wrong in an instructive way: this note assumed the source "has never been fetched into
  `standing_deals.csv`", but the 40 rows had been there since 2026-08-23. The missing piece
  was the venue rows to join them to. A zero-yield source is not always an unfetched source.
- **`marcus_kids_dream` — still open.** Needs its per-theatre summer schedule. If Marcus
  turns out to end in mid-August rather than end-of-August, narrow its `SEASONAL` range to
  `(6, 7)` rather than dropping the source.

---

## Venues named by the discount guide but MISSING from the feed — RESOLVED 2026-08-22

The first join matched 18 of 29 discount venues to existing rows. The rest had a verified
standing discount but **no row to attach it to.** Two separate causes, and only one of them
was a real gap:

- **Oliver H. Kelley Farm was never missing.** It was in the feed the whole time; the join
  used substring matching and `standing_deals.csv` says "Oliver Kelley Farm" without the
  middle initial. Fixed in `deals_overlay.py` with token-subset matching. Before blaming a
  seed list for a miss, check the matcher.
- The rest were genuinely absent and are now **seeded in SKILL.md with Nominatim-verified,
  MN-bbox-validated coordinates**: Crayola Experience (MOA) · FlyOver America (MOA) ·
  Minnesota State Capitol · James J. Hill House · Alexander Ramsey House · Minnehaha Depot ·
  Zero Gravity Adventure Park · Walker Art Center · Circus Juventas · Hennepin History
  Museum · Park Square Theatre.

Five being MNHS historic sites was a systematic gap, not five coincidences — the museum seed
list covered the flagship MNHS sites (History Center, Fort Snelling, Mill City, Split Rock)
but not the smaller house museums. SKILL.md's MNHS block now carries them.

**SteppingStone Theatre is deliberately NOT seeded.** A search result says it closed and
merged into Park Square Theatre in June; its geocode also returned a road centroid conflicting
with its 55104 zip. Unverified closure + unreliable coordinate = do not seed. Revisit only
with a primary source.

Two addresses I recalled rather than verified were both wrong, and WebSearch caught them
before they were written: Zero Gravity is **2292 Woodale Dr, Mounds View** (not Plymouth) at
`zerogravitymn.com` (not `zerogravitympls.com`), and Crayola Experience is **300 South Ave
Level 3** — the guessed 166 South Ave resolved to The North Face. Geocode from a verified
address string, never from memory.

---

## Deal terms must be quoted from the source, never reconstructed

When the eleven venues above were seeded, the first draft of their `standing_deals.csv` rows
was written from plausibility rather than from the page. Re-fetching the discount guide showed
all three of the guessed rows were wrong in substance:

| Venue | What was guessed | What the source actually says |
|---|---|---|
| Crayola Experience | "discounted advance tickets, free under 2" | **The discount no longer exists** — "my exclusive deal is no longer available due to changes in the Crayola Experience's ticketing system" |
| FlyOver America | "combo, MN-resident and military discounts" | 15% off general admission via a Bloomington Coupons coupon |
| Zero Gravity | "weekday and non-peak rates, toddler rates" | 50% off with code **TCFM**, any ticket except bundles, extras and Friday homeschool passes |

The Crayola case is the instructive one: a plausible-sounding invented discount would have
shipped a **live promise the venue does not honour** — worse than shipping nothing. Crayola
Experience therefore stays a seed venue with **no row in `standing_deals.csv`**. If a future
run is tempted to add one, the guide explicitly says the deal is gone.

The MNHS house-museum rows were also over-broad: they had inherited the flagship sites'
"Bank of America first-weekend / 6th-grade History Pass" language, which the guide does not
state for the smaller houses. They now carry only the two terms the source gives — free to
age 4, and $4 adult / free under 18 on the MNHS limited-income program.

**Rule: a `deal_description` is a quotation, not a summary from memory.** A discount code or
a percentage is a factual claim a family will act on at a ticket counter. If the page cannot
be fetched, write no row.

**SteppingStone Theatre's row was removed** for the same reason — it was carried as a
smARTpass partner, but the venue's standalone status is in flux (SKILL.md now lists it
confirm-only, producing in partnership with Park Square). A deal row for a venue with no seed
row would also have shown up as a phantom "missing seed venue" on every future overlay run.

---

## Routing rule

A standing deal is **an attribute of a venue, not a row of its own.** Do not create a
`meal_deals` row for "Como Zoo is free."

1. Join the deal to existing `events` / `parks` / `restaurants` rows by normalized venue
   name (strip punctuation, casefold, substring match on `title` then `address`).
2. Stamp `has_deal=true`, `deal_description` with the exact terms, `deal_expiry` only if the
   source states an end date.
3. Only if no row matches AND the deal is food, create a `meal_deals` row.
4. If no row matches and it is an attraction, log it to the missing-venues list above rather
   than inventing a row.

---

## Provenance: `deal_source` is destroyed at build (found 2026-08-26)

Run `deal_provenance_restore.py` as a **STEP 4.35 pre-pass, before `deals_overlay.py`.**

```bash
python3 bycat_shim.py deal_provenance_restore.py
python3 bycat_shim.py deals_overlay.py
python3 bycat_shim.py deals_yield.py
```

`deals_overlay.py` stamps a `deal_source` key on every row it touches, but `deal_source` is
not one of the 19 schema-v3.1 BASE fields and `build_guide.py:22` rebuilds each row as
`{k: it.get(k,'') for k in BASE}`. The key is therefore created by the overlay, consumed in
the same run, and **destroyed at build** — it never reaches the published CSV, so the carried
base arrives next run with it blank.

Both consequences are silent, and both matter to this registry:

- **The overlay stops being able to update its own rows.** Its `owned` carve-out exists so
  that an edit to `standing_deals.csv` actually reaches the live app on a re-run, and that
  carve-out tests `deal_source`. Blank means not-owned, so the overlay skipped every carried
  row — a no-op on precisely the rows it was written to refresh. **Correcting a wrong
  `deal_description` in this table would have changed nothing downstream.** Given the
  quotation rule above, that is the more serious half of the defect: the mechanism for fixing
  a bad quotation was itself broken.
- **The yield check warns forever.** `deals_yield.py` attributes by `deal_source`, so a source
  whose venues were all stamped on an earlier run reports 0. On 2026-08-26 `kids_bowl_free`
  and `frugalmom_kids_eat_free` both warned falsely; their real yields are 21 and 9. A
  permanent warning trains the reader to skim the block — the same failure the `NON_TABLE` /
  `RETIRED` classification exists to prevent.

The restore matches a stored `deal_description` against this table by **whitespace-normalised
full-string equality**. That is not the forbidden substring keyword scan: the stored text is a
verbatim copy of a table row, so exact equality recovers the original attribution rather than
inferring it. It refuses to guess — a description claimed by two sources is left blank, and so
is one that matches nothing (259 such rows on 2026-08-26, all row-level deals STEP 2 found
itself, correctly unattributed rather than a shortfall).

Measured 2026-08-26: 131 rows restored (`frugalmom_discount_guide` 95, `kids_bowl_free` 21,
`frugalmom_kids_eat_free` 9, `melsa_smartpass` 6), 0 ambiguous. Overlay stamping went 5 → 147
and yield warnings 2 → 0.

**Do not fix this by adding `deal_source` to `BASE`.** Base44 consumes the 21-column contract,
so widening it breaks a consumer outside this repo. The pre-pass gets the same result without
touching the contract.
