"""STEP 2 mandatory direct feed pull — 2026-08-28.

Raw HTTP reads only (event-source-calendars.md §5 / coverage-spec §4: never accept a
summarizer's count for a feed).  Reads each feed to the END — iCal sorts DTSTART ascending
from ~4 weeks in the past, so a truncated read shows only stale rows and reports 0 in-window.
"""
import urllib.request, urllib.error, json, re, ssl, sys, time, gzip, io, os, html
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# The window is READ FROM THE ENVIRONMENT, never hardcoded (changed 2026-09-08).
# This file previously carried a literal `TODAY = "<date>"` that STEP 1 had to remember to
# restamp by hand every run.  A missed restamp silently shifts the whole rolling window and
# raises nothing -- the same failure class CLAUDE.md records for `_staledate*.py` and for the
# f-string-embedded `_feedpull_{which}_0828.json` path.  STEP 1 derives TODAY from a
# server-side timestamp (the sandbox clock is forbidden) and exports MSP_TODAY / MSP_END.
# The fallback is a HARD FAILURE, not a stale literal: a wrong window is worse than no window,
# because it fails silently while a missing one does not.
TODAY = os.environ.get("MSP_TODAY", "").strip()
END = os.environ.get("MSP_END", "").strip()
if not re.fullmatch(r"\d{4}-\d\d-\d\d", TODAY) or not re.fullmatch(r"\d{4}-\d\d-\d\d", END):
    raise SystemExit(
        "fetch_feeds.py: MSP_TODAY / MSP_END must be set to YYYY-MM-DD.\n"
        "  STEP 1 derives these from a server-side timestamp -- see params.txt.\n"
        f"  got MSP_TODAY={TODAY!r} MSP_END={END!r}")
UA = "Mozilla/5.0 (compatible; MSPFamilyGuide/1.0; +https://github.com/avlhohn/msp-family-feed)"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def http(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


# ---------------------------------------------------------------- iCal parsing
def unfold(text):
    # RFC5545 line folding: continuation lines start with space/tab
    return re.sub(r"\r?\n[ \t]", "", text)


def ical_events(text):
    text = unfold(text)
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        ev = {}
        for line in block.split("\n"):
            line = line.strip("\r")
            if not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            name = key.split(";")[0].upper()
            params = key.split(";")[1:]
            if name in ("SUMMARY", "DESCRIPTION", "LOCATION", "URL", "UID",
                        "DTSTART", "DTEND", "CATEGORIES", "ORGANIZER"):
                val = (val.replace("\\,", ",").replace("\\;", ";")
                          .replace("\\n", " ").replace("\\N", " ").strip())
                if name in ("DTSTART", "DTEND"):
                    ev[name + "_P"] = ";".join(params)
                if name == "ORGANIZER":
                    m = re.search(r"CN=([^;:]+)", key)
                    if m:
                        ev["ORG_CN"] = m.group(1).strip('"')
                ev.setdefault(name, val)
        if ev.get("DTSTART"):
            out.append(ev)
    return out


_CENTRAL = ZoneInfo("America/Chicago")
_UTC = ZoneInfo("UTC")


def _ical_parse(v, params=""):
    """Parse an iCal DTSTART/DTEND into (date_str, datetime|None) in America/Chicago.

    iCal timestamps arrive in four forms and ONLY the UTC form needs converting:
      * UTC       20261001T233000Z              -> convert UTC -> America/Chicago
      * zoned     TZID=America/Chicago:...T1830  -> already local (convert only if some
                  other named zone ever appears)
      * floating  20261001T183000               -> treat as local wall time (no shift)
      * all-day   VALUE=DATE  20261001           -> date only, no time component

    Before 2026-09-29 the raw hour digits were formatted verbatim (no tz handling), so
    LibCal's UTC-stamped events printed 5-6h late ("6:30 PM" -> "11:30 PM") AND any
    late-evening event that crosses midnight in UTC was filed on the WRONG DAY, which also
    fed a wrong `date` into the window filter.  Converting the full timestamp first fixes
    both, and is DST-correct because zoneinfo picks CDT vs CST from the actual date.
    Returns ('YYYY-MM-DD' or '', a Central-tz datetime or None for date-only/unparseable).
    """
    v = (v or "").strip()
    md = re.match(r"(\d{4})(\d{2})(\d{2})", v)
    if not md:
        return "", None
    y, mo, da = int(md.group(1)), int(md.group(2)), int(md.group(3))
    mt = re.match(r"\d{8}T(\d{2})(\d{2})(\d{2})?", v)
    if not mt:                                    # all-day / date-only value
        return f"{y:04d}-{mo:02d}-{da:02d}", None
    hh, mi, ss = int(mt.group(1)), int(mt.group(2)), int(mt.group(3) or 0)
    naive = datetime(y, mo, da, hh, mi, ss)
    up = (params or "").upper()
    if v.endswith("Z") or "TZID=UTC" in up:
        src = _UTC
    elif "TZID=" in up:
        m = re.search(r"TZID=([^;:]+)", params)
        try:
            src = ZoneInfo(m.group(1).strip()) if m else _CENTRAL
        except Exception:
            src = _CENTRAL                        # unknown zone -> assume local, don't shift
    else:
        src = _CENTRAL                            # floating -> local wall time (no shift)
    local = naive.replace(tzinfo=src).astimezone(_CENTRAL)
    return local.strftime("%Y-%m-%d"), local


def ical_date(v, params=""):
    return _ical_parse(v, params)[0]


def ical_time(v, params=""):
    dt = _ical_parse(v, params)[1]
    if dt is None:
        return ""
    ap = "AM" if dt.hour < 12 else "PM"
    return f"{dt.hour % 12 or 12}:{dt.minute:02d} {ap}"


def in_window(d):
    return bool(d) and TODAY <= d <= END


def clean(s, limit=600):
    # Decode HTML entities FIRST, then strip tags.  Several sources (e.g. the Burnsville
    # municipal rec feed) deliver ENTITY-ENCODED markup -- `&lt;strong&gt;...&lt;br&gt;`.
    # The old order stripped `<...>` first (no literal brackets to match), then the
    # `&[a-z]+;` rule deleted `&lt;`/`&gt;` but left the tag words "strong"/"br"/"BR/"
    # behind as visible text.  html.unescape turns `&lt;strong&gt;` back into `<strong>`
    # (and `&amp;`->&, `&#8217;`->', `&hellip;`->..., etc.), so the tag strip below then
    # removes it.  This also handles literal-HTML sources unchanged, and is idempotent.
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&[a-z0-9#]+;", " ", s)  # backstop for any stray double-encoded entity
    return re.sub(r"\s+", " ", s).strip()[:limit]


def row(title, desc, addr, dt, tm, url, source, tags=""):
    return {
        "title": clean(title, 160), "description": clean(desc, 600),
        "category": "events", "price_type": "", "price": "", "age_range": "",
        "address": clean(addr, 200), "latitude": "", "longitude": "",
        "image_url": "", "image_source": "", "date": dt, "time": tm,
        "phone": "", "website": url.strip()[:300], "has_deal": False,
        "deal_description": "", "deal_expiry": "", "tags": tags,
        "_src": source,
    }


RESULTS = []
REPORT = []


def log(src, status, n, note=""):
    REPORT.append({"source": src, "status": status, "in_window": n, "note": note})
    print(f"  {status:8} {src:38} {n:>5}  {note}")


# ---------------------------------------------------------------- 1. CVB / misc iCal
#
# MOVED OUT 2026-09-11 -- eight `?ical=1` CVB/nature sources were rewired to TRIBE_FEEDS
# below.  They are WordPress "The Events Calendar" sites, and that plugin's `?ical=1` export
# serializes THE CURRENT LIST-VIEW PAGE, not the calendar: the export is capped at whatever
# each site's posts-per-page setting happens to be.  Measured this run, in-window:
#     visit_winona    30 -> 579     willmar      30 -> 250     visit_marshall 30 ->  90
#     explore_alex    30 ->  99     dodge_nature 29 ->  57     visit_bemidji  11 ->  26
#     brainerd         5 ->   8     visit_faribault 12 ->  12   (control -- see below)
# Four of them returned EXACTLY 30, which is the round-number-at-a-limit tell CLAUDE.md
# already documents for the 500-VEVENT LibCal cap.  But bemidji returned 11 and brainerd 5,
# so **the round number is NOT the reliable signal** -- the cap is per-site.  The reliable
# signal is the returned span's END versus END_DATE, which is why the check below now fires
# on a short span as well as on a round count.
#
# This also RETRACTS two standing diagnoses in CLAUDE.md's "a low-yield feed is usually the
# source's silence" section.  `dodge_nature` and `visit_bemidji` are named there as the
# canonical content-gap examples ("Dodge Nature Center has simply published nothing past
# August"; bemidji "shrunk to 11 annual placeholders").  Both were FETCH defects: the events
# existed and we were failing to ask for them.  `visit_faribault` is the control that makes
# this safe to act on -- its iCal was NOT truncated (span ran to 2027-02-05) and it returns
# 12 in-window by BOTH methods, so REST is not inflating counts.  Second control: every one
# of the 177 iCal rows appears in the REST set (0 missing, all 8 sources), so REST is a
# strict superset, not a different dataset.
ICAL_FEEDS = [
    # winona_library RETIRED 2026-08-30. `winona.lib.mn.us/events/list/?ical=1` has
    # returned 403 on three consecutive runs (08-28, 08-29, 08-30). event-source-calendars.md
    # §4 already lists it as a dead end with "stop retrying it every run", but it was still
    # being dispatched, so it logged an identical ERROR every run -- the permanent-warning
    # failure mode that trains the reader to skim the whole block. `visit_winona` still
    # covers the city (via TRIBE_FEEDS since 2026-09-11), so nothing is lost.
    ("krls", "https://krls.org/feed/my-calendar-ics/", ""),
    ("ecrl", "https://ecrlib.libcal.com/ical_subscribe.php?src=p&cid=13690", ""),
]

# ---------------------------------------------------------------- 1b. The Events Calendar
# WordPress REST, same class of endpoint `run_decc()` already uses.  The date filter IS
# honored here (verified per host: 0 out-of-window rows returned), unlike BiblioCommons,
# which ignores startDate/endDate -- but `in_window()` is still applied belt-and-braces,
# because a server-side filter is a claim until each host has been checked and hosts change.
TRIBE_FEEDS = [
    ("visit_bemidji", "www.visitbemidji.com", "Bemidji, MN"),
    ("brainerd", "calendar.brainerd.com", "Brainerd, MN"),
    ("visit_winona", "visitwinona.com", "Winona, MN"),
    ("visit_faribault", "www.visitfaribault.com", "Faribault, MN"),
    ("willmar", "willmarlakesarea.com", "Willmar, MN"),
    ("visit_marshall", "visitmarshallmn.com", "Marshall, MN"),
    ("explore_alex", "www.explorealex.com", "Alexandria, MN"),
    ("dodge_nature", "dodgenaturecenter.org", "365 Marie Ave W, West St Paul, MN"),
]

# Minnesota bounding box -- same constant the Wikimedia image layer uses to reject an
# out-of-state match.  Applied here to the venue's OWN geo_lat/geo_lng before we accept it.
MN_BBOX = (43.0, 49.6, -97.6, -89.2)

# A feed whose last event is a few days short of END_DATE has simply not got an event booked
# on the window's final day -- which is the normal state of a small-town calendar, not a
# truncation.  Reporting it anyway is the permanent-WARN failure mode: `winona_library` and
# `great_pumpkin_trail` both show that a warning which fires every run stops being read, and
# then the one run it matters is skimmed past too.  7 days was chosen against this run's
# measurements: the genuinely-truncated feeds were 35-49 days short, the genuinely-quiet
# tails were 1 day short, so the gap between the two populations is wide and nothing sits
# near the boundary.
SPAN_SHORT_DAYS = 7


def span_status(count, last_date, ceiling_hit=False):
    """Classify a feed's returned span.  Shared by run_ical() and run_tribe_rest() so the
    two dispatch paths cannot drift apart -- the exact failure that let `ecrl` sit in
    ICAL_FEEDS exempt from the 500-cap guard written for its own feed type.

      CAPPED -- we stopped being served. A FETCH defect: the events exist and we are failing
                to ask for them, so the remedy is a better request (paging, date bounds).
      SHORT  -- the source is quiet at the tail. Record and re-probe; "fixing" it would mean
                inventing rows.  Informational, never an error.
      OK     -- reaches the window, or is short by less than SPAN_SHORT_DAYS.
    """
    # Ceiling first, and BEFORE the span margin. Hitting our own page ceiling means we
    # stopped asking, which is a fetch defect no matter what span we happened to collect --
    # a feed can reach END_DATE and still have more we never requested. Testing the span
    # first returned a confident "OK" for exactly that case.
    if ceiling_hit:
        return "CAPPED"
    if not last_date:
        return "OK"                      # an empty feed is not a truncated one
    try:
        gap = (date.fromisoformat(END) - date.fromisoformat(last_date)).days
    except ValueError:
        return "OK"
    if gap < SPAN_SHORT_DAYS:
        return "OK"
    return "CAPPED" if count in (30, 50, 100, 200, 250, 500, 1000) else "SHORT"

# A WordPress "My Calendar" ICS export is MONTH-SCOPED, and its default serves only the
# CURRENT month (found 2026-09-12).  `krls` returned 17 VEVENTs spanning 2026-09-01..09-24 --
# a plausible, correctly-parsed, stable-across-runs number for a small regional system, which
# is exactly the signature event-source-calendars.md §1.1 records for The Events Calendar's
# `?ical=1`.  Asking the SAME url with `?month=10&yr=2026` returns a DIFFERENT 9 events; the
# whole back half of the window was structurally invisible, so Kitchigami's October
# programming (Park Rapids / Pine River storytimes, book sales, art clubs) could never land.
#
# This is the fourth instance of the same class, and the second one where the export looked
# healthy: `?ical=1` (8 Tribe sources), the LibCal 500-cap, the LibCal `api_events.php`
# today-only regression, and now this.  The generalisation CLAUDE.md already states holds --
# prefer a date-bounded request to an export -- but note what actually caught it: `span_status`
# flagged `krls` SHORT one run after being built.  The count (6 in-window) was unremarkable
# and no count-based check would ever have fired; the SPAN was the signal, as designed.
#
# Kept as a NAMED SET rather than a URL-shape sniff on `/feed/my-calendar-ics/`.  A sniff
# would silently start rewriting the request for any future source matching the pattern,
# and a wrong month argument returns 200 with a plausible subset -- the failure mode is a
# quietly smaller feed, not an error.  event-source-calendars.md flags "My Calendar" as a
# replicable pattern, so the next source added on it joins this set explicitly.
MONTH_LOOP_ICAL = {"krls"}


def month_urls(url, today, end):
    """One URL per calendar month spanned by [today, end], for a month-scoped ICS export.

    The bare url is fetched FIRST and kept in the list: the default (current-month) response
    and `?month=<this month>` were byte-equivalent in the probe, but that is an observation
    about one host on one day, not a guarantee, and a duplicate costs one request while a
    missing month costs a third of the window.  De-duplication happens on (UID, DTSTART)
    after parsing, so an overlapping fetch cannot inflate the row count.

    Fetches ONE MONTH PAST `end`.  The per-request response is itself capped (~9-17 events),
    so `month=10` came back spanning 2026-09-25..2026-10-17 while the 2026-10-30 storytime
    appeared only under `month=11`.  The month argument therefore selects a STARTING POINT,
    not a closed interval, and stopping at END's own month leaves a hole in the last two
    weeks of the window -- the very tail the export was truncating in the first place.
    """
    y, m = int(today[:4]), int(today[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    if (ey, em) < (y, m):
        raise ValueError(f"month_urls: end {end} precedes today {today}")
    ey, em = (ey + 1, 1) if em == 12 else (ey, em + 1)      # one month past END
    sep = "&" if "?" in url else "?"
    out = [url]
    while (y, m) <= (ey, em):
        out.append(f"{url}{sep}month={m}&yr={y}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


ECRL_BRANCH_CITY = {
    "cambridge": "Cambridge", "isanti": "Isanti", "north branch": "North Branch",
    "chisago": "Chisago City", "milaca": "Milaca", "mille lacs": "Isle",
    "isle": "Isle", "mora": "Mora", "pine city": "Pine City",
    "princeton": "Princeton", "rush city": "Rush City", "hinckley": "Hinckley",
    "sandstone": "Sandstone", "braham": "Braham", "cambridge public": "Cambridge",
}


def run_ical():
    print("\n=== 1. iCal feeds (CVB / library / nature centers) ===")
    for name, url, default_addr in ICAL_FEEDS:
        urls = month_urls(url, TODAY, END) if name in MONTH_LOOP_ICAL else [url]
        nbytes, evs, seen, errs = 0, [], set(), []
        for u in urls:
            try:
                txt = http(u, timeout=90)
            except Exception as e:
                errs.append(f"{type(e).__name__}: {str(e)[:40]}")
                continue
            nbytes += len(txt)
            if "BEGIN:VEVENT" not in txt:
                continue
            for ev in ical_events(txt):
                # De-duplicate across the month fetches.  DTSTART is part of the key because
                # a recurring series shares one UID across its occurrences, and CLAUDE.md's
                # standing rule is that time is a SEPARATOR: collapsing on UID alone would
                # merge a weekly storytime into a single row -- the `_dedup4` failure,
                # reached from the fetcher instead of from a dedup pass.
                k = (ev.get("UID", ""), ev.get("DTSTART", ""))
                if k in seen:
                    continue
                seen.add(k)
                evs.append(ev)
        if not evs:
            if errs:
                log(name, "ERROR", 0, "; ".join(errs[:2]))
            else:
                log(name, "NOFEED", 0, f"no VEVENT in {nbytes}b across {len(urls)} fetch(es)")
            continue
        n = 0
        for ev in evs:
            d = ical_date(ev.get("DTSTART", ""), ev.get("DTSTART_P", ""))
            if not in_window(d):
                continue
            loc = ev.get("LOCATION", "") or ev.get("ORG_CN", "")
            addr = loc or default_addr
            if name == "ecrl":
                blob = (loc + " " + ev.get("ORG_CN", "")).lower()
                city = next((v for k, v in ECRL_BRANCH_CITY.items() if k in blob), "")
                addr = f"{loc}, {city}, MN" if city else loc
            elif default_addr and not re.search(r"\d", addr):
                addr = f"{addr}, {default_addr}" if addr else default_addr
            RESULTS.append(row(ev.get("SUMMARY", ""), ev.get("DESCRIPTION", ""), addr,
                               d, ical_time(ev.get("DTSTART", ""), ev.get("DTSTART_P", "")),
                               ev.get("URL", ""), name))
            n += 1
        # Truncation check -- added 2026-09-10, ported verbatim in spirit from run_libcal().
        # The 500-cap detector was written for the LIBCAL dispatch path only, but `ecrl` is a
        # LibCal system that happens to be configured as an ICAL_FEEDS row, so it was
        # STRUCTURALLY EXEMPT from the very guard designed for its feed type: it returned
        # exactly 500 VEVENTs this run and logged a clean "OK". Its span reached 2026-11-13,
        # past END, so nothing was actually lost -- but that was luck, not a check, and the
        # luck runs out the first time east-central programming gets denser.
        # Same shape as the LIBRARY_SRC/dispatch and deals_yield/SOURCE_KEYS drifts: a guard
        # bolted to one registry while a second registry names the same kind of source. A round
        # number at a limit boundary is a truncation signal, so test it wherever an iCal feed is
        # read -- CLAUDE.md already says "for every iCal source"; only one path obeyed it.
        #
        # GENERALISED 2026-09-11. The check above keyed on `len(evs) >= 500`, which is the
        # LibCal cap. Eight CVB feeds were being truncated by The Events Calendar's
        # list-view export at 30 / 11 / 5 -- none of them round numbers at 500 -- and every
        # one logged a clean "OK". A guard written around ONE limit's magic number cannot
        # see a second limit, the same way the 500-detector bolted to the LIBCAL dispatch
        # could not see `ecrl` sitting in ICAL_FEEDS.
        #
        # So the count is no longer the signal; the returned SPAN is. Any feed whose last
        # event lands before END_DATE is reported, because an iCal export that stops short
        # of the window is either truncated or genuinely empty at the tail -- and those two
        # diagnoses lead opposite ways, so the run must SEE it rather than be told "OK".
        # They are deliberately given different statuses, not merged:
        #   CAPPED -- count sits at a known limit AND the span stops short. A fetch defect:
        #             the events exist and we are failing to ask for them. Fix the request.
        #   SHORT  -- span stops short at an unremarkable count. Probably the source's own
        #             silence (the Dodge Nature / Bemidji reading). Record and re-probe;
        #             "fixing" it would mean inventing rows.
        # SHORT is NOT a warning -- treating an ordinary content gap as an error is the
        # permanent-WARN failure mode this project has hit three times.
        alld = sorted(x for x in (ical_date(e.get("DTSTART", ""), e.get("DTSTART_P", "")) for e in evs) if x)
        status = span_status(len(evs), alld[-1] if alld else "")
        log(name, status, n,
            f"{len(evs)} VEVENT total, {nbytes//1024}KB"
            + (f", {len(urls)} month fetches" if len(urls) > 1 else "")
            + (f"; partial: {errs[0]}" if errs else "")
            + (f", span {alld[0]}..{alld[-1]}" if alld else "")
            + (f"  <-- count at a limit boundary AND span stops short of {END}: fetch defect"
               if status == "CAPPED" else
               f"  <-- span stops short of {END}; source silence, record and re-probe"
               if status == "SHORT" else ""))


# ---------------------------------------------------------------- 2. RSS
RSS_FEEDS = [
    ("rochester_rss", "https://www.experiencerochestermn.com/event/rss/", "Rochester, MN"),
    ("richfield", "https://www.richfieldmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml", "Richfield, MN"),
    ("maplewood", "https://www.maplewoodmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml", "Maplewood, MN"),
    ("south_st_paul", "http://www.southstpaulmn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml", "South St. Paul, MN"),
    ("burnsville", "https://www.burnsvillemn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml", "Burnsville, MN"),
    ("lakeville", "https://www.lakevillemn.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml", "Lakeville, MN"),
]

# event-source-calendars.md: CivicPlus items are dominated by governance; hard filter.
GOV_RE = re.compile(r"\b(city council|council meeting|planning commission|commission|"
                    r"board meeting|park board|hra|eda|workshop|public hearing|hearing|"
                    r"study session|advisory|charter|canvass|closed session|"
                    r"utilities commission|economic development authority)\b", re.I)

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


def parse_desc_date(desc):
    """CivicPlus puts the REAL event date in <description>, not <pubDate>."""
    t = clean(desc, 400)
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})", t)
    if m and m.group(1).lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""


def parse_time(desc):
    m = re.search(r"(\d{1,2}):(\d{2})\s*([APap][Mm])", clean(desc, 400))
    return f"{int(m.group(1))}:{m.group(2)} {m.group(3).upper()}" if m else ""


def run_rss():
    print("\n=== 2. RSS feeds (CVB + CivicPlus city calendars) ===")
    for name, url, default_addr in RSS_FEEDS:
        try:
            txt = http(url, timeout=60)
        except Exception as e:
            log(name, "ERROR", 0, f"{type(e).__name__}: {str(e)[:70]}")
            continue
        items = re.findall(r"<item>(.*?)</item>", txt, re.S | re.I)
        if not items:
            log(name, "NOFEED", 0, f"0 <item> in {len(txt)}b")
            continue
        n = 0
        gov = 0
        for it in items:
            def tag(t):
                m = re.search(rf"<{t}[^>]*>(.*?)</{t}>", it, re.S | re.I)
                v = m.group(1) if m else ""
                return re.sub(r"^<!\[CDATA\[|\]\]>$", "", v.strip())
            title = clean(tag("title"), 160)
            desc = tag("description")
            if GOV_RE.search(title):
                gov += 1
                continue
            d = parse_desc_date(desc) or parse_desc_date(tag("pubDate"))
            if not in_window(d):
                continue
            RESULTS.append(row(title, desc, default_addr, d, parse_time(desc),
                               tag("link"), name))
            n += 1
        log(name, "OK", n, f"{len(items)} items, {gov} governance-filtered")


# ---------------------------------------------------------------- 3. DNR JSON
def run_dnr():
    print("\n=== 3. MN DNR state-park naturalist programs (JSON) ===")
    base = ("https://webapps.dnr.state.mn.us/calendar/app?jsp=json"
            "&o=startdate&o=starttime&k=stpk&ae=y&p=")
    total = 0
    for p in ("thismonth", "nextmonth"):
        try:
            txt = http(base + p, timeout=90)
            data = json.loads(txt)
        except Exception as e:
            log(f"dnr_{p}", "ERROR", 0, f"{type(e).__name__}: {str(e)[:70]}")
            continue
        evs = data.get("events", data if isinstance(data, list) else [])
        n = 0
        for ev in evs:
            d = (ev.get("startdate") or "")[:10]
            if not in_window(d):
                continue
            loc = ev.get("location", "")
            RESULTS.append(row(
                ev.get("title", ""), ev.get("description", ""),
                f"{loc}, MN" if loc and "MN" not in loc else loc,
                d, ev.get("starttime", ""), ev.get("location_url", ""),
                "dnr_stpk", "outdoors,nature,free,state park"))
            n += 1
        total += n
        log(f"dnr_{p}", "OK", n, f"{len(evs)} events returned")
    return total


# ---------------------------------------------------------------- 4. BiblioCommons
# sppl added 2026-09-07.  SKILL.md:848 mandates all THREE BiblioCommons systems, but only
# hclib+rclreads were ever dispatched -- the same absent-not-broken failure class as DECC:
# a mandated source that is MISSING raises no error and is invisible to every yield and
# coverage check, because those only inspect sources they already know about.
# event-source-calendars.md:172 called sppl "redundant with Ramsey County for coverage
# purposes".  That claim was tested on 2026-09-07 and is FALSE.  SPPL's 14 branches are the
# CITY of Saint Paul (Rondo, Sun Ray, Highland Park, Rice Street, Riverview, Dayton's Bluff,
# Arlington Hills, Hamline Midway, Hayden Heights, Merriam Park, Saint Anthony Park, West
# 7th, George Latimer Central, Mobile Library); Ramsey County's 8 are the SUBURBS (Roseville,
# Maplewood, Shoreview, White Bear Lake, ...).  Zero branch overlap -- disjoint systems.
BIBLIO = [("hclib", "Hennepin County Library"), ("rclreads", "Ramsey County Library"),
          ("sppl", "Saint Paul Public Library")]


def biblio_paged(code, path, per=50, cap=200):
    """Both endpoints paginate; page to exhaustion or you capture only the head.
    Payload shape: {<path>: {results|items, pagination}, entities: {<path>: {id: obj}}}.
    The entity dict is the authoritative object — the results list is only ids."""
    ents, page = {}, 1
    while page <= cap:
        url = (f"https://gateway.bibliocommons.com/v2/libraries/{code}/{path}"
               f"?limit={per}&page={page}")
        try:
            data = json.loads(http(url, timeout=60))
        except Exception:
            break
        got = (data.get("entities") or {}).get(path) or {}
        ents.update(got)
        pg = (data.get(path) or {}).get("pagination") or {}
        if not got or page >= (pg.get("pages") or 1):
            break
        page += 1
    return ents


def run_biblio():
    print("\n=== 4. BiblioCommons (paginated; startDate/endDate IGNORED by server) ===")
    for code, label in BIBLIO:
        # join to /locations for real street addresses -- never hardcode branch codes
        locs = biblio_paged(code, "locations", per=25)
        lmap = {}
        for lid, L in locs.items():
            a = L.get("address") or {}
            street = " ".join(x for x in [a.get("number"), a.get("street")] if x)
            parts = [street, a.get("city"), a.get("state"), a.get("zip")]
            addr = ", ".join(p for p in parts if p)
            lmap[str(lid)] = addr or f"{L.get('name','')}, MN"
        evs = biblio_paged(code, "events", per=50)
        n = cancelled = 0
        for eid, ev in evs.items():
            de = ev.get("definition") or {}
            d = (de.get("start") or ev.get("indexStart") or "")[:10]
            if not in_window(d):
                continue          # server ignores the bounds; filter client-side
            if str(de.get("isCancelled")).lower() == "true":
                cancelled += 1
                continue
            addr = lmap.get(str(de.get("branchLocationId") or ""), "") or f"{label}, MN"
            t = (de.get("start") or "")[11:16]
            tm = ""
            if re.match(r"\d\d:\d\d", t):
                h, mi = int(t[:2]), t[3:]
                tm = f"{h % 12 or 12}:{mi} {'AM' if h < 12 else 'PM'}"
            RESULTS.append(row(
                de.get("title", ""), de.get("description", ""), addr, d, tm,
                f"https://{code}.bibliocommons.com/events/{eid}", code))
            n += 1
        log(code, "OK", n, f"{len(evs)} events fetched, {len(lmap)} branches joined, "
                           f"{cancelled} cancelled dropped")


# ---------------------------------------------------------------- 5. LibCal
# cid values re-verified 2026-08-28 by reading each system's /calendar page for its
# default cid, then confirming the ical feed returns in-window VEVENTs.
# carverlib 9314 and griver 18620 were previously UNRESOLVED ("cal_id=0 yields nothing").
#
# 5-tuple: (key, host, cid, default_city, default_venue).  Both defaults are consulted ONLY
# when the row's own text yields nothing.  They are correct for a SINGLE-LIBRARY calendar,
# where the venue and city are properties of the CID; they must stay "" for a county
# AGGREGATE cid, where stamping one city on every branch is the wrong-CITY defect
# (CLAUDE.md: a wrong city passes every guard).
#
# `default_venue` is needed because these two feeds put a STAFF MEMBER in ORGANIZER;CN
# ("Kamra Heldman"), where the aggregate feeds put the branch name.  Without it the
# `branch or room` rule below writes a person's name into the address field.
#
# stillwater_libcal / bayport_libcal added 2026-09-16.  Both sit on the Washington County
# LibCal TENANT but are NOT inside the county aggregate (cid 10166): measured disjoint --
# 103 in-window events, intersection with the aggregate exactly ZERO.  They are independent
# municipal libraries that merely share the host.  The same probe was run against anoka,
# dakota, carver and scott: on all four, every non-aggregate cid IS subsumed by the
# aggregate (union of new in-window rows = 0), so this fan-out is specific to washco and
# must NOT be generalised to the other five.
# A feed can be COMPLETE, HONEST, UN-TRUNCATED and still nearly empty (found 2026-09-18).
#
# `griver_libcal` (cid 18620) returned 11 VEVENTs TOTAL -- 1 in-window -- on both 2026-09-17
# and 2026-09-18, for Great River Regional Library: a THIRTY-BRANCH system covering St. Cloud
# and most of central Minnesota.  `span_status` reported OK, and it was RIGHT to: the feed's
# span reaches 2027-01-18, far past END_DATE, so nothing is being truncated.  We are being
# served the whole of a near-empty umbrella calendar that the branches do not publish into.
#
# That is a FOURTH truncation-adjacent class, and the existing detector is structurally blind
# to it.  `span_status` measures whether we were CUT OFF; this feed was not.  Nothing in the
# pipeline compares a feed's size against the size of the INSTITUTION behind it, so a wrong
# cid looks exactly like a quiet library.  Both count-based and span-based checks return
# "fine", which is the two-signals-agree failure the run-date skew already demonstrated.
# The tell was neither: it was reading the source list and noticing that a regional system
# serving ~30 cities was contributing one row.
#
# Per-branch calendars measured 2026-09-18 before wiring (the measure-before-acting rule):
# 386 in-window rows against the umbrella's 1.  Kept as an EXPLICIT HAND TABLE of cids, not
# an auto-discovery scrape of /calendar -- the same argument `MONTH_LOOP_ICAL` records: a
# sniff silently starts rewriting requests when the host's markup changes, and a wrong cid
# returns 200 with a plausible subset, so the failure mode is a quietly smaller feed rather
# than an error.  Each cid was read off that branch's own LibCal page and every city was
# checked against the gazetteer (30/30) before this table was written.
#
# The umbrella cid 18620 is DELIBERATELY KEPT below.  It costs one request, it may carry
# system-wide events no branch publishes, and the dedup chain handles any overlap -- the same
# trade `month_urls()` makes when it keeps the bare URL alongside the per-month ones.
#
# `Saint Cloud` / `Saint Michael` are spelled the GAZETTEER's way, not the library's.  The
# branch is named "St. Cloud Public Library" and `st. cloud` is absent from the gazetteer, so
# the city field must carry `Saint Cloud` or the address branch of mn_city_resolve cannot
# fire and the largest city in this source resolves city-less.  The VENUE name keeps the real
# spelling; only the city token is normalized.
LIBCAL = [
    ("anoka_libcal", "anokacounty.libcal.com", 9233, "", ""),
    ("washco_libcal", "washcolib.libcal.com", 10166, "", ""),
    ("dakota_libcal", "dakotacountylibrary.libcal.com", 9306, "", ""),
    ("carver_libcal", "carverlib.libcal.com", 9314, "", ""),
    ("griver_libcal", "events.griver.org", 18620, "", ""),
    ("scott_libcal", "scottlib.libcal.com", 10242, "", ""),
    ("stillwater_libcal", "washcolib.libcal.com", 10442, "Stillwater",
     "Stillwater Public Library"),
    ("bayport_libcal", "washcolib.libcal.com", 10451, "Bayport",
     "Bayport Public Library"),
    # --- Great River Regional per-branch calendars (see the note above) --------------
    # INLINED here, never a separate list concatenated with `+`.  The first cut wrote
    # `LIBCAL = [...] + GRIVER_BRANCHES`, and compile_step3._assert_library_src_covers_fetcher()
    # -- the registry-drift alarm that exists to make exactly this mistake loud -- PASSED,
    # because it slices this literal by BRACKET DEPTH and everything past the closing `]` is
    # invisible to it.  All 30 sources would have reached STEP 4.8 untagged while the check
    # guarding against that reported success: the failure its own docstring names ("a check
    # that cannot fail correctly is worse than no check"), reproduced by handing it a second
    # table to miss.  One table, one parser.  Do not re-split this.
    ("griver_albany", "events.griver.org", 18245, "Albany", "Albany Public Library"),
    ("griver_annandale", "events.griver.org", 18246, "Annandale", "Annandale Public Library"),
    ("griver_becker", "events.griver.org", 18247, "Becker", "Becker Public Library"),
    ("griver_belgrade", "events.griver.org", 18248, "Belgrade", "Belgrade Public Library"),
    ("griver_biglake", "events.griver.org", 18249, "Big Lake", "Big Lake Public Library"),
    ("griver_buffalo", "events.griver.org", 18250, "Buffalo", "Buffalo Public Library"),
    ("griver_clearwater", "events.griver.org", 18251, "Clearwater", "Clearwater Public Library"),
    ("griver_cokato", "events.griver.org", 18252, "Cokato", "Cokato Public Library"),
    ("griver_coldspring", "events.griver.org", 18253, "Cold Spring", "Cold Spring Public Library"),
    ("griver_delano", "events.griver.org", 18254, "Delano", "Delano Public Library"),
    ("griver_eaglebend", "events.griver.org", 18255, "Eagle Bend", "Eagle Bend Public Library"),
    ("griver_elkriver", "events.griver.org", 18256, "Elk River", "Elk River Public Library"),
    ("griver_foley", "events.griver.org", 18257, "Foley", "Foley Public Library"),
    ("griver_greyeagle", "events.griver.org", 18258, "Grey Eagle", "Grey Eagle Public Library"),
    ("griver_howardlake", "events.griver.org", 18259, "Howard Lake", "Howard Lake Public Library"),
    ("griver_kimball", "events.griver.org", 18260, "Kimball", "Kimball Public Library"),
    ("griver_littlefalls", "events.griver.org", 18261, "Little Falls", "Little Falls Public Library"),
    ("griver_longprairie", "events.griver.org", 18262, "Long Prairie", "Long Prairie Public Library"),
    ("griver_melrose", "events.griver.org", 18263, "Melrose", "Melrose Public Library"),
    ("griver_monticello", "events.griver.org", 18264, "Monticello", "Monticello Public Library"),
    ("griver_paynesville", "events.griver.org", 18265, "Paynesville", "Paynesville Public Library"),
    ("griver_pierz", "events.griver.org", 18266, "Pierz", "Pierz Public Library"),
    ("griver_richmond", "events.griver.org", 18267, "Richmond", "Richmond Public Library"),
    ("griver_rockford", "events.griver.org", 18268, "Rockford", "Rockford Public Library"),
    ("griver_royalton", "events.griver.org", 18269, "Royalton", "Royalton Public Library"),
    ("griver_saukcentre", "events.griver.org", 18271, "Sauk Centre", "Sauk Centre Public Library"),
    ("griver_staples", "events.griver.org", 18272, "Staples", "Staples Public Library"),
    ("griver_stcloud", "events.griver.org", 18223, "Saint Cloud", "St. Cloud Public Library"),
    ("griver_stmichael", "events.griver.org", 18270, "Saint Michael", "St. Michael Public Library"),
    ("griver_swanville", "events.griver.org", 18273, "Swanville", "Swanville Public Library"),
]

BRANCH_CITY = {
    # Anoka County
    "mississippi": "Fridley", "centennial": "Circle Pines", "north central": "Ham Lake",
    "northtown": "Blaine", "johnsville": "Blaine", "crooked lake": "Coon Rapids",
    "rum river": "Anoka", "st. francis": "St. Francis", "st francis": "St. Francis",
    "columbia heights": "Columbia Heights",
    # Scott County
    "savage": "Savage", "prior lake": "Prior Lake", "shakopee": "Shakopee",
    "new prague": "New Prague", "jordan": "Jordan", "belle plaine": "Belle Plaine",
    "elko new market": "Elko New Market",
    # Washington County
    "stafford": "Woodbury", "oakdale": "Oakdale", "hardwood creek": "Forest Lake",
    "lake elmo": "Lake Elmo", "park grove": "Cottage Grove", "wildwood": "Mahtomedi",
    "valley library": "Lakeland", "stillwater": "Stillwater", "newport": "Newport",
    "marine": "Marine on St. Croix",
    # Dakota County
    "burnhaven": "Burnsville", "galaxie": "Apple Valley", "heritage": "Lakeville",
    "inver glen": "Inver Grove Heights", "kaposia": "South St. Paul",
    "pleasant hill": "Hastings", "robert trail": "Rosemount",
    "wentworth": "West St. Paul", "farmington": "Farmington",
    # Carver County
    "chaska": "Chaska", "chanhassen": "Chanhassen", "waconia": "Waconia",
    "victoria": "Victoria", "norwood": "Norwood Young America", "watertown": "Watertown",
}


def libcal_parse(html, host, source, seen):
    """api_events.php returns HTML despite the name. Real markup (verified 2026-08-28) is
    one <table class="s-lc-ea-tb"> per event with label/value <tr> rows -- NOT the
    s-lc-ea-ev <div> the old parser looked for, and the date is prose
    ("10:15am Friday, August 28, 2026"), never ISO."""
    n = 0
    for b in re.split(r'(?=<table[^>]*class="[^"]*s-lc-ea-tb)', html)[1:]:
        m = re.search(r'href="(https?://[^"]*?/event/(\d+)[^"]*)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        url, eid, title = m.group(1), m.group(2), clean(m.group(3), 160)
        if not title or eid in seen:
            continue
        fm = re.search(r's-lc-ea-from.*?<td>\s*(?:(\d{1,2}:\d{2}\s*[ap]m)\s*)?'
                       r'\w+day,\s*([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})', b, re.S)
        if not fm:
            continue
        mon = MONTHS.get(fm.group(2).lower())
        if not mon:
            continue
        d = f"{fm.group(4)}-{mon:02d}-{int(fm.group(3)):02d}"
        if not in_window(d):
            continue
        tm = ""
        if fm.group(1):
            raw = fm.group(1).replace(" ", "")
            tm = f"{raw[:-2]} {raw[-2:].upper()}"
        # Location = room; Library = branch. The branch is what names the city.
        room = re.search(r's-lc-ea-tloc.*?<td>\s*([^<]{2,90})', b, re.S)
        lib = re.search(r'Library:.*?<td>\s*([^<]{2,90})', b, re.S)
        room = clean(room.group(1), 90) if room else ""
        branch = clean(lib.group(1), 90) if lib else ""
        blob = f"{branch} {room}".lower()
        city = next((v for k, v in BRANCH_CITY.items() if k in blob), "")
        loc = branch or room
        addr = f"{loc}, {city}, MN" if city else (f"{loc}, MN" if loc else "")
        seen.add(eid)
        RESULTS.append(row(title, "", addr, d, tm, url, source))
        n += 1
    return n


def run_libcal():
    """VERIFIED 2026-08-28: `api_events.php` now ignores BOTH `date` and `days` -- it
    returns "Today's Events" for every request (Anoka: identical 3 event ids for
    date=08-28, 09-15 and 09-29). event-source-calendars.md \u00a73 says to prefer it over
    ical_subscribe because the ical feed "truncates on fetch"; that truncation is a
    ~450KB WebFetch ceiling, NOT an HTTP one. Read raw and the 741KB Anoka feed arrives
    whole. So the \u00a73 preference is inverted here: use ical_subscribe, read to the END.
    Feeds sort DTSTART ascending from ~4 weeks in the past and cap at 500 VEVENTs, so the
    wasted head is past events and the in-window rows are in the tail -- report the max
    DTSTART so a cap that bites before END_DATE is visible rather than silent."""
    print("\n=== 5. LibCal ical_subscribe (api_events.php ignores date/days - see docstring) ===")
    for name, host, cid, default_city, default_venue in LIBCAL:
        url = f"https://{host}/ical_subscribe.php?src=p&cid={cid}"
        try:
            txt = http(url, timeout=180)
        except Exception as e:
            log(name, "ERROR", 0, f"{type(e).__name__}: {str(e)[:70]}")
            continue
        evs = ical_events(txt)
        if not evs:
            log(name, "NOFEED", 0, f"0 VEVENT in {len(txt)}b (wrong cid?)")
            continue
        n = 0
        for ev in evs:
            d = ical_date(ev.get("DTSTART", ""), ev.get("DTSTART_P", ""))
            if not in_window(d):
                continue
            # LibCal has no /locations endpoint, so the branch name IS the city signal.
            # Anoka/Scott put the branch in ORGANIZER;CN=, Washington in LOCATION.
            room = ev.get("LOCATION", "")
            branch = ev.get("ORG_CN", "")
            blob = f"{branch} {room}".lower()
            # A single-library cid falls back to its own city. On these feeds ORGANIZER;CN
            # is a STAFF MEMBER ("Kamra Heldman"), not a branch, and LOCATION is often a
            # bare room name ("Prairie Room"), so the row carries no city signal at all --
            # BRANCH_CITY cannot fire and the row would resolve city-less. `default_city`
            # is empty for every aggregate cid, so this cannot mis-stamp a county feed.
            city = next((v for k, v in BRANCH_CITY.items() if k in blob), "") or default_city
            if default_venue:
                # Single-library cid: ORGANIZER;CN is a staff member, so `branch` must NOT
                # reach the address. Keep the room (it is real) and name the library itself.
                loc = f"{room}, {default_venue}" if room and default_venue.lower() \
                    not in room.lower() else (room or default_venue)
            else:
                loc = branch or room
            # rewrite address to the branch host city BEFORE mn_city_resolve runs,
            # so the address branch of the resolver can fire (event-source-calendars 4c)
            addr = f"{loc}, {city}, MN" if city else (f"{loc}, MN" if loc else "")
            RESULTS.append(row(ev.get("SUMMARY", ""), ev.get("DESCRIPTION", ""), addr, d,
                               ical_time(ev.get("DTSTART", ""), ev.get("DTSTART_P", "")),
                               ev.get("URL", ""), name))
            n += 1
        alld = sorted(ical_date(e.get("DTSTART", ""), e.get("DTSTART_P", "")) for e in evs)
        capped = len(evs) >= 500 and alld[-1] < END
        log(name, "CAPPED" if capped else "OK", n,
            f"{len(evs)} VEVENT, {len(txt)//1024}KB, span {alld[0]}..{alld[-1]}"
            + ("  <-- 500-cap bites before END_DATE" if capped else ""))


# ---------------------------------------------------------------- 6. DECC (Duluth)
def run_decc():
    """SKILL.md line 832 mandates the DECC Duluth feed. It was NEVER implemented --
    `grep -ci decc` returned 0 on both 2026-08-29 and 2026-08-30. A mandated source that
    is ABSENT rather than broken raises no error and is invisible to every yield and
    coverage check, because those only inspect sources they already know about.

    It is WordPress REST, not iCal. Shape verified live 2026-08-30 (86 events, 18 pages
    at per_page=5; per_page=100 returns all in one call):
      event_start_date / event_end_date -> "YYYYMMDD" (NOT ISO -- must be reformatted)
      event_start_time -> free text, often ""
      title.rendered, content.rendered, link, featured_image_url
    `featured_image_url` is the organizer's own photo served by their own API, so it is a
    real `site_photo` -- not a stock or curated fallback."""
    print("\n=== 6. DECC Duluth (WordPress REST) ===")
    url = "https://decc.org/wp-json/wp/v2/events?per_page=100"
    try:
        data = json.loads(http(url, timeout=90))
    except Exception as e:
        log("decc_duluth", "ERROR", 0, f"{type(e).__name__}: {str(e)[:70]}")
        return 0
    n = 0
    for ev in data:
        raw = (ev.get("event_start_date") or "").strip()
        if not re.fullmatch(r"\d{8}", raw):
            continue
        d = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        if not in_window(d):
            continue
        r = row((ev.get("title") or {}).get("rendered", ""),
                (ev.get("content") or {}).get("rendered", ""),
                "350 Harbor Dr, Duluth, MN 55802",
                d, clean(ev.get("event_start_time") or "", 40),
                ev.get("link", ""), "decc_duluth", "duluth,arena,entertainment")
        img = (ev.get("featured_image_url") or "").strip()
        if img.startswith("http"):
            r["image_url"] = img[:300]
            r["image_source"] = "site_photo"
        RESULTS.append(r)
        n += 1
    log("decc_duluth", "OK", n, f"{len(data)} events returned")
    return n


def _tribe_venue(ev):
    """Tribe serves `venue` as a DICT when set and as an empty LIST `[]` when not.
    Indexing it blind raises AttributeError on the empty case -- which is how this was
    found. Returns (address, phone, lat, lng, venue_name), any of which may be ''."""
    v = ev.get("venue")
    if isinstance(v, list):
        v = v[0] if v else {}
    if not isinstance(v, dict):
        return "", "", "", "", ""
    parts = [str(v.get(k) or "").strip()
             for k in ("address", "city", "state", "zip")]
    street, city, st, zp = parts
    addr = ", ".join(x for x in (street, city) if x)
    if addr and st:
        addr += f", {st}"
    if addr and zp:
        addr += f" {zp}"
    lat = lng = ""
    try:
        la, lo = float(v.get("geo_lat")), float(v.get("geo_lng"))
        # Accept the venue's own coordinate ONLY inside Minnesota. STEP 4.9 SKIPS populated
        # coordinates, so a wrong pin written here would never self-heal on any later run --
        # the Bell Museum failure mode. Outside the bbox we leave it blank and let the
        # geocode pass derive it from the address instead.
        if MN_BBOX[0] <= la <= MN_BBOX[1] and MN_BBOX[2] <= lo <= MN_BBOX[3]:
            lat, lng = f"{la:.6f}", f"{lo:.6f}"
    except (TypeError, ValueError):
        pass
    return addr, str(v.get("phone") or "").strip()[:40], lat, lng, str(v.get("venue") or "").strip()


def run_tribe_rest():
    """The Events Calendar WordPress REST -- replaces eight truncated `?ical=1` exports.

    See the TRIBE_FEEDS comment for the measurement and the two controls. The payload is
    strictly richer than the iCal LOCATION string: a structured street address, city, zip,
    phone, the venue's own coordinates, and the event's own featured image (which is the
    organizer serving their own photo from their own API -- a real `site_photo`, the same
    reading `run_decc()` applies to `featured_image_url`, not a curated fallback)."""
    print("\n=== 1b. The Events Calendar (WordPress REST) ===")
    total = 0
    for name, host, default_addr in TRIBE_FEEDS:
        rows, page, reported, pages_seen, err = [], 1, None, 0, ""
        while page <= 30:                      # 30 * 50 = 1500 event hard ceiling
            url = (f"https://{host}/wp-json/tribe/events/v1/events?per_page=50&page={page}"
                   f"&start_date={TODAY}&end_date={END}")
            try:
                data = json.loads(http(url, timeout=90))
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:60]} (page {page})"
                break
            batch = data.get("events") or []
            if not batch:
                break
            rows += batch
            reported = data.get("total", reported)
            pages_seen = page
            if page >= int(data.get("total_pages") or 1):
                break
            page += 1
        if err and not rows:
            log(name, "ERROR", 0, err)
            continue
        n, oow = 0, 0
        for ev in rows:
            d = str(ev.get("start_date") or "")[:10]
            if not re.fullmatch(r"\d{4}-\d\d-\d\d", d):
                continue
            if not in_window(d):
                oow += 1                        # server filter disagreed with us -- count it
                continue
            addr, phone, lat, lng, vname = _tribe_venue(ev)
            if not addr:
                addr = default_addr
            elif not re.search(r"\d", addr):
                addr = f"{addr}, {default_addr}" if default_addr else addr
            # "2026-09-11 10:00:00" -> "20260911T100000". The COLONS have to go too:
            # ical_time()'s regex is \d{8}T(\d{2})(\d{2}), so leaving them in makes it match
            # nothing and return "" -- a blank time on every row, with no error. Caught only
            # by asserting the conversion against known values before trusting it.
            tm = "" if ev.get("all_day") else ical_time(
                re.sub(r"[-:\s]", lambda m: "T" if m.group() == " " else "",
                       str(ev.get("start_date") or "")))
            r = row(ev.get("title", ""), ev.get("description", ""), addr, d, tm,
                    ev.get("url", ""), name)
            if vname:
                r["description"] = clean(f"{vname}. {r['description']}", 600)
            r["phone"], r["latitude"], r["longitude"] = phone, lat, lng
            img = ((ev.get("image") or {}) if isinstance(ev.get("image"), dict) else {}).get("url", "")
            if str(img).startswith("http"):
                r["image_url"], r["image_source"] = str(img)[:300], "site_photo"
            # `cost` is the organizer's OWN statement, so this is filling a blank FROM A
            # SOURCE, not the guess CLAUDE.md forbids. Anything ambiguous stays blank for
            # pricetype_fix.py -- notably a blank cost, which does NOT mean free.
            cost = str(ev.get("cost") or "").strip()
            if cost:
                r["price"] = cost[:40]
                if re.search(r"\d", cost):
                    r["price_type"] = "Paid"
                elif re.fullmatch(r"(?i)free", cost):
                    r["price_type"] = "Free"
            RESULTS.append(r)
            n += 1
        alld = sorted(str(e.get("start_date") or "")[:10] for e in rows if e.get("start_date"))
        # Same span test as run_ical(). A paged endpoint we walked to total_pages should
        # never be short, so a short span here means the SOURCE is quiet, not that we
        # stopped asking -- unless we hit the 30-page ceiling, which is a real cap.
        ceil_hit = pages_seen >= 30
        status = span_status(len(rows), alld[-1] if alld else "", ceiling_hit=ceil_hit)
        log(name, status, n,
            f"{len(rows)} fetched of {reported} reported, {pages_seen}p"
            + (f", span {alld[0]}..{alld[-1]}" if alld else "")
            + (f", {oow} out-of-window dropped" if oow else "")
            + (f"; partial: {err}" if err else "")
            + ("  <-- 30-page ceiling hit" if ceil_hit else ""))
        total += n
    return total


def run_espn_sports():
    """STEP 2 structured sports intake via espn_sports.py (ESPN hidden JSON API).

    ADDITIVE + SOFT-FAIL by construction (espn_sports rule 1): a total ESPN outage, an import
    failure, or a bad JSON response contributes ZERO rows and cannot break the nightly -- the
    season-gated sports_coverage.py tripwire remains the safety net either way.  This is why the
    source can be wired before its reachability from the pipeline UA is proven in production:
    the worst case is "no worse than today", where sports entered only via free-text WebSearch.
    """
    try:
        import espn_sports as S
    except Exception as e:  # noqa: BLE001 -- an import failure must not abort the fetch run
        log("espn_sports", "ERROR", 0, f"import failed: {type(e).__name__}: {str(e)[:120]}")
        return 0
    rows, reports = S.fetch_all(TODAY, END, http, row)
    for rep in reports:
        log(rep["source"], rep["status"], rep.get("in_window", 0), rep.get("note", ""))
    RESULTS.extend(rows)
    return len(rows)


def run_kid_chains():
    """STEP 2 structured kid-chain intake via kid_chains.py (recurring free chain programs).

    ADDITIVE + SOFT-FAIL by construction (kid_chains rule 1): an import failure or a malformed
    registry entry contributes ZERO rows and cannot break the nightly.  Purely generative -- no
    network -- so the dated occurrences regenerate against the current window every run, which is
    why a chain program listed here never goes stale the way a one-time hand-add would.
    """
    try:
        import kid_chains as K
    except Exception as e:  # noqa: BLE001 -- an import failure must not abort the fetch run
        log("kid_chains", "ERROR", 0, f"import failed: {type(e).__name__}: {str(e)[:120]}")
        return 0
    rows, reports = K.fetch_all(TODAY, END, None, row)
    for rep in reports:
        log(rep["source"], rep["status"], rep.get("in_window", 0), rep.get("note", ""))
    RESULTS.extend(rows)
    return len(rows)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.time()
    if which in ("all", "sports"):
        run_espn_sports()
    if which in ("all", "chains"):
        run_kid_chains()
    if which in ("all", "decc"):
        run_decc()
    if which in ("all", "tribe"):
        run_tribe_rest()
    if which in ("all", "ical"):
        run_ical()
    if which in ("all", "rss"):
        run_rss()
    if which in ("all", "dnr"):
        run_dnr()
    if which in ("all", "biblio"):
        run_biblio()
    if which in ("all", "libcal"):
        run_libcal()
    out = f"_feedpull_{which}.json"
    json.dump({"rows": RESULTS, "report": REPORT}, open(out, "w"), ensure_ascii=False)
    print(f"\nTOTAL in-window rows: {len(RESULTS)}  ->  {out}  ({time.time()-t0:.0f}s)")
