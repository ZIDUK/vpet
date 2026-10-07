"""Small, original pixel glyphs for the simulator's practice prototype."""
from functools import lru_cache

from PIL import Image, ImageDraw, ImageOps


PATTERNS = {
    "punch": (
        "................", "....oooooo......", "..oottttttoo....", ".otttltltltto...",
        ".ottthththtto...", ".ottthththtto...", ".ottthththttoo..", "..ottttttttltto.",
        "..otttttttthtto.", "...ottttttthto..", "...otttttttto...", "....otttttto....",
        "....obbbbbbbo...", "....obllllbbo...", "....obbbbbbbo...", ".....ooooooo....",
    ),
    "flame": (
        "........o.......", ".......oro......", "......orro......", ".....orro.......",
        ".....oryro......", "..o.orryrro.....", "..rooryyyrro....", "..orrooyyyrro...",
        ".orryyyyyyyrro..", ".orryyllyyyyrro.", ".oryylllyyyyro..", ".orylllllyyyro..",
        "..oylllllyyro...", "..orylllyyrro...", "...orryyyroo....", ".....ooooo......",
    ),
    "guard": (
        ".......ll.......", "....llllblll....", ".llllbbbbbbllll.", ".lbbbbbbbbbbbbl.",
        ".lbcccbllbccbbl.", ".lbcccbllbccbbl.", "..lbbbllllbbbl..", "..lbbbllllbbbl..",
        "..lbcccllbccbl..", "...lcccllbcbl...", "...lbbbllbbbl...", "....lbbbbcbl....",
        ".....lbbcbl.....", "......lbbl......", ".......ll.......", "................",
    ),
    "auto": (
        "................", "....oooooooo....", "..ooggggggggoo..", ".oggggggggggggo.",
        ".oggllggggllggo.", "ogggllggggllgggo", "oggggggggggggggo", "oggggggggggggggo",
        "ogglgggggggglggo", ".ogllggggggllgo.", ".ogggllllllgggo.", "..oggggggggggo..",
        "...ooggggggoo...", "....oggoooo.....", "....ogo.........", "....oo..........",
    ),
}
PALETTE = {
    ".": (0, 0, 0, 0), "o": (16, 22, 27, 255), "l": (244, 240, 211, 255),
    "t": (226, 179, 112, 255), "h": (141, 87, 61, 255), "b": (49, 109, 151, 255),
    "c": (84, 197, 222, 255), "r": (243, 91, 35, 255), "y": (255, 202, 49, 255),
    "g": (100, 200, 157, 255),
}


def _scale_8(rows):
    """Turn compact 8x8 symbols into crisp 16x16 pixel-art icons."""
    return tuple("".join(pixel * 2 for pixel in row) for row in rows for _ in (0, 1))


INFO_PATTERNS = {
    "heart": _scale_8((
        ".rr.rr..", "rrrrrrrr", "rrrrrrrr", ".rrrrrr.", "..rrrr..",
        "...rr...", "........", "........",
    )),
    "energy": _scale_8((
        "....yy..", "...yy...", "..yy....", ".yyyyyy.", "....yy..",
        "...yy...", "..yy....", "........",
    )),
    "mana": _scale_8((
        "...c....", "..ccc...", "..clc...", ".clccc..", ".clccc..",
        ".ccccc..", "..ccc...", "........",
    )),
    "speed": _scale_8((
        "........", ".c..c...", "..c..c..", "...c..c.", "..c..c..",
        ".c..c...", "........", "........",
    )),
    "mind": _scale_8((
        "..gggg..", ".gbbbbg.", "gbggbbgg", "gbggbbgg", "gggggggg",
        ".gggggg.", "..gggg..", "........",
    )),
    "range": _scale_8((
        "....c...", ".....c..", "cccccccc", "cccccccc", "cccccccc",
        ".....c..", "....c...", "........",
    )),
    "mastery": _scale_8((
        "...y....", "..yyy...", ".yyyyy..", "yyyyyyyy", "..yyy...",
        ".y...y..", "........", "........",
    )),
    "training": _scale_8((
        "........", ".bb..bb.", "bbb..bbb", "bllllllb", "bbb..bbb",
        ".bb..bb.", "........", "........",
    )),
    "bond": _scale_8((
        "........", ".ggg....", "gg.gg...", "g..gggg.", ".gggg..g",
        "...gg.gg", "....ggg.", "........",
    )),
    "lock": _scale_8((
        "..llll..", ".llllll.", ".loooll.", ".loooll.", ".llllll.",
        ".llooll.", ".llllll.", "........",
    )),
}

INFO_ICONS = {
    "hp": "heart", "mp": "mana", "energy": "energy", "attack": "punch", "defense": "guard",
    "speed": "speed", "mind": "mind", "bond": "bond", "power": "punch",
    "cost": "mana", "range": "range", "mastery": "mastery", "training": "training",
    "lock": "lock",
}


@lru_cache(maxsize=16)
def technique_icon(name, locked=False):
    pattern = PATTERNS[name]
    icon = Image.new("RGBA", (16, 16))
    icon.putdata([PALETTE[pixel] for row in pattern for pixel in row])
    if locked:
        silhouette = Image.new("RGBA", icon.size, (103, 117, 120, 255))
        silhouette.putalpha(icon.getchannel("A"))
        icon = silhouette
        draw = ImageDraw.Draw(icon)
        draw.rectangle((9, 8, 13, 12), outline=(255, 220, 70), width=1)
        draw.rectangle((8, 11, 14, 15), fill=(255, 220, 70))
        draw.point((11, 13), fill=(19, 23, 27))
    return icon


@lru_cache(maxsize=48)
def info_icon(name, size=16):
    pattern_name = INFO_ICONS[name]
    pattern = PATTERNS[pattern_name] if pattern_name in PATTERNS else INFO_PATTERNS[pattern_name]
    icon = Image.new("RGBA", (16, 16))
    icon.putdata([PALETTE[pixel] for row in pattern for pixel in row])
    return icon if size == 16 else icon.resize((size, size), Image.Resampling.NEAREST)


def muted_icon(icon):
    gray = ImageOps.grayscale(icon).convert("RGBA")
    gray.putalpha(icon.getchannel("A"))
    return gray
