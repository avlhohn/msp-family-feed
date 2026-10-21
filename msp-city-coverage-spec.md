# City Resolution & Coverage Spec — MSP Family Guide

Adopted 2026-08-19. This file **supersedes** three things in `SKILL.md`. Read it during
STEP 2 and STEP 8 of every `msp-family-guide-daily` run.

| Supersedes | Replaced by |
|---|---|
| Any regex that parses a city out of an address by requiring a literal `", MN"` | §1 gazetteer resolution |
| STEP 8 bullet "Any cities where event count was notably low (< 3 events found)" | §2 population-tiered coverage |
| Ad-hoc per-run feed rediscovery | §3 + `event-source-calendars.md` |

---

## Why this changed

The "low coverage cities" number was mostly a measurement artifact, not a real content
gap. On the 2026-08-19 data the old check reported 99 low-coverage cities. Investigation
of that number found:

- 54 of 908 events had **no parseable city at all**, because the regex required a literal
  `", MN"` in the address string.
- `St. Paul`, `Saint Paul` and `St Paul` were counted as **three separate cities**.
  Combined they had 99 events — statistically tied with Minneapolis for the largest city
  in the dataset — yet each fragment individually looked like a coverage gap.
- 34 **phantom cities** ("Downtown Moorhead", "Centennial Library", "Hennepin County")
  absorbed 64 events between them.

Worse, the old check was structurally blind to the gap that actually matters. It could
only flag cities that already appeared in the data, so a city with **zero** events
contributed zero rows and was therefore invisible. The most important gap was the one the
check could not see.

---

## §1 — City resolution

Use `mn_city_resolve.py`. Never parse cities with a bespoke regex again.

```python
import mn_city_resolve as M
by_name, cities = M.load_gazetteer()
city, source = M.resolve_city(row, by_name, cities)
```

`mn_city_gazetteer.json` holds 986 Minnesota municipalities (939 with population), built
once from a single OSM Overpass query. It is **cached on disk** — do not re-query Overpass
per run. Rebuild only if municipalities are visibly missing:

```
[out:json][timeout:120];
area["ISO3166-2"="US-MN"][admin_level=4]->.mn;
(node["place"~"^(city|town|village)$"](area.mn);
 relation["place"~"^(city|town|village)$"](area.mn);
 way["place"~"^(city|town|village)$"](area.mn););
out center tags;
```

### Precedence: the address wins

A street address that names a **real gazetteer municipality** beats a geocoded point.
This was validated against 207 address/coordinate disagreements on 2026-08-19; in every
sampled case the address was right and the coordinate was wrong. "Littles and Lattes Play
Cafe, 15670 Edgewood Dr, Baxter, MN" geocoded into Minneapolis, 171 km away. Lake Carlos
State Park (Alexandria) was off by 77 km; River Bend Nature Center (Faribault) by 88.8 km.

So a large address/coordinate gap is a **bad-coordinate signal, not a bad-city signal**.
Beyond `BAD_COORD_KM = 25.0` the resolver keeps the address city and returns
`coord_city_mismatch`, which STEP 7 should log as a re-geocode candidate. That surfaced 19
genuinely wrong coordinates on its first run.

### Provenance values

| Source | Meaning |
|---|---|
| `address_gazetteer` | Address named a real MN city. Authoritative. |
| `coords_nearest` | No usable city in the address; nearest plausible centroid. |
| `coord_city_mismatch` | City trusted, but stored lat/lon is >25 km away — **re-geocode the row**. |
| `centroid_circular` | Coordinates were themselves a city centroid. The city is an INPUT, not a finding. |
| `unresolved` | Neither signal produced a municipality. |

**`centroid_circular` must never count as evidence of coverage.** If the coordinate was
derived from the city, then using it to prove the city has events is circular reasoning.
`mn_coverage.py` already excludes it; any new consumer must too.

### The gazetteer is the authority, not the word filter

`_NOTACITY` rejects segments containing `park`, `center`, `library`, `county` and similar.
Applied naively it **destroys real municipalities**: Brooklyn Park, Brooklyn Center, Saint
Louis Park and Columbia Heights all contain banned words. This bit us — "8001 109th Ave N,
Brooklyn Park, MN 55443" resolved to *Osseo*.

Correct order: check the gazetteer **first**; apply `_NOTACITY` only to segments the
gazetteer does not recognize. Fixing this raised `address_gazetteer` from 1,930 to 1,962
rows in one pass.

### Regression tests

`test_city_resolve.py` holds 18 cases, every one a real observed failure, not a synthetic
example. Run it after any resolver edit:

```
python3 test_city_resolve.py
```

It must print `22 passed, 0 failed`. (18 when this spec was adopted; four cases were
added later. Verified 22/22 on 2026-08-25.)

---

## §2 — Population-tiered coverage check

Use `mn_coverage.py`. It replaces the flat "< 3 events" warning, which held Hanska
(pop 400) to the same standard as Bloomington (pop 83,000) and so parked ~70 tiny towns
permanently on the warning list as noise.

| Tier | Population | Minimum events per ~6-week window |
|---|---|---|
| core metro | 50,000+ | 8 |
| major suburb | 15,000–49,999 | 4 |
| small city | 5,000–14,999 | 2 |
| town | under 5,000 | reported, never warned on |

**Walk the gazetteer, not the dataset.** This is the whole point: iterating over cities
rather than over rows is what makes a zero-event city visible. Iterating over rows can
never surface one.

On first run this immediately exposed **Brooklyn Park — Minnesota's 6th largest city, pop
75,781 — with 1 event**, plus Richfield, Fridley, Brooklyn Center, New Hope, South Saint
Paul and Lino Lakes at **zero**. All were confirmed as genuine content gaps (zero mentions
anywhere in the dataset), not resolver artifacts.

STEP 8 should report per-tier: number of cities, how many meet target, how many have zero
events; then list the shortfall cities by population descending.

---

## §3 — Feeds

Maintained in `event-source-calendars.md`, which now carries verified/dead status per
source. Feeds decisively outperform keyword search in thin markets: Visit Bemidji returns
15 events and Brainerd 21, against roughly 1 event each from keyword-searching the same
towns.

Sources added 2026-08-19, all personally fetched and confirmed to return in-window events:
Brainerd, Winona (CVB + library), Faribault, Rochester, Willmar, Bemidji; Richfield,
Maplewood and South St. Paul city calendars; and the Hennepin, Ramsey and Anoka county
library systems, which between them cover every one of the zero-coverage suburbs above.

Three handling rules that will silently corrupt results if skipped — full detail in
`event-source-calendars.md`:

1. **BiblioCommons ignores `startDate`/`endDate`.** Filter the window client-side.
2. **Never hardcode BiblioCommons branch codes.** Join to the `/locations` endpoint, which
   carries street addresses, and run those through `mn_city_resolve`.
3. **iCal feeds sort ascending from ~4 weeks in the past** and truncate on fetch, so a
   partial read reports zero in-window events. Read to the END, or use a date-bounded
   endpoint where one exists.

---

## §4 — Trust rule

Do not accept a subagent's or a summarizer's count for any feed or mapping. Both failed on
2026-08-19: a subagent declared Richfield and Maplewood dead after probing the wrong URL
(`iCalendar.aspx`, which is a subscription info page, not a feed — both cities are live
via `RSSFeed.aspx`), and a fetch summarizer invented a BiblioCommons branch mapping,
reporting `AF` as Anoka and `FR` as Fridley when the authoritative endpoint gives Arvonne
Fraser and Franklin, both in Minneapolis. Verify personally, and confirm cited events fall
on or after the run date.
