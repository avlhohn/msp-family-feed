#!/usr/bin/env python3
"""STEP 4.5 -- og:image / body-hero `site_photo` backfill.

WHY THIS FILE EXISTS
--------------------
For weeks the nightly never ran STEP 4.5. SKILL.md:1171 mandated it the whole time, but
CLAUDE.md's documented image chain read `4.3 -> 4.35 -> 4.8 -> 4.9` and never named 4.5, and
the nightly treats CLAUDE.md as the running order. Nothing warned, because a skipped step
raises nothing -- the same invisible-lapse class as the six-run `ical_feed_pull` silence and
the `run_summary` lapse. The chain is now explicitly `4.3 -> 4.35 -> 4.5 -> 4.8 -> 4.9`, and
this pass is the 4.5 link. Before today no helper existed at all, so there was nothing to
inherit and nothing to restore.

THE MANDATED MARKER IS THE POINT
--------------------------------
A mandate is not self-enforcing, so the enforcement is a file. This pass MUST write
`_image_backfill.json` at the folder root, and `errlog_step7.py` asserts four things about it
before STEP 7 will exit 0: that it EXISTS (a skipped 4.5 is the case the guard is for), that
it is FRESH (mtime >= `_feedpull_all.json`, so yesterday's marker cannot pose as today's),
that `stop_reason` is one of exactly two legal values, and that exactly one non-empty
`image_backfill` row reaches the log.

`stop_reason` is load-bearing and must be honest:
  "completed" -- the eligible set was exhausted.
  "deadline"  -- the shared 20-minute ENRICH_DEADLINE hit first.
Without that distinction the fix just moves the silent failure one level down: a
budget-starved pass and a converged one would both report a number and look alike.

NOTE ON WHAT "COMPLETED" REALISTICALLY MEANS HERE. The eligible set is ~4,200 DISTINCT
websites. One WebFetch each, inside a 20-minute budget shared with 4.6-4.8, cannot exhaust
it and will not for the foreseeable future. So `deadline` is the expected honest answer on a
normal run, and `errlog_step7.py` logging it as a WARNING is correct -- it is a true statement
that this pass is budget-bound, not converged. Do not "fix" that warning by relabelling it
`completed`; that would be exactly the stale-claim-in-prose defect CLAUDE.md warns about.

WHY WEBFETCH, AND WHY TWO PHASES
--------------------------------
The pipeline is policy-bound to WebFetch for web pages -- never curl/requests. WebFetch is a
tool call, not something a Python process can make, so this helper cannot fetch anything
itself. It therefore runs in two phases with the fetching done between them:

    python3 step45_site_photo.py --select 40     -> _step45_candidates.json
    (WebFetch each candidate; record the chosen image URL per page)
    python3 step45_site_photo.py --apply         <- _step45_results.json

TARGETING IS BY DISTINCT WEBSITE, NOT BY ROW, and that is a deliberate trade. Ranking pages
by how many eligible rows they would improve means ~12 DNR state-park pages cover ~160 rows.
The cost is that it pushes against the feed's real weak spot -- CLAUDE.md records that one
image already covers 1,437 rows and the whole feed has only ~495 distinct image URLs. It is
still a strict improvement, because every row it touches is moving OFF a generic
`curated_category` category image and ONTO the venue's own photo from the venue's own page;
the fan-out is bounded by MAX_FANOUT below so one page cannot dominate.
"""
import json, os, re, sys, time
from urllib.parse import urljoin, urlparse

ROOT = os.environ.get("MSP_RUNDIR", os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "_compiled_work.json")
CAND = os.path.join(ROOT, "_step45_candidates.json")
RESULTS = os.path.join(ROOT, "_step45_results.json")
MARKER = os.path.join(ROOT, "_image_backfill.json")

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# The corrected gate. It keys on `image_source`, NOT on whether `image_url` is blank -- that
# was the original defect: nearly every row already carries a generic category image, so a
# blank-image gate matched almost nothing and the step looked like it had nothing to do.
GATE = {"curated_category", "stock", "openverse_named", ""}

# No single page may claim more than this many rows. Bounds the image-diversity cost above.
MAX_FANOUT = 25

# Reject logos/wordmarks/icons/vector art. Same standard as the Wikimedia layer's screen in
# image_upgrades.py -- a brand logo is not a venue photo, and shipping one defeats the whole
# purpose of preferring a real photo over the curated fallback.
BAD_TOKENS = ("logo", "wordmark", "icon", "favicon", "seal", "sprite", "placeholder",
              "avatar", "banner-ad", "pixel", "spacer", "badge", "btn-", "button")


def is_usable_image(u):
    """True if `u` looks like a real content photograph rather than chrome."""
    if not u or not isinstance(u, str):
        return False
    u = u.strip()
    if not u.lower().startswith(("http://", "https://")):
        return False
    path = urlparse(u).path.lower()
    if path.endswith((".svg", ".gif", ".ico", ".svg.png")):
        return False          # vector art / animations are virtually always chrome
    if not path.endswith((".jpg", ".jpeg", ".png", ".webp")):
        # Some CDNs serve extensionless images; allow only if the host looks like an image CDN
        #
        # `imagerepository/document` ADDED 2026-09-27, and it is a VOCABULARY completion, not a
        # SHAPE change -- the three grounds below and the BAD_TOKENS screen are untouched, which
        # is what makes it this task's call rather than the owner's (the 2026-09-07 `brewing`
        # precedent). It is the CivicPlus signature, and CivicPlus is what essentially every
        # Minnesota municipal .gov site runs on: park, pool and community-centre photos are served
        # from `/ImageRepository/Document?documentID=N`, extensionless, on a host matching none of
        # the CDN names above. So the whole municipal-parks class was being rejected as "not an
        # image" on the strength of its URL shape alone.
        #
        # This is the same failure class as the adult filter's `brewery`-but-not-`brewing` gap: a
        # vocabulary hole in a screen looks exactly like a source with nothing to catch -- no
        # error, just a quiet zero. It surfaced only because `--apply` prints `rejected_logo` with
        # an instruction to ATTRIBUTE the number, and attributing it showed 5 of 5 were the
        # EXTENSION ground and none was a logo -- the second consecutive run where that was true
        # (4 of 4 on 2026-09-22). A count reported under the wrong name stays unread.
        #
        # FALSE-POSITIVE SURFACE MEASURED BEFORE THE EDIT, on real cache data, per the same
        # precedent: 5 of 109 resolved photo URLs match the pattern, and all 5 were byte-checked
        # by magic number over the wire -- 3 JPEG, 2 PNG, 0 non-images. Provably zero FP here.
        #
        # WHAT THIS DOES NOT COVER, stated in the same breath as what it does: the endpoint is
        # extensionless, so `os.path.basename(path)` is always the literal "document" and the
        # BAD_TOKENS screen below is INERT for these URLs -- a CivicPlus LOGO served through the
        # same endpoint would be admitted. That is not new (the existing `cloudfront`/`imgix`
        # entries have the identical property) and it is bounded by the fact that the candidate
        # was already chosen as the page's largest body/hero image, but it is the reason every
        # accept on this route is byte-checked rather than trusted.
        if not re.search(r"(cloudfront|imgix|cloudinary|squarespace|wp-content|uploads"
                         r"|imagerepository/document)", u, re.I):
            return False
    fname = os.path.basename(path)
    return not any(b in fname for b in BAD_TOKENS)


# ---------------------------------------------------------------- DNR state parks
# THE DNR PARKS ARE THE SINGLE BIGGEST BLOCK OF ELIGIBLE ROWS AND WEBFETCH CANNOT SEE THEM.
#
# Our DNR rows carry `website` = https://www.dnr.state.mn.us/state_parks/<slug>, which is a
# JAVASCRIPT REDIRECT STUB. WebFetch converts HTML to markdown without executing scripts, so
# it retrieves the stub, not the park page, and reports NONE -- for every park, every run. A
# naive STEP 4.5 therefore reports "no usable photo" on ~180 of its highest-value rows and
# looks like it simply found nothing. That is the zero-is-a-claim-about-the-input case: the
# zero was a fact about the FETCH ROUTE, not about the source.
#
# The remedy needs no page fetch at all. The DNR calendar JSON -- the same allowed read-only
# API `fetch_feeds.run_dnr()` already calls -- carries `location_tag` (the park id, spkNNNNN)
# alongside `location_url`, and the park's own banner photo is at a deterministic path:
#
#     https://images.dnr.state.mn.us/destinations/state_parks/banners/<location_tag>.jpg
#
# TWO TRAPS, both found by verifying rather than assuming (2026-09-14):
#
#  1. DO NOT key on the JSON's `image` field. It is usually the park banner but sometimes an
#     EVENT image (`nature_cart.jpg`, `wildflowers.jpg`, `birding-winter.jpg`), and those do
#     not exist under banners/ -- they 404. Three of the first six sampled were exactly this.
#     `location_tag` is the park identity; `image` is whatever the event chose.
#  2. VERIFY THE ASSET, do not trust the pattern. Each URL is fetched and required to begin
#     with the JPEG magic bytes before it is used. A 404 page returned as an image URL would
#     otherwise ship a broken image to every row for that park, which is worse than the
#     generic category image it replaced.
def dnr_banner_map():
    """{park page URL -> verified banner image URL} from the DNR calendar JSON."""
    import urllib.request
    sys.path.insert(0, ROOT)
    import fetch_feeds as F
    base = ("https://webapps.dnr.state.mn.us/calendar/app?jsp=json"
            "&o=startdate&k=stpk&ae=y&p=")
    ban = "https://images.dnr.state.mn.us/destinations/state_parks/banners/"
    cand = {}
    for p in ("thismonth", "nextmonth"):
        try:
            data = json.loads(F.http(base + p, timeout=90))
        except Exception as e:
            print(f"   dnr {p}: {type(e).__name__} {e}")
            continue
        for ev in data.get("events", []):
            lu = (ev.get("location_url") or "").strip()
            tag = (ev.get("location_tag") or "").strip()
            # `sra` added 2026-10-01 -- a VOCABULARY completion, not a SHAPE change.
            #
            # The tag regex was `spk\d+` only, so every State RECREATION AREA was silently
            # excluded. CLAUDE.md 2026-09-29 recorded the symptom without the cause: "`big_bog`
            # was recorded `None` while `--dnr` verified 23 banners present ... its
            # `location_tag` lookup failed rather than the banner being absent." It did not
            # fail -- Big Bog State Recreation Area's tag is `sra00308`, and the regex rejected
            # it. Same class as the adult filter's `brewery`-without-`brewing` gap: a
            # vocabulary hole in a gate looks exactly like a source with nothing to catch.
            #
            # MEASURED BEFORE THE EDIT, per the standing rule. Over this run's window the
            # calendar carries 24 distinct `location_url`s: 23 `spk` (all already handled) and
            # exactly 1 `sra`. So the widening admits ONE url and the false-positive surface is
            # zero -- and the accept gate is unchanged regardless, because every candidate
            # still has to BYTE-CHECK as a JPEG below (sra00308.jpg: 200, 370,826 b, FF D8).
            # SRAs live in the same `state_parks/banners/` directory; a
            # `state_recreation_areas/` path 404s, which is why the directory is NOT widened.
            #
            # The shape is untouched: still derived from the calendar's own `location_tag`,
            # never guessed, and still byte-checked. That is what makes this the task's call.
            if lu and re.fullmatch(r"(?:spk|sra)\d+", tag):
                cand.setdefault("https://www.dnr.state.mn.us" + lu, ban + tag + ".jpg")
    out = {}
    for site, img in cand.items():
        try:
            rq = urllib.request.Request(img, headers={"User-Agent": "msp-family-guide/1.0"})
            if urllib.request.urlopen(rq, timeout=30).read(2) == b"\xff\xd8":
                out[site] = img
        except Exception:
            pass
    print(f"   DNR: {len(cand)} candidates -> {len(out)} banners verified present")
    return out


def load_work():
    d = json.load(open(WORK))
    d.pop("counts", None)
    return d


def eligible_rows(d):
    for cat in CATS:
        for r in d[cat]:
            if (r.get("image_source") or "").strip() in GATE:
                w = (r.get("website") or "").strip()
                if w.lower().startswith(("http://", "https://")):
                    yield cat, r, w


# --------------------------------------------------------------- rejection ledger
# WHY THIS IS A TOP-LEVEL KEY AND NOT PART OF `__meta__` (wired 2026-09-18).
#
# CLAUDE.md's 2026-09-15 entry requires 4.5 to record REJECTED candidates with reasons next
# to the accepted ones -- that record is what keeps the carried website->photo map
# trustworthy. Its 2026-09-17 entry observes that the list had been living inside `__meta__`,
# which `do_dnr()` now DROPS when stale, so the freshness fix was silently destroying the
# trust record, and says it was "fixed in-run by persisting rejections outside `__meta__`".
#
# That in-run fix never landed in this file. Verified 2026-09-18: `_step45_results.json` had
# no `__rejected__` key and no rejection record of any kind, and both sites CLAUDE.md names
# as known-bad -- `ccstcloud.org/volunteer` (serves Pexels/AdobeStock as its hero) and
# `experiencerochestermn.com`'s calendar (a Mayo Civic Center umbrella banner) -- were back
# at the top of today's selection, ready to be re-fetched and re-rejected. So the finding's
# own remedy decayed exactly the way this project's hand-maintained rules always decay: a fix
# applied by hand, to data, in one run, is not a fix.
#
# The ledger is therefore CARRIED, deliberately and permanently: it is a cache of "do not
# re-fetch this", the same argument that keeps the negative geocache and the website->photo
# map. `__meta__` describes ONE run and resets; `__rejected__` describes the WEB and does not.
# Per the 2026-09-17 rule, that decision is stated here in the same edit that adds the key.
REJECT_SEED = {
    # --- added 2026-09-21 ---
    "https://aftonapple.com/":
        "JavaScript SHELL: WebFetch receives page-structure identifiers and GCS script "
        "references only -- no address, hours, prices or image URLs. Same DEAD-ROUTE class as "
        "the MN DNR /state_parks/ stubs (CLAUDE.md 2026-09-14), so NOT a retry case: no number "
        "of attempts changes what WebFetch can read. That makes it a property of the PAGE (a "
        "ledger entry) rather than a `None` meaning 'no photo found today', which is the "
        "distinction the 2026-09-18 deprioritise-never-exclude rule turns on. Verified live "
        "2026-09-21 while sourcing the Afton Apple Orchard seed; logged in _findings.json as "
        "`aftonapple_js_shell`.",
    "https://www.ccstcloud.org/volunteer":
        "hero + body images are licensed Pexels/AdobeStock stock, not photos of the venue "
        "(CLAUDE.md 2026-09-15); accepting would launder stock into site_photo, which is in "
        "REAL_PHOTO_SOURCES and never self-heals",
    "https://www.experiencerochestermn.com/things-to-do/events-calendar/":
        "returns a Mayo Civic Center umbrella banner that would be stamped onto unrelated "
        "events; SKILL.md forbids an aggregator banner (CLAUDE.md 2026-09-15)",
    "https://thriftyminnesota.com/indoor-playgrounds-in-minnesota/":
        "aggregator listicle, not a venue page -- any hero here is an aggregator banner",
    "https://carshowscalendar.org/car-show-calendar-2026-listings-for-nd-sd-and-mn/":
        "aggregator listing page, not a venue page",
}


def load_rejected():
    """The carried do-not-fetch ledger, seeded with CLAUDE.md's recorded rejections."""
    rej = dict(REJECT_SEED)
    try:
        stored = json.load(open(RESULTS)).get("__rejected__") or {}
        if isinstance(stored, dict):
            rej.update(stored)
    except Exception:
        pass
    return rej


def load_seen():
    """Sites already RESOLVED by an earlier run: {site: True if it yielded a photo}.

    2026-09-18: `do_select` ranked purely by row count and consulted nothing but the row gate,
    so it re-offered sites the cache had already answered -- 26 of one run's 40 selections were
    already in `_step45_results.json`, 22 of them recorded as `None` ("no usable photo").  The
    WebFetch budget was therefore spent re-deriving what was on disk, which is the `geo0826.py`
    lesson arriving through the ACCEPTED half of the cache rather than the rejected half that
    `__rejected__` closes.

    Deprioritised, NOT excluded, and the distinction is the whole point.  A `None` here is a
    NEGATIVE CACHE, and CLAUDE.md already records where a negative cache that never retries does
    harm (the geocoder's).  A site with no photo today may publish one next month, so hard-
    excluding it rebuilds the one-way ratchet `image_upgrades.py` had to be rescued from.
    Ranking unseen sites first spends each run's budget on genuinely new ground while leaving
    every previously-empty site reachable once the new ground runs out.
    """
    try:
        res = json.load(open(RESULTS))
    except Exception:
        return {}
    return {k: bool(v) for k, v in res.items() if not k.startswith("__")}


# A PER-EVENT CALENDAR PERMALINK, deprioritised below every ordinary site (found 2026-09-22).
#
# The 2026-09-18 `load_seen()` fix works exactly as designed, and its consequence is this: with
# already-answered sites pushed to the back, the front of the queue became an inexhaustible
# tail of permanently-UNSEEN per-event permalinks.  Measured this run -- 4002 eligible distinct
# sites, of which 3426 (86%) are one-row calendar permalinks and only 576 are ordinary site
# URLs.  Both classes are overwhelmingly 1-row, so `-len(rows)` cannot separate them and the
# tiebreak fell through to the URL string: the pass was selecting BY ALPHABET, which is why a
# `--select 40` returned 39 consecutive `anokacounty.libcal.com/event/<id>` links.
#
# This is the SELECTION defect class CLAUDE.md 2026-09-18 names -- a pass whose budget is time
# rather than rows, failing in a way no count-based check can see.  Every count looked healthy;
# `stop_reason: deadline` read as honest budget pressure rather than self-inflicted waste.
#
# The expected yield is ~0 and the RISK is not zero, which is what makes this worth an edit
# rather than a note.  Three hosts were fetched and read before this pattern was written:
#   anokacounty.libcal.com/event/17056660 -- a site-wide `LibCal-HEADER-...-sep-2026.png`
#       promotional banner plus `Storytime--200.png` clip art;
#   sppl.bibliocommons.com/events/6a4aac65... -- the SPPL logo, nothing else;
#   events.griver.org/event/17308105 -- `lcimages.../feat_img/6187/TEMPLATE/1683817551.jpg`,
#       whose own asset path names it a template image.
# All three are "addressed by the TEMPLATE, not by the page" (CLAUDE.md 2026-09-18, CivicPlus
# carousel).  Accepting one would launder a library-system banner into `site_photo`, which sits
# in REAL_PHOTO_SOURCES and never self-heals.
#
# DEPRIORITISED, NOT EXCLUDED, and NOT put in `__rejected__` -- the same distinction
# `load_seen()` turns on.  The ledger keys on an exact URL and event ids never repeat, so it
# could never accumulate knowledge about this class anyway; and a class-wide hard exclusion is
# the one-way ratchet `image_upgrades.py` had to be rescued from.  Ranked last, the permalinks
# stay reachable once the ~576 real sites run out (~14 runs at 40/run).
#
# ANCHORED ON THE PATH SHAPE, NEVER ON THE HOST.  The first draft matched `libcal.com/event/`
# and `bibliocommons.com/events/` and LEAKED 321 urls, 320 of them `events.griver.org` -- Great
# River Regional Library runs LibCal on its OWN domain.  That is the vocabulary-gap class this
# project keeps re-finding: a gap in a pattern looks exactly like nothing to catch.  Measured
# before the edit (`_permalink_fp.py` / `_permalink_fp2.py`, CLAUDE.md 2026-09-07): widening to
# the path shape caught 321 more and lost 0, and the newly-caught set is 320 griver + 1
# facebook.com event permalink, with ZERO real venue sites in it.
#
# Deliberately does NOT catch SLUG-based event urls (`visitbemidji.com/event/conversing-in-
# music/`, 79 of them).  Those sit on CVB and venue domains, some are real venue pages, and the
# existing acceptance rules already handle the aggregator-banner half.  Sweeping them in on a
# guess is the wrong-merge asymmetry in selection form: a missed deprioritisation costs one
# WebFetch, hiding a real venue page costs a photo that never arrives.
EVENT_PERMALINK = re.compile(
    r"^https?://[^/]+/events?/(?:\d{5,}|[0-9a-f]{16,})(?:[/?#]|$)", re.I)

# A SIXTH URL SHAPE, and the THIRD instance of the vocabulary-gap class inside this one finding:
# a per-event permalink can be a QUERY STRING rather than a path segment.  CivicPlus serves
# `Calendar.aspx?EID=<id>` and WordPress My Calendar serves `<slug>/?mc_id=<id>`, both of which
# the path-anchored pattern above is structurally blind to -- so deprioritising the path class
# did not fix the queue, it handed the front of it to the next class: the post-fix `--select 40`
# returned 40 consecutive `burnsvillemn.gov/Calendar.aspx?EID=` links.  The alphabet tiebreak
# was never the disease; it was the symptom of a discriminator that did not discriminate.
#
# Measured before the edit, on this run's own data: 80 hits across 5 hosts (burnsvillemn.gov 62,
# krls.org 7, lakevillemn.gov 5, richfieldmn.gov 4, southstpaulmn.gov 2), and ZERO hits covering
# more than one row -- the FP tell for a permalink pattern stays silent, as a true 1:1 per-event
# url must.  Two INDEPENDENT CivicPlus cities were fetched and read first:
#   burnsvillemn.gov/Calendar.aspx?EID=22216 -- homepage logo, search/news/permits/jobs icons
#       and their hover variants, footer logo, share icons.  No venue or event image at all.
#   lakevillemn.gov/Calendar.aspx?EID=14921 -- logos, social icons, slideshow nav arrows, the
#       Google Translate icon.  No photograph of the venue or the event.
# Both are "addressed by the TEMPLATE, not by the page."  Note the contrast that keeps this
# narrow: CLAUDE.md 2026-09-18 ACCEPTED a CivicPlus body photo (Maple Grove `documentId=9075`,
# alt "Crowd at Town Green with musicians") -- but that is a VENUE page, not a per-event
# `Calendar.aspx?EID=` page, and CivicPlus venue pages keep normal priority here.
#
# The id is the evidence; the slug is not.  So `krls.org/mc-events/<slug>/?mc_id=1124` is
# demoted while the same page without the occurrence id is not -- deliberately asymmetric, and
# the same call as leaving the 79 slug-based CVB event pages alone.  `ci.bemidji.mn.us/?SEC=
# <guid>` is likewise left at normal priority: a non-numeric query id on a single site is not
# enough shape to anchor on, and it is one site's homepage, not a per-event url.
EVENT_PERMALINK_Q = re.compile(r"[?&](?:eid|mc_id)=\d+\b", re.I)

# A SEVENTH AND EIGHTH SHAPE (added 2026-09-30), both of which put the id in a LATER path
# segment, where the two anchored patterns above are structurally blind to it.  Both were named
# as known gaps by the 2026-09-29 run and neither was closed then because that run had no
# measurement; this run has one, and one of them turned into 20 of 40 selection slots.
#
#   (a) `espn.com/<league>/game/_/gameId/<id>/<slug>` -- 39 eligible sites, ALL on www.espn.com.
#       These are NEW THIS RUN as a population: the season-type fix took ESPN rows 19 -> 39, so
#       a shape that was a nuisance on 2026-09-29 became the FRONT OF THE QUEUE on 2026-09-30 --
#       a `--select 40` returned 20 espn game links.  This is the alphabet-tiebreak symptom
#       again, reached from a new direction: the discriminator did not discriminate, and a
#       source improvement upstream is what exposed it.  ESPN is also a host CLAUDE.md already
#       records as 403-ing WebFetch, so every one of those slots was a guaranteed zero.
#   (b) `<host>/event/<slug>/<id>/` -- 7 eligible sites (experiencerochestermn.com 6,
#       exploreminnesota.com 1).  The exploreminnesota hit is the persuasive one: it is ALREADY
#       in the carried `__rejected__` ledger, and the previous run's own reject note says of it
#       "Also note it carries a TRAILING NUMERIC ID and still scored permalink=False."  A reject
#       note that names the gap is a measurement the next run should not have to re-derive.
#
# MEASURED BEFORE THE EDIT, on this run's data, the same two tests the query-string shape got:
# 39 and 7 hits, and ZERO hits covering more than one row in either class -- the FP tell for a
# permalink pattern stays silent, as a true 1:1 per-event url must.  The digit floor is `{5,}`
# rather than `{4,}` to keep a `/event/<slug>/2026/` YEAR segment out by construction; measured,
# 0 eligible sites have a 4-digit-only trailing segment, so the floor costs nothing today and
# forecloses the one false friend this shape has.
#
# DEPRIORITISED, NOT EXCLUDED, and NOT written to `__rejected__` -- same call as the two shapes
# above, and for the same reason: the ledger keys on an exact URL and game/event ids never
# repeat, so it could never accumulate knowledge about the class, while a class-wide hard
# exclusion is the one-way ratchet `image_upgrades.py` had to be rescued from.
EVENT_PERMALINK_GAME = re.compile(r"^https?://[^/]+/[^/]*/game/_/gameid/\d{5,}", re.I)
EVENT_PERMALINK_TRAIL = re.compile(
    r"^https?://[^/]+/events?/[^/?#]+/\d{5,}/?(?:[?#]|$)", re.I)


def is_event_permalink(url):
    u = url or ""
    return bool(EVENT_PERMALINK.match(u) or EVENT_PERMALINK_Q.search(u)
                or EVENT_PERMALINK_GAME.match(u) or EVENT_PERMALINK_TRAIL.match(u))


def do_select(n):
    d = load_work()
    rejected = load_rejected()
    seen = load_seen()
    by_site = {}
    for cat, r, w in eligible_rows(d):
        by_site.setdefault(w, []).append(r.get("title"))
    skipped = [w for w in by_site if w in rejected]
    for w in skipped:
        by_site.pop(w)
    # Ordinary sites before per-event permalinks; then unseen first, then most rows, then name
    # -- deterministic and re-runnable.  The permalink test outranks `seen` because it is a
    # property of the URL CLASS (like the ledger), while `seen` is a property of the moment.
    ranked = sorted(by_site.items(),
                    key=lambda kv: (is_event_permalink(kv[0]), kv[0] in seen,
                                    -len(kv[1]), kv[0]))
    out = [{"website": w, "rows": len(t), "sample_titles": t[:3],
            "cached": w in seen,
            "permalink": is_event_permalink(w)} for w, t in ranked[:n]]
    n_cached = sum(1 for o in out if o["cached"])
    n_perma = sum(1 for w in by_site if is_event_permalink(w))
    json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "eligible_rows": sum(len(v) for v in by_site.values()),
               "eligible_sites": len(by_site),
               "permalink_sites_deprioritised": n_perma,
               "real_sites_available": len(by_site) - n_perma,
               "already_resolved_sites": len(seen),
               "selected_already_cached": n_cached,
               "selected_permalinks": sum(1 for o in out if o["permalink"]),
               "skipped_known_bad": {w: rejected[w] for w in skipped},
               "selected": out}, open(CAND, "w"), indent=1)
    print(f"eligible rows        : {sum(len(v) for v in by_site.values())}")
    print(f"eligible DISTINCT sites: {len(by_site)}")
    # Reported, not merely applied -- a deprioritisation nobody reads decays into one nobody
    # can justify, the same reason `--select` prints the known-bad ledger with its reasons.
    print(f"per-event permalinks deprioritised: {n_perma}  "
          f"(real sites still ahead of them: {len(by_site) - n_perma})")
    print(f"known-bad sites skipped: {len(skipped)}  (carried ledger: {len(rejected)})")
    for w in skipped:
        print(f"   SKIP {w}\n        {rejected[w]}")
    print(f"already resolved in cache: {len(seen)} sites "
          f"({sum(1 for v in seen.values() if v)} with a photo, "
          f"{sum(1 for v in seen.values() if not v)} recorded as none)")
    print(f"selected top          : {len(out)}  (covering {sum(o['rows'] for o in out)} rows; "
          f"{n_cached} already cached -- do NOT re-fetch those)")
    print(f"wrote {CAND}")
    for o in out:
        print(f"   {o['rows']:4}  {'[cached] ' if o['cached'] else '          '}{o['website']}")


def do_apply():
    """Apply fetched images. `_step45_results.json` maps website -> image URL or null.

    A null means the fetch happened and yielded no usable photo. That is a RESULT, not a
    failure, and it still counts toward `attempted` -- otherwise the marker would overstate
    convergence by only counting the wins.
    """
    if not os.path.exists(RESULTS):
        raise SystemExit(f"STEP 4.5: {RESULTS} missing -- run the WebFetch phase first")
    res = json.load(open(RESULTS))
    meta = res.pop("__meta__", {}) if isinstance(res, dict) else {}
    # `__rejected__` is a LEDGER, not a site entry. Popping it here is load-bearing twice
    # over: left in, it would be iterated as a website whose "image" is a dict, and it would
    # inflate `attempted` -- overstating the marker exactly the way the module docstring says
    # counting only the wins would understate it.
    ledger = res.pop("__rejected__", {}) if isinstance(res, dict) else {}
    if not isinstance(ledger, dict):
        ledger = {}
    stop_reason = (meta.get("stop_reason") or "").strip()
    if stop_reason not in ("completed", "deadline"):
        raise SystemExit(
            f"STEP 4.5: stop_reason={stop_reason!r} is not one of 'completed'/'deadline'. "
            "This value is asserted by errlog_step7.py and distinguishes a budget-starved "
            "pass from a converged one; it must not be guessed.")

    # RUN_DATE ASSERTION (added 2026-09-16) -- the second half of the `__meta__` fix, and the
    # half that has teeth. `do_dnr()` now DROPS `__meta__`, which stops the stale value being
    # inherited; this stops a stale value being SUPPLIED. CLAUDE.md, 2026-09-15: "`run_date`
    # inside a run-scoped marker is now the cheap tell. A marker whose own `run_date` disagrees
    # with `argv[1]` is stale no matter what its mtime says."
    #
    # It is checked against MSP_TODAY, not against a default, because this project's standing
    # rule is that a value which must come from STEP 1 has its ABSENCE made a crash rather than
    # a default -- the same treatment `fetch_feeds.py`'s window and `errlog_step7.py`'s argv[1]
    # already get. A date a helper can guess is a date it will guess wrong.
    today = (os.environ.get("MSP_TODAY") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", today):
        raise SystemExit(
            f"STEP 4.5: env MSP_TODAY must be set to YYYY-MM-DD (got {today!r}). It is the "
            "run date from STEP 1 and is asserted against the results file's own run_date.")
    run_date = (meta.get("run_date") or "").strip()
    if run_date != today:
        raise SystemExit(
            f"STEP 4.5: _step45_results.json __meta__.run_date={run_date!r} != MSP_TODAY="
            f"{today!r}. The results file's metadata is from another run -- the site->photo "
            "CACHE may legitimately carry forward, but `stop_reason` and `run_date` describe "
            "ONE run and must be re-stamped by this run's WebFetch phase.")

    d = load_work()
    attempted = len(res)
    rejected_logo, upgraded, warm, per_site = 0, 0, 0, []

    for site, img in res.items():
        if img and not is_usable_image(img):
            rejected_logo += 1
            img = None
        if not img:
            per_site.append((site, 0, "no usable photo"))
            continue
        # IDEMPOTENT, and the marker is the reason it has to be. Applying the photo moves the
        # row's image_source OUT of GATE, so a naive warm re-run finds nothing eligible,
        # reports `upgraded: 0`, and OVERWRITES the marker with that zero -- turning a
        # successful pass into a permanent false claim that STEP 4.5 did nothing. A row
        # already carrying THIS pass's photo therefore still counts. Same standard as
        # closure_filter / entity_fix: a warm re-run must reproduce the cold result.
        n = warm_n = 0
        for cat in CATS:
            for r in d[cat]:
                if (r.get("website") or "").strip() != site:
                    continue
                src = (r.get("image_source") or "").strip()
                if src == "site_photo" and (r.get("image_url") or "").strip() == img:
                    warm_n += 1
                elif src in GATE and (n + warm_n) < MAX_FANOUT:
                    r["image_url"] = img
                    r["image_source"] = "site_photo"
                    n += 1
        warm += warm_n
        upgraded += n + warm_n
        per_site.append((site, n + warm_n, img))

    json.dump(d, open(WORK, "w"), ensure_ascii=False)

    # The description is PROSE, and prose is the one thing no guard in this pipeline asserts,
    # so it must not overstate method. 4.5 resolves images two ways and saying "fetched N
    # pages" would be false for the DNR half, which never fetches a page at all.
    desc = (f"STEP 4.5 site_photo backfill: resolved {attempted} venue sites "
            f"(venue pages via WebFetch; MN DNR state parks via the calendar API's "
            f"location_tag plus a JPEG byte-check, their /state_parks/ URLs being JavaScript "
            f"redirect stubs WebFetch cannot follow); upgraded {upgraded} rows from a generic "
            f"category image to the venue's own photo, of which {warm} were already correct "
            f"from an earlier invocation this run; {rejected_logo} candidate images rejected "
            f"by is_usable_image(), which screens on THREE grounds -- a vector/animation "
            f"extension, an unrecognised extension on a host that is not a known image CDN, "
            f"and a logo/chrome token in the filename -- so this count must be ATTRIBUTED "
            f"before it is read as 'the logo screen did its job' (on 2026-09-22 all 4 were "
            f"the EXTENSION ground and none was a logo). Stopped because: "
            + ("the shared 20-min enrichment budget was reached (the eligible set is ~4.2k "
               "distinct sites and cannot be exhausted in one run)."
               if stop_reason == "deadline" else "the eligible set was exhausted."))

    # `run_date` is carried INTO the marker so the same cheap tell is available one level up:
    # errlog_step7.py can compare it against its own argv[1] without re-deriving anything.
    json.dump({"item": "site_photo_pass", "attempted": attempted, "upgraded": upgraded,
               "rejected_logo": rejected_logo, "stop_reason": stop_reason,
               "run_date": today, "routes": meta.get("routes", ""),
               "description": desc}, open(MARKER, "w"), indent=1)

    print("=" * 74)
    print("STEP 4.5 SITE_PHOTO BACKFILL")
    print("=" * 74)
    for site, n, img in per_site:
        print(f"   {n:4} rows  {site}")
        if n:
            print(f"             -> {img}")
    print(f"\n   attempted (sites resolved): {attempted}")
    print(f"   rows upgraded             : {upgraded}")
    print(f"   rejected by is_usable_image: {rejected_logo}  (ATTRIBUTE THIS -- the screen has "
          f"three grounds and only one is 'logo')")
    print(f"   of which already correct  : {warm}  (warm re-run)")
    print(f"   stop_reason               : {stop_reason}")
    print(f"\nwrote {WORK}")
    print(f"wrote {MARKER}")


def do_dnr():
    """Merge the DNR banner map into `_step45_results.json`.

    Kept as its own phase, and merged rather than written, because the DNR half needs NO
    WebFetch at all -- it is a read-only API call plus an asset byte-check, so it can run
    unattended before or after the hand-fetched half without either clobbering the other.
    An existing entry always wins: a page that was actually fetched and inspected is better
    evidence than a deterministic path, even when the path verifies.
    """
    res = {}
    if os.path.exists(RESULTS):
        res = json.load(open(RESULTS))
    # `__meta__` is DISCARDED here, never merged forward (fixed 2026-09-16).
    #
    # It used to be popped and written back, which made `_image_backfill.json` the fourth
    # instance of this project's stale-inherited-value class -- and the nastiest, because it
    # defeated the very guard built to catch the class. `errlog_step7.py` asserts the marker
    # EXISTS, is FRESH BY MTIME, and carries a LEGAL `stop_reason`; on 2026-09-15 all three
    # passed while `stop_reason` was yesterday's verdict, because the FILE was genuinely new
    # and only a FIELD inside it was carried. Neither content-freshness nor mtime-freshness
    # can see that.
    #
    # The split is per-field, by what the value describes:
    #   site -> photo   CACHE, describes the world. Carries. Re-fetching it would spend the
    #                   enrichment budget rediscovering what is already on disk (the
    #                   `geo0826.py` lesson), so an existing entry still wins over the DNR map.
    #   __meta__        describes ONE RUN -- why it stopped, when, by what route. Cannot carry.
    #                   Dropping it makes a missing value a CRASH in do_apply() rather than a
    #                   silently inherited one: "a value a helper can default is a value it
    #                   will default wrongly."
    # DROPPED ONLY IF STALE, not unconditionally (corrected 2026-09-16, same run).
    #
    # The first cut of this fix popped `__meta__` every time. That closes the stale-inheritance
    # hole, but it opens a worse one: it also destroys a FRESH `__meta__` that THIS run's
    # WebFetch phase just wrote, so `--dnr` after the fetch phase silently deletes the run's own
    # metadata and `do_apply()` then hard-fails. Observed immediately on live data. It made the
    # phase ORDER load-bearing and undocumented -- and "remember to call these in the right
    # order" is exactly the obey-it-perfectly-forever rule this project keeps proving worthless.
    #
    # The test is the value's OWN run_date, which is the cheap tell CLAUDE.md names: yesterday's
    # metadata goes, today's survives, and the phases commute again.
    old = res.pop("__meta__", None)
    today = (os.environ.get("MSP_TODAY") or "").strip()
    fresh = isinstance(old, dict) and (old.get("run_date") or "").strip() == today and today
    if fresh:
        print(f"   __meta__ KEPT (run_date={today} == MSP_TODAY: written by this run)")
    elif old is None:
        print("   __meta__ absent")
    else:
        print(f"   __meta__ DROPPED as stale (run_date={old.get('run_date')!r} != "
              f"MSP_TODAY={today!r}); do_apply needs a fresh stop_reason + run_date")
    before = len(res)
    added = 0
    for site, img in dnr_banner_map().items():
        if site not in res:
            res[site] = img
            added += 1
    if fresh:
        res["__meta__"] = old
    json.dump(res, open(RESULTS, "w"), indent=1)
    print(f"   results: {before} -> {len(res) - (1 if fresh else 0)} entries (+{added} DNR)")


if __name__ == "__main__":
    if "--select" in sys.argv:
        i = sys.argv.index("--select")
        do_select(int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 40)
    elif "--dnr" in sys.argv:
        do_dnr()
    elif "--apply" in sys.argv:
        do_apply()
    else:
        raise SystemExit("usage: step45_site_photo.py --select N | --dnr | --apply")
