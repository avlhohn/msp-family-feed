#!/usr/bin/env python3
"""STEP 8 venue repair: closed-venue drops + hand-adjudicated same-address collapses.

WHY THIS EXISTS
---------------
The 2026-09-06 STEP 8 play-cafe tripwire (`play_cafe_low`) passed at 19 tagged rows, but
reading the 19 TITLES rather than just the count surfaced two defects the whole dedup chain
is structurally blind to:

1. A venue SKILL.md declares permanently closed was carried anyway. MiniSota Play Cafe
   (Maple Grove) closed 2026-04-29; SKILL.md 404 says "do NOT re-add it" and log a
   `dropped_closed_venues` row. Nothing in the pipeline reads that instruction, so the row
   rode the carried base forward. `closure_filter.py` cannot catch it -- that helper reads a
   row's own title for a cancellation notice, and "MiniSota Play Cafe" announces nothing.

2. SAME ADDRESS, DIFFERENT TITLE is the mirror image of the blind spot `dedup_titles.py` was
   written to fix. Every pass in the chain blocks on an exact normalized TITLE and then
   compares place; `dupsweep.py` requires title AND address AND date to match. So one venue
   written up six different ways by six sources never collides. Sovereign Grounds -- a single
   coffeehouse per SKILL.md 407 -- was carrying SEVEN rows.

WHY THIS IS A HAND TABLE AND NOT A RULE
---------------------------------------
Because the automatic version is wrong. Scanning for "same normalized address, differing
titles sharing a distinctive token" over restaurants+parks returned 7 groups, and 2 of them
are FALSE POSITIVES that a rule would have merged:

  * Chipotle Mexican Grill Mankato / Noodles & Company Mankato -- two different chains that
    happen to share a mall address (1600 Warren St).
  * Lake Phalen Beach / Phalen Regional Park -- a beach inside a park; a family searching for
    the beach wants the beach.

CLAUDE.md's standing asymmetry applies with full force here: a missed duplicate is cosmetic,
a wrong merge silently deletes a real venue. So every group below is adjudicated individually
against an EXTERNAL authority (SKILL.md's seed list, or an identical street address, or the
venue's own per-location URL path), never against a similarity score. The two false positives
above are recorded in KEEP_APART so a later reader does not "fix" them.

RED COW IS THE CASE THAT PROVES THE POINT. It has NINE rows and it is a genuine multi-location
chain -- collapsing it on name would be exactly the chain-collapse error CLAUDE.md forbids.
Only two pairs merge, each on evidence that is not the name:
  * 3624 W 50th St appears verbatim on two rows.
  * `Red Cow - St. Paul` (393 Selby Ave) and `Red Cow St. Paul Cathedral Hill` (neighborhood
    only) both resolve to redcowmn.com/st-paul-selby-avenue/ -- the venue's OWN per-location
    URL is the authority, and Selby Ave is in Cathedral Hill.
Uptown, North Loop, Wayzata and Rochester stay as four separate rows.

Survivor selection and field salvage reuse `dupsweep.completeness()` / `merge_into()` rather
than bespoke logic, so this pass cannot drift from the sanctioned merge semantics.
"""
import json, os, re, sys, importlib

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
dsw = importlib.import_module("dupsweep")

CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]

# --- 1. Venues SKILL.md declares permanently closed. Drop, and log dropped_closed_venues. ---
CLOSED = [
    # (matcher on lowercased title, reason)
    ("minisota play cafe", "Permanently closed 2026-04-29 (SKILL.md 404: do NOT re-add)"),
]

# --- 2. Hand-adjudicated single-venue groups. Each entry:
#        (label, canonical_title, canonical_address, [predicates], evidence)
#    A row joins the group only if a predicate matches. Predicates are (title_substr, addr_substr)
#    with addr_substr="" meaning "any address" -- used ONLY where the title alone is unambiguous
#    for a single-location venue.
#
#    Two optional keys, both added 2026-09-14 for urban_air_coon_rapids:
#
#      route="<category>"   The survivor is MOVED into this category after the merge. Required
#                           whenever a group spans categories, because the survivor is chosen by
#                           dupsweep.completeness() and completeness knows nothing about routing
#                           -- so without this the merged row lands in whichever category the
#                           richest row happened to sit in, which is a heuristic. CLAUDE.md is
#                           explicit that a cross-category merge must follow SKILL.md's DECLARED
#                           route for that venue; `route` is where that declaration is recorded,
#                           and the evidence string must cite the SKILL.md line.
#
#      force_recoord=True   Blank lat/lon even when the survivor's address already normalizes to
#                           the canonical one. The default test (survivor address changed =>
#                           re-geocode) assumes the survivor's pin was derived from its own
#                           address and is therefore right when the address is right. That
#                           assumption fails when the group's members carry MUTUALLY
#                           INCONSISTENT coordinates for one address: at most one of them can be
#                           correct, and completeness() does not rank pins. Blanking is the safe
#                           side -- STEP 4.9 skips populated coordinates, so a wrong pin kept
#                           here never self-heals on any later run.
GROUPS = [
    dict(
        label="sovereign_grounds",
        title="Sovereign Grounds",
        address="813 E 48th St, Minneapolis, MN 55417",
        match=[("sovereign grounds", "")],
        evidence="SKILL.md 407 declares ONE Sovereign Grounds at 813 E 48th St. Four of the "
                 "seven rows carry that street address verbatim; two carry no street address; "
                 "one carries 2400 Third Avenue South sourced from a minnesotaparent.com "
                 "listicle (a third-party roundup in the `website` field, not the venue site) "
                 "-- the wrong-address-but-plausible-website defect class. Seed address wins.",
    ),
    dict(
        label="littles_and_lattes",
        title="Littles and Lattes Play Cafe",
        address="15670 Edgewood Dr, Suite 120, Baxter, MN 56425",
        match=[("littles and lattes", "")],
        evidence="SKILL.md 416 declares one venue at 15670 Edgewood Dr Suite 120, Baxter. Both "
                 "rows carry that address; they differ only by 'Suite 120' vs 'Ste 120'. "
                 "dupsweep.na() maps 'ste'->'st' but leaves 'suite' alone, so the two normalize "
                 "differently and never collide -- see the suite-designator note in the report.",
    ),
    dict(
        label="angel_food_bakery",
        title="Angel Food Bakery",
        address="701 Mainstreet, Hopkins, MN 55343",
        match=[("angel food bakery", "")],
        evidence="Identical street address (701 Mainstreet, Hopkins) and identical website "
                 "angelfoodmn.com/hopkins. The second title is the same venue carrying a "
                 "former-name parenthetical ('formerly Amy's Cupcake Shoppe'), not a second shop.",
    ),
    dict(
        label="brasa_grand_ave",
        title="Brasa Premium Rotisserie",
        address="777 Grand Ave, St Paul, MN 55105",
        match=[("brasa", "777 grand"), ("brasa premium rotisserie", "__blank__")],
        evidence="Two rows carry 777 Grand Ave verbatim (differing only by 'St Paul' vs "
                 "'St. Paul'). The third has a BLANK address and a title exactly equal to one "
                 "of them; Brasa is multi-location, so a blank-address stub cannot be pinned to "
                 "any location and folding it removes an unlocatable row rather than a venue.",
    ),
    dict(
        label="red_cow_50th",
        title="Red Cow - 50th & France",
        address="3624 W 50th St, Minneapolis, MN 55410",
        match=[("red cow", "3624 w 50th")],
        evidence="Both rows carry 3624 W 50th St verbatim. Merging on ADDRESS, not on the "
                 "'Red Cow' name -- Red Cow is a real multi-location chain and the other four "
                 "locations stay separate.",
    ),
    dict(
        label="red_cow_selby",
        title="Red Cow - St. Paul",
        address="393 Selby Ave, St. Paul, MN 55102",
        match=[("red cow", "393 selby"), ("red cow st. paul cathedral hill", ""),
               ("red cow st paul cathedral hill", "")],
        evidence="Both resolve to the venue's OWN per-location URL redcowmn.com/"
                 "st-paul-selby-avenue/. One row carries the street address, the other only the "
                 "neighborhood ('Cathedral Hill'), and Selby Ave is in Cathedral Hill. The "
                 "per-location URL is the authority here, not the title.",
    ),
    dict(
        label="st_paul_tap",
        title="St. Paul Tap",
        address="825 Jefferson Ave, St Paul, MN 55102",
        match=[("paul tap", "825 jefferson")],
        evidence="Both rows carry 825 Jefferson Ave verbatim; the longer title is the venue's "
                 "full trade name ('Sports Bar & Gaming Co').",
    ),
    # --- added 2026-09-08, from reading the play-cafe TITLES (the count-only tripwire passed) ---
    dict(
        label="peak_cafe_edinborough",
        title="Peak Café",
        address="7700 York Ave S, Edina, MN 55435",
        match=[("peak caf", "")],
        evidence="Three restaurants rows, ONE cafe. Merging on the fact that all three name "
                 "Edinborough Park -- a single municipal facility at 7700 York Ave S -- not on "
                 "the 'Peak' token, which also appears in the separate Adventure Peak ATTRACTION "
                 "rows that are deliberately left alone. The predicate is 'peak caf', which does "
                 "not match 'Adventure Peak at Edinborough Park'; verified against the whole "
                 "dataset before adding (3 hits, exactly the intended rows). "
                 "The third row is a WRONG-CITY defect, not a second location: 'Peak Cafe "
                 "Adventure Peak - White Bear Lake' carries the address 'Edinborough Park, White "
                 "Bear Lake, MN' -- the address string names Edinborough Park, which is in EDINA, "
                 "~30 km from White Bear Lake. There is no Peak Cafe in White Bear Lake. The "
                 "canonical address therefore also repairs the bad city, and because the survivor "
                 "address differs the lat/lon is blanked and re-geocoded rather than left pinned "
                 "to the wrong town.",
    ),
    dict(
        label="edinborough_playpark",
        title="Edinborough Park PlayPark",
        address="7700 York Ave S, Edina, MN 55435",
        match=[("playpark", "")],
        evidence="Both rows carry 7700 York Ave S verbatim (differing only by ZIP placement) AND "
                 "both resolve to the city's own page path edinamn.gov/.../PlayPark. Merging on "
                 "the address + the venue's own per-location URL, the Red Cow Selby standard -- "
                 "not on the name. "
                 "'Adventure Peak at Edinborough Park' is NOT in this group: different attraction "
                 "name, different city page (/1841/Edinborough-Park), and the Lake Phalen Beach "
                 "precedent says an attraction inside a facility stays its own destination.",
    ),
    dict(
        label="rebes_play_cafe",
        title="Rebe's Play Cafe",
        address="2054 St Clair Ave, St. Paul, MN 55105",
        match=[("rebe's play cafe", "2054 st clair"), ("rebe's play cafe", "minneapolis")],
        evidence="Two restaurants rows, identical title, both carrying the venue's OWN website "
                 "rebesplaycafe.com at the ROOT with no per-location path -- a single-location "
                 "business, which is what distinguishes this from the Red Cow chain case. The "
                 "second row's 'address' is not an address: it is the venue NAME plus a city "
                 "(\"Rebe's Play Cafe, Minneapolis, MN\") with a downtown-Minneapolis "
                 "city-centroid pin ~9 km from the real St Clair Ave door. Same shape as "
                 "Sovereign Grounds. "
                 "The predicate is deliberately ADDRESS-QUALIFIED rather than a bare title "
                 "match: a bare match would also catch the meal_deals row \"Rebe's Play Cafe - "
                 "Playtime with Food\" and perform a CROSS-CATEGORY merge on a heuristic, which "
                 "CLAUDE.md forbids -- a cross-category move must follow SKILL.md's declared "
                 "route for the venue. That row has a blank address and is left alone.",
    ),
    dict(
        label="kids_empire_bloomington",
        title="Kids Empire - Bloomington",
        address="10590 France Ave S, Bloomington, MN 55431",
        match=[("kids empire", "")],
        evidence="Two rows whose GEOCODED COORDINATES agree to 4 decimal places "
                 "(44.8322/-93.3204 vs 44.8322/-93.3205, i.e. the same point) -- that is the "
                 "evidence, not the shared name. One row carries only 'Bloomington, MN' and a "
                 "thriftyminnesota.com listicle URL; the other supplies the real street address "
                 "it lacks. Kids Empire is a national chain, so the predicate is safe here ONLY "
                 "because Bloomington is currently its single Minnesota location -- if a second "
                 "MN location appears, this entry must gain an address qualifier or it becomes "
                 "the chain-collapse error.",
    ),
    # --- added 2026-09-14, from the wide play-cafe/indoor-attraction title probe ---
    dict(
        label="urban_air_coon_rapids",
        title="Urban Air Adventure Park - Coon Rapids",
        address="10 Coon Rapids Boulevard NW, Coon Rapids, MN 55448",
        match=[("urban air", "coon rapids")],
        route="events",
        force_recoord=True,
        evidence="THREE rows for one trampoline park, and the merge is on two kinds of evidence "
                 "that are NOT the name -- which matters more here than anywhere else in this "
                 "table, because Urban Air is a genuine multi-location chain (SKILL.md 791: "
                 "'3 metro locations, verify per-location each run') and a name match would be "
                 "the chain-collapse error. (a) The two `events` rows both resolve to the "
                 "venue's OWN per-location URL urbanair.com/minnesota-coon-rapids (one with a "
                 "trailing slash) -- the Red Cow Selby standard. (b) The `restaurants` row's "
                 "website is the BARE urbanair.com root, so the URL ties it to nothing; it joins "
                 "on COORDINATES agreeing to 4 dp with the second events row "
                 "(45.172892/-93.30239 vs 45.1728923/-93.3023898) -- the Kids Empire standard. "
                 "Apple Valley and Plymouth carry their own per-location URLs and their own "
                 "addresses and stay separate rows; the predicate is address-qualified on "
                 "'coon rapids' so it cannot reach them (verified: 3 hits, exactly the "
                 "intended rows). "
                 "ROUTE: the third row sits in `restaurants` and is mis-routed. SKILL.md 788 "
                 "declares 'Must-include indoor adventure & trampoline parks ... Route to "
                 "`events` as a standing/recurring attraction', so the cross-category move "
                 "follows a DECLARED route, not a heuristic -- which is the only form CLAUDE.md "
                 "permits. It is also why this entry carries route= rather than letting "
                 "completeness() decide the category. "
                 "ADDRESS: taken from the venue's own page, which states '10 Coon Rapids "
                 "Boulevard, Coon Rapids, Minnesota 55448' (verified by WebFetch this run). "
                 "Note SKILL.md 791's seed line carries ZIP 55433, which the venue page "
                 "contradicts; the venue's own page wins, per the wrong-address remedy. The NW "
                 "directional is kept because the seed row and SKILL.md 791 both carry it and "
                 "the page does not contradict it. "
                 "COORDINATES: force_recoord, because the three rows carry three MUTUALLY "
                 "INCONSISTENT pins (45.1733/-93.2750 vs 45.1729/-93.3024, ~2 km apart) and "
                 "SKILL.md 791 asserts a fourth (45.13429/-93.26869) that matches none of them. "
                 "At most one can be right and nothing here ranks them, so all are discarded and "
                 "STEP 4.9 re-derives the pin from the verified address.",
    ),
    # --- added 2026-09-21, from the MISSING-SEED stem probe (`afton`) ---
    dict(
        label="afton_apple_fall_festival",
        title="Afton Apple Fall Festival",
        address="14421 90th St S, Hastings, MN 55033",
        match=[("afton apple festival", ""), ("afton apple fall festival", "")],
        force_recoord=True,
        evidence="THREE rows for ONE festival, all dated 2026-09-26, and nothing in the dedup "
                 "chain can see them: dedup_titles blocks on an exact normalized title and "
                 "neither of its two safe rules (city_suffix, reordered) reaches "
                 "'Afton Apple Festival' <-> 'Afton Apple Fall Festival', while dupsweep keys on "
                 "title AND address AND date, so the differing titles defeat it before the "
                 "address is ever compared. Same-date/same-place/different-phrasing is the exact "
                 "blind spot dedup_titles was built for and the one case its safe rules miss. "
                 "EVIDENCE THAT IS NOT THE NAME: rows 1 and 2 carry the street address "
                 "'14421 90th St S, Hastings, MN 55033' VERBATIM (and it is the address SKILL.md "
                 "758 declares for Afton Apple Orchard) and both resolve to aftonapple.com. "
                 "Row 3 ('Afton Apple Festival Weekends') carries NO street address -- only "
                 "'Afton, MN' with that city's centroid pin, which is centroid_circular and can "
                 "never be evidence. It joins on the SOVEREIGN GROUNDS standard instead: "
                 "SKILL.md 758 declares exactly ONE Afton Apple, a single 190-acre farm, so a "
                 "title match carries no chain-collapse risk and the seed address wins. Note the "
                 "row's city token is WRONG (the orchard is in Denmark Township/Hastings, not in "
                 "the city of Afton) -- the Peak Cafe / White Bear Lake shape, where a bare city "
                 "string reads as a second location and is not one. Predicate verified on live "
                 "data: 3 hits, exactly the intended rows. "
                 "IT MUST NOT REACH THE SEED ROW. Afton Apple Orchard is emitted this run as a "
                 "STANDING seasonal attraction with a BLANK date (SKILL.md 757's declared route); "
                 "the festival is a dated event. CLAUDE.md forbids merging rows that differ in "
                 "`date` absent a source stating a span, and collapsing a standing venue into a "
                 "one-day row would destroy whichever of the two the survivor did not keep. Both "
                 "predicates therefore require the word 'festival' -- neither is a substring of "
                 "'afton apple orchard' (asserted, not assumed) -- and the pair is recorded in "
                 "KEEP_APART. Two predicates rather than one because 'afton apple festival' is "
                 "NOT a substring of 'afton apple fall festival'. "
                 "COORDINATES: force_recoord. The three rows carry three MUTUALLY INCONSISTENT "
                 "pins (44.8316/-92.8342, 44.7427/-92.8519, 44.902841/-92.783232 -- the outer "
                 "two ~18 km apart) and SKILL.md 758 asserts a fourth (44.81882/-92.81918) "
                 "matching none. At most one can be right, completeness() does not rank pins, "
                 "and STEP 4.9 skips populated coordinates -- so a wrong pin kept here never "
                 "self-heals. All are discarded and re-derived from the verified address.",
    ),
]

# Deliberately NOT merged -- recorded so a later pass does not 'fix' them.
KEEP_APART = [
    # --- added 2026-09-21 ---
    ("Afton Apple Orchard (seed, blank date) / Afton Apple Fall Festival (2026-09-26)",
     "Same venue, same address, DELIBERATELY two rows. SKILL.md 757 routes an in-season orchard "
     "to `events` as a standing seasonal attraction with a blank date AND wants the festival "
     "dates in `description`; the festival rows are a dated occurrence. Merging them would "
     "either age the standing venue out with the festival or strip the festival's date, and "
     "CLAUDE.md forbids merging rows differing in `date` absent a stated span. The "
     "afton_apple_fall_festival predicates are word-'festival'-qualified so they cannot reach "
     "the seed."),
    ("Joyer Adventure Farm at Waldoch Farm / Waldoch Farm & Garden Center",
     "Only ONE row exists (the seed emitted 2026-09-21); recorded pre-emptively because the "
     "venue trades under two names in its own materials and a future garden-centre row is a "
     "legitimate separate listing, not a duplicate, unless it carries 8174 Lake Dr verbatim."),
    ("Chipotle Mexican Grill Mankato / Noodles & Company Mankato @ 1600 Warren St, Mankato",
     "Two different restaurant chains sharing one mall address. A same-address rule merges these."),
    ("Lake Phalen Beach / Phalen Regional Park @ 1600 Phalen Dr, St Paul",
     "A beach inside a regional park. Distinct destinations; a family searching the beach wants the beach."),
    ("Red Cow (address 'Multiple Twin Cities locations')",
     "Chain-level seed stub naming no location. Duplicates no specific row and is an is_seed row, "
     "so it is left alone rather than dropped on inference."),
    ("Red Cow Uptown / North Loop / Wayzata / Rochester",
     "Four genuinely distinct locations of one chain, each with its own street address or "
     "per-location URL. Collapsing them is the chain-collapse error."),
    # --- added 2026-09-08 alongside the three new Edinborough/Kids Empire groups ---
    ("Adventure Peak at Edinborough Park / Edinborough Park PlayPark / Edinborough Park",
     "Three rows at 7700 York Ave S that are NOT one row: the park itself, and two distinct "
     "attractions inside it with separate edinamn.gov pages. Same address is not same "
     "destination -- this is the Lake Phalen Beach case, and a same-address rule merges them."),
    ("Edinborough Park - Indoor Playground (exploreminnesota.com listicle stub)",
     "REVIEW, not merged. It has no street address and no coordinates, and its title does not "
     "say WHICH of the two indoor attractions it means (PlayPark or Adventure Peak). Folding it "
     "into either one asserts a fact the source does not state; folding it into the park row "
     "loses the distinction the other two rows are keeping."),
    ("Good Times Park Eagan / Good Times Park - Indoor Playground (Saint Paul)",
     "REVIEW, not merged. The Eagan row has a real suite address; the other has only 'Saint "
     "Paul, MN' with a CITY-CENTROID pin ~15 km away and a minnesotaparent.com listicle URL. "
     "The coordinate test that justified merging Kids Empire FAILS here, so there is no "
     "evidence beyond the name -- and a real second location cannot be ruled out. A missed "
     "duplicate is cosmetic; a wrong merge deletes a real venue."),
    # --- added 2026-09-14, the rejected half of the Urban Air / Sky Zone adjudication ---
    ("Urban Air Trampoline Park - Apple Valley / - Plymouth",
     "Two further locations of the same chain whose Coon Rapids rows DO merge above. Each "
     "carries its own per-location URL (minnesota-apple-valley/, minnesota-plymouth/) and its "
     "own pin. Recorded here because the merge entry sitting directly above is an invitation to "
     "'finish the job' on the chain, which is the chain-collapse error."),
    ("Sky Zone - Oakdale / Sky Zone Trampoline Park - Little Leapers (multiple locations) / "
     "Sky Zone Trampoline Park",
     "Three seed rows, NO merge -- there is no evidence that is not the name. They share no "
     "street address (595 Hale Ave N / 'Twin Cities, MN' / 'Minnesota'), no per-location URL "
     "(skyzone.com/oakdale / a familyfuntwincities.com roundup / the skyzonetrampoline.com "
     "root), and no coordinates within any distance of each other. CLAUDE.md names Sky Zone "
     "explicitly as a chain whose variants must not be collapsed onto one coordinate. "
     "'Little Leapers' is additionally a PROGRAM offered across locations, not a location."),
    ("Sky Zone Trampoline Park @ address 'Minnesota' -- WRONG COORDINATE, not a duplicate",
     "Logged as a data-quality finding rather than repaired here. Its pin (45.989659, "
     "-94.611329) is in central Minnesota near Little Falls, ~100 km from any Sky Zone site. "
     "The cause is upstream of this pass: the 'address' is the bare state name, so whatever "
     "geocoded it had nothing to work with. The fix is an address from the venue's own page "
     "plus a blanked pin, which needs a source this pass does not have -- and merging it into "
     "the Oakdale row to make the bad pin disappear would assert a location the row never "
     "claimed."),
    ("Edinborough Park PlayPark pin (44.8650, -93.3350) vs Adventure Peak / Edinborough Park "
     "(44.864, -93.3215) at the SAME street address -- WRONG COORDINATE, not a duplicate",
     "Three rows agreeing on 7700 York Ave S but one pin sitting ~1 km west of the other two. "
     "The KEEP_APART entry above already settles that these are distinct destinations, so this "
     "is a coordinate defect inside a row that is correctly separate. Logged as a finding; "
     "repairing it means blanking that row's lat/lon for STEP 4.9, which is deliberately NOT "
     "done from inside a merge pass -- this pass only blanks pins on rows it actually merges."),
]


def na(a):
    return dsw.na(a)


def joins(row, spec):
    t = (row.get("title") or "").lower()
    a = na(row.get("address") or "")
    raw_addr = (row.get("address") or "").strip()
    for tsub, asub in spec["match"]:
        if tsub not in t:
            continue
        if asub == "":
            return True
        if asub == "__blank__":
            if not raw_addr:
                return True
            continue
        if asub in a:
            return True
    return False


def main():
    dry = "--dry-run" in sys.argv
    path = os.path.join(ROOT, "_compiled_work.json")
    d = json.load(open(path))
    d.pop("counts", None)

    before = {c: len(d[c]) for c in CATS}
    dropped_closed, merged = [], []

    # --- closed venues ---
    for cat in CATS:
        keep = []
        for r in d[cat]:
            t = (r.get("title") or "").lower()
            hit = next((rsn for m, rsn in CLOSED if m in t), None)
            if hit:
                dropped_closed.append((cat, r.get("title"), r.get("address"), hit))
            else:
                keep.append(r)
        d[cat] = keep

    # --- hand-adjudicated groups ---
    for spec in GROUPS:
        members = [(c, i) for c in CATS for i, r in enumerate(d[c]) if joins(d[c][i], spec)]
        if len(members) < 2:
            merged.append((spec["label"], len(members), [], None, "", False, None))
            continue
        rows = [d[c][i] for c, i in members]
        keep = max(rows, key=dsw.completeness)
        titles = [r.get("title") for r in rows]
        # The survivor is chosen by field completeness, NOT by address correctness, so the
        # richest row can easily be the one carrying the WRONG address -- and its lat/lon was
        # geocoded FROM that wrong address. Sovereign Grounds is exactly this: the 2400 Third
        # Avenue South row is field-rich and its pin sits ~4 km from the real door at 813 E
        # 48th St. Overwriting the address without clearing the coordinate leaves a row whose
        # text and pin disagree, which is the wrong-address-but-plausible-everything-else
        # defect in its most durable form: STEP 4.9 skips populated coordinates, so it would
        # never self-correct on any later run. Blank it and let the geocoder re-derive.
        survivor_addr_was = keep.get("address") or ""
        for r in rows:
            if r is not keep:
                dsw.merge_into(keep, r)
        keep["title"] = spec["title"]
        keep["address"] = spec["address"]
        recoord = spec.get("force_recoord", False) or na(survivor_addr_was) != na(spec["address"])
        if recoord:
            keep["latitude"] = ""
            keep["longitude"] = ""
        drop_ids = {id(r) for r in rows if r is not keep}
        for c in CATS:
            d[c] = [r for r in d[c] if id(r) not in drop_ids]
        # Declared-route move. Only ever runs when the entry names a route, and the route is a
        # SKILL.md citation recorded in `evidence` -- never an inference from the survivor.
        moved_from = None
        route = spec.get("route")
        if route:
            cur = next((c for c in CATS if any(r is keep for r in d[c])), None)
            if cur is None:
                raise SystemExit(f"{spec['label']}: survivor vanished from every category")
            if route not in CATS:
                raise SystemExit(f"{spec['label']}: route={route!r} is not a category")
            if cur != route:
                d[cur] = [r for r in d[cur] if r is not keep]
                d[route].append(keep)
                moved_from = cur
        merged.append((spec["label"], len(rows), titles, spec["title"], survivor_addr_was,
                       recoord, moved_from))

    after = {c: len(d[c]) for c in CATS}

    print("=" * 78)
    print("STEP 8 VENUE REPAIR " + ("(DRY RUN)" if dry else "(APPLIED)"))
    print("=" * 78)
    print("\n-- closed venues dropped (SKILL.md-declared) --")
    for cat, t, a, rsn in dropped_closed:
        print(f"   DROP [{cat}] {t!r} @ {a!r}\n        {rsn}")
    if not dropped_closed:
        print("   (none)")
    print("\n-- same-address / single-venue collapses --")
    for label, n, titles, canon, was, recoord, moved_from in merged:
        if n < 2:
            print(f"   {label:22} {n} row(s) matched -- NO MERGE")
            continue
        print(f"   {label:22} {n} rows -> 1   canonical={canon!r}")
        for t in titles:
            print(f"        - {t}")
        if recoord:
            print(f"        ! survivor address was {was!r} -> lat/lon BLANKED for re-geocode")
        if moved_from:
            print(f"        ! survivor ROUTED {moved_from} -> declared category (SKILL.md route)")
    print("\n-- deliberately NOT merged --")
    for what, why in KEEP_APART:
        print(f"   KEEP {what}\n        {why}")
    print("\n-- counts --")
    tot_b = tot_a = 0
    for c in CATS:
        tot_b += before[c]; tot_a += after[c]
        flag = "" if before[c] == after[c] else f"   ({after[c]-before[c]:+d})"
        print(f"   {c:26} {before[c]:5} -> {after[c]:5}{flag}")
    print(f"   {'TOTAL':26} {tot_b:5} -> {tot_a:5}   ({tot_a-tot_b:+d})")

    if dry:
        print("\nDRY RUN -- nothing written.")
        return
    json.dump(d, open(path, "w"), ensure_ascii=False)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
