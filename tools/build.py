"""Build Pasindu's GitHub profile README assets (SVG cards with embedded Geist fonts)."""
import base64, io, json, math, os, random, urllib.request
from datetime import datetime, timedelta, timezone
import numpy as np
from PIL import Image
from fontTools import subset
from fontTools.ttLib import TTFont

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(f"{OUT}/assets", exist_ok=True)
FONTS = os.environ.get("GEIST_FONTS", "node_modules/geist/dist/fonts")

# ---------- palette (swap ACCENT to recolour everything) ----------
BG, BAR, LINE = "#02070A", "#071017", "#16232D"
P, T, M = "#E6EDF2", "#8B98A4", "#52606B"
ACCENT, ACCENT_BG = "#FF6A3D", "#2A130C"

CHARS = "".join(chr(c) for c in range(32, 127)) + "↗²·•—'’"


def font_b64(path, text=CHARS):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    f = TTFont(path)
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


GM400 = font_b64(f"{FONTS}/geist-mono/GeistMono-Regular.woff2")
GM500 = font_b64(f"{FONTS}/geist-mono/GeistMono-Medium.woff2")
GS300 = font_b64(f"{FONTS}/geist-sans/Geist-Light.woff2")
GS500 = font_b64(f"{FONTS}/geist-sans/Geist-SemiBold.woff2")

STYLE = (
    "<style>"
    f"@font-face{{font-family:GM;font-weight:400;src:url(data:font/woff2;base64,{GM400}) format('woff2')}}"
    f"@font-face{{font-family:GM;font-weight:500;src:url(data:font/woff2;base64,{GM500}) format('woff2')}}"
    f"@font-face{{font-family:GS;font-weight:300;src:url(data:font/woff2;base64,{GS300}) format('woff2')}}"
    f"@font-face{{font-family:GS;font-weight:600;src:url(data:font/woff2;base64,{GS500}) format('woff2')}}"
    f"text{{font-family:GM,'Geist Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{T};white-space:pre}}"
    f".p{{fill:{P}}}.m{{fill:{M}}}.a{{fill:{ACCENT}}}.w{{font-weight:500}}"
    ".s{font-family:GS,Geist,'Helvetica Neue',Arial,sans-serif}"
    "image{image-rendering:pixelated}"
    "</style>"
)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, size=13, cls="p", anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}"{a} xml:space="preserve"{extra}>{esc(s)}</text>'


def hline(x1, x2, y):
    return f'<line x1="{x1}" y1="{y+.5}" x2="{x2}" y2="{y+.5}" stroke="{LINE}"/>'


def vline(x, y1, y2):
    return f'<line x1="{x+.5}" y1="{y1}" x2="{x+.5}" y2="{y2}" stroke="{LINE}"/>'


def svg(w, h, title, body):
    st = STYLE
    if 'class="p s"' not in body and "s\"" not in body:
        st = st.replace(f"@font-face{{font-family:GS;font-weight:300;src:url(data:font/woff2;base64,{GS300}) format('woff2')}}", "")
        st = st.replace(f"@font-face{{font-family:GS;font-weight:600;src:url(data:font/woff2;base64,{GS500}) format('woff2')}}", "")
    if " w\"" not in body:
        st = st.replace(f"@font-face{{font-family:GM;font-weight:500;src:url(data:font/woff2;base64,{GM500}) format('woff2')}}", "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{esc(title)}</title>{st}'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>{body}'
        f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" fill="none" stroke="{LINE}"/></svg>'
    )


def png_b64(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


# ---------- header band: an ember wave that scrolls forever ----------
def week_totals():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        return None
    to = datetime.now(timezone.utc).replace(microsecond=0)
    frm = to - timedelta(days=364)
    query = (
        "query($login:String!,$from:DateTime!,$to:DateTime!){"
        "user(login:$login){contributionsCollection(from:$from,to:$to){"
        "contributionCalendar{weeks{contributionDays{contributionCount}}}}}}"
    )
    body = json.dumps({"query": query, "variables": {
        "login": "PasinduSuraweera",
        "from": frm.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": to.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-header"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except Exception:
        return None
    if not weeks:
        return None
    days = [d.get("contributionCount") or 0 for w in weeks for d in (w.get("contributionDays") or [])]
    days = days[-(52 * 7):]
    if len(days) < 7 * 8:
        return None
    n = len(days) - len(days) % 7
    return [sum(days[i:i + 7]) for i in range(0, n, 7)]


def contribution_wave(cols):
    totals = week_totals()
    if not totals:
        return None
    y = np.asarray(totals, float)
    if y.max() - y.min() < 1:
        return None
    n = len(y)
    win = min(5, n // 5)
    target = 0.5 * (y[0] + y[-1])
    ramp = 0.5 * (1 - np.cos(np.linspace(0, np.pi, win)))
    pull = 1 - ramp
    y = y.copy()
    y[:win] = y[:win] * (1 - pull) + target * pull
    y[-win:] = y[-win:] * (1 - pull[::-1]) + target * pull[::-1]
    sampled = np.interp(np.linspace(0, n, cols, endpoint=False), np.arange(n + 1), np.r_[y, y[0]])
    sigma = cols / n * 1.8
    radius = max(1, int(round(sigma * 3)))
    kx = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (kx / sigma) ** 2)
    k /= k.sum()
    smooth = np.convolve(np.r_[sampled[-radius:], sampled, sampled[:radius]], k, "valid")
    span = float(smooth.max() - smooth.min())
    if span < 1e-6:
        return None
    print(f"header wave: {n} contribution weeks")
    return (smooth - smooth.min()) / span


def sine_wave(cols):
    x = np.arange(cols)
    t = 2 * np.pi * x / cols
    wave = np.sin(2 * t + 0.4) + 0.36 * np.sin(t) + 0.16 * np.sin(3 * t + 2.1)
    return (wave - wave.min()) / (wave.max() - wave.min())


def band_png():
    cols, rows, cell = 220, 35, 4          # 880 x 140 px
    wave = contribution_wave(cols)
    if wave is None:
        print("header wave: sine fallback")
        wave = sine_wave(cols)
    line_row = 22 - wave * 15                            # crests near row 7, troughs near 22

    bg, acc = hex2rgb(BG), hex2rgb(ACCENT)
    hot = hex2rgb("#FF9A58")
    inten = np.zeros((rows, cols))
    cores = np.empty(cols, np.int16)
    for c in range(cols):
        lr = float(line_row[c])
        core = int(round(lr))
        cores[c] = core
        for r in range(rows):
            d = r - lr
            if abs(d) < 0.8:
                v = 1.35 if r == core else 1.0          # hotter cap on the same ridge
            elif -1.7 < d < -0.8:
                v = 0.34                                # one-pixel ember halo
            elif d >= 0.8 and r < rows - 1:
                v = 0.56 * math.exp(-(d - 0.8) / 3.5)   # body under the ridge
            else:
                v = 0.0
            inten[r, c] = v
    # dim grid of dots everywhere, like a board waiting for data
    inten = np.maximum(inten, 0.07)

    img = np.zeros((rows * cell, cols * cell * 2, 3), np.uint8)
    img[:] = bg
    for r in range(rows):
        for c in range(cols):
            v = inten[r, c]
            if v > 1:
                col = hot
            else:
                col = bg + (acc - bg) * v
            for rep in (0, cols):
                xx = (c + rep) * cell
                img[r * cell:r * cell + 3, xx:xx + 3] = col
    im = Image.fromarray(img).convert("P", palette=Image.ADAPTIVE, colors=64)
    return im, cores


def glint_layer(cores):
    phases, dur = 22, 5.5
    buckets = [[] for _ in range(phases)]
    cols = len(cores)
    for c, core in enumerate(cores):
        phase = (c * phases) // cols
        y = int(core) * 4
        for rep in (0, 1):
            buckets[phase].append(f'<rect x="{(c + rep * cols) * 4}" y="{y}" width="3" height="3"/>')
    step = dur / phases
    out = []
    for i, rects in enumerate(buckets):
        delay = f"{i * step:.2f}".rstrip("0").rstrip(".")
        out.append(f'<g class="gl" fill="#FFD0AE" style="animation-delay:{delay}s">{"".join(rects)}</g>')
    return "".join(out)


def rider(cores):
    pale, hot = "#FFD0AE", "#FF9A58"
    cells = [
        (2, 0, pale), (3, 0, pale),
        (1, 1, pale), (2, 1, pale), (3, 1, ACCENT), (4, 1, pale),
        (2, 2, ACCENT), (3, 2, ACCENT), (4, 2, ACCENT), (5, 2, pale),
        (1, 3, ACCENT), (2, 3, ACCENT), (3, 3, ACCENT),
        (2, 4, ACCENT), (4, 4, ACCENT),
        (0, 5, pale), (1, 5, pale), (2, 5, pale), (3, 5, pale), (4, 5, pale), (5, 5, pale),
        (6, 4, hot),
        (3, 6, pale),
    ]
    left, board_row = 72, 5
    contact = left + 3
    n = len(cores)

    def y_of(core):
        return (int(core) - 1 - board_row) * 4

    y0 = y_of(cores[contact])
    frames = [f"0%{{transform:translateY({y0}px)}}"]
    i = 0
    while i < n:
        y = y_of(cores[(contact + i) % n])
        j = i + 1
        while j < n and y_of(cores[(contact + j) % n]) == y:
            j += 1
        if j < n:
            frames.append(f"{100 * j / n:.4f}%{{transform:translateY({y_of(cores[(contact + j) % n])}px)}}")
        i = j
    frames.append(f"100%{{transform:translateY({y0}px)}}")
    css = (f"@keyframes bob{{{''.join(frames)}}}"
           f".rd{{transform:translateY({y0}px);animation:bob 33s steps(1,end) infinite}}")
    rects = "".join(
        f'<rect x="{(left + c) * 4}" y="{r * 4}" width="3" height="3" fill="{fill}"/>'
        for c, r, fill in cells)
    return css, f'<g class="rd">{rects}</g>'


def timeline_mark(x, y):
    """Timeline's week wave mark: seven squares riding one swell, 2px each, on whole pixels."""
    return "".join(f'<rect x="{x + i * 3:g}" y="{y + dy}" width="2" height="2" fill="{ACCENT}"/>'
                   for i, dy in enumerate([4, 1, 1, 4, 7, 7, 4]))


def bar():
    """The top bar: name, BUILDING and the Timeline credit. It sits above
    Timeline's live wave (timeline-readme.vercel.app) in the README."""
    W, H = 880, 28
    b = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BAR}"/>',
         t(12, 19, "Pasindu", 12, "p w"), t(100, 19, "BUILDING", 12, "p w")]
    tag = "timeline-readme.vercel.app ↗"
    # Geist Mono is 0.6em a character, so at 12px the tag ends at the right margin (868).
    # The text starts a fixed gap after the mark, so it holds even if a fallback font draws it.
    x = round(868 - len(tag) * 7.2) - 30
    b.append(timeline_mark(x, 9))
    b.append(t(x + 30, 19, tag, 12, "m"))
    b.append("<style>@keyframes bl{0%,24%{opacity:1}25%,100%{opacity:.2}}"
             ".bl{animation:bl 1.2s steps(1,end) infinite}"
             "@media(prefers-reduced-motion:reduce){.bl{animation:none}}</style>")
    for (xx, yy), d in zip([(79, 10), (85, 10), (85, 16), (79, 16)], [-1.2, -.9, -.6, -.3]):
        b.append(f'<rect class="bl" x="{xx}" y="{yy}" width="4" height="4" fill="{ACCENT}" style="animation-delay:{d}s"/>')
    return svg(W, H, "Pasindu, building. The wave below is drawn by Timeline.", "".join(b))


def header():
    """The name panel under the wave."""
    W, H = 880, 198
    b = []
    b.append(t(22, 64, "Pasindu", 56, "p s", extra=' style="font-weight:300;letter-spacing:-2px"'))
    b.append(t(24, 92, "Data engineering, analytics and open source.", 14, "p"))
    b.append(t(24, 136, "NOW", 11, "m"))
    b.append(t(104, 136, "building Basis and altr", 13, "p w"))
    b.append(t(24, 164, "HANDLE", 11, "m"))
    b.append(t(104, 164, "@PasinduSuraweera", 13, "p w"))
    b.append(vline(536, 0, H)); b.append(vline(708, 0, H)); b.append(hline(536, W, 99))
    cells = [(552, 28, "WORKING AT", "Gamma Pizzakraft"), (724, 28, "FOCUS", "data platforms"),
             (552, 127, "FELLOW", "Databricks '26"), (724, 127, "STUDYING", "Data Science")]
    for x, y, k, v in cells:
        b.append(t(x, y, k, 10, "m")); b.append(t(x, y + 33, v, 13, "p w"))
    return svg(W, H, "Pasindu Suraweera: data engineering, analytics and open source. "
               "Building Basis and altr. Databricks Student Fellow 2026.", "".join(b))


# ---------- project tiles ----------
def tile(num, name, domain, art, caption, tag, title):
    W, H = 440, 307
    b = [f'<rect x="0" y="0" width="{W}" height="28" fill="{BAR}"/>', hline(0, W, 27),
         f'<rect x="8" y="6" width="16" height="16" fill="{ACCENT_BG}"/>',
         t(16, 18, str(num), 12, "a w", "middle"), t(32, 18, name, 12, "p w"),
         t(428, 18, domain, 12, "m", "end"),
         f'<svg x="0" y="28" width="440" height="231" viewBox="0 0 440 231" overflow="hidden">{art}</svg>',
         hline(0, W, 259), t(16, 288, caption, 13, "p"), t(424, 288, tag, 12, "m", "end")]
    return svg(W, H, title, "".join(b))


def dotgrid(w, h, step=12, color=LINE):
    return (f'<defs><pattern id="dg" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<rect x="0" y="0" width="2" height="2" fill="{color}"/></pattern></defs>'
            f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#dg)"/>')


def art_altr():
    a = [f'<rect width="440" height="231" fill="{BG}"/>', dotgrid(440, 231)]
    a.append(t(22, 78, "altr", 52, "p s", extra=' style="font-weight:600;letter-spacing:-2px"'))
    a.append(t(24, 104, "doc, sheet and deck", 12, "m"))
    a.append(t(24, 120, "skills for any model", 12, "m"))
    a.append(f'<rect x="22" y="150" width="182" height="30" fill="{BAR}" stroke="{LINE}"/>')
    a.append(t(32, 170, "$", 12, "a")); a.append(t(46, 170, "pip install altr-oss", 12, "p"))
    a.append(t(24, 206, "gpt-oss · llama · qwen", 11, "m"))

    def card(x, y, label, inner):
        return (f'<g transform="translate({x} {y})"><rect width="128" height="150" fill="#0A141B" stroke="{LINE}"/>'
                f'<rect width="128" height="20" fill="{BAR}"/>{hline(0, 128, 19)}'
                f'{t(8, 14, label, 10, "a w")}{inner}</g>')
    doc = "".join(f'<rect x="10" y="{32+i*12}" width="{[96,108,80,104,60,100,92,70][i]}" height="4" fill="{M if i else P}"/>' for i in range(8))
    sheet = "".join(f'<rect x="{10+c*27}" y="{30+r*15}" width="25" height="13" fill="{"#132029" if r else ACCENT_BG}"/>'
                    for r in range(7) for c in range(4))
    deck = (f'<rect x="10" y="30" width="108" height="64" fill="#132029"/>'
            + "".join(f'<rect x="{20+i*20}" y="{84-hh}" width="12" height="{hh}" fill="{ACCENT if i==3 else M}"/>'
                      for i, hh in enumerate([18, 30, 24, 46, 36]))
            + f'<rect x="10" y="104" width="80" height="5" fill="{P}"/><rect x="10" y="116" width="100" height="4" fill="{M}"/>'
            + f'<rect x="10" y="126" width="64" height="4" fill="{M}"/>')
    a.append(card(232, 30, ".docx", doc))
    a.append(card(262, 52, ".xlsx", sheet))
    a.append(card(292, 74, ".pptx", deck))
    return "".join(a)


def art_silo():
    a = [f'<rect width="440" height="231" fill="{BG}"/>', dotgrid(440, 231)]
    code = [
        [("from ", M), ("flask_silo ", P), ("import ", M), ("Silo", ACCENT)],
        [],
        [("silo ", P), ("= ", M), ("Silo", ACCENT), ("(app, ttl=", P), ("3600", ACCENT), (")", P)],
        [("silo.", P), ("register", ACCENT), ("(", P), ("'cart'", T), (",", P)],
        [("    ", P), ("lambda", M), (": {", P), ("'items'", T), (": []})", P)],
        [],
        [("state ", P), ("= ", M), ("silo.", P), ("state", ACCENT), ("(", P), ("'cart'", T), (")", P)],
    ]
    a.append(f'<rect x="18" y="22" width="250" height="148" fill="{BAR}" stroke="{LINE}"/>')
    for i, line in enumerate(code):
        x = 30
        a.append(t(26, 46 + i * 17, str(i + 1).rjust(1), 10, "m", extra=' style="opacity:.6"'))
        x = 42
        for s, c in line:
            a.append(f'<text x="{x}" y="{46+i*17}" font-size="11" style="fill:{c}" xml:space="preserve">{esc(s)}</text>')
            x += len(s) * 6.6
    sids = [("a1f3", "3 items", True), ("9c2e", "1 item", False), ("77b0", "expired", False)]
    for i, (sid, st, live) in enumerate(sids):
        x = 290 + i * 46
        a.append(f'<rect x="{x}" y="22" width="38" height="148" fill="{"#0A141B"}" stroke="{ACCENT if live else LINE}"/>')
        for j in range(6 if st != "expired" else 0):
            on = j < (3 if live else 1)
            a.append(f'<rect x="{x+8}" y="{150-j*16}" width="22" height="10" fill="{ACCENT if on and live else (M if on else "#132029")}"/>')
        if st == "expired":
            a.append(t(x + 19, 100, "410", 11, "m", "middle"))
        a.append(t(x + 19, 188, sid, 10, "p" if live else "m", "middle"))
    a.append(t(18, 212, "one private workspace per client", 11, "m"))
    a.append(t(422, 212, "X-Session-ID", 11, "a", "end"))
    return "".join(a)


def art_jevflow():
    # pixel-art island, 110 x 58 px scaled 4x
    w, h = 110, 58
    rng = np.random.default_rng(11)
    img = np.zeros((h, w, 3), np.uint8)
    sea_a, sea_b = hex2rgb("#06141C"), hex2rgb("#0C2632")
    for y in range(h):
        for x in range(w):
            img[y, x] = sea_b if (x + y * 3) % 7 == 0 and rng.random() < .6 else sea_a
    cx, cy = 55, 30
    ang = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    rad = 21 + 3 * np.sin(3 * ang + 1) + 2 * np.sin(5 * ang) + rng.normal(0, .4, 360)
    sand, grass, grass2 = hex2rgb("#C9A96E"), hex2rgb("#3E7A45"), hex2rgb("#4E8E50")
    for y in range(h):
        for x in range(w):
            dx, dy = (x - cx) / 1.9, (y - cy)
            r = math.hypot(dx, dy)
            i = int((math.atan2(dy, dx) % (2 * np.pi)) / (2 * np.pi) * 360) % 360
            if r < rad[i] * .62:
                img[y, x] = grass2 if (x * 7 + y * 13) % 11 == 0 else grass
            elif r < rad[i] * .70:
                img[y, x] = sand
            elif r < rad[i] * .78 and (x + y) % 2 == 0:
                img[y, x] = sea_b
    def put(px, color):
        for x, y in px:
            if 0 <= x < w and 0 <= y < h:
                img[y, x] = hex2rgb(color)
    def house(x, y, roof):
        put([(x + i, y + j) for i in range(5) for j in range(3)], "#E8DCC4")
        put([(x - 1 + i, y - 1) for i in range(7)] + [(x + i, y - 2) for i in range(1, 4)], roof)
        put([(x + 2, y + 2)], "#5B3A24")
        put([(x + 1, y + 1)], "#FFD27A")
    def tree(x, y):
        put([(x, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)], "#1F4D2B")
        put([(x, y + 2)], "#5B3A24")
    for x, y in [(36, 18), (44, 40), (70, 16), (76, 38), (40, 30), (64, 44), (58, 14), (82, 28), (34, 24)]:
        tree(x, y)
    house(47, 24, ACCENT); house(56, 32, "#B5523B"); house(64, 24, ACCENT); house(48, 34, "#B5523B")
    # windmill
    put([(73, 29), (73, 30), (73, 31), (74, 31), (72, 31)], "#E8DCC4")
    put([(73, 28), (71, 26), (72, 27), (74, 27), (75, 26), (72, 29), (71, 30), (74, 29), (75, 30)], "#8B98A4")
    # pond, dock, boat
    put([(56 + i, 41 + j) for i in range(4) for j in range(2)], "#2C6C86")
    put([(cx + i, 53) for i in range(0, 3)] + [(cx + 1, 52)], "#7A5634")
    put([(92 + i, 46) for i in range(4)] + [(93, 45), (94, 45)], "#8B98A4")
    big = Image.fromarray(img).resize((w * 4, h * 4), Image.NEAREST)
    b64 = png_b64(big.convert("P", palette=Image.ADAPTIVE, colors=48))
    a = [f'<image x="0" y="0" width="440" height="232" href="data:image/png;base64,{b64}" '
         f'xlink:href="data:image/png;base64,{b64}"/>']
    # floating tags, like the in-game ones
    def tag(x, y, s, hot=False):
        wpx = len(s) * 6.6 + 16
        return (f'<rect x="{x}" y="{y}" width="{wpx}" height="20" fill="{BG}" fill-opacity=".82" '
                f'stroke="{ACCENT if hot else LINE}"/>{t(x+8, y+14, s, 11, "p" if hot else "m")}')
    a.append(tag(18, 18, "Mira · baking bread", True))
    a.append(tag(272, 30, "Inn · open til 22:00"))
    a.append(tag(24, 190, "Day 4 · spring · rain"))
    a.append(tag(286, 190, "Rowan · stargazing"))
    return "".join(a)


def art_basis():
    a = [f'<rect width="440" height="231" fill="{BG}"/>', dotgrid(440, 231)]
    rng = np.random.default_rng(3)
    n, x0, cw = 30, 20, 9
    price, rows = 120.0, []
    for i in range(n):
        hot = 18 <= i <= 21
        drift = 4.5 if hot else (-0.8 if i > 22 else 0.15)
        o = price; c = o + drift + rng.normal(0, 0.6 if hot else 1.8)
        hi = max(o, c) + abs(rng.normal(0, 1.6)); lo = min(o, c) - abs(rng.normal(0, 1.6))
        rows.append((o, hi, lo, c)); price = c
    allv = [v for r in rows for v in r]
    lo_v, hi_v = min(allv), max(allv)
    Y = lambda v: 160 - (v - lo_v) / (hi_v - lo_v) * 120
    ann_x = x0 + 22 * cw + 4
    a.append(f'<rect x="{x0+18*cw-1}" y="22" width="{4*cw}" height="194" fill="{ACCENT}" fill-opacity=".09"/>')
    a.append(f'<line x1="{ann_x}" y1="30" x2="{ann_x}" y2="186" stroke="{P}" stroke-dasharray="2 3" stroke-opacity=".6"/>')
    for i, (o, hi, lo, c) in enumerate(rows):
        x = x0 + i * cw
        up = c >= o
        col = ACCENT if 18 <= i <= 21 else (P if up else M)
        a.append(f'<line x1="{x+3.5}" y1="{Y(hi):.1f}" x2="{x+3.5}" y2="{Y(lo):.1f}" stroke="{col}"/>')
        top, bot = Y(max(o, c)), Y(min(o, c))
        a.append(f'<rect x="{x+1}" y="{top:.1f}" width="5" height="{max(1.5, bot-top):.1f}" fill="{col}"/>')
        vh = 4 + abs(c - o) * 3 + (14 if 18 <= i <= 21 else 0)
        a.append(f'<rect x="{x+1}" y="{214-vh:.1f}" width="5" height="{vh:.1f}" fill="{ACCENT if 18<=i<=21 else "#1C2B36"}"/>')
    a.append(t(x0, 224, "CSE · daily", 10, "m"))
    a.append(t(x0 + 18 * cw - 1, 30, "unusual volume", 10, "a", extra=' text-anchor="end" dx="-6"'))
    a.append(t(ann_x + 4, 42, "disclosure", 10, "p"))
    # group graph
    gx, gy = 358, 110
    nodes = [(0, 0, 9, True), (-44, -46, 5, False), (40, -54, 6, False), (52, 8, 5, False),
             (30, 58, 6, False), (-40, 50, 5, False), (-58, 2, 4, False)]
    for nx, ny, r, hub in nodes[1:]:
        a.append(f'<line x1="{gx}" y1="{gy}" x2="{gx+nx}" y2="{gy+ny}" stroke="{LINE}" stroke-width="1.5"/>')
    a.append(f'<line x1="{gx+40}" y1="{gy-54}" x2="{gx+52}" y2="{gy+8}" stroke="{LINE}" stroke-width="1.5"/>')
    a.append(f'<line x1="{gx+30}" y1="{gy+58}" x2="{gx-40}" y2="{gy+50}" stroke="{LINE}" stroke-width="1.5"/>')
    for nx, ny, r, hub in nodes:
        a.append(f'<rect x="{gx+nx-r}" y="{gy+ny-r}" width="{2*r}" height="{2*r}" '
                 f'fill="{ACCENT if hub else "#132029"}" stroke="{ACCENT if hub else M}"/>')
    a.append(t(gx, 212, "group graph", 10, "m", "middle"))
    return "".join(a)


def chip(label, icon, w=None):
    w = w or int(48 + len(label) * 7.8 + 34)
    b = [f'<g transform="translate(10 10)">{icon}</g>', vline(36, 0, 36),
         t(48, 23, label, 13, "p"), t(w - 12, 23, "↗", 13, "m", "end")]
    return svg(w, 36, label, "".join(b)), w


GLOBE = (f'<g fill="none" stroke="{T}" stroke-width="1.3"><circle cx="8" cy="8" r="7"/>'
         f'<ellipse cx="8" cy="8" rx="3" ry="7"/><line x1="1" y1="8" x2="15" y2="8"/></g>')
XLOGO = (f'<g transform="scale(0.6666)"><path fill="{T}" d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.4l-5.8-7.58-6.64 '
         f'7.58H.47l8.6-9.83L0 1.15h7.6l5.24 6.93zM17.6 20.64h2.04L6.49 3.24H4.3z"/></g>')
PYPI = (f'<g fill="none" stroke="{T}" stroke-width="1.3"><path d="M8 1 L15 4.5 L15 11.5 L8 15 L1 11.5 L1 4.5 Z"/>'
        f'<path d="M1 4.5 L8 8 L15 4.5 M8 8 L8 15"/></g>')


def write(name, content):
    with open(f"{OUT}/assets/{name}", "w") as f:
        f.write(content)
    print(f"{name}: {len(content)/1024:.0f} KB")


write("bar.svg", bar())
write("header.svg", header())
write("tile-altr.svg", tile(2, "altr", "pypi.org/project/altr-oss", art_altr(),
                            "Office skills for open-weight LLMs", "python",
                            "altr: doc, sheet and deck skills for open-weight LLMs (pip install altr-oss)"))
write("tile-flask-silo.svg", tile(3, "flask-silo", "pypi.org/project/flask-silo", art_silo(),
                                  "Session-isolated state for Flask", "python",
                                  "Flask-Silo: session-isolated state management for Flask APIs"))
write("tile-jevflow.svg", tile(4, "jevflow", "github.com/PasinduSuraweera", art_jevflow(),
                               "A little world with a mind of its own", "web",
                               "JevFlow: a village simulation where villagers decide their own days"))
write("tile-basis.svg", tile(5, "basis", "in progress", art_basis(),
                             "CSE market intelligence lakehouse", "databricks",
                             "Basis: Colombo Stock Exchange market and company intelligence on Databricks"))
s, _ = chip("pasindusuraweera.com", GLOBE); write("chip-site.svg", s)
s, _ = chip("@pasindu__s", XLOGO); write("chip-x.svg", s)
