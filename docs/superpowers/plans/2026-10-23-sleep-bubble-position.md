# Sleep Bubble Position Correction

## Approved Direction

User confirms Zzz appears on hardware but wants it directly above the pet,
not detached toward the top of Home. Change only its position; retain
the approved fixed glyph, darkness, actions, persistence and Status.

## Implementation

- [x] Pin horizontal center of the 32px bubble to the 88px pet, both facing
  directions and at x=0/76/152, in actual C++ and simulator tests.
- [x] Anchor vertically to the sprite's first visible row minus 30px,
  clamped below navigation. Transparent space above a lying pet must not
  separate it from its bubble.
- [x] Extend AssetStore::drawFrame with optional visibleTop output. Capture
  it from existing visible runs, including the icon cache; no extra I/O
  or allocation. Existing callers remain compatible.
- [x] Match that bound using the simulator's existing transparency mask.
- [x] Inspect C++ pixels for four species standing/lying, unchanged tired
  bubbles, darkness and wake behavior; run focused/native tests and build.
- [x] Finish full Python suite and record results: 1602 passed in 234.27 s;
  existing warnings retained. Generated consumable catalog check passed.
- [x] Obtain revision-specific Status waiver before firmware-only load.
- [x] Back up current NVS/table, load only app, independently verify digest
  and unchanged critical bytes, confirm normal boot and bounded liveness.
- [ ] Obtain physical acceptance of corrected position; Status stays open.

## Evidence

Focused suite: 213 passed, including cached/cold opaque-row reporting and
missing-asset sentinel. Native: 185 passed. Firmware built: 1015849 app
bytes, static RAM 56116 unchanged. Images:
`out/sleep-bubble-position/home-lying.png`, `sleep-gallery.png`.
Initial regression failed against the prior lateral anchor. No asset or
domain file changes; no new persistent values.

## Deployment Boundary

Original Zzz revision 7815af9 was loaded and accepted only as present.
User explicitly authorized this position correction as firmware-only,
preserving the game and without repeating the pending four-page Status
validation. Fresh build from ece6506 loaded at 0x10000 only; no FS,
partition-table or NVS write. Physical placement and Status acceptance
remain pending; do not infer them from host pixels or serial telemetry.

## Board Delivery Evidence

MAC 08:f9:e0:d0:07:88, 16 MB. Independent verify_flash matched both the
new application and unchanged LittleFS image:
- App SHA-256 `bf4291a0d91dfcb6f8e3a2ffd59e787c3b86545802137222d5576cbb40ce69d8`.
- Existing FS SHA-256 `8b636fa38e2f3aaf061580b95b8fe527dd18fc70faa574da0a634ea0905dd459`.

Fresh critical backup:
`out/board-backups/20261023-zzz-position/1792762284348377000/08f9e0d00788-20261023-083124-critical.bin`.
Post-flash table/NVS read is byte-identical (24576 bytes), SHA-256
`1eacf2312d618bb69f24ad3a0a1d1c3e19ba50c4fd201c4eee608dbd563ff287`.

Normal boot: VPET_READY, manifest 1, FS 11792384/12451840. Four runtime
samples over 45.182 s: free heap 66144 stable, minimum watermark 60952,
no fatal/restart, zero button events. Max loop includes startup, not FPS.
Evidence: `out/sleep-bubble-position/deployment.json`, upload/verify logs,
board boot log, runtime JSON and critical post-read. No backup/log/game
data is committed. User visual confirmation of corrected position requested.
