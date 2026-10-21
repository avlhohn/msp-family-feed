"""STEP 3 compile — carried base + this run's feed rows.

Promoted to the folder ROOT under an undated name 2026-08-30.  The 2026-08-29 run wrote
this logic into `.run0829/_merge0829.py`, where the next run could not reach it — the same
stranding bug CLAUDE.md records for `dupsweep`/`seeds_reassert`/`publish_feed`.  DECC and
`tagify()` were BOTH implemented on 2026-08-29 and BOTH lost for exactly this reason.
Nothing here may hardcode a run date, a `.runNNNN/` path, or a `/sessions/<name>/` path.

Output is a DICT of five category lists (NOT a flat list).  Verified on disk 2026-08-29:
`_seeds`/`_dupsweep`/`deals_overlay`/`dedup_titles` all index it by category, so
`bycat_shim.py` is unnecessary.

Window rule: an `events` row is dropped only if it carries a NON-BLANK date outside
[TODAY, END].  A blank date means a standing/recurring attraction (SKILL.md lines 546, 610)
and must be carried, never aged out.  `parks`/`restaurants` are evergreen.

Stale-date rule (CLAUDE.md): an out-of-window `meal_deals` / `volunteer_opportunities` row
dated exactly a PREVIOUS run's TODAY is an "as-of" stamp a recurring row picked up when it
was written -- not a claim the offer ended.  `build_guide.py` already blanks `date` for
`restaurants`/`parks` for this reason; the same leak is unhandled in those two categories.
Blank the date (keeping the row) unless the row's OWN text states a range still covering
today.  Never roll a date forward unconditionally: that asserts an offer is still running on
the strength of nothing but its having existed yesterday.
"""
import json, os, re, sys, collections, datetime

# There is deliberately NO default for the window (added 2026-09-10).  Both `fetch_feeds.py`
# and `build_guide.py` were given hard-fail guards under CLAUDE.md's "delete the date literal"
# rule, and this file was MISSED: it carried MSP_TODAY defaulting to a literal "2026-09-07",
# three days stale by the time it was found.  The default is more dangerous here than anywhere
# else in the chain, because TODAY/END drive the window test that decides which `events` rows
# age out -- so a silent fallback does not crash and does not warn, it just keeps or drops the
# wrong rows and hands the rest of the pipeline a plausible-looking dataset.
# A date a helper can guess is a date it will guess wrong: make its absence a crash.
TODAY = os.environ.get("MSP_TODAY", "").strip()
END = os.environ.get("MSP_END", "").strip()
for _n, _v in (("MSP_TODAY", TODAY), ("MSP_END", END)):
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", _v):
        raise SystemExit(
            f"compile_step3.py: env {_n} must be set to YYYY-MM-DD (got {_v!r}).\n"
            "  STEP 1 derives the run date and window end from a server-side timestamp.\n"
            "  There is deliberately NO default: the window silently decides which events\n"
            "  age out, so a stale fallback yields a wrong dataset with no error at all.")
if END < TODAY:
    raise SystemExit(f"compile_step3.py: MSP_END ({END}) precedes MSP_TODAY ({TODAY}).")
RUNDIR = os.environ.get("MSP_RUNDIR", ".")
CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
BASEJSON = os.environ.get("MSP_BASE", "msp_family_guide.json")
FEEDS = ["all"]          # fetch_feeds.py writes one combined `_feedpull_all.json`
OUT = "_compiled_work.json"

BASE = ['title', 'description', 'category', 'price_type', 'price', 'age_range', 'address',
        'latitude', 'longitude', 'image_url', 'image_source', 'date', 'time', 'phone',
        'website', 'has_deal', 'deal_description', 'deal_expiry', 'tags']

# Sources whose rows are library programming.  SKILL.md mandates a `library` content tag on
# every LibCal / BiblioCommons row: without it these rows carry only venue-plumbing tags,
# and the image stage matched a bilingual storytime to a fire-truck photo on that basis.
#
# `sppl` ADDED 2026-09-08.  Saint Paul Public Library was wired into fetch_feeds.py's BIBLIO
# list on 2026-09-07 and contributed 669 in-window rows immediately -- but THIS set was not
# updated, so every one of those rows reached the image stage carrying plumbing tags only.
# The defect was invisible for the same reason CLAUDE.md records for the adult filter's
# missing `brewing` token: a vocabulary gap in a lookup set looks exactly like a source that
# has nothing to match -- no error, no warning, just a quiet zero.  It is the same failure
# CLAUDE.md already names for `deals_yield` vs `deals_overlay.SOURCE_KEYS`: two registries
# naming the same sources with nothing keeping them in sync.  The assertion below is the part
# that stops it recurring; adding the token alone would just reset the clock.
# `stillwater_libcal` / `bayport_libcal` ADDED 2026-09-16 alongside the washco per-cid
# fan-out. The assertion below caught the omission on the SAME run the two sources were
# wired -- the drift alarm firing on live data, which is the outcome the sppl case above
# was written to produce. Note it also survived a change to the LIBCAL tuple's ARITY
# (3 -> 5 elements); the reader reads the table's extent, not its shape.
#
# 2026-09-18: the hand-rolled bracket-depth scan that used to read those tables was
# REPLACED with `ast` after it was found to stop at a bare `]` INSIDE A COMMENT -- and the
# comment it choked on was an explanation of the bracket-depth scan.  It then reported
# 8 of 38 sources as the whole table and PASSED.  That is the second hand-rolled scanner
# to fail here by UNDER-reading, which is the dangerous direction: "nothing missing" and
# "nothing seen" are the same output, so the check manufactures the confidence it exists
# to earn.  Hence also the vacuous-pass guard below: reading ZERO sources is a parse
# failure, never an empty fetcher.
LIBRARY_SRC = {"hclib", "rclreads", "sppl", "anoka_libcal", "washco_libcal", "dakota_libcal",
               "carver_libcal", "griver_libcal", "scott_libcal", "ecrl", "krls",
               "winona_library", "stillwater_libcal", "bayport_libcal",
               # Great River Regional per-branch calendars, wired 2026-09-18 after the
               # umbrella cid 18620 was found to carry 1 in-window row for a ~30-branch
               # system (386 across the branches).  These arrived here because the
               # assertion below FAILED on them -- the drift alarm doing its job a second
               # time, on the same run the sources were wired.
               "griver_albany", "griver_annandale", "griver_becker", "griver_belgrade",
               "griver_biglake", "griver_buffalo", "griver_clearwater",
               "griver_cokato", "griver_coldspring", "griver_delano",
               "griver_eaglebend", "griver_elkriver", "griver_foley",
               "griver_greyeagle", "griver_howardlake", "griver_kimball",
               "griver_littlefalls", "griver_longprairie", "griver_melrose",
               "griver_monticello", "griver_paynesville", "griver_pierz",
               "griver_richmond", "griver_rockford", "griver_royalton",
               "griver_saukcentre", "griver_staples", "griver_stcloud",
               "griver_stmichael", "griver_swanville"}


def _assert_library_src_covers_fetcher():
    """Fail loudly if fetch_feeds.py dispatches a library system this set does not know.

    Reads the fetcher's own BIBLIO / LIBCAL tables as the source of truth rather than
    duplicating them, so a source added there can never again silently miss its mandated
    `library` tag.  Soft-fails if the fetcher is unreadable -- this is a drift alarm, not a
    dependency.  Retired sources may remain in LIBRARY_SRC (a stale ALLOW entry is harmless;
    a missing one is the defect), so the check is one-directional by design.
    """
    try:
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "fetch_feeds.py"), encoding="utf-8").read()
    except OSError:
        return
    # Parse the fetcher with PYTHON'S OWN PARSER.  Two hand-rolled scanners have now failed
    # here, each in a way that UNDER-read the table and therefore reported success:
    #
    #   1. A lazy regex `\[(.*?)\]` overran the list and swallowed the function bodies below
    #      it, where `.get("address")` is indistinguishable from an entry `("address", ...)`
    #      -- 13 phantom "missing systems" including `zip` and `pagination` (2026-09-08).
    #   2. The bracket-depth scan that replaced it counts brackets in COMMENTS.  On
    #      2026-09-18 a comment added inside the LIBCAL literal contained a bare `]` in
    #      prose; depth hit zero there and the slice ended mid-comment, capturing 8 of 38
    #      rows.  The 30 new `griver_*` sources were invisible and the check PASSED -- while
    #      the comment it choked on was, exactly, an explanation of the bracket-depth scan.
    #
    # Both failures share a shape worth naming: a parser that under-reads a registry
    # MANUFACTURES the confidence it was supposed to earn, because "nothing missing" and
    # "nothing seen" are the same output.  The language ships a parser that handles comments,
    # strings, nesting and line continuations correctly, so the third attempt uses it.
    # Names are resolved one level (`LIBCAL = [...] + OTHER`), so splitting the table across
    # two module-level lists is now safe as well.
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    lists = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            lists[node.targets[0].id] = node.value

    def keys_of(expr, _depth=0):
        """First string element of every tuple in `expr`, resolving Name and `+`."""
        if _depth > 4:
            return set()
        if isinstance(expr, ast.Name):
            return keys_of(lists[expr.id], _depth + 1) if expr.id in lists else set()
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            return keys_of(expr.left, _depth + 1) | keys_of(expr.right, _depth + 1)
        out = set()
        if isinstance(expr, (ast.List, ast.Tuple)):
            for el in expr.elts:
                if isinstance(el, (ast.Tuple, ast.List)) and el.elts \
                        and isinstance(el.elts[0], ast.Constant) \
                        and isinstance(el.elts[0].value, str):
                    out.add(el.elts[0].value)
        return out

    dispatched = set()
    for block in ("BIBLIO", "LIBCAL"):
        if block in lists:
            dispatched |= keys_of(lists[block])
    # A scanner that reads ZERO rows would pass this check vacuously -- the exact failure
    # above.  Both tables are non-empty in every version of the fetcher, so an empty read
    # means the parse broke, not that the fetcher dispatches nothing.
    if not dispatched:
        raise SystemExit(
            "compile_step3.py: read 0 library sources out of fetch_feeds.py's BIBLIO/LIBCAL "
            "tables. That is a PARSE failure, not an empty fetcher -- do not treat the "
            "passing registry check that follows as meaningful until this is fixed.")
    missing = dispatched - LIBRARY_SRC
    if missing:
        raise SystemExit(
            "compile_step3.py: fetch_feeds.py dispatches library system(s) that LIBRARY_SRC "
            f"does not cover: {sorted(missing)}\n"
            "  Those rows would reach STEP 4.8 with venue-plumbing tags only and can be "
            "stamped with an unrelated image (SKILL.md mandates a `library` tag on every "
            "LibCal/BiblioCommons row).  Add them to LIBRARY_SRC above.")

# Content tags describing WHAT THE EVENT IS -- what the image chooser actually needs.
CONTENT = [
    ("story-time", r"\bstory\s?times?\b|\bstorytime\b|\bstory hour\b"),
    ("baby", r"\bbabies\b|\bbaby\b|\binfant\b|\blapsit\b|\blap sit\b"),
    ("toddler", r"\btoddlers?\b|\bwee\b|\bwiggle\b"),
    ("teen", r"\bteens?\b|\btween\b|\bya\b(?= )"),
    ("stem", r"\bstem\b|\bsteam\b|\blego\b|\brobotic|\bcoding\b|\bscience\b|\bmakerspace\b"),
    ("crafts", r"\bcraft|\bart\b|\bdiy\b|\bmaker\b|\bpainting\b|\bdrawing\b|"
               r"\bhandiwork\b|\bknit|\bcrochet|\bembroider|\bquilt|\bneedle|\byarn\b|"
               r"\bsew(?:s|ing|n)?\b|\bscrapbook|\borigami\b|\bmacram|\bcross[-\s]?stitch|"
               r"\bceramic|\bjewelry\b|\bcollage\b|\bbead(?:ing|ed|work)\b"),
    ("music", r"\bmusic\b|\bconcert\b|\bsing|\bband\b|\bdrum|\borchestra\b"),
    ("reading", r"\bbook club\b|\breading\b|\bbooks?\b|\bliterac"),
    ("games", r"\bgames?\b|\bchess\b|\bpuzzle|\bbingo\b|\bdungeons\b"),
    ("bilingual", r"\bbilingual\b|\bspanish\b|\bsomali\b|\bhmong\b|\bespa\w*ol\b"),
    ("movie", r"\bmovie\b|\bfilm\b|\bcinema\b"),
    ("outdoors", r"\bhike\b|\bhiking\b|\btrail\b|\bnature\b|\bbirding\b|\bcanoe|\bcamp"),
    ("animals", r"\banimal|\bzoo\b|\bwildlife\b|\bbats?\b|\bbirds?\b|\braptor"),
    ("play", r"\bplay\s?date\b|\bplaygroup\b|\bdrop-?in play\b|\bopen play\b"),
    ("sensory", r"\bsensory\b|\bautism\b|\binclusive\b|\badaptive\b"),
    ("food", r"\bcooking\b|\bbaking\b|\bfood\b|\bsnack\b"),
    ("skating", r"\bskat(e|ing)\b|\bhockey\b|\bstick and puck\b"),
    ("farmers-market", r"\bfarmers?\s?market\b"),
]
CONTENT = [(t, re.compile(p, re.I)) for t, p in CONTENT]

MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
MON_RE = "|".join(m for m in MONTHS if m)


def norm(it, cat):
    """Normalize a carried row to the 19 BASE fields.  `tags` is emitted as a STRING:
    CLAUDE.md records that a list here breaks the build, and every downstream pass in this
    pipeline splits on commas."""
    row = {k: it.get(k, "") for k in BASE}
    for k in BASE:
        if row[k] is None:
            row[k] = ""
    row["category"] = cat
    t = row["tags"]
    if isinstance(t, list):
        row["tags"] = ",".join(str(x).strip() for x in t if str(x).strip())
    else:
        row["tags"] = str(t or "")
    hv = row["has_deal"]
    row["has_deal"] = hv if isinstance(hv, bool) else str(hv).lower() in ("true", "1", "yes")
    row["_src"] = it.get("_src", "carry")
    return row


def covers_today(text):
    """True only if the row's OWN text states a date range that still covers TODAY.
    Precision-first, exactly like `end_date_pass.py`: a bare month name or a vague
    'through fall' is NOT evidence, because a wrong roll-forward claims an offer is still
    running when it is not."""
    blob = (text or "").lower()
    y = int(TODAY[:4])
    for m in re.finditer(r"\b(?:through|thru|until|ends?|runs? through)\s+(%s)\.?\s+(\d{1,2})\b"
                         % MON_RE, blob):
        mo, day = MONTHS[m.group(1)], int(m.group(2))
        try:
            end = datetime.date(y, mo, day).isoformat()
        except ValueError:
            continue
        if end >= TODAY:
            return True
    for m in re.finditer(r"\b(\d{4}-\d{2}-\d{2})\b", blob):
        if m.group(1) >= TODAY:
            return True
    return False


def tagify(row):
    """Merge existing tags with source + content tags. Returns a comma-joined string."""
    have = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]
    seen = {t.lower() for t in have}
    add = []
    if row.get("_src") in LIBRARY_SRC and "library" not in seen:
        add.append("library"); seen.add("library")
    blob = f"{row.get('title','')} {row.get('description','')}"
    # Puppet shows: match on TITLE only (precise — a "Big Truck Day" that merely mentions
    # puppets in its description must not be tagged). Exclude the venue "Puppet Library"
    # (In the Heart of the Beast), which gets its own venue photo via a keyword override.
    title_l = (row.get("title", "") or "").lower()
    if "puppet" in title_l and "puppet library" not in title_l and "puppet-show" not in seen:
        add.append("puppet-show"); seen.add("puppet-show")
    # Movie SCREENINGS: TITLE says movie/film/cinema. The bare `movie` CONTENT tag below is
    # description-scoped and polluted (a "Photo & Video Conversion" class that digitizes Super-8
    # FILM, and "Magnet Senior Center" drop-ins whose description mentions a movie), so the image
    # pool is led by this precise title tag instead. \bfilm\b does not match "filmmaking"; the
    # exclusion keeps a movie-MAKING/editing class or camp out (that is a workshop, not a showing).
    if (re.search(r"\bmovies?\b|\bfilms?\b|\bcinema\b", title_l)
            and not re.search(r"\b(class|classes|workshop|camp|making|editing|production|"
                              r"audition)\b", title_l)
            and "movie-screening" not in seen):
        add.append("movie-screening"); seen.add("movie-screening")
    # Theatre SHOWS: match on TITLE only, and only a real show to sit and watch. The raw source
    # `theater` tag is polluted (dance classes at Minnesota Dance Theatre, library "Creative
    # Expression Sessions" run by zAmya Theater, Circus Juventas, Caponi Art Park, an interactive
    # library "Fri-Yay! with Mixed Blood Theater" drop-in) — none are a stage show. So emit
    # `theatre-show` only when the title says theater/theatre, does NOT read as a
    # class/session/storytime/dance/circus/camp/workshop, AND carries a stage-show signal: the
    # title contains "presents"/"play"/a colon (a production title), or the row already carries a
    # show/performance/performing-arts tag. \btheater\b does not match "amphitheater".
    show_sig = (("presents" in title_l) or re.search(r"\bplay\b", title_l) or (":" in title_l)
                or bool(seen & {"show", "performance", "performing-arts", "performing arts"}))
    if (re.search(r"\btheat(?:er|re)s?\b", title_l)
            and not re.search(r"\b(class|classes|session|sessions|storytime|story\s?time|"
                              r"dance|circus|camp|workshop|audition|rehearsal|lesson)\b", title_l)
            and show_sig and "theatre-show" not in seen):
        add.append("theatre-show"); seen.add("theatre-show")
    # Fall seasonal: pumpkin patch / corn maze, TITLE-only for precision (a fall-festival
    # description that merely mentions a corn maze must not repaint the whole festival card).
    if re.search(r"\bpumpkin\s*patch\b", title_l) and "pumpkin-patch" not in seen:
        add.append("pumpkin-patch"); seen.add("pumpkin-patch")
    if re.search(r"\bcorn\s*maze\b", title_l) and "corn-maze" not in seen:
        add.append("corn-maze"); seen.add("corn-maze")
    # Art activities: painting / drawing, TITLE-only for precision. `\bpaint(?:s|ing|ings|ed)?\b`
    # matches paint/painting/painted but NOT "painter" (the park name "Painter Park") nor
    # "paintball"; the drawing rule additionally excludes "… Draw Park" (e.g. West Draw Park).
    # Both lead crafts/craft in the rebucket PRIORITY, so a painting/drawing-TITLED card gets the
    # specific art image while a generic "Craft Time" still draws from the broad craft pool (into
    # which these same art photos are folded).
    if (re.search(r"\bpaint(?:s|ing|ings|ed)?\b", title_l) and "painting" not in seen):
        add.append("painting"); seen.add("painting")
    if (re.search(r"\bdraw(?:s|ing|ings|n)?\b", title_l)
            and not re.search(r"\bdraw\s+park\b", title_l) and "drawing" not in seen):
        add.append("drawing"); seen.add("drawing")
    for tag, rx in CONTENT:
        if tag not in seen and rx.search(blob):
            add.append(tag); seen.add(tag)
    return ",".join(have + add)


def main():
    _assert_library_src_covers_fetcher()
    base = json.load(open(BASEJSON))
    print(f"carry base: {BASEJSON}  generated_date={base.get('generated_date')}  "
          f"counts={base.get('counts')}")
    out = {c: [] for c in CATS}
    st = collections.Counter()

    for c in CATS:
        for it in base.get(c, []):
            r = norm(it, c)
            d = (r.get("date") or "").strip()[:10]
            if d and not (TODAY <= d <= END):
                if c == "events":
                    st[f"{c}_dropped_out_of_window"] += 1
                    continue
                if c in ("meal_deals", "volunteer_opportunities"):
                    # stale "as-of" stamp -> blank the date, keep the row (see module docstring)
                    if covers_today(f"{r.get('title','')} {r.get('description','')} "
                                    f"{r.get('deal_description','')}"):
                        st[f"{c}_range_still_open"] += 1
                    else:
                        r["date"] = ""
                        st[f"{c}_stale_asof_date_blanked"] += 1
            out[c].append(r)
            st[f"{c}_carried"] += 1

    tagged = 0
    for w in FEEDS:
        p = os.path.join(RUNDIR, f"_feedpull_{w}.json")
        if not os.path.exists(p):
            p = f"_feedpull_{w}.json"
        try:
            rows = json.load(open(p))["rows"]
        except FileNotFoundError:
            print(f"  WARN missing {p}")
            continue
        for r in rows:
            before = r.get("tags") or ""
            r["tags"] = tagify(r)
            if r["tags"] != before:
                tagged += 1
            r.setdefault("category", "events")
            out["events"].append(r)
            st[f"feed_{w}"] += 1

    out["counts"] = {c: len(out[c]) for c in CATS}
    json.dump(out, open(OUT, "w"), ensure_ascii=False)
    print("STEP 3 compile ->", OUT)
    for k in sorted(st):
        print(f"  {k:42s} {st[k]:>6d}")
    print(f"  {'feed rows given content/library tags':42s} {tagged:>6d}")
    print("  " + "-" * 50)
    for c in CATS:
        print(f"  {c:42s} {len(out[c]):>6d}")
    print(f"  {'TOTAL':42s} {sum(len(out[c]) for c in CATS):>6d}")


if __name__ == "__main__":
    main()
