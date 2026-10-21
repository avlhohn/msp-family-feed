#!/usr/bin/env python3
"""
mn_coverage.py — population-tiered event-coverage check for the MSP Family Guide.

Replaces the flat "fewer than 3 events" warning, which had two flaws:
  1. It held Hanska (pop 400) to the same standard as Bloomington (pop 83,000),
     so ~70 tiny towns permanently occupied the warning list as noise.
  2. It could only flag cities that ALREADY APPEARED in the data. A city with zero
     events contributed no rows, so it was invisible — the most important gap of all
     was the one the check structurally could not see.

This version walks the gazetteer rather than the dataset, so absent cities surface,
and applies a per-tier minimum.

Usage:  python3 mn_coverage.py [compiled_work.json]
Import: tiered_coverage(events) -> (report_rows, warnings)
"""
import json, sys
from collections import Counter

import mn_city_resolve as M

# (label, min_population, max_population, expected minimum events in a ~6-week window)
TIERS = [
    ('core metro',      50000, 10**9, 8),
    ('major suburb',    15000, 49999, 4),
    ('small city',       5000, 14999, 2),
    ('town',                0,  4999, 0),   # reported, never warned on
]


def tier_of(pop):
    p = pop or 0
    for label, lo, hi, target in TIERS:
        if lo <= p <= hi:
            return label, target
    return 'town', 0


def tiered_coverage(events, by_name=None, cities=None):
    """Return (rows, warnings).

    rows: one dict per tier-1/2/3 municipality with its count, target and status.
    warnings: the subset that missed its target — these are the real gaps.
    """
    if by_name is None:
        by_name, cities = M.load_gazetteer()

    counts = Counter()
    for r in events:
        city, src = M.resolve_city(r, by_name, cities)
        # centroid_circular is excluded: the city was an INPUT to the coordinate, so
        # counting it as evidence of coverage would be circular.
        if city and src in ('address_gazetteer', 'coords_nearest', 'coord_city_mismatch'):
            counts[M._norm(city)] += 1

    rows, warnings = [], []
    for c in cities:
        pop = c.get('population') or 0
        label, target = tier_of(pop)
        if target == 0:
            continue                      # towns are never warned on
        n = counts.get(M._norm(c['name']), 0)
        row = {'city': c['name'], 'population': pop, 'tier': label,
               'events': n, 'target': target, 'shortfall': max(0, target - n)}
        rows.append(row)
        if n < target:
            warnings.append(row)

    rows.sort(key=lambda r: -r['population'])
    warnings.sort(key=lambda r: (-r['population']))
    return rows, warnings


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '_compiled_work.json'
    d = json.load(open(path))
    rows, warns = tiered_coverage(d['events'])

    by_tier = {}
    for r in rows:
        by_tier.setdefault(r['tier'], []).append(r)

    print('=== TIERED EVENT COVERAGE ===')
    for label, _, _, target in TIERS:
        rs = by_tier.get(label)
        if not rs:
            continue
        met = sum(1 for r in rs if r['events'] >= target)
        zero = sum(1 for r in rs if r['events'] == 0)
        print(f'  {label:14s} n={len(rs):>3}  target>={target}  meeting={met:>3} '
              f'({100*met/len(rs):.0f}%)  ZERO events={zero}')

    print(f'\n=== {len(warns)} CITIES BELOW TARGET ===')
    for r in warns[:30]:
        flag = 'NO COVERAGE' if r['events'] == 0 else f"{r['events']}/{r['target']}"
        print(f"  {r['city']:<22} pop={r['population']:>7,}  {r['tier']:<13} {flag}")
    if len(warns) > 30:
        print(f'  ... and {len(warns)-30} more')
