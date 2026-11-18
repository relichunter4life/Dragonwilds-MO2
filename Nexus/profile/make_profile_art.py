# Made by Claude Ai & Relic Hunter
import math
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "RelicModsBot", "art"))
import make_art as A

ICONS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "icons")
OUT = os.path.join(HERE, "..", "..", "images", "nexus-profile")
W = 1000

LINKS = [
    ("nexusmods", "NEXUS MODS", "RelicHunter  -  all my mods in one place", "BROWSE", "E6832B"),
    ("github", "GITHUB", "@relichunter4life  -  Dragonwilds MO2 and tools", "VISIT", "FFFFFF"),
    ("curseforge", "CURSEFORGE", "RelicHunter  -  Dragonwilds mods", "VISIT", "F16436"),
    ("youtube", "YOUTUBE", "@RelicHunterMods  -  showcases and Shorts", "SUBSCRIBE", "FF0000"),
    ("tiktok", "TIKTOK", "@_relichunter", "FOLLOW", "FFFFFF"),
    ("instagram", "INSTAGRAM", "@the_relichunter", "FOLLOW", "FF0069"),
    ("x", "X  /  TWITTER", "@xTheRelicHunter", "FOLLOW", "FFFFFF"),
    ("facebook", "FACEBOOK", "Relic Mods", "FOLLOW", "0866FF"),
    ("kick", "KICK", "TheRelicHunter  -  live streams", "FOLLOW", "53FC19"),
    ("rumble", "RUMBLE", "RelicHunter_Show", "FOLLOW", "85C742"),
    ("kofi", "KO-FI", "relichunter  -  buy me a coffee", "SUPPORT", "FF6433"),
]
SECTIONS = {
    "section-work": "MY WORK",
    "section-follow": "FOLLOW RELIC MODS",
    "section-about": "ABOUT ME",
    "section-support": "SUPPORT MY WORK",
}


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def arc_points(x0, y0, rx, ry, rot, large, sweep, x1, y1, steps=40):
    if rx == 0 or ry == 0:
        return [(x1, y1)]
    phi = math.radians(rot)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x0 + x1) / 2
    cy = sp * cxp + cp * cyp + (y0 + y1) / 2

    def ang(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    pts = []
    for i in range(1, steps + 1):
        t = t1 + dt * i / steps
        pts.append((cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp, cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp))
    return pts


def bez(p0, p1, p2, p3, steps=14):
    out = []
    for s in range(1, steps + 1):
        t = s / steps
        m = 1 - t
        out.append((
            m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
            m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1],
        ))
    return out


def subpaths(d):
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", d)
    paths, cur = [], []
    i = 0
    cmd = None
    x = y = sx = sy = 0.0
    last_c = last_q = None
    flags_cmd = "Aa"

    def num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    def flag():
        nonlocal i
        t = tokens[i]
        if len(t) > 1 and t[0] in "01" and cmd in flags_cmd:
            tokens[i] = t[1:]
            return int(t[0])
        i += 1
        return int(float(t))

    while i < len(tokens):
        if re.match(r"[A-Za-z]", tokens[i]):
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    paths.append(cur)
                cur = []
                x, y = sx, sy
                last_c = last_q = None
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if c == "M":
            if cur:
                paths.append(cur)
            x, y = ox + num(), oy + num()
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "l" if rel else "L"
            last_c = last_q = None
        elif c == "L":
            x, y = ox + num(), oy + num()
            cur.append((x, y))
            last_c = last_q = None
        elif c == "H":
            x = (x if rel else 0.0) + num()
            cur.append((x, y))
            last_c = last_q = None
        elif c == "V":
            y = (y if rel else 0.0) + num()
            cur.append((x, y))
            last_c = last_q = None
        elif c == "C":
            p1 = (ox + num(), oy + num())
            p2 = (ox + num(), oy + num())
            p3 = (ox + num(), oy + num())
            cur.extend(bez((x, y), p1, p2, p3))
            x, y = p3
            last_c, last_q = p2, None
        elif c == "S":
            p1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c else (x, y)
            p2 = (ox + num(), oy + num())
            p3 = (ox + num(), oy + num())
            cur.extend(bez((x, y), p1, p2, p3))
            x, y = p3
            last_c, last_q = p2, None
        elif c == "Q":
            q = (ox + num(), oy + num())
            p3 = (ox + num(), oy + num())
            p1 = (x + 2 / 3 * (q[0] - x), y + 2 / 3 * (q[1] - y))
            p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            cur.extend(bez((x, y), p1, p2, p3))
            x, y = p3
            last_q, last_c = q, None
        elif c == "T":
            q = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q else (x, y)
            p3 = (ox + num(), oy + num())
            p1 = (x + 2 / 3 * (q[0] - x), y + 2 / 3 * (q[1] - y))
            p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            cur.extend(bez((x, y), p1, p2, p3))
            x, y = p3
            last_q, last_c = q, None
        elif c == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = flag(), flag()
            nx, ny = ox + num(), oy + num()
            cur.extend(arc_points(x, y, rx, ry, rot, large, sweep, nx, ny))
            x, y = nx, ny
            last_c = last_q = None
        else:
            raise ValueError("unsupported command " + cmd)
    if cur:
        paths.append(cur)
    return paths


def icon_mask(name, size):
    text = open(os.path.join(ICONS, name + ".svg"), encoding="utf-8").read()
    box = [float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
    big = size * 8
    mask = Image.new("L", (big, big), 0)
    for d in re.findall(r'\sd="([^"]+)"', text):
        for sub in subpaths(d):
            if len(sub) < 3:
                continue
            layer = Image.new("L", (big, big), 0)
            pts = [((px - box[0]) * big / box[2], (py - box[1]) * big / box[3]) for px, py in sub]
            ImageDraw.Draw(layer).polygon(pts, fill=255)
            mask = ImageChops.logical_xor(mask.convert("1"), layer.convert("1")).convert("L")
    return mask.resize((size, size), Image.LANCZOS)


def left_text(base, x, y, text, size, stops, sp_k, weight=800, stroke=3, glow=None):
    f = A.cinzel(size, weight)
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    w = A.spaced_width(d, text, f, int(size * sp_k))
    return A.text_row(base, x + w / 2, y, text, f, stops, int(size * sp_k), stroke, glow)


def medallion(base, cx, cy, r, mask, colour):
    halo = Image.new("RGBA", base.size, colour + (0,))
    halo.putalpha(A.radial(base.size, cx, cy, r * 2.2, r * 2.2, 0.55, 1.3))
    base.alpha_composite(halo)
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=A.GOLD3 + (255,))
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=A.GOLD + (255,))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 9, 9, 255))
    s = mask.size[0]
    glyph = Image.new("RGBA", (s, s), colour + (255,))
    glyph.putalpha(mask)
    base.alpha_composite(glyph, (int(cx - s / 2), int(cy - s / 2)))


def pill(base, right, cy, text, size=20):
    f = A.cinzel(size, 800)
    d = ImageDraw.Draw(base)
    sp = int(size * 0.14)
    w = A.spaced_width(d, text, f, sp)
    h = size + 22
    x0, y0, x1, y1 = right - w - 44, cy - h / 2, right, cy + h / 2
    d.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], radius=h / 2 + 2, fill=A.GOLD + (255,))
    d.rounded_rectangle([x0, y0, x1, y1], radius=h / 2, fill=A.CRIMSON3 + (255,))
    grad = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    gd.rounded_rectangle([x0 + 3, y0 + 3, x1 - 3, cy], radius=h / 2, fill=A.CRIMSON + (120,))
    base.alpha_composite(grad)
    A.text_row(base, (x0 + x1) / 2, cy - size * 0.36, text, f, A.GOLD_GRAD, sp, 2)
    return x0


def save(base, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".jpg")
    base.convert("RGB").save(path, quality=92, optimize=True)
    return path


def link_button(key, title, handle, cta, colour, n):
    H = 124
    base = A.backdrop(n, W, H, 0.5, W * 0.45, H / 2, W * 0.7, H * 1.1)
    A.frame(base)
    medallion(base, 78, H / 2, 40, icon_mask(key, 46), hex_rgb(colour))
    pill_x = pill(base, W - 34, H / 2, cta)
    tx = 140
    maxw = pill_x - tx - 24
    k = A.fit(title, 40, maxw, 0.08)
    y_end, _ = left_text(base, tx, 24, title, k, A.GOLD_GRAD, 0.08, glow=A.CRIMSON)
    ks = A.fit(handle, 22, maxw, 0.06, 700)
    left_text(base, tx, y_end + 13, handle, ks, A.CREAM_GRAD, 0.06, 700, 2)
    return save(base, "link-" + key)


def discord_button():
    H = 200
    base = A.backdrop(2, W, H, 0.5, W * 0.5, H / 2, W * 0.7, H)
    A.frame(base)
    medallion(base, 110, H / 2, 66, icon_mask("discord", 76), hex_rgb("5865F2"))
    pill_x = pill(base, W - 40, H / 2, "JOIN", 26)
    tx = 205
    maxw = pill_x - tx - 30
    title = "JOIN THE RELIC MODS DISCORD"
    k = A.fit(title, 50, maxw, 0.06)
    y_end, _ = left_text(base, tx, 40, title, k, A.GOLD_GRAD, 0.06, glow=A.CRIMSON)
    sub = "MOD SUPPORT  -  EARLY LOOKS  -  GUIDES  -  FRIENDLY COMMUNITY"
    ks = A.fit(sub, 22, maxw, 0.08, 700)
    y2, _ = left_text(base, tx, y_end + 18, sub, ks, A.CREAM_GRAD, 0.08, 700, 2)
    ki = A.fit("discord.gg/BumVNYDUec", 20, maxw, 0.04, 600)
    left_text(base, tx, y2 + 14, "discord.gg/BumVNYDUec", ki, A.GOLD_GRAD, 0.04, 600, 2)
    return save(base, "link-discord")


def section(name, text):
    H = 92
    base = Image.new("RGBA", (W, H), A.BG + (255,))
    glow = Image.new("RGBA", base.size, A.CRIMSON3 + (0,))
    glow.putalpha(A.radial(base.size, W / 2, H / 2, W * 0.4, H * 0.9, 0.7, 1.2))
    base.alpha_composite(glow)
    k = A.fit(text, 40, W - 360, 0.12)
    f = A.cinzel(k)
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    w = A.spaced_width(d, text, f, int(k * 0.12))
    y_end, _ = A.text_row(base, W / 2, 20, text, f, A.GOLD_GRAD, int(k * 0.12), 3, glow=A.CRIMSON)
    line_y = (20 + y_end) / 2
    dd = ImageDraw.Draw(base)
    for s in (-1, 1):
        x_in = W / 2 + s * (w / 2 + 28)
        x_out = W / 2 + s * (W / 2 - 40)
        dd.line([(x_in, line_y), (x_out, line_y)], fill=A.GOLD + (255,), width=2)
        dd.line([(x_in + s * 30, line_y + 5), (x_out - s * 120, line_y + 5)], fill=A.CRIMSON + (200,), width=1)
        r = 7
        dd.polygon([(x_in, line_y - r), (x_in + r, line_y), (x_in, line_y + r), (x_in - r, line_y)], fill=A.CRIMSON + (255,), outline=A.GOLD2 + (255,))
        dd.polygon([(x_out, line_y - 4), (x_out + 4, line_y), (x_out, line_y + 4), (x_out - 4, line_y)], fill=A.GOLD + (255,))
    return save(base, name)


def header():
    H = 340
    base = A.backdrop(1, W, H, 0.42, W / 2, H * 0.55, W * 0.55, H * 0.75)
    A.frame(base)
    A.gem(base, W / 2, 74, 44)
    title = "RELIC HUNTER"
    k = A.fit(title, 92, W - 200, 0.08)
    y_end, _ = A.text_row(base, W / 2, 130, title, A.cinzel(k), A.GOLD_GRAD, int(k * 0.08), 5, glow=A.CRIMSON)
    A.divider(base, W / 2, y_end + 22, 300)
    sub = "MOD AUTHOR  -  RELIC MODS  -  RUNESCAPE: DRAGONWILDS"
    ks = A.fit(sub, 26, W - 180, 0.1, 700)
    y2, _ = A.text_row(base, W / 2, y_end + 44, sub, A.cinzel(ks, 700), A.CREAM_GRAD, int(ks * 0.1), 2)
    stats = "30+ MODS   -   16K+ DOWNLOADS   -   #1 TOP MOD"
    kk = A.fit(stats, 24, W - 260, 0.12)
    A.text_row(base, W / 2, y2 + 20, stats, A.cinzel(kk), A.RED_GRAD, int(kk * 0.12), 2)
    return save(base, "header")


def main():
    made = [header(), discord_button()]
    made += [section(k, v) for k, v in SECTIONS.items()]
    for idx, (key, title, handle, cta, colour) in enumerate(LINKS):
        made.append(link_button(key, title, handle, cta, colour, 1 + idx % 4))
    for path in made:
        print(os.path.abspath(path))


if __name__ == "__main__":
    main()
