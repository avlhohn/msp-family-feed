#!/usr/bin/env python3
"""Tests for sports_dedup.py.

Every MERGE case is a real row observed in _compiled_work.json on 2026-09-21.
Every KEEP case is a false positive that a looser rule would have produced --
in particular the away-game watch party, which is the row a city-blind rule
would silently delete.
"""
import sports_dedup as S

P = F = 0


def chk(cond, label):
    global P, F
    if cond:
        P += 1
    else:
        F += 1
        print(f"  FAIL: {label}")


def ev(title, date, addr, src=None, **kw):
    r = {"title": title, "date": date, "address": addr, "category": "events",
         "description": "", "website": "", "time": "", "price_type": ""}
    if src:
        r["_src"] = src
    r.update(kw)
    return r


def collapse(rows):
    g = S.find_groups(rows)
    new, log = S.merge(list(rows), g)
    return new, log


# ---------------------------------------------------------------- tokenizer
chk(S.toks("Minnesota Wild vs. Dallas Stars") == {"minnesota", "wild", "dallas", "stars"},
    "toks drops 'vs.' punctuation")
chk(S.toks("Minnesota Wild vs Dallas Stars") == S.toks("Minnesota Wild vs. Dallas Stars"),
    "'vs' and 'vs.' tokenize identically")
chk(S.toks("Minnesota Wild vs Dallas Stars (Preseason)") > S.toks("Minnesota Wild vs Dallas Stars"),
    "parenthetical qualifier is a strict superset")
chk("game" not in S.toks("Vikings Home Game"), "'game' is a stopword")

# ---------------------------------------------------------------- city_of
chk(S.city_of("199 Kellogg Boulevard West, St. Paul, MN 55102") == "st paul",
    "ZIP and state stripped, St. Paul -> st paul")
chk(S.city_of("Xcel Energy Center, Saint Paul, MN") == "st paul",
    "Saint -> St fold")
chk(S.city_of("Grand Casino Arena, Saint Paul, MN") == S.city_of("199 Kellogg Boulevard West, St. Paul, MN 55102"),
    "renamed venue + street address agree on city")
chk(S.city_of("Target Field, Minneapolis, Minnesota") == "minneapolis",
    "spelled-out state stripped")
chk(S.city_of("Target Field, Minneapolis, MN") == S.city_of("Target Field, Minneapolis, Minnesota"),
    "MN and Minnesota agree")
chk(S.city_of("") == "", "empty address -> empty city")

# ------------------------------------------------- MERGE: real observed rows
wild = [
    ev("Minnesota Wild vs Dallas Stars (Preseason)", "2026-09-25",
       "199 Kellogg Boulevard West, St. Paul, MN 55102", price_type="Paid"),
    ev("Minnesota Wild vs Dallas Stars", "2026-09-25",
       "Xcel Energy Center, Saint Paul, MN", price_type="Paid"),
    ev("Minnesota Wild vs. Dallas Stars", "2026-09-25",
       "Grand Casino Arena, Saint Paul, MN", src="espn_wild", time="7:00 PM"),
]
new, log = collapse(wild)
chk(len(new) == 1, "Wild triple collapses to one row")
chk(len(log) == 1 and len(log[0]["dropped"]) == 2, "Wild merge logs two drops")
chk(new[0].get("time") == "7:00 PM",
    "ESPN's authoritative time is preserved onto the survivor")
chk(new[0].get("price_type") == "Paid",
    "carried row's richer price_type survives over ESPN's conservative Varies")

# ---------------------------------------------- ANCHOR_AUTHORITATIVE: time
# The four cases above pass with a BLANK carried time, so none of them exercises
# the conflict the line-73 assertion names.  On 2026-09-22 all three live groups
# carried a NON-blank time and the blank-only backfill kept it -- espn_wild
# 7:00 PM lost to a carried 8:00 PM, twice, the ET/CT off-by-one signature.
# These are those real rows.
wild_conflict = [
    ev("Minnesota Wild vs Dallas Stars (Preseason)", "2026-09-25",
       "199 Kellogg Boulevard West, St. Paul, MN 55102",
       price_type="Paid", time="8:00 PM", website="https://www.nhl.com/wild/schedule"),
    ev("Minnesota Wild vs. Dallas Stars", "2026-09-25",
       "Grand Casino Arena, Saint Paul, MN", src="espn_wild", time="7:00 PM"),
]
new, log = collapse(wild_conflict)
chk(len(new) == 1, "conflicting-time Wild pair still collapses")
chk(new[0].get("time") == "7:00 PM",
    "ESPN's time OVERWRITES a conflicting carried time (not merely backfills)")
chk(log[0]["anchor_overrides"] == [("time", "8:00 PM", "7:00 PM")],
    "the overwrite is LOGGED, so a wrong override is visible rather than silent")
chk(new[0].get("address") == "199 Kellogg Boulevard West, St. Paul, MN 55102",
    "address is NOT anchor-authoritative -- the real street address survives")
chk(new[0].get("price_type") == "Paid",
    "price_type is NOT anchor-authoritative -- ESPN's 'Varies' must not overwrite")

# 24-hour carried format against ESPN's 12-hour -- same instant, so this is NOT
# a correctness fix but it is the same rule, and it is the live espn_twins row.
twins_fmt = [
    ev("Minnesota Twins vs Texas Rangers Fan Appreciation Day", "2026-09-26",
       "Target Field, Minneapolis, MN", price_type="Paid", time="15:10"),
    ev("Minnesota Twins vs. Texas Rangers", "2026-09-26",
       "Target Field, Minneapolis, Minnesota", src="espn_twins", time="3:10 PM"),
]
new, _ = collapse(twins_fmt)
chk(new[0].get("time") == "3:10 PM",
    "ESPN's 12-hour format replaces a carried 24-hour one")

# The inverse, and it is the guard that keeps this from INVENTING a time: an
# anchor that states nothing must not blank a carried value.  espn_sports.py
# leaves `time` empty when `timeValid` is false, so this is the unannounced
# kickoff case arriving here.
anchor_notime = [
    ev("Minnesota Vikings vs Green Bay Packers Tailgate", "2026-10-11",
       "401 Chicago Ave, Minneapolis, MN 55415", time="12:00 PM"),
    ev("Minnesota Vikings vs. Green Bay Packers", "2026-10-11",
       "U.S. Bank Stadium, Minneapolis, MN", src="espn_vikings"),
]
new, log = collapse(anchor_notime)
chk(len(new) == 1, "unannounced-kickoff anchor still merges")
chk(new[0].get("time") == "12:00 PM",
    "an anchor with NO time does not blank the carried one (timeValid=false case)")
chk(log[0]["anchor_overrides"] == [],
    "no override is logged when the anchor states nothing")

twins = [
    ev("Minnesota Twins vs Texas Rangers Fan Appreciation Day", "2026-09-26",
       "Target Field, Minneapolis, MN", price_type="Paid"),
    ev("Minnesota Twins vs. Texas Rangers", "2026-09-26",
       "Target Field, Minneapolis, Minnesota", src="espn_twins"),
]
new, _ = collapse(twins)
chk(len(new) == 1, "promo-day title collapses into the ESPN game row")
chk("Fan Appreciation" in new[0]["title"], "richer promo title survives")

lynx = [
    ev("Minnesota Lynx vs Indiana Fever (WNBA)", "2026-09-24",
       "600 First Avenue North, Minneapolis, MN 55403", price_type="Paid"),
    ev("Minnesota Lynx vs. Indiana Fever", "2026-09-24",
       "Target Center, Minneapolis, MN", src="espn_lynx"),
]
chk(len(collapse(lynx)[0]) == 1, "street address and venue name agree on city -> merge")

# ------------------------------------------------------------- KEEP cases
# NOTE: the anchor here deliberately carries 5 tokens, so guard 3 does NOT fire
# and guard 4 (city) is the only thing preventing the merge.  An earlier version
# of this case used a 3-token anchor and therefore passed for the WRONG REASON --
# it was green with guard 4 disabled.  Verified by fail-on-purpose.
watch = [
    ev("Week 3 Watch Party: Minnesota Vikings vs Tampa Bay Buccaneers", "2026-09-27",
       "9375 Deerwood Ln N, Maple Grove, MN 55369"),
    ev("Minnesota Vikings vs. Tampa Bay Buccaneers", "2026-09-27",
       "U.S. Bank Stadium, Minneapolis, MN", src="espn_vikings"),
]
chk(len(S.toks(watch[1]["title"])) >= S.MIN_ANCHOR_TOKENS,
    "watch-party anchor clears guard 3, so guard 4 is what is under test")
chk(len(collapse(watch)[0]) == 2,
    "away-game WATCH PARTY in another city is NOT eaten (guard 4)")

diffdate = [
    ev("Minnesota Lynx vs. Indiana Fever", "2026-09-22",
       "Target Center, 600 1st Ave N, Minneapolis, MN", price_type="Paid"),
    ev("Minnesota Lynx vs. Indiana Fever", "2026-09-24",
       "Target Center, Minneapolis, MN", src="espn_lynx"),
]
chk(len(collapse(diffdate)[0]) == 2,
    "same matchup on a DIFFERENT date is never merged (guard 2)")

noanchor = [
    ev("Minnesota Wild vs Dallas Stars (Preseason)", "2026-09-25",
       "Xcel Energy Center, Saint Paul, MN"),
    ev("Minnesota Wild vs Dallas Stars", "2026-09-25",
       "Xcel Energy Center, Saint Paul, MN"),
]
chk(len(collapse(noanchor)[0]) == 2,
    "with NO espn anchor nothing merges -- a bare subset rule is never applied")

zoo = [
    ev("Minnesota Zoo", "2026-10-01", "Apple Valley, MN", src="espn_fake"),
    ev("Minnesota Zoo Wanderlight Trail", "2026-10-01", "Apple Valley, MN"),
]
chk(len(collapse(zoo)[0]) == 2,
    "short anchor (<4 tokens) cannot absorb -- the Minnesota Zoo failure (guard 3)")

unrelated = [
    ev("Minnesota Wild vs. Dallas Stars", "2026-09-25",
       "Grand Casino Arena, Saint Paul, MN", src="espn_wild"),
    ev("Storytime at Rondo Library", "2026-09-25", "461 Dale St N, Saint Paul, MN"),
]
chk(len(collapse(unrelated)[0]) == 2, "unrelated same-city same-date row survives")

twoanchors = [
    ev("Minnesota Twins vs. Texas Rangers", "2026-09-25",
       "Target Field, Minneapolis, Minnesota", src="espn_twins"),
    ev("Minnesota Twins vs. Texas Rangers", "2026-09-26",
       "Target Field, Minneapolis, Minnesota", src="espn_twins"),
]
chk(len(collapse(twoanchors)[0]) == 2, "two ESPN anchors never eat each other")

# ------------------------------------------------------------- idempotence
once, _ = collapse(wild)
twice, log2 = collapse(once)
chk(len(twice) == 1 and len(log2) == 0, "warm re-run collapses 0 (idempotent)")

# --------------------------------------------------- no cross-category reach
chk(all(r.get("category") == "events" for r in collapse(wild)[0]),
    "pass touches only the events category")

# ------------------------------------------------------------- completeness
chk(S.completeness({"a": "x", "b": "", "c": None, "d": False, "e": "y"}) == 2,
    "completeness counts only populated fields")

print(f"{P} passed, {F} failed")
raise SystemExit(1 if F else 0)
