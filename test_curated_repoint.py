#!/usr/bin/env python3
"""Tests for curated_repoint.py.

Every case below is a real hazard, not a synthetic one. The three that matter
most are the EXCLUSIONS -- a pass that repoints a site_photo, a wikimedia photo
or a per-park `curated` photograph would silently replace a real picture of a
real place with generic stock art, which is the unrecoverable direction. The
inclusion case failing is cosmetic; an exclusion case failing is data loss.

Read failures BY MESSAGE, not by count.
"""
import csv
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cr", os.path.join(HERE, "curated_repoint.py"))
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)
iu = cr._load_image_upgrades(HERE)

PASS = FAIL = 0


def check(name, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL: %s\n   got:  %r\n   want: %r" % (name, got, want))


def write_curated(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["match_type", "match_value", "image_url", "notes"])
        for r in rows:
            w.writerow(list(r) + [""])
    return path


INDOOR = "https://example.org/indoor_rink.jpg"
RETIRED = "https://example.org/outdoor_lake.jpg"
GENERIC = "https://example.org/generic_event.jpg"

CURATED_ROWS = [
    ("tag", "skating", INDOOR),
    ("category", "events", GENERIC),
]


def run(items, curated_rows=CURATED_ROWS):
    """Repoint a list of items in one 'events' category. Returns the items."""
    path = write_curated(curated_rows)
    try:
        live = cr.curated_urls(path)
        curated = iu.load_curated(path)
        data = {"events": items}
        cr.repoint(data, iu, live, curated)
        return data["events"]
    finally:
        os.unlink(path)


def row(**kw):
    base = {"title": "Cheap Skate", "category": "events", "tags": "skating",
            "image_url": RETIRED, "image_source": "curated_category"}
    base.update(kw)
    return base


# --- 1. the inclusion case: a stranded curated_category row IS repointed -----
out = run([row()])
check("stranded curated_category row is repointed", out[0]["image_url"], INDOOR)
check("repoint does not change image_source", out[0]["image_source"], "curated_category")

# --- 2. a row whose curated URL is STILL LIVE is untouched -------------------
out = run([row(image_url=INDOOR)])
check("live curated URL untouched", out[0]["image_url"], INDOOR)

# --- 3-5. THE EXCLUSIONS. Each of these repointing = a real photo destroyed --
for src in ("site_photo", "wikimedia", "og_image", "facebook", "stock_openverse_specific"):
    out = run([row(image_url="https://venue.example/real_photo.jpg", image_source=src)])
    check("real photo protected: %s" % src,
          out[0]["image_url"], "https://venue.example/real_photo.jpg")

park = "https://raw.githubusercontent.com/avlhohn/msp-family-feed/main/park_images/logan-park.jpg"
out = run([row(image_url=park, image_source="curated")])
check("`curated` park photograph is NOT repointed (measured: all 12 are real park photos)",
      out[0]["image_url"], park)

# --- 6. a row that resolves to nothing keeps what it has, never blanked ------
out = run([row(tags="", category="nothing_maps_here")])
check("unresolvable row keeps its image rather than being blanked",
      out[0]["image_url"], RETIRED)

# --- 7. idempotency: the second pass must repoint ZERO -----------------------
path = write_curated(CURATED_ROWS)
try:
    live = cr.curated_urls(path)
    curated = iu.load_curated(path)
    data = {"events": [row()]}
    _, s1 = cr.repoint(data, iu, live, curated)
    _, s2 = cr.repoint(data, iu, live, curated)
    check("first pass repoints 1", s1["repointed"], 1)
    check("second pass repoints 0 (idempotent)", s2["repointed"], 0)
finally:
    os.unlink(path)

# --- 8. tag precedence over category (mirrors apply_curated_category) --------
out = run([row(tags="skating", category="events")])
check("tag row wins over category row", out[0]["image_url"], INDOOR)
out = run([row(tags="", category="events")])
check("falls back to category when no tag matches", out[0]["image_url"], GENERIC)

# --- 9. a row carrying NO image at all is not invented into existence --------
out = run([row(image_url="")])
check("blank image_url is left blank by this pass", out[0]["image_url"], "")

# --- 10. FAIL-ON-PURPOSE: an empty curated file must CRASH, not retire all ---
path = write_curated([])
try:
    try:
        cr.curated_urls(path)
        check("empty curated file must raise", "no raise", "SystemExit")
    except SystemExit as e:
        check("empty curated file raises with an explanatory message",
              "ZERO image_urls" in str(e), True)
finally:
    os.unlink(path)

# --- 11. FAIL-ON-PURPOSE: a MISSING curated file must crash too --------------
try:
    cr.curated_urls(os.path.join(tempfile.gettempdir(), "definitely_not_here_12345.csv"))
    check("missing curated file must raise", "no raise", "SystemExit")
except SystemExit as e:
    check("missing curated file raises", "not found" in str(e), True)

# --- 12. FAIL-ON-PURPOSE: remove the exclusion and case 3 must break ---------
# Proves the real-photo guard is WIRED, not merely present. Without this, a
# guard that silently never fires still shows green above.
_real = iu.REAL_PHOTO_SOURCES
try:
    iu.REAL_PHOTO_SOURCES = set()
    out = run([row(image_url="https://venue.example/real_photo.jpg",
                   image_source="site_photo")])
    # `curated_category` check still blocks it, so the SECOND guard must hold
    check("with REAL_PHOTO_SOURCES emptied, the source-equality guard still holds",
          out[0]["image_url"], "https://venue.example/real_photo.jpg")
finally:
    iu.REAL_PHOTO_SOURCES = _real

# with BOTH guards gone the row would be repointed -- proving the test is able
# to detect the failure it claims to guard against
_real = iu.REAL_PHOTO_SOURCES
_orig = cr.repoint
try:
    iu.REAL_PHOTO_SOURCES = set()

    def unguarded(data, iu_, live, curated):
        tag_map = iu_._collect_multi(curated["tag"])
        cat_map = iu_._collect_multi(curated["category"])
        n = 0
        for cat in [k for k, v in data.items() if isinstance(v, list)]:
            for item in data[cat]:
                u = (item.get(iu_.F_IMG) or "").strip()
                if not u or u in live:
                    continue
                new, _ = cr.resolve(iu_, item, tag_map, cat_map)
                if new and new != u:
                    item[iu_.F_IMG] = new
                    n += 1
        return [], {"repointed": n}
    cr.repoint = unguarded
    out = run([row(image_url="https://venue.example/real_photo.jpg",
                   image_source="site_photo")])
    check("control: with every guard removed the real photo IS clobbered "
          "(so the test can detect the failure it guards against)",
          out[0]["image_url"], INDOOR)
finally:
    iu.REAL_PHOTO_SOURCES = _real
    cr.repoint = _orig

print("\n%d passed, %d failed" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
