"""Framed pixel-art navigation symbols, matching the dark menu tiles."""
from PIL import Image, ImageDraw


def render_menu_icon(name, size=20):
    if name not in ("Explore", "Back"):
        raise ValueError(name)
    image = Image.new("RGBA", (32, 32), (5, 9, 14, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 30, 30), outline=(20, 31, 44), width=2)
    draw.line((3, 2, 28, 2), fill=(66, 80, 90), width=1)
    draw.line((2, 3, 2, 28), fill=(43, 58, 72), width=1)
    draw.line((4, 29, 29, 29), fill=(27, 41, 56), width=1)
    draw.rectangle((4, 4, 27, 27), fill=(8, 15, 22))
    if name == "Explore":
        # Compass rose: a gold rim, pale face and a red north needle.
        rim = [(12, 5), (19, 5), (24, 10), (26, 14), (26, 18),
               (22, 24), (18, 26), (13, 26), (7, 22), (5, 18), (5, 13), (8, 8)]
        draw.polygon(rim, fill=(114, 78, 38))
        draw.polygon([(12, 6), (19, 6), (24, 12), (24, 19), (19, 24),
                      (12, 24), (7, 19), (7, 12)], fill=(209, 171, 91))
        draw.polygon([(12, 8), (19, 8), (22, 12), (22, 19), (18, 22),
                      (12, 22), (9, 18), (9, 12)], fill=(205, 212, 193))
        draw.line((12, 6, 19, 6), fill=(255, 236, 172), width=2)
        draw.line((11, 15, 20, 15), fill=(95, 119, 123))
        draw.line((15, 10, 15, 21), fill=(95, 119, 123))
        draw.polygon([(18, 9), (17, 17), (13, 15)], fill=(209, 62, 59))
        draw.polygon([(13, 15), (17, 17), (12, 22)], fill=(51, 107, 140))
        draw.rectangle((15, 15, 16, 16), fill=(255, 239, 176))
    else:
        # Clear left-facing return arrow, shaded like the sword blades.
        draw.polygon([(13, 7), (5, 15), (13, 23), (13, 18), (19, 18),
                      (22, 20), (22, 25), (26, 22), (26, 16),
                      (22, 12), (13, 12)], fill=(111, 77, 35))
        draw.polygon([(12, 8), (6, 15), (12, 21), (12, 17), (20, 17),
                      (23, 20), (23, 23), (25, 21), (25, 16),
                      (21, 13), (12, 13)], fill=(221, 189, 114))
        draw.polygon([(11, 11), (8, 15), (11, 18), (11, 16), (20, 16),
                      (24, 19), (24, 16), (21, 14), (11, 14)], fill=(182, 190, 190))
        draw.line((10, 13, 9, 15), fill=(247, 245, 221), width=1)
        draw.line((12, 14, 20, 14), fill=(247, 245, 221), width=1)
        draw.line((20, 17, 23, 20), fill=(108, 124, 133), width=1)
    return image.resize((size, size), Image.Resampling.LANCZOS)
