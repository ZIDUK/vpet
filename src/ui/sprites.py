"""Sprite loading and tile-grid helpers."""
import displayio


def load_bmp(path, transparent_index=0):
    """Load a BMP from disk and return (bitmap, palette).
    Use the palette's make_transparent() if needed."""
    bmp = displayio.OnDiskBitmap(path)
    bmp.pixel_shader.make_transparent(transparent_index)
    return bmp


def make_tile_grid(bmp, x=0, y=0, tile_width=None, tile_height=None):
    """Wrap a BMP in a TileGrid (animated if width > tile_width)."""
    kwargs = {"pixel_shader": bmp.pixel_shader, "x": x, "y": y}
    if tile_width is not None:
        kwargs["tile_width"] = tile_width
    if tile_height is not None:
        kwargs["tile_height"] = tile_height
    return displayio.TileGrid(bmp, **kwargs)
