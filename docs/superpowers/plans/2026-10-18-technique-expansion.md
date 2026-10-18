# Evolution Technique Expansion

Approved scope: Firemon equips 2, Flamemon 3, Dragfiremon 4; expand the
catalogue in the simulator and T-Display, deploy, commit and push.

## Contract

Existing IDs 0 punch, 1 flame, 2 guard and their rules remain unchanged.
Append 3 flare (RAFAGA / FLARE, fire, power 30, 12 MP, range 2,
cooldown 1, Champion+, training >= 4) and 4 inferno (INFERNO, fire,
power 38, 18 MP, range 2, cooldown 2, Ultimate, training >= 6).
Training is the existing lifetime technique lesson counter. Night continues
to teach/master Flame only. Evolution preserves learned/equipped techniques;
additional slots stay empty. Equipment remains manual. No new conditions,
species, signature category, Digimon World names or evolution thresholds.

## Tasks

- [x] Add failing tests for 2/3/4 capacity, stage gates, manual equipment,
  legacy saves, MP/cooldown/element rules and Python/C++ parity.
- [x] Extend portable catalogues/progress/battle/session rules; retain the
  old numeric IDs and NVS schema 3. Append mastery keys and snapshot version
  3 with readers for versions 1/2; preserve legacy item transaction recovery.
- [x] Adapt both technique screens and Arena selectors for four equipped
  attacks without overlap in 240x135 ES/EN; generate distinct pixel icons.
- [x] Verify old/new save recovery, power cuts, rollback, screenshots,
  native/Python suites, make sim, firmware and filesystem budgets.
- [x] Back up connected board, deploy current firmware and assets, verify
  digests/boot. Record physical acceptance separately from USB checks.
- [x] Update official docs and roadmap; review accumulated changes, exclude
  local saves/backups/logs/secrets, commit and push.

## Validation Evidence

2026-10-18: 1132 Python tests passed (6708 existing Pillow/pytest warnings),
175 native tests passed. The user-level controller test learns and manually
equips four, reloads saved JSON and reaches every Arena command/retreat with
NEXT/ACTION. The 48 new complete cross-language battle traces cover fire,
plant, water, MP, cooldowns, all personalities and the new techniques.

The production C++ TrainingUi raster matches the simulator exactly in ES/EN,
including all five techniques, six navigation entries and 2/3/4 equipment.
Real Panels/AssetStore tests exercise all Arena selectors for new attacks,
cached/uncached images and translated names. TFT font raster in Arena is
still outside that host adapter's scope; physical acceptance is separate.

Native Battle remains below 256 bytes using bounded byte mastery/cooldown/use
arrays. T-Display build: RAM 56044/327680; flash 1009965/4194304. Make Sim
passed headless for 90 frames. Assets: 204 files, 10497880 raw bytes (562
additional bytes for the two icons). Preflight filesystem payload including
manifest: 10549894/12451840. Preview: `scripts/preview_techniques.py` produces
ES/EN review sheets in `out/technique-review/`, not photographs of hardware.

Fresh critical-state backup (24576 bytes, SHA-256 checked):
`out/board-backups/20261018-technique-expansion/08f9e0d00788-20261018-151619-critical.bin`.

## USB Delivery

Firmware and complete LittleFS uploaded on 2026-10-18 without erasing NVS.
Deploy OK: heap_free=66640, heap_min=66564, fs=11309056/12451840, manifest=1.
Independent esptool verify_flash reports digest matched at 0x10000 and
0x410000. Firmware SHA-256:
`aa2d6df392e637ee507e2d8102604651df420c7900a44e54d73d0bd4a5955754`.
LittleFS SHA-256:
`7d02ecf8e91199ed1606fd58985c9b7a8aeec662a94d58bd39531b54459ac858`.
The two icons each occupy 281 raw bytes; LittleFS block overhead makes actual
used space 16384 bytes larger than the previous image.

Logs and complete test outputs: `out/technique-board-deploy/` (local only).
An 18-second boot observation completed with TECHNIQUE_EXPANSION_BOARD_OK,
VPET_READY and BLE ADVERTISING; no fatal, panic, brownout or abort occurred.
The optional missing swapTx key still logs NOT_FOUND without blocking boot.
Physical acceptance of the new equipment/attacks is still pending; simulator
screenshots, byte digests and boot telemetry do not certify the physical UI.
