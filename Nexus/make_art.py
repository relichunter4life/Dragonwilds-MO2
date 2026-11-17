# Made by Claude Ai & Relic Hunter
import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "theme", "splash_chatgpt_original.png")
TITLE_BOX = (250, 185, 1455, 565)
GOLD = (214, 168, 92)


def thumbnail(art):
    im = art.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
    im.save(os.path.join(HERE, "DragonwildsMO2-Thumbnail-1920.jpg"), quality=93)


def header(art, style):
    W, H = 1300, 372
    w, h = art.size
    bw = 1740
    big = art.resize((bw, round(h * bw / w)), Image.LANCZOS)
    top = min(big.height - H, round(TITLE_BOX[3] * bw / w) + 10)
    left = (bw - W) // 2
    band = big.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(1.2))
    band = ImageEnhance.Brightness(band).enhance(0.92).convert("RGBA")
    title = art.crop(TITLE_BOX)
    th = 196
    tw = round(title.width * th / title.height)
    title = title.resize((tw, th), Image.LANCZOS)
    x, y = (W - tw) // 2, 12
    if style == "plaque":
        shadow = Image.new("RGBA", band.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([x + 6, y + 10, x + tw + 10, y + th + 14], 14, fill=(0, 0, 0, 200))
        band.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
        rim = ImageDraw.Draw(band)
        rim.rounded_rectangle([x - 7, y - 7, x + tw + 6, y + th + 6], 12, fill=(10, 8, 6, 255))
        rim.rounded_rectangle([x - 4, y - 4, x + tw + 3, y + th + 3], 10, outline=GOLD, width=2)
        mask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, th - 1], 9, fill=255)
        band.paste(title, (x, y), mask)
    else:
        mask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mask).rounded_rectangle([34, 22, tw - 35, th - 23], 60, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(18))
        band.paste(title, (x, y), mask)
    band.convert("RGB").save(os.path.join(HERE, f"DragonwildsMO2-Header-1300x372-{style}.jpg"), quality=93)


art = Image.open(SRC).convert("RGB")
thumbnail(art)
header(art, "plaque")
header(art, "glow")
print("ok")
