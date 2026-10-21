#!/usr/bin/env python3
"""
end_date_pass.py  —  emit an `end_date` on ranged / multi-day rows in the JSON feed.

WHY: The Base44 Event entity has an `end_date` field and `dailyJsonImport`'s mapRecord
carries `r.end_date` (Fix 4). Our source rows have NO structured end date — only a single
`date`. So end_date must be parsed from the row's own text, and the pipeline's precision-
over-recall rule applies: a WRONG end_date asserts an event is still running when it is not.
We therefore emit ONLY on two high-confidence, self-anchored signals and stay silent otherwise.

SIGNALS (both anchored to the row's own start `date`):
  1. ISO end   — a bare YYYY-MM-DD in title/description that is > start and <= 15 months out.
                 (Descriptions frequently embed "... through 2026-09-13".)
  2. Spelled   — "through|thru|until|ends|runs through <Month> <Day>[, <Year>]" with a real
                 numeric day. Year inferred from start year (rolls forward if month < start).
                 Vague forms with NO day ("through winter", "through end of September",
                 "through preschoolers") match nothing and are intentionally left blank.

SCOPE: dated categories only (events, meal_deals, volunteer_opportunities). parks & restaurants
are evergreen — build_guide.py blanks their `date`, so they get no end_date.

CONTRACT SAFETY: operates on the JSON feed ONLY (what dailyJsonImport reads). It does NOT touch
the CSVs, so the published 21-column CSV contract is unchanged. Run AFTER build_guide.py.

Idempotent. Never overwrites a non-empty end_date already present. `--dry-run` reports only.

Usage:
  python3 end_date_pass.py msp_family_guide.json --dry-run
  python3 end_date_pass.py msp_family_guide.json
"""
import json, re, sys
from datetime import date

DATED_CATS = ['events', 'meal_deals', 'volunteer_opportunities']
WINDOW_MONTHS = 15          # ISO end must be within 15 months of start
SPELL_MAX_DAYS = 460        # spelled end must be within ~15 months of start

MON = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,
       'oct':10,'nov':11,'dec':12,'january':1,'february':2,'march':3,'april':4,'june':6,
       'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}
_MONALT = '|'.join(sorted(MON, key=len, reverse=True))
ISO_RE   = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
SPELL_RE = re.compile(
    r'\b(?:through|thru|until|ends?|runs? through|on view through)\s+('
    + _MONALT + r')\.?\s+(\d{1,2})\b(?:,?\s*(\d{4}))?', re.I)
START_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _text(row):
    return f"{row.get('title','')} {row.get('description','')}"


def compute_end_date(start, text):
    """Return an ISO end_date string strictly after `start`, or None. Pure/testable."""
    if not start or not START_RE.match(start):
        return None
    sy, sm, sd = map(int, start.split('-'))
    try:
        start_d = date(sy, sm, sd)
    except ValueError:
        return None

    # Signal 1: bare ISO date > start, within window. Take the furthest valid one.
    iso_cands = []
    for a, b, c in ISO_RE.findall(text):
        cand = f"{a}-{b}-{c}"
        if cand <= start:
            continue
        try:
            cd = date(int(a), int(b), int(c))
        except ValueError:
            continue
        months = (cd.year - sy) * 12 + (cd.month - sm)
        if 0 <= months <= WINDOW_MONTHS:
            iso_cands.append(cand)
    if iso_cands:
        return max(iso_cands)

    # Signal 2: spelled "through <Month> <Day>[, <Year>]" with a numeric day.
    m = SPELL_RE.search(text)
    if m:
        mon = MON[m.group(1).lower()]
        day = int(m.group(2))
        yr = m.group(3)
        year = int(yr) if yr else (sy if mon >= sm else sy + 1)
        try:
            end_d = date(year, mon, day)
        except ValueError:
            return None
        if end_d > start_d and (end_d - start_d).days <= SPELL_MAX_DAYS:
            return end_d.isoformat()

    return None


def run(path, dry_run=False):
    with open(path) as f:
        feed = json.load(f)

    added = 0
    kept = 0
    samples = []
    for cat in DATED_CATS:
        rows = feed.get(cat)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            existing = row.get('end_date')
            if existing:                       # never overwrite an existing value
                kept += 1
                continue
            end = compute_end_date(row.get('date') or '', _text(row))
            if end:
                if not dry_run:
                    row['end_date'] = end
                added += 1
                if len(samples) < 15:
                    samples.append((row.get('date'), end, (row.get('title') or '')[:50]))

    print(f"end_date_pass: {'DRY-RUN ' if dry_run else ''}added={added} kept_existing={kept}")
    for s, e, t in samples:
        print(f"   {s} -> {e}   {t!r}")

    if not dry_run:
        with open(path, 'w') as f:
            json.dump(feed, f, ensure_ascii=False, indent=2)
        print(f"end_date_pass: wrote {path}")
    return added


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = args[0] if args else 'msp_family_guide.json'
    run(path, dry_run='--dry-run' in sys.argv)
