# Dragfiremon Animation Assets

Four user-supplied PNG sheets received on 2026-10-16, retained byte-for-byte
under `assets/digimon/digimon1/ultimate/idle/`. Each source has 25 cells in a
5x5 grid of 256x256 pixels.

| Received filename | Canonical source | Runtime use |
| --- | --- | --- |
| `dragfiremon-victory.png` | `dragfiremon_happy.png` | Victory |
| `dragfiremon-sad.png` | `dragfiremon_sad.png` | Defeat |
| `dragfiremon-hurt-v1.png` | `dragfiremon_hurt.png` | Receiving damage |
| `dragfiremon-block-v1.png` | `dragfiremon_block.png` | Guard and Defense training |

The existing build pipeline generates 15-frame transparent indexed atlases
and native LittleFS VPA files. Viewports include occupied source pixels,
including wings and feet, in every selected frame. Arena keeps its existing
100 ms frame interval and 1200 ms impact window. Training keeps its existing
animation timing. No domain rules, persisted enums, or NVS schema change.

Home, Training, and Arena use the dedicated available animations in both
simulator and firmware. A connected attacker hit still uses `punch`; a
dedicated `hit` sheet has not been supplied. No dedicated `dodge` is available
and this import does not introduce evasion into combat.

Flamemon's use of `punch` for `hit` is separately approved by the user and
is not an outstanding asset requirement. The initial import was validated
without flashing; the subsequent authorized USB deployment is recorded below.

## Validation (2026-10-16)

- All four canonical PNGs match the supplied originals byte-for-byte.
- `make build` regenerates both simulator profiles and packages 43 animations,
  186 total native assets, and 8,635,006 bytes of asset data.
- Full pytest: 1077 passed, 7738 warnings, 255.48 seconds. Warnings include
  Pillow deprecations and palette-transparency notices.
- Crop checks cover all selected source frames of both evolved imports.
- Native Training selection checks include Dragfiremon's dedicated block asset.
- Firmware and LittleFS image compile successfully. Static RAM: 50,188 bytes;
  firmware flash: 1,006,917 bytes.
- Reviewed animation contact sheet and victory/defeat cards in ES/EN at
  `out/dragfiremon-import/animations.png` and `results-es-en.png`.
  Animated preview: `out/dragfiremon-import/animations.gif`.
- This initial validation did not deploy hardware. Physical visual acceptance
  remains separate from the subsequent USB verification.

## USB Deployment (2026-10-16)

User-authorized deployment to the connected 16 MB ESP32 T-Display completed
with both Flamemon and Dragfiremon imports. The existing Status rendering
was retained and the current firmware compiled successfully before upload.
No NVS erase or deliberate pet reset/provisioning was performed.

- Fresh partition/NVS backup is retained locally under
  `out/board-backups/20261016-animation-assets/`, with its SHA-256 sidecar.
- Firmware verified against flash at `0x10000`: 1,013,488 bytes, digest matched.
- LittleFS verified at `0x410000`: 12,451,840 bytes, digest matched.
- Ready telemetry: heap free 72,504; minimum 72,436; filesystem
  9,404,416 / 12,451,840 bytes; asset manifest version 1.
- Final reset booted normally and emitted `VPET_READY` followed by the
  verification marker `ANIMATION_ASSETS_BOOT_OK`.
- Local evidence: `out/animation-board-deploy/vpet-animation-deploy.log`,
  `vpet-animation-verify.log`, and `vpet-animation-boot.log`.
- Visual acceptance of the new animations on the physical display still
  requires user observation; serial/digest checks do not certify appearance.
