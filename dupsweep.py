#!/usr/bin/env python3
"""Final exact-duplicate sweep across ALL five categories — 2026-08-28.

Found while re-asserting the seed list: `Minnesota Zoo` had three rows, `Minnesota Children's
Museum` two, `Science Museum of Minnesota` two. Two structural gaps let them through:

1. **The dedup passes are per-category.** `dedup_events_0828.py` only walks `events`;
   `dedup_titles.py` walks each category independently. A seed venue emitted into BOTH
   `events` and `parks` is therefore never compared against itself. 20 such rows exist.

2. **`norm_addr` does not fold `Saint` -> `St`, nor drop the ZIP and state.** So
   "10 West Seventh Street, Saint Paul, MN" and "10 West Seventh Street, St. Paul, MN 55102"
   produce different blocking keys and the two Children's Museum rows never met. Folding
   those three things takes the exact-duplicate count from 67 to 146 — in a state whose
   largest city is spelled both ways in ordinary use, this is not an edge case.

This sweep uses the STRONGEST available duplicate signal and nothing weaker: identical
normalized title AND identical date AND identical normalized street address. That is
SKILL.md's own baseline event rule, so it needs no new justification — and CLAUDE.md's
objection to it (four "Ask a Sewing Mentor" slots at one address on one day are four real,
separately-registerable events) is preserved exactly as `dedup_events_0828.py` preserved it:
where both rows carry a start time and the times DIFFER, they are kept apart. Time is ignored
only when one side has none, which is the re-scrape signature.

Pass B additionally collapses the events<->parks pairs, but ONLY for venues SKILL.md itself
routes explicitly ("Route to `events`" / "Route to `parks`" in the seed bullet), and only when
the two rows agree on location to within 5 km. The declared route wins. Deal rows are NOT
touched: a `meal_deals` row that shares a title with a `restaurants` row may be the venue's
deal rather than a copy of the venue, and merging those two would destroy a category the
Base44 contract publishes separately.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import json, re, sys, math, unicodedata, collections

import glob as _glob, os as _os
def _find_skill():
    """Resolve SKILL.md at runtime. A hardcoded /sessions/<name>/ path from a
    prior run is dead in this session -- that stranding is a known recurring bug."""
    cands = []
    if _os.environ.get("MSP_SKILL"):
        cands.append(_os.environ["MSP_SKILL"])
    cands += sorted(_glob.glob("/sessions/*/mnt/uploads/SKILL.md"))
    cands += sorted(_glob.glob("/sessions/*/mnt/msp-family-guide-daily/SKILL.md"))
    cands += sorted(_glob.glob("/sessions/*/mnt/*/SKILL.md"))
    for p in cands:
        if _os.path.exists(p):
            return p
    raise SystemExit("FATAL: SKILL.md not found in any session uploads dir")
SKILL = _find_skill()
WORK = "_compiled_work.json"
OUT = RUNDIR + "/_dupsweep_report.json"
CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
DRY = "--dry-run" in sys.argv


def nt(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def na(a):
    a = unicodedata.normalize("NFKD", str(a or "")).encode("ascii", "ignore").decode().lower()
    a = re.sub(r"[^a-z0-9 ]", " ", a)
    for x, y in [("street", "st"), ("avenue", "ave"), ("north", "n"), ("south", "s"),
                 ("east", "e"), ("west", "w"), ("road", "rd"), ("drive", "dr"),
                 ("boulevard", "blvd"), ("saint", "st"), ("ste", "st")]:
        a = re.sub(rf"\b{x}\b", y, a)
    a = re.sub(r"\b5[0-9]{4}\b", " ", a)      # MN ZIP
    a = re.sub(r"\bmn\b", " ", a)             # state token
    return re.sub(r"\s+", " ", a).strip()


def ntime(t):
    """Canonicalize a clock time to 24-hour 'HH:MM', so the SAME instant written two ways
    lands in one bucket. Two formats coexist in the feeds because two ingestion paths disagree:
    a 24-hour '17:00' and a 12-hour '5:00 PM' are the same event, and on the 2026-09-01 feed
    350 such twins survived every dedup pass.

    The meridiem math (mod-12, +12 for pm) is applied ONLY when an am/pm marker is present.
    The prior version applied `int(hour) % 12` unconditionally, which silently mangled every
    bare 24-hour string: '17:00' -> '05:00' (5 AM), so it not only failed to match its
    '5:00 PM' twin but actively corrupted unambiguous 24-hour times into the wrong bucket.
    A bare 'HH:MM' with no marker is already 24-hour and is kept verbatim."""
    t = str(t or "").strip().lower().replace(" ", "")
    m = re.match(r"(\d{1,2}):(\d{2})(am|pm)?", t)
    if not m:
        return ""
    h = int(m.group(1))
    mer = m.group(3)
    if mer == "pm":
        if h != 12:
            h += 12
    elif mer == "am":
        if h == 12:
            h = 0
    # else: no marker -> already 24-hour (or a bare hour); leave as-is
    if h > 23:
        h %= 24
    return f"{h:02d}:{m.group(2)}"


def completeness(r):
    score = 0
    for f in ("latitude", "longitude", "website", "image_url", "phone", "address",
              "time", "age_range", "price_type", "deal_description"):
        if str(r.get(f) or "").strip():
            score += 1
    score += min(len(str(r.get("description") or "")) // 200, 4)
    if str(r.get("has_deal")).lower() == "true":
        score += 1
    return score


def merge_into(keep, drop):
    seedsafe = {"title", "address", "category", "tags"} if keep.get("is_seed") else set()
    for k, v in drop.items():
        if k.startswith("_") or k in ("is_seed",) or k in seedsafe:
            continue
        if not str(keep.get(k) or "").strip() and str(v or "").strip():
            keep[k] = v
    kt = [x for x in str(keep.get("tags") or "").split(",") if x]
    for t in str(drop.get("tags") or "").split(","):
        if t and t not in kt:
            kt.append(t)
    keep["tags"] = ",".join(kt)
    if str(drop.get("has_deal")).lower() == "true":
        keep["has_deal"] = True


ROUTE_RE = re.compile(r"route to `(events|parks|restaurants|meal_deals|"
                      r"volunteer_opportunities)`")


def declared_routes():
    """Venues whose SKILL.md seed bullet — or its enclosing section — states a route.

    The section route MUST be reset at every `### ` heading. Letting it persist is a real
    bug, not a hypothetical: the "*Splash pads & water play (route to `parks`)*" sub-line sits
    a few lines above the `### Must-include children's & science museums` and
    `### Must-include marquee attractions` headings, so a sticky variable hands `parks` to the
    Science Museum of Minnesota and Como Park Zoo — both of which their own sections route to
    `events`. That inversion showed up here as a cross-category merge that would have kept the
    WRONG row, i.e. it would have moved two marquee venues into the parks CSV.
    """
    txt = open(SKILL, encoding="utf-8").read().split("\n")
    starts = [i for i, L in enumerate(txt) if L.startswith("### Must-include")]
    ends = [i for i, L in enumerate(txt) if L.startswith("### STEP 2 — MANDATORY")]
    if not starts or not ends:
        return {}
    out, sec = {}, ""
    for L in txt[starts[0]:ends[0]]:
        if L.startswith("### "):
            sec = ""                      # new section: forget the previous section's route
            continue
        m = re.match(r"\s*-\s+\*\*(.+?)\*\*(.*)$", L)
        if not m:
            r = ROUTE_RE.search(L.lower())     # section intro paragraph or `*…*` sub-heading
            if r:
                sec = r.group(1)
            continue
        name, body = m.group(1).strip(), m.group(2).lower()
        r = ROUTE_RE.search(body)             # the bullet's own route always wins
        route = r.group(1) if r else sec
        if route:
            out[nt(name)] = route
    return out


def km(r1, r2):
    try:
        a, b = float(r1.get("latitude")), float(r1.get("longitude"))
        c, e = float(r2.get("latitude")), float(r2.get("longitude"))
    except (TypeError, ValueError):
        return None
    if not (a and b and c and e):
        return None
    return math.hypot((a - c) * 111.0, (b - e) * 79.0)


def collapse(groups, rule, merges, killed):
    for g in groups:
        g = [r for r in g if id(r) not in killed]
        if len(g) < 2:
            continue
        seeds = [r for r in g if r.get("is_seed")]
        keep = max(seeds if seeds else g, key=completeness)
        for r in g:
            if r is keep:
                continue
            merge_into(keep, r)
            killed.add(id(r))
            merges.append({"rule": rule, "kept": str(keep.get("title"))[:80],
                           "kept_cat": keep.get("category", ""),
                           "dropped": str(r.get("title"))[:80],
                           "dropped_cat": r.get("category", ""),
                           "date": str(r.get("date") or "")[:10],
                           "seed": bool(seeds)})


def main():
    d = json.load(open(WORK))
    before = {c: len(d[c]) for c in CATS}
    merges, killed = [], set()

    # ---- Pass A: within-category, exact title + date + address, time as separator ----
    for c in CATS:
        buckets = collections.defaultdict(list)
        for r in d[c]:
            buckets[(nt(r.get("title")), str(r.get("date") or "")[:10],
                     na(r.get("address")))].append(r)
        for key, rows in buckets.items():
            if len(rows) < 2:
                continue
            timed, untimed = collections.defaultdict(list), []
            for r in rows:
                t = ntime(r.get("time"))
                (timed[t] if t else untimed).append(r)
            groups = list(timed.values())
            if untimed:
                if len(groups) == 1:
                    groups[0].extend(untimed)
                elif not groups:
                    groups = [untimed]
                else:
                    groups.append(untimed)
            collapse(groups, "exact_title+date+addr", merges, killed)

    # ---- Pass B: events <-> parks, SKILL.md-declared route wins ----
    routes = declared_routes()
    pair = collections.defaultdict(list)
    for c in ("events", "parks"):
        for r in d[c]:
            if id(r) in killed:
                continue
            pair[(nt(r.get("title")), str(r.get("date") or "")[:10])].append((c, r))
    xcat = []
    for key, cr in pair.items():
        if len({c for c, _ in cr}) < 2:
            continue
        want = routes.get(key[0])
        if not want:
            xcat.append({"title": key[0], "reason": "no declared route in SKILL.md",
                         "cats": sorted({c for c, _ in cr})})
            continue
        dist = km(cr[0][1], cr[1][1])
        if dist is not None and dist > 5:
            xcat.append({"title": key[0], "reason": f"locations {dist:.1f} km apart",
                         "cats": sorted({c for c, _ in cr})})
            continue
        winners = [r for c, r in cr if c == want]
        if not winners:
            xcat.append({"title": key[0], "reason": f"declared {want}, no row there",
                         "cats": sorted({c for c, _ in cr})})
            continue
        keep = max(winners, key=completeness)
        for c, r in cr:
            if r is keep or id(r) in killed:
                continue
            merge_into(keep, r)
            killed.add(id(r))
            merges.append({"rule": "cross_category_declared_route",
                           "kept": str(keep.get("title"))[:80], "kept_cat": want,
                           "dropped": str(r.get("title"))[:80], "dropped_cat": c,
                           "date": str(r.get("date") or "")[:10],
                           "seed": bool(keep.get("is_seed"))})

    for c in CATS:
        d[c] = [r for r in d[c] if id(r) not in killed]
    after = {c: len(d[c]) for c in CATS}

    print(f"{'DRY RUN — ' if DRY else ''}exact-duplicate sweep: "
          f"{sum(before.values())} -> {sum(after.values())} "
          f"({sum(before.values()) - sum(after.values())} collapsed)")
    for c in CATS:
        if before[c] != after[c]:
            print(f"    {c:26} {before[c]:5} -> {after[c]:5}")
    for k, v in collections.Counter(m["rule"] for m in merges).most_common():
        print(f"  rule {k:32} {v}")
    print(f"  seed-involved merges: {sum(1 for m in merges if m['seed'])}")
    if xcat:
        print(f"  cross-category pairs HELD for review (not merged): {len(xcat)}")
        for x in xcat[:12]:
            print(f"    {x['title'][:46]:48s} {x['cats']}  — {x['reason']}")

    json.dump({"merges": merges, "cross_category_held": xcat,
               "before": before, "after": after},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print("  report ->", OUT)
    if not DRY:
        json.dump(d, open(WORK, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
