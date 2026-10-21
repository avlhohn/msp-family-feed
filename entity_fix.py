#!/usr/bin/env python3
"""
entity_fix.py  --  STEP 4.3 pre-pass: decode HTML entities left in user-visible text.

WHY THIS EXISTS (found 2026-09-10)
----------------------------------
`dedup_titles.py`'s REVIEW list surfaced two pairs that were the SAME row written twice:

    St. Paul Farmer&#39;s Market            +  St. Paul Farmer's Market
    League of Women Voters Roseville Area&#160;  +  League of Women Voters Roseville Area

Several feeds (RSS in particular) emit HTML-escaped text into fields we publish verbatim, so
a family reading the app sees the literal characters `&#39;` in a venue name. Two consequences,
and the second is the one that matters:

1. Cosmetic: the escape is displayed as-is. Bad, but visible and therefore self-reporting.
2. Structural: EVERY dedup pass in this project normalizes and compares TEXT. `&#39;` and `'`
   normalize differently, so an escaped row can never collide with its unescaped twin -- the
   same class of blindness as `Saint`/`St` (dupsweep) and `Suite`/`Ste` (na()). The escaping
   is not just ugly; it is a duplicate the whole chain is structurally incapable of seeing.

So this runs BEFORE the dedup chain, not after: decoding afterwards leaves the duplicate pair
in the dataset for another run.

SCOPE -- deliberately narrow
----------------------------
* Only `title`, `description`, `address`, `venue_name`, `location` -- human-readable fields.
  URLs are NOT touched: a `&amp;` inside a query string is a legitimately escaped separator in
  some feeds and unescaping it can break the link.
* `html.unescape` is applied ONCE. Applying it repeatedly is how `&amp;#39;` (a correctly
  double-escaped literal ampersand) would decay into an apostrophe -- a silent corruption.
  Idempotence here means "a warm re-run changes 0 rows", which holds because a decoded string
  contains no entity for the second pass to find.
* NBSP (U+00A0) and friends collapse to a plain space and the field is stripped. `&#160;` is
  the actual observed case and it is invisible on screen, so without this the trailing-NBSP
  twin STILL fails to collide after decoding -- which would make this pass look like it worked
  while leaving the duplicate in place.
"""
import html
import json
import re
import sys

FIELDS = ("title", "description", "address", "venue_name", "location")
CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# An entity is only "present" if it is a real named/numeric reference. A bare `&` (as in
# "Milk & Cookies") must not count as a hit, or the report over-states what changed.
RX_ENTITY = re.compile(r"&(?:#\d{1,7}|#[xX][0-9a-fA-F]{1,6}|[a-zA-Z][a-zA-Z0-9]{1,31});")
# Unicode spaces that are invisible on screen but are NOT U+0020, so they defeat text equality.
RX_ODDSPACE = re.compile("[\u00a0\u2007\u202f\u2009\u200a\u2002\u2003\ufeff]")


def clean(value):
    """Return (new_value, changed). Pure -- no I/O, so the tests can drive it directly."""
    if not isinstance(value, str):
        return value, False
    out = value
    if RX_ENTITY.search(out):
        decoded = html.unescape(out)
        # DOUBLE-ESCAPE GUARD. If one decode still leaves a live entity behind, the source
        # escaped an entity ON PURPOSE (`&amp;#39;` means "show the characters &#39;") and we
        # cannot tell that apart from a feed that double-escaped by accident. Decoding it is a
        # coin flip, and the pipeline carries rows forward, so this pass meets the same row
        # again tomorrow: a non-idempotent decode would eat one level per day until the text
        # was silently destroyed. Leave it alone and let it be read by hand -- the standing
        # asymmetry (a cosmetic miss beats a silent corruption) applied to text instead of
        # to merges. This branch is exercised by test_entity_fix.py and was written only
        # after the idempotence check caught the loop version failing on exactly this input.
        if RX_ENTITY.search(decoded):
            return value, False
        out = decoded
    out = RX_ODDSPACE.sub(" ", out)
    # Collapse runs of whitespace introduced by the substitution, then strip.
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out, out != value


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "_compiled_work.json"
    dry = "--dry-run" in sys.argv
    d = json.load(open(path))

    changed_rows = 0
    changed_fields = 0
    # Report BY KIND, not as one total. The raw total is ~330 while the entity decodes this
    # pass is named for are ~9; a bare "330 rows changed" reads like a mass rewrite and
    # invites either alarm or a shrug, and CLAUDE.md's standing rule is that a large number
    # must be re-measured before it is acted on. Breaking it out IS that re-measurement, done
    # once inside the pass so the next reader does not have to reconstruct it by hand.
    kinds = {}
    samples = {}
    for cat in CATS:
        for row in d.get(cat, []):
            if not isinstance(row, dict):
                continue
            row_hit = False
            for f in FIELDS:
                old = row.get(f)
                new, ch = clean(old)
                if not ch:
                    continue
                if RX_ENTITY.search(old):
                    kind = "entity decoded"
                elif RX_ODDSPACE.search(old):
                    kind = "unicode space -> U+0020"
                elif old != old.strip():
                    kind = "leading/trailing space"
                else:
                    kind = "internal double space"
                kinds[kind] = kinds.get(kind, 0) + 1
                samples.setdefault(kind, []).append((cat, f, old, new))
                changed_fields += 1
                row_hit = True
                if not dry:
                    row[f] = new
            if row_hit:
                changed_rows += 1

    print("entity_fix%s: %d rows changed (%d fields)"
          % (" (DRY RUN)" if dry else "", changed_rows, changed_fields))
    for kind in sorted(kinds, key=lambda k: -kinds[k]):
        print("  %-26s %5d" % (kind, kinds[kind]))
        for cat, f, old, new in samples[kind][:2]:
            print("      [%s/%s] %r" % (cat, f, old[:64]))
            print("      %s-> %r" % (" " * (len(cat) + len(f) + 3), new[:64]))

    if not dry:
        json.dump(d, open(path, "w"), ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
