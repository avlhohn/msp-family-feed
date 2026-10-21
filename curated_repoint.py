#!/usr/bin/env python3
"""curated_repoint.py -- re-derive rows stranded on a RETIRED curated image.

WHY THIS EXISTS
---------------
`image_upgrades.apply_curated_category()` gates on

    WEAK_SOURCES = {"", "blank", "stock_openverse", "openverse_named", None}

and `curated_category` is NOT in that set. So the layer only ever stamps a row
ONCE. Editing a mapping in `curated_images.csv` afterwards -- repointing
`tag,skating` from an outdoor-lake stock photo to an indoor rink photo, say --
changes the file and never reaches a single already-stamped row. That is the
one-way ratchet CLAUDE.md documents for the Wikimedia layer (which WAS fixed to
treat `curated_category` as upgradeable); this layer never got the same
treatment.

Found 2026-09-29: 69 published `curated_category` rows carried a URL that is no
longer present anywhere in `curated_images.csv`, 44 of them on the two outdoor
skating photos explicitly retired on 2026-09-27.

WHAT MAKES THIS PASS SAFE, AND WHY IT IS NARROW ON PURPOSE
----------------------------------------------------------
The eligibility test is not "looks stale" -- it is "this row's image_url is
ABSENT from curated_images.csv". An absent URL is positive proof the mapping was
retired, so re-deriving that row from the current file is correct by
construction. There is no judgement call and therefore no false-positive
surface. Rows whose curated URL is still live are left completely alone.

Three exclusions, each load-bearing:

  1. REAL_PHOTO_SOURCES (facebook / og_image / site_photo / wikimedia /
     stock_openverse_specific) are never touched. Those are photos of the actual
     place; generic curated art must never overwrite one.
  2. `curated` (the title/keyword override) is NOT eligible even when its URL is
     absent from the CSV. Measured 2026-09-29: all 12 such rows are per-park
     photographs under `park_images/` in the feed repo -- real, specific
     pictures assigned by a different route. Repointing them would DOWNGRADE a
     real park photo to generic stock. Only `curated_category` is in scope.
  3. A row that re-derives to nothing keeps what it has. A wrong image is
     cosmetic; a blank one is a regression, and this pass is not a cleaner.

The mapping logic is NOT reimplemented here. `image_upgrades` is imported and
its own `load_curated` / `_collect_multi` / `item_tags` / `_stable_pick` /
`norm` are called, so there is exactly one source of truth for how a row
resolves to an image. (Importing it is side-effect free: module level is
constants only and `main()` sits behind `__main__`.)

Idempotent by construction: after a row is repointed its URL IS in the CSV, so
it is no longer eligible. A second run applies 0.

USAGE
    python3 curated_repoint.py _compiled_work.json --dry-run   # report only
    python3 curated_repoint.py _compiled_work.json             # apply
    python3 test_curated_repoint.py                            # must pass

Paths resolve at runtime from MSP_RUNDIR (default "."); nothing is pinned to one
run's scratch directory and no date literal is carried.
"""
import argparse
import collections
import csv
import importlib.util
import json
import os
import sys

ROOT = os.environ.get("MSP_RUNDIR", ".")


def _load_image_upgrades(root=None):
    """Import image_upgrades.py by path so this helper works from any cwd."""
    root = root if root is not None else ROOT
    path = os.path.join(root, "image_upgrades.py")
    if not os.path.exists(path):
        raise SystemExit("FATAL: image_upgrades.py not found at %s -- this pass "
                         "reuses its mapping logic and must not reimplement it." % path)
    spec = importlib.util.spec_from_file_location("_iu_for_repoint", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def curated_urls(curated_csv):
    """Every image_url the curated file currently offers, read from the COLUMN.

    Deliberately read straight from the CSV rather than from load_curated()'s
    parsed structures: the question this pass asks is "does this URL still
    appear in the file at all", and the raw column is the honest answer to that
    regardless of match_type.
    """
    if not os.path.exists(curated_csv):
        raise SystemExit("FATAL: %s not found -- refusing to declare every URL "
                         "retired against a missing file." % curated_csv)
    with open(curated_csv, newline="", encoding="utf-8") as fh:
        urls = {r["image_url"].strip() for r in csv.DictReader(fh)
                if (r.get("image_url") or "").strip()}
    if not urls:
        raise SystemExit("FATAL: %s parsed to ZERO image_urls. Every row would "
                         "look retired. Refusing to run." % curated_csv)
    return urls


def resolve(iu, item, tag_map, cat_map):
    """What this row WOULD resolve to under the current curated file.

    Mirrors apply_curated_category's precedence exactly: a tag row wins over a
    category row, and among several options for one tag the choice is a stable
    hash of the title so a single event keeps the same image across runs.
    """
    for tg in iu.item_tags(item):
        if tg in tag_map:
            return iu._stable_pick(tag_map[tg], item.get(iu.F_TITLE)), "tag:%s" % tg
    options = cat_map.get(iu.norm(item.get(iu.F_CATEGORY)))
    if options:
        return iu._stable_pick(options, item.get(iu.F_TITLE)), "category"
    return None, "unresolved"


def repoint(data, iu, live_urls, curated):
    """Repoint stranded curated_category rows. Returns (changed, stats)."""
    tag_map = iu._collect_multi(curated["tag"])
    cat_map = iu._collect_multi(curated["category"])
    changed, stats = [], collections.Counter()

    cats = [k for k, v in data.items() if isinstance(v, list)]
    for cat in cats:
        for item in data[cat]:
            src = iu.norm(item.get(iu.F_SRC))
            url = (item.get(iu.F_IMG) or "").strip()
            if src in {iu.norm(x) for x in iu.REAL_PHOTO_SOURCES}:
                stats["skip_real_photo"] += 1
                continue
            if src != "curated_category":       # excludes `curated` on purpose
                stats["skip_not_curated_category"] += 1
                continue
            if not url or url in live_urls:
                stats["skip_url_still_live"] += 1
                continue
            new, via = resolve(iu, item, tag_map, cat_map)
            if not new:
                stats["skip_unresolved"] += 1   # keep what it has; never blank
                continue
            if new == url:
                stats["skip_same_url"] += 1
                continue
            changed.append({"category": cat, "title": item.get(iu.F_TITLE, ""),
                            "old": url, "new": new, "via": via})
            item[iu.F_IMG] = new
            stats["repointed"] += 1
    return changed, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?", default=os.path.join(ROOT, "_compiled_work.json"))
    ap.add_argument("--curated", default=os.path.join(ROOT, "curated_images.csv"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    iu = _load_image_upgrades()
    live = curated_urls(args.curated)
    with open(args.data, encoding="utf-8") as fh:
        data = json.load(fh)
    curated = iu.load_curated(args.curated)

    changed, stats = repoint(data, iu, live, curated)

    groups = collections.Counter((c["old"], c["new"], c["via"]) for c in changed)
    for (old, new, via), n in groups.most_common():
        print("  %4d  %-14s %s\n              -> %s" % (n, via, old, new))
    print("\nrepointed: %d rows over %d distinct retired images"
          % (stats["repointed"], len({c["old"] for c in changed})))
    for k in ("skip_url_still_live", "skip_not_curated_category",
              "skip_real_photo", "skip_unresolved", "skip_same_url"):
        print("  %-28s %d" % (k, stats[k]))

    if args.dry_run:
        print("\nDRY RUN -- nothing written.")
        return 0
    if not changed:
        print("\nNothing to do (converged).")
        return 0
    with open(args.data, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    print("\nWROTE %s" % args.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
