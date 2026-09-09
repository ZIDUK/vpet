"""Reusable displayio widgets for the 128x128 screen.

Widgets return (TileGrid, draw_function) so the screen can manage their lifecycle.
"""
import displayio

# ---------- Stat Bar (5px tall) ----------

def make_stat_bar(x, y, color, width=26, height=5, bg_color=0x282828):
    """Create a two-color bar that can be filled via draw_stat_bar()."""
    bmp = displayio.Bitmap(width, height, 2)
    pal = displayio.Palette(2)
    pal[0] = bg_color
    pal[1] = color
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y)
    return bmp, tg


def draw_stat_bar(bmp, value, max_value=100):
    """Fill the bar based on value (0..max_value)."""
    fill = int(bmp.width * value / max_value)
    for x in range(bmp.width):
        on = 1 if x < fill else 0
        for y in range(bmp.height):
            bmp[x, y] = on


# ---------- Action Button (24x24) ----------
#
# A button is either:
#   (a) A solid color square with a centered letter glyph (the original 4x7 pixel
#       F/H/P/E style), or
#   (b) A solid color background with a 24x24 BMP icon drawn on top
#       (loaded from /UIAssets/buttons/<name>.bmp).
#
# Use make_button_letter() for (a), make_button_icon() for (b), or make_button()
# which auto-detects: tries to load the icon first, falls back to letter.

# Pixel-art 4x7 letter glyphs centered in 24x24 (offset = +8)
GLYPHS = {
    "F": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
          (1,0),(2,0),(3,0),(1,3),(2,3),(3,3),(1,4),(2,5)],
    "H": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
          (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),
          (1,3),(2,3)],
    "P": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
          (1,0),(2,0),(3,0),(1,3),(2,3),(3,3),
          (1,1),(1,2),(2,1),(2,2)],
    "E": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
          (1,0),(2,0),(3,0),(1,3),(2,3),(1,6),(2,6),(3,6)],
}


def _load_icon_or_none(path):
    """Try to load a 24x24 BMP icon from disk. Returns (bmp, palette) or None."""
    try:
        bmp = displayio.OnDiskBitmap(path)
        # Make the first palette entry transparent so the icon blends onto the bg
        bmp.pixel_shader.make_transparent(0)
        return bmp
    except (OSError, ValueError):
        return None


def make_button(x, y, bg_color, label, size=24, icon_path=None):
    """Create an action button at (x, y).

    Args:
        x, y: pixel position
        bg_color: 0xRRGGBB color of the button background
        label: short string (F, H, P, E, etc.) used for the letter fallback
        size: button size in pixels (default 24x24)
        icon_path: optional path to a 24x24 BMP icon. If given AND the file
                   exists, the icon is used. Otherwise the letter glyph is used.

    Returns:
        (bg_bmp, bg_tg, icon_tg_or_None) — icon_tg is None if no icon was used.
        You must append BOTH the bg_tg and (if not None) the icon_tg to your
        displayio group, in that order.
    """
    # Background bitmap
    bg = displayio.Bitmap(size, size, 1)
    bg_pal = displayio.Palette(1)
    bg_pal[0] = bg_color
    for xi in range(size):
        for yi in range(size):
            bg[xi, yi] = 0  # fill with bg color (index 0)
    bg_tg = displayio.TileGrid(bg, pixel_shader=bg_pal, x=x, y=y)

    # Try to load an icon
    icon_tg = None
    if icon_path:
        icon_bmp = _load_icon_or_none(icon_path)
        if icon_bmp:
            # Use the icon's own palette (already transparent-set on index 0)
            icon_tg = displayio.TileGrid(
                icon_bmp, pixel_shader=icon_bmp.pixel_shader, x=x, y=y
            )
            return bg, bg_tg, icon_tg

    # Fallback: draw letter glyph
    glyph = GLYPHS.get(label, [])
    for gx, gy in glyph:
        if 0 <= gx + 8 < size and 0 <= gy + 8 < size:
            # Need a 2-color bitmap for the bg so the glyph can use color 1
            # Replace the bg we just made with a 2-color one
            bg2 = displayio.Bitmap(size, size, 2)
            bg2_pal = displayio.Palette(2)
            bg2_pal[0] = bg_color
            bg2_pal[1] = 0xffffff
            for xi in range(size):
                for yi in range(size):
                    bg2[xi, yi] = 0
            for gx, gy in glyph:
                if 0 <= gx + 8 < size and 0 <= gy + 8 < size:
                    bg2[gx + 8, gy + 8] = 1
            # Replace the TileGrid with the 2-color version
            bg2_tg = displayio.TileGrid(bg2, pixel_shader=bg2_pal, x=x, y=y)
            return bg2, bg2_tg, None

    return bg, bg_tg, None


# ---------- Selection Ring (24x24 white border) ----------

def make_selection_ring(x, y, size=24):
    """Create a 1-bit white border for highlighting the selected button.

    Uses 2-color palette: index 0 = transparent (so the inside of the ring
    is invisible and the underlying button shows through), index 1 = white
    (only the border pixels use this).
    """
    bmp = displayio.Bitmap(size, size, 2)
    pal = displayio.Palette(2)
    pal[0] = 0x000000
    pal.make_transparent(0)
    pal[1] = 0xffffff
    for xi in range(size):
        bmp[xi, 0] = 1
        bmp[xi, size - 1] = 1
    for yi in range(size):
        bmp[0, yi] = 1
        bmp[size - 1, yi] = 1
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y)
    return bmp, tg
