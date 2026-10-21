#!/usr/bin/env python3
"""Regression tests for mn_city_resolve. Run: python3 test_city_resolve.py

Every case here is a real failure mode observed in production data, not a synthetic
example. Keep them passing.
"""
import mn_city_resolve as M

by, cities = M.load_gazetteer()

# (address, lat, lon, expected_city, note)
CASES = [
    # Municipalities whose names contain Park/Center/Heights — the "not a city"
    # word filter used to reject these and fall through to a coordinate guess.
    ('8001 109th Ave N, Brooklyn Park, MN 55443', 45.10, -93.35, 'Brooklyn Park', 'city named ...Park'),
    ('Park Center High School, Brooklyn Center', 45.06, -93.33, 'Brooklyn Center', 'city named ...Center'),
    ('3700 Monterey Dr, Saint Louis Park, MN', 44.94, -93.36, 'Saint Louis Park', 'city named ...Park'),
    ('590 40th Ave NE, Columbia Heights, MN', 45.04, -93.24, 'Columbia Heights', 'city named ...Heights'),

    # Saint/St./St aliases must collapse to one canonical city.
    ('1265 N Snelling Ave, Saint Paul, MN 55108', 44.98, -93.17, 'Saint Paul', 'Saint spelled out'),
    ('75 5th St W, St. Paul, MN', 44.95, -93.10, 'Saint Paul', 'St. abbreviated'),
    ('St Paul, MN', 44.95, -93.09, 'Saint Paul', 'St no period'),

    # Compass-prefixed Saint cities are distinct municipalities, and the start-anchored
    # Saint fold never fires on them. These resolved to nothing until 2026-08-19.
    ('2400 Margaret St N, North St. Paul, MN 55109', 45.01, -92.99, 'North Saint Paul', 'North St. Paul'),
    ('1616 Humboldt Ave, West St. Paul, MN', 44.92, -93.10, 'West Saint Paul', 'West St. Paul'),
    ('Central Park, North St Paul, MN', 45.01, -92.99, 'North Saint Paul', 'North St no period'),
    # ...but a street suffix must NOT be folded into "saint".
    ('337 Water St, Excelsior, MN', 44.90, -93.57, 'Excelsior', 'street suffix not folded'),

    # No ", MN" present — the old regex resolved these to nothing.
    ('Ojibway Park, 2695 Ojibway Dr, Woodbury', 44.92, -92.93, 'Woodbury', 'no state suffix'),
    ('Central Park, Roseville', 45.01, -93.15, 'Roseville', 'venue + bare city'),
    # No city in the address AND no coordinates -> must stay unresolved rather than
    # inventing a municipality from the venue name.
    ('Deer Lake Orchard, Minnesota', None, None, None, 'venue name, no city, no coords'),

    # Decorated names should still resolve to the municipality.
    ('Downtown Moorhead', 46.87, -96.77, 'Moorhead', 'Downtown prefix'),
    ('Historic Fort Snelling, 200 Tower Ave, St. Paul, MN', 44.89, -93.18, 'Saint Paul', 'Historic prefix'),

    # Non-municipalities must NOT become phantom cities.
    ('Centennial Library', None, None, None, 'library is not a city'),
    ('Hennepin County', None, None, None, 'county is not a city'),
    ('Multiple Twin Cities locations', None, None, None, 'multi-location chain'),
    ('Multiple locations across Minnesota', None, None, None, 'statewide program'),

    # Address wins over a wrong coordinate, and the row is flagged for re-geocoding.
    ('15670 Edgewood Dr, Suite 120, Baxter, MN', 44.98, -93.27, 'Baxter', 'bad coord, good address'),
]


def run():
    passed = failed = 0
    for addr, lat, lon, expected, note in CASES:
        row = {'address': addr, 'latitude': lat if lat is not None else '',
               'longitude': lon if lon is not None else ''}
        got, src = M.resolve_city(row, by, cities)
        ok = (got or None) == expected
        if ok:
            passed += 1
        else:
            failed += 1
            print(f'  FAIL [{note}]\n        {addr!r}\n        expected={expected!r} got={got!r} ({src})')
    # The bad-coordinate case must also raise the right provenance flag.
    row = {'address': '15670 Edgewood Dr, Suite 120, Baxter, MN', 'latitude': 44.98, 'longitude': -93.27}
    _, src = M.resolve_city(row, by, cities)
    if src != 'coord_city_mismatch':
        failed += 1
        print(f'  FAIL [bad coord must flag] expected coord_city_mismatch got {src}')
    else:
        passed += 1
    print(f'\n{passed} passed, {failed} failed')
    return failed


if __name__ == '__main__':
    raise SystemExit(1 if run() else 0)
