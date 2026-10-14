"""Small hand-authored pixel icons shared by the T-Display and simulator."""
from PIL import Image, ImageDraw


ICON_NAMES = (
    "Backpack",
    "ItemMeat",
    "ItemEnergy",
    "ItemExp",
    "ItemRing",
    "ItemProtein",
    "ItemMedkit",
)

_COLORS = {
    "outline": (13, 20, 30, 255),
    "tile": (27, 47, 53, 255),
    "tile_edge": (52, 82, 84, 255),
    "blue": (49, 104, 151, 255),
    "blue_light": (88, 164, 195, 255),
    "blue_dark": (30, 64, 103, 255),
    "leather": (137, 75, 43, 255),
    "leather_light": (208, 126, 61, 255),
    "gold": (255, 205, 63, 255),
    "gold_light": (255, 237, 145, 255),
    "red": (203, 57, 56, 255),
    "red_light": (246, 103, 65, 255),
    "cream": (245, 232, 185, 255),
    "white": (246, 247, 230, 255),
    "cyan": (52, 195, 220, 255),
    "cyan_light": (155, 244, 236, 255),
    "green": (55, 155, 116, 255),
    "green_light": (135, 219, 150, 255),
}


def render_item_icon(name, size=16):
    """Return one crisp RGBA pixel-art icon at the requested square size."""
    if name not in ICON_NAMES:
        raise ValueError(f"Unknown item icon: {name}")
    scale = 2
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def rect(box, color):
        x0, y0, x1, y1 = box
        draw.rectangle((x0 * scale, y0 * scale, (x1 + 1) * scale - 1,
                        (y1 + 1) * scale - 1), fill=_COLORS[color])

    def poly(points, color):
        draw.polygon([(x * scale, y * scale) for x, y in points], fill=_COLORS[color])

    def tile():
        if name == "Backpack":
            rect((0, 0, 15, 15), "outline")
            rect((1, 1, 14, 14), "tile")
        else:
            rect((0, 0, 15, 15), "tile_edge")
            rect((1, 1, 14, 14), "tile")
            rect((1, 1, 14, 1), "blue_dark")

    tile()
    if name == "Backpack":
        rect((5, 2, 10, 4), "leather")
        rect((4, 4, 11, 13), "outline")
        rect((5, 5, 10, 12), "blue")
        rect((6, 5, 9, 6), "blue_light")
        rect((5, 8, 10, 10), "blue_dark")
        rect((6, 8, 9, 10), "blue")
        rect((7, 9, 8, 10), "gold")
        rect((3, 6, 4, 11), "leather")
        rect((11, 6, 12, 11), "leather")
        rect((4, 11, 5, 13), "leather_light")
        rect((10, 11, 11, 13), "leather_light")
        rect((7, 3, 8, 3), "gold_light")
    elif name == "ItemMeat":
        poly([(4, 5), (6, 3), (10, 3), (12, 5), (12, 9), (10, 12),
              (6, 12), (4, 10)], "outline")
        poly([(5, 5), (7, 4), (10, 4), (11, 6), (11, 9), (9, 11),
              (6, 10), (5, 8)], "red")
        rect((7, 4, 9, 5), "red_light")
        rect((6, 7, 7, 8), "leather_light")
        rect((10, 10, 11, 11), "red_light")
        rect((3, 10, 5, 11), "cream")
        rect((2, 9, 3, 10), "white")
        rect((4, 12, 5, 13), "white")
        rect((4, 10, 4, 10), "leather")
    elif name == "ItemEnergy":
        rect((6, 3, 9, 4), "outline")
        rect((7, 2, 8, 3), "gold")
        rect((6, 4, 9, 5), "blue_light")
        poly([(5, 6), (10, 6), (11, 8), (11, 12), (10, 13), (5, 13),
              (4, 12), (4, 8)], "outline")
        poly([(6, 7), (9, 7), (10, 9), (10, 12), (5, 12), (5, 9)], "cyan")
        rect((6, 8, 7, 10), "cyan_light")
        rect((8, 11, 9, 12), "blue_light")
    elif name == "ItemExp":
        poly([(8, 2), (9, 5), (12, 5), (10, 7), (11, 11), (8, 9),
              (5, 11), (6, 7), (4, 5), (7, 5)], "outline")
        poly([(8, 3), (9, 6), (11, 6), (9, 8), (10, 10), (8, 8),
              (6, 10), (7, 8), (5, 6), (7, 6)], "gold")
        rect((7, 5, 8, 6), "gold_light")
        rect((8, 7, 9, 8), "red_light")
        rect((7, 12, 9, 13), "blue_light")
    elif name == "ItemRing":
        rect((5, 3, 10, 4), "outline")
        rect((3, 5, 4, 10), "outline")
        rect((11, 5, 12, 10), "outline")
        rect((5, 11, 10, 12), "outline")
        rect((5, 4, 10, 5), "gold")
        rect((4, 5, 5, 10), "gold")
        rect((10, 5, 11, 10), "gold_light")
        rect((5, 10, 10, 11), "gold")
        rect((6, 6, 9, 9), "tile")
        poly([(7, 2), (9, 3), (9, 5), (7, 6), (5, 5), (5, 3)], "red")
        rect((7, 3, 8, 3), "red_light")
    elif name == "ItemProtein":
        rect((5, 3, 10, 4), "outline")
        rect((6, 2, 9, 3), "green_light")
        poly([(5, 5), (10, 5), (11, 7), (11, 12), (10, 13), (5, 13),
              (4, 12), (4, 7)], "outline")
        poly([(6, 6), (9, 6), (10, 8), (10, 12), (5, 12), (5, 8)], "green")
        rect((6, 7, 6, 10), "green_light")
        rect((7, 9, 8, 9), "white")
        rect((6, 8, 6, 10), "white")
        rect((9, 8, 9, 10), "white")
        rect((8, 8, 8, 10), "white")
    elif name == "ItemMedkit":
        rect((6, 3, 9, 4), "white")
        rect((5, 4, 10, 5), "outline")
        rect((4, 6, 11, 12), "outline")
        rect((5, 7, 10, 11), "white")
        rect((7, 7, 8, 11), "red")
        rect((6, 8, 9, 9), "red")
        rect((5, 11, 10, 12), "blue_light")

    return image.resize((size, size), Image.Resampling.NEAREST)
