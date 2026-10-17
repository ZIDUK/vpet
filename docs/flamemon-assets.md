# Flamemon Animation Assets

Source: eight user-supplied PNG sheets received on 2026-10-16. Each sheet
contains 25 cells in a 5x5 grid of 256x256 pixels. Originals are retained
without image modification under `assets/digimon/digimon1/champion/idle/`.
The received cast and punch files match the existing canonical sources.

| Received filename | Canonical source | Runtime use |
| --- | --- | --- |
| `flamemon-cast-v1.png` | `flamemon_cast.png` | Technique casting |
| `flamemon-punch-v1.png` | `flamemon_punch.png` | Punch and attacker-hit fallback |
| `flamemon-block-v1.png` | `flamemon_block.png` | Guard and Defense training |
| `flamemon-hurt-v1.png` | `flamemon_hurt.png` | Receiving damage |
| `flamemon-hit_react-v1.png` | `flamemon_hit_react.png` | Packaged alternative receiving-damage reaction; not automatically selected |
| `flamemon-victory.png` | `flamemon_happy.png` | Victory |
| `flamemon-sad.png` | `flamemon_sad.png` | Defeat |
| `flamemon-dodge.png` | `flamemon_dodge.png` | Available for Dodge motion; does not introduce evasion into combat |

`scripts/build.py` generates 15-frame transparent indexed atlases for each
action, retaining transitions while reducing repeated holds. Per-sheet
viewports include all occupied source pixels in the selected frames.
`scripts/build_tdisplay.py` packages the same atlases into LittleFS VPA assets.
Arena retains its existing 100 ms animation interval and 1200 ms impact window.
No damage, element, reward, persistence, or evolution rules change.

The simulator and firmware use Flamemon's own guard, hurt, happy, and sad
assets. The user approved `punch` as the official attacker `hit` animation
on 2026-10-16; no separate attacker sheet is required for Flamemon.
`hit_react` depicts the recipient of a blow and must not be mislabeled as
the attacker. See `docs/dragfiremon-assets.md` for the subsequent Dragfiremon import.

Generated visual checks are in `out/flamemon-import/animations.png` and
`out/flamemon-import/results-es-en.png`. Hardware flashing and physical
verification are not part of this asset import.

## Validation (2026-10-16)

- All eight canonical PNGs match the received originals byte-for-byte.
- `make build` regenerates Pico and T-Display atlases and packages 39
  animations / 182 total native assets (8,168,104 bytes).
- Full pytest: 1073 passed, 7338 warnings, 367.57 seconds. Warnings include
  existing Pillow deprecations and palette-transparency warnings.
- Native Training selection test confirms Flamemon Defense requests
  `/training/flamemon_block.vpa`, not the former casting fallback.
- T-Display firmware and LittleFS image compile successfully. Firmware uses
  50,188 bytes static RAM and 1,006,753 bytes flash.
- Reviewed animation contact sheet and victory/defeat captures in ES/EN.
  No deployment or physical-board behavior is claimed.
