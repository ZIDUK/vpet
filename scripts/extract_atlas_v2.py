"""
Extract Agumon animation frames from atlas row images.
v2: Smart 4-bit quantization using median cut + dithering.
"""

import os
import sys
import numpy as np
from PIL import Image

ATLAS_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/sprites/agumon_atlas"
OUT_DIR = "/Users/jonathanpardofuentes/Documents/Arduino/vPet/Agumon_atlas/scaled"
os.makedirs(OUT_DIR, exist_ok=True)


def find_label_end(im_arr, max_check=120):
    """Find rightmost column of the label area."""
    brightness = im_arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 100).sum(axis=0)
    for i in range(20, max_check):
        if (content_per_col[i:i+10] < 3).all():
            return i
    return 80


def find_frames(im_arr, label_end=80, min_frame=20):
    """Return list of (x_start, x_end) frame boxes."""
    brightness = im_arr[:, :, :3].mean(axis=2)
    content_per_col = (brightness > 60).sum(axis=0)
    blocks = []
    in_block = False
    start = 0
    for i in range(label_end, len(content_per_col)):
        has_content = content_per_col[i] >= 2
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
    # Merge close blocks
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
        alpha = arr[:, :, 3]
        mask = alpha > threshold_alpha
    else:
        brightness = arr[:, :, :3].mean(axis=2)
        mask = brightness > 60
    if not mask.any():
        return None
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def pad_to_square(im, size, transparent_idx=0):
    w, h = im.size
    side = max(w, h)
    square = Image.new("P", (side, side), transparent_idx)
    square.paste(im, ((side - w) // 2, (side - h) // 2))
    return square.resize((size, size), Image.NEAREST)


def quantize_to_4bit(im_rgba, n_colors=15, transparent_idx=0):
    """Quantize to 4-bit (16 colors). Index 0 = transparent."""
    # Step 1: split into opaque and transparent
    arr = np.array(im_rgba)
    h, w = arr.shape[:2]
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3]
    transparent_mask = alpha < 30

    # Step 2: create an image with only opaque pixels, fill transparent with placeholder
    rgb_for_quant = rgb.copy()
    rgb_for_quant[transparent_mask] = [0, 0, 0]  # placeholder, will be remapped

    # Step 3: quantize using median cut (use int 0 to avoid enum hang)
    pil_in = Image.fromarray(rgb_for_quant)
    pil_quant = pil_in.quantize(colors=n_colors, method=0)  # 0 = MEDIANCUT
    quant_palette = pil_quant.getpalette()
    quant_indices = np.array(pil_quant)

    # Step 4: build new palette [transparent, *colors] - take n_colors from quantized
    new_palette = [(0, 0, 0)]  # index 0 = transparent
    for i in range(n_colors):
        r = quant_palette[i*3]
        g = quant_palette[i*3 + 1]
        b = quant_palette[i*3 + 2]
        new_palette.append((r, g, b))

    # Step 5: shift indices by +1 (so transparent is 0)
    new_indices = quant_indices + 1
    new_indices[transparent_mask] = 0

    # Step 6: build P mode image
    out = Image.fromarray(new_indices.astype(np.uint8), mode="P")
    flat_pal = sum(new_palette, ())
    flat_pal = flat_pal + (0, 0, 0) * (256 - len(new_palette))
    out.putpalette(flat_pal)
    return out


def process_row(path, name, target=64):
    print(f"\n=== {name} ({os.path.basename(path)}) ===")
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    w, h = im.size

    label_end = find_label_end(arr)
    frame_cols = find_frames(arr, label_end=label_end)
    print(f"  Label ends at {label_end}, image {w}x{h}, {len(frame_cols)} frames: {frame_cols}")

    # Make bg transparent (bg is dark blue ~ (12, 16, 28))
    rgb = arr[:, :, :3].astype(np.int32)
    bg_dist = ((rgb - np.array([12, 16, 28])) ** 2).sum(axis=2)
    is_bg = bg_dist < 1500
    alpha = arr[:, :, 3].copy() if arr.shape[2] == 4 else np.full((h, w), 255, dtype=np.uint8)
    alpha[is_bg] = 0
    out_rgba = np.dstack([rgb.astype(np.uint8), alpha])
    im_rgba = Image.fromarray(out_rgba, mode="RGBA")

    frames = []
    for i, (xs, xe) in enumerate(frame_cols):
        crop = im_rgba.crop((xs, 0, xe, h))
        bbox = crop_to_bbox(crop)
        if bbox is None:
            print(f"    Frame {i}: empty, skip")
            continue
        frames.append(bbox)

    if not frames:
        return None

    # Pad to square, resize
    padded = [pad_to_square(f, target) for f in frames]

    # Quantize each frame to 4-bit
    quantized = [quantize_to_4bit(f.convert("RGBA"), n_colors=15) for f in padded]

    # Build strip
    strip = Image.new("P", (target * len(quantized), target), 0)
    for i, f in enumerate(quantized):
        strip.paste(f, (i * target, 0))

    # Make sure all frames use same palette
    final_palette = quantized[0].getpalette()[:768]
    strip.putpalette(final_palette + [0] * (768 - len(final_palette)))

    out_path = os.path.join(OUT_DIR, f"agumon_{name}.bmp")
    strip.save(out_path)
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
    print(f"Target: {target}x{target}, 4-bit")
    results = []
    for fname, name in rows:
        path = os.path.join(ATLAS_DIR, fname)
        if not os.path.exists(path):
            continue
        r = process_row(path, name, target)
        if r:
            results.append(r)
    print(f"\n=== Generated {len(results)} strips ===")
    for r in results:
        size_kb = os.path.getsize(r) / 1024
        print(f"  {os.path.basename(r)} ({size_kb:.1f}KB)")
