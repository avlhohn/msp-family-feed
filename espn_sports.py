#!/usr/bin/env python3
"""STEP 2 structured sports intake -- ESPN hidden JSON API.  Folder root, undated.

WHY THIS EXISTS
---------------
Sports are in scope (SKILL.md:44) and belong in `events`.  Until now they entered ONLY via
STEP 2 free-text WebSearch -- an untagged, non-deterministic path -- which is how Minnesota
United silently contributed zero rows on 2026-09-19 with home games plainly on the calendar
(see sports_coverage.py, the STEP 8 tripwire that DETECTS the gap).  This module is the
deterministic SOURCE that closes it: one JSON schedule call per team, home games only, mapped
to the same event-row shape every other fetcher emits.

DESIGN RULES (each of these is load-bearing; breaking one fails silently)
-------------------------------------------------------------------------
1. ADDITIVE + SOFT-FAIL.  ESPN's API is unofficial and has been observed to 403 non-browser
   agents.  `fetch_all()` wraps every per-team fetch in try/except and returns ([], ERROR-note)
   on ANY failure, so a total ESPN outage contributes zero rows and CANNOT break the nightly.
   The season-gated sports_coverage.py tripwire remains the safety net either way.  This is why
   the module can be wired before ESPN reachability from the pipeline UA is proven: the worst
   case is "no worse than today."

2. HOME GAMES ONLY, IN-WINDOW ONLY.  A family guide lists things to attend locally; an away
   game is not one.  The home filter reads ESPN's own `homeAway` flag on the competitor that
   matches THIS team (resolved from the schedule's top-level `team` block, never guessed).

3. UTC -> America/Chicago BEFORE the date test, but ONLY when ESPN says the time is REAL.
   ESPN stamps kickoff in UTC; a 7pm CT game is ~00:00-01:00 UTC the NEXT day, so a naive date
   slice drops or misfiles evening games -- the exact off-by-one class CLAUDE.md documents for
   the run window.  Conversion uses zoneinfo.

   3b. `timeValid: False` MEANS THE TIMESTAMP IS A PLACEHOLDER AND MUST NOT BE CONVERTED
   (found 2026-09-21, live, in a published-bound feed).  When a kickoff has not been announced
   ESPN still emits a full ISO timestamp -- and the placeholder it uses is MIDNIGHT EASTERN,
   i.e. 04:00Z under EDT and 05:00Z under EST.  Converted to America/Chicago that is 23:00 on
   the PREVIOUS DAY, so the row is filed one day early while looking entirely well-formed:

       2026-10-03T04:00Z  timeValid=False  ->  filed 2026-10-02, "11:00 PM"   WRONG
       2026-10-03T04:00Z  timeValid=False  ->  filed 2026-10-03, time ""      correct

   A wrong DATE is the most damaging defect this feed can ship -- a family arrives on the wrong
   day -- and it is invisible to every guard here, because dedup, coverage and the schema checks
   all read a date that is present and well-formed.  It was caught by reading the surviving
   sports titles after sports_dedup.py and noticing both Gophers games claimed an 11:00 PM
   kickoff.  Big Ten football is played on Saturdays; the UTC date is Saturday and the converted
   date is Friday, which is what made the diagnosis decisive rather than a guess.

   So when `timeValid` is False the date is taken from the RAW UTC DATE PREFIX with no
   conversion, and `time` is emitted EMPTY rather than fabricated.  Two notes on that choice:

   * The raw prefix is used in preference to converting to America/New_York, even though
     reconstructing ESPN's own midnight is the more "principled" reading.  Both agree on a
     midnight-Eastern placeholder, but only the raw prefix is also correct if a league ever
     uses a midnight-UTC placeholder instead -- and it assumes nothing about ESPN's internal
     timezone, which is not a documented contract.
   * The flag is the ONLY evidence used.  A value-shaped heuristic ("04:00Z looks like a
     placeholder") was rejected: this same schedule carries a genuine `2026-09-04T00:00Z`
     Thursday night game with timeValid=True, so guessing from the timestamp alone would blank
     a real kickoff.  Evidence that is not the name, per CLAUDE.md -- the source states the
     time is invalid, which is a fact, not a similarity score.

   An absent `timeValid` key defaults to True (convert), because a real time is the
   overwhelming majority case and ESPN flags the exception explicitly.  The pre-existing
   "00:00 local -> blank the time" guard is KEPT but must not be mistaken for this fix: it was
   the first attempt at this problem and it is structurally incapable of catching it, because
   it only ever blanks a TIME and never repairs a DATE, and the Eastern placeholder does not
   land on local midnight in the first place.

4. row_fn IS INJECTED, the schema is NOT duplicated.  Production passes fetch_feeds.row so
   there is a single source of truth for the 20-key event dict; tests pass a stub.  This avoids
   the registry-drift class (two copies of one contract that drift apart).

5. price_type = "Varies".  Pro/college games are ticketed with no single quoted price -- per
   SKILL.md that is "Varies", never "Free" (stamping Free is a claim a family acts on at a
   ticket counter).

The module NEVER fetches at import time (import must not be a write -- CLAUDE.md 2026-09-18);
all network work is behind functions and the __main__ guard.
"""
import json
import datetime as _dt

# ---- team registry -----------------------------------------------------------------------
# `ref` is the ESPN team identifier in the schedule URL.  The big-4 + WNBA resolve by the
# "min" abbreviation; MLS requires the numeric id (17362, confirmed 2026-09-20); college uses
# the program id.  `active_months` gates a team in the probe/coverage sense only -- the fetch
# itself is harmless year-round (an off-season schedule simply returns no in-window home games).
TEAMS = [
    {"key": "twins",        "name": "Minnesota Twins",                          "sport": "baseball",   "league": "mlb",                     "ref": "min",   "tier": "pro",     "active_months": [3, 4, 5, 6, 7, 8, 9, 10]},
    {"key": "vikings",      "name": "Minnesota Vikings",                        "sport": "football",   "league": "nfl",                     "ref": "min",   "tier": "pro",     "active_months": [8, 9, 10, 11, 12, 1]},
    {"key": "timberwolves", "name": "Minnesota Timberwolves",                   "sport": "basketball", "league": "nba",                     "ref": "min",   "tier": "pro",     "active_months": [10, 11, 12, 1, 2, 3, 4, 5, 6]},
    {"key": "wild",         "name": "Minnesota Wild",                           "sport": "hockey",     "league": "nhl",                     "ref": "min",   "tier": "pro",     "active_months": [9, 10, 11, 12, 1, 2, 3, 4, 5, 6]},
    {"key": "lynx",         "name": "Minnesota Lynx",                           "sport": "basketball", "league": "wnba",                    "ref": "min",   "tier": "pro",     "active_months": [5, 6, 7, 8, 9, 10]},
    {"key": "mnufc",        "name": "Minnesota United FC",                      "sport": "soccer",     "league": "usa.1",                   "ref": "17362", "tier": "pro",     "active_months": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]},
    {"key": "gophers_fb",   "name": "Minnesota Golden Gophers Football",        "sport": "football",   "league": "college-football",        "ref": "135",   "tier": "college", "active_months": [8, 9, 10, 11, 12, 1]},
    {"key": "gophers_mbb",  "name": "Minnesota Golden Gophers Men's Basketball","sport": "basketball", "league": "mens-college-basketball", "ref": "135",   "tier": "college", "active_months": [11, 12, 1, 2, 3, 4]},
]

BASE = "https://site.api.espn.com/apis/site/v2/sports"


def schedule_url(team, seasontype=None):
    u = f"{BASE}/{team['sport']}/{team['league']}/teams/{team['ref']}/schedule"
    if seasontype is not None:
        u += f"?seasontype={seasontype}"
    return u


# ESPN's own season-phase enum, as reported in the response's `season.type`.
PRESEASON, REGULAR, POSTSEASON = 1, 2, 3


def season_type(js):
    """The `season.type` integer ESPN reports for the slate it just served, or None.

    This is the DISCRIMINATOR for the preseason-stub defect (CLAUDE.md 2026-09-27, evidenced
    2026-09-30).  `schedule_url()` sends no season parameter, so ESPN serves whatever phase it
    considers current -- and for a league whose regular season has not opened yet, that is
    PRESEASON: a handful of games masquerading as the whole slate.  Crucially, the response
    SAYS SO, in a field the old code never read.
    """
    s = (js or {}).get("season") or {}
    t = s.get("type")
    if isinstance(t, dict):          # some endpoints nest it
        t = t.get("type")
    return t if isinstance(t, int) else None


# ---- pure parsing / filtering (no network) -----------------------------------------------
def _to_local_date_time(iso, time_valid=True):
    """ESPN UTC ISO ('2026-09-22T23:10Z' or with +00:00) -> ('YYYY-MM-DD', 'H:MM AM/PM') in
    America/Chicago.  Returns ('', '') if unparseable.  TZ conversion is rule 3 above.

    `time_valid=False` is ESPN's own "kickoff not announced" flag: the timestamp is a
    midnight-Eastern PLACEHOLDER, so converting it moves the date back a day.  In that case the
    raw UTC date prefix is returned with an EMPTY time.  See rule 3b -- this is a wrong-date
    defect, not a cosmetic one."""
    if not iso:
        return "", ""
    if not time_valid:
        # Placeholder timestamp: the DATE is real, the time is not.  Do not convert.
        d = iso.strip()[:10]
        try:
            _dt.date.fromisoformat(d)
        except ValueError:
            return "", ""
        return d, ""
    s = iso.strip().replace("Z", "+00:00")
    try:
        dt = _dt.datetime.fromisoformat(s)
    except ValueError:
        return "", ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local = dt.astimezone(ZoneInfo("America/Chicago"))
    except Exception:
        # Fallback: fixed CDT/CST is wrong at the DST boundary but never crashes.
        local = dt.astimezone(_dt.timezone(_dt.timedelta(hours=-5)))
    date = local.strftime("%Y-%m-%d")
    hour = local.strftime("%I:%M %p").lstrip("0")
    # A midnight-UTC placeholder (TBD kickoff) often lands 00:00 local -> emit no time.
    if local.hour == 0 and local.minute == 0:
        hour = ""
    return date, hour


def _our_team_names(js):
    """The set of identifiers that mark THIS schedule's team as the home side: its id,
    displayName and abbreviation, from the top-level `team` block.  Never guessed."""
    t = (js or {}).get("team") or {}
    out = set()
    for k in ("id", "displayName", "shortDisplayName", "abbreviation", "name", "nickname"):
        v = t.get(k)
        if v:
            out.add(str(v).strip().lower())
    return out


def parse_home_games(js, team):
    """Return normalized home-game dicts for `team` from an ESPN schedule JSON object.
    Each: {date, time, opponent, venue, city, state, url, iso}.  Away games are dropped."""
    ours = _our_team_names(js)
    # If the top-level team block is thin, fall back to the registry name/ref.
    ours |= {team["name"].strip().lower(), str(team["ref"]).strip().lower()}
    games = []
    for ev in (js or {}).get("events", []) or []:
        comps = ev.get("competitions") or []
        if not comps:
            continue
        comp = comps[0]
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if (c.get("homeAway") == "home")), None)
        away = next((c for c in competitors if (c.get("homeAway") == "away")), None)
        if not home:
            continue
        home_team = home.get("team") or {}
        home_ids = {str(home_team.get(k, "")).strip().lower()
                    for k in ("id", "displayName", "shortDisplayName", "abbreviation", "name", "nickname")}
        home_ids.discard("")
        if not (ours & home_ids):
            continue  # our team is the away side -> not a home game
        opp_team = (away or {}).get("team") or {}
        opponent = opp_team.get("displayName") or opp_team.get("name") or opp_team.get("shortDisplayName") or "TBD"
        venue = comp.get("venue") or ev.get("venue") or {}
        addr = venue.get("address") or {}
        iso = ev.get("date") or comp.get("date") or ""
        # ESPN carries the flag on the competition; some payloads repeat it on the event.
        # ABSENT -> True (convert): a real time is the overwhelming majority case and ESPN
        # flags the placeholder explicitly.  See rule 3b.
        tv = comp.get("timeValid", ev.get("timeValid", True))
        date, tm = _to_local_date_time(iso, time_valid=(tv is not False))
        url = ""
        for ln in (ev.get("links") or []):
            if ln.get("href"):
                url = ln["href"]
                break
        games.append({
            "date": date, "time": tm, "opponent": str(opponent).strip(),
            "venue": (venue.get("fullName") or "").strip(),
            "city": (addr.get("city") or "").strip(),
            "state": (addr.get("state") or "").strip(),
            "url": url, "iso": iso,
        })
    return games


def game_key(g):
    """Stable identity for a normalized home game, for merging two slates of the SAME team.

    parse_home_games() emits NO `id` field.  The first draft of the preseason supplement below
    deduped on `g.get("id")`, which is absent on every row, so its `added` list filtered to
    empty and the supplement contributed a silent +0 -- caught by its own tests, not in
    production.  The lesson is this file's own: a key must name a field the PRODUCER actually
    writes, and the safe place to define it is beside the producer.

    The ESPN game permalink carries the gameId and is the strongest key when present; a game
    with no link falls back to its UTC timestamp plus opponent, which is unique within one
    team's schedule (a team plays one opponent at one kickoff).
    """
    u = (g.get("url") or "").strip()
    if u:
        return ("url", u)
    return ("iso", (g.get("iso") or "").strip(), (g.get("opponent") or "").strip())


def in_window(date, today, end):
    return bool(date) and today <= date <= end


def to_feed_rows(games, team, today, end, row_fn):
    """Map normalized home games (in window) to the pipeline event-row shape via row_fn.
    row_fn signature matches fetch_feeds.row(title, desc, addr, dt, tm, url, source, tags)."""
    rows = []
    for g in games:
        if not in_window(g["date"], today, end):
            continue
        title = f"{team['name']} vs. {g['opponent']}".strip()
        addr_bits = [b for b in (g["venue"], g["city"], g["state"]) if b]
        addr = ", ".join(addr_bits)
        desc = f"{team['name']} home game" + (f" at {g['venue']}" if g["venue"] else "") + "."
        url = g["url"] or schedule_url(team)
        r = row_fn(title, desc, addr, g["date"], g["time"], url, f"espn_{team['key']}", "sports")
        r["price_type"] = "Varies"   # ticketed, no single quoted price -> Varies (rule 5)
        rows.append(r)
    return rows


# ---- network layer (dependency-injected http_fn so tests stay offline) --------------------
def fetch_team(team, today, end, http_fn, row_fn):
    """(rows, report) for one team.  SOFT-FAIL: any exception -> ([], ERROR report). Never raises."""
    url = schedule_url(team)
    try:
        raw = http_fn(url)
        js = json.loads(raw)
    except Exception as e:  # noqa: BLE001 -- soft-fail is the whole point (rule 1)
        return [], {"source": f"espn_{team['key']}", "status": "ERROR",
                    "in_window": 0, "note": f"{type(e).__name__}: {str(e)[:120]}"}
    games = parse_home_games(js, team)
    stype = season_type(js)
    supp = ""

    # --- PRESEASON-STUB SUPPLEMENT (added 2026-09-30) -------------------------------------
    # Gated on the response's OWN `season.type == 1`, and strictly ADDITIVE: the bare slate is
    # always kept and the regular-season slate is merged into it, deduped by game_key() --
    # the ESPN game permalink, falling back to UTC timestamp + opponent.
    #
    # Why gated rather than always-on.  Measured against live responses for all 8 teams on
    # 2026-09-30, across a real league boundary:
    #   timberwolves type=1   6 ->  80   NBA regular season opens Oct 21  -- was a stub
    #   gophers_mbb  type=1   0 ->  32   NCAA MBB opens Nov 2             -- was a stub
    #   wild         type=2  84 ==  84   no-op; the CONTROL that proves the mechanism
    #   mnufc    type=13846  27 ->   0   soccer uses a DIFFERENT taxonomy: a blanket
    #                                    seasontype=2 DESTROYS 27 real events
    #   twins        type=3   0 -> 162   postseason/eliminated; forcing regular resurrects a
    #                                    FINISHED season (all past, but conceptually wrong)
    # So `seasontype=2` is emphatically NOT a safe blanket fix -- on 2 of 8 teams it is a large
    # correction and on 2 others it is a regression.  `type == 1` selects exactly the broken
    # case and leaves the other 6 teams byte-identical.
    #
    # Preseason home games are KEPT, not replaced: a preseason game at Target Center is a real
    # event a family can attend.  Union, never swap -- worst case is "no worse than today".
    if stype == PRESEASON:
        try:
            js2 = json.loads(http_fn(schedule_url(team, seasontype=REGULAR)))
            extra = parse_home_games(js2, team)
            seen = {game_key(g) for g in games}
            added = [g for g in extra if game_key(g) not in seen]
            games = games + added
            supp = f"; preseason stub supplemented +{len(added)} regular-season home games"
        except Exception as e:  # noqa: BLE001 -- additive: a failure leaves the bare slate intact
            supp = f"; seasontype=2 supplement FAILED ({type(e).__name__}) - bare slate kept"

    rows = to_feed_rows(games, team, today, end, row_fn)
    n_home = len(games)
    status = "OK" if rows else ("EMPTY" if n_home == 0 else "NO_HOME_IN_WINDOW")
    note = f"{n_home} home games total, {len(rows)} in [{today}..{end}] (season.type={stype}){supp}"
    return rows, {"source": f"espn_{team['key']}", "status": status,
                  "in_window": len(rows), "note": note}


def fetch_all(today, end, http_fn, row_fn):
    """(all_rows, reports) across every team.  Additive + soft-fail; safe to call unconditionally."""
    all_rows, reports = [], []
    for team in TEAMS:
        rows, rep = fetch_team(team, today, end, http_fn, row_fn)
        all_rows.extend(rows)
        reports.append(rep)
    return all_rows, reports


def probe(http_fn):
    """Reachability check for the nightly (real env): hits each team's schedule endpoint and
    reports HTTP/parse status + a home-game count, WITHOUT the window filter.  This is the
    production go/no-go the sandbox cannot run (WebFetch 403s ESPN; curl/python fetch is
    policy-barred).  Prints a table and returns the per-team report list."""
    reports = []
    for team in TEAMS:
        url = schedule_url(team)
        try:
            raw = http_fn(url)
            js = json.loads(raw)
            n = len(parse_home_games(js, team))
            total = len((js or {}).get("events", []) or [])
            reports.append({"team": team["key"], "reachable": True,
                            "events": total, "home_games": n, "note": ""})
        except Exception as e:  # noqa: BLE001
            reports.append({"team": team["key"], "reachable": False,
                            "events": 0, "home_games": 0, "note": f"{type(e).__name__}: {str(e)[:120]}"})
    width = max(len(r["team"]) for r in reports)
    for r in reports:
        flag = "OK  " if r["reachable"] else "FAIL"
        print(f"  {flag}  {r['team']:<{width}}  events={r['events']:<4} home={r['home_games']:<4} {r['note']}")
    ok = sum(1 for r in reports if r["reachable"])
    print(f"\nESPN probe: {ok}/{len(reports)} teams reachable from this environment.")
    return reports


if __name__ == "__main__":
    # Run ONLY in an environment that can reach ESPN (the nightly cloud run).  Uses the
    # pipeline's own urllib fetcher and row() so this is a true production probe.
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    import fetch_feeds as F  # imports fine only when MSP_TODAY / MSP_END are set
    if mode == "probe":
        probe(F.http)
    elif mode == "fetch":
        rows, reports = fetch_all(F.TODAY, F.END, F.http, F.row)
        for rep in reports:
            print(rep)
        print(f"\nESPN sports in-window rows: {len(rows)}")
