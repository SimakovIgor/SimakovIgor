#!/usr/bin/env python3
"""Fetch real GitHub stats for the profile card and write stats.json, then
regenerate dark.svg / light.svg. Runs locally and in GitHub Actions.

Token resolution: ACCESS_TOKEN (repo secret) > GH_TOKEN > GITHUB_TOKEN.
LOC per repo is cached in loc.json so daily runs only fetch new commits."""
import os, json, sys, subprocess, urllib.request, urllib.error, time, datetime

LOGIN = os.environ.get("PROFILE_LOGIN", "SimakovIgor")
YEAR = int(os.environ.get("PROFILE_YEAR", "2026"))
TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
API = "https://api.github.com/graphql"
BLOCKS = "▁▂▃▄▅▆▇█"


def gql(query, variables, tries=4):
    body = json.dumps({"query": query, "variables": variables}).encode()
    for i in range(tries):
        req = urllib.request.Request(API, body, {
            "Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
            "User-Agent": "simakov-profile-card"})
        try:
            j = json.loads(urllib.request.urlopen(req, timeout=30).read())
            if "errors" in j:
                raise RuntimeError(json.dumps(j["errors"], ensure_ascii=False))
            return j["data"]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def fetch_profile():
    q = """query($l:String!,$from:DateTime!,$to:DateTime!,$after:String){
      user(login:$l){ id createdAt
        followers{totalCount}
        contributionsCollection(from:$from,to:$to){
          contributionCalendar{ totalContributions weeks{contributionDays{contributionCount}} } }
        repositories(first:100, ownerAffiliations:OWNER, isFork:false, after:$after){
          totalCount pageInfo{hasNextPage endCursor}
          nodes{ name stargazerCount primaryLanguage{name} } }
      }}"""
    nodes, after, base = [], None, None
    while True:
        d = gql(q, {"l": LOGIN, "from": f"{YEAR}-01-01T00:00:00Z",
                    "to": f"{YEAR}-12-31T23:59:59Z", "after": after})
        u = d["user"]
        base = base or u
        page = u["repositories"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return base, nodes


def fetch_loc(user_id, repos):
    """Sum additions/deletions authored by the user across all repos.
    Counted fresh each run (repos are small); per-repo totals saved for debug."""
    q = """query($o:String!,$n:String!,$id:ID!,$after:String){
      repository(owner:$o,name:$n){ defaultBranchRef{ target{ ... on Commit{
        history(first:100, author:{id:$id}, after:$after){
          pageInfo{hasNextPage endCursor} nodes{ additions deletions } } }}}}}"""
    per_repo, added, removed = {}, 0, 0
    for r in repos:
        name, ra, rd, after = r["name"], 0, 0, None
        try:
            while True:
                d = gql(q, {"o": LOGIN, "n": name, "id": user_id, "after": after})
                ref = d["repository"]["defaultBranchRef"]
                if not ref:
                    break
                h = ref["target"]["history"]
                for c in h["nodes"]:
                    ra += c["additions"]; rd += c["deletions"]
                if not h["pageInfo"]["hasNextPage"]:
                    break
                after = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"  loc {name}: {e}", file=sys.stderr)
        per_repo[name] = {"add": ra, "del": rd}
        added += ra; removed += rd
    json.dump(per_repo, open("loc.json", "w"), indent=2)
    return added, removed


def fetch_recent_weeks(weeks_back=26):
    to = datetime.datetime.utcnow().replace(microsecond=0)
    frm = to - datetime.timedelta(weeks=weeks_back)
    q = """query($l:String!,$from:DateTime!,$to:DateTime!){ user(login:$l){
      contributionsCollection(from:$from,to:$to){ contributionCalendar{
        weeks{ contributionDays{ contributionCount } } } } } }"""
    d = gql(q, {"l": LOGIN, "from": frm.isoformat() + "Z", "to": to.isoformat() + "Z"})
    return d["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def sparkline(weeks, n=26):
    totals = [sum(dd["contributionCount"] for dd in w["contributionDays"]) for w in weeks][-n:]
    hi = max(totals) or 1
    return "".join(BLOCKS[min(7, int(v / hi * 7 + 0.5))] for v in totals)


def main():
    if not TOKEN:
        sys.exit("no token (set ACCESS_TOKEN / GH_TOKEN)")
    user, repos = fetch_profile()
    stars = sum(r["stargazerCount"] for r in repos)
    langs = {}
    for r in repos:
        pl = r.get("primaryLanguage")
        if pl:
            langs[pl["name"]] = langs.get(pl["name"], 0) + 1
    total_lang = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:2]
    cal = user["contributionsCollection"]["contributionCalendar"]

    added, removed = fetch_loc(user["id"], repos)

    stats = {
        "year": YEAR,
        "built": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "uptime": "10 yrs in IT",
        "email": os.environ.get("PROFILE_EMAIL", "simakoff30@gmail.com"),
        "repos": len(repos),
        "stars": stars,
        "followers": user["followers"]["totalCount"],
        "commits": cal["totalContributions"],
        "added": added,
        "removed": removed,
        "net": added - removed,
        "lang1_name": top[0][0] if top else "Java",
        "lang1_pct": round(top[0][1] * 100 / total_lang) if top else 0,
        "lang2_name": top[1][0] if len(top) > 1 else "Python",
        "lang2_pct": round(top[1][1] * 100 / total_lang) if len(top) > 1 else 0,
        "activity": sparkline(fetch_recent_weeks()),
        "pinned_name": "java-roadmap",
        "pinned_stars": max((r["stargazerCount"] for r in repos if r["name"] == "java-roadmap"), default=18),
    }
    json.dump(stats, open("stats.json", "w"), ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    subprocess.run([sys.executable, "build_svg.py"], check=True)


if __name__ == "__main__":
    main()
