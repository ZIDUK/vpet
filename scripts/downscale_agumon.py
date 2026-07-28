"""
Downscale Agumon animations to 32x32 per frame horizontal strips.
- Detects frame boundaries (columns that are mostly background palette 0)
- Crops each frame, finds tight bbox
- Downscales to fit in 32x32 with transparency padding
- Saves as 8-bit indexed BMP with palette 0 = transparent
"""
import os
from PIL import Image

ANIM_DIR = os.path.join(os.path.dirname(__file__), '..', 'Agumon')
OUT_DIR = os.path.join(ANIM_DIR, 'scaled')
os.makedirs(OUT_DIR, exist_ok=True)

TARGET = 32
MIN_RATIO = 0.20
MAX_GAP = 4
MIN_WIDTH = 30


def detect_frames(img_p):
    """Return list of (x_start, x_end) for each frame in a P-mode image."""
    w, h = img_p.size
    px = img_p.load()
    intensity = [0] * w
    for x in range(w):
        for y in range(h):
            if px[x, y] != 0:
                intensity[x] += 1
    threshold = MIN_RATIO * h
    is_frame = [intensity[x] >= threshold for x in range(w)]
    raw = []
    in_seg = False
    start = 0
    gap = 0
    for x in range(w):
        if is_frame[x]:
            if not in_seg:
                start = x
                in_seg = True
            gap = 0
        else:
            if in_seg:
                gap += 1
                if gap > MAX_GAP:
                    raw.append((start, x - gap + 1))
                    in_seg = False
                    gap = 0
    if in_seg:
        raw.append((start, w))
    return [s for s in raw if s[1] - s[0] >= MIN_WIDTH]


def crop_to_rgba(img_p, x0, x1, pad=2):
    """Crop frame region with optional padding, return RGBA (transparent where idx 0)."""
    w, h = img_p.size
    x0 = max(0, x0 - pad)
    x1 = min(w, x1 + pad)
    # Find vertical extent of non-zero in this x range
    px = img_p.load()
    y0 = h
    y1 = 0
    for x in range(x0, x1):
        for y in range(h):
            if px[x, y] != 0:
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    if y1 < y0:
        return None  # empty frame
    # Crop
    cropped = img_p.crop((x0, y0, x1, y1 + 1))
    rgba = Image.new('RGBA', cropped.size, (0, 0, 0, 0))
    # Manual paste: idx 0 = transparent, others = palette color
    src_px = cropped.load()
    pal = img_p.getpalette()
    dst_px = rgba.load()
    for y in range(cropped.size[1]):
        for x in range(cropped.size[0]):
            idx = src_px[x, y]
            if idx == 0:
                dst_px[x, y] = (0, 0, 0, 0)
            else:
                r = pal[idx * 3]
                g = pal[idx * 3 + 1]
                b = pal[idx * 3 + 2]
                dst_px[x, y] = (r, g, b, 255)
    return rgba


def downscale_to_32(rgba, target=TARGET):
    """Downscale RGBA to fit in target×target, preserving aspect, transparent pad."""
    w, h = rgba.size
    scale = min(target / w, target / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    if (new_w, new_h) != (w, h):
        # Use NEAREST to keep pixel-art feel
        scaled = rgba.resize((new_w, new_h), Image.NEAREST)
    else:
        scaled = rgba
    # Pad to target
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    ox = (target - new_w) // 2
    oy = (target - new_h) // 2
    canvas.paste(scaled, (ox, oy), scaled)
    return canvas


def make_strip_bmp(frames_rgba, out_path):
    """Combine list of 32x32 RGBA frames into a horizontal strip saved as 8-bit BMP.
    Palette 0 = transparent black (alpha 0).
    """
    n = len(frames_rgba)
    if n == 0:
        return None
    # Build full RGBA strip
    strip = Image.new('RGBA', (TARGET * n, TARGET), (0, 0, 0, 0))
    for i, fr in enumerate(frames_rgba):
        strip.paste(fr, (i * TARGET, 0), fr)
    # Composite on opaque black so quantization has a clear background to map to idx 0
    bg = Image.new('RGB', strip.size, (0, 0, 0))
    composite = Image.alpha_composite(bg.convert('RGBA'), strip)
    rgb = composite.convert('RGB')
    # Quantize: we want palette 0 = (0,0,0) and other indices for the sprite
    # Use 255 colors so we have room + idx 0 reserved for transparent
    p = rgb.quantize(colors=255, method=2, dither=Image.NONE)
    # Shift palette: current idx 0 might be (0,0,0) from quantization,
    # but we need a *dedicated* idx 0 for transparency. Since the source has black
    # background that became idx 0, that's actually fine — keep idx 0 as the
    # black/transparent color and let the sprite use 1..255.
    # Verify: ensure idx 0 is (0,0,0)
    pal = p.getpalette()
    pal[0] = 0
    pal[1] = 0
    pal[2] = 0
    p.putpalette(pal)
    p.save(out_path, 'BMP')
    return p


def process(name, input_name, out_name):
    src = os.path.join(ANIM_DIR, input_name)
    if not os.path.exists(src):
        print(f"  SKIP {input_name} (missing)")
        return
    img = Image.open(src)
    frames = detect_frames(img)
    print(f"  {input_name}: {img.size} -> {len(frames)} frames")
    if not frames:
        return
    downscaled = []
    for x0, x1 in frames:
        rgba = crop_to_rgba(img, x0, x1)
        if rgba is None:
            continue
        small = downscale_to_32(rgba)
        downscaled.append(small)
    out_path = os.path.join(OUT_DIR, out_name)
    res = make_strip_bmp(downscaled, out_path)
    if res:
        print(f"    -> {out_path} ({res.size[0]}x{res.size[1]}, {os.path.getsize(out_path)} bytes)")


if __name__ == '__main__':
    process('idle', 'idle.bmp', 'agumon_idle.bmp')
    process('walk', 'walk.bmp', 'agumon_walk.bmp')
    process('eat', 'eat.bmp', 'agumon_eat.bmp')
    process('attack', 'attack.bmp', 'agumon_attack.bmp')
    process('hurt', 'hurt.bmp', 'agumon_hurt.bmp')
    process('sleep', 'sleep.bmp', 'agumon_sleep.bmp')
    process('happy', 'happy.bmp', 'agumon_happy.bmp')
    process('evolve', 'evolve.bmp', 'agumon_evolve.bmp')
    print(f"\nDone. Files in {OUT_DIR}/")
