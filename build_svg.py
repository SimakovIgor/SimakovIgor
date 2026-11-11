#!/usr/bin/env python3
"""Profile cards -> self-contained SVGs (render inside <img> on GitHub), dark and light.
  dark.svg / light.svg            hero: a year of contributions as a 3D city, live GitHub stats, who I am
  cards/buddy-*.svg               pixel-buddy
  cards/habr-*.svg                Habr articles and reads
  cards/roadmap-*.svg             java-roadmap
  cards/contact-*.svg             contact buttons for Say hi
Numbers come from stats.json (today.py). Text is visible without animation; motion only
adds to it and stops under prefers-reduced-motion. Standard library only."""
import datetime, html, json, math, os, re

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

PAL = {
    "dark": dict(card="#14111c", card2="#191521", border="#2a2434", ink="#ece6f3", dim="#a39bb3",
                 faint="#6d6680", accent="#f2adc0", accent2="#c3b1de", num="#e9a86b", ok="#7fd6a9",
                 tile="#221d2c", side1=0.28, side2=0.45,
                 lv=["#4a3f63", "#7a62a6", "#b88fd0", "#f2adc0"], sheen=0.10,
                 hl="#ffc9da", tip="#ece6f3", merged="#8957e5", add="#3fb950", rem="#f85149"),
    "light": dict(card="#fbf7f4", card2="#f4ecee", border="#e6d8dd", ink="#241d29", dim="#6c6172",
                  faint="#9d8f9a", accent="#c25e86", accent2="#7a5fb0", num="#b86f22", ok="#2f9e6b",
                  tile="#efe5e9", side1=0.16, side2=0.30,
                  lv=["#d9c9ec", "#b597dc", "#9466c4", "#c25e86"], sheen=0.55,
                  hl="#d0457a", tip="#241d29", merged="#8250df", add="#1a7f37", rem="#cf222e"),
}

CAREER_START = 2016
STATS = json.load(open("stats.json")) if os.path.exists("stats.json") else {}

HABR_SHORT = {
    "814485": "JUnit 5 + Mockito + AssertJ", "1092932": "Полгода не пишем код руками",
    "1041296": "Десять лет писал код руками", "968058": "IN (:ids) и Plan Cache",
    "1039862": "SXSSFWorkbook без dispose()", "1037972": "История одного // todo",
    "1046417": "Переименовал две колонки", "1032902": "GitPulse: метрики команды",
    "1044626": "Black-box тесты на Java",
}

CAT = [["..b.....b.", "..bc...cb.", "s.bbbbbbb.", "s.bebbbeb.", ".scbbmbbc.", "...sbbbs.."],
       ["..b.....b.", "..bc...cb.", "..bbbbbbb.", "..bebbbeb.", "s.cbbmbbc.", ".s.sbbbs.."]]
CAT_PAL = dict(b="#f2a65a", s="#c97b35", e="#1d1b26", c="#ff8fab", m="#5a2a3a")


def esc(s):
    return html.escape(s, quote=True)


def T(x, y, segs, size, weight=400, anchor=None, family=MONO, ls=None, cls=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    c = f' class="{cls}"' if cls else ""
    sp = "".join(f'<tspan fill="{col}">{esc(t)}</tspan>' for t, col in segs)
    return (f'<text{c} x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}"{a}{l} xml:space="preserve">{sp}</text>')


def short(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{round(n / 1_000)}K"
    return str(n)


def pixels(rows, pal, x0, y0, px):
    out = []
    for y, r in enumerate(rows):
        x = 0
        while x < len(r):
            c = r[x]
            if c == ".":
                x += 1
                continue
            e = x
            while e + 1 < len(r) and r[e + 1] == c:
                e += 1
            out.append(f'<rect x="{x0 + x * px:.1f}" y="{y0 + y * px:.1f}" width="{(e - x + 1) * px:.1f}" '
                       f'height="{px:.1f}" fill="{pal[c]}"/>')
            x = e + 1
    return "".join(out)


def svg_open(w, h, label, style):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}"><style>{style}'
            f'@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>')


def frame(p, w, h, title_bar=False):
    o = [f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{p["card"]}" stroke="{p["border"]}"/>']
    if title_bar:
        o.append(f'<path d="M0.5 40.5 V14.5 a14 14 0 0 1 14 -14 H{w - 14.5} a14 14 0 0 1 14 14 V40.5 Z" '
                 f'fill="{p["card2"]}" stroke="{p["border"]}"/>')
    return o


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def city(p, ox, oy, a=4.7, b=3.05, hmax=92):
    weeks = [list(w) for w in (STATS.get("days") or [[0] * 7] * 53)]
    pad = 7 - len(weeks[0])
    weeks[0] = [None] * pad + weeks[0]
    weeks[-1] = weeks[-1] + [None] * (7 - len(weeks[-1]))
    start = datetime.date.fromisoformat(STATS.get("since", "2025-11-09")) - datetime.timedelta(days=pad)
    nz = sorted(c for w in weeks for c in w if c)
    hi = nz[-1] if nz else 1
    qs = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)] if nz else [1, 1, 1]

    def height(c):
        return 2 + math.sqrt(c / hi) * hmax

    cells, last, peak = [], None, None
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            if c is None:
                continue
            cells.append((wi + di, wi, di, c))
            last = (wi, di, c)
            if c and (peak is None or c > peak[2]):
                peak = (wi, di, c)
    o = []
    for _, wi, di, c in sorted(cells):
        x, y = ox + (wi - di) * a, oy + (wi + di) * b
        o.append(f'<path d="M{x:.1f} {y:.1f}l{a} {b}l{-a} {b}l{-a} {-b}z" fill="{p["tile"]}"/>')
        if not c:
            continue
        top = p["lv"][sum(c > q for q in qs)]
        h = height(c)
        o.append(f'<g class="rise" style="animation-delay:{0.35 + wi * 0.028:.2f}s">'
                 f'<path d="M{x - a:.1f} {y + b - h:.1f}l{a} {b}v{h:.1f}l{-a} {-b}z" fill="{mix(top, "#000000", p["side1"])}"/>'
                 f'<path d="M{x:.1f} {y + 2 * b - h:.1f}l{a} {-b}v{h:.1f}l{-a} {b}z" fill="{mix(top, "#000000", p["side2"])}"/>'
                 f'<path d="M{x:.1f} {y - h:.1f}l{a} {b}l{-a} {b}l{-a} {-b}z" fill="{top}"/></g>')

    ang = math.degrees(math.atan2(b, a))
    firsts = [wi for wi in range(1, len(weeks)) if (start + datetime.timedelta(days=7 * wi)).day <= 7]
    for wi in firsts[::2]:
        d = start + datetime.timedelta(days=7 * wi)
        x, y = ox + (wi - 7) * a - 7, oy + (wi + 7) * b + 15
        o.append(f'<text transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})" font-family="{MONO}" font-size="9.5" '
                 f'fill="{p["faint"]}">{d.strftime("%b")}</text>')

    late = []
    if peak:
        wi, di, c = peak
        x, y = ox + (wi - di) * a, oy + (wi + di) * b - height(c)
        ty = 78
        when = start + datetime.timedelta(days=7 * wi + di)
        day = f"{when.day} {when:%b}"
        label = [("peak ", p["faint"]), (str(c), p["num"]), (f" · {day}", p["faint"])]
        lw = sum(len(t) for t, _ in label) * 6.6
        anchor_end = x + 6 + lw > 316
        late.append(f'<path d="M{x:.1f} {y - 3:.1f} V{ty + 5}" stroke="{p["faint"]}" stroke-dasharray="1.5 2.5"/>'
                    f'<circle cx="{x:.1f}" cy="{y - 3:.1f}" r="1.8" fill="{p["num"]}"/>')
        late.append(T(x - 6 if anchor_end else x + 6, ty + 4, label, 11, anchor="end" if anchor_end else None))
    if last:
        wi, di, c = last
        x, y = ox + (wi - di) * a, oy + (wi + di) * b + b - (height(c) if c else 0)
        late.append(f'<circle class="pulse" cx="{x:.1f}" cy="{y - 7:.1f}" r="3" fill="{p["ok"]}"/>')
    o.append(f'<g class="late">{"".join(late)}</g>')
    return "".join(o)


def merged_bar(p, W):
    o = [f'<rect x="14" y="9" width="84" height="23" rx="11.5" fill="{p["merged"]}"/>'
         f'<g transform="translate(24 12.5)" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round">'
         f'<circle cx="3" cy="2.5" r="1.9"/><circle cx="3" cy="13.5" r="1.9"/><circle cx="11" cy="8" r="1.9"/>'
         f'<path d="M3 4.4V11.6M3 4.6C3 7 5.5 8 9.1 8"/></g>',
         T(42, 25, [("Merged", "#ffffff")], 12, 600, family=SANS)]
    sent = [("SimakovIgor", p["ink"]), (" merged ", p["dim"]),
            (f"{STATS.get('commits', 0):,} commits", p["num"]), (" into ", p["dim"])]
    o.append(T(112, 25, sent, 12))
    cx = 112 + sum(len(t) for t, _ in sent) * 7.22 - 2
    o.append(f'<rect x="{cx:.0f}" y="11" width="40" height="19" rx="6" fill="{p["accent2"]}" opacity="0.16"/>')
    o.append(T(cx + 20, 24.5, [("main", p["accent2"])], 11.5, anchor="middle"))
    add, rem = STATS.get("added", 0), STATS.get("removed", 0)
    green = round(5 * add / max(add + rem, 1))
    bx = W - 72
    o += [f'<rect x="{bx + i * 10}" y="16.5" width="8" height="8" rx="1.5" fill="{p["add"] if i < green else p["rem"]}"/>'
          for i in range(5)]
    diff = [(f"+{add:,}", p["add"]), (f" −{rem:,}", p["rem"])]
    o.append(T(bx - 10, 25, diff, 11.5, 600, anchor="end"))
    upd = f"updated {STATS.get('built', '')}"
    ux = bx - 10 - sum(len(t) for t, _ in diff) * 6.9 - 22
    o.append(T(ux, 25, [(upd, p["faint"])], 11, anchor="end"))
    o.append(f'<circle class="pulse" cx="{ux - len(upd) * 6.6 - 10:.0f}" cy="20.5" r="3.5" fill="{p["ok"]}"/>')
    return o


def hero(p):
    W, H = 840, 500
    years = int(STATS.get("built", "2026")[:4]) - CAREER_START
    habr = STATS.get("habr") or {}
    style = (f'.pulse{{animation:pulse 2.2s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:1}}65%{{opacity:.25}}}}'
             f'.rise{{transform-box:fill-box;transform-origin:50% 100%;animation:rise .8s cubic-bezier(.2,.9,.25,1) both}}'
             f'@keyframes rise{{from{{transform:scaleY(0)}}}}'
             f'.late{{animation:late .4s ease-out 2.2s both}}@keyframes late{{from{{opacity:0}}}}')
    o = [svg_open(W, H, "Igor Simakov, Java backend lead: a year of contributions, live GitHub stats and what I do", style)]
    o += frame(p, W, H, title_bar=True)
    o += merged_bar(p, W)

    o.append(city(p, ox=56, oy=120))
    L, LV = 26, 104
    o.append(T(L, 344, [(f"{STATS.get('contributions', 0):,}", p["num"])], 26, 700, family=SANS))
    o.append(T(L, 364, [("contributions in the last 12 months", p["dim"])], 11.5))
    langs = " · ".join(f"{n} {v}%" for n, v in STATS.get("langs", []))
    stat_rows = [
        ("COMMITS", [(f"{STATS.get('commits', 0):,}", p["num"]), (f" in {STATS.get('year', '')}", p["faint"])]),
        ("LINES", [(f"+{STATS.get('added', 0):,}", p["num"]), (" / ", p["faint"]),
                   (f"−{STATS.get('removed', 0):,}", p["num"])]),
        ("NET", [(f"{STATS.get('net', 0):+,}".replace("-", "−"), p["num"]),
                 (f" across {STATS.get('repos', 0)} repos", p["faint"])]),
        ("GITHUB", [(f"{STATS.get('stars', 0)}", p["num"]), (" stars · ", p["faint"]),
                    (f"{STATS.get('followers', 0)}", p["num"]), (" followers", p["faint"])]),
        ("LANGS", [(langs, p["ink"])]),
    ]
    for i, (lab, val) in enumerate(stat_rows):
        y = 396 + i * 21
        o.append(T(L, y, [(lab, p["accent2"])], 10, 600, ls="1.4"))
        o.append(T(LV, y, val, 12.5))

    o.append(f'<path d="M324.5 64 V{H - 24}" stroke="{p["border"]}"/>')
    X, V = 348, 426
    o.append(T(X, 90, [("Igor Simakov", p["ink"])], 30, 700, family=SANS))
    o.append(T(X, 118, [("Java backend lead", p["accent"]), (f" · {years} years in production", p["dim"])], 15))
    rows = [
        ("WORK", [("marketplace fulfillment @ ", p["ink"]), ("Uzum Market", p["accent"])]),
        ("STACK", [("Java 21 · Spring · Kafka · PostgreSQL · K8s", p["ink"])]),
        ("BUILD", [("pixel-buddy", p["accent"]), (" · a pet for Claude Code", p["ink"])]),
        ("WRITE", [(str(habr.get("articles", 9)), p["num"]), (" articles on Habr · ", p["ink"]),
                   (short(habr.get("reads", 92000)), p["num"]), (" reads", p["ink"])]),
        ("MENTOR", [("21", p["num"]), (" mentees on OpenMentor", p["ink"])]),
        ("REACH", [("@igoresha_simakov", p["ink"]), (" · ", p["faint"]), ("Simakoff10@mail.ru", p["ink"])]),
    ]
    for i, (lab, val) in enumerate(rows):
        y = 184 + i * 48
        o.append(T(X, y, [(lab, p["accent2"])], 10.5, 600, ls="1.6"))
        o.append(T(V, y, val, 13.5))

    o.append("</svg>")
    return "".join(o)


def card_head(p, w, h, label, title=None):
    o = frame(p, w, h)
    o.append(T(18, 28, [(label, p["accent2"])], 10, 600, ls="1.4"))
    if title:
        o.append(T(18, 54, [(title, p["ink"])], 18, 700, family=SANS))
    return o


def card_buddy(p):
    w, h = 272, 168
    repo = (STATS.get("featured") or {}).get("pixel-buddy") or {}
    style = ('.walk{animation:walk 7s linear infinite}@keyframes walk{80%,100%{transform:translateX(178px)}}'
             '.f0{animation:f0 .5s steps(1) infinite}@keyframes f0{50%{opacity:0}}'
             '.f1{opacity:0;animation:f1 .5s steps(1) infinite}@keyframes f1{50%{opacity:1}}')
    o = [svg_open(w, h, "pixel-buddy, a pixel pet for Claude Code", style)]
    o += card_head(p, w, h, "CLAUDE CODE MOD", "pixel-buddy")
    o.append(T(18, 76, [("A pixel pet in your footer.", p["dim"])], 12))
    o.append(T(18, 93, [("Ship code, feed your buddy.", p["dim"])], 12))
    o.append(f'<path d="M18 133.5 H254" stroke="{p["border"]}" stroke-dasharray="2 3"/>')
    o.append('<rect x="232" y="125" width="8" height="8" rx="2" fill="#d9a066"/>'
             '<rect x="234" y="127" width="2" height="2" fill="#6b3f1f"/><rect x="237" y="129" width="2" height="2" fill="#6b3f1f"/>')
    o.append(f'<g transform="translate(18 112)"><g class="walk">'
             f'<g class="f0" shape-rendering="crispEdges">{pixels(CAT[0], CAT_PAL, 0, 0, 3.5)}</g>'
             f'<g class="f1" shape-rendering="crispEdges">{pixels(CAT[1], CAT_PAL, 0, 0, 3.5)}</g></g></g>')
    o.append(T(18, 156, [(f"★ {repo.get('stars', 0)}", p["num"]), (f"  ·  {repo.get('lang', '')}", p["faint"])], 11.5))
    o.append(T(254, 156, [("install →", p["accent"])], 11.5, anchor="end"))
    o.append("</svg>")
    return "".join(o)


def card_habr(p):
    w, h = 272, 168
    habr = STATS.get("habr") or {}
    o = [svg_open(w, h, "Articles on Habr", "")]
    o += card_head(p, w, h, f"HABR · {habr.get('articles', 9)} ARTICLES · {short(habr.get('reads', 92000))} READS")
    top = list(habr.get("top") or [])[:4]
    latest = habr.get("latest")
    if latest and latest["url"] not in [a["url"] for a in top]:
        top = top[:3] + [dict(latest, new=True)]
    for i, a in enumerate(top):
        y = 56 + i * 23
        o.append(T(18, y, [(short_title(a, 22 if a.get("new") else 27), p["ink"])], 12))
        if a.get("new"):
            o.append(f'<rect x="{190}" y="{y - 11}" width="30" height="15" rx="4" fill="{p["accent"]}" opacity="0.18"/>')
            o.append(T(205, y, [("new", p["accent"])], 10, 600, anchor="middle"))
        o.append(T(254, y, [(short(a["views"]), p["num"])], 12, anchor="end"))
        if i < 3:
            o.append(f'<path d="M18 {y + 8.5} H254" stroke="{p["border"]}"/>')
    o.append(T(18, 156, [("RU · tests, ORM, AI", p["faint"])], 11.5))
    o.append(T(254, 156, [("read →", p["accent"])], 11.5, anchor="end"))
    o.append("</svg>")
    return "".join(o)


def short_title(a, limit):
    known = HABR_SHORT.get(a["url"].rstrip("/").rsplit("/", 1)[-1])
    if known and len(known) <= limit:
        return known
    t = re.split(r"[.:!?]\s", a["title"])[0]
    if len(t) <= limit:
        return t
    cut = t[:limit - 1].rsplit(" ", 1)[0].rstrip(",;—-")
    return cut + "…"


def card_roadmap(p):
    w, h = 272, 168
    stars = ((STATS.get("featured") or {}).get("java-roadmap") or {}).get("stars", 0)
    lessons = (STATS.get("roadmap") or {}).get("lessons")
    xs, labs = [34, 96, 160, 222], ["Core", "Hibernate", "Spring", "Reliability"]
    L = xs[-1] - xs[0]
    style = f'.draw{{animation:draw 1.6s ease-out .3s both}}@keyframes draw{{from{{stroke-dashoffset:{L}}}to{{stroke-dashoffset:0}}}}'
    o = [svg_open(w, h, "java-roadmap, from first class to production", style)]
    o += card_head(p, w, h, "FOR JUNIORS · IN RUSSIAN", "java-roadmap")
    o.append(T(18, 76, [("From first class to production.", p["dim"])], 12))
    o.append(f'<path d="M{xs[0]} 104.5 H{xs[-1]}" stroke="{p["border"]}" stroke-width="2"/>')
    o.append(f'<path class="draw" d="M{xs[0]} 104.5 H{xs[-1]}" stroke="{p["accent"]}" stroke-width="2" '
             f'stroke-dasharray="{L}" stroke-dashoffset="0"/>')
    for i, (x, l) in enumerate(zip(xs, labs)):
        o.append(f'<circle cx="{x}" cy="104.5" r="5" fill="{p["card"]}" stroke="{p["accent"] if i < 3 else p["num"]}" stroke-width="2"/>')
        o.append(T(x, 126, [(l, p["dim"])], 10.5, anchor="middle"))
    o.append(T(18, 156, [(f"★ {stars}", p["num"]), (f"  ·  {lessons} lessons" if lessons else "", p["faint"])], 11.5))
    o.append(T(254, 156, [("open →", p["accent"])], 11.5, anchor="end"))
    o.append("</svg>")
    return "".join(o)


CONTACTS = [
    ("tg", "Telegram", "@igoresha_simakov", "#2AABEE",
     '<path d="M7.6 12.1 16.9 8.3c.5-.2.9.1.8.6l-1.6 7.6c-.1.5-.6.6-1 .4l-2.6-1.9-1.3 1.2c-.1.1-.3.2-.5.2l.2-2.6 4.7-4.3c.2-.2 0-.3-.3-.1l-5.8 3.7-2.5-.8c-.5-.2-.5-.5.1-.7z" fill="#fff"/>'),
    ("mail", "Email", "Simakoff10@mail.ru", "#E9A86B",
     '<rect x="6.5" y="8" width="11" height="8" rx="1.6" fill="none" stroke="#fff" stroke-width="1.5"/>'
     '<path d="M7 9l5 3.6L17 9" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'),
    ("in", "LinkedIn", "igor-simakov", "#0A66C2",
     '<rect x="7.2" y="10.2" width="2.2" height="6.6" fill="#fff"/><circle cx="8.3" cy="7.9" r="1.3" fill="#fff"/>'
     '<path d="M11.2 10.2h2.1v1c.4-.7 1.2-1.2 2.3-1.2 1.8 0 2.5 1.1 2.5 3v3.8h-2.2v-3.4c0-.9-.3-1.5-1.1-1.5s-1.4.6-1.4 1.5v3.4h-2.2z" fill="#fff"/>'),
    ("mentor", "Mentoring", "21 on OpenMentor", "#9466C4",
     '<path d="M12 7l6.5 3.2L12 13.4 5.5 10.2z" fill="#fff"/><path d="M8.3 11.8v2.6c0 .9 1.7 2 3.7 2s3.7-1.1 3.7-2v-2.6L12 13.6z" fill="#fff"/>'
     '<path d="M18.5 10.2v3.4" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/>'),
]


def card_contact(p, idx):
    key, title, handle, brand, icon = CONTACTS[idx]
    w, h = 196, 54
    style = (f'.sh{{transform:translateX(-90px);animation:sh 7s ease-in-out {0.6 + idx * 0.22:.2f}s infinite}}'
             f'@keyframes sh{{0%{{transform:translateX(-90px)}}18%,100%{{transform:translateX({w + 40}px)}}}}')
    o = [svg_open(w, h, f"{title}: {handle}", style)]
    o.append(f'<defs><clipPath id="r"><rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12"/></clipPath>'
             f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="#fff" stop-opacity="{p["sheen"]}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p["accent2"]}" stop-opacity="0.55"/>'
             f'<stop offset="1" stop-color="{p["accent"]}" stop-opacity="0.55"/></linearGradient></defs>')
    o.append(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{p["card"]}" stroke="url(#b)"/>')
    o.append(f'<g transform="translate(13 12)"><rect width="30" height="30" rx="9" fill="{brand}"/>'
             f'<g transform="translate(3 3)">{icon}</g></g>')
    o.append(T(54, 24, [(title, p["ink"])], 13.5, 700, family=SANS))
    o.append(T(54, 41, [(handle, p["dim"])], 10.8))
    o.append(f'<g clip-path="url(#r)"><g transform="skewX(-20)"><rect class="sh" x="0" y="-20" width="46" '
             f'height="{h + 40}" fill="url(#g)"/></g></g>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    os.makedirs("cards", exist_ok=True)
    for theme, p in PAL.items():
        out = {f"{theme}.svg": hero(p),
               f"cards/buddy-{theme}.svg": card_buddy(p),
               f"cards/habr-{theme}.svg": card_habr(p),
               f"cards/roadmap-{theme}.svg": card_roadmap(p)}
        out.update({f"cards/contact-{c[0]}-{theme}.svg": card_contact(p, i) for i, c in enumerate(CONTACTS)})
        for path, svg in out.items():
            open(path, "w").write(svg)
            print("wrote", path)
