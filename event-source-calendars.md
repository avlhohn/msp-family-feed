# Event Source Calendars — MSP Family Guide

Verified 2026-08-19; **expanded 2026-08-20** (Washington County Library, Marshall and
Alexandria CVBs added; metro-county / regional library candidates and the city-gov
meeting-noise finding recorded). Every feed marked `VERIFIED` was fetched live with a raw
HTTP read (never a summarizer) and confirmed to return parseable events **in the forward
window** on the stated date. Feeds are worth far more than keyword search for thin markets:
Visit Bemidji returns 15 events and Brainerd 21, where keyword-searching those same towns
returned about 1 event each.

> **Why this expansion (2026-08-20):** the 2026-08-20 run's population-tiered coverage
> check (`mn_coverage.py`) still reported **78 shortfall cities** — 1 core metro (Brooklyn
> Park, 6/8), 21 major suburbs (Fridley, New Hope, Owatonna, Red Wing, Albert Lea, Hibbing
> and Saint Michael all at **zero**), and 56 small cities. The additions below target the
> two biggest clusters: east-metro suburbs (via the Washington County library system) and
> outstate regional hubs (via CVB iCal feeds). The single highest-leverage pattern remains
> the **county / regional library system** — one feed covers every branch city at once, the
> way Hennepin/Ramsey/Anoka already blanket the west and central metro.

Status values: `VERIFIED` (fetched, returned in-window events), `LIVE-NO-VALUE` (feed
works but yields nothing usable for a family guide), `DEAD` (do not retry — see reason).

> SKILL.md STEP 2 cites "the full annotated list in `event-source-calendars.md` §6" for
> outstate regional sources. That list is now **§1** below. This file had been missing
> from the workspace across several runs; it is rebuilt here from live verification
> rather than from the prior contents.

---

## 1. Outstate metro feeds

| City | URL | Format | In-window events |
|---|---|---|---|
| Bemidji | `https://www.visitbemidji.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | 26 (was 15 → 1 on `?ical=1`) |
| Brainerd | `https://calendar.brainerd.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | 8 — `SHORT`, span ends 2026-10-13; see §1.1 |
| Winona (CVB) | `https://visitwinona.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | **579** (was 30) |
| Winona (library) | `https://winona.lib.mn.us/events/list/?ical=1` | iCal | **DEAD — 403 since 2026-08-28, see §4** |
| Duluth (DECC) | `https://decc.org/wp-json/wp/v2/events?per_page=100` | WP REST JSON | 17 |
| Faribault | `https://www.visitfaribault.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | 12 (was 9) |
| Rochester | `https://www.experiencerochestermn.com/event/rss/` | RSS | 14 |
| Willmar | `https://willmarlakesarea.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | **250** (was 28) |
| Marshall | `https://visitmarshallmn.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | **90** (was 16) |
| Alexandria | `https://www.explorealex.com/wp-json/tribe/events/v1/events` | WP REST (Tribe) | **99** (was 30), span reaches END_DATE |
| Dodge Nature Center | `https://dodgenaturecenter.org/wp-json/tribe/events/v1/events` | WP REST (Tribe) | **57** (was 1) |

**DECC added 2026-08-29.** SKILL.md line 832 has mandated this source all along, but it had
never been implemented — `grep -ci decc` over the fetcher returned 0. A mandated source that is
*absent* rather than *broken* raises no error and is invisible to every yield and coverage
check, because those only inspect sources they already know about. **At STEP 2, diff SKILL.md's
mandated source list against the fetcher's dispatch table** rather than assuming a named source
is wired up. It is not an iCal feed: dates arrive as `YYYYMMDD` strings in `event_start_date`,
and the venue address is fixed at 350 Harbor Dr, Duluth, MN 55802.

All others `VERIFIED`. Marshall and Alexandria added 2026-08-20 (raw VEVENT read: Marshall 18
total / 16 in-window; Alexandria 30 / 30). Both return real family/community programming —
farmers markets, library book sales, Film Friday, concert series, county fair, trail
races — not meeting agendas. Marshall closes the SW-Minnesota gap (Marshall was 0/2);
Alexandria strengthens Douglas County.

> **CVB `?ical=1` is hit-or-miss by platform.** Only tourism sites running The Events
> Calendar (WordPress) expose `?ical=1`. Sites that returned a full HTML page instead of an
> iCal on 2026-08-20 — and so need a *different* feed path, not a retry of this one:
> Owatonna (`visitowatonna.org`), Fergus Falls (`visitfergusfalls.com`), New Ulm
> (`newulm.com`), Detroit Lakes (`visitdetroitlakes.com`), Hastings (`hastingsmn.gov`).
> Red Wing's CVB iCal (`redwing.org/events/?ical=1`) parses but returned **0 in-window**
> (all 27 VEVENTs fell outside the window) — its *city* calendar is the better bet (see §2
> note). Do not re-add these as `?ical=1` candidates.

### §1.1 — `?ical=1` SERIALIZES ONLY THE CURRENT LIST-VIEW PAGE (found 2026-09-11)

**Every `?ical=1` count in the table above was an artifact of the export, not a yield.** The
Events Calendar's iCal export does not serialize the calendar; it serializes **whatever the
list view is currently paginated to** — roughly one screen of upcoming events. So the feed
returns a small, plausible, *correctly parsed* set every time. Nothing errors, nothing looks
capped, and the number is stable run over run, which is exactly what makes it invisible.

Moved all eight WordPress Tribe sources onto the plugin's own REST endpoint:

```
https://<host>/wp-json/tribe/events/v1/events?start_date=<TODAY>&end_date=<END>&per_page=50&page=N
```

It is date-bounded and paged, so it answers the question we were actually asking. Measured
this run (`run_tribe_rest()` / `TRIBE_FEEDS` in `fetch_feeds.py`):

| Source | `?ical=1` | WP REST | |
|---|---|---|---|
| Winona (CVB) | 30 | **579** | ×19 |
| Willmar | 28 | **250** | ×9 |
| Alexandria | 30 | **99** | ×3 |
| Marshall | 16 | **90** | ×6 |
| Dodge Nature Center | 1 | **57** | ×57 |
| Bemidji | 1 | **26** | ×26 |
| Faribault | 9 | 12 | |
| Brainerd | 21 | 8 | `SHORT` — span ends 2026-10-13 |

**+944 in-window rows**, and `site_photo` went **0 → 992** because the REST payload carries
each organizer's own `featured_image_url`.

**Two recorded diagnoses are hereby RETRACTED.** CLAUDE.md's "A low-yield feed is usually the
source's silence" section (2026-08-30) concluded that `dodge_nature` "has simply published
nothing past August" and that `visit_bemidji` "has shrunk to 11 annual placeholders" — and
both were read off the truncated export. Dodge Nature had **57**
in-window events and Bemidji **26**; the content was always there and we were failing to
ask for it. That is the *third* diagnosis from CLAUDE.md's low-yield section — **the source
truncated us** — and it is the dangerous one, because unlike a 403 or a parse error it
presents as a healthy small feed.

Carry three things:

1. **A low yield that is STABLE across runs is not thereby trustworthy.** Stability was the
   reason nobody re-probed these for three weeks. A truncation is *more* stable than real
   content, not less.
2. **Read a feed's returned SPAN, not just its count.** `span_status()` (generalised this run
   from the exactly-500 LibCal tell) flags a source whose last event falls more than 6 days
   short of `END_DATE` as `SHORT`, and a page-ceiling hit as `CAPPED`. A round count at a limit
   is *one* tell; the span is the reliable one. Brainerd is `SHORT` at 8 events — genuinely
   thin, or still truncated; re-probe.
3. **Prefer a date-bounded endpoint to an export, always.** An export answers "what is on the
   page"; an endpoint answers "what is in the window." `test_tribe_rest.py` (34 passed) pins
   the payload shapes, the MN bounding-box rejection, the colon-bearing timestamp bug, and the
   span detector.

### Statewide structured feed — DNR state-park naturalist programs (highest-leverage outstate)

`https://webapps.dnr.state.mn.us/calendar/app?jsp=json&o=startdate&o=starttime&k=stpk&p=thismonth&ae=y`
— official MN DNR calendar **JSON** API. ✅ `VERIFIED` 2026-08-21: `p=thismonth` returned
~177 events statewide; also fetch `p=nextmonth`. Each `events[]` item carries `title`,
`startdate`/`enddate` (`YYYY-MM-DD`), `starttime`/`endtime`, `location` (park name, e.g.
"Wild River State Park"), `location_url`, `description`, `directions`, `contact`. All are
free family/nature programs (junior park naturalist, guided hikes, bat walks, candlelight
events, "I Can…" outdoor-skills). This is the single best way to reach greater-MN parks the
metro feeds never touch, and keyword search does not index it — now wired into SKILL.md's
reliable structured feeds. `k=stpk` is the state-parks key; the same host serves other keys
(community, environmental-education) worth probing later. Resolve city from the park name
(or mine `directions` for the nearest town). Filter `startdate` to the run window.

## 2. Metro suburb city calendars (CivicPlus)

CivicPlus sites expose events at `RSSFeed.aspx?ModID=58&CID=<CalendarName>-<id>`. Use
`CID=All-calendar.xml` for the combined calendar. **`iCalendar.aspx` is not a feed** — it
is a human-facing subscription-instructions page, and testing it produces false negatives.

| City | URL | Format | In-window events |
|---|---|---|---|
| Richfield | `https://www.richfieldmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` | RSS | 9 |
| Maplewood | `https://www.maplewoodmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` | RSS | 4 |
| South St. Paul | `http://www.southstpaulmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` | RSS | 9 |
| Burnsville | `https://www.burnsvillemn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` | RSS | 31 |
| Lakeville | `https://www.lakevillemn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` | RSS | 8 |

All `VERIFIED`. Burnsville + Lakeville added 2026-08-21. **Burnsville is a genuine
family/rec positive** (unlike the meeting-noise cities in the note below): its 31 items are
Adult Open Hockey, Public Skating, Stick and Puck, Developmental Hockey Ice and similar
rec-center programming, each with a real `Calendar.aspx?EID=<id>` deep link. Lakeville (8)
mixes St. Paul Farmers Market listings with a Finance Committee meeting — ingest behind the
family filter. **Gotcha:** the item's real event date is in the `<description>`, NOT
`<pubDate>` (pubDate is the publish timestamp). Covers Dakota-county shortfall suburbs.

Legacy `*.ci.<city>.mn.us` and `*.<city>.us` hostnames 301-redirect to `<city>mn.gov`.
Always follow the redirect; the old host will otherwise look dead.

> **City-gov CivicPlus feeds are mostly meeting-noise — treat them as low-yield (2026-08-20
> finding).** Testing the `RSSFeed.aspx?ModID=58&CID=All-calendar.xml` pattern across a
> dozen shortfall cities: the ones that returned items were dominated by City Council,
> Planning Commission, HRA/EDA and board meetings, not family programming. **Owatonna
> (16 items) and Northfield (7) and Rosemount (5) were essentially ALL meetings** — same
> failure mode as the Lino Lakes `LIVE-NO-VALUE` note below; do not ingest them as family
> sources. Two were partial: **Red Wing** (`red-wing.org`, 24 items) mixes in a few real
> ones (Farmers Market, Concerts in the Park, an author event) and **Mendota Heights**
> (`mendotaheightsmn.gov`, 13 items) has Music in the Park / Park Hangout / Workout in the
> Park amid the meetings — worth ingesting ONLY behind a hard family-appropriate filter
> that drops anything matching `council|commission|board|HRA|EDA|workshop|hearing|study
> session`. The lesson mirrors the coverage spec: **library and CVB feeds carry family
> content; municipal government feeds mostly carry governance.** Prefer the former.
> 403/404 on the RSS path (Savage, Prior Lake, Shoreview, White Bear Lake, Ramsey,
> Hastings on 2026-08-20) — cover those cities via their county library system instead.

## 3. Library systems

These are the highest-yield sources for the metro, because branch programming is
concentrated in exactly the suburbs that show zero coverage.

| System | Events endpoint | Format | Events |
|---|---|---|---|
| Hennepin County | `https://gateway.bibliocommons.com/v2/libraries/hclib/events` | JSON | 2,162 |
| Ramsey County | `https://gateway.bibliocommons.com/v2/libraries/rclreads/events` | JSON | 761 |
| Anoka County | `https://anokacounty.libcal.com/api_events.php?cal_id=9233&date=YYYY-MM-DD&days=N` | HTML | date-bounded |
| Washington County | `https://washcolib.libcal.com/api_events.php?cal_id=0&date=YYYY-MM-DD&days=1` | HTML | **day-loop** |

Washington County added 2026-08-20, `VERIFIED`: Aug 20 alone returned 9 family events
(Storytime, Drop-In Play Date, Baby Storytime, Lego Robotics Workshop, plus adult clubs),
and every future sample date carried recurring storytimes. This is the east-metro
counterpart to Hennepin/Ramsey/Anoka — its branches (Woodbury, Cottage Grove, Stillwater,
Oakdale, Forest Lake, Hardwood Creek/Hugo, Mahtomedi/Wildwood, Newport, Marine) cover the
shortfall suburbs **Hugo** and **Mahtomedi** (both 0) among others.

**Washington's LibCal does NOT honor `days`.** Unlike Anoka (where `days=42` returns the
whole span from one call), `washcolib`'s `api_events.php` returns only the single `date`
requested no matter what `days` is set to — verified by fetching Aug 20 / 27, Sep 3 / 17
and getting one day each. So **loop day-by-day from TODAY to END_DATE** and concatenate;
do not trust a single `days=N` call to have returned the window. `cal_id=0` is the
system-wide aggregate here (a specific branch cal_id is not required). This is exactly the
"verify the `days` span is actually honored" rule from §3 of the coverage spec — one LibCal
instance honors it, the next silently does not.

### County / regional library systems — high-priority candidates to wire up

The library-system pattern is the highest-yield way to close many gap-cities with one
feed. Beyond the four already ingested (Hennepin, Ramsey, Anoka, Washington), these were
located and confirmed to be live LibCal instances with real children's programming in
their web calendars on 2026-08-20, but their `api_events.php` aggregation did not yield a
clean programmatic count under `cal_id=0` — each needs its correct aggregate/branch
`cal_id` resolved (read the system's `/calendar` page, find the default `cid`, then
day-loop as with Washington) before being promoted to `VERIFIED`:

| System | Host | Region / gap-cities it would cover |
|---|---|---|
| Dakota County Library | `dakotacountylibrary.libcal.com` (calendar `cid=9306`) | Rosemount, Farmington, Mendota Heights + Eagan/Apple Valley/Burnsville/Lakeville |
| Carver County Library | `carverlib.libcal.com` | Waconia, Chaska, Chanhassen, Victoria (thin — mostly art exhibits on 2026-08-20) |
| Great River Regional | `events.griver.org` (LibCal) | St. Cloud region: Sauk Rapids, Waite Park, St. Joseph, Big Lake, Monticello, Litchfield |

**Not found on either platform (BiblioCommons gateway 404 + no LibCal subdomain resolves),
so still open:** Scott County (Savage, Prior Lake, Shakopee), and the outstate federated
systems SELCO (Owatonna, Austin, Red Wing, Northfield, Albert Lea — **federated, so each
member library runs its own calendar; there is no single system feed**), Arrowhead/Duluth
(Hibbing, Virginia, International Falls, Cloquet, Grand Rapids), and Plum Creek (Marshall,
Worthington). St. Paul Public (`sppl`) IS on the BiblioCommons gateway but is redundant
with Ramsey County for coverage purposes.

### Regional systems verified / platformed 2026-08-21

Extending the library-system pattern outstate. All checked by raw endpoint read on
2026-08-21 (per the §5 rule):

| System | Region / gap-cities | Platform + endpoint | Status |
|---|---|---|---|
| **East Central Regional (ECRL)** | Cambridge, Isanti, North Branch, Chisago Lakes, Milaca, Mille Lacs/Isle, Mora, Pine City, Princeton, Rush City, Hinckley, Sandstone | **LibCal** `ecrlib.libcal.com`, `cid=13690` — `ical_subscribe.php?src=p&cid=13690` returns 500 events (the cap), past-front-loaded. Real event URLs `ecrlib.libcal.com/event/<digits>`. | ✅ `VERIFIED` — wired into SKILL.md mandatory iCal pull. **LOCATION carries the branch name, not a street address** — derive city from the branch name (it contains its city). |
| **Kitchigami Regional (KRLS)** | Brainerd/Baxter, Pine River, Park Rapids, Walker, Longville, Pequot Lakes, Nisswa, Wadena, Backus, Remer | **WordPress "My Calendar" ICS** `https://krls.org/feed/my-calendar-ics/` — PRODID `spatie/icalendar-generator`. **MONTH-SCOPED — must be fetched once per month via `?month=<m>&yr=<y>`; see §1.2.** | ✅ `VERIFIED` — wired into SKILL.md mandatory iCal pull. **LOCATION carries the FULL street address** (e.g. "Park Rapids Area Library 210 W. First St. Park Rapids Minnesota 56470") → geocodes directly, no branch→city map. Real URLs `krls.org/mc-events/<slug>/`. Supersedes the earlier "thin/low-yield/needs browser-UA" note — plain curl retrieved it fine. **The "best-in-class" label was removed 2026-09-12: the address handling is still the best of any source here, but the bare URL was serving ONE MONTH and reading as a healthy small feed. 33 VEVENTs / 16 in-window across 4 month fetches, span 2026-09-01..2026-11-19, against 17 / 6 ending 2026-09-24 on the bare URL.** |
| **Lake Agassiz Regional (LARL)** | Moorhead, Detroit Lakes, Fergus Falls, Barnesville, Ada, Hawley, Mahnomen | **Communico** (`api.communico.co`); public events page `https://www.larl.org/events`. No clean public iCal without an API key. | ◐ platform confirmed, HTML best-effort — wired into SKILL.md as best-effort. |
| **Great River Regional (GRRL)** | St. Cloud region | **LibCal** confirmed on `griver.org/events` (loads LibCal widget). | Already in mandatory pull (low-yield admin cid — branch cids still to resolve). |

**"My Calendar" WordPress ICS is a new replicable pattern:** `<host>/feed/my-calendar-ics/`
(the plugin also exposes `webcal://<host>/feed/my-calendar-google/`). When a MN library or
CVB runs on WordPress, probe this path — it yields a clean address-bearing `.ics`. **But see
§1.2 first: the bare path is month-scoped, so probing it tells you the plugin is there and
NOTHING about the source's real volume.**

### §1.2 — "My Calendar" ICS is MONTH-SCOPED, and the month arg is a START not an interval

Found 2026-09-12, and it is the **fourth instance of the truncation class** after the
`?ical=1` list-view export (§1.1), the LibCal 500-VEVENT cap, and the LibCal
`api_events.php` today-only regression.

The bare `https://krls.org/feed/my-calendar-ics/` returns **the current month only**. On
2026-09-12 that was 17 VEVENTs spanning to 2026-09-24 — 6 in-window against an `END_DATE`
of 2026-10-31, so **the whole back half of the window was structurally invisible** while the
feed looked like an ordinary quiet outstate library system. Fetched month by month it returns
33 VEVENTs / **16 in-window**, span 2026-09-01..2026-11-19.

Handling is `month_urls(url, today, end)` + `MONTH_LOOP_ICAL` in `fetch_feeds.py`. Five
things it has to get right:

1. **Fetch the bare URL as well as the explicit months.** The default *appears* to be the
   current month, but that is observed, not documented, and a plugin update could change it.
2. **Fetch ONE MONTH PAST `END_DATE`.** This is not belt-and-braces: `month=10` came back
   spanning 09-25..10-17, while the 2026-10-30 Park Rapids storytime appeared **only** under
   `month=11`. The month argument selects a start point, not a bounded interval, so stopping
   at END's own month leaves a hole in exactly the tail the export was already truncating.
3. **De-duplicate on `(UID, DTSTART)`, never on `UID` alone.** Consecutive month fetches
   overlap, and a weekly series shares one UID across every occurrence — keying on UID alone
   collapses a weekly program to a single row, which is the `_dedup4_0822` defect arriving
   through the fetcher instead of through a dedup pass.
4. **A reversed window raises** rather than returning `[]`. A silently-empty URL list means
   zero fetches and a zero-row source: the quiet failure this whole class is made of.
5. **`&` not `?` when the URL already carries a query.**

Two things generalise beyond this source. **`span_status()` is what caught it** — the
in-window count (6) was unremarkable and no count-based check could ever have fired, which is
the argument for the span half of that detector made a second time on a second source. And
**a truncated feed is MORE stable run-over-run than real content**, because you are re-reading
the same fixed slice, so run-over-run stability is not evidence of correctness.

**Negative result recorded the same day: LibCal `ical_subscribe.php` takes NO date bounds.**
`washco_libcal` and `dakota_libcal` are `CAPPED` at exactly 500 VEVENTs with spans ending
before `END_DATE`, and the obvious remedy — add a date parameter the way KRLS takes `month` —
was probed and does not exist. `start`, `start_date`, `date`, `from`, `days` and `cal_date`
were all accepted-and-ignored: byte-identical 500-VEVENT responses every time. So this one
needs a **different endpoint or real paging**, not a query param, and it stays `CAPPED`/warning
until then. Do not re-probe the query-param route.

### BiblioCommons gateway — required handling

Four things will silently produce wrong results if ignored:

**`startDate` / `endDate` are ignored.** The endpoint accepts them and returns the full
forward set anyway (Aug 2026 through Jan 2027 on a request bounded to Aug 19–Sep 30).
Filter the window client-side; never assume the server did it.

**Events carry a location *code*, not a city.** Resolve codes by fetching
`https://gateway.bibliocommons.com/v2/libraries/<code>/locations`, which returns each
branch with its street address, and feed that address through `mn_city_resolve`.

**Never hardcode the code→branch map.** Fetched summaries of the events payload produced
two mutually contradictory mappings, both wrong: `AF` was reported as Anoka and `FR` as
Fridley, when the authoritative `/locations` response gives `AF` = Arvonne Fraser
(Minneapolis) and `FR` = Franklin (Minneapolis). Joining on `/locations` every run is both
correct and self-maintaining.

**Both endpoints paginate** — `/locations` at 10 per page, `/events` at 50 per page. Page
to exhaustion or you will capture only the alphabetical head of the branch list.

Confirmed branch→city hits in previously zero-coverage suburbs: `BD` Brookdale →
Brooklyn Center, `BP` Brooklyn Park → Brooklyn Park, `AP` Augsburg Park → Richfield.
Anoka's LibCal returns Mississippi Library (Fridley) and Columbia Heights Public Library.

### LibCal — required handling (**REVERSED 2026-08-28 — read this before the paragraph below**)

**Use `ical_subscribe.php?src=p&cid=<id>`, fetched raw. Do not use `api_events.php`.**

On 2026-08-28 all six LibCal systems returned **0 in-window rows**. `api_events.php` now
ignores both `date` and `days` and serves "Today's Events" for every request — verified by
asking Anoka for `date=2026-08-28`, `2026-09-15` and `2026-09-29` and getting byte-identical
event ids all three times. That is a silent failure, not an error: the endpoint returns 200
with well-formed HTML, so a pull that trusts it looks healthy and ships an empty library
category.

The truncation that drove the original preference for `api_events.php` was **a ~450 KB
WebFetch ceiling, not an HTTP one**. Read raw, Anoka's 741 KB feed arrives whole. Switching
back recovered **0 → 879 in-window rows**. The lesson generalises past LibCal: when a spec
says "feed X truncates," record *what did the truncating*, because a tool limit and a server
limit call for opposite responses.

Two consequences of reading the ical feed to keep in mind:

* Feeds are `DTSTART`-ascending from roughly four weeks **before** the run date, so the head
  of the file is spent on past events. Filter to the window after parsing; never conclude
  "no in-window events" from a partial read.
* The **500-VEVENT cap** is applied by the server before the window is reached on busy
  systems. Check each feed's last `DTSTART` against `END_DATE`. On 2026-08-28 `washcolib`
  spanned only `2026-07-28..2026-09-28`, silently losing 09-29 and 09-30; every other capped
  feed reached past `END_DATE`. A capped feed is not a failed feed — log it, don't drop it.

Verified cids (all pulled successfully 2026-08-28):

| System | Host | cid | In-window |
|---|---|---|---|
| Anoka County | `anokacounty.libcal.com` | 9233 | 177 |
| Washington County | `washcolib.libcal.com` | 10166 | 226 (**CAPPED at 09-28**) |
| Dakota County | `dakotacountylibrary.libcal.com` | 9306 | 210 |
| Scott County | `scottlib.libcal.com` | 10242 | 139 |
| Carver County | `carverlib.libcal.com` | **9314** | 126 |
| East Central (ECRL) | `ecrlib.libcal.com` | 13690 | 172 |
| Great River (GRRL) | `events.griver.org` | **18620** | 1 |

The two bolded cids were recorded as UNRESOLVED in §3 above and were found this run by
reading each system's `/calendar` page. **Scott County is also resolved** — §3's "not found
on either platform" line for Scott (Savage, Prior Lake, Shakopee) is stale; it is on LibCal
at `scottlib.libcal.com`. GRRL's cid is correct but the calendar is genuinely near-empty
(11 VEVENT total); that is a real yield, not a broken fetch, so do not re-hunt it.

### §3.1 — A LibCal HOST can carry libraries the county AGGREGATE does not (found 2026-09-16)

`washco_libcal` has been `CAPPED` for weeks (500 VEVENTs, span ending before `END_DATE`), and
CLAUDE.md leaves the remedy open as *"a different endpoint or real paging"*. Hunting that
remedy turned up something else entirely, and the distinction is the finding.

Scanning `washcolib.libcal.com/calendar` for `cal_id[=:"\s]{1,4}(\d+)` yields **21 numeric
cids**. Two of them return real feeds: **`10442` = Stillwater Public Library** (194 VEVENT,
span `2026-08-17..2027-03-16`) and **`10451` = Bayport Public Library** (75 VEVENT, span
`..2027-01-01`). Keyed on `(UID, DTSTART)`, their intersection with the aggregate `cid=10166`
is **exactly zero**, and they contribute **103 in-window events** — Stillwater 72, Bayport 31.
The other 19 cids return a 19-byte empty calendar.

**This is a MISSING SOURCE wearing a truncation investigation's clothes.** The cap is
untouched: washco's aggregate still ends `2026-10-16`. Stillwater and Bayport are independent
*municipal* libraries that merely share the county's LibCal tenant, so they were never inside
the feed being capped — they were never being asked for at all. Both now dispatch as
`stillwater_libcal` / `bayport_libcal` in `fetch_feeds.py`'s `LIBCAL` table.

Four things to carry:

1. **The fan-out does NOT generalise — it was measured on all five other systems and found
   redundant there.** Anoka (20 extra cids), Dakota (17), Carver (22) and Scott (21) were each
   probed the same way, and on every one the union of non-aggregate cids added **0** new
   in-window events: those aggregates genuinely subsume their branches. Wiring per-branch cids
   there would multiply requests for nothing. A remedy that works on one host of a platform is
   a fact about that host's tenancy, not about the platform.
2. **A single-library cid needs a default city AND a default venue, because its own rows carry
   neither.** On these two feeds `ORGANIZER;CN` is a **staff member** ("Kamra Heldman"), where
   the aggregate feeds put the branch name, and `LOCATION` is frequently a bare room ("Prairie
   Room"). So `BRANCH_CITY` cannot fire, and the existing `branch or room` rule would have
   written *a person's name into the address field*. `LIBCAL` is now a 5-tuple
   `(key, host, cid, default_city, default_venue)`; both defaults are `""` for every aggregate,
   because stamping one city across a county feed is the wrong-CITY defect CLAUDE.md records.
3. **The `LIBRARY_SRC` registry assertion caught the resulting drift on the same run that
   created it.** `compile_step3._assert_library_src_covers_fetcher()` failed with
   `['bayport_libcal', 'stillwater_libcal']` the first time it ran — the alarm built after the
   `sppl` 669-untagged-row incident doing precisely its job, on live data, before any row
   reached the image stage. It also survived the `LIBCAL` tuple **arity** change (3 → 5),
   because the bracket-depth scan reads the table's extent rather than its shape.
4. **Re-confirmed negative, do not re-probe:** the query-param route is still dead. `&audience=`,
   `&cam=`, `&ct=`, `&inc=0`, `&l=` and `&camps=` each returned 200 / 500 VEVENT /
   **byte-identical sha `8f93b746a6`** — accepted and ignored, the same shape as
   BiblioCommons `startDate`/`endDate`. Comparing bytes rather than row counts is what makes
   that a finding instead of a guess.

### §3.2 — `SHORT` does not imply truncation: the first confirmed TRUE NEGATIVE (2026-09-16)

`span_status` flagged `brainerd` SHORT. Every previous `SHORT`/`CAPPED` in this project's
history — `krls`, `visit_bemidji`, `dodge_nature`, the two LibCal systems — turned out to be
truncation, which had quietly made "SHORT" read as a synonym for "we are being cut off."

Brainerd is not. Asked **unbounded** on the Tribe REST endpoint it reports `total=13`,
`total_pages=1`, i.e. the whole calendar in one page: 8 in-window, span
`2026-09-23..2026-10-13`, by month `2026-09`:3, `2026-10`:5, `2026-11`:1, `2026-12`:2,
`2027-04`:2. The bounded query returns the same 8. The CVB has simply published nothing
between 10-13 and 10-31.

This closes the open question §1.1 left on Brainerd, and it sharpens the detector's meaning:
**`SHORT` says the span ends early, which is a question, not an answer.** The way to settle it
is the same either way — ask an unbounded or date-bounded endpoint and compare — but the
verdict can legitimately be "the source is quiet," and CLAUDE.md's rule that a content gap
must be *recorded and re-probed* rather than fixed applies here. Do not loosen the detector
because it produced a true negative; a detector that never fires falsely is one that is not
looking hard enough.

### §3.3 — A parked domain can return HTTP 200 carrying SOMEONE ELSE'S page (found 2026-09-16)

Probing LARL (Lake Agassiz Regional Library, Communico platform) for a feed:
`https://larl.attend.communico.co/` returns **HTTP 200** — and the body is a **Google page**
(`gb_` CSS classes, `window.gapi`, `lsb`/`lst` search-box classes). The subdomain is parked
and redirects; nothing about the status code says so.

This is a silent-failure shape not previously recorded here, and it is worse than a 404 in the
obvious way: a fetcher that checks `status == 200` and then looks for its expected markers logs
"0 events" and moves on, which is indistinguishable from a quiet source. **Assert something
about the BODY, not just the status** — the same reason `dnr_banner_map()` byte-checks its
JPEGs after the DNR API's own `image` field was found to 404.

The rest of the LARL probe is a **confirmed negative** and should not be re-run:
`larl.libnet.info` is a JavaScript web-component app; `/api/events`, `/ical`, `/events.ics`,
`/api/1/events`, `/eventlist` and `/feed` all 404, `/events/ical` is a catch-all serving the
same HTML, and `/rss` returns 25 empty bytes. The registry's existing classification — no clean
public iCal without an API key, HTML best-effort only — is correct as written.

## 4. Dead ends — do not retry

| Source | Reason |
|---|---|
| `fridleymn.gov/RSSFeed.aspx` | 403 |
| `brooklyncentermn.gov/RSSFeed.aspx` | 403 |
| `newhopemn.gov/RSSFeed.aspx` | 403 |
| `brooklynpark.org/RSSFeed.aspx` | 404 — site runs Vermont Systems / MyVSCloud |
| Richfield `CID=Parks-and-Recreation-23` | Returns 0 items; use `All-calendar.xml` |
| `anoka.bibliocommons.com` | 404 — Anoka County uses LibCal, not BiblioCommons |
| `gateway.bibliocommons.com/v2/libraries/anokacounty/*` | 404 — wrong library code |
| `washcolib.bibliocommons.com` | 404 — Washington County is on **LibCal**, not BiblioCommons; use `washcolib.libcal.com` (now in §3, `VERIFIED` 2026-08-20) |
| `anokacountylibrary.org` | TLS certificate verification error |
| Any `iCalendar.aspx` on a CivicPlus site | Not a feed; subscription info page only |
| `winona_library` ical feed | **403 Forbidden, confirmed on two consecutive runs (2026-08-28 and 2026-08-29).** Recorded `VERIFIED` on 2026-08-19, so this is a real new block rather than a stale entry, and two runs make it persistent rather than transient. **Stop retrying it every run** — it is now a dead end, not an ERROR to re-investigate. `visit_winona` (30 in-window) still covers the city. |
| `*.libcal.com/api_events.php` | Serves "Today's Events" regardless of `date`/`days` as of 2026-08-28. Returns HTTP 200, so it fails **silently**. See §3. |
| CVB `?ical=1` on Explore Minnesota, Visit Brainerd, Explore Alexandria, Visit Winona, Visit Mankato | 0 VEVENTs (2026-08-21) — these tourism sites are not on The Events Calendar / don't expose an ical export at that path. Do NOT assume the `?ical=1` template scales to CVBs; it was only ever verified for Visit Bemidji + Dodge Nature Center. |
| `rochesterpubliclibrary.org` via curl | HTTP 000 (2026-08-21) — blocks datacenter/non-browser requests. Rochester Public Library's calendar platform is still UNCONFIRMED. Retry only via runtime `WebFetch` (browser-like), not curl. Rochester (~pop 121k) is the single biggest outstate gap; worth a manual platform check. |
| `alslib.info` "ical" strings | False positive (2026-08-21) — the 112 "ical" hits were the `ajax-search-lite` JS plugin (`asl-results-vertical.js`), NOT an iCal feed. Arrowhead (ALS) event platform still UNCONFIRMED. |
| Hopkins / Cottage Grove `RSSFeed.aspx?ModID=58` | HTTP 200 but 0 items (2026-08-21) — on CivicPlus but this module is empty for them; Eagan's redirects (301). CivicPlus RSS is not universal — confirm item count per city. |
| `grpl.bibliocommons.com/v2/events` | **WRONG STATE — this is Grand Rapids, MICHIGAN** (probed 2026-09-09). SKILL.md lists it under the greater-MN outstate sources as "Grand Rapids Public Library … tag `grand-rapids`", and it is a perfectly healthy, live BiblioCommons instance — 8 branches, 211 events, **130 of them in-window** — which is exactly what makes it dangerous. Every branch address reads `Grand Rapids, MI 49503`; the Main Library centroid is `42.9649, -85.6660`, outside the MN bounding box on both axes. Its platform is identical to `sppl`/`rclreads`, so wiring it on the SPPL pattern costs one `BIBLIO` row and no new code — and would have folded 130 Michigan library events into a Minnesota family guide. **The spec itself carries the wrong subdomain**; do not wire `grpl`. Grand Rapids **MN** is served by the Grand Rapids Area Library (Arrowhead / ALS region, platform still UNCONFIRMED per the `alslib.info` row above) — that is the source to find, and it must not be substituted with this one. |

`linolakes.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml` is `LIVE-NO-VALUE`: it returns
5 in-window items, all city council, EDA, environmental board and park board meetings.
Nothing family-facing. Keep the URL on record so it is not rediscovered as a candidate,
but do not ingest it.

## 4b. Listed-but-not-landing — an ingestion gap, not a source gap

A feed being on this list does not prove its events reach the final dataset. On 2026-08-20,
**Willmar** showed only **1 event** in the coverage check despite its CVB feed returning 28
(§1). That is not a missing source — it is one of: (a) the feed not actually being fetched
that run, (b) its events resolving to *surrounding* towns rather than to "Willmar" (the
Willmar Lakes Area feed spans several municipalities), or (c) events landing out-of-window.
Before hunting for a *new* Willmar source, confirm the existing one is being fetched and
that `mn_city_resolve` is attributing its rows correctly. The same "listed feed, near-zero
coverage" pattern is worth spot-checking for any §1 city that still appears in the
shortfall list (Faribault and Rochester currently do clear, so the ingestion path works in
general — Willmar is the outlier to chase).

## 4c. The suburban shortfall is a branch→city resolution gap, not a missing source

Investigated 2026-08-20. Most of the metro major-suburb shortfall is caused by the LibCal
library feeds — which are already pulled in STEP 2 — carrying events whose **only** location
signal is a branch *name*, not a street address. `mn_city_resolve` needs an address to name
a city, so these rows resolve to nothing (or to the county) and never land in the suburb.

Concrete proof: the Anoka County feed contains, in-window, **~46 events at "Mississippi
Library (Fridley)"**, 36 at Centennial (serves Lino Lakes / Circle Pines), 34 at Columbia
Heights, and 30 at North Central (Ham Lake) — yet the 2026-08-20 coverage check reported
**Fridley 0, Lino Lakes 0, Columbia Heights 3, Ham Lake 1**. The events exist in a source
already on this list; they are simply not being attributed to a city.

This is the LibCal analogue of the BiblioCommons "join to /locations for the street address"
rule in §3 of the coverage spec. LibCal has no locations endpoint, so it needs an explicit
branch→city map. Below is the verified map for the three systems whose feeds carry branch
names (extracted from live feeds 2026-08-20). Anoka/Scott expose the branch in
`ORGANIZER;CN=`; Washington exposes it in `LOCATION`.

**Anoka County Library** (`anokacounty.libcal.com`, cid 9233):

| Branch (as it appears in feed) | City |
|---|---|
| Mississippi Library | Fridley |
| Centennial Library | Circle Pines (also serves Lino Lakes) |
| North Central Library | Ham Lake |
| Northtown Library | Blaine |
| Johnsville Library | Blaine |
| Crooked Lake Library | Coon Rapids |
| Rum River Library | Anoka |
| St. Francis Library | St. Francis |
| Columbia Heights Public Library | Columbia Heights |

**Scott County Library** (`scottlib.libcal.com`, cid 10242):

| Branch | City |
|---|---|
| Savage Library | Savage |
| Prior Lake Library | Prior Lake |
| Shakopee Library | Shakopee |
| New Prague Library | New Prague |
| Jordan Library | Jordan |
| Belle Plaine Library | Belle Plaine |
| Elko New Market Library | Elko New Market |

**Washington County Library** (`washcolib.libcal.com`, cid 10166):

| Branch | City |
|---|---|
| R.H. Stafford Library | Woodbury |
| Oakdale Library | Oakdale |
| Hardwood Creek Library | Forest Lake |
| Lake Elmo Library | Lake Elmo |
| Park Grove Library | Cottage Grove |
| Wildwood Library | Mahtomedi |
| Valley Library | Lakeland |

Apply by rewriting each event's `address` to the branch's host city (e.g.
`"Mississippi Library, Fridley, MN"`) **before** running `mn_city_resolve`, so the address
branch of the resolver fires. To take effect in the cloud run this map must live in
`SKILL.md` (only that file loads in the sandbox) — recording it here is documentation, not
deployment.

### The oversized-feed truncation, compounding it

The Anoka `ical_subscribe.php` feed is **748 KB** — larger than WebFetch's ~450 KB ceiling,
so a single fetch truncates it. Feeds sort DTSTART ascending starting ~4 weeks *before* the
run date (Anoka's earliest is 2026-07-20), so the wasted head is all past events and the
**truncated tail is the in-window events**. Washington (440 KB, 500-event cap) stops at
2026-09-17, losing the last ~2 weeks of a window that runs to 09-30. Fix options, in order
of preference: fetch `api_events.php?cal_id=0&date=<run-date>&days=<N>` (starts at the run
date, no past-event waste — but the `days` param is honored inconsistently, so day-loop
where it isn't), or page the ical feed by date range. Do not rely on a one-shot WebFetch of
the raw ical feed for any system whose feed exceeds ~400 KB.

## 5. Verification rule

Never accept a subagent's or a summarizer's count for a feed. Two failures on 2026-08-19
came from exactly that: a subagent declared Richfield and Maplewood dead after testing
`iCalendar.aspx` (both are in fact live via `RSSFeed.aspx`), and its one "working" claim
for South St. Paul cited Aug 5 and Aug 12 events that were already out of window. Confirm
each feed personally, and confirm that the events cited fall **on or after** the run date.
