#!/usr/bin/env python3
"""Offline tests for espn_sports.py -- fixture-based, no network.

Every case below exercises a pure function against a hand-built ESPN-shaped fixture, so the
suite runs anywhere the sandbox does (ESPN itself 403s here -- that is exactly why the network
layer is dependency-injected and NOT tested live).  The load-bearing cases, in the sense
CLAUDE.md means it:

  * the EVENING-GAME date boundary  -- a 7:10pm CT game is ~00:10 UTC the NEXT day; a naive
    date slice misfiles it.  Two of these, one in CDT (Sept) and one in CST (Jan), because the
    off-by-one and the DST offset fail independently.
  * HOME vs AWAY filtering          -- an away game must be dropped even though our team is in it.
  * price_type == "Varies"          -- stamping "Free" is a claim a family acts on at a counter.
  * the pro-team roster             -- vikings, timberwolves, wild, twins, lynx, mnufc must all
                                       be present, or "are and will be included" is a false claim.
"""
import espn_sports as E

_pass = 0
_fail = 0


def check(name, got, want):
    global _pass, _fail
    if got == want:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {name}\n        got : {got!r}\n        want: {want!r}")


def check_true(name, cond):
    check(name, bool(cond), True)


# ---- row_fn stub: mirrors fetch_feeds.row's signature, returns a minimal 20-ish-key dict ----
def stub_row(title, desc, addr, dt, tm, url, source, tags=""):
    return {"title": title, "description": desc, "category": "events", "price_type": "",
            "address": addr, "date": dt, "time": tm, "website": url, "tags": tags, "_src": source}


# ---- fixture: one HOME game (evening, CDT) + one AWAY game, for the Twins --------------------
def twins_schedule():
    return {
        "team": {"id": "9", "displayName": "Minnesota Twins", "abbreviation": "MIN"},
        "events": [
            {   # HOME: 2026-09-23T00:10Z == 2026-09-22 7:10 PM CDT
                "date": "2026-09-23T00:10Z",
                "links": [{"href": "https://www.espn.com/mlb/game/_/gameId/HOME1"}],
                "competitions": [{
                    "venue": {"fullName": "Target Field",
                              "address": {"city": "Minneapolis", "state": "MN"}},
                    "competitors": [
                        {"homeAway": "home", "team": {"id": "9", "displayName": "Minnesota Twins"}},
                        {"homeAway": "away", "team": {"displayName": "Chicago White Sox"}},
                    ],
                }],
            },
            {   # AWAY: our team is the visitor -> must be dropped
                "date": "2026-09-25T18:10Z",
                "competitions": [{
                    "venue": {"fullName": "Comerica Park",
                              "address": {"city": "Detroit", "state": "MI"}},
                    "competitors": [
                        {"homeAway": "home", "team": {"id": "6", "displayName": "Detroit Tigers"}},
                        {"homeAway": "away", "team": {"id": "9", "displayName": "Minnesota Twins"}},
                    ],
                }],
            },
        ],
    }


TWINS = next(t for t in E.TEAMS if t["key"] == "twins")

# ---- _to_local_date_time: UTC -> America/Chicago ------------------------------------------
check("evening CDT rolls back a day (date)", E._to_local_date_time("2026-09-23T00:10Z")[0], "2026-09-22")
check("evening CDT rolls back a day (time)", E._to_local_date_time("2026-09-23T00:10Z")[1], "7:10 PM")
check("day game CDT same date", E._to_local_date_time("2026-09-22T18:10Z"), ("2026-09-22", "1:10 PM"))
check("evening CST (winter) rolls back", E._to_local_date_time("2026-01-15T01:00Z"), ("2026-01-14", "7:00 PM"))
check("+00:00 offset form parses", E._to_local_date_time("2026-09-23T00:10+00:00"), ("2026-09-22", "7:10 PM"))
check("midnight-UTC placeholder blanks time", E._to_local_date_time("2026-09-22T05:00Z"), ("2026-09-22", ""))
check("empty iso -> blanks", E._to_local_date_time(""), ("", ""))
check("garbage iso -> blanks", E._to_local_date_time("not-a-date"), ("", ""))

# ---- timeValid=False: the midnight-EASTERN placeholder (rule 3b, found live 2026-09-21) ----
# Every iso below is a REAL value observed in ESPN's gophers_fb / vikings schedules this run.
# Converting these shifts the date back across midnight and files the game a DAY EARLY, which
# is the most damaging defect this feed can ship.  The pair of checks on each iso is the point:
# the SAME timestamp must resolve differently depending only on ESPN's flag.
check("EDT placeholder 04:00Z keeps the UTC date",
      E._to_local_date_time("2026-10-03T04:00Z", time_valid=False), ("2026-10-03", ""))
check("EDT placeholder CONVERTED would be a day early (the bug)",
      E._to_local_date_time("2026-10-03T04:00Z", time_valid=True), ("2026-10-02", "11:00 PM"))
check("EST placeholder 05:00Z keeps the UTC date",
      E._to_local_date_time("2026-11-07T05:00Z", time_valid=False), ("2026-11-07", ""))
check("EST placeholder CONVERTED would be a day early",
      E._to_local_date_time("2026-11-07T05:00Z", time_valid=True)[0], "2026-11-06")
check("placeholder never fabricates a time",
      E._to_local_date_time("2026-10-24T04:00Z", time_valid=False)[1], "")
check("placeholder + garbage iso still blanks",
      E._to_local_date_time("not-a-date", time_valid=False), ("", ""))
check("placeholder + empty iso still blanks",
      E._to_local_date_time("", time_valid=False), ("", ""))
check("time_valid defaults to True (absent flag converts)",
      E._to_local_date_time("2026-10-03T04:00Z"), ("2026-10-02", "11:00 PM"))
# THE CASE THAT REJECTS A VALUE-SHAPED HEURISTIC.  A rule that guessed "placeholder" from the
# timestamp alone would blank this real Thursday-night kickoff, which sits in the very same
# gophers_fb schedule as the 04:00Z placeholders above and carries timeValid=True.
check("genuine 00:00Z game with timeValid=True still converts",
      E._to_local_date_time("2026-09-04T00:00Z", time_valid=True), ("2026-09-03", "7:00 PM"))

# ---- _our_team_names ----------------------------------------------------------------------
names = E._our_team_names(twins_schedule())
check_true("our_team_names has displayName", "minnesota twins" in names)
check_true("our_team_names has abbreviation", "min" in names)
check_true("our_team_names has id", "9" in names)
check("our_team_names empty on junk", E._our_team_names({}), set())

# ---- parse_home_games: home kept, away dropped --------------------------------------------
games = E.parse_home_games(twins_schedule(), TWINS)
check("exactly one home game parsed", len(games), 1)
check("home opponent resolved", games[0]["opponent"], "Chicago White Sox")
check("home venue resolved", games[0]["venue"], "Target Field")
check("home city resolved", games[0]["city"], "Minneapolis")
check("home date is local CDT date", games[0]["date"], "2026-09-22")
check("home url from links", games[0]["url"], "https://www.espn.com/mlb/game/_/gameId/HOME1")
check("no events -> no games", E.parse_home_games({"events": []}, TWINS), [])

# ---- parse_home_games must READ the flag, not just accept it as an argument ----------------
# _to_local_date_time can be perfectly correct while parse_home_games never passes the flag --
# that is the defect this whole section exists to pin, and it is invisible to the unit checks
# above.  Fixture is the real Michigan-at-Minnesota game (home, 2026-10-03, kickoff TBD).
#
# VERIFIED BY FAIL-ON-PURPOSE 2026-09-21, and the result is the argument for keeping this block:
# a mutant that drops the flag at the CALL SITE (parse_home_games -> _to_local_date_time) leaves
# ALL EIGHT unit checks above green and is caught by these five cases and nothing else.  A
# correct helper plus a caller that never invokes it correctly is a fully intact defect, so a
# unit test on the helper is not evidence the pipeline is fixed.  Two further mutants: removing
# the placeholder branch itself fails 8, and defaulting an absent flag to False -- the
# over-correction -- fails 6, all of them on GENUINE kickoff times rather than placeholders.
GFB = next(t for t in E.TEAMS if t["key"] == "gophers_fb")


def gophers_schedule(time_valid, on_event=False):
    comp = {
        "venue": {"fullName": "Huntington Bank Stadium",
                  "address": {"city": "Minneapolis", "state": "MN"}},
        "competitors": [
            {"homeAway": "home", "team": {"id": "135", "displayName": "Minnesota Golden Gophers"}},
            {"homeAway": "away", "team": {"displayName": "Michigan Wolverines"}},
        ],
    }
    ev = {"date": "2026-10-03T04:00Z", "competitions": [comp]}
    if time_valid is not None:
        (ev if on_event else comp)["timeValid"] = time_valid
    return {"team": {"id": "135", "displayName": "Minnesota Golden Gophers"}, "events": [ev]}


g = E.parse_home_games(gophers_schedule(False), GFB)
check("TBD kickoff files on the REAL game day", g[0]["date"], "2026-10-03")
check("TBD kickoff publishes no time", g[0]["time"], "")
g = E.parse_home_games(gophers_schedule(False, on_event=True), GFB)
check("timeValid also honored on the EVENT block", g[0]["date"], "2026-10-03")
g = E.parse_home_games(gophers_schedule(True), GFB)
check("timeValid=True still converts to Central", g[0]["date"], "2026-10-02")
g = E.parse_home_games(gophers_schedule(None), GFB)
check("absent timeValid defaults to converting", g[0]["date"], "2026-10-02")
# A date-only row must survive the window test like any other -- a blank TIME is not a blank date.
rows = E.to_feed_rows(E.parse_home_games(gophers_schedule(False), GFB),
                      GFB, "2026-09-21", "2026-10-31", stub_row)
check("TBD-kickoff home game still reaches the feed", len(rows), 1)
check("TBD-kickoff feed row carries the real date", rows[0]["date"], "2026-10-03")
check("TBD-kickoff feed row carries no time", rows[0]["time"], "")
check("missing competitions skipped", E.parse_home_games({"events": [{}]}, TWINS), [])

# ---- in_window ----------------------------------------------------------------------------
check_true("in_window inside", E.in_window("2026-09-22", "2026-09-20", "2026-10-31"))
check_true("in_window at start edge", E.in_window("2026-09-20", "2026-09-20", "2026-10-31"))
check_true("in_window at end edge", E.in_window("2026-10-31", "2026-09-20", "2026-10-31"))
check("in_window before start", E.in_window("2026-09-19", "2026-09-20", "2026-10-31"), False)
check("in_window after end", E.in_window("2026-11-01", "2026-09-20", "2026-10-31"), False)
check("in_window blank date", E.in_window("", "2026-09-20", "2026-10-31"), False)

# ---- to_feed_rows: mapping + window filter ------------------------------------------------
rows = E.to_feed_rows(games, TWINS, "2026-09-20", "2026-10-31", stub_row)
check("one in-window row", len(rows), 1)
check("title is 'Team vs. Opponent'", rows[0]["title"], "Minnesota Twins vs. Chicago White Sox")
check("price_type Varies (never Free)", rows[0]["price_type"], "Varies")
check("tags == sports", rows[0]["tags"], "sports")
check("source is espn_<key>", rows[0]["_src"], "espn_twins")
check("address joins venue/city/state", rows[0]["address"], "Target Field, Minneapolis, MN")
check("date carried onto row", rows[0]["date"], "2026-09-22")
# out-of-window home game contributes nothing
check("out-of-window row dropped", len(E.to_feed_rows(games, TWINS, "2026-10-01", "2026-10-31", stub_row)), 0)

# ---- fetch_team soft-fail: a raising http_fn must NOT crash --------------------------------
def boom(_url):
    raise RuntimeError("403 Forbidden")

rws, rep = E.fetch_team(TWINS, "2026-09-20", "2026-10-31", boom, stub_row)
check("soft-fail returns no rows", rws, [])
check("soft-fail reports ERROR", rep["status"], "ERROR")
check("soft-fail note names exception", "RuntimeError" in rep["note"], True)

# fetch_team happy path with an injected http_fn returning our fixture JSON
import json as _json
def fake_http(_url):
    return _json.dumps(twins_schedule())

rws2, rep2 = E.fetch_team(TWINS, "2026-09-20", "2026-10-31", fake_http, stub_row)
check("injected-http fetch yields one row", len(rws2), 1)
check("injected-http status OK", rep2["status"], "OK")

# ---- fetch_all is additive + soft-fail across the whole registry --------------------------
all_rows, all_reports = E.fetch_all("2026-09-20", "2026-10-31", boom, stub_row)
check("fetch_all soft-fails to zero rows", all_rows, [])
check("fetch_all reports every team", len(all_reports), len(E.TEAMS))
check_true("fetch_all never raised (reached here)", True)

# ---- roster: the pro teams the user required, plus the D-I Gophers ------------------------
keys = {t["key"] for t in E.TEAMS}
for must in ("vikings", "timberwolves", "wild", "twins", "lynx", "mnufc"):
    check_true(f"roster includes {must}", must in keys)
check_true("roster includes gophers football", "gophers_fb" in keys)
check_true("roster includes gophers basketball", "gophers_mbb" in keys)
# every team has a well-formed schedule URL
for t in E.TEAMS:
    check_true(f"{t['key']} url well-formed", E.schedule_url(t).startswith("https://site.api.espn.com/"))


# ==========================================================================================
# PRESEASON-STUB SUPPLEMENT  (added 2026-09-30)
# ==========================================================================================
# CLAUDE.md 2026-09-27 opened `espn_season_param_check`: schedule_url() sends no season
# parameter, so a league whose regular season has not opened yet returns a PRESEASON STUB
# that parses cleanly and reads as a complete slate.  The dangerous half is the team that
# reads OK -- a false PASS is worse than a false negative, because a shortfall gets
# investigated and a covered team never does.
#
# Measured live on 2026-09-30 across a real league boundary (see espn_sports.fetch_team):
# a blanket `seasontype=2` is NOT safe -- it zeroes MNUFC (soccer type=13846) and resurrects
# the Twins' finished 162-game season (type=3).  So the supplement is GATED on the response's
# own `season.type == 1` and is strictly ADDITIVE.

def _sched(season_type_val, ids, team_id="9", name="Minnesota Twins"):
    """Minimal schedule JSON: `ids` become HOME games."""
    return {
        "team": {"id": team_id, "displayName": name},
        "season": {"year": 2027, "type": season_type_val},
        "events": [
            {"id": gid, "date": "2026-10-22T00:10Z",
             "links": [{"href": f"https://www.espn.com/nba/game/_/gameId/{gid}"}],
             "competitions": [{
                 "venue": {"fullName": "Target Center",
                           "address": {"city": "Minneapolis", "state": "MN"}},
                 "competitors": [
                     {"homeAway": "home", "team": {"id": team_id, "displayName": name}},
                     {"homeAway": "away", "team": {"displayName": "Chicago Bulls"}},
                 ]}]}
            for gid in ids
        ],
    }

# --- season_type() reads the discriminator the old code never looked at -------------------
check("season_type reads preseason", E.season_type(_sched(1, [])), 1)
check("season_type reads regular",   E.season_type(_sched(2, [])), 2)
check("season_type reads postseason",E.season_type(_sched(3, [])), 3)
check("season_type on missing season", E.season_type({}), None)
check("season_type on None", E.season_type(None), None)
check("season_type ignores non-int (soccer sends 13846 as int -> kept)",
      E.season_type({"season": {"type": 13846}}), 13846)
check("season_type unwraps a nested dict", E.season_type({"season": {"type": {"type": 2}}}), 2)

# --- schedule_url gains an OPTIONAL param; the bare form must be byte-identical ------------
_t = [t for t in E.TEAMS if t["key"] == "timberwolves"][0]
check("schedule_url bare unchanged (no ? at all)",
      E.schedule_url(_t),
      "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/min/schedule")
check("schedule_url with seasontype appends the param",
      E.schedule_url(_t, seasontype=2),
      "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/min/schedule?seasontype=2")
check_true("schedule_url(seasontype=None) adds nothing", "?" not in E.schedule_url(_t, seasontype=None))

# --- THE SUPPLEMENT FIRES on a preseason stub, and is ADDITIVE ----------------------------
_calls = []
def http_preseason(url):
    _calls.append(url)
    if "seasontype=2" in url:
        return _json.dumps(_sched(1, ["REG1", "REG2", "REG3"]))
    return _json.dumps(_sched(1, ["PRE1"]))

rows_s, rep_s = E.fetch_team(_t, "2026-10-01", "2026-11-30", http_preseason, stub_row)
check("preseason stub triggers a SECOND fetch", len(_calls), 2)
check_true("the 2nd fetch carries seasontype=2", "seasontype=2" in _calls[1])
check("supplement is ADDITIVE: 1 preseason + 3 regular = 4 home games", len(rows_s), 4)
check_true("preseason game is KEPT, not replaced",
           any("PRE1" in (r.get("website") or "") for r in rows_s))
check_true("regular-season games are merged in",
           all(any(g in (r.get("website") or "") for r in rows_s) for g in ("REG1", "REG2", "REG3")))
check_true("report names the supplement", "supplemented +3" in rep_s["note"])
check_true("report records season.type", "season.type=1" in rep_s["note"])

# --- dedup by game id: an id present in BOTH slates must not double-count -------------------
def http_overlap(url):
    if "seasontype=2" in url:
        return _json.dumps(_sched(1, ["PRE1", "REG1"]))   # PRE1 appears in both
    return _json.dumps(_sched(1, ["PRE1"]))
rows_o, _ = E.fetch_team(_t, "2026-10-01", "2026-11-30", http_overlap, stub_row)
check("overlapping game id is deduped, not doubled", len(rows_o), 2)

# --- THE GATE: the other 6 teams must be untouched -----------------------------------------
# This is the half that matters most.  A blanket seasontype=2 was MEASURED and rejected.
for _label, _stype in (("regular (wild)", 2), ("postseason (twins)", 3), ("soccer (mnufc)", 13846)):
    _n = []
    def _http(url, _n=_n, _s=_stype):
        _n.append(url)
        if "seasontype=2" in url:
            return _json.dumps(_sched(_s, ["SHOULD_NEVER_BE_FETCHED"] * 1))
        return _json.dumps(_sched(_s, ["G1", "G2"]))
    _rows, _rep = E.fetch_team(_t, "2026-10-01", "2026-11-30", _http, stub_row)
    check(f"{_label}: exactly ONE fetch, no supplement", len(_n), 1)
    check(f"{_label}: rows untouched", len(_rows), 2)
    check_true(f"{_label}: report mentions no supplement", "supplement" not in _rep["note"])

# --- SOFT-FAIL: a failing supplement leaves the bare slate intact (rule 1) -------------------
def http_supp_boom(url):
    if "seasontype=2" in url:
        raise RuntimeError("ESPN 403")
    return _json.dumps(_sched(1, ["PRE1", "PRE2"]))
rows_b, rep_b = E.fetch_team(_t, "2026-10-01", "2026-11-30", http_supp_boom, stub_row)
check("supplement failure keeps the bare slate", len(rows_b), 2)
check_true("supplement failure is REPORTED, not silent", "FAILED" in rep_b["note"])
check_true("supplement failure does not become an ERROR status", rep_b["status"] == "OK")

# ---- summary ------------------------------------------------------------------------------
print(f"\n{_pass} passed, {_fail} failed")
if _fail:
    raise SystemExit(1)
