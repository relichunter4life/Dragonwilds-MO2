# Made by Claude Ai & Relic Hunter
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "RelicModsBot", "art"))
import make_art as A

MARK = (
    "M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 "
    "0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 "
    "0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 "
    "1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61"
    ".55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 "
    ".67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"
)


def arc_points(x0, y0, rx, ry, rot, large, sweep, x1, y1, steps=48):
    phi = math.radians(rot)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x0 + x1) / 2
    cy = sp * cxp + cp * cyp + (y0 + y1) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    out = []
    for i in range(1, steps + 1):
        t = t1 + dt * i / steps
        out.append((cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp, cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp))
    return out


def path_points(d):
    tokens = re.findall(r"[A-Za-z]|-?(?:\d+\.\d*|\.\d+|\d+)(?:e-?\d+)?", d)
    pts, i, cmd = [], 0, None
    x = y = sx = sy = 0.0
    while i < len(tokens):
        if re.match(r"[A-Za-z]", tokens[i]):
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                x, y = sx, sy
                continue

        def num():
            nonlocal i
            v = float(tokens[i])
            i += 1
            return v

        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            sx, sy = x, y
            pts.append((x, y))
            cmd = "l" if rel else "L"
        elif c == "L":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            pts.append((x, y))
        elif c == "C":
            v = [num() for _ in range(6)]
            if rel:
                v = [v[k] + (x if k % 2 == 0 else y) for k in range(6)]
            for s in range(1, 17):
                t = s / 16
                mt = 1 - t
                px = mt ** 3 * x + 3 * mt * mt * t * v[0] + 3 * mt * t * t * v[2] + t ** 3 * v[4]
                py = mt ** 3 * y + 3 * mt * mt * t * v[1] + 3 * mt * t * t * v[3] + t ** 3 * v[5]
                pts.append((px, py))
            x, y = v[4], v[5]
        elif c == "A":
            rx, ry, rot, large, sweep, nx, ny = (num() for _ in range(7))
            if rel:
                nx, ny = x + nx, y + ny
            pts.extend(arc_points(x, y, rx, ry, rot, int(large), int(sweep), nx, ny))
            x, y = nx, ny
        else:
            raise ValueError("unsupported path command " + cmd)
    return pts


def github_mark(size, colour_stops):
    scale = 8
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    pts = [(px * big / 16, py * big / 16) for px, py in path_points(MARK)]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    fill = A.gradient((size, size), colour_stops, 0, size)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(fill, (0, 0), mask)
    return out, mask


def main():
    W, H = 1000, 230
    base = A.backdrop(4, W, H, 0.45, W * 0.58, H / 2, W * 0.55, H * 0.75)
    A.frame(base)
    size = 150
    mx, my = 70, (H - size) // 2
    halo = Image.new("RGBA", base.size, A.CRIMSON + (0,))
    halo.putalpha(A.radial(base.size, mx + size / 2, my + size / 2, size * 0.95, size * 0.95, 0.85, 1.2))
    base.alpha_composite(halo)
    mark, mask = github_mark(size, A.GOLD_GRAD)
    edge = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
    shadow = Image.new("L", edge.size, 0)
    shadow.paste(mask, (6, 6))
    edge.putalpha(shadow.filter(ImageFilter.GaussianBlur(5)))
    base.alpha_composite(edge, (mx - 6 + 3, my - 6 + 5))
    base.alpha_composite(mark, (mx, my))
    tx0 = mx + size + 40
    cx = tx0 + (W - 40 - tx0) / 2
    title = "DOWNLOAD ON GITHUB"
    k = A.fit(title, 60, W - 40 - tx0 - 20, 0.07)
    y_end, _ = A.text_row(base, cx, 52, title, A.cinzel(k), A.GOLD_GRAD, int(k * 0.07), 4, glow=A.CRIMSON)
    A.divider(base, cx, y_end + 24, (W - 40 - tx0) * 0.42)
    sub = "STAND-ALONE  &  ADD-ON  -  LATEST RELEASE"
    ks = A.fit(sub, 24, W - 40 - tx0 - 40, 0.12, 700)
    A.text_row(base, cx, y_end + 48, sub, A.cinzel(ks, 700), A.CREAM_GRAD, int(ks * 0.12), 2)
    out = os.path.join(HERE, "..", "images", "download-on-github.png")
    base.convert("RGB").save(out, optimize=True)
    print(os.path.abspath(out), base.size)


if __name__ == "__main__":
    main()
