"""
Build missing UI icons (BATH, HEALTH, SCAN, DIGIDEX, DIGIVOLVE, MAP, STATUS, OPTIONS)
as 18x18 8-bit indexed BMPs with palette 0 = transparent.
Style: simple line-art in yellow on black, matching the existing icon set.
"""
import os
from PIL import Image, ImageDraw

ICONS = '/Users/jonathanpardofuentes/Documents/Arduino/vPet/icons'
OUT = '/Users/jonathanpardofuentes/Documents/Arduino/vPet/icons'

SIZE = 18
# Colors that match the existing yellow-on-dark theme
FG = (240, 180, 30)   # yellow
BG = (20, 30, 50)     # dark blue (will be palette idx 1)

def make_icon(name, draw_fn):
    img = Image.new('RGB', (SIZE, SIZE), (0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d)
    # Quantize: palette 0 = black (transparent), palette 1 = FG
    p = img.quantize(colors=2, method=0, dither=Image.NONE)
    pal = [0, 0, 0,  # 0 = transparent black
           240, 180, 30] + [0] * (256 * 3 - 6)
    p.putpalette(pal)
    out_path = os.path.join(OUT, f'{name}.bmp')
    p.save(out_path, 'BMP')
    return out_path

# BATH: water drop
def bath(d):
    # teardrop: top point, rounded bottom
    d.polygon([(9, 1), (4, 10), (4, 14), (9, 17), (14, 14), (14, 10)], outline=FG, width=1)
    # water lines
    for y in [12, 14]:
        d.line((7, y, 11, y), fill=FG)
    d.line((8, 11, 10, 11), fill=FG)

# HEALTH: plus/cross
def health(d):
    d.rectangle((7, 1, 11, 16), outline=FG, fill=FG)
    d.rectangle((1, 7, 16, 11), outline=FG, fill=FG)

# SCAN: radar/wifi
def scan(d):
    d.pieslice((1, 4, 16, 16), 220, 320, outline=FG, width=1)
    d.pieslice((4, 6, 13, 15), 220, 320, outline=FG, width=1)
    d.ellipse((7, 10, 10, 13), outline=FG, fill=FG)
    # pulse dot top-right
    d.ellipse((13, 1, 16, 4), outline=FG, fill=FG)

# DIGIDEX: book
def digidex(d):
    d.rectangle((1, 3, 16, 15), outline=FG, width=1)
    d.line((8, 3, 8, 15), fill=FG)
    for y in [6, 9, 12]:
        d.line((2, y, 7, y), fill=FG)
        d.line((9, y, 15, y), fill=FG)

# DIGIVOLVE: up arrow with sparkles
def digivolve(d):
    d.polygon([(9, 1), (4, 7), (7, 7), (7, 16), (11, 16), (11, 7), (14, 7)], outline=FG, fill=FG)
    # sparkles
    d.ellipse((1, 11, 3, 13), fill=FG)
    d.ellipse((15, 13, 17, 15), fill=FG)

# MAP: pin
def mapicon(d):
    d.ellipse((4, 1, 14, 11), outline=FG, width=1)
    d.ellipse((7, 4, 11, 8), outline=FG, fill=FG)
    d.polygon([(9, 9), (5, 17), (13, 17)], outline=FG)

# STATUS: bar chart
def status(d):
    d.rectangle((1, 12, 4, 16), outline=FG, fill=FG)
    d.rectangle((5, 8, 8, 16), outline=FG, fill=FG)
    d.rectangle((9, 4, 12, 16), outline=FG, fill=FG)
    d.rectangle((13, 10, 16, 16), outline=FG, fill=FG)

# OPTIONS: gear
def options(d):
    cx, cy = 9, 9
    r = 5
    # gear teeth (8 little squares around)
    for ang in range(0, 360, 45):
        import math
        rad = math.radians(ang)
        x = cx + int((r+2) * math.cos(rad)) - 1
        y = cy + int((r+2) * math.sin(rad)) - 1
        d.rectangle((x, y, x+2, y+2), fill=FG)
    d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=FG, width=1)
    d.ellipse((cx-2, cy-2, cx+2, cy+2), fill=FG)

# CALL: speech bubble
def call(d):
    d.ellipse((1, 1, 16, 13), outline=FG, width=1)
    d.polygon([(4, 12), (3, 17), (8, 12)], outline=FG)
    d.line((5, 5, 12, 5), fill=FG)
    d.line((5, 8, 12, 8), fill=FG)
    d.line((5, 11, 10, 11), fill=FG)

# FEED: existing eat icons are fine, but let's also do a custom one
def feed(d):
    # meat on bone
    d.ellipse((3, 7, 8, 12), outline=FG, fill=FG)
    d.line((7, 9, 16, 4), fill=FG, width=1)
    d.line((7, 9, 16, 14), fill=FG, width=1)
    d.ellipse((14, 2, 17, 5), fill=FG)
    d.ellipse((14, 13, 17, 16), fill=FG)

# Generate all
for name, fn in [('bath', bath), ('health', health), ('scan', scan),
                 ('digidex', digidex), ('digivolve', digivolve), ('mapicon', mapicon),
                 ('status', status), ('options', options), ('call', call), ('feed', feed)]:
    p = make_icon(name, fn)
    print(f"  {p} ({os.path.getsize(p)} bytes)")
print("done")
