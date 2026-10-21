#!/usr/bin/env python3
"""
mn_city_resolve.py — canonical Minnesota city resolution for the MSP Family Guide.

Replaces the old regex that required a literal ", MN" in the address string. That
regex silently produced three defects:
  * "St. Paul" / "Saint Paul" / "St Paul" counted as three separate cities
  * addresses ending in ", Minnesota" or in a bare city name resolved to nothing
  * "Downtown Moorhead", "Centennial Library", "Hennepin County" became phantom cities

Strategy: the address string is the primary signal but is only trusted when it names
a REAL municipality present in the OSM gazetteer. Coordinates are the fallback and
the tie-breaker. Every result carries provenance so a circular result (city derived
from coordinates that were themselves a city centroid) is never mistaken for a
confirmed one.

Exposes: resolve_city(row) -> (canonical_name|'', city_source)
         load_gazetteer()
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
GAZ_PATH = os.path.join(HERE, 'mn_city_gazetteer.json')

# Strip decorations that are not part of a municipality name.
_PREFIX = re.compile(r'^(downtown|historic|old town|uptown|greater|the)\s+', re.I)
_SUFFIX = re.compile(r'\s+(area|region|metro|vicinity)$', re.I)
# A point further than this from its stated city's centroid means the geocode landed
# in the wrong place. 25 km clears even Minneapolis-sized footprints plus centroid
# offset, so anything beyond it is a real error worth queueing for the fixer.
BAD_COORD_KM = 25.0

# Fragments that indicate a venue/administrative string rather than a city.
_NOTACITY = re.compile(
    r'\b(librar|county|room|school|church|hall|museum|arena|center|centre|'
    r'fairground|park|orchard|campus|building|stadium|theat|mall|store)\b', re.I)


def _norm(s):
    """Fold Saint/St./St variants and punctuation so aliases collapse to one key."""
    s = (s or '').strip().lower()
    s = _PREFIX.sub('', s)
    s = _SUFFIX.sub('', s)
    s = re.sub(r'^(saint|st\.?)\s+', 'saint ', s)
    # Also fold the abbreviation after a leading compass word: North/West/South St. Paul
    # are real municipalities and the start-anchored rule above never fires on them.
    # Deliberately NOT a global \bst\b fold, which would turn the street suffix in
    # "Water St" into "water saint".
    s = re.sub(r'^(north|south|east|west)\s+(?:saint|st\.?)\s+', r'\1 saint ', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def load_gazetteer(path=GAZ_PATH):
    """Return (by_norm_name, list_of_cities). Built from OSM place=city/town/village."""
    cities = json.load(open(path))
    by_name = {}
    for c in cities:
        key = _norm(c['name'])
        # Prefer the more populous entry when two municipalities normalise alike.
        if key not in by_name or (c.get('population') or 0) > (by_name[key].get('population') or 0):
            by_name[key] = c
    return by_name, cities


def _radius_km(pop):
    """Plausible city radius from population, assuming ~2,800 people/km^2.

    Minneapolis (430k) -> ~7 km, which matches its real footprint. A 3 km floor keeps
    small towns from rejecting an event at the edge of town; the 15 km cap stops a
    large city from swallowing its neighbours.
    """
    if not pop:
        return 4.0
    area = pop / 2800.0
    return max(3.0, min(15.0, 1.6 * math.sqrt(area / math.pi)))


def _haversine(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _address_candidates(address, by_name=None):
    """Comma-segments of the address that could plausibly be a city name.

    The gazetteer is the authority. _NOTACITY is only a fallback filter for segments
    the gazetteer does NOT know — otherwise it wrongly rejects real municipalities
    whose names contain Park/Center/Heights (Brooklyn Park, Brooklyn Center, Saint
    Louis Park, Columbia Heights). Caught 2026-08-19 when "8001 109th Ave N, Brooklyn
    Park, MN" fell through to a coordinate lookup and resolved to Osseo.
    """
    a = (address or '').strip().rstrip('.')
    a = re.sub(r'\s*\d{5}(-\d{4})?\s*$', '', a)
    a = re.sub(r',?\s*(MN|Minnesota|USA|United States)\s*$', '', a, flags=re.I)
    out = []
    for part in reversed([p.strip() for p in a.split(',') if p.strip()]):
        part = _PREFIX.sub('', part).strip()
        if not part or not (2 < len(part) < 30):
            continue
        known = by_name is not None and _norm(part) in by_name
        if not known and (_NOTACITY.search(part) or re.search(r'\d', part)):
            continue
        out.append(part)
    return out


def resolve_city(row, by_name=None, cities=None, max_km=30.0):
    """Resolve one row to a canonical MN municipality.

    Returns (city_name, city_source) where city_source is one of:
      address_gazetteer  - address named a real MN city; authoritative
      coords_nearest     - no usable city in the address; nearest centroid to the point
      coord_city_mismatch - address city is trusted, but the stored lat/lon sits >25 km
                           away, so the COORDINATE is wrong and should be re-geocoded
      centroid_circular  - coords were themselves a city centroid, so the city is an
                           input, not a finding. Never count these as confirmed.
      unresolved         - neither signal produced a municipality
    """
    if by_name is None:
        by_name, cities = load_gazetteer()

    addr_hit = None
    for cand in _address_candidates(row.get('address'), by_name):
        hit = by_name.get(_norm(cand))
        if hit:
            addr_hit = hit
            break

    try:
        lat = float(str(row.get('latitude', '')).strip())
        lon = float(str(row.get('longitude', '')).strip())
    except (TypeError, ValueError):
        lat = lon = None

    coord_hit, coord_km = None, None
    if lat is not None:
        best = None
        for c in cities:
            km = _haversine(lat, lon, c['lat'], c['lon'])
            if km > max_km:
                continue
            # Score by how far inside the city's plausible footprint the point sits.
            score = km / _radius_km(c.get('population'))
            if best is None or score < best[0]:
                best = (score, km, c)
        if best:
            coord_hit, coord_km = best[2], best[1]

    circular = row.get('_geo') == 'city_centroid'

    # Precedence: a street address that names a REAL municipality beats a geocoded
    # point. Validated 2026-08-19 against 207 disagreements — in every sampled case
    # the address was correct and the coordinate was wrong (e.g. "Littles and Lattes,
    # 15670 Edgewood Dr, Baxter, MN" geocoded into Minneapolis, 171 km away). So a
    # large address/coord gap is a BAD COORDINATE signal, not a bad city.
    if addr_hit:
        if coord_hit and lat is not None:
            km = _haversine(lat, lon, addr_hit['lat'], addr_hit['lon'])
            if km > BAD_COORD_KM:
                return addr_hit['name'], 'coord_city_mismatch'
        return addr_hit['name'], ('centroid_circular' if circular else 'address_gazetteer')
    if coord_hit:
        return coord_hit['name'], ('centroid_circular' if circular else 'coords_nearest')
    return '', 'unresolved'


if __name__ == '__main__':
    import sys
    from collections import Counter
    by_name, cities = load_gazetteer()
    d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '_compiled_work.json'))
    for cat in ['events', 'parks', 'meal_deals', 'volunteer_opportunities', 'restaurants']:
        src = Counter()
        for r in d.get(cat, []):
            _, s = resolve_city(r, by_name, cities)
            src[s] += 1
        print(f'{cat:24s}', dict(src))
