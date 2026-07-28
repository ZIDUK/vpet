"""
Extract Agumon animation frames from atlas row images.

For each row PNG:
  - Detect label area (left dense block, ~80px wide)
  - Detect frame boundaries (gaps in content density)
  - Crop each frame to its bbox
  - Make non-Agumon pixels transparent (alpha=0)
  - Pad to square (max bbox w/h), keep aspect ratio
  - Resize to target size (default 64x64)
  - Build 8-bit indexed BMP strip with transparent palette[0]
  - Save to <stage>/scaled/<anim>.bmp
"""

import os
import sys
import numpy as np
from PIL import Image
from collections import Counter

ATLAS_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/sprites/agumon_atlas"
OUT_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/Agumon_atlas/scaled"
os.makedirs(OUT_DIR, exist_ok=True)

# Agumon palette (16 colors max for 4-bit) - common Digimon colors
PALETTE_8BIT = [
    (0, 0, 0),         # 0: transparent (will be set by make_transparent)
    (12, 16, 28),     # 1: very dark blue (background of digivice)
    (32, 24, 16),     # 2: dark brown
    (60, 40, 20),     # 3: brown shadow
    (100, 64, 32),    # 4: dark orange
    (140, 88, 44),    # 5: mid orange
    (200, 128, 56),   # 6: Agumon orange
    (255, 180, 80),   # 7: Agumon light
    (255, 220, 140),  # 8: Agumon highlight
    (200, 60, 60),    # 9: red (hearts, fire)
    (255, 100, 100),  # 10: pink
    (60, 60, 60),     # 11: dark gray (eye)
    (180, 100, 60),   # 12: light brown
    (240, 240, 240),  # 13: white (Z's, sparkles)
    (60, 120, 60),    # 14: green (poop hint)
    (120, 80, 40),    # 15: darker brown
]


def find_frames(im_arr, label_end=80, gap_threshold=2, min_gap=8, min_frame=20):
    """Return list of (x_start, x_end) frame boxes in a row image."""
    brightness = im_arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 60).sum(axis=0)

    # Find content blocks after the label
    blocks = []
    in_block = False
    start = 0
    for i in range(label_end, len(content_per_col)):
        has_content = content_per_col[i] >= gap_threshold
        if has_content:
            if not in_block:
                start = i
                in_block = True
        else:
            if in_block:
                blocks.append((start, i))
                in_block = False
    if in_block:
        blocks.append((start, len(content_per_col)))

    # Merge blocks closer than min_gap
    merged = []
    for s, e in blocks:
        if merged and s - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    # Filter too small
    return [(s, e) for s, e in merged if (e - s) >= min_frame]


def find_label_end(im_arr, max_check=120):
    """Find the rightmost column of the label area (white text on dark bg)."""
    # Label is on the left, with high contrast (white text on dark bg)
    # After label, content density drops to ~0 for several columns
    brightness = im_arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 100).sum(axis=0)  # strict: only bright pixels

    # Walk from left, find first long dim run
    for i in range(20, max_check):
        if content_per_col[i] < 2 and content_per_col[i+1] < 2 and content_per_col[i+2] < 2:
            # Check that we stay dim for 10 more columns
            if (content_per_col[i:i+10] < 3).all():
                return i
    return 80  # default


def crop_to_bbox(im, threshold_alpha=10):
    """Crop to non-transparent bbox. Returns RGBA."""
    arr = np.array(im)
    if arr.shape[2] == 4:
        alpha = arr[:, :, 3]
        mask = alpha > threshold_alpha
    else:
        # No alpha: detect non-bg by brightness
        brightness = arr[:, :, :3].mean(axis=2)
        mask = brightness > 60
    if not mask.any():
        return None
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    top, bottom = rows[0], rows[-1] + 1
    left, right = cols[0], cols[-1] + 1
    return im.crop((left, top, right, bottom))


def quantize_to_8bit(im_rgba, palette, transparent_idx=0):
    """Quantize RGBA image to indexed 8-bit with given palette.
    Pixels matching palette[transparent_idx] (or any near-bg) get that index."""
    arr = np.array(im_rgba)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.int32)
    alpha = arr[:, :, 3]

    # Build distance matrix to each palette color
    pal = np.array(palette, dtype=np.int32)
    dists = np.zeros((h, w, len(pal)), dtype=np.int32)
    for i, c in enumerate(pal):
        d = (rgb - c) ** 2
        dists[:, :, i] = d.sum(axis=2)

    # Nearest palette index
    idx = dists.argmin(axis=2).astype(np.uint8)

    # Override: low alpha → transparent
    idx[alpha < 30] = transparent_idx

    return Image.fromarray(idx, mode="P")


def pad_to_square(im, size, transparent_idx=0):
    """Pad image to square, center it, resize to target size."""
    w, h = im.size
    side = max(w, h)
    square = Image.new("P", (side, side), transparent_idx)
    square.paste(im, ((side - w) // 2, (side - h) // 2))
    return square.resize((size, size), Image.NEAREST)


def process_row(path, name, target=64):
    print(f"\n=== {name} ({os.path.basename(path)}) ===")
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    w, h = im.size

    label_end = find_label_end(arr)
    print(f"  Label ends at col {label_end}, image {w}x{h}")

    frame_cols = find_frames(arr, label_end=label_end)
    print(f"  Detected {len(frame_cols)} frame blocks: {frame_cols}")

    # Convert: bg pixels → transparent
    # bg is dark blue/black. Detect via low brightness AND low saturation
    # Actually easier: any pixel matching bg-color → alpha 0
    # bg is around (10, 18, 30) - dark blue
    rgb = arr[:, :, :3].astype(np.int32)
    bg_dist = ((rgb - np.array([12, 16, 28])) ** 2).sum(axis=2)
    # If pixel is "close to bg" (within distance 800 ~= 28 RGB units), make transparent
    is_bg = bg_dist < 1500
    # Also make green-tinted bg pixels transparent (the line accents)
    # Hmm, the gold lines... keep them, they're part of the design.

    # Use alpha channel if present, else create from bg
    if arr.shape[2] == 4:
        alpha = arr[:, :, 3].copy()
    else:
        alpha = np.full((h, w), 255, dtype=np.uint8)
    alpha[is_bg] = 0

    # Save transparency-applied RGBA
    out_rgba = np.dstack([rgb.astype(np.uint8), alpha])
    im_rgba = Image.fromarray(out_rgba, mode="RGBA")

    # Extract each frame
    frame_bboxes = []
    frames = []
    for i, (xs, xe) in enumerate(frame_cols):
        crop = im_rgba.crop((xs, 0, xe, h))
        bbox = crop_to_bbox(crop)
        if bbox is None:
            print(f"    Frame {i}: empty bbox, skipping")
            continue
        frames.append(bbox)
        frame_bboxes.append(bbox.size)
        print(f"    Frame {i}: {bbox.size} from col {xs}-{xe}")

    if not frames:
        print("  No frames!")
        return None

    # Pad each to square, resize, quantize
    processed = []
    for f in frames:
        sq = pad_to_square(f, target, transparent_idx=0)
        processed.append(sq)

    # Build strip
    strip = Image.new("P", (target * len(processed), target), 0)
    for i, f in enumerate(processed):
        strip.paste(f, (i * target, 0))

    # Set palette
    flat_pal = sum(PALETTE_8BIT, ())
    # Pad to 256 colors
    flat_pal = flat_pal + (0, 0, 0) * (256 - len(PALETTE_8BIT))
    strip.putpalette(flat_pal)

    out_path = os.path.join(OUT_DIR, f"agumon_{name}.bmp")
    strip.save(out_path)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"  -> {out_path} ({len(processed)} frames, {size_kb:.1f}KB)")
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

    target = 64
    if len(sys.argv) > 1:
        target = int(sys.argv[1])

    print(f"Target size: {target}x{target}")
    results = []
    for fname, name in rows:
        path = os.path.join(ATLAS_DIR, fname)
        if not os.path.exists(path):
            print(f"Missing: {path}")
            continue
        r = process_row(path, name, target=target)
        if r:
            results.append(r)

    print(f"\n=== Generated {len(results)} strips ===")
    for r in results:
        size_kb = os.path.getsize(r) / 1024
        print(f"  {r} ({size_kb:.1f}KB)")
