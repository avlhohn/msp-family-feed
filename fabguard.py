#!/usr/bin/env python3
"""STEP 4.3 (last) -- fabricated-source guard.  REQUIRED, non-negotiable.

Corrects `_fabguard0822.py`, which **blanked the website and kept the row**.
SKILL.md step 2 is explicit that this is wrong:

    "Drop every row that fails -- a fabricated URL means the whole row is
     invented, not just its link. Do not try to 'repair' it by blanking the
     URL; the title/date/venue are equally untrustworthy."

Blanking is strictly worse than either alternative: it launders an invented
event into a normal-looking row with no link, which then survives every later
pass and ships. The 0822 script also carried a one-time "restore websites
blanked by the previous buggy pass" block reading `.run0822/_fabricated_purged.json`;
that repair is spent, and re-running it now would re-inject the very URLs the
guard exists to remove. Both behaviours are dropped here.

Real-ID shapes (deterministic, per SKILL.md):
  LibCal          `*.libcal.com/event/<id>`        -> <id> is ALL DIGITS
  BiblioCommons   `*.bibliocommons.com/events/<id>` -> <id> is [0-9a-f]{24}

No source is exempt. A trust allowlist would defeat the point: the guard is the
contents-level complement to "never trust a subagent's counts", and a real feed
URL passes by construction anyway, so exempting costs nothing and risks
everything.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import json, re, collections

CATS = ['events', 'parks', 'meal_deals', 'volunteer_opportunities', 'restaurants']
RUN = RUNDIR

LIBCAL = re.compile(r'https?://[^/]*libcal\.com/event/([^/?#]+)', re.I)
BIBLIO = re.compile(r'https?://[^/]*bibliocommons\.com/events/([^/?#]+)', re.I)
PLACE = re.compile(r'\bexample\.(com|org)\b|\blorem\b|\bipsum\b|\bplaceholder\b|'
                   r'\byour-?site\b|\bsample\.com\b', re.I)


DNR_BASE = 'https://www.dnr.state.mn.us'
BARE = re.compile(r'^[\w-]+(\.[\w-]+)+(/|$)')


def repair(u):
    """A missing scheme is a formatting defect, not evidence of fabrication.

    The 0822 guard lumped these in with fabricated URLs and blanked 303 of them
    on this run -- 236 root-relative DNR paths (`/state_parks/flandrau`) and 67
    scheme-less domains (`childrensmuseum.org`, `mnzoo.org`). Every one is a real
    destination that the fabrication test already cleared; discarding them costs
    the guide working links to the Minnesota Zoo and the Children's Museum for no
    safety gain. Repair what is unambiguous, and only blank what is not.
    """
    if u.startswith('//'):
        return 'https:' + u, 'added_scheme'
    if u.startswith('/'):
        return DNR_BASE + u, 'resolved_dnr_relative'
    if BARE.match(u):
        return 'https://' + u, 'added_scheme'
    return None, None


def verdict(u):
    """-> (reason, fatal). fatal=True means drop the row; False means blank the URL."""
    m = LIBCAL.search(u)
    if m and not m.group(1).isdigit():
        return 'fabricated_url', True
    m = BIBLIO.search(u)
    if m and not re.fullmatch(r'[0-9a-f]{24}', m.group(1)):
        return 'fabricated_url', True
    if PLACE.search(u):
        return 'placeholder_url', True
    if not re.match(r'^https?://', u):
        # a malformed link is a bad link, not proof the event is invented
        return 'malformed_url', False
    return None, False


def main():
    w = json.load(open('_compiled_work.json'))
    dropped, blanked, repaired = [], [], []
    per_feed = collections.Counter()
    surviving_by_feed = collections.Counter()

    for c in CATS:
        keep = []
        for r in w[c]:
            u = (r.get('website') or '').strip()
            src = r.get('_src', '') or ''
            reason, fatal = verdict(u) if u else (None, False)
            if reason and fatal:
                dropped.append({'category': c, 'title': r.get('title'), 'url': u,
                                'reason': reason, 'src': src, 'date': r.get('date', '')})
                per_feed[src] += 1
                continue
            if reason == 'malformed_url':
                fixed, how = repair(u)
                if fixed:
                    repaired.append({'category': c, 'title': r.get('title'),
                                     'from': u, 'to': fixed, 'how': how, 'src': src})
                    r['website'] = fixed
                else:
                    blanked.append({'category': c, 'title': r.get('title'), 'url': u,
                                    'reason': reason, 'src': src})
                    r['website'] = ''
            if src.startswith('feed:'):
                surviving_by_feed[src] += 1
            keep.append(r)
        w[c] = keep

    w['counts'] = {c: len(w[c]) for c in CATS}
    json.dump(w, open('_compiled_work.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'dropped': dropped, 'blanked': blanked, 'repaired': repaired,
               'fabrication_by_feed': dict(per_feed),
               'surviving_by_feed': dict(surviving_by_feed)},
              open(f'{RUN}/_fabricated_purged.json', 'w'), indent=1)

    print('ROWS DROPPED (fabricated/placeholder):', len(dropped))
    print(collections.Counter(x['reason'] for x in dropped))
    for x in dropped[:20]:
        print(f"   x {x['reason']:16s} | {(x['title'] or '')[:40]:40s} | {x['url'][:62]} | {x['src']}")
    if per_feed:
        print('FABRICATION BY FEED (distrust these feeds\' other output too):', dict(per_feed))
    print('urls REPAIRED (row kept, link now works):', len(repaired),
          dict(collections.Counter(x['how'] for x in repaired)))
    for x in repaired[:6]:
        print(f"   + {(x['title'] or '')[:34]:34s} | {x['from'][:30]:30s} -> {x['to'][:52]}")
    print('urls blanked (unrepairable, row kept):', len(blanked))
    for x in blanked[:10]:
        print(f"   ~ {(x['title'] or '')[:40]:40s} | {x['url'][:62]}")

    # cross-check: booking-system feeds' surviving volume
    print('surviving rows per LibCal/Biblio feed:')
    for k in sorted(surviving_by_feed, key=lambda x: -surviving_by_feed[x]):
        if 'librar' in k or k.endswith('griver') or 'grrl' in k:
            print(f'   {k:32s} {surviving_by_feed[k]:>5}')
    print('counts:', w['counts'], 'TOTAL', sum(w['counts'].values()))
    print('seed rows intact:', sum(1 for c in CATS for r in w[c] if r.get('is_seed')))


if __name__ == '__main__':
    main()
