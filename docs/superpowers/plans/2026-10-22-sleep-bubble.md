# Fixed Sleep Bubble Implementation Plan

**Goal:** Show a fixed Zzz bubble on Home while sleeping, as approved by the user.

**Architecture:** Extend the existing generated 32x28 mood assets with right/left
tails but identical, readable Zzz glyphs. Draw the sleep indicator after Home's
lights-off dimming. Domain rules, persistence, combat pacing and Status stay intact.

## Constraints

- Hide outside Home, after waking, and for Egg, dead, paused or away pets.
- Keep existing awake bubbles unchanged; do not add captions, counters or bars.
- Preserve the light-off appearance of the world and pet and the navigation row.
- Generate graphics through the existing Pillow/BMP/VPA pipeline.
- The user explicitly approved this revision's deployment without repeating the
  pending physical four-page Status validation. Preserve NVS before flashing.

## Tasks

- [x] Add failing asset and actual-renderer tests: fixed, bright, edge-safe,
  unmirrored, no saved-state mutation, hidden after waking and in invalid contexts.
- [x] Generate `asleep.bmp` and `asleep_left.bmp` in `scripts/mood_assets.py`.
- [x] Update Home-only composition in `Renderer.cpp` and `sim_renderer.py`.
- [x] Run focused/full Python tests, native tests and a fresh T-Display build.
- [x] Inspect an actual C++ pixel preview and generated icon at display scale.
- [x] Back up critical flash, upload app/FS, verify both digests and unchanged
  critical bytes, reset to normal boot, inspect bounded runtime telemetry.
- [ ] Commit and push the verified source changes; keep board visual acceptance
  and the four-page Status acceptance explicitly pending until user confirmation.

## Verification

Red: two asset tests fail because only 13 icons exist; actual C++ renderer
asserts no asleep icon was opened. Green: full Python suite 1596 passed in
233.51 s, existing warnings retained; native 185 passed. ESP32 app 1015685
bytes, static RAM 56116 bytes; 227 assets/10891653 payload bytes. Full
LittleFS build succeeded. Previous 13 generated mood BMP files are byte
identical to HEAD. Text sizing requires Pillow >=10.1; dependency floor
updated to match the existing installed API.

Preview from actual Renderer.cpp: `out/sleep-bubble/home.png` and enlarged
`home-large.png`; icon orientations in `icons-large.png`. Tests cover all
four live species in sleep rendering, three Home positions, ES/EN, unchanged
saved routine, brightness after lights-off, no accumulated dimming, waking
and suppression during invalid states/actions/panels. This does not prove
a full night or physical display acceptance.

## Board Delivery

Explicit user authorization covers only this Zzz revision and waives the
previous physical Status gate without declaring it accepted. MAC
08:f9:e0:d0:07:88, 16 MB. Application at 0x10000 and FS at 0x410000, no
NVS/partition write. New critical backup:
`out/board-backups/20261022-sleep-zzz-final/08f9e0d00788-20261022-204843-critical.bin`.
Post-flash 24576-byte read is identical to that backup, SHA-256
`695011133bba21d31b869b2cc8b99ca3692087a9771cdfa2509a094e0b0949b4`.

Independent verify_flash digests matched:
- App `cf70ac4f4d47eb64a0ddb513a00399e55d75fff49c6c9ca4d93ecb3093b96dc2`.
- FS `8b636fa38e2f3aaf061580b95b8fe527dd18fc70faa574da0a634ea0905dd459`.

Normal boot VPET_READY, manifest 1; real FS used 11792384/12451840,
659456 bytes free after filesystem overhead. Logical asset/manifest budget
10949817/12451840 is a different measure. Four runtime samples in 45.123 s:
free heap 66128 stable, minimum watermark 60980, no fatal/restart and zero
button events. Max loop 584084 us includes startup; no FPS claim. Evidence
under `out/sleep-bubble/` (deployment.json, upload/verify logs, boot log,
runtime JSON). Visual Zzz acceptance, a full night and Status remain open.
