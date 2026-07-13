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
try:
    TOOLS = json.load(open("tools.json"))     # [[name, inner_svg], ...]
except FileNotFoundError:
    TOOLS = []

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
                 shadow="#050409", shadow_op=0.5,
                 csh="#030206", csh_op=0.5, lift_col="#000000", lift_op=0.55,
                 vmin=0.60, vmax=1.0, smul=1.05),
    "light": dict(card="#fbf7f4", card2="#f4ecee", border="#e6d8dd",
                  ink="#241d29", dim="#6c6172", faint="#a99ba6",
                  accent="#c25e86", accent2="#7a5fb0", num="#c07a2e",
                  ok="#2f9e6b", bad="#d64a3e", baron="#c25e86", baroff="#e6d8dd",
                  shadow="#7a5fb0", shadow_op=0.20,
                  csh="#6a4f96", csh_op=0.22, lift_col="#2a2233", lift_op=0.30,
                  vmin=0.0, vmax=0.60, smul=1.15),
}

M = 30
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
    ICON, IGAP = 27, 17
    tools_w = len(TOOLS) * ICON + (len(TOOLS) - 1) * IGAP if TOOLS else 0
    tools_band = 68 if TOOLS else 0
    W = int(max(ascii_x + ascii_w, fetch_x + fetch_w, tools_w + 2 * (M + PAD_L)) + PAD_R + M)
    H = int(body_top + content_h + PAD_R + M) + tools_band
    line_w = ncur * FCW

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">']
    o.append(
        f'<defs>'
        f'<filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="13"/></filter>'
        f'<filter id="fea" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4.5"/></filter>'
        f'<filter id="cg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.2"/></filter>'
        f'<filter id="csh" x="-120%" y="-160%" width="340%" height="420%"><feGaussianBlur stdDeviation="5.5"/></filter>'
        f'<filter id="lift" x="-25%" y="-25%" width="155%" height="170%">'
        f'<feGaussianBlur in="SourceAlpha" stdDeviation="3.2"/>'
        f'<feOffset dx="2" dy="4.5" result="s"/>'
        f'<feFlood flood-color="{p["lift_col"]}" flood-opacity="{p["lift_op"]}"/>'
        f'<feComposite in2="s" operator="in"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<mask id="feather" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="16" fill="#fff" filter="url(#fea)"/></mask>'
        f'<style>'
        f'.type{{animation:type 1.7s steps({ncur},end) .45s both}}'
        f'@keyframes type{{from{{clip-path:inset(-3px 101% -3px -3px)}}to{{clip-path:inset(-3px -3px -3px -3px)}}}}'
        f'.tcur{{animation:tmove 1.7s steps({ncur},end) .45s both,blink 1.05s steps(1) 2.15s infinite}}'
        f'@keyframes tmove{{from{{transform:translateX(-{line_w:.0f}px)}}to{{transform:translateX(0)}}}}'
        f'.pulse{{animation:pulse 2.2s ease-in-out infinite}}'
        f'@keyframes blink{{50%{{opacity:0}}}}@keyframes pulse{{0%,100%{{opacity:1}}65%{{opacity:.25}}}}'
        f'.bob{{animation:bob 2.4s ease-in-out infinite;transform-origin:center;transform-box:fill-box}}'
        f'@keyframes bob{{0%,100%{{transform:translateY(0) rotate(-.4deg)}}50%{{transform:translateY(-2px) rotate(.4deg)}}}}'
        f'.legL{{animation:stepL 2.4s ease-in-out infinite}}'
        f'.legR{{animation:stepR 2.4s ease-in-out infinite}}'
        f'@keyframes stepL{{0%,100%{{transform:translate(-1.6px,0)}}25%{{transform:translate(1.8px,-2.6px)}}50%{{transform:translate(-1.6px,0)}}}}'
        f'@keyframes stepR{{0%,50%{{transform:translate(-1.6px,0)}}75%{{transform:translate(1.8px,-2.6px)}}100%{{transform:translate(-1.6px,0)}}}}'
        f'.csh{{animation:csh 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}'
        f'@keyframes csh{{0%,100%{{opacity:1;transform:scaleX(1)}}50%{{opacity:.6;transform:scaleX(.8)}}}}'
        f'@media(prefers-reduced-motion:reduce){{.type,.tcur,.bob,.legL,.legR,.csh{{animation:none;transform:none;clip-path:none}}.pulse{{animation:none}}}}'
        f'</style></defs>')

    cx, cy, cw, ch = M, M, W - 2 * M, H - 2 * M
    # soft shadow halo — melts the card into the page background
    o.append(f'<rect x="{cx}" y="{cy+4}" width="{cw}" height="{ch}" rx="18" fill="{p["shadow"]}" opacity="{p["shadow_op"]}" filter="url(#soft)"/>')
    # feathered panel — edges fade instead of a hard rectangle
    o.append('<g mask="url(#feather)">')
    o.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16" fill="{p["card"]}"/>')
    o.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16" fill="none" stroke="{p["border"]}" stroke-opacity="0.7"/>')
    o.append(f'<path d="M{cx},{cy+16} a16,16 0 0 1 16,-16 h{cw-32} a16,16 0 0 1 16,16 v{TITLE_H-16} h-{cw} z" fill="{p["card2"]}"/>')
    o.append(f'<line x1="{cx}" y1="{cy+TITLE_H}" x2="{cx+cw}" y2="{cy+TITLE_H}" stroke="{p["border"]}"/>')
    o.append('</g>')
    ty = cy + TITLE_H / 2
    for i, col in enumerate(["#ec6a5e", "#f4bf4f", "#61c554"]):
        o.append(f'<circle cx="{cx+22+i*18}" cy="{ty}" r="6" fill="{col}"/>')
    o.append(T(cx + cw / 2, ty + 4.5, [("simakov@bali", p["ink"]), ("  : ~/dev", p["dim"])], 12.5, anchor="middle"))
    built = S("built", "")
    hdr = f"live · updated {built}" if built else "live · rebuilt daily"
    hx = cx + cw - 22
    o.append(T(hx, ty + 4, [(hdr, p["faint"])], 11, anchor="end"))
    o.append(f'<circle class="pulse" cx="{hx - len(hdr) * 6.35 - 11:.0f}" cy="{ty}" r="4" fill="{p["ok"]}"/>')

    # ascii (colored per char) — the "creature" gently bobs as it walks in place,
    # with the two feet (bottom rows, split at the gap between them) stepping alternately.
    def txt(x, cells):
        return f'<text x="{x:.1f}" y="{yy:.1f}" font-size="{AF}" xml:space="preserve">{ascii_tspans(cells, p)}</text>'

    LEG_ROWS = 3                                  # bottom rows that hold the legs/feet
    leg_start = max(0, len(ROWS) - LEG_ROWS)

    def gap_center(r):                            # midpoint of the widest interior space run
        nz = [i for i, c in enumerate(r) if c[0] != " "]
        if len(nz) < 2:
            return None
        lo, hi = nz[0], nz[-1]
        best_len, best_c, run, start = 0, None, 0, lo
        for i in range(lo, hi + 2):
            blank = i <= hi and r[i][0] == " "
            if blank:
                if run == 0:
                    start = i
                run += 1
            else:
                if run > best_len:
                    best_len, best_c = run, (start + i - 1) // 2
                run = 0
        return best_c if best_len >= 2 else None

    seam = next((gc for r in reversed(ROWS[leg_start:]) if (gc := gap_center(r)) is not None), ascii_cols // 2)

    # depth: a soft contact shadow under the feet grounds the walk; the avatar itself
    # gets a cast drop-shadow (url(#lift)) so it reads as a solid object above the panel.
    acx = ascii_x + ascii_w / 2
    feet_y = ascii_dy + len(ROWS) * ALH - 1
    o.append(f'<ellipse class="csh" cx="{acx:.1f}" cy="{feet_y:.1f}" rx="{ascii_w*0.30:.1f}" ry="6.5" fill="{p["csh"]}" fill-opacity="{p["csh_op"]}" filter="url(#csh)"/>')

    o.append('<g class="bob" filter="url(#lift)">')
    legL, legR = [], []
    for i, r in enumerate(ROWS):
        yy = ascii_dy + ALH * (i + 1)
        if i >= leg_start:                        # split this row into left foot / right foot
            legL.append(txt(ascii_x, r[:seam]))
            legR.append(txt(ascii_x + seam * ACW, r[seam:]))
        else:
            o.append(txt(ascii_x, r))
    o.append(f'<g class="legL">{"".join(legL)}</g>')
    o.append(f'<g class="legR">{"".join(legR)}</g>')
    o.append('</g>')
    o.append(T(ascii_x + ascii_w / 2, ascii_dy + len(ROWS) * ALH + 15, [("@SIMAKOVIGOR · BALI", p["faint"])], 10, anchor="middle", ls="2"))

    o.append(f'<g transform="translate({fetch_x:.1f},{fetch_dy:.1f})">')
    o.extend(fops)
    o.append('</g>')
    # cursor: glow + solid block, taller/brighter
    curX = fetch_x + curx; curY = fetch_dy + cury
    o.append(f'<rect class="tcur" x="{curX:.0f}" y="{curY:.0f}" width="{FCW+1:.0f}" height="{FF:.0f}" rx="1" fill="{p["accent"]}" filter="url(#cg)" opacity="0.55"/>')
    o.append(f'<rect class="tcur" x="{curX:.0f}" y="{curY:.0f}" width="{FCW+1:.0f}" height="{FF:.0f}" rx="1" fill="{p["accent"]}"/>')

    # tools band: hairline + inlined tech-stack logos, centered
    if TOOLS:
        div_y = H - M - tools_band + 12
        o.append(f'<line x1="{M+PAD_L}" y1="{div_y}" x2="{W-M-PAD_R}" y2="{div_y}" stroke="{p["border"]}"/>')
        start_x = (W - tools_w) / 2
        icon_y = div_y + (tools_band - 12 - ICON) / 2
        for i, (name, inner) in enumerate(TOOLS):
            x = start_x + i * (ICON + IGAP)
            o.append(f'<svg x="{x:.1f}" y="{icon_y:.1f}" width="{ICON}" height="{ICON}" viewBox="0 0 128 128">{inner}</svg>')

    o.append('</svg>')
    return "\n".join(o)

for theme in ("dark", "light"):
    open(f"{theme}.svg", "w").write(build(theme))
    print("wrote", f"{theme}.svg")
