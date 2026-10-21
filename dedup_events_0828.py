"""STEP 4.3 precedence & de-duplication for the `events` category — 2026-08-28.

Runs BETWEEN 4.3a (adult_events_filter) and 4.3b (dedup_titles), which is where SKILL.md
puts the precedence/dedup rules. `dedup_titles.py` still runs LAST, per CLAUDE.md.

The merge stance is CLAUDE.md's, restated because it drives every threshold here:
**a missed duplicate is cosmetic; a wrong merge silently deletes a real event.**

So this pass deliberately does NOT implement SKILL.md's broadest event rule
("same title + same date + same venue collapses"). On the 2026-08-28 data that rule
would have merged 4 rows of "Ask a Sewing Mentor" at one Hastings address on one day
into 1 — but those are four separate appointment slots at 9:00/10:00/11:00/12:00, i.e.
four real, separately-registerable events. Where both rows carry a start time and the
times DIFFER, they are kept apart. Time is only ignored when one side has none, which is
the actual re-scrape signature (the same listing captured with and without a time).
"""
import json, re, sys, unicodedata, collections

SRC = sys.argv[1] if len(sys.argv) > 1 else "_compiled_work.json"
DRY = "--dry-run" in sys.argv

GENERIC = {"bar", "grill", "pub", "eatery", "cafe", "restaurant", "kitchen",
           "ristorante", "pizzeria", "company", "co", "and", "the", "of", "at"}


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    t = t.replace("&", " and ")
    t = re.sub(r"\s+[-\u2013\u2014]\s+.*$", "", t)      # trailing location qualifier
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)              # trailing parenthetical
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b(llc|inc|co|company)\b", " ", t)
    t = re.sub(r"^\s*the\s+", "", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_addr(a):
    a = unicodedata.normalize("NFKD", a or "").encode("ascii", "ignore").decode().lower()
    a = re.sub(r"[^a-z0-9 ]", " ", a)
    for x, y in [("street", "st"), ("avenue", "ave"), ("north", "n"), ("south", "s"),
                 ("east", "e"), ("west", "w"), ("road", "rd"), ("drive", "dr"),
                 ("boulevard", "blvd")]:
        a = re.sub(rf"\b{x}\b", y, a)
    return re.sub(r"\s+", " ", a).strip()


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#")[0].split("?")[0].rstrip("/")
    return u


def norm_time(t):
    t = (t or "").strip().lower().replace(" ", "")
    m = re.match(r"(\d{1,2}):(\d{2})(am|pm)?", t)
    if not m:
        return ""
    h = int(m.group(1)) % 12
    if m.group(3) == "pm":
        h += 12
    return f"{h:02d}:{m.group(2)}"


def completeness(r):
    """Richest row survives (CLAUDE.md dedup rule 3)."""
    score = 0
    for f in ("latitude", "longitude", "website", "image_url", "phone", "address",
              "time", "age_range", "price_type", "deal_description"):
        if str(r.get(f) or "").strip():
            score += 1
    score += min(len(str(r.get("description") or "")) // 200, 4)
    if str(r.get("has_deal")).lower() == "true":
        score += 1
    return score


def merge_into(keep, drop):
    """Copy the loser's non-empty unique fields up. Never overwrite a populated field,
    and never let a scraped row overwrite a seed's curated values."""
    seedsafe = {"title", "address", "category", "tags"} if keep.get("is_seed") else set()
    for k, v in drop.items():
        if k.startswith("_") or k in ("is_seed",) or k in seedsafe:
            continue
        if not str(keep.get(k) or "").strip() and str(v or "").strip():
            keep[k] = v
    kt = [x for x in (keep.get("tags") or "").split(",") if x]
    for t in (drop.get("tags") or "").split(","):
        if t and t not in kt:
            kt.append(t)
    keep["tags"] = ",".join(kt)
    if str(drop.get("has_deal")).lower() == "true":
        keep["has_deal"] = True


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    ev = d["events"]
    for i, r in enumerate(ev):
        r["_ix"] = i

    clusters = collections.defaultdict(list)
    for r in ev:
        date = (r.get("date") or "")[:10]
        u = norm_url(r.get("website"))
        # rule A: same event deep-link + same date
        if u and re.search(r"/(event|events|mc-events)/", u):
            clusters[("url", u, date)].append(r)
            continue
        # rules B/C: normalized title + date + venue, time as a separator only
        clusters[("tav", norm_title(r.get("title")), date,
                  norm_addr(r.get("address"))[:45])].append(r)

    merges, dropped = [], set()
    for key, rows in clusters.items():
        if len(rows) < 2:
            continue
        if key[0] == "tav":
            # split the cluster by start time; rows with NO time join every subgroup's
            # merge candidate list, because a missing time is the re-scrape signature.
            timed = collections.defaultdict(list)
            untimed = []
            for r in rows:
                t = norm_time(r.get("time"))
                (timed[t] if t else untimed).append(r)
            groups = [v for v in timed.values()]
            if untimed:
                if len(groups) == 1:
                    groups[0].extend(untimed)          # one real slot + bare re-scrapes
                elif not groups:
                    groups = [untimed]
                else:
                    groups.append(untimed)             # ambiguous: collapse among themselves
        else:
            groups = [rows]

        for g in groups:
            if len(g) < 2:
                continue
            seeds = [r for r in g if r.get("is_seed")]
            pool = seeds if seeds else g
            keep = max(pool, key=completeness)
            for r in g:
                if r is keep or r["_ix"] in dropped:
                    continue
                merge_into(keep, r)
                dropped.add(r["_ix"])
                merges.append({
                    "kept": keep.get("title", "")[:90],
                    "dropped": r.get("title", "")[:90],
                    "date": (r.get("date") or "")[:10],
                    "rule": ("event_url+date" if key[0] == "url" else
                             "title+date+venue" + ("+time" if norm_time(r.get("time")) else "")),
                    "seed_override": bool(seeds),
                })

    kept = [r for r in ev if r["_ix"] not in dropped]
    for r in ev:
        r.pop("_ix", None)
    print(f"STEP 4.3 event dedup{' (DRY RUN)' if DRY else ''}: "
          f"{len(ev)} -> {len(kept)} ({len(dropped)} collapsed)")
    by = collections.Counter(m["rule"] for m in merges)
    for k, v in by.most_common():
        print(f"  rule {k:26} {v}")
    print(f"  seed overrides: {sum(1 for m in merges if m['seed_override'])}")
    json.dump(merges, open("_dedup_events_report_0828.json", "w"),
              ensure_ascii=False, indent=1)
    print("  report -> _dedup_events_report_0828.json")
    if not DRY:
        d["events"] = kept
        json.dump(d, open(SRC, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
