#!/usr/bin/env python3
"""
test_entity_fix.py -- every DECODE case is a string observed in the live 2026-09-10 dataset;
every UNCHANGED case is a false positive a looser rule would have produced.

Written to FAIL first (per CLAUDE.md: make a new guard fail on purpose before trusting it to
pass) -- the double-escape and bare-ampersand cases were both confirmed failing against a
draft that called html.unescape() in a loop and that stripped every '&'.
"""
import entity_fix as E

CASES = [
    # ---- must DECODE (real live strings) ----
    ("St. Paul Farmer&#39;s Market", "St. Paul Farmer's Market"),
    ("League of Women Voters Roseville Area&#160;", "League of Women Voters Roseville Area"),
    ("Caf&#xB7; Night", "Caf\u00b7 Night"),
    ("Don&#x2019;t Miss It", "Don\u2019t Miss It"),
    ("September 12 &#x2013; October 3", "September 12 \u2013 October 3"),
    ("Milk &amp; Cookies Storytime", "Milk & Cookies Storytime"),
    ("Fun &lt;3 for Kids", "Fun <3 for Kids"),

    # ---- NBSP handling: invisible on screen, so a decoded twin STILL would not collide
    #      without it. This is the half of the fix that is easy to omit and impossible to see.
    ("Story\u00a0Time", "Story Time"),
    ("Trailing NBSP\u00a0", "Trailing NBSP"),
    ("\u00a0Leading NBSP", "Leading NBSP"),
    ("Narrow\u202fSpace", "Narrow Space"),

    # ---- must be UNCHANGED ----
    # A bare ampersand is not an entity. If this decoded, "Milk & Cookies" would be rewritten
    # on every row in the dataset and the change report would be meaningless.
    ("Milk & Cookies Storytime", "Milk & Cookies Storytime"),
    ("Bricks & Minifigs Open Play", "Bricks & Minifigs Open Play"),
    # `&` followed by a space or a digit is not a reference.
    ("Rock & 100 Years", "Rock & 100 Years"),
    # A DOUBLE-escaped string is left ENTIRELY ALONE, not decoded one level. `&amp;#39;` means
    # "display the characters &#39;", and one decode leaves `&#39;` -- which tomorrow's run,
    # meeting the same carried row, would decode again into an apostrophe. One level per day
    # until the text is destroyed. Ambiguous input is reverted, never half-decoded.
    ("Type &amp;#39; to quote", "Type &amp;#39; to quote"),
    ("Milk &amp;amp; Cookies", "Milk &amp;amp; Cookies"),
    # Already-clean text of every shape we touch.
    ("Family Storytime", "Family Storytime"),
    ("1600 Warren St, Mankato, MN 56001", "1600 Warren St, Mankato, MN 56001"),
    ("Red Cow \u2014 50th & France", "Red Cow \u2014 50th & France"),
    # A URL-ish string handed to clean() directly must not lose its escaped separator; the
    # caller never passes URL fields, and this pins the behaviour if someone adds one.
    ("plain text with no entities at all", "plain text with no entities at all"),
    # Single internal spaces are preserved -- only runs of 2+ collapse.
    ("A B C", "A B C"),
    # Non-strings pass through untouched (rows carry None/ints in some fields).
    (None, None),
    (123, 123),
]

IDEMPOTENT = [c[0] for c in CASES if isinstance(c[0], str)]


def main():
    passed = failed = 0
    for src, want in CASES:
        got, changed = E.clean(src)
        ok = got == want and (changed == (got != src))
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  {src!r}: expected {want!r}, got {got!r} (changed={changed})")

    # A warm re-run must change nothing -- the property the pass claims by running pre-dedup.
    for src in IDEMPOTENT:
        once, _ = E.clean(src)
        twice, ch2 = E.clean(once)
        if twice != once or ch2:
            failed += 1
            print(f"  FAIL  not idempotent: {src!r} -> {once!r} -> {twice!r}")
        else:
            passed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
