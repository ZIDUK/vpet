# Sprites — Digital Monster vPet

This directory contains sprite strips extracted from the Digital Monster
reference mockup. The reference image is 1536×1024 with a 32×32 tile size.

## Structure

```
sprites/
├── egg/           # Digi-Egg stage (4 evolution stages left → right)
├── agumon/        # Rookie stage
├── greymon/       # Champion stage
└── metalgreymon/  # Ultimate stage
```

Each stage folder contains:

- `00_*_full_column.png` — full vertical column from the reference (all
  rows for that character, includes labels).
- `strip01_row17.png` … `strip06_row31.png` — **6 candidate animation
  strips** per stage (256×32 px, 8 frames each).

## How the strips were picked

The reference image has the evolution line in the bottom half (rows 17-31
of the 32-row grid). Each character stage occupies 8 columns in that
region. The strips here are the 6 rows with the highest pixel density
(bright pixel count) in that region — a rough proxy for "most likely to
be a real sprite, not a label".

Rows used: **17, 21, 24, 26, 29, 31** (32-pixel tile rows).

## Caveat — strip labels are NOT yet known

The reference image has TEXT labels for each row (IDLE, WALK, ATTACK,
OTHER, EVOLVE-TO), but my extraction script picked rows by pixel
density, not by label position. So the strips are in roughly the
right area but the **action for each strip is not guaranteed**.

To use them, you need to:
1. Open each `strip0X_rowYY.png` and visually identify what action
   it shows (idle breathing, walk cycle, attack pose, hurt, digivolve
   glow, etc).
2. Rename the files to meaningful names like:
   - `idle.png` for the breathing pose
   - `walk.png` for the walking cycle
   - `attack.png` for the attack pose
   - `hurt.png` for the damage/hit pose
   - `digivolve.png` for the evolution animation
3. Re-run the BMP conversion (8-bit indexed, idx 0 = transparent)
   before deploying to the Pico.

## Conversion to BMP (for Pico)

The current files are PNGs. The Pico expects 8-bit palette BMPs with
index 0 = transparent (matching the existing project format). To
convert, the script `/tmp/extract_animations.py` (used previously)
does this for the Greymon sprites. A similar conversion needs to be
run for these new strips.

## RAM budget (32×32)

- Per frame: 32×32 = 1,024 bytes (1 KB) at 8-bit indexed
- Per action (4-8 frames): 4-8 KB
- All 4 stages × 6 actions × 6 KB avg ≈ 144 KB
- **Tight for the 150 KB Pico W free RAM** — would need lazy-loading
  or to pick only 2-3 key actions per stage
