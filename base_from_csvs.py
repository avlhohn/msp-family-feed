"""Build the STEP 3 carried base from the PUBLISHED CSVs, not from `msp_family_guide.json`.

WHY (found 2026-09-22).  `compile_step3.py` defaults `MSP_BASE` to `msp_family_guide.json`,
so the carried base is the FEED JSON.  The owner, however, edits the **CSVs** between runs —
the commits are hand uploads of `deals.csv` / `restaurants.csv` / `events.csv`, and nothing
regenerates the JSON from them.  So the two artifacts published by the same run can diverge,
and the next run carries the side the owner did NOT edit.

Measured on 2026-09-22.  Published JSON said `meal_deals=150, restaurants=459`; published
`deals.csv` said 140 and `restaurants.csv` said 461.  `events`, `parks` and `volunteer`
agreed exactly.  Carrying the JSON therefore resurrected **12 rows the owner had just
deleted** (the Smashburger / Ze's Diner / Andiamo / Dickey's kids-eat-free fragmentation
cluster) and **dropped the 2 rows the owner had just added** (`Tipsy Steer - Blaine`,
`Ze's Diner` with its real Woodbury street address, plus a corrected Pizza Luce row).

This is CLAUDE.md's 2026-09-02 "the owner edits the live artifacts between runs" finding
arriving through a door that entry does not cover.  That entry's remedy — "verify the local
artifacts match the remote by blob SHA-1 before trusting them as the carried base" — passes
here, and passes *while the defect is present*, because the local artifacts DO match the
remote.  The divergence is between two REMOTE artifacts, not between local and remote.

The CSVs win for three reasons:
  1. They are what the owner edits, so they are the only place a hand correction exists.
  2. They are what Base44 reads (the 21-column contract).
  3. `build_guide.py` rebuilds every row from `BASE` anyway, so the JSON carries no field
     the CSVs lack.  `end_date` lives ONLY in the JSON and is re-derived at STEP 5.5 from
     each row's own text, so nothing durable is lost by carrying the CSVs.

Deliberately NOT done: "fix" this by having the owner edit the JSON too, or by widening the
CSV contract.  Both are rules someone has to obey perfectly forever, which this project has
repeatedly shown is worth nothing.  Reading the artifact the owner actually edits needs no
discipline at all.

Usage (STEP 3, before `compile_step3.py`):

    python3 base_from_csvs.py                 # writes _base_from_csvs.json, prints the diff
    MSP_BASE=_base_from_csvs.json python3 compile_step3.py

Hard-fails on a missing CSV, on a column-set mismatch, and on a row whose key set is not
exactly the 19 BASE fields — the absence of an input must be a crash, not a default.
"""
import csv, json, os, sys

RUNDIR = os.environ.get("MSP_RUNDIR", ".")
OUT = os.path.join(RUNDIR, "_base_from_csvs.json")
JSONBASE = os.path.join(RUNDIR, "msp_family_guide.json")

# The 19 schema-v3.1 BASE fields, copied from build_guide.py / compile_step3.py.
BASE = ['title', 'description', 'category', 'price_type', 'price', 'age_range', 'address',
        'latitude', 'longitude', 'image_url', 'image_source', 'date', 'time', 'phone',
        'website', 'has_deal', 'deal_description', 'deal_expiry', 'tags']
# The two published columns that are NOT row data (they are constants stamped at build).
EXTRA = ['metro_area', 'schema_version']

# category key  ->  published CSV filename.  `meal_deals` publishes as deals.csv and
# `volunteer_opportunities` as volunteer.csv; `meal_deals.csv` is a KNOWN ORPHAN (CLAUDE.md)
# and must never be read here.
FILES = [
    ("events",                  "events.csv"),
    ("parks",                   "parks.csv"),
    ("meal_deals",              "deals.csv"),
    ("volunteer_opportunities", "volunteer.csv"),
    ("restaurants",             "restaurants.csv"),
]


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        cols = list(rdr.fieldnames or [])
        if cols != BASE + EXTRA:
            raise SystemExit(f"base_from_csvs.py: {path} columns are not the 21-column "
                             f"contract.\n  got:      {cols}\n  expected: {BASE + EXTRA}")
        rows = []
        for r in rdr:
            row = {k: (r.get(k) or "") for k in BASE}
            rows.append(row)
    return rows


def main():
    out, counts = {}, {}
    for cat, fn in FILES:
        p = os.path.join(RUNDIR, fn)
        if not os.path.exists(p):
            raise SystemExit(f"base_from_csvs.py: missing published artifact {p}. "
                             "The carried base cannot be assembled; do not fall back to the "
                             "feed JSON, which may be a commit behind the owner's edits.")
        rows = load_csv(p)
        for row in rows:
            if set(row) != set(BASE):
                raise SystemExit(f"base_from_csvs.py: row key set drift in {fn}")
        out[cat] = rows
        counts[cat] = len(rows)

    # Report the JSON-vs-CSV divergence rather than silently papering over it: a run where
    # the two agree is the normal case and should print zeros, so a NON-zero line is the
    # signal that the owner edited something since the last build.
    drift, checked = {}, False
    if os.path.exists(JSONBASE):
        checked = True
        j = json.load(open(JSONBASE, encoding="utf-8"))
        jc = {k: len(v) for k, v in j.items() if isinstance(v, list)}
        print(f"feed JSON  generated_date={j.get('generated_date')}  counts={jc}")
        for cat, _ in FILES:
            if jc.get(cat, 0) != counts[cat]:
                drift[cat] = (jc.get(cat, 0), counts[cat])
    else:
        print("feed JSON  ABSENT (no divergence check possible)")

    out["generated_date"] = ""       # deliberately blank: this is a BASE, not a built feed
    out["source"] = "published CSVs"
    out["counts"] = counts

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)

    print(f"base from CSVs -> {OUT}")
    for cat, _ in FILES:
        print(f"  {cat:26s} {counts[cat]:6d}")
    print(f"  {'TOTAL':26s} {sum(counts.values()):6d}")
    if not checked:
        # Never print a clean verdict for a check that did not run -- that is this project's
        # standing silent-failure class (a quiet zero reads exactly like a real all-clear).
        print("  JSON/CSV divergence: NOT CHECKED (no feed JSON present)")
    elif drift:
        print("  !! JSON/CSV DIVERGENCE (owner edited the CSVs after the last build):")
        for cat, (a, b) in drift.items():
            print(f"     {cat:24s} json={a}  csv={b}  delta={b - a:+d}")
    else:
        print("  JSON/CSV divergence: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
