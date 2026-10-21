#!/usr/bin/env python3
"""
STEP 4.3 helper - collapse duplicate rows whose TITLES differ but denote the same thing.

WHY THIS EXISTS
---------------
All four existing dedup passes (_dedup*.py) block on an EXACT normalized title. They compare
only rows whose titles already match after normalization, then use venue/date/coords to decide.
That means two rows for the same event with different title phrasing are never even compared,
no matter how identical everything else is. On 2026-08-22 this shipped to the app:

    "Live at the Rog: Alligations - Roseville"   Central Park - Frank Rog Amphitheatre, Roseville
    "Live at the Rog: Alligations"               Central Park Frank Rog Amphitheatre, Roseville

Same venue, same date, same 6:00 PM start - two cards in the feed. 216 such pairs were present.

This module is the missing INVERSE pass: it blocks on place+date and compares titles, rather
than blocking on title and comparing place. Run it AFTER the existing passes.

WHY IT IS DELIBERATELY NARROW
-----------------------------
"One title's tokens are a subset of the other's" is far too loose to use on its own. Real
non-duplicates in this dataset that it would wrongly merge:

    "Minnesota Zoo"                    vs "Minnesota Zoo Wanderlight Trail"   (distinct attraction)
    "Minnesota State Fair - Alphabet Forest" vs "... Alphabet Forest Photo Booth" (distinct shifts)

So only two high-precision patterns are collapsed, and both are mechanical rather than semantic:

  RULE A - city-qualifier suffix. tokens(A) is a subset of tokens(B), and every extra token in
           B is a GEOGRAPHIC token (a word from the city name in either row's address, or a
           state word). "Maple Maze" + "Maple Maze - Maple Grove". Cannot fire on Wanderlight,
           because "wanderlight" and "trail" are not city words.

  RULE B - pure reordering. tokens(A) == tokens(B) but the strings differ, i.e. the same words
           in a different arrangement. "Children's Theatre Company: Pinocchio" +
           "Pinocchio - Children's Theatre Company". Same words, same place, same date.

Anything else is left alone. A missed duplicate is a cosmetic annoyance; a wrongly merged pair
silently deletes a real event from the guide, which is much worse.

Usage:
    python3 dedup_titles.py _compiled_work.json
    python3 dedup_titles.py _compiled_work.json --dry-run    # report only, write nothing
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# Parks are exempt for the same reason they are exempt from pass 3: distinct parks in one city
# frequently share a municipal address, so they over-collapse. Rule A is safe there but the
# gain is one row, and the existing exemption is a decision worth respecting rather than
# quietly reversing.
EXEMPT = {"parks"}

STOP = {"the", "a", "an", "at", "of", "in", "on", "for", "and", "with", "to"}
STATE = {"mn", "minnesota", "twin", "cities", "metro", "area"}

# Fields copied from a dropped row into the survivor when the survivor's is blank.
MERGE_FIELDS = [
    "image_url", "image_source", "website", "latitude", "longitude", "phone", "price",
    "price_type", "time", "start_time", "end_time", "deal_description", "deal_expiry",
    "deal_source", "date", "address", "description", "age_range",
]


def norm(s):
    """Casefold and strip punctuation. '&' becomes 'and' BEFORE punctuation is stripped.

    That ordering matters: the older passes strip '&' to whitespace while leaving a literal
    'and' intact, so 'Loaves & Fishes' and 'Loaves and Fishes' normalize differently and are
    never compared. Both are in the current dataset.
    """
    s = unicodedata.normalize("NFKD", (s or "")).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def toks(s):
    return {t for t in norm(s).split() if t not in STOP}


def city_of(row):
    """Extract the city from an address.

    The leading `(?:^|,)` is load-bearing. The obvious regex requires a comma BEFORE the city,
    which silently fails on the very common city-only address "Maple Grove, MN" - there is no
    comma ahead of the city, so no city is found, so the row gets an empty blocking key and is
    skipped entirely. `_dedup3_0822.py` still has that form and has therefore been ignoring
    every city-only row in the dataset. `_dedup4_0822.py` has the correct form.
    """
    m = re.search(r"(?:^|,)\s*([A-Za-z .']+?),?\s*(?:MN|Minnesota)\b", row.get("address") or "", re.I)
    return norm(m.group(1)).replace("saint", "st") if m else ""


def street(row):
    """Street-address key, or '' when the address is city-only."""
    a = (row.get("address") or "").strip()
    first = norm(re.split(r",", a)[0])
    return first if re.match(r"^\d", first) else ""


def timekey(row):
    for f in ("start_time", "time"):
        v = str(row.get(f) or "").strip()
        if v:
            return norm(v)
    return ""


def filled(row):
    return sum(1 for k, v in row.items() if not k.startswith("_") and str(v).strip())


def geo_tokens(a, b):
    """Words that may legitimately appear as a city qualifier on these two rows.

    DELIBERATELY the CITY NAME ONLY, never the whole address. Harvesting every address token
    was tried first and it silently merged distinct locations of a chain, because a
    neighborhood name sitting in the address became a droppable "geographic" word:

        "Red Cow - St. Paul"          <= "Red Cow St. Paul Cathedral Hill"
        "Colossal Cafe Grand Avenue"  <= "Colossal Cafe"

    Cathedral Hill and Grand Avenue are exactly the tokens that DISTINGUISH two locations of
    one restaurant, so treating them as noise deletes a real venue. For a multi-location
    brand the qualifier is the whole point of the row.
    """
    g = set(STATE)
    for r in (a, b):
        g |= set(city_of(r).split())
    return g


def classify(a, b):
    """Return 'city_suffix', 'reordered', or None."""
    ta, tb = toks(a.get("title")), toks(b.get("title"))
    if not ta or not tb:
        return None
    if norm(a.get("title")) == norm(b.get("title")):
        return None  # the existing passes already handle exact-title pairs

    if ta == tb:
        return "reordered"

    small, big = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    if small < big and (big - small) <= geo_tokens(a, b):
        return "city_suffix"
    return None


def compatible_place(a, b):
    """Block a merge when the rows demonstrably sit at different street addresses."""
    sa, sb = street(a), street(b)
    return not (sa and sb and sa != sb)


REVIEW_THRESHOLD = 0.8


def suspects(data):
    """Near-duplicate pairs that are NOT collapsed - reported for human review instead.

    There is a real band of pairs that look like duplicates but cannot be decided mechanically,
    because a single extra word may or may not change the meaning:

        "Minnesota Wild vs Dallas Stars"           + "... (Preseason)"       -> same game
        "Duluth Children's Museum Harvest Festival" + "... MINI Harvest ..." -> possibly not

    'Mini', 'Junior', 'Teen' and 'Preseason' all occupy the same syntactic slot and only one of
    them is safely ignorable. Since a wrong merge silently deletes a real event from the guide
    while a missed one is merely an ugly card, these are surfaced rather than resolved. Confirm
    against the source, then either fix the title upstream or add a case to
    test_dedup_titles.py.
    """
    from itertools import combinations
    out = []
    for cat in CATS:
        if cat in EXEMPT or cat not in data:
            continue
        blocks = defaultdict(list)
        for r in data[cat]:
            dt = (r.get("date") or "").strip()
            if dt:
                blocks[(city_of(r), dt)].append(r)
        for (city, dt), rs in blocks.items():
            if not city or len(rs) < 2:
                continue
            for a, b in combinations(rs, 2):
                ka, kb = timekey(a), timekey(b)
                if ka and kb and ka != kb:
                    continue
                if not compatible_place(a, b):
                    continue
                ta, tb = toks(a.get("title")), toks(b.get("title"))
                if not ta or not tb or norm(a.get("title")) == norm(b.get("title")):
                    continue
                if classify(a, b):
                    continue  # already handled by rule A or B
                j = len(ta & tb) / len(ta | tb)
                if j >= REVIEW_THRESHOLD:
                    out.append({"category": cat, "city": city, "date": dt,
                                "similarity": round(j, 2),
                                "a": a.get("title"), "b": b.get("title")})
    return sorted(out, key=lambda x: -x["similarity"])


def collapse(data, dry_run=False):
    log = []
    for cat in CATS:
        if cat in EXEMPT or cat not in data:
            continue
        rows = data[cat]

        # Block on place + date (+ time when both have one). This is the INVERSE of the
        # existing passes: they block on title and compare place, which is exactly why a
        # title variation defeats them.
        blocks = defaultdict(list)
        for r in rows:
            blocks[(city_of(r), (r.get("date") or "").strip())].append(r)

        dropped = set()
        for (city, _date), rs in blocks.items():
            if not city or len(rs) < 2:
                continue
            for i, a in enumerate(rs):
                if id(a) in dropped:
                    continue
                for b in rs[i + 1:]:
                    if id(b) in dropped:
                        continue
                    ka, kb = timekey(a), timekey(b)
                    if ka and kb and ka != kb:
                        continue  # same venue+day but different showtimes: distinct
                    if not compatible_place(a, b):
                        continue
                    kind = classify(a, b)
                    if not kind:
                        continue
                    win, lose = sorted(
                        (a, b),
                        key=lambda r: (0 if r.get("is_seed") else 1,
                                       0 if street(r) else 1,
                                       -filled(r)),
                    )
                    for f in MERGE_FIELDS:
                        if not str(win.get(f) or "").strip() and str(lose.get(f) or "").strip():
                            win[f] = lose[f]
                    if lose.get("has_deal") and not win.get("has_deal"):
                        win["has_deal"] = True
                        if not str(win.get("deal_description") or "").strip():
                            win["deal_description"] = lose.get("deal_description", "")

                    def aslist(v):
                        return v if isinstance(v, list) else [
                            x.strip() for x in str(v or "").split(",") if x.strip()]

                    win["tags"] = list(dict.fromkeys(aslist(win.get("tags")) + aslist(lose.get("tags"))))

                    # Log the ORIGINAL titles, before the rename below. Logging the post-rename
                    # title makes both sides of the pair print identically, which hides what
                    # was actually merged and makes the report useless for spotting a bad call.
                    kept_title, lost_title = win.get("title"), lose.get("title")

                    # Keep the richer ROW but the more specific TITLE. The survivor is chosen
                    # for data completeness, which is unrelated to how informative its title
                    # is - without this, "Maple Maze - Maple Grove" loses to a barer
                    # "Maple Maze" that merely had more fields populated, and the qualifier a
                    # reader uses to tell locations apart disappears from the card.
                    if len(toks(lost_title)) > len(toks(kept_title)):
                        win["title"] = lost_title

                    dropped.add(id(lose))
                    log.append({"category": cat, "rule": kind, "city": city,
                                "kept": kept_title, "dropped": lost_title,
                                "final_title": win.get("title"),
                                "date": lose.get("date", "")})

        if not dry_run:
            data[cat] = [r for r in rows if id(r) not in dropped]

    if not dry_run:
        data["counts"] = {c: len(data[c]) for c in CATS if c in data}
    return log


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "_compiled_work.json"
    dry = "--dry-run" in sys.argv

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    before = {c: len(data.get(c, [])) for c in CATS}
    log = collapse(data, dry_run=dry)
    review = suspects(data)

    if not dry:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    with open("_dedup_titles_report.json", "w", encoding="utf-8") as fh:
        json.dump({"collapsed": log, "review": review}, fh, ensure_ascii=False, indent=1)

    print(f"title-variant dedup{' (DRY RUN)' if dry else ''}: {len(log)} collapsed")
    for cat in CATS:
        n = sum(1 for x in log if x["category"] == cat)
        if n:
            after = before[cat] - n
            print(f"  {cat:26s} {before[cat]:5d} -> {after:5d}  (-{n})")
    for rule in ("city_suffix", "reordered"):
        print(f"  rule {rule:12s} {sum(1 for x in log if x['rule'] == rule)}")

    print(f"  {len(review)} near-duplicate pairs flagged for REVIEW (not merged):")
    for x in review[:10]:
        print(f"    {x['similarity']}  {x['a'][:44]:44s} + {x['b'][:44]}")


if __name__ == "__main__":
    main()
