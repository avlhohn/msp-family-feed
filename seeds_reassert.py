#!/usr/bin/env python3
"""STEP 3 re-assertion of the must-include seed list — 2026-08-28.

Two jobs, in this order:

1. **Drift check.** The stored slug list (`.run0822/_seed_names.json`, 182 names) is a
   snapshot. CLAUDE.md/memory rule 4 says the seed span must be derived at RUNTIME because
   SKILL.md gets edited, so this re-parses the `### Must-include …` → `### STEP 2 — MANDATORY`
   span and diffs the venue names against the snapshot. A name added to SKILL.md since
   2026-08-22 would otherwise never be checked for.

2. **Presence check + is_seed marking.** `is_seed` is NOT one of the 19 schema-v3.1 BASE
   fields, so — exactly like `deal_source` — `build_guide.py` destroys it and the carried base
   always arrives with zero seeds marked. It therefore has to be re-derived every run, and it
   must be re-derived BEFORE anything that gives seeds precedence.

Matching follows CLAUDE.md's precision stance: a *contiguous token subsequence*, never a loose
subset. The normalizer drops {the, and, at, of, a, an, in, minnesota}; a one-token residue
("Minnesota Zoo" -> "zoo") is too weak to substring-match, so those fall back to the
parenthetical-qualified form or an exact title prefix.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import json, re, sys, time, unicodedata, collections

import glob as _glob, os as _os
def _find_skill():
    """Resolve SKILL.md at runtime. A hardcoded /sessions/<name>/ path from a
    prior run is dead in this session -- that stranding is a known recurring bug."""
    cands = []
    if _os.environ.get("MSP_SKILL"):
        cands.append(_os.environ["MSP_SKILL"])
    cands += sorted(_glob.glob("/sessions/*/mnt/uploads/SKILL.md"))
    cands += sorted(_glob.glob("/sessions/*/mnt/msp-family-guide-daily/SKILL.md"))
    cands += sorted(_glob.glob("/sessions/*/mnt/*/SKILL.md"))
    for p in cands:
        if _os.path.exists(p):
            return p
    raise SystemExit("FATAL: SKILL.md not found in any session uploads dir")
SKILL = _find_skill()
SNAP = "seed_names_snapshot.json"   # promoted to root 2026-08-29 from .run0822/
WORK = "_compiled_work.json"
OUT = RUNDIR + "/_seed_report.json"
CATS = ["events", "parks", "meal_deals", "volunteer_opportunities", "restaurants"]
STOP = {"the", "and", "at", "of", "a", "an", "in", "minnesota"}


def toks(s, keep_paren=False):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    if not keep_paren:
        s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^A-Za-z0-9]", " ", s.lower())
    return [w for w in s.split() if w not in STOP]


def seed_key(name):
    bare = toks(name)
    if len(bare) == 1:
        q = toks(name, keep_paren=True)
        if len(q) > 1:
            return q, "qualified"
        return bare, "prefix"
    return bare, "contiguous"


def contiguous(needle, hay):
    n = len(needle)
    if not n or n > len(hay):
        return False
    return any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


def parse_skill_names():
    """Runtime-derived seed span. Never hardcode line indices."""
    txt = open(SKILL, encoding="utf-8").read().split("\n")
    starts = [i for i, L in enumerate(txt) if L.startswith("### Must-include")]
    ends = [i for i, L in enumerate(txt) if L.startswith("### STEP 2 — MANDATORY")]
    if not starts or not ends:
        sys.exit("FATAL: could not locate seed section bounds in SKILL.md")
    S, E = starts[0], ends[0]
    names = []
    for L in txt[S:E]:
        m = re.match(r"\s*-\s+\*\*(.+?)\*\*(.*)$", L)
        if not m:
            continue
        raw = m.group(1).strip()
        if len(raw) < 3 or raw.endswith(":"):
            continue
        if re.match(r"^(NO |Accuracy guard|Discovery|Routing|IMPORTANT|NOTE)", raw, re.I):
            continue
        names.append(raw)
    return names, (S + 1, E, len(starts))


def main():
    snap = json.load(open(SNAP))
    bad = [s["name"] for s in snap if " ".join(toks(s["name"])) != s["slug"]]
    if bad:
        print("NORMALIZER MISMATCH on", len(bad), "seeds:", bad[:10])
        sys.exit(1)
    print(f"normalizer self-check: {len(snap)}/{len(snap)} stored slugs reproduced exactly")

    live, span = parse_skill_names()
    print(f"SKILL.md seed span: lines {span[0]}..{span[1]} ({span[2]} Must-include headings)")
    snap_n = {s["name"] for s in snap}
    live_n = set(live)
    added = sorted(live_n - snap_n)
    gone = sorted(snap_n - live_n)
    # The snapshot's date is read from the FILE, never carried as a literal: this line
    # read "vs 2026-08-22 snapshot" for 19 days after the snapshot was refreshed on
    # 2026-08-30, so a reader diffing against a file that had already moved was told it
    # was diffing against one that had not.  Same class as the _errlog_NNNN date literals.
    _snap_date = time.strftime("%Y-%m-%d", time.gmtime(_os.path.getmtime(SNAP)))
    print(f"seed-list drift vs {_snap_date} snapshot ({len(snap)} names): "
          f"+{len(added)} / -{len(gone)}")
    if added:
        print("  ADDED in SKILL.md since snapshot:", added)
    if gone:
        print("  IN SNAPSHOT BUT NOT PARSED NOW:", gone[:12],
              "..." if len(gone) > 12 else "")

    # Check the union so a newly added SKILL.md venue is not skipped this run.
    seeds = [{"name": n} for n in sorted(snap_n | live_n)]

    d = json.load(open(WORK))
    rows = [(c, r) for c in CATS for r in d[c]]
    for _, r in rows:
        r["is_seed"] = False
    tcache = [(c, r, toks(r.get("title")), toks(r.get("address"))) for c, r in rows]

    marked = 0
    missing = []
    per_seed = {}
    modes = collections.Counter()
    for s in seeds:
        st, mode = seed_key(s["name"])
        modes[mode] += 1
        hits = 0
        for c, r, tt, at in tcache:
            if mode == "prefix":
                ok = tt[:1] == st
            else:
                ok = contiguous(st, tt) or (len(st) >= 3 and contiguous(st, at))
            if ok:
                r["is_seed"] = True
                hits += 1
        per_seed[s["name"]] = hits
        marked += hits
        if hits == 0:
            missing.append(s["name"])

    n_seed_rows = sum(1 for _, r in rows if r["is_seed"])
    json.dump(d, open(WORK, "w"), ensure_ascii=False)
    json.dump({"snapshot_names": len(snap), "skill_names_parsed": len(live),
               "checked": len(seeds), "added_vs_snapshot": added,
               "absent_vs_snapshot": gone, "rows_marked": n_seed_rows,
               "missing": missing, "per_seed": per_seed},
              open(OUT, "w"), indent=1)

    print(f"seed names checked={len(seeds)}  distinct rows marked is_seed=True: {n_seed_rows}"
          f"  (raw hits {marked})  missing: {len(missing)}")
    print("  match modes:", dict(modes))
    top = sorted(per_seed.items(), key=lambda x: -x[1])[:6]
    print("  widest matches (watch for over-broad slugs):", top)
    if missing:
        print("  MISSING:", missing)
    print("  report ->", OUT)


if __name__ == "__main__":
    main()
