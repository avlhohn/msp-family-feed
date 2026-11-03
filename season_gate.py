#!/usr/bin/env python3
"""STEP 5.6 - season-gate blank-date STANDING events. Added 2026-11-03.

WHY: Seasonal series (outdoor concerts, movies in the park, KidStock) are stored
as blank-date "standing" rows so they are never aged out. The side effect is they
show YEAR-ROUND, so a summer-only series surfaces in November. This pass hides a
blank-date standing event from the PUBLISHED FEED when its season (from
seasonal_registry.json) does not intersect the run window's months.

CRITICAL - FEED-ONLY, like end_date_pass.py:
  * Operates ONLY on msp_family_guide.json (the feed Base44 reads).
  * NEVER touches the 5 category CSVs. The seasonal rows MUST stay in events.csv
    (the carried base) so they come back in season next year. Removing them from
    the base would delete them permanently. So run this AFTER build_guide.py.
  * Only blank-date rows are eligible. A row with a real date ages out on its own
    and is never gated.

Window months come from MSP_TODAY / MSP_END (preferred) or, failing that, from the
feed's own generated_date + date_range. Idempotent. Resolves paths from MSP_RUNDIR.
"""
import os, sys, re, json, datetime

RUNDIR = os.environ.get("MSP_RUNDIR", os.path.dirname(os.path.abspath(__file__)) or ".")

def months_between(d0, d1):
    out, y, mo = set(), d0.year, d0.month
    while (y, mo) <= (d1.year, d1.month):
        out.add(mo)
        mo += 1
        if mo > 12:
            mo = 1; y += 1
    return out

def window_months(feed):
    t = os.environ.get("MSP_TODAY", "").strip()
    e = os.environ.get("MSP_END", "").strip()
    if not t:
        t = (feed.get("generated_date") or "").strip()
    if not e:
        dr = (feed.get("date_range") or "")
        m = re.search(r"to\s+(\d{4}-\d{2}-\d{2})", dr)
        e = m.group(1) if m else t
    d0 = datetime.date.fromisoformat(t)
    d1 = datetime.date.fromisoformat(e)
    return months_between(d0, d1)

def main():
    feed_path = os.path.join(RUNDIR, sys.argv[1] if len(sys.argv) > 1 else "msp_family_guide.json")
    reg_path = os.path.join(RUNDIR, "seasonal_registry.json")
    dry = "--dry-run" in sys.argv
    feed = json.load(open(feed_path, encoding="utf-8"))
    rules = [(r["name"], re.compile(r["pattern"], re.I), set(r["months"]))
             for r in json.load(open(reg_path, encoding="utf-8"))["rules"]]
    wm = window_months(feed)

    kept, dropped = [], []
    for r in feed.get("events", []):
        if r.get("date"):                       # dated rows age out on their own
            kept.append(r); continue
        title = r.get("title", "") or ""
        hit = next((nm for nm, rx, mo in rules if rx.search(title) and not (mo & wm)), None)
        if hit:
            dropped.append((title, hit))
        else:
            kept.append(r)

    print(f"season_gate: window months {sorted(wm)} | dropped {len(dropped)} out-of-season standing events")
    for t, nm in dropped:
        print(f"  - [{nm}] {t}")
    if not dry:
        feed["events"] = kept
        if isinstance(feed.get("counts"), dict):
            feed["counts"]["events"] = len(kept)
        json.dump(feed, open(feed_path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"season_gate: wrote {feed_path} ({len(kept)} events)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
