"""Prepare small, transparent UI assets from the approved raster artwork."""
from pathlib import Path

from PIL import Image


NAMES = ("face_happy", "face_neutral", "face_sad", "face_angry",
         "food", "food_angry", "rest", "rest_angry", "hurt", "sad", "angry",
         "energy", "energy_angry")


def _fit(image, size):
    image = image.convert("RGBA")
    image.putalpha(image.getchannel("A").point(lambda value: 255 if value >= 192 else 0))
    bounds = image.getbbox()
    if bounds is None:
        raise ValueError("Empty mood artwork")
    image = image.crop(bounds)
    image.thumbnail(size, Image.Resampling.NEAREST)
    return image


def _center(canvas, image, box):
    x, y, width, height = box
    canvas.alpha_composite(image, (x + (width-image.width)//2, y + (height-image.height)//2))


def build_mood_assets(root, output_dir):
    from scripts.build import _quantize_rgba_with_transparency

    root, output_dir = Path(root), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(root / "assets/ui/mood/mood-atlas-v1.png") as source:
        atlas = source.convert("RGBA")
    if atlas.size != (1536, 1024):
        raise ValueError("Mood atlas must contain six 512x512 cells")
    cells = [atlas.crop((x*512, y*512, (x+1)*512, (y+1)*512))
             for y in range(2) for x in range(3)]
    images = {}
    for name, cell in zip(NAMES[:4], cells[:4]):
        canvas = Image.new("RGBA", (20, 20))
        _center(canvas, _fit(cell, (18, 18)), (1, 1, 18, 18))
        images[name] = canvas

    blank = Image.new("RGBA", (32, 28))
    _center(blank, _fit(cells[4], (30, 26)), (1, 1, 30, 26))
    content = {"food": "assets/ui/items/meat.png",
               "rest": "assets/ui/icons/Rest.png",
               "energy": "assets/ui/icons/Energy.png",
               "hurt": "assets/ui/items/adopted/bandage.png"}
    for name, path in content.items():
        with Image.open(root / path) as source:
            art = source.convert("RGBA")
        if name in ("rest","energy"):
            # Menu icons include a dark tile; keep only the lit glyph.
            light = art.convert("L").point(lambda value: 255 if value >= 72 else 0)
            art.putalpha(light)
        glyph = _fit(art, (16, 16))
        canvas = blank.copy()
        _center(canvas, glyph, (7, 2, 18, 19))
        images[name] = canvas
        if name in ("rest","energy"):
            canvas = blank.copy()
            _center(canvas, _fit(glyph, (12, 14)), (4, 3, 14, 18))
            _center(canvas, _fit(cells[5], (8, 8)), (21, 3, 8, 8))
            images[name+"_angry"] = canvas
    for name, cell in (("sad", cells[2]), ("angry", cells[3])):
        canvas = blank.copy()
        _center(canvas, _fit(cell, (15, 15)), (7, 2, 18, 19))
        images[name] = canvas
    with Image.open(root / "assets/ui/mood/food-angry-v1.png") as source:
        canvas = Image.new("RGBA", (32, 28))
        _center(canvas, _fit(source, (30, 26)), (1, 1, 30, 26))
        images["food_angry"] = canvas
    paths = []
    for name in NAMES:
        path = output_dir / (name + ".bmp")
        _quantize_rgba_with_transparency(images[name]).save(path, format="BMP")
        paths.append(path)
    return paths
