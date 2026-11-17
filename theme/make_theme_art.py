# Made by Claude Ai & Relic Hunter
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ART = r"D:\Modding\FModel\Output\Textures_PNG\RSDragonwilds\Content\Art\UI\Loading\T_Concept_Art_Placeholder_{}.png"
FONTS = os.path.join(HERE, "..", "..", "AstralCompanions-2.0.0", "Nexus", "osrs-fonts", "ttf")
OUT = os.path.join(HERE, "stylesheets", "Transparent-Style", "Dragonwilds")
GOLD = (240, 180, 76)
GOLD_HI = (255, 214, 120)
EMBER = (217, 83, 30)
BONE = (232, 220, 196)
DARK = (18, 14, 10)
S = 4


def art(n):
    im = Image.open(ART.format(n)).convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=0.5)
    im = ImageEnhance.Color(im).enhance(1.08)
    return ImageEnhance.Brightness(im).enhance(1.06)


def lift_edges(im, amount):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-w * 0.25, -h * 0.25, w * 1.25, h * 1.25), fill=255)
    mask = ImageOps.invert(mask.filter(ImageFilter.GaussianBlur(min(w, h) // 6)))
    bright = ImageEnhance.Brightness(im).enhance(1 + amount * 1.6)
    return Image.composite(bright, im, mask)


def cover(im, w, h, cy=0.5):
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def shade(im, top, bottom):
    w, h = im.size
    grad = Image.new("L", (1, h))
    for y in range(h):
        grad.putpixel((0, y), int(top + (bottom - top) * y / (h - 1)))
    dark = Image.new("RGB", (w, h), DARK)
    return Image.composite(dark, im, grad.resize((w, h)))


def backgrounds():
    main = cover(lift_edges(art(3), 0.42), 3840, 1700, 0.45)
    main = main.filter(ImageFilter.GaussianBlur(3))
    main = ImageEnhance.Brightness(main).enhance(0.95)
    shade(main, 20, 80).save(os.path.join(OUT, "bg_main.jpg"), quality=88)
    dialog = cover(lift_edges(art(4), 0.42), 1800, 1100)
    dialog = ImageEnhance.Brightness(dialog.filter(ImageFilter.GaussianBlur(4))).enhance(0.62)
    shade(dialog, 60, 140).save(os.path.join(OUT, "bg_dialog.jpg"), quality=88)
    menu = cover(art(4), 600, 600).filter(ImageFilter.GaussianBlur(12))
    ImageEnhance.Brightness(menu).enhance(0.3).save(os.path.join(OUT, "bg_menu.jpg"), quality=88)


def canvas(size):
    return Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))


def save(im, name, size):
    im.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))


def box(name, checked, hover=False, disabled=False):
    im = canvas(20)
    d = ImageDraw.Draw(im)
    rim = (120, 104, 84, 255) if disabled else (GOLD_HI if hover else GOLD) + (255,)
    d.rounded_rectangle((2 * S, 2 * S, 18 * S, 18 * S), radius=3 * S, fill=(14, 11, 8, 230), outline=rim, width=int(1.6 * S))
    if checked:
        tick = (150, 140, 120, 255) if disabled else (GOLD_HI if hover else GOLD) + (255,)
        d.line([(5.5 * S, 10.5 * S), (8.5 * S, 13.8 * S), (14.8 * S, 6.2 * S)], fill=tick, width=int(2.6 * S), joint="curve")
    save(im, name, 20)


def radio(name, checked, hover=False):
    im = canvas(16)
    d = ImageDraw.Draw(im)
    rim = (GOLD_HI if hover else GOLD) + (255,)
    d.ellipse((1.5 * S, 1.5 * S, 14.5 * S, 14.5 * S), fill=(14, 11, 8, 230), outline=rim, width=int(1.5 * S))
    if checked:
        d.ellipse((5 * S, 5 * S, 11 * S, 11 * S), fill=rim)
    save(im, name, 16)


def arrow(name, direction, size=12, color=GOLD):
    im = canvas(size)
    d = ImageDraw.Draw(im)
    a, b, c = 2.5 * S, (size - 2.5) * S, size / 2 * S
    pts = {
        "down": [(a, a + S), (b, a + S), (c, b - S)],
        "up": [(a, b - S), (b, b - S), (c, a + S)],
        "right": [(a + S, a), (a + S, b), (b - S, c)],
        "left": [(b - S, a), (b - S, b), (a + S, c)],
    }[direction]
    d.polygon(pts, fill=color + (255,))
    save(im, name, size)


def rune(name, size):
    im = canvas(size)
    d = ImageDraw.Draw(im)
    c = size / 2 * S
    r = (size / 2 - 2) * S
    d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=(30, 22, 14, 255), outline=GOLD + (255,), width=int(1.5 * S))
    q = r * 0.45
    d.polygon([(c, c - q), (c + q, c), (c, c + q), (c - q, c)], fill=EMBER + (255,))
    save(im, name, size)


def tooltip_border():
    n = 81
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4 * S, 4 * S, (n - 4) * S, (n - 4) * S), radius=12 * S, fill=(16, 12, 9, 238), outline=GOLD + (255,), width=2 * S)
    d.rounded_rectangle((8 * S, 8 * S, (n - 8) * S, (n - 8) * S), radius=9 * S, outline=(120, 74, 30, 255), width=S)
    im.resize((n, n), Image.LANCZOS).save(os.path.join(OUT, "border-image.png"))


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def gradient_text(base, xy, text, fnt, top, bottom, stroke):
    w, h = base.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt, fill=255)
    box = mask.getbbox()
    if not box:
        return
    outline = Image.new("L", (w, h), 0)
    ImageDraw.Draw(outline).text(xy, text, font=fnt, fill=255, stroke_width=stroke, stroke_fill=255)
    shadow = outline.filter(ImageFilter.GaussianBlur(stroke * 1.5))
    base.paste(Image.new("RGB", (w, h), (0, 0, 0)), (stroke // 2, stroke), shadow.point(lambda v: int(v * 0.85)))
    base.paste(Image.new("RGB", (w, h), (0, 0, 0)), (0, 0), outline)
    grad = Image.new("RGB", (1, h))
    y0, y1 = box[1], box[3]
    for y in range(h):
        t = min(1, max(0, (y - y0) / max(1, y1 - y0)))
        grad.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    base.paste(grad.resize((w, h)), (0, 0), mask)


def centred(base, y, text, fnt, top, bottom, stroke):
    w = ImageDraw.Draw(base).textlength(text, font=fnt)
    gradient_text(base, ((base.width - w) / 2, y), text, fnt, top, bottom, stroke)


def splash():
    w, h = 1200, 675
    im = cover(lift_edges(art(6), 0.42), w, h, 0.4)
    im = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(2.5))).enhance(1.22)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).ellipse((w * 0.12, 40, w * 0.88, 420), fill=255)
    im = Image.composite(Image.new("RGB", (w, h), DARK), im, glow.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * 0.32)))
    centred(im, 70, "RUNESCAPE", font("RuneScape-Quill.ttf", 96), (255, 250, 238), (176, 164, 150), 4)
    centred(im, 150, "DRAGONWILDS", font("RuneScape-Quill.ttf", 150), (255, 196, 96), (206, 64, 22), 6)
    d = ImageDraw.Draw(im)
    for i in range(520):
        t = i / 519
        a = int(255 * (1 - abs(t - 0.5) * 2) ** 0.6)
        c = tuple(int(GOLD[k] + (EMBER[k] - GOLD[k]) * abs(t - 0.5) * 2) for k in range(3))
        d.line([(w / 2 - 260 + i, 322), (w / 2 - 260 + i, 325)], fill=c + (a,))
    centred(im, 340, "MOD ORGANIZER 2", font("RuneScape-Bold-12.ttf", 64), (255, 240, 210), (214, 196, 160), 3)
    im.save(os.path.join(HERE, "splash.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    backgrounds()
    box("checkbox.png", False)
    box("checkbox-hover.png", False, hover=True)
    box("checkbox-checked.png", True)
    box("checkbox-checked-hover.png", True, hover=True)
    box("checkbox-checked-disabled.png", True, disabled=True)
    box("checkbox-disabled.png", False, disabled=True)
    radio("radio.png", False)
    radio("radio-hover.png", False, hover=True)
    radio("radio-checked.png", True)
    radio("radio-checked-hover.png", True, hover=True)
    for direction in ("up", "down", "left", "right"):
        arrow(f"arrow-{direction}.png", direction)
    arrow("branch-closed.png", "right", 14, BONE)
    arrow("branch-open.png", "down", 14, GOLD)
    rune("rune.png", 18)
    tooltip_border()
    splash()
    fonts = os.path.join(OUT, "fonts")
    os.makedirs(fonts, exist_ok=True)
    for f in ("RuneScape-Bold-12.ttf",):
        with open(os.path.join(FONTS, f), "rb") as src, open(os.path.join(fonts, f), "wb") as dst:
            dst.write(src.read())
    print("theme art written to", OUT)


if __name__ == "__main__":
    main()
