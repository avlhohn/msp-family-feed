"""STEP 7 error-log append -- UNDATED, folder-root, run date passed in.

Supersedes the `_errlog_NNNN*.py` family. Those were copied forward and hand-restamped every
run, which CLAUDE.md flags as a standing defect ("restamp every helper that stamps its own
date"): `_errlog_0907_feeds.py` hardcoded RUN = "2026-09-07", so running it unchanged on a
later day silently files the whole run under yesterday. The fix is not to restamp more
carefully, it is to remove the literal -- the run date is argv[1] and a missing/malformed one
is a HARD FAILURE, the same treatment fetch_feeds.py's window got on 2026-09-08.

What it does, in order:
  0. ASSERTS the run-scoped INPUT files are this run's, not yesterday's, BEFORE any append
     (existence + freshness of _findings.json, _run_summary.json and _image_backfill.json)
  1. appends this run's findings (passed in as a JSON file, --findings)
  2. appends one `ical_feed_pull` info row PER DISPATCHED FEED, built from the run's own
     _feedpull_all.json `report` list -- never by hand, so the log cannot drift from what
     actually dispatched
  3. appends the per-source `deal_source_yield` rows from _deals_yield.json
  3b. appends the single `image_backfill` marker (proves STEP 4.5 ran), from _image_backfill.json
  4. appends the single `run_summary` marker
  5. ASSERTS all of the above by CONTENT before exiting 0

Reserved issue_types (counted by the section-5 signal assertions -- do NOT reuse as free text):
  `ical_feed_pull`, anything beginning `deal_source_`, `image_backfill`, `run_summary`.

The assertions are the point. SKILL.md:840 calls the per-feed row "our verification signal --
always write it", and it still lapsed for six consecutive runs, because a missing row raises
nothing. A mandated log is not self-enforcing; if a signal matters, something has to fail when
it is absent.
"""
import csv, json, sys, os, collections, re

COLS = ["run_date", "severity", "category", "step", "issue_type", "item", "description",
        "resolved_date", "resolved_by", "resolution_note"]
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.csv")

if len(sys.argv) < 2 or not re.fullmatch(r"\d{4}-\d\d-\d\d", sys.argv[1]):
    raise SystemExit("errlog_step7.py: argv[1] must be the run date as YYYY-MM-DD.\n"
                     "  STEP 1 derives it from a server-side timestamp -- see params.txt.\n"
                     "  It is NOT read from the sandbox clock: the clock and the injected\n"
                     "  currentDate have both been wrong, and wrong IN AGREEMENT.")
RUN = sys.argv[1]
FINDINGS = sys.argv[2] if len(sys.argv) > 2 else "_findings.json"

new = []


def add(sev, cat, step, itype, item, desc):
    new.append({"run_date": RUN, "severity": sev, "category": cat, "step": step,
                "issue_type": itype, "item": str(item)[:200], "description": str(desc)[:500],
                "resolved_date": "", "resolved_by": "", "resolution_note": ""})


# ---- 0a. REGENERATE _run_summary.json FROM THE BUILT CSVs  (promoted 2026-09-25)
# The 2026-09-22 blast-radius finding, and its fix restated three times (09-22/-23/-24): a stale
# _run_summary.json trips the section-0 freshness assertion just below, which fires BEFORE
# open(LOG,"a") and so suppresses the ENTIRE run's logging -- the feed rows, the deal-yield rows,
# the image-backfill row, the coverage rows and every finding -- to prevent one stale row. It was
# applied for three consecutive runs only as dated one-off scripts (_mk_run_summary_09NN.py, each
# HARDCODING RUN_DATE), which is exactly the _errlog_NNNN antipattern this file exists to kill.
# Promoted here so the next run inherits the FIX, not the diagnosis: STEP 7 regenerates the marker
# at the top of the step, making the staleness UNREACHABLE rather than merely detected.
#
# Two disciplines the one-offs got right and a hand-copy gets wrong, both preserved here:
#   * COUNTS ARE READ, NEVER TYPED. Section 5 re-reads the same five CSVs and asserts this marker's
#     counts row-by-row, so a typed number is a hand-maintained duplicate of a value on disk (the
#     2026-09-06 phantom-delta shape). Regeneration reads the CSVs; the assertion re-reads them;
#     they agree by construction.
#   * The run date is RUN (argv[1], derived server-side by STEP 1) and the weekday is DERIVED from
#     it -- never a literal, per the _errlog_NNNN hand-restamp defect and the "DOW is DERIVED from
#     TODAY, never passed separately" rule. The window end prefers MSP_END from the environment
#     (what STEP 1 exports) and otherwise computes the last day of next month from RUN; both are
#     runtime-derived, neither is a literal.
# Category KEY vs FILE name (the 2026-09-22 correction): build_guide.py writes deals.csv /
# volunteer.csv while the keys are meal_deals / volunteer_opportunities.
def _regen_run_summary():
    import datetime
    import calendar
    root = os.path.dirname(os.path.abspath(__file__))
    files = {"events": "events.csv", "parks": "parks.csv", "meal_deals": "deals.csv",
             "volunteer_opportunities": "volunteer.csv", "restaurants": "restaurants.csv"}
    counts, bad = {}, {}
    for key, fn in files.items():
        with open(os.path.join(root, fn), "r", encoding="utf-8-sig", newline="") as fh:
            rdr = csv.reader(fh)
            header = next(rdr)
            counts[key] = sum(1 for _ in rdr)
        if len(header) != 21:
            bad[fn] = len(header)
    assert not bad, f"21-column contract violated: {bad}"

    run = datetime.date.fromisoformat(RUN)
    end_env = os.environ.get("MSP_END", "").strip()
    if re.fullmatch(r"\d{4}-\d\d-\d\d", end_env):
        end = datetime.date.fromisoformat(end_env)
    else:  # last day of NEXT month, the pipeline's fixed-window definition
        ny, nm = (run.year + 1, 1) if run.month == 12 else (run.year, run.month + 1)
        end = datetime.date(ny, nm, calendar.monthrange(ny, nm)[1])
    window_days = (end - run).days + 1
    dow = run.strftime("%A")
    total = sum(counts.values())

    summary = {
        "item": "run_summary",
        "run_date": RUN,
        "window": f"{RUN} to {end.isoformat()}",
        "window_days": window_days,
        "day_of_week": dow,
        "schema_version": "3.1",
        "counts": counts,
        "total_rows": total,
        "description": (
            f"msp-family-guide-daily {RUN} ({dow}), window {RUN}..{end.isoformat()} "
            f"({window_days} days). Built {total} rows: events {counts['events']}, "
            f"parks {counts['parks']}, meal_deals {counts['meal_deals']}, "
            f"volunteer_opportunities {counts['volunteer_opportunities']}, "
            f"restaurants {counts['restaurants']}. Counts READ from the five built CSVs, not typed. "
            "Marker regenerated at the top of STEP 7 so a carried-forward copy cannot trip the "
            "freshness guard (CLAUDE.md 2026-09-22 blast-radius class)."
        ),
    }
    with open(os.path.join(root, "_run_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    return summary


_regen_run_summary()


# ---- 0. ASSERT THE RUN-SCOPED INPUT FILES ARE THIS RUN'S, NOT YESTERDAY'S
# Found 2026-09-09. This file's founding lesson was "delete the date literal": the run date is
# argv[1] and a missing one is a hard failure. But that only removed the literal from the CONTROL
# FLOW. Both of this script's run-scoped INPUT artifacts -- _findings.json and _run_summary.json --
# sit at the folder root under undated names and are simply LEFT THERE by the previous run, so a
# run that forgets to regenerate one silently re-reads yesterday's and re-stamps it with today's
# run_date. That is the _errlog_NNNN family's defect wearing different clothes.
#
# It happened, and the two files failed DIFFERENTLY, which is the whole point:
#   * _run_summary.json WAS caught -- but only incidentally, because its counts assertion below
#     disagreed (claimed events=4964 against a built 4950). Had the counts coincidentally matched,
#     yesterday's PROSE would have published as today's marker and nothing would have objected.
#   * _findings.json was NOT caught at all. All 31 of yesterday's findings were appended under
#     run_date=2026-09-09, including one asserting "today is Tuesday" and a willmar 401 that did
#     not happen today. Prose is unasserted by construction; no row-level check can see it.
#
# So assert freshness by CONTENT (the findings must name today) and by MTIME (both must be newer
# than the fetch report, which every run necessarily regenerates). Verified by making each branch
# FAIL on purpose before trusting it to pass, per CLAUDE.md.
_run_verified = [f for f in json.load(open(FINDINGS)) if f[3] == "run_date_verified"]
assert len(_run_verified) == 1, (
    f"{FINDINGS} must carry exactly one `run_date_verified` finding, found {len(_run_verified)}. "
    "STEP 1 writes it; its absence means this file was not regenerated for this run.")
assert _run_verified[0][4] == RUN, (
    f"{FINDINGS} is STALE: its run_date_verified finding names {_run_verified[0][4]!r} but this "
    f"run is {RUN!r}. It is the PREVIOUS run's file, left at the folder root under an undated "
    "name. Regenerate it from this run's own results -- do not restamp it.")
_fetch_mtime = os.path.getmtime("_feedpull_all.json")
for _f in (FINDINGS, "_run_summary.json"):
    assert os.path.getmtime(_f) >= _fetch_mtime, (
        f"{_f} is OLDER than _feedpull_all.json, so it predates this run's fetch and is a "
        "carried-forward artifact from a previous run. Regenerate it.")

# ---- 0b. ASSERT STEP 4.5 (image backfill) ACTUALLY RAN THIS RUN
# Added 2026-09-13. STEP 4.5 (og:image + body/hero site_photo capture) is mandated by SKILL.md:1171
# but was ABSENT from CLAUDE.md's documented image chain (4.3 -> 4.35 -> 4.8 -> 4.9), so the nightly
# never entered it -- for weeks, silently, because a skipped step raises nothing. Same failure class
# as the six-run ical_feed_pull lapse and the run_summary lapse: a mandated action that produces no
# error when absent is invisible. The remedy is the one this file already uses -- make its absence a
# HARD FAILURE. STEP 4.5 must write _image_backfill.json; without it the curated_category ratchet
# quietly re-freezes every venue out of a real photo.
#
# This check is deliberately in section 0, BEFORE open(LOG,"a") -- so a SKIPPED 4.5 (the whole point
# of the guard) leaves error_log.csv untouched. That is the partial-write lesson of the 2026-09-13
# deal_source_ finding: the section-5 signal assertions run after the append and a failure there
# leaves rows already written. Existence/freshness belongs here; content consistency stays in 5.
assert os.path.exists("_image_backfill.json"), (
    "_image_backfill.json is MISSING: STEP 4.5 (image backfill) did not run this run. It is "
    "mandated by SKILL.md:1171 and is in CLAUDE.md's image chain. A skipped image backfill is the "
    "curated_category ratchet re-freezing venues out of a real photo. Run STEP 4.5 -- which writes "
    "this marker -- before STEP 7. Do NOT satisfy this by touching the file by hand.")
assert os.path.getmtime("_image_backfill.json") >= _fetch_mtime, (
    "_image_backfill.json is OLDER than _feedpull_all.json, so it is a carried-forward marker from "
    "a previous run and STEP 4.5 did not run THIS run. Regenerate it -- same stale-input hazard as "
    "_findings.json / _run_summary.json.")
_imgbf = json.load(open("_image_backfill.json"))
assert _imgbf.get("stop_reason") in ("completed", "deadline"), (
    f"_image_backfill.json stop_reason must be 'completed' or 'deadline', got "
    f"{_imgbf.get('stop_reason')!r}. It records WHY 4.5 stopped so a budget-starved pass "
    "('deadline', SKILL.md's 20-min ENRICH_DEADLINE hit) is distinguishable from a converged one "
    "('completed') -- and BOTH are distinguishable from a skip, which is the missing-file case "
    "above. Moving the silent failure one level down is not a fix.")
# Added 2026-09-16, and it closes a hole the THREE checks above could not see. On 2026-09-15 all
# three passed on a marker whose `stop_reason` was YESTERDAY'S verdict: step45_site_photo.do_dnr()
# merged `__meta__` forward, so the FILE was genuinely new and only a FIELD inside it was carried.
# Content-freshness and mtime-freshness were adopted precisely because they fail independently;
# this was a third mode neither covers. The marker now carries its own `run_date` and it is the
# cheap tell -- a marker whose run_date disagrees with argv[1] is stale whatever its mtime says.
# This is the `_findings.json` run_date_verified content check applied one level in. Fourth
# instance of the class (_errlog_NNNN literals -> _findings/_run_summary inputs -> __meta__
# fields): anything a run inherits under a stable name is stale until something ASSERTS otherwise.
assert _imgbf.get("run_date") == RUN, (
    f"_image_backfill.json run_date={_imgbf.get('run_date')!r} != this run {RUN!r}. The marker "
    "FILE is fresh but a FIELD inside it was inherited from a previous run -- the 2026-09-15 "
    "__meta__ defect. step45_site_photo.do_dnr() drops a stale __meta__ and keeps a fresh one; "
    "do_apply() stamps run_date from MSP_TODAY. Re-run STEP 4.5; do not edit this file by hand.")

# ---- 1. this run's findings
findings = json.load(open(FINDINGS))
for f in findings:
    add(*f)

# ---- 2. per-feed contribution rows, from the run's OWN fetch report
report = json.load(open("_feedpull_all.json"))["report"]
for r in report:
    src, status, n, note = r["source"], r["status"], r["in_window"], r.get("note", "")
    add("info" if status == "OK" else "warning", "events", "STEP 7", "ical_feed_pull", src,
        f"{src}: {n} in-window events folded into events (status {status}). {note}")

# ---- 3. per-source deal yield (registry requires per-source, never aggregate)
dy = json.load(open("_deals_yield.json"))
yrows = dy["rows"] if isinstance(dy, dict) else dy
for r in yrows:
    rec = {c: "" for c in COLS}
    rec.update({k: v for k, v in r.items() if k in COLS})
    rec["run_date"] = RUN
    rec["item"] = str(rec["item"])[:200]
    rec["description"] = str(rec["description"])[:500]
    new.append(rec)

# ---- 3b. STEP 4.5 image-backfill signal row, from the run's OWN marker.
# `image_backfill` is now a RESERVED issue_type (asserted below), alongside ical_feed_pull,
# deal_source_*, and run_summary. Per the 2026-09-13 prefix-collision finding, name any CHECK of
# this signal `<thing>_check`, never `image_backfill*`, or it enrolls itself in this assertion.
# A 'deadline' stop is a warning (the pass was budget-starved, not converged); 'completed' is info.
add("info" if _imgbf["stop_reason"] == "completed" else "warning", "images", "STEP 4.5",
    "image_backfill", _imgbf.get("item", "site_photo_pass"),
    _imgbf.get("description",
               f"image backfill: {_imgbf.get('upgraded', 0)} of {_imgbf.get('attempted', 0)} "
               f"eligible rows upgraded to a real photo; stopped: {_imgbf['stop_reason']}."))

# ---- 4. the run_summary marker, LAST
summary = json.load(open("_run_summary.json"))
add("info", "pipeline", "STEP 8", "run_summary", summary["item"], summary["description"])

# ---- append
with open(LOG, "r", encoding="utf-8-sig", newline="") as f:
    existing = list(csv.DictReader(f))
before = len(existing)
assert list(existing[0].keys()) == COLS, f"header drift: {list(existing[0].keys())}"

with open(LOG, "a", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    for r in new:
        w.writerow(r)

with open(LOG, "r", encoding="utf-8-sig", newline="") as f:
    after = list(csv.DictReader(f))
assert len(after) == before + len(new), "row-count check failed"

mine = [r for r in after if r["run_date"] == RUN]

# ---- 5. ASSERT THE MANDATED SIGNALS BY CONTENT ----------------------------------------
pulls = [r for r in mine if r["issue_type"] == "ical_feed_pull"]
assert len(pulls) == len(report), \
    f"ical_feed_pull rows {len(pulls)} != dispatched sources {len(report)}"
assert {r["item"] for r in pulls} == {r["source"] for r in report}, "feed name set mismatch"
assert all(r["description"].strip() for r in pulls), "an ical_feed_pull row is empty"

yields = [r for r in mine if r["issue_type"].startswith("deal_source_")]
assert len(yields) == len(yrows), f"deal yield rows {len(yields)} != {len(yrows)} sources"

backfill = [r for r in mine if r["issue_type"] == "image_backfill"]
assert len(backfill) == 1, f"image_backfill marker missing or duplicated: {len(backfill)}"
assert backfill[0]["description"].strip(), "the image_backfill row is empty"

markers = [r for r in mine if r["issue_type"] == "run_summary"]
assert len(markers) == 1, f"run_summary marker missing or duplicated: {len(markers)}"
# The marker must describe the FINAL published state. On 2026-09-06 it was written at STEP 7,
# BEFORE that run's STEP 8 repair removed 14 rows, so it recorded restaurants=476 against a
# published 462 -- a phantom -14 on the next run's delta. Assert it against the built CSVs.
for cat, fn in [("events", "events.csv"), ("parks", "parks.csv"), ("meal_deals", "deals.csv"),
                ("volunteer_opportunities", "volunteer.csv"),
                ("restaurants", "restaurants.csv")]:
    path = os.path.join(os.path.dirname(LOG), fn)
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        n = len(list(csv.DictReader(f)))
    claimed = summary["counts"][cat]
    assert n == claimed, (f"run_summary claims {cat}={claimed} but {fn} holds {n} rows. "
                          "The marker must describe the PUBLISHED artifacts.")

print(f"error_log.csv: {before} -> {len(after)} (+{len(new)})")
print(f"ical_feed_pull      ASSERTED  {len(pulls)} rows == {len(report)} dispatched sources")
print(f"deal_source_yield   ASSERTED  {len(yields)} rows == {len(yrows)} sources")
print(f"image_backfill      ASSERTED  exactly 1 (STEP 4.5 ran; stop={_imgbf['stop_reason']})")
print(f"run_summary         ASSERTED  exactly 1, and its counts match the built CSVs")
print("by severity:", dict(collections.Counter(r["severity"] for r in new)))
