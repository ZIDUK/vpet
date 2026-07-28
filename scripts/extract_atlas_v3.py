"""
v3: numpy-based 4-bit quantization (avoids PIL.quantize hang).
Fixed 16-color palette tuned to Agumon, nearest-color matching with numpy.
"""
import os, sys
import numpy as np
from PIL import Image

ATLAS_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/sprites/agumon_atlas"
OUT_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/Agumon_atlas/scaled"
os.makedirs(OUT_DIR, exist_ok=True)

# 16-color palette tuned to Agumon's actual colors
# 0: transparent
# 1-15: visible colors
PALETTE = [
    (0, 0, 0),          # 0: transparent
    (32, 24, 16),       # 1: very dark brown (outline)
    (90, 50, 24),       # 2: dark brown shadow
    (148, 88, 40),      # 3: brown
    (210, 130, 60),     # 4: dark orange
    (255, 175, 85),     # 5: Agumon orange (main)
    (255, 215, 140),    # 6: Agumon light
    (255, 245, 200),    # 7: Agumon highlight (belly)
    (60, 50, 40),       # 8: dark eye/mouth
    (200, 60, 50),      # 9: red (hearts, fire core)
    (255, 130, 80),     # 10: orange-red (fire mid)
    (255, 220, 100),    # 11: yellow (fire outer, sparkles)
    (240, 240, 240),    # 12: white (Z's, sparkles)
    (140, 100, 60),     # 13: light brown (poop)
    (90, 60, 30),       # 14: dark brown (poop shadow)
    (180, 200, 80),     # 15: green-yellow (poop highlight, vomit)
]


def find_label_end(arr, max_check=120):
    brightness = arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 100).sum(axis=0)
    for i in range(20, max_check):
        if (content_per_col[i:i+10] < 3).all():
            return i
    return 80


def find_frames(arr, label_end=80, min_frame=20):
    brightness = arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 60).sum(axis=0)
    blocks = []
    in_block, start = False, 0
    for i in range(label_end, len(content_per_col)):
        if content_per_col[i] >= 2:
            if not in_block:
                start = i
                in_block = True
        else:
            if in_block:
                blocks.append((start, i))
                in_block = False
    if in_block:
        blocks.append((start, len(content_per_col)))
    merged = []
    for s, e in blocks:
        if merged and s - merged[-1][1] < 6:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return [(s, e) for s, e in merged if (e - s) >= min_frame]


def crop_to_bbox(im, threshold_alpha=10):
    arr = np.array(im)
    if arr.shape[2] == 4:
        mask = arr[:, :, 3] > threshold_alpha
    else:
        mask = arr[:, :, :3].mean(axis=2) > 60
    if not mask.any():
        return None
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def pad_to_square_rgba(im, size):
    w, h = im.size
    side = max(w, h)
    arr = np.array(im)
    if arr.shape[2] == 4:
        square = np.zeros((side, side, 4), dtype=np.uint8)
    else:
        square = np.zeros((side, side, 3), dtype=np.uint8)
    square[(side - h) // 2:(side - h) // 2 + h, (side - w) // 2:(side - w) // 2 + w] = arr
    pil_sq = Image.fromarray(square, mode="RGBA" if square.shape[2] == 4 else "RGB")
    return pil_sq.resize((size, size), Image.LANCZOS)


def quantize_rgba(arr_rgba, palette, transparent_idx=0):
    """arr_rgba: HxWx4 uint8. Returns HxW uint8 indices."""
    h, w = arr_rgba.shape[:2]
    rgb = arr_rgba[:, :, :3].astype(np.int32)
    alpha = arr_rgba[:, :, 3]

    pal = np.array(palette, dtype=np.int32)
    # Distance to each palette color: HxWxN
    dists = np.zeros((h, w, len(pal)), dtype=np.int32)
    for i, c in enumerate(pal):
        d = (rgb - c[None, None, :]) ** 2
        dists[:, :, i] = d.sum(axis=2)

    idx = dists.argmin(axis=2).astype(np.uint8)
    # Force transparent where alpha is low
    idx[alpha < 30] = transparent_idx
    return idx


def process_row(path, name, target=64):
    print(f"\n=== {name} ({os.path.basename(path)}) ===")
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    w, h = im.size

    label_end = find_label_end(arr)
    frame_cols = find_frames(arr, label_end=label_end)
    print(f"  {w}x{h}, label_end={label_end}, {len(frame_cols)} frames: {frame_cols}")

    # Make bg transparent (dark blue)
    rgb = arr[:, :, :3].astype(np.int32)
    bg_dist = ((rgb - np.array([12, 16, 28])) ** 2).sum(axis=2)
    is_bg = bg_dist < 1500
    alpha = arr[:, :, 3].copy() if arr.shape[2] == 4 else np.full((h, w), 255, dtype=np.uint8)
    alpha[is_bg] = 0
    rgba_clean = np.dstack([rgb.astype(np.uint8), alpha])
    im_clean = Image.fromarray(rgba_clean, mode="RGBA")

    frames = []
    for i, (xs, xe) in enumerate(frame_cols):
        crop = im_clean.crop((xs, 0, xe, h))
        bbox = crop_to_bbox(crop)
        if bbox is None:
            continue
        # Pad to square, resize
        padded = pad_to_square_rgba(bbox, target)
        frames.append(np.array(padded))

    if not frames:
        return None

    # Quantize each frame
    quantized = [quantize_rgba(f, PALETTE) for f in frames]

    # Build strip
    strip = np.zeros((target, target * len(quantized)), dtype=np.uint8)
    for i, q in enumerate(quantized):
        strip[:, i * target:(i + 1) * target] = q

    # Save as 8-bit BMP (displayio handles; pal[0]=transparent)
    strip_im = Image.fromarray(strip, mode="P")
    flat_pal = sum(PALETTE, ())
    flat_pal = flat_pal + (0, 0, 0) * (256 - len(PALETTE))
    strip_im.putpalette(flat_pal)
    out_path = os.path.join(OUT_DIR, f"agumon_{name}.bmp")
    strip_im.save(out_path)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"  -> {out_path} ({len(quantized)} frames, {size_kb:.1f}KB)")
    return out_path


if __name__ == "__main__":
    rows = [
        ("01_idle.png", "idle"),
        ("02_walk.png", "walk"),
        ("03_run.png", "run"),
        ("04_attack.png", "attack"),
        ("05_hurt.png", "hurt"),
        ("06_eat.png", "eat"),
        ("07_sleep.png", "sleep"),
        ("08_happy.png", "happy"),
        ("09_poop.png", "poop"),
        ("10_victory.png", "victory"),
    ]
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    print(f"Target: {target}x{target}, fixed 16-color palette")
    results = []
    for fname, name in rows:
        path = os.path.join(ATLAS_DIR, fname)
        if not os.path.exists(path):
            continue
        r = process_row(path, name, target)
        if r:
            results.append(r)
    print(f"\n=== {len(results)} strips ===")
    total = 0
    for r in results:
        s = os.path.getsize(r)
        total += s
        print(f"  {os.path.basename(r):30s} {s/1024:6.1f}KB")
    print(f"  TOTAL: {total/1024:.1f}KB")
