#!/usr/bin/env python3
"""Fetch live stats for the profile cards, write stats.json, then rebuild the SVGs.
Runs locally and in GitHub Actions.
  GitHub: commits this year, lines added/removed, repos, stars, followers, top languages,
          contributions by day for the last 12 months, stars of the featured repos
  Habr:   article count, reads, top and latest articles; if Habr does not answer, yesterday's numbers stay
  java-roadmap: modules and lessons from the badges in its README

Token resolution: ACCESS_TOKEN (repo secret) > GH_TOKEN > GITHUB_TOKEN.
Per-repo line counts go to loc.json for debugging."""
import datetime, html, json, os, re, subprocess, sys, time, urllib.error, urllib.request

LOGIN = os.environ.get("PROFILE_LOGIN", "SimakovIgor")
YEAR = int(os.environ.get("PROFILE_YEAR", datetime.date.today().year))
TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
API = "https://api.github.com/graphql"
HABR = "https://habr.com/ru/users/igoresha_s/articles/"
FEATURED = ("pixel-buddy", "java-roadmap")


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
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def fetch_profile():
    q = """query($l:String!,$from:DateTime!,$to:DateTime!,$after:String){
      user(login:$l){ id
        followers{totalCount}
        thisYear: contributionsCollection(from:$from,to:$to){ contributionCalendar{ totalContributions } }
        lastYear: contributionsCollection{ contributionCalendar{ totalContributions
          weeks{ contributionDays{ contributionCount date } } } }
        repositories(first:100, ownerAffiliations:OWNER, isFork:false, after:$after){
          pageInfo{hasNextPage endCursor}
          nodes{ name stargazerCount primaryLanguage{name} } }
      }}"""
    nodes, after, base = [], None, None
    while True:
        d = gql(q, {"l": LOGIN, "from": f"{YEAR}-01-01T00:00:00Z", "to": f"{YEAR}-12-31T23:59:59Z", "after": after})
        u = d["user"]
        base = base or u
        nodes += u["repositories"]["nodes"]
        if not u["repositories"]["pageInfo"]["hasNextPage"]:
            break
        after = u["repositories"]["pageInfo"]["endCursor"]
    return base, nodes


def fetch_loc(user_id, repos):
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
                    ra += c["additions"]
                    rd += c["deletions"]
                if not h["pageInfo"]["hasNextPage"]:
                    break
                after = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"  loc {name}: {e}", file=sys.stderr)
        per_repo[name] = {"add": ra, "del": rd}
        added += ra
        removed += rd
    json.dump(per_repo, open("loc.json", "w"), indent=2)
    return added, removed


def views(s):
    s = s.strip().replace(",", ".")
    mult = {"K": 1_000, "M": 1_000_000}.get(s[-1:].upper(), 1)
    return round(float(s.rstrip("KkMm")) * mult)


def fetch_habr(prev):
    try:
        req = urllib.request.Request(HABR, headers={"User-Agent": "Mozilla/5.0 (profile card)"})
        page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except Exception as e:
        print(f"habr: {e}, keeping previous numbers", file=sys.stderr)
        return prev
    arts = []
    for block in page.split("<article")[1:]:
        link = re.search(r'href="([^"]*/articles/\d+/)"', block)
        title = re.search(r'tm-title__link[^>]*>\s*<span>(.*?)</span>', block, re.S)
        count = re.search(r'tm-icon-counter__value[^>]*>([^<]+)<', block)
        if link and title and count:
            arts.append(dict(url="https://habr.com" + link.group(1),
                             title=html.unescape(title.group(1)).strip(), views=views(count.group(1))))
    if not arts:
        print("habr: no articles parsed, keeping previous numbers", file=sys.stderr)
        return prev
    return dict(articles=len(arts), reads=sum(a["views"] for a in arts), latest=arts[0],
                top=sorted(arts, key=lambda a: -a["views"])[:4])


def fetch_roadmap(prev):
    q = """query($o:String!){ repository(owner:$o, name:"java-roadmap"){
      object(expression:"HEAD:README.md"){ ... on Blob{ text } } } }"""
    try:
        text = gql(q, {"o": LOGIN})["repository"]["object"]["text"]
        modules = re.search(r"модулей-(\d+)", text)
        lessons = re.search(r"уроков-(\d+)", text)
        return dict(modules=int(modules.group(1)), lessons=int(lessons.group(1)))
    except Exception as e:
        print(f"roadmap: {e}, keeping previous numbers", file=sys.stderr)
        return prev


def main():
    if not TOKEN:
        sys.exit("no token (set ACCESS_TOKEN / GH_TOKEN)")
    prev = json.load(open("stats.json")) if os.path.exists("stats.json") else {}
    user, repos = fetch_profile()
    langs = {}
    for r in repos:
        if r.get("primaryLanguage"):
            langs[r["primaryLanguage"]["name"]] = langs.get(r["primaryLanguage"]["name"], 0) + 1
    total_lang = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:2]
    added, removed = fetch_loc(user["id"], repos)
    last = user["lastYear"]["contributionCalendar"]
    stats = {
        "year": YEAR,
        "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "repos": len(repos),
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": user["followers"]["totalCount"],
        "commits": user["thisYear"]["contributionCalendar"]["totalContributions"],
        "added": added,
        "removed": removed,
        "net": added - removed,
        "langs": [[n, round(c * 100 / total_lang)] for n, c in top],
        "contributions": last["totalContributions"],
        "since": last["weeks"][0]["contributionDays"][0]["date"],
        "days": [[d["contributionCount"] for d in w["contributionDays"]] for w in last["weeks"]],
        "featured": {r["name"]: {"stars": r["stargazerCount"],
                                 "lang": (r.get("primaryLanguage") or {}).get("name", "")}
                     for r in repos if r["name"] in FEATURED},
        "roadmap": fetch_roadmap(prev.get("roadmap")),
        "habr": fetch_habr(prev.get("habr")),
    }
    json.dump(stats, open("stats.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k != "days"}, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, "build_svg.py"], check=True)


if __name__ == "__main__":
    main()
