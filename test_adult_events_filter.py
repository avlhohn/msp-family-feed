#!/usr/bin/env python3
"""
test_adult_events_filter.py — real observed cases for adult_events_filter.py

Every DROP case is a title seen on the live 2026-08-25 feed. Every KEEP case is a real
family event that a naive keyword filter got wrong (Fiesta Latina, caregiver-attended
storytimes, kids' book clubs). Run after any edit to adult_events_filter.py:
    python3 test_adult_events_filter.py
Must report: all passed, 0 failed.
"""
import adult_events_filter as A

# (title, category, expected_verdict, is_seed)
CASES = [
    # ---- must DROP (real adult-service titles from the live feed) ----
    ("Career Services", "events", "drop", False),
    ("Job Search Assistance", "events", "drop", False),
    ("Job Search Assistance: Goodwill-Easter Seals", "events", "drop", False),
    ("In-Person Job Club", "events", "drop", False),
    ("LGBTQIA+ Job Seeker Workshop", "events", "drop", False),
    ("Seasoned Job Seeker Roundtable", "events", "drop", False),
    ("Medicare Counseling", "events", "drop", False),
    ("Medicare 101 with Minnesota Aging Pathways", "events", "drop", False),
    ("Medicare and Medicaid 101 OPEN HOUSE", "events", "drop", False),
    ("MNsure Help and Enrollment", "events", "drop", False),
    ("Learn About MNsure and MinnesotaCare", "events", "drop", False),
    ("1:1 Tech Help", "events", "drop", False),
    ("Drop-in Tech Help", "events", "drop", False),
    ("Tech Help for Seniors", "events", "drop", False),
    ("One-to-One Computer and Tech Help by Appointment", "events", "drop", False),
    ("Tech Drop-in Session", "events", "drop", False),
    ("Resume Writing", "events", "drop", False),
    ("Drop-in Job Search and R\u00e9sum\u00e9 Assistance", "events", "drop", False),  # accented
    ("Resume Review with Career Force", "events", "drop", False),
    ("Virtual Interviewing Workshop", "events", "drop", False),
    ("City of Minneapolis Small Business Support", "events", "drop", False),
    ("Drop-in Business Consultations", "events", "drop", False),
    ("Employer of the Day: Terracon", "events", "drop", False),
    ("Community Partner of the Day: Urban League Twin Cities", "events", "drop", False),
    ("Employment Resource Fair", "events", "drop", False),
    ("Minneapolis Works: CAPI", "events", "drop", False),
    ("Work Wednesday: Job Training and Resources", "events", "drop", False),

    # ---- must DROP (2026-08-28 synonym expansion: real live-feed titles) ----
    ("Public Computer Aide", "events", "drop", False),
    ("Book a Tech Tutor", "events", "drop", False),
    ("Computer Tutor Appointment", "events", "drop", False),
    ("Technology Assistance Drop-In", "events", "drop", False),
    ("1:1 Technology Help", "events", "drop", False),
    ("Drop-in Computer Lab", "events", "drop", False),
    ("Digital Literacy Class", "events", "drop", False),
    ("CareerForce Winona Office Hours", "events", "drop", False),
    ("Career Planning for Artists", "events", "drop", False),
    ("Senior Coffee Hour", "events", "drop", False),
    ("Senior Social", "events", "drop", False),
    ("Coffee for Older Adults", "events", "drop", False),
    ("55+ Book Club", "events", "drop", False),
    ("Drop-in Resources for Veterans", "events", "drop", False),
    # generic adult programming (the guarded rule)
    ("Adult Coloring Hour", "events", "drop", False),
    ("Adult Craft - Macrame Plant Hanger", "events", "drop", False),
    ("Book Club for Adults", "events", "drop", False),
    ("Dial-a-Story for Adults", "events", "drop", False),
    ("Soma Yoga for Adults", "events", "drop", False),
    ("Adaptive Adult Storytime", "events", "drop", False),

    # ---- must DROP (2026-08-31 expansion: adult titles found stale in the live app) ----
    ("Estate Planning 101", "events", "drop", False),
    ("Navigating Estate Planning", "events", "drop", False),
    ("Dementia 101", "events", "drop", False),
    ("Join Us for an Informative Presentation: Navigating the Dementia Journey", "events", "drop", False),
    ("AGC North Metro Member & Guest Happy Hour", "events", "drop", False),
    ("Dave\u2019s retirement party", "events", "drop", False),           # curly apostrophe
    ("Harvest Bank Blood Drive", "events", "drop", False),
    # compound bar/brewery-trivia rule (trivia + alcohol token only)
    ("Trivia Thursday at Minnesota BEER Company", "events", "drop", False),
    ("Pub Trivia Night", "events", "drop", False),
    ("Trivia at Bent Brewstillery Taproom", "events", "drop", False),
    # 2026-09-07: the 'Brewing' form. Both are REAL live titles in the 09-07 window that the
    # rule could not see while the alcohol list carried \bbrewery\b alone.
    ("Smart Alex Trivia at Copper Trail Brewing", "events", "drop", False),
    ("Intuit-To-Win-It Trivia at Intuition Brewing", "events", "drop", False),
    # 2026-09-23: the 'tavern' form. The first is a REAL live title in the 09-23 window that the
    # rule could not see while the alcohol list named every drinking-establishment synonym except
    # the oldest one. The other two pin saloon/alehouse, which have no live titles yet.
    ("Trivia night at Tavern 507 in Marshall", "events", "drop", False),
    ("Bingo at the Silver Dollar Saloon", "events", "drop", False),
    ("Karaoke at the Riverside Alehouse", "events", "drop", False),

    # ---- must DROP (2026-09-01 audit: adult/non-family titles found stale in the live app) ----
    # concerts / comedy — explicit named-act list (no keyword catches these)
    ("Wallflowers 30th Anniversary Tour", "events", "drop", False),
    ("Happy Together Tour", "events", "drop", False),
    ("Doug Stone Farewell Tour", "events", "drop", False),
    ("Tom Papa", "events", "drop", False),
    ("Liz Phair - St. Paul, MN", "events", "drop", False),
    ("Brandon Flowers - Saint Paul, MN", "events", "drop", False),
    ("Phoebe Bridgers at Saint Paul, MN", "events", "drop", False),
    ("Bombargo - Saint Paul", "events", "drop", False),
    ("Ida Undertow Show - St. Paul, MN", "events", "drop", False),
    ("Sugarland Ride or Die Tour", "events", "drop", False),
    ("Tyler Polzin @ OMNI - Maple Grove!", "events", "drop", False),
    # fundraiser galas / banquets
    ("Aspirus | Circle of Light Gala", "events", "drop", False),
    ("DMN Light of Hope Fundraiser Dinner Gala", "events", "drop", False),
    ("Itasca chapter annual banquet", "events", "drop", False),
    ("MN Lacrosse Hall of Fame Award Ceremony & Gala", "events", "drop", False),
    # professional / business conferences
    ("AWWA MN Section Annual Conference", "events", "drop", False),
    ("MN Recreation and Park Association Annual Conference", "events", "drop", False),
    ("Women in Leadership Conference", "events", "drop", False),
    ("WCR Realtor Safety CE", "events", "drop", False),
    ("Regenerative AG & Homesteading Summit with Joel Salatin", "events", "drop", False),
    ("SBR: Marketing Matters... No Really. It Does.", "events", "drop", False),
    ("Inside Executive Minds with Radha Chavali", "events", "drop", False),
    ("Zion Lutheran Church Stewardship Conference", "events", "drop", False),
    ("Fast-Track to Social Media Marketing for Business", "events", "drop", False),
    # men-only adult groups
    ("Men's Bible Study - Subversive: Living in God's Kingdom", "events", "drop", False),
    ("Oakdale Men's Book Club", "events", "drop", False),
    ("F3 Men's Workout - The Edge", "events", "drop", False),
    # adult wellness / mental-health talks & fairs
    ("Changing the Narrative on Mental Health and Suicide", "events", "drop", False),
    ("Holistic Healing & Wellness Fair Maple Grove, MN", "events", "drop", False),
    ("Maternal Mental Health Awarness", "events", "drop", False),
    ("The Working Caregiver, Presented by Family Means", "events", "drop", False),
    # ruck / adult import-car expo / adult women's fitness class
    ("Ruck Life Twin Cities", "events", "drop", False),
    ("IMPORTEXPO - Minnesota 2026", "events", "drop", False),
    ("IMPORTEXPO Minnesota", "events", "drop", False),
    ("SHiNE @ Fitness in the Parks", "events", "drop", False),

    # ---- must KEEP (2026-09-01 rules must NOT sweep in the family false-positives) ----
    ("Wayzata Car Show", "events", None, False),                     # community car show, not IMPORTEXPO
    ("Anoka Classic Car Show", "events", None, False),
    ("Otsego Prairie Festival - Touch-A-Truck & Car Show", "events", None, False),
    ("Meet the Author: Elizabeth Acevedo", "events", None, False),   # library author visit
    ("Local Author Visit: John Ball", "events", None, False),
    ("Black Authors Book Club: Black Buck", "events", None, False),  # community book club (not men's)
    ("Galaxie Book Club", "events", None, False),                    # 'gala' substring must not trip
    ("UMD Men's Hockey vs Bemidji State University", "events", None, False),   # college sport
    ("Minnesota Gophers Women's Soccer vs Iowa", "events", None, False),       # college sport
    ("Parent-Teacher Conference Day Camp", "events", None, False),   # 'conference' w/o adult-context words
    ("Spirits of Summit Avenue St. Paul Ghost Walk", "events", None, False),   # 'summit' in a street name

    # ---- must KEEP (the compound trivia rule must NOT over-fire) ----
    ("Trivia Night with Trivia Mafia", "events", None, False),          # library all-ages trivia, no alcohol token
    ("Family Trivia at the Library", "events", None, False),            # 'library' must not trip \bbar\b
    ("OMNI Brewery Oktoberfest", "events", None, False),                # brewery but no 'trivia' -> family fest
    ("Waldmann Brewery Oktoberfest", "events", None, False),            # brewery but no 'trivia'
    # 2026-09-07: the KEEP side of the 'Brewing' widening — each a real live title. These are
    # what prove the change completed the VOCABULARY without widening the rule's SHAPE.
    ("Live Music at 22 Northmen Brewing", "events", None, False),        # brewing, no 'trivia'
    ("Driftless Revelers at Bent Paddle Brewing Company", "events", None, False),
    ("Mille Lacs Kathio State Park Trivia", "events", None, False),      # state-park all-ages trivia
    ("Tall Tale Trivia at Sibley State Park", "events", None, False),    # state-park all-ages trivia
    ("Public Library Story Time", "events", None, False),               # 'public' must not trip \bpub\b
    # 2026-09-23: the KEEP side of the 'tavern' widening. A REAL 12-row live title -- venue vibe,
    # no activity token, correctly survives, which is what proves the change completed the
    # VOCABULARY without widening the rule's SHAPE.
    ("Live Music at The Depot Smokehouse and Tavern", "events", None, False),
    # And the REJECTED candidate `lounge`, pinned by a case that can actually DISCRIMINATE. The
    # first draft of this pair was `Lactation Lounge` / `Teen Craft and Lounge` -- both real live
    # family titles, and both worthless AS TESTS, because neither carries an activity token, so
    # the compound rule could not have dropped them whether `lounge` were in the alcohol list or
    # not. They would have stayed green through exactly the regression they named (the 2026-09-21
    # NA_DIFFER lesson: isolate the thing under test). This case carries BOTH halves, so it goes
    # red the moment someone adds `lounge`, which is the decision being recorded.
    ("Teen Game Night Bingo at the Lounge", "events", None, False),

    # ---- 2026-09-21: the ACTIVITY widening (trivia -> trivia|bingo|karaoke) -----------------
    # DROP side: the only title in the live dataset the widened compound rule newly reaches.
    ("Bar Bingo", "events", "drop", False),                    # 929 Beer House & Grill, progressive jackpots
    ("Music Bingo at the Taproom", "events", "drop", False),   # constructed: activity + alcohol token
    ("Karaoke at the Brewpub", "events", "drop", False),       # \bpub\b must NOT be what fires here
    # KEEP side — every one a REAL live title, and these are what pin the widening down.
    # Plant Bingo is the load-bearing case: it runs at Two Fathoms BREWING and its own
    # description says "we welcome all ages", so a rule that dropped brewery bingo on venue
    # vibe would have deleted a real family event. The title carries no alcohol token, so it
    # survives -- which is the title-only scope doing exactly its job.
    ("Plant Bingo", "events", None, False),                    # Two Fathoms Brewing, all ages
    ("Two Fathoms Karaoke Night", "events", None, False),      # same venue, no age gate -> not a proper noun
    ("Fun Friday: Music Bingo", "events", None, False),        # Minnesota Beer Co., no alcohol token in TITLE
    ("Karaoke Night", "events", None, False),                  # George Latimer Central Library, k-pop, all ages
    ("Karaoke Party at Little Theatre Auditorium", "events", None, False),  # community theatre
    ("Book Bingo at the Shakopee Library!", "events", None, False),
    ("Kid's BINGO", "events", None, False),
    ("Community Bingo", "events", None, False),                # North Branch Library, "ages 8 and up"
    ("Afternoon of Bingo", "events", None, False),             # Willmar Community Center, "all ages"
    ("Youth Book Bingo", "events", None, False),

    # ---- 2026-09-21: proper nouns for adult venues that declare themselves only in the
    # DESCRIPTION, which a title-only rule can never reach (the `magnet senior center` case) ----
    ("Karaoke with DJ Rhumpshaker", "events", "drop", False),  # No Name Bar: "9pm-1am Free | 21+"
    ("Karaoke at Willy T\u2019s", "events", "drop", False),    # CURLY apostrophe, as the feed emits it
    ("Karaoke at Willy T's", "events", "drop", False),         # straight apostrophe must drop too
    ("Thirsty Thursdays Karaoke at the New London Legion", "events", "drop", False),
    ("Gun Bingo", "events", "drop", False),                    # American Legion, $50/ticket firearms raffle
    ("Y Cares Black Tie Bingo", "events", "drop", False),      # YMCA black-tie fundraiser gala
    ("Wild Cocktails", "events", "drop", False),               # the activity IS making alcoholic drinks
    # KEEP side for those proper nouns — each a real live title a looser phrase would have eaten.
    # Bare "black tie" must not be a DROP. NOTE the first draft of this case used "Black Tie
    # Family Gala" and legitimately FAILED -- `gala` is a long-standing DROP_PHRASE in its own
    # right, so the title never tested what it claimed to. Isolate the phrase under test.
    ("Black Tie Skate Night", "events", None, False),
    ("Live Jazz Music", "events", None, False),                # 18 rows merely MENTION a cocktail menu
    ("Wild Rice Harvest Festival", "events", None, False),     # bare "wild" must not fire
    ("Willy Wonka Jr. at the Youth Theatre", "events", None, False),  # "willy" must not fire alone

    # ---- 2026-09-22: the CRAWL, a drinking itinerary no activity keyword reaches -------------
    # DROP: the live row. Its description states "must be 21" AND the activity IS alcohol -- two
    # independent explicit adult signals, which is the line the 2026-09-21 block draws. The
    # compound rule could never reach it: a crawl is a ROUTE between bars, not one of the
    # (trivia|bingo|karaoke) activities, so this is a VOCABULARY entry, not a shape change.
    ("Fari \u201cBOO\u201d Downtown Bar Crawl", "events", "drop", False),  # curly quotes, as the feed emits
    ("Fari \"BOO\" Downtown Bar Crawl", "events", "drop", False),          # straight quotes must drop too
    ("Downtown Pub Crawl", "events", "drop", False),            # the "pub crawl" half, pinned separately
    # KEEP side, and these are what make the phrase ANCHORED rather than a bare keyword.
    # Measured on the live dataset before the edit: "bar crawl" 1 title / 1 row, "pub crawl" 0,
    # bare "crawl" 2 -- the extra one being this real family Halloween event. A bare `crawl`
    # keyword would have deleted it, which is the wrong-DROP direction that actually hurts.
    ("Winona Zombie Crawl *20 Years And Crawling*", "events", None, False),
    ("Baby Crawling Races", "events", None, False),             # "crawl" as a family activity
    # A live Kids Bowl Free bowling center, in the dataset today. Any rule keyed on \bbar\b
    # alone would eat it -- the same shape as "Public Library" fencing \bpub\b.
    ("Wildwood Sports Bar & Grill", "events", None, False),

    # ---- must KEEP (guards against the generic adult rule — every one a real live title) ----
    ("Bird Migration Walk (best for ages 8 to adult)", "events", None, False),   # age range
    ("Fungus Among Us (best for ages 8-adult)", "events", None, False),          # age range
    ("Don't Move a Mussel (best for ages 3 to adult)", "events", None, False),   # age range
    ("Birds of Wild River (best for ages 3 to adult)", "events", None, False),   # age range
    ("Createch Unplugged", "events", None, False),                               # kids/maker
    ("Createch Tournament of Champions: Smash Brothers", "events", None, False), # kids/maker
    ("Ask an iLAB Mentor: 3D Modeling and Slicing Techniques", "events", None, False),
    ("DIY: Sewing Techniques", "events", None, False),                           # maker substring
    ("Veterans Memorial Pow Wow", "events", None, False),                        # place name
    ("Free Summer Concerts at Veterans Memorial Park", "events", None, False),   # place name
    ("Young Adult Book Club", "events", None, False),                            # teen (YA) category

    # ---- must KEEP (family events a naive keyword filter wrongly flags) ----
    ("Fiesta Latina", "events", None, False),                       # desc mentions a job booth; title clean
    ("Family Storytime", "events", None, False),                    # "caregiver" only in desc
    ("Baby Storytime", "events", None, False),
    ("Library Book Club - Where Rivers Part", "events", None, False),  # book club NOT filtered
    ("Short Story Book Club (Final Session)", "events", None, False),  # kids' book club
    ("Toddler Open Gym", "events", None, False),
    ("Teen Career Exploration Night", "events", None, False),        # a real teen program stays (no drop phrase)
    ("Fall Harvest Orchard Opening Weekend", "events", None, False), # earlier "55+" substring misfire

    # ---- category guard: adult-sounding title outside events is untouched ----
    ("Small Business Saturday Market", "restaurants", None, False),
    ("Job Corps Volunteer Day", "volunteer_opportunities", None, False),

    # ---- must NOT DROP (2026-09-10 hand review of the REVIEW tier). Both are real live titles
    #      whose adult-sounding words name PARENTS OF CHILDREN -- i.e. exactly this guide's
    #      audience.  They correctly land in REVIEW rather than being silently kept: "caregiver
    #      support" and "support group" DO name adult programming most of the time, so the tier
    #      is right and the hand read is the resolution.  What these cases assert is that they
    #      never become DROPs -- a later reader tempted to promote either phrase into
    #      DROP_PHRASES will fail here.  Both were reviewed and KEPT on 2026-09-10.
    ("Family Caregiver Support Consultations", "events", "review", False),
    #   age_range "All ages", tags carry all-ages: a free library social-worker consultation.
    #   The source declares the audience; inferring adult-only from the word "Caregiver" would
    #   assert a claim the source did not make.
    ("Family Support Group-Afton,MN", "events", "review", False),
    #   description: "a parent or caregiver of a child age 21 or younger". Note that "the
    #   working caregiver" IS a DROP phrase -- a specific adult talk title -- which is exactly
    #   why neither rule is a bare "caregiver" or a bare "support group".

    # ---- REVIEW tier (borderline, never auto-dropped) ----
    # 2026-09-10: "Magnet Senior Center" was a REVIEW case here until its 16 live rows were
    # read by hand -- its description says "All individuals age 55+ are welcome" -- so it is
    # now an unambiguous DROP by proper noun. Bare "senior center" must STAY in REVIEW: an
    # intergenerational event held AT a senior center is a real family KEEP, and the two cases
    # below are what pin that distinction down for the next reader.
    ("Magnet Senior Center", "events", "drop", False),
    ("Family Fun Night at the Eagan Senior Center", "events", "review", False),
    ("Senior Center Open House", "events", "review", False),
    # 2026-09-10, same shape: an adult library meditation talk, dropped by its own full title.
    # Bare "grief" must STAY in REVIEW -- the three KEEPs below are real Minnesota family
    # grief programming that a bare "grief" DROP phrase would silently delete.
    ("Dealing with Grief and Other Emotional Challenges Through Meditation",
     "events", "drop", False),
    ("Children's Grief Connection Family Camp", "events", "review", False),
    ("Kids Grief Support Group", "events", "review", False),
    ("Grief Camp for Children and Teens", "events", "review", False),

    # ---- seed guard: a seed matching a drop phrase is reviewed, never dropped ----
    ("Career Services", "events", "review", True),
]


def main():
    passed = failed = 0
    for title, cat, expected, is_seed in CASES:
        row = {"title": title, "category": cat}
        if is_seed:
            row["is_seed"] = True
        verdict, phrase = A.classify(row)
        ok = verdict == expected
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  {title!r} ({cat}, seed={is_seed}): "
                  f"expected {expected!r}, got {verdict!r} [{phrase}]")
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
