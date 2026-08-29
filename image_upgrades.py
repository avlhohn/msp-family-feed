#!/usr/bin/env python3
"""
image_upgrades.py — STEP 4.8 of the msp-family-guide-daily pipeline.

Upgrades item imagery in four layers, in this precedence order (later wins):
  1. openverse_named   — real Openverse photo of a named proper place/venue,
                         applied only to items with no real photo yet
                         (image_source blank or 'stock_openverse').
  1b. wikimedia        — the named venue's OWN photo from Wikipedia's REST summary
                         API (a direct read-only API, NOT scraping). Unlike the
                         other upgrade layers this one is eligible on 'curated_category'
                         as well as the blank/weak sources: on the daily pipeline a
                         named venue arrives already stamped 'curated_category' from a
                         prior run, and the old blank-only gate froze it out of ever
                         getting a real photo (a one-way ratchet). Four precision
                         guards keep it from substituting the wrong place: a place-hint
                         gate (only venue-shaped titles are queried), name/page token
                         overlap, a Minnesota bounding-box check on the article's
                         coordinates (blocks a same-named park in another state), and a
                         logo/wordmark/SVG screen (a Wikipedia brand logo is not a
                         venue photo — same standard as STEP 4.5). Disambiguation pages
                         and 404s resolve to nothing and the item keeps its fallback.
                         Never overwrites a genuine self-photo or a hand-picked
                         'curated' override. Time-boxed and disk-cached by venue name.
  2. curated_category  — hand-picked category/tag fallback from curated_images.csv,
                         applied to items whose image_source is blank / stock_openverse
                         / openverse_named (i.e. NO real venue photo of their own).
                         A 'tag' row beats a 'category' row. Never overrides a real
                         'facebook' / 'og_image' / 'site_photo' photo. Multiple rows may share one
                         tag/category value; the layer spreads matching items across
                         those images by a stable per-title hash so the same picture
                         doesn't repeat across many events (differentiation).
  3. curated           — hand-picked title/keyword override from curated_images.csv.
                         Wins over the weak/fallback sources (blank, stock_openverse,
                         openverse_named, curated_category) — so it stays the backstop
                         for venues that have no real photo of their own — but DEFERS to
                         a genuine venue self-photo (facebook / og_image / site_photo /
                         stock_openverse_specific): a real, relevance-filtered photo of
                         the actual place beats generic curated art. (og_image and
                         site_photo only earn their labels after STEP 4.5's filter rejects
                         logos/wordmarks/banners, so by this point they are vetted real
                         photos of the actual place.)

Reads the compiled data (a JSON list of item dicts, or a dict with a 'records'/'items'
list) and writes the upgraded data back to the SAME file — only at the very end.

Usage:
    python3 image_upgrades.py [DATA_JSON] [--curated curated_images.csv]
                              [--deadline-seconds 420] [--no-openverse]
                              [--no-wikimedia] [--wiki-deadline-seconds 240]

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
import re
import csv
import json
import time
import glob
import html
import hashlib
import argparse
import urllib.parse
import urllib.request
from collections import Counter

# ----------------------------------------------------------------------------- config
OPENVERSE_URL = "https://api.openverse.org/v1/images/"
OPENVERSE_TIMEOUT = 8          # seconds per HTTP call
OPENVERSE_PAGESIZE = 8         # candidates fetched per named query
USER_AGENT = "msp-family-feed/1.0 (image_upgrades.py)"

# --- Wikimedia named-venue layer -------------------------------------------------
# Wikipedia REST summary endpoint: a direct read-only API (NOT web-page scraping),
# so it is policy-allowed exactly like the Openverse API above. For a proper-place
# title it returns the venue's own photo, or 404s; there is no wrong-place keyword
# match to fall into. Precision is enforced with three guards (place-hint gate,
# name/page token overlap, and a Minnesota bounding-box check on the article's
# coordinates) so a same-named venue in another state can never be substituted.
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_TIMEOUT = 6               # seconds per HTTP call
WIKI_CACHE = "_wiki_cache.json"   # disk cache, keyed by normalized venue name
# Minnesota bounding box (padded). MN spans lat 43.499-49.384, lon -97.239 to -89.489.
MN_LAT = (43.0, 49.6)
MN_LON = (-97.6, -89.2)
_OTHER_STATES = ("alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho", "illinois",
    "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "mississippi", "missouri", "montana", "nebraska",
    "nevada", "hampshire", "jersey", "mexico", "york", "carolina", "dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "wisconsin", "wyoming")

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


# ------------------------------------------------------------------- Wikimedia layer
# Rows eligible for a Wikimedia venue photo: those with no real photo of their own.
# CRUCIALLY this INCLUDES 'curated_category'. On the daily pipeline a named venue's
# row arrives already stamped 'curated_category' from a previous run, and the old
# Openverse gate (WEAK_SOURCES only) treated that as final — a one-way ratchet that
# permanently froze every named place out of ever getting a real photo. Treating
# curated_category as upgradeable here is the fix. It still never touches a genuine
# venue self-photo (facebook/og_image/site_photo/...) or a hand-picked 'curated'
# override.
WIKI_UPGRADEABLE = {"", "blank", "stock_openverse", "openverse_named",
                    "curated_category", None}

WIKI_STOPWORDS = {"the", "a", "an", "of", "and", "at", "in", "on", "for", "to",
    "with", "by", "&", "park", "event", "events", "day", "days", "festival", "fair",
    "show", "class", "classes", "storytime", "story", "time", "free", "family",
    "kids", "kid", "children", "childrens", "club", "group", "session", "sessions",
    "lab", "zone", "circle", "meetup", "hangout", "discussion", "gaming", "craft",
    "crafts", "knitting", "sewing", "chat", "chats", "night", "minnesota", "mn"}

_wiki_cache = None


def _wiki_norm(s):
    return html.unescape(re.sub(r"\s+", " ", (s or "").strip()))


def _wiki_tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if w not in WIKI_STOPWORDS and len(w) > 1}


def _wiki_has_hint(name):
    nl = (name or "").lower()
    return any(h in nl for h in PLACE_HINTS)


def _wiki_candidates(title):
    """Leading segment before a delimiter, then the full title. Venue names lead."""
    t = _wiki_norm(title)
    cands = []
    for delim in [" - ", " \u2013 ", " \u2014 ", " | ", " @ ", ": ", ", "]:
        if delim in t:
            head = t.split(delim)[0].strip()
            if head and head.lower() not in [c.lower() for c in cands]:
                cands.append(head)
            break
    if t.lower() not in [c.lower() for c in cands]:
        cands.append(t)
    return [c for c in cands if len(c) >= 3]


def _wiki_load_cache():
    global _wiki_cache
    if _wiki_cache is None:
        try:
            _wiki_cache = json.load(open(WIKI_CACHE)) if os.path.exists(WIKI_CACHE) else {}
        except Exception:
            _wiki_cache = {}
    return _wiki_cache


def _wiki_save_cache():
    if _wiki_cache is not None:
        tmp = WIKI_CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(_wiki_cache, fh)
        os.replace(tmp, WIKI_CACHE)


def _wiki_is_photo(url):
    """Reject logos/wordmarks/icons and vector graphics: the summary image is often a
    brand logo rather than a photo of the place, and shipping a logo would defeat the
    same STEP 4.5 filter that rejects logo og:images in favour of real venue photos.
    A photographed sign (e.g. a park entrance sign) is a real photo and is kept."""
    if not url:
        return False
    path = url.split("?", 1)[0].lower()
    if path.endswith(".svg") or path.endswith(".svg.png"):
        return False                # vector art on Wikipedia is virtually always a logo/map
    fname = path.rsplit("/", 1)[-1]
    return not any(bad in fname for bad in ("logo", "wordmark", "icon", "favicon", "seal"))


def _wiki_out_of_mn(data):
    """True if the article is confidently located OUTSIDE Minnesota. Coordinates are
    authoritative; the description string is a fallback when coordinates are absent."""
    c = data.get("coordinates") or {}
    lat, lon = c.get("lat"), c.get("lon")
    if lat is not None and lon is not None:
        return not (MN_LAT[0] <= lat <= MN_LAT[1] and MN_LON[0] <= lon <= MN_LON[1])
    desc = (data.get("description") or "").lower()
    if "minnesota" in desc:
        return False
    return any(s in desc for s in _OTHER_STATES)


def wiki_lookup(name):
    """Return (status, page_title, image_url). status in
    ok / notfound / disambig / noimage / outside_mn / err.
    Cached on disk by normalized name; transient errors are NOT cached."""
    cache = _wiki_load_cache()
    key = _wiki_norm(name).lower()
    if key in cache:
        return tuple(cache[key])
    url = WIKI_SUMMARY + urllib.parse.quote(_wiki_norm(name).replace(" ", "_"), safe="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                    "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=WIKI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        res = ("notfound", "", "") if e.code == 404 else ("err", str(e.code), "")
        if e.code == 404:
            cache[key] = list(res)
        return res
    except Exception as e:
        return ("err", str(e)[:40], "")     # transient: do NOT cache
    if data.get("type") == "disambiguation":
        res = ("disambig", data.get("title", ""), "")
    elif _wiki_out_of_mn(data):
        res = ("outside_mn", data.get("title", ""), "")
    else:
        img = ((data.get("originalimage") or {}).get("source")
               or (data.get("thumbnail") or {}).get("source") or "")
        if img and not _wiki_is_photo(img):
            img = ""                # logo/wordmark/vector: treat as no usable photo
        res = ("ok" if img else "noimage", data.get("title", ""), img)
    cache[key] = list(res)
    return res


def wiki_resolve(title, min_overlap=1):
    """High-precision resolve of a row title to a Minnesota venue's Wikipedia photo.
    Guards: (1) title must name a place (is_named_place); (2) only candidates that
    contain a place-hint word are queried, so generic activity titles like
    'Chess Club' are never attempted; (3) the returned page title must share a
    distinctive token with the candidate; (4) the article must sit inside the MN
    bounding box. Returns the image URL or None."""
    if not is_named_place(title):
        return None
    cands = [c for c in _wiki_candidates(title) if _wiki_has_hint(c)]
    for cand in cands:
        status, page, img = wiki_lookup(cand)
        if status == "ok":
            if len(_wiki_tokens(cand) & _wiki_tokens(page)) >= min_overlap:
                return img
            return None                 # matched a page but not the same entity
    return None


def apply_wikimedia_named(records, deadline_ts):
    """Upgrade eligible named-venue rows to their Wikipedia venue photo.
    Time-boxed like the Openverse layer; the disk cache is flushed periodically so
    the expensive network work is durable across a timeout and a re-run resumes
    from where it stopped (on the daily pipeline the cache is warm after day one)."""
    upgraded = 0
    since_save = 0
    _wiki_load_cache()
    for item in records:
        if time.time() >= deadline_ts:
            break
        if norm(item.get(F_SRC)) not in {norm(x) for x in WIKI_UPGRADEABLE}:
            continue
        title = item.get(F_TITLE) or ""
        if not is_named_place(title):
            continue
        try:
            url = wiki_resolve(title)
        except Exception:
            url = None
        since_save += 1
        if url:
            item[F_IMG] = url
            item[F_SRC] = "wikimedia"
            upgraded += 1
        if since_save >= 25:
            _wiki_save_cache()
            since_save = 0
    _wiki_save_cache()
    return upgraded


# ------------------------------------------------------------------- curated layers
def _collect_multi(pairs):
    """Group (match_value, url) pairs into {norm(match_value): [url, url, ...]},
    preserving CSV order and dropping duplicate URLs. Lets several rows share the
    same tag/category value so the layer has multiple images to choose among."""
    out = {}
    for mv, url in pairs:
        key = norm(mv)
        bucket = out.setdefault(key, [])
        if url and url not in bucket:
            bucket.append(url)
    return out


def _stable_pick(options, key):
    """Deterministically choose one URL from `options` for a given item `key`.

    Uses a stable md5 hash of the key (NOT Python's built-in hash(), which is
    salted per process) so the same event maps to the same image run-over-run
    (no flicker), while different events sharing a tag spread across the list
    (differentiation). Falls back to options[0] when key is empty."""
    if not options:
        return None
    if len(options) == 1:
        return options[0]
    k = norm(key)
    if not k:
        return options[0]
    h = int(hashlib.md5(k.encode("utf-8")).hexdigest(), 16)
    return options[h % len(options)]


def apply_curated_category(records, curated):
    """tag rows beat category rows; only touches weak-source items.

    Multiple curated rows may share the same tag/category value: they are gathered
    into a list and one is chosen per item by a stable hash of the item's title, so
    several events carrying the same tag (e.g. many 'parade' or 'community-fest'
    rows) are spread across the available images instead of all showing the one
    picture. A single event keeps the same image across runs."""
    weak = {norm(x) for x in WEAK_SOURCES}
    tag_map = _collect_multi(curated["tag"])
    cat_map = _collect_multi(curated["category"])
    upgraded = 0
    for item in records:
        if norm(item.get(F_SRC)) not in weak:
            continue
        options = None
        for tg in item_tags(item):          # tag row wins (more specific)
            if tg in tag_map:
                options = tag_map[tg]
                break
        if options is None:
            options = cat_map.get(norm(item.get(F_CATEGORY)))
        if options:
            url = _stable_pick(options, item.get(F_TITLE))
            if url:
                item[F_IMG] = url
                item[F_SRC] = "curated_category"
                upgraded += 1
    return upgraded


# genuine venue self-photos: a real, relevance-filtered photo of the actual place.
# The curated title/keyword override defers to these instead of overwriting them.
# 'site_photo' is the STEP 4.5 body/hero capture — the largest non-logo content photo
# on the item's OWN page, taken when its og:image was a logo/wordmark/banner. It clears
# the same relevance filter as og_image, so it is just as much a real venue photo and
# must be protected identically.
REAL_PHOTO_SOURCES = {"facebook", "og_image", "site_photo", "stock_openverse_specific",
                      "wikimedia"}


def apply_curated_override(records, curated):
    """title/keyword override. Wins over the weak/fallback sources, but DEFERS to a
    genuine venue self-photo (facebook / og_image / site_photo / stock_openverse_specific)
    — a real photo of the actual place beats generic curated art. Curated therefore stays
    the backstop for venues that have no real photo of their own."""
    protected = {norm(x) for x in REAL_PHOTO_SOURCES}
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
            if norm(item.get(F_SRC)) in protected:
                continue                     # keep the real venue photo; do not overwrite
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
    ap.add_argument("--no-wikimedia", action="store_true",
                    help="skip the network Wikimedia venue-photo layer")
    ap.add_argument("--wiki-deadline-seconds", type=int, default=240,
                    help="time budget for the Wikimedia layer (cache makes re-runs cheap)")
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

    wiki = 0
    if not args.no_wikimedia:
        wiki_deadline = time.time() + max(30, args.wiki_deadline_seconds)
        try:
            wiki = apply_wikimedia_named(records, wiki_deadline)
        except Exception as e:                      # never let this layer kill the run
            print("image_upgrades: wikimedia layer error (skipped): %s" % e,
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
        "wikimedia_named_applied": wiki,
        "curated_category_applied": cat,
        "curated_override_applied": override,
        "image_source_before": dict(before),
        "image_source_after": dict(after),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
