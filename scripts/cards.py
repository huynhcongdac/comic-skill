"""Cards drawn with real fonts (text always exact): part cover, "previously", "to be continued" / "the end"."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import FONTS

W, H = 1152, 2048
F = lambda weight, size: ImageFont.truetype(str(FONTS / f"BeVietnamPro-{weight}.ttf"), size)
RED, YELLOW, WHITE = (179, 18, 27), (245, 197, 24), (255, 255, 255)


def cover_fit(im):
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)))
    return im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if draw.textlength(t, font=font) <= max_w: cur = t
        else: lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines


def centered(draw, y, text, font, fill=WHITE, max_w=W - 140, gap=1.25, shadow=True):
    for line in wrap(draw, text, font, max_w):
        w = draw.textlength(line, font=font); x = (W - w) / 2
        if shadow: draw.text((x + 3, y + 4), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=fill); y += font.size * gap
    return y


def tag(draw, y, text, size=54, fill=RED, color=WHITE):
    f = F("Black", size); w = draw.textlength(text, font=f)
    draw.rounded_rectangle(((W - w) / 2 - 34, y - 14, (W + w) / 2 + 34, y + size + 18), radius=14, fill=fill)
    draw.text(((W - w) / 2, y - 4), text, font=f, fill=color)
    return y + size + 50


def gradient(im, start, full):
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), 0 if y < start else 255 if y > full else int(255 * (y - start) / (full - start)))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(black, im, g.resize((W, H)))


def make_cards(C, L, P, file):
    parts = C.get("parts") or {}
    n = len(parts)
    for key, info in parts.items():
        p = int(key)
        # part cover: shared cover art + part tag + part title
        if file("cover") and file("cover").exists():
            im = gradient(cover_fit(Image.open(file("cover")).convert("RGB")), int(H * 0.52), int(H * 0.82))
            d = ImageDraw.Draw(im)
            y = tag(d, int(H * 0.70), f"{L['part']} {p}/{n}")
            centered(d, y, info["title"], F("Black", 92))
            im.save(P["img"] / f"card_cover_{p}.png"); print(f"card_cover_{p}")
        # previously (from part 2): 3 thumbnails of the previous part + its summary
        if p > 1:
            prev = parts[str(p - 1)]
            im = Image.new("RGB", (W, H), (14, 12, 18)); d = ImageDraw.Draw(im)
            y = tag(d, 200, L["previously"])
            centered(d, y, prev["title"], F("Black", 76), fill=YELLOW)
            thumbs = [t for t in prev.get("recap", []) if file(t) and file(t).exists()][:3]
            tw, th, gap = 340, 604, 24; x0 = (W - (tw * len(thumbs) + gap * (len(thumbs) - 1))) / 2
            for i, t in enumerate(thumbs):
                im.paste(cover_fit(Image.open(file(t)).convert("RGB")).resize((tw, th)), (int(x0 + i * (tw + gap)), 520))
            centered(d, 1200, prev.get("summary", ""), F("ExtraBold", 50), max_w=W - 220, gap=1.45, shadow=False)
            im.save(P["img"] / f"card_recap_{p}.png"); print(f"card_recap_{p}")
        # to be continued / the end, over a dark blurred page
        bg = file(info.get("endBg", "")) if info.get("endBg") else None
        im = cover_fit(Image.open(bg).convert("RGB")).filter(ImageFilter.GaussianBlur(8)) if bg and bg.exists() else Image.new("RGB", (W, H), (10, 10, 14))
        im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), 0.65); d = ImageDraw.Draw(im)
        if p < n:
            nxt = parts[str(p + 1)]
            y = centered(d, 760, L["next"], F("Black", 120))
            y = centered(d, y + 30, L["nextPart"].format(n=p + 1, title=nxt["title"]), F("ExtraBold", 56), fill=YELLOW)
        else:
            y = centered(d, 760, L["end"], F("Black", 140))
            y = centered(d, y + 30, L["ask"], F("ExtraBold", 56), fill=YELLOW)
        tag(d, y + 80, L["follow"], size=50, fill=YELLOW, color=(17, 17, 17))
        im.save(P["img"] / f"card_end_{p}.png"); print(f"card_end_{p}")
