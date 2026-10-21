import json, csv, os, sys, re, datetime

# The feed's metadata header (generated_date / date_range / day_of_week) is the ONLY place a
# reader learns when this feed was built and what window it covers. It used to be three hardcoded
# literals -- `TODAY="2026-09-07"; END="2026-10-31"; DOW="Monday"` -- copied forward every run and
# restamped by hand. On 2026-09-08 the restamp was missed: every CATEGORY LIST and every count was
# correct and current, while the header announced the feed as Monday 2026-09-07 covering a window
# that had already started. Nothing raised, because the data and the header are written by
# different lines and only the data is ever checked.
#
# Same treatment as fetch_feeds.py's window and errlog_step7.py's run date: no literal, no
# default, and a MISSING value is a hard failure rather than a silent fallback. STEP 1 derives
# these from a server-side timestamp (see params.txt) -- never from the sandbox clock, which has
# been wrong, and wrong in agreement with the injected currentDate.
#
# DOW is DERIVED from TODAY rather than passed in. Two values that must agree, supplied
# separately, are two values that will eventually disagree -- and the weekday is what RUN_APIFY
# gates on.
TODAY = os.environ.get("MSP_TODAY", "")
END   = os.environ.get("MSP_END", "")
for _n, _v in (("MSP_TODAY", TODAY), ("MSP_END", END)):
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", _v):
        raise SystemExit(
            f"build_guide.py: env {_n} must be set to YYYY-MM-DD (got {_v!r}).\n"
            "  STEP 1 derives the run date and window end from a server-side timestamp.\n"
            "  There is deliberately NO default: a stale feed header is invisible, because\n"
            "  the rows can be perfectly current while the header names the wrong day.")
DOW = datetime.date.fromisoformat(TODAY).strftime("%A")
if END < TODAY:
    raise SystemExit(f"build_guide.py: MSP_END ({END}) precedes MSP_TODAY ({TODAY}).")

SRC = sys.argv[1] if len(sys.argv)>1 else '_compiled_base.json'
METRO="Minnesota Statewide (Twin Cities metro + Duluth, Rochester, St. Cloud, Mankato, Moorhead, Brainerd, Bemidji, Winona, Alexandria)"
SCHEMA="3.1"
CATS=['events','parks','meal_deals','volunteer_opportunities','restaurants']
CSVMAP={'events':'events.csv','parks':'parks.csv','meal_deals':'deals.csv',
        'volunteer_opportunities':'volunteer.csv','restaurants':'restaurants.csv'}
BASE=['title','description','category','price_type','price','age_range','address',
      'latitude','longitude','image_url','image_source','date','time','phone',
      'website','has_deal','deal_description','deal_expiry','tags']
COLS=BASE+['metro_area','schema_version']

d=json.load(open(SRC))
feed={
 'generated_date':TODAY,'date_range':f'{TODAY} to {END}','day_of_week':DOW,
 'metro_area':METRO,'schema_version':SCHEMA,
 'counts':{c:len(d[c]) for c in CATS},
}
for c in CATS:
    clean=[]
    for it in d[c]:
        row={k:it.get(k,'') for k in BASE}
        if row['tags'] is None: row['tags']=''
        if isinstance(row['tags'],list): row['tags']=','.join(x for x in row['tags'] if x)
        hv=row['has_deal']
        row['has_deal']= True if str(hv).lower() in ('true','1','yes') else (bool(hv) if isinstance(hv,bool) else False)
        for k in BASE:
            if row[k] is None: row[k]=''
        # gotcha 18: evergreen categories accumulate stale date values across runs
        if c in ('restaurants','parks'):
            row['date']=''
        clean.append(row)
    feed[c]=clean

json.dump(feed, open('msp_family_guide.json','w'), ensure_ascii=False, indent=2)
for c in CATS:
    with open(CSVMAP[c],'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=COLS); w.writeheader()
        for it in feed[c]:
            row=dict(it); row['metro_area']=METRO; row['schema_version']=SCHEMA
            w.writerow(row)
print('BUILD OK counts:', feed['counts'])
for fn in ['msp_family_guide.json']+list(CSVMAP.values()):
    print(fn, os.path.getsize(fn), 'bytes')
