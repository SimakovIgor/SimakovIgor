#!/usr/bin/env python3
"""simakov@bali neofetch card -> self-contained SVG (renders in <img> on GitHub).
Avatar ASCII is colored per-character from the real avatar pixels. Content is
visible by default; motion (blink + typing) only enhances, never hides."""
import html, json, colorsys

ROWS = json.load(open("face.json"))              # [[ [char, "#hex"|null], ... ], ...]
try:
    STATS = json.load(open("stats.json"))
except FileNotFoundError:
    STATS = {}

def S(k, d):
    return STATS.get(k, d)

EMAIL = S("email", "simakoff30@gmail.com")

def fmt(n):
    return f"{n:,}".replace(",", ",")

def bar_segs(pct, on_col, off_col):
    on = max(1, min(10, round(pct / 10)))
    return [("█" * on, on_col), ("█" * (10 - on), off_col)] if on < 10 else [("█" * 10, on_col)]

PAL = {
    "dark": dict(card="#14111c", card2="#191521", border="#2a2434",
                 ink="#e7e2ef", dim="#9a92ab", faint="#6a6379",
                 accent="#f2adc0", accent2="#c3b1de", num="#e9a86b",
                 ok="#7fd6a9", bad="#ef7a72", baron="#f2adc0", baroff="#2f2838",
                 vmin=0.60, vmax=1.0, smul=1.05),
    "light": dict(card="#fbf7f4", card2="#f4ecee", border="#e6d8dd",
                  ink="#241d29", dim="#6c6172", faint="#a99ba6",
                  accent="#c25e86", accent2="#7a5fb0", num="#c07a2e",
                  ok="#2f9e6b", bad="#d64a3e", baron="#c25e86", baroff="#e6d8dd",
                  vmin=0.0, vmax=0.60, smul=1.15),
}

M = 14
PAD_L, PAD_R = 12, 28
TITLE_H = 44
AF = 9.0
ACW, ALH = AF * 0.60, AF * 1.03
FF = 13.5
FLH = 20.5
FCW = FF * 0.60

ascii_cols = max(len(r) for r in ROWS)
ascii_w = ascii_cols * ACW
ascii_h = len(ROWS) * ALH + 22

def esc(s):
    return html.escape(s, quote=True)

def adj(hexc, p):
    r = int(hexc[1:3], 16) / 255; g = int(hexc[3:5], 16) / 255; b = int(hexc[5:7], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = max(v, p["vmin"])          # dark: raise dark colors so they read on dark bg
    v = min(v, p["vmax"])          # light: cap bright colors so they read on cream
    s = min(1.0, s * p["smul"])
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

def T(x, y, segs, size, weight="400", anchor=None, ls=None, cls=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    c = f' class="{cls}"' if cls else ""
    tspans = "".join(f'<tspan fill="{col}">{esc(t)}</tspan>' for t, col in segs)
    return f'<text{c} x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}"{a}{l} xml:space="preserve">{tspans}</text>'

def ascii_tspans(row, p):
    parts, buf, cur = [], "", "INIT"
    def flush():
        nonlocal buf, cur
        if not buf:
            return
        f = "" if cur is None else f' fill="{cur}"'
        parts.append(f'<tspan{f}>{esc(buf)}</tspan>')
        buf = ""
    for ch, col in row:
        ac = None if col is None else adj(col, p)
        if ac == cur:
            buf += ch
        else:
            flush(); cur = ac; buf = ch
    flush()
    return "".join(parts)

def fetch_ops(p):
    ops, y = [], FF
    XL, XV, XL2, XV2 = 0, 92, 168, 246
    maxr = [0.0]
    def rt(x, n): maxr[0] = max(maxr[0], x + n * FCW)
    def row(k, v, kw=None):
        nonlocal y
        ops.append(T(XL, y, k, FF)); ops.append(T(XV, y, v, FF)); y += FLH
    def sec(label, note=""):
        nonlocal y
        y += 5
        segs = [(label, p["accent2"])] + ([(note, p["faint"])] if note else [])
        ops.append(T(XL, y, segs, 10.5, ls="2")); y += FLH

    ops.append(T(XL, y, [("igor", p["accent"]), ("@", p["faint"]), ("bali", p["accent"])], FF, "600")); rt(XL, 9); y += FLH
    ops.append(T(XL, y, [("────────────────────────────────────────", p["faint"])], FF)); rt(XL, 40); y += FLH

    fields = [
        ("role", [("Tech / Team Lead", p["accent"]), (" · Mentor", p["ink"])], 24),
        ("company", [("Uzum.uz", p["ink"])], 7),
        ("email", [(EMAIL, p["ink"])], len(EMAIL)),
        ("location", [("Bali", p["ink"]), ("   ·   UTC+8", p["faint"])], 16),
        ("uptime", [("10", p["num"]), (" yrs in IT", p["faint"])], 12),
        ("editor", [("IntelliJ IDEA", p["ink"]), (" · ", p["faint"]), ("Claude Code", p["ink"])], 27),
    ]
    for k, v, n in fields:
        row([(k, p["dim"])], v); rt(XV, n)

    l1n, l1p = S("lang1_name", "Java"), S("lang1_pct", 81)
    l2n, l2p = S("lang2_name", "Python"), S("lang2_pct", 6)
    sec("S T A C K")
    row([(l1n, p["dim"])], bar_segs(l1p, p["baron"], p["baroff"]) + [(f"  {l1p}%", p["num"])]); rt(XV, 14)
    row([(l2n, p["dim"])], bar_segs(l2p, p["baron"], p["baroff"]) + [(f"  {l2p}%", p["num"])]); rt(XV, 14)
    row([("focus", p["dim"])], [("Spring · Microservices · DDD", p["ink"])]); rt(XV, 28)

    added, removed = S("added", 512880), S("removed", 76902)
    net, repos = S("net", added - removed), S("repos", 27)
    commits = S("commits", 2155)
    lines_v = [(f"+{added:,}", p["ok"]), (" / ", p["faint"]), (f"−{removed:,}", p["bad"])]
    netstr = f"+{net:,}" if net >= 0 else f"−{abs(net):,}"
    sec("C O D E", "   — auto · rebuilt daily")
    row([("commits", p["dim"])], [(f"{commits:,}", p["num"]), (" this year", p["faint"])]); rt(XV, len(f"{commits:,}") + 10)
    row([("lines", p["dim"])], lines_v); rt(XV, len(f"+{added:,}") + len(f"−{removed:,}") + 3)
    row([("net", p["dim"])], [(netstr, p["ok"] if net >= 0 else p["bad"]), (f" across {repos} repos", p["faint"])]); rt(XV, len(netstr) + len(f" across {repos} repos"))
    row([("activity", p["dim"])], [(S("activity", "▁▂▃▅▂▄▆█▅▃▄▆▇█▆▄▂▃▅▇█▆▄▃▂▄▅"), p["ok"])]); rt(XV, 27)

    stars, followers = S("stars", 53), S("followers", 10)
    pinned, pstars = S("pinned_name", "java-roadmap"), S("pinned_stars", 18)
    sec("G I T H U B")
    ops.append(T(XL, y, [("repos", p["dim"])], FF)); ops.append(T(XV, y, [(str(repos), p["num"])], FF))
    ops.append(T(XL2, y, [("stars", p["dim"])], FF)); ops.append(T(XV2, y, [(str(stars), p["num"])], FF)); rt(XV2, 5); y += FLH
    ops.append(T(XL, y, [("followers", p["dim"])], FF)); ops.append(T(XV, y, [(str(followers), p["num"])], FF))
    ops.append(T(XL2, y, [("pinned", p["dim"])], FF)); ops.append(T(XV2, y, [(f"{pinned} ", p["ink"]), (f"★{pstars}", p["num"])], FF)); rt(XV2, len(pinned) + len(str(pstars)) + 2); y += FLH

    y += 9
    prompt = 'git commit -m "another day in paradise"'
    full = "➜ ~/dev " + prompt
    ncur = len(full)
    ops.append(T(XL, y, [("➜", p["ok"]), (" ~/dev ", p["dim"]), (prompt, p["ink"])], FF, cls="type"))
    rt(XL, ncur + 1)
    cur = (XL + ncur * FCW, y - FF + 1, ncur)
    return ops, maxr[0], y + 6, cur

def build(theme):
    p = PAL[theme]
    fops, fetch_w, fetch_h, (curx, cury, ncur) = fetch_ops(p)
    content_h = max(ascii_h, fetch_h)
    ascii_x = M + PAD_L
    fetch_x = ascii_x + ascii_w + 30
    body_top = M + TITLE_H + 24
    ascii_dy = body_top + max(0, (content_h - ascii_h) / 2)
    fetch_dy = body_top + max(0, (content_h - fetch_h) / 2)
    W = int(max(ascii_x + ascii_w, fetch_x + fetch_w) + PAD_R + M)
    H = int(body_top + content_h + PAD_R + M)
    line_w = ncur * FCW

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">']
    o.append(
        f'<defs>'
        f'<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="22" flood-color="{p["accent"]}" flood-opacity="0.18"/></filter>'
        f'<filter id="cg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.2"/></filter>'
        f'<style>'
        f'.type{{animation:type 1.7s steps({ncur},end) .45s both}}'
        f'@keyframes type{{from{{clip-path:inset(-3px 101% -3px -3px)}}to{{clip-path:inset(-3px -3px -3px -3px)}}}}'
        f'.tcur{{animation:tmove 1.7s steps({ncur},end) .45s both,blink 1.05s steps(1) 2.15s infinite}}'
        f'@keyframes tmove{{from{{transform:translateX(-{line_w:.0f}px)}}to{{transform:translateX(0)}}}}'
        f'.pulse{{animation:pulse 2.2s ease-in-out infinite}}'
        f'@keyframes blink{{50%{{opacity:0}}}}@keyframes pulse{{0%,100%{{opacity:1}}65%{{opacity:.25}}}}'
        f'@media(prefers-reduced-motion:reduce){{.type,.tcur{{animation:none;transform:none;clip-path:none}}.pulse{{animation:none}}}}'
        f'</style></defs>')

    cx, cy, cw, ch = M, M, W - 2 * M, H - 2 * M
    o.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16" fill="{p["card"]}" stroke="{p["border"]}" filter="url(#sh)"/>')
    o.append(f'<path d="M{cx},{cy+16} a16,16 0 0 1 16,-16 h{cw-32} a16,16 0 0 1 16,16 v{TITLE_H-16} h-{cw} z" fill="{p["card2"]}"/>')
    o.append(f'<line x1="{cx}" y1="{cy+TITLE_H}" x2="{cx+cw}" y2="{cy+TITLE_H}" stroke="{p["border"]}"/>')
    ty = cy + TITLE_H / 2
    for i, col in enumerate(["#ec6a5e", "#f4bf4f", "#61c554"]):
        o.append(f'<circle cx="{cx+22+i*18}" cy="{ty}" r="6" fill="{col}"/>')
    o.append(T(cx + cw / 2, ty + 4.5, [("simakov@bali", p["ink"]), ("  : ~/dev", p["dim"])], 12.5, anchor="middle"))
    o.append(f'<circle class="pulse" cx="{cx+cw-152}" cy="{ty}" r="4" fill="{p["ok"]}"/>')
    o.append(T(cx + cw - 140, ty + 4, [("live · rebuilt daily", p["faint"])], 11))

    # ascii (colored per char)
    for i, r in enumerate(ROWS):
        o.append(f'<text x="{ascii_x:.1f}" y="{ascii_dy+ALH*(i+1):.1f}" font-size="{AF}" xml:space="preserve">{ascii_tspans(r, p)}</text>')
    o.append(T(ascii_x + ascii_w / 2, ascii_dy + len(ROWS) * ALH + 15, [("@SIMAKOVIGOR · BALI", p["faint"])], 10, anchor="middle", ls="2"))

    o.append(f'<g transform="translate({fetch_x:.1f},{fetch_dy:.1f})">')
    o.extend(fops)
    o.append('</g>')
    # cursor: glow + solid block, taller/brighter
    curX = fetch_x + curx; curY = fetch_dy + cury
    o.append(f'<rect class="tcur" x="{curX:.0f}" y="{curY:.0f}" width="{FCW+1:.0f}" height="{FF:.0f}" rx="1" fill="{p["accent"]}" filter="url(#cg)" opacity="0.55"/>')
    o.append(f'<rect class="tcur" x="{curX:.0f}" y="{curY:.0f}" width="{FCW+1:.0f}" height="{FF:.0f}" rx="1" fill="{p["accent"]}"/>')

    o.append('</svg>')
    return "\n".join(o)

for theme in ("dark", "light"):
    open(f"{theme}.svg", "w").write(build(theme))
    print("wrote", f"{theme}.svg")
