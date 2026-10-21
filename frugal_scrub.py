#!/usr/bin/env python3
"""frugal_scrub.py — strip Twin Cities Frugal Mom exclusive discount codes from
deal_description, everywhere they appear, on every run.

WHY THIS EXISTS
---------------
Twin Cities Frugal Mom was retired as a source on 2026-08-28 because her roundups
carried discount codes EXCLUSIVE to her — `TCFM`, `TCFMB$2OFF`, `FRUGALMOM25`, and
"mention the Twin Cities Frugal Mom post" style asks — that must not be republished
in this app. Retiring the source stops NEW pulls, but rows captured BEFORE that date
keep the codes baked into their `deal_description`, and the carried base preserves
them every run. So without a standing scrub the codes reappear the next day. This
pass removes them permanently.

WHAT IT DOES (surgically, clause by clause)
-------------------------------------------
`deal_description` is a semicolon-delimited list of separate discounts, e.g.
  "Free First Sundays; free with MELSA smARTpass; $3 off with code TCFM; Play for All..."
Only the offending clause is removed; every other publicly-true discount is kept:
  -> "Free First Sundays; free with MELSA smARTpass; Play for All..."
If NO legitimate clause remains (the code WAS the whole deal — Zero Gravity, Hyderabad),
`deal_description`/`deal_expiry` are blanked and `has_deal` is cleared, so no empty
deal card ships.

WHAT IT DELIBERATELY KEEPS
--------------------------
The Minnesota Renaissance Festival's own "Frugal Friday" promotion is NOT a Frugal Mom
code. It matches on the word "frugal" but not on "frugal mom" or any code token, so it
is left untouched. The match is intentionally on "frugal mom"/code tokens, never bare
"frugal".

USAGE
-----
  python3 frugal_scrub.py <file> [--dry-run]
Accepts either a compiled-data JSON (a dict of category -> list-of-rows, the pipeline's
_compiled_work.json shape) or a category CSV (a deal_description column). Writes back in
place unless --dry-run. Idempotent: a second run changes nothing.
"""
import sys, os, re, json, csv, io

# A clause is dropped if it names a Frugal Mom code token or the phrase "frugal mom".
# "TCFM" is a substring of TCFM / TCFMB / TCFMB$2OFF; "FRUGALMOM" covers FRUGALMOM25.
# "frugal mom" catches the "mention the Twin Cities Frugal Mom post" ask. Bare "frugal"
# (as in the Renaissance Festival's "Frugal Friday") is intentionally NOT matched.
OFFENDING = re.compile(r'TCFM|FRUGALMOM|frugal\s+mom', re.I)

DEAL_FIELDS_TO_CLEAR = ("deal_description", "deal_expiry")


def scrub_description(text):
    """Return (new_text, changed, emptied). Removes offending semicolon-clauses."""
    if not text:
        return text, False, False
    parts = [p for p in re.split(r'\s*;\s*', text) if p.strip() != ""]
    kept = [p for p in parts if not OFFENDING.search(p)]
    if len(kept) == len(parts):
        return text, False, False           # nothing offending -> untouched
    new = "; ".join(kept)
    return new, True, (new.strip() == "")


def scrub_row(row):
    """Mutate a row dict in place. Return 1 if the row was changed, else 0."""
    dd = row.get("deal_description", "") or ""
    new, changed, emptied = scrub_description(dd)
    if not changed:
        return 0
    row["deal_description"] = new
    if emptied:
        # the code was the entire deal -> no real discount remains
        row["deal_description"] = ""
        if "deal_expiry" in row:
            row["deal_expiry"] = ""
        if "has_deal" in row:
            # match the field's existing truthiness style (bool vs string)
            row["has_deal"] = False if isinstance(row["has_deal"], bool) else ""
    return 1


def process_json(path, dry):
    data = json.load(open(path, encoding="utf-8"))
    changed = 0
    emptied = 0
    if isinstance(data, dict):
        iterables = [v for v in data.values() if isinstance(v, list)]
    elif isinstance(data, list):
        iterables = [data]
    else:
        print("frugal_scrub: unrecognized JSON shape", file=sys.stderr)
        return 2
    for lst in iterables:
        for row in lst:
            if not isinstance(row, dict):
                continue
            before = row.get("deal_description", "")
            n = scrub_row(row)
            changed += n
            if n and not (row.get("deal_description") or "").strip():
                emptied += 1
    print(f"frugal_scrub[json]: {changed} deal_description(s) scrubbed "
          f"({emptied} deals cleared entirely){' [DRY-RUN]' if dry else ''}  {path}")
    if not dry and changed:
        tmp = path + ".tmp"
        json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, path)
    return 0


def process_csv(path, dry):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = rows[0].keys() if rows else []
    if not rows or "deal_description" not in (fieldnames or []):
        print(f"frugal_scrub[csv]: no deal_description column, skipped  {path}")
        return 0
    changed = 0
    for row in rows:
        changed += scrub_row(row)
    print(f"frugal_scrub[csv]: {changed} deal_description(s) scrubbed"
          f"{' [DRY-RUN]' if dry else ''}  {path}")
    if not dry and changed:
        # preserve CRLF line endings the pipeline writes (see publish_feed note)
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(fieldnames))
        w.writeheader()
        w.writerows(rows)
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write(buf.getvalue())
    return 0


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 1
    path = args[0]
    if path.lower().endswith(".json"):
        return process_json(path, dry)
    return process_csv(path, dry)


if __name__ == "__main__":
    sys.exit(main())
