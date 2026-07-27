#!/usr/bin/env python3
"""
image_upgrades.py — STEP 4.8 of the msp-family-guide-daily pipeline.

Upgrades item imagery in three layers, in this precedence order (later wins):
  1. openverse_named   — real Openverse photo of a named proper place/venue,
                         applied only to items with no real photo yet
                         (image_source blank or 'stock_openverse').
  2. curated_category  — hand-picked category/tag fallback from curated_images.csv,
                         applied to items whose image_source is blank / stock_openverse
                         / openverse_named (i.e. NO real venue photo of their own).
                         A 'tag' row beats a 'category' row. Never overrides a real
                         'facebook' / 'og_image' photo.
  3. curated           — hand-picked title/keyword override from curated_images.csv,
                         applied to EVERY item. Wins over everything, including a real
                         photo and any curated_category fallback.

Reads the compiled data (a JSON list of item dicts, or a dict with a 'records'/'items'
list) and writes the upgraded data back to the SAME file — only at the very end.

Usage:
    python3 image_upgrades.py [DATA_JSON] [--curated curated_images.csv]
                              [--deadline-seconds 420] [--no-openverse]

If DATA_JSON is omitted, the script auto-discovers a compiled-data JSON in the
current working folder (a file whose top level is a list of dicts that carry the
expected item fields). curated_images.csv defaults to ./curated_images.csv.

The Openverse layer uses the public, read-only Openverse image-search API
(https://api.openverse.org/v1/images/) — this is an allowed direct API call, NOT
web-page scraping. It is time-boxed by --deadline-seconds (default 7 min) and fails
soft: any network error or empty result simply leaves the item's existing image
untouched. The script never raises on a single-item failure.
"""

import sys
import os
import csv
import json
import time
import glob
import argparse
import urllib.parse
import urllib.request
from collections import Counter

# ----------------------------------------------------------------------------- config
OPENVERSE_URL = "https://api.openverse.org/v1/images/"
OPENVERSE_TIMEOUT = 8          # seconds per HTTP call
OPENVERSE_PAGESIZE = 8         # candidates fetched per named query
USER_AGENT = "msp-family-feed/1.0 (image_upgrades.py)"

# item fields
F_TITLE = "title"
F_CATEGORY = "category"
F_TAGS = "tags"
F_IMG = "image_url"
F_SRC = "image_source"

# image_source values that mean "no real venue photo of its own" (safe to overwrite
# with an openverse_named / curated_category upgrade)
WEAK_SOURCES = {"", "blank", "stock_openverse", "openverse_named", None}

# words that signal the *title* names a recognizable proper place/venue worth an
# Openverse named-entity lookup
PLACE_HINTS = (
    "state park", "regional park", "county park", "city park", "nature center",
    "arboretum", "gardens", "garden", "zoo", "aquarium", "museum", "landmark",
    "lake", "falls", "river", "trail", "reserve", "refuge", "wildlife", "prairie",
    "forest", "conservatory", "observatory", "planetarium", "amphitheater",
    "fairgrounds", "festival", "library", "historic site", "monument", "beach",
    "island", "bluff", "caverns", "cave", "orchard", "farm", "vineyard",
)

# reject Openverse results whose title/tags smell like a person/portrait/protest
BAD_IMAGE_TOKENS = (
    "portrait", "protest", "rally", "headshot", "selfie", "mugshot", "funeral",
    "wedding", "obituary", "nude", "model", "person", "man ", "woman ", "boy ",
    "girl ", "politician", "senator", "governor", "president", "candidate",
)

# generic English words to ignore when scoring name-token overlap
STOPWORDS = {
    "the", "a", "an", "of", "and", "at", "in", "on", "for", "to", "park", "the",
    "minnesota", "mn", "st", "saint", "day", "days", "event", "class", "camp",
    "free", "kids", "family", "summer", "fall", "winter", "spring",
}


# ----------------------------------------------------------------------------- helpers
def norm(s):
    return (s or "").strip().lower()


def tokens(s):
    out = []
    for t in "".join(c if c.isalnum() else " " for c in norm(s)).split():
        if t and t not in STOPWORDS and len(t) > 2:
            out.append(t)
    return out


def item_tags(item):
    """Return the item's tags as a lowercased list, tolerating list or delimited str."""
    raw = item.get(F_TAGS)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [norm(t) for t in raw if str(t).strip()]
    # string form: split on comma / pipe / semicolon
    parts = str(raw).replace("|", ",").replace(";", ",").split(",")
    return [norm(p) for p in parts if p.strip()]


def is_named_place(title):
    t = norm(title)
    if any(h in t for h in PLACE_HINTS):
        return True
    # heuristic: a proper multi-word name in Title Case (>=2 capitalized words,
    # not a generic lowercase phrase)
    words = [w for w in (title or "").split() if w]
    caps = sum(1 for w in words if w[:1].isupper())
    return len(words) >= 2 and caps >= 2 and caps >= len(words) - 1


# ------------------------------------------------------------------- data file loading
def looks_like_items(obj):
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        keys = set(obj[0].keys())
        return F_TITLE in keys and (F_IMG in keys or F_CATEGORY in keys)
    return False


def load_data(path):
    """Return (records_list, container, write_back_fn). Supports a bare list or a
    dict that holds the list under a known key."""
    with open(path, "r", encoding="utf-8") as fh:
        obj = json.load(fh)
    if isinstance(obj, list):
        return obj, obj, lambda recs: recs
    if isinstance(obj, dict):
        for key in ("records", "items", "data", "listings"):
            if isinstance(obj.get(key), list):
                container = obj
                k = key

                def _wb(recs, _c=container, _k=k):
                    _c[_k] = recs
                    return _c

                return obj[key], obj, _wb
        # dict-of-categories (feed shape): merge category lists
        cat_keys = [k for k in ("events", "parks", "meal_deals",
                                "volunteer_opportunities", "restaurants")
                    if isinstance(obj.get(k), list)]
        if cat_keys:
            merged = []
            for k in cat_keys:
                merged.extend(obj[k])

            def _wb_cats(recs, _c=obj, _keys=cat_keys):
                # re-split by the item's category field
                buckets = {k: [] for k in _keys}
                for r in recs:
                    c = r.get(F_CATEGORY)
                    if c in buckets:
                        buckets[c].append(r)
                    else:
                        # keep unknown-category items in their original bucket if any
                        buckets[_keys[0]].append(r)
                for k in _keys:
                    _c[k] = buckets[k]
                return _c

            return merged, obj, _wb_cats
    raise ValueError("Unrecognized compiled-data shape in %s" % path)


def discover_data_file():
    candidates = []
    for pat in ("*compiled*.json", "*guide*data*.json", "*enriched*.json",
                "*merged*.json", "*.json"):
        for p in glob.glob(pat):
            base = os.path.basename(p).lower()
            if base in ("curated_images.json",):
                continue
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    obj = json.load(fh)
            except Exception:
                continue
            recs = None
            if looks_like_items(obj):
                recs = obj
            elif isinstance(obj, dict):
                for key in ("records", "items", "data", "listings",
                            "events", "parks"):
                    if looks_like_items(obj.get(key)):
                        recs = obj[key]
                        break
            if recs is not None:
                candidates.append((len(recs), p))
    if not candidates:
        return None
    # prefer the file with the most item records
    candidates.sort(reverse=True)
    return candidates[0][1]


# ------------------------------------------------------------------- curated CSV
def load_curated(path):
    """Return dict of lists keyed by match_type, each a (match_value, image_url) list.
    Blank-image_url rows are dropped."""
    out = {"title": [], "keyword": [], "category": [], "tag": []}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            mt = norm(row.get("match_type"))
            mv = (row.get("match_value") or "").strip()
            url = (row.get("image_url") or "").strip()
            if mt in out and mv and url:
                out[mt].append((mv, url))
    return out


# ------------------------------------------------------------------- Openverse layer
def openverse_search(query):
    params = urllib.parse.urlencode({
        "q": query,
        "page_size": OPENVERSE_PAGESIZE,
        "license_type": "all",
        "mature": "false",
    })
    req = urllib.request.Request(OPENVERSE_URL + "?" + params,
                                 headers={"User-Agent": USER_AGENT,
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=OPENVERSE_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("results", []) or []


def pick_named_image(title, results):
    want = set(tokens(title))
    if not want:
        return None
    best, best_score = None, 0
    for r in results:
        blob = norm(r.get("title")) + " " + norm(" ".join(
            t.get("name", "") if isinstance(t, dict) else str(t)
            for t in (r.get("tags") or [])))
        if any(bad in blob for bad in BAD_IMAGE_TOKENS):
            continue
        url = r.get("url") or ""
        if not url.lower().startswith("http"):
            continue
        have = set(tokens(blob))
        score = len(want & have)
        if score > best_score:
            best, best_score = url, score
    # require at least 2 shared distinctive tokens for a confident match
    return best if best_score >= 2 else None


def apply_openverse_named(records, deadline_ts):
    upgraded = 0
    cache = {}
    for item in records:
        if time.time() >= deadline_ts:
            break
        if norm(item.get(F_SRC)) not in {norm(x) for x in WEAK_SOURCES}:
            continue
        title = item.get(F_TITLE) or ""
        if not is_named_place(title):
            continue
        query = title.strip() + " Minnesota"
        if query in cache:
            url = cache[query]
        else:
            try:
                results = openverse_search(query)
                url = pick_named_image(title, results)
            except Exception:
                url = None
            cache[query] = url
        if url:
            item[F_IMG] = url
            item[F_SRC] = "openverse_named"
            upgraded += 1
    return upgraded


# ------------------------------------------------------------------- curated layers
def apply_curated_category(records, curated):
    """tag rows beat category rows; only touches weak-source items."""
    weak = {norm(x) for x in WEAK_SOURCES}
    tag_map = {norm(mv): url for mv, url in curated["tag"]}
    cat_map = {norm(mv): url for mv, url in curated["category"]}
    upgraded = 0
    for item in records:
        if norm(item.get(F_SRC)) not in weak:
            continue
        url = None
        for tg in item_tags(item):          # tag row wins (more specific)
            if tg in tag_map:
                url = tag_map[tg]
                break
        if url is None:
            url = cat_map.get(norm(item.get(F_CATEGORY)))
        if url:
            item[F_IMG] = url
            item[F_SRC] = "curated_category"
            upgraded += 1
    return upgraded


def apply_curated_override(records, curated):
    """title/keyword override, applied to EVERY item; wins over everything."""
    title_map = {norm(mv): url for mv, url in curated["title"]}
    keyword_rows = [(norm(mv), url) for mv, url in curated["keyword"]]
    upgraded = 0
    for item in records:
        t = norm(item.get(F_TITLE))
        url = title_map.get(t)
        if url is None:
            for kw, kurl in keyword_rows:    # substring/keyword match on title
                if kw and kw in t:
                    url = kurl
                    break
        if url:
            item[F_IMG] = url
            item[F_SRC] = "curated"
            upgraded += 1
    return upgraded


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?", help="compiled-data JSON (auto-discovered if omitted)")
    ap.add_argument("--curated", default="curated_images.csv")
    ap.add_argument("--deadline-seconds", type=int, default=420)
    ap.add_argument("--no-openverse", action="store_true",
                    help="skip the network Openverse named-entity layer")
    args = ap.parse_args()

    data_path = args.data or discover_data_file()
    if not data_path or not os.path.exists(data_path):
        print("image_upgrades: ERROR no compiled-data JSON found "
              "(pass it as the first argument)", file=sys.stderr)
        return 2

    records, container, write_back = load_data(data_path)
    curated = load_curated(args.curated)
    deadline_ts = time.time() + max(30, args.deadline_seconds)

    before = Counter(norm(i.get(F_SRC)) or "blank" for i in records)

    named = 0
    if not args.no_openverse:
        try:
            named = apply_openverse_named(records, deadline_ts)
        except Exception as e:                      # never let this layer kill the run
            print("image_upgrades: openverse layer error (skipped): %s" % e,
                  file=sys.stderr)
    cat = apply_curated_category(records, curated)
    override = apply_curated_override(records, curated)

    # write back ONLY at the end
    out_obj = write_back(records)
    tmp = data_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out_obj, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, data_path)

    after = Counter(norm(i.get(F_SRC)) or "blank" for i in records)
    print(json.dumps({
        "data_file": data_path,
        "records": len(records),
        "openverse_named_applied": named,
        "curated_category_applied": cat,
        "curated_override_applied": override,
        "image_source_before": dict(before),
        "image_source_after": dict(after),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
