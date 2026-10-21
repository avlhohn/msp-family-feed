#!/usr/bin/env python3
"""STEP 4.9 — geocode blank lat/lon, MN-bbox validated. 2026-08-25.

Rules this encodes (all previously learned the hard way):
  * MN bbox: lat 43.3-49.5, lon -97.5..-89.4. A hit outside it is DISCARDED,
    not stored -- an out-of-bbox result is a wrong match, not a MN address.
  * A NEGATIVE cache entry is never retried against Nominatim. It already
    failed; retrying burns the 1 req/sec budget to fail again. Negative rows
    fall straight through to the city-centroid fallback.
  * City centroid comes from the gazetteer via mn_city_resolve, and is recorded
    with provenance `city_centroid` so STEP 8 can tell a real geocode from a
    fallback. `centroid_circular` must never later count as coverage evidence.
  * Nominatim politeness: >=1.05 s between calls, descriptive UA. Read-only
    structured API, which policy allows via urllib.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import json, os, re, sys, time, urllib.parse, urllib.request

WORKDIR = _os.environ.get(
    "MSP_WORKDIR",
    _os.path.dirname(_os.path.abspath(__file__)),
)
# 2026-08-29: the original derived HERE from __file__ and CACHE from its PARENT,
# which only resolves correctly when the script sits in a .runNNNN/ subfolder.
# Run from the folder root it looked for _geocache.json one level too high, found
# nothing, and would have re-queried Nominatim for all 2261 known addresses.
# 2026-08-30: hardcoding a session path re-stranded it (dead session). Resolve
# from MSP_WORKDIR or the script's own folder, where _geocache.json now lives.
HERE = WORKDIR
PARENT = WORKDIR
sys.path.insert(0, PARENT)
import mn_city_resolve as M

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
LAT_MIN, LAT_MAX = 43.3, 49.5
LON_MIN, LON_MAX = -97.5, -89.4
CACHE = os.path.join(PARENT, "_geocache.json")
UA = "msp-family-feed/1.0 (daily guide build; contact avlhohn@gmail.com)"
DEADLINE = float(os.environ.get("GEO_DEADLINE", "1500"))


def in_mn(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def blank(r):
    la, lo = str(r.get("latitude") or "").strip(), str(r.get("longitude") or "").strip()
    if not la or not lo:
        return True
    return not in_mn(la, lo)


def norm_addr(a):
    a = re.sub(r"\s+", " ", (a or "").strip())
    return a.rstrip(" ,")


def nominatim(q):
    url = ("https://nominatim.openstreetmap.org/search?" +
           urllib.parse.urlencode({
               "q": q, "format": "json", "limit": 1, "countrycodes": "us",
               "viewbox": "%s,%s,%s,%s" % (LON_MIN, LAT_MAX, LON_MAX, LAT_MIN),
               "bounded": 1}))
    rq = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(rq, timeout=20) as resp:
        js = json.loads(resp.read().decode())
    if not js:
        return None
    lat, lon = float(js[0]["lat"]), float(js[0]["lon"])
    return [lat, lon] if in_mn(lat, lon) else None


def main():
    t0 = time.time()
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    n_cache_in = len(cache)
    by_name, cities = M.load_gazetteer()
    cent = {c["name"].casefold(): (c["lat"], c["lon"])
            for c in cities if c.get("lat") and c.get("lon")}

    data = json.load(open(os.path.join(HERE, "_compiled_work.json")))
    todo = []
    for c in CATS:
        for i, r in enumerate(data[c]):
            if blank(r):
                todo.append((c, i, r))

    stats = dict(queue=len(todo), cache_hit=0, cache_negative=0, api_ok=0,
                 api_none=0, api_err=0, centroid=0, unresolved=0,
                 out_of_bbox_discarded=0, deadline_hit=False)
    last = 0.0

    for c, i, r in todo:
        key = norm_addr(r.get("address"))
        got = None
        prov = None

        if key and key in cache:
            v = cache[key]
            if v and in_mn(v[0], v[1]):
                got, prov = v, "cache"
                stats["cache_hit"] += 1
            else:
                stats["cache_negative"] += 1        # never retried
        elif key and len(key) > 6:
            if time.time() - t0 > DEADLINE:
                stats["deadline_hit"] = True
            else:
                wait = 1.05 - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.time()
                try:
                    hit = nominatim(key)
                    cache[key] = hit
                    if hit:
                        got, prov = hit, "nominatim"
                        stats["api_ok"] += 1
                    else:
                        stats["api_none"] += 1
                except Exception:
                    stats["api_err"] += 1

        if got is None:
            city, csrc = M.resolve_city(r, by_name, cities)
            ll = cent.get((city or "").casefold())
            if ll and in_mn(ll[0], ll[1]):
                got, prov = list(ll), "city_centroid"
                stats["centroid"] += 1
            else:
                stats["unresolved"] += 1
                continue

        r["latitude"] = round(float(got[0]), 6)
        r["longitude"] = round(float(got[1]), 6)
        r["geo_provenance"] = prov

    json.dump(cache, open(CACHE, "w"))
    json.dump(data, open(os.path.join(HERE, "_compiled_work.json"), "w"))

    remaining = sum(1 for c in CATS for r in data[c] if blank(r))
    stats["remaining_blank_or_out_of_bbox"] = remaining
    stats["cache_size_before"] = n_cache_in
    stats["cache_size_after"] = len(cache)
    stats["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(stats, open(os.path.join(HERE, "_geo_report.json"), "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
