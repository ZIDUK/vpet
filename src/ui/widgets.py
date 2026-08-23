"""Reusable displayio widgets for the 128x128 screen.

Widgets return (TileGrid, draw_function) so the screen can manage their lifecycle.
"""
import displayio


# ---------- Stat Bar (5px tall) ----------

def make_stat_bar(x, y, color, width=26, height=5):
    """Create a 1-bit bar that can be filled/unfilled via draw_stat_bar()."""
    bmp = displayio.Bitmap(width, height, 1)
    pal = displayio.Palette(1)
    pal[0] = color
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


def make_button(x, y, bg_color, label, size=24):
    """Create a colored button with a centered letter label."""
    bmp = displayio.Bitmap(size, size, 2)
    pal = displayio.Palette(2)
    pal[0] = bg_color
    pal[1] = 0xffffff
    # Default: all bg
    for xi in range(size):
        for yi in range(size):
            bmp[xi, yi] = 0
    # Draw glyph
    for gx, gy in GLYPHS[label]:
        if 0 <= gx + 8 < size and 0 <= gy + 8 < size:
            bmp[gx + 8, gy + 8] = 1
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y)
    return bmp, tg


# ---------- Selection Ring (24x24 white border) ----------

def make_selection_ring(x, y, size=24):
    """Create a 1-bit white border for highlighting the selected button."""
    bmp = displayio.Bitmap(size, size, 1)
    pal = displayio.Palette(1)
    pal[0] = 0xffffff
    for xi in range(size):
        bmp[xi, 0] = 1
        bmp[xi, size - 1] = 1
    for yi in range(size):
        bmp[0, yi] = 1
        bmp[size - 1, yi] = 1
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y)
    return bmp, tg
