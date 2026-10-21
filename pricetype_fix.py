#!/usr/bin/env python3
"""Normalize `price_type` to the schema enum, and drop one adults-only row — 2026-08-28.

`price_type` is a schema-v3.1 field with three legal values: `Free | Paid | Varies`. Nothing
in the pipeline validates it, and because the base is carried forward wholesale, a bad value
survives indefinitely (491 non-schema values were found this way on 2026-08-14). This run
arrives with 281 BLANK values and one `Donation`.

**A price is a factual claim a family acts on at a ticket counter** — the same standard
CLAUDE.md sets for `deal_description`. So blanks are filled only where a SOURCE, not a guess,
supports the value:

* Library systems (`hclib`, `rclreads`, `*_libcal`, `ecrl`) -> `Free`. SKILL.md's iCal mapping
  rule states outright: "`price_type`=`free` for library programs unless the DESCRIPTION
  states a fee."
* MN DNR state-park naturalist programs (`dnr_stpk`) -> `Free`. SKILL.md: "state-park programs
  are free; a vehicle permit is separate — do not mark as paid."
* Any row whose own text quotes a dollar amount -> `Paid`, with that amount copied into
  `price`.
* **Everything else -> `Varies`, never `Free`.** The remaining blanks are municipal and CVB
  event feeds (visit_winona, willmar, brainerd, burnsville, ...) which publish free and
  ticketed events side by side without a price field. `Varies` is the schema's honest
  "depends / check the listing"; stamping `Free` on 58 rows on the strength of "most community
  events are free" would ship a claim no source made.

`Donation` -> the single row is South Washington County Schools ECFE, whose own description
says "sliding scale fees" — that is `Varies`, not `Free`.

Also removes ONE row the adult filter missed: a 9:00pm, $5, **21+** bar music show. It is not
a near-miss for a family guide; the filter's phrase list simply has no `21+` token. Two other
`21+` matches were inspected and KEPT — a junior volunteer program that pairs a child with an
adult chaperone "(age 21+)", and a pinball bar that is family-friendly until 8pm. Both are
exactly the false positives an unexamined regex sweep would have deleted.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import json, re, collections

WORK = "_compiled_work.json"
CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
ALLOWED = {"Free", "Paid", "Varies"}
FREE_SRC = re.compile(r"src:(hclib|rclreads|ecrl|dnr_stpk|[a-z]+_libcal)\b")
MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{2})?)")
ADULT_DROP = "Live Music: The Lavender Project w/ Thundergrass"

d = json.load(open(WORK))
fixed = collections.Counter()
report = {"filled": [], "recased": [], "dropped_adult": []}

for c in CATS:
    keep = []
    for r in d[c]:
        title = str(r.get("title") or "")
        if c == "events" and title.startswith("Live Music: The Lavender Project"):
            report["dropped_adult"].append({"title": title,
                                            "why": "9:00pm show, $5 entry, 21+ only"})
            fixed["dropped_adult"] += 1
            continue

        v = str(r.get("price_type") or "").strip()
        if v in ALLOWED:
            keep.append(r)
            continue

        tags = str(r.get("tags") or "")
        blob = f"{title} {r.get('description') or ''}"
        m = MONEY.search(blob)
        if v.lower() in ("free", "paid", "varies"):
            new, why = v.capitalize(), "casing"
        elif v.lower() == "donation":
            new, why = "Varies", "donation/sliding-scale is not Free"
        elif m:
            new, why = "Paid", f"quoted price ${m.group(1)}"
            if not str(r.get("price") or "").strip():
                r["price"] = f"${m.group(1)}"
        elif FREE_SRC.search(tags):
            new, why = "Free", "library/DNR source — SKILL.md declares these free"
        else:
            new, why = "Varies", "no source states a price"

        r["price_type"] = new
        fixed[f"{v or '<blank>'} -> {new}"] += 1
        (report["recased"] if why == "casing" else report["filled"]).append(
            {"category": c, "title": title[:80], "from": v, "to": new, "why": why})
        keep.append(r)
    d[c] = keep

json.dump(d, open(WORK, "w"), ensure_ascii=False)

after = collections.Counter()
for c in CATS:
    for r in d[c]:
        after[str(r.get("price_type") or "<blank>")] += 1
print("price_type normalization:")
for k, v in fixed.most_common():
    print(f"    {k:52} {v}")
print("  final distribution:", dict(after))
bad = {k for k in after if k not in ALLOWED}
print("  NON-SCHEMA VALUES REMAINING:", bad if bad else "none")
why = collections.Counter(x["why"] for x in report["filled"])
print("  fill basis:", dict(why))
json.dump(report, open(RUNDIR + "/_pricetype_report.json", "w"),
          ensure_ascii=False, indent=1)
print("  report ->", RUNDIR + "/_pricetype_report.json")
