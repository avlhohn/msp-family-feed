#!/usr/bin/env python3
"""STEP 6 publish — all six feed artifacts to avlhohn/msp-family-feed — 2026-08-28.

`gh_publish_feed.py` hardcodes `PATH="msp_family_guide.json"`, so it can only ship one of the
six files. Its logic is reused unchanged (GET sha -> base64 PUT -> verify, up to 3 attempts);
only the verification is replaced, for a specific reason:

`gh_publish_feed.py` verifies by re-reading the file's `size` and asserting `size >= 50000`.
That is both too weak and too strong. Too weak: any 50 KB file passes, including LAST run's
copy if the PUT silently no-opped. Too strong: `deals.csv` is the smallest artifact and an
off-season day could legitimately take it under the threshold. It is also the check that
produced the known false `parks.csv` publish FAIL — an idempotent PUT (identical content)
leaves the sha unchanged, which the size/sha heuristics read as "nothing happened."

This verifies by **git blob SHA-1** instead: `sha1("blob <len>\\0" + bytes)` is exactly what
GitHub reports in the contents API `sha` field, for a file of any size, and it is computable
locally. If the local blob hash equals the remote one, the remote content IS the local
content — whether the PUT changed anything or not. That makes an idempotent publish a PASS
rather than a false failure, and makes a stale remote an unambiguous FAIL.

Bytes are uploaded verbatim. The published CSVs use CRLF (verified against the live
`deals.csv` this run), which is what `build_guide.py`'s `csv.DictWriter` emits, so no
line-ending rewrite is applied — rewriting them would churn every line of every file in the
repo's diff for no benefit.
"""
import os as _os
# Promoted to the folder ROOT 2026-08-29. Helpers CLAUDE.md names must live here, not
# in a .runNNNN/ scratch folder -- that folder is private to one run and the next run
# is sent to a path that may not exist. Report/output paths now resolve at runtime from
# MSP_RUNDIR (default "."), so nothing is hardcoded to one run's directory.
RUNDIR = _os.environ.get("MSP_RUNDIR", ".")

import sys, json, time, base64, hashlib, urllib.request, urllib.error

REPO = "avlhohn/msp-family-feed"
BRANCH = "main"
FILES = ["msp_family_guide.json", "events.csv", "parks.csv", "deals.csv",
         "volunteer.csv", "restaurants.csv"]
if "--only" in sys.argv:
    FILES = [sys.argv[sys.argv.index("--only") + 1]]
MSG = sys.argv[1] if len(sys.argv) > 1 else "Daily feed 2026-09-02"

# --- publish_feed_secret_guard (2026-10-02) ---------------------------------
# argv[1] is the COMMIT MESSAGE, and the token comes from github_token.txt. On
# 2026-10-02 a token was passed here as argv[1] and published verbatim into the
# commit log of a PUBLIC repo; GitHub secret scanning revoked it. A commit
# message is metadata, invisible to every content-based check in this pipeline,
# so this is the only place the leak can be caught. HARD FAIL (not a warning):
# the consequence is irreversible publication of a live credential. The shape
# list is measured against the real leaked string (a `github_pat_` fine-grained
# PAT) plus the classic/oauth/app/refresh shapes and a bare 40-hex classic token.
import re as _re
def _looks_like_secret(s):
    t = (s or "").strip()
    if _re.match(r"^gh[pousr]_[A-Za-z0-9]{20,}$", t):      # ghp_/gho_/ghu_/ghs_/ghr_
        return "github classic/oauth/app token shape"
    if t.startswith("github_pat_"):                         # fine-grained PAT (the real leak)
        return "github fine-grained PAT shape"
    if _re.fullmatch(r"[0-9a-f]{40}", t):                   # legacy 40-hex token
        return "40-hex token shape"
    for k, v in _os.environ.items():                        # exact match vs any *TOKEN*/*SECRET* env
        if ("TOKEN" in k.upper() or "SECRET" in k.upper()) and v and v.strip() == t:
            return "exact match of env var " + k
    try:                                                    # exact match vs the token file itself
        if t and t == open("github_token.txt").read().strip():
            return "exact match of github_token.txt contents"
    except OSError:
        pass
    return None
_why = _looks_like_secret(MSG)
if _why:
    sys.exit("REFUSING TO PUBLISH: argv[1] (the commit MESSAGE) looks like a credential "
             "(" + _why + "). The token belongs ONLY in github_token.txt, never on the "
             "command line. Re-run with a real commit message, e.g.:\n"
             '    python3 publish_feed.py "Daily feed update" --only restaurants.csv')
# ----------------------------------------------------------------------------


def tok():
    return open("github_token.txt").read().strip()


def api(method, url, token, body=None):
    req = urllib.request.Request(
        url, method=method, data=(json.dumps(body).encode() if body else None))
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "msp-family-feed")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except ValueError:
            return e.code, {}
    except urllib.error.URLError as e:
        return 0, {"message": str(e)}


def blob_sha(raw):
    """The object id git stores — identical to the contents API `sha` field."""
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(raw))
    h.update(raw)
    return h.hexdigest()


def remote(token, path):
    st, j = api("GET", f"https://api.github.com/repos/{REPO}/contents/{path}"
                       f"?ref={BRANCH}", token)
    if st == 200:
        return j.get("sha"), j.get("size")
    return None, None


def publish_one(token, path):
    raw = open(path, "rb").read()
    want = blob_sha(raw)
    b64 = base64.b64encode(raw).decode()
    last = None
    for attempt in range(1, 4):
        sha, size = remote(token, path)
        if sha == want:
            return {"file": path, "result": "OK", "attempt": attempt,
                    "bytes": len(raw), "sha": want[:12],
                    "note": "already identical (idempotent)" if attempt == 1 else "verified"}
        body = {"message": MSG, "content": b64, "branch": BRANCH}
        if sha:
            body["sha"] = sha
        st, j = api("PUT", f"https://api.github.com/repos/{REPO}/contents/{path}",
                    token, body)
        vsha, vsize = remote(token, path)
        if st in (200, 201) and vsha == want:
            return {"file": path, "result": "OK", "attempt": attempt,
                    "bytes": len(raw), "sha": want[:12], "note": f"PUT {st}"}
        last = f"put={st} {str(j.get('message'))[:60]} remote_sha={str(vsha)[:12]}"
        print(f"    RETRY {path} attempt={attempt} {last}")
        time.sleep(2 * attempt)
    return {"file": path, "result": "FAIL", "attempt": 3, "bytes": len(raw),
            "sha": want[:12], "note": last}


def main():
    token = tok()
    out = []
    for p in FILES:
        r = publish_one(token, p)
        out.append(r)
        print(f"  {r['result']:4} {p:26} {r['bytes']:>9} bytes  blob={r['sha']}"
              f"  attempt={r['attempt']}  {r['note']}")
    ok = sum(1 for r in out if r["result"] == "OK")
    print(f"STEP 6 publish: {ok}/{len(FILES)} verified by git blob SHA-1")
    json.dump(out, open(RUNDIR + "/_publish_report.json", "w"), indent=1)
    return 0 if ok == len(FILES) else 1


if __name__ == "__main__":
    sys.exit(main())
