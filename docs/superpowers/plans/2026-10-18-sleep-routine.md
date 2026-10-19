# Night, Tired Sprites and Learned Sleep Routine

Approved by the user on 2026-10-18, including separate dawn/wake and the
supplied tired sheets for Sparkmon, Firemon, Flamemon and Dragfiremon.
Execute inline with test-driven-development and verification-before-completion.

## Contract

- Environment night is local civil time [18:00,06:00); sleeping never forces
  night scenery during daylight. Use the approved generated night artwork.
- DNA trait 0/1/2 seeds bedtime at 18:30/18:15/18:00 and low-energy tired
  thresholds at 20/25/30. Physical tired clears ten points above threshold;
  bedtime sleepiness cannot be cleared with protein.
- Manual light-off starts sleep. Three consistent night bedtimes within 30
  minutes establish a target. Move preferred bedtime toward that target by
  at most 15 minutes per night, within 18:00..23:00. Learn at most once per
  civil night; daytime naps, interruptions and one exceptional night do not
  establish a routine. Preserve routine through evolution; reset on new life.
- Night sleep wakes after both the next 06:00 and eight hours of on-device
  sleep have elapsed. Thus 18:00->06:00 and 23:00->07:00. Day naps last 30
  minutes. Dawn only changes scenery. No offline sleep progress is inferred.
- Sleep recovers one energy per five on-device minutes; no instant energy
  or repeated button reward. Care metabolism pauses while sleeping, but age
  and injury time continue. Full-night completion grants the existing rest
  HP/DP/EV bonus at most once per civil night. Interrupted sleep grants none.
- Sleepiness is a soft cue, not a care mistake. Legacy APIs retain their
  behavior for Pico/old tests; active T-Display flow uses the new routine.
  No new automatic lights penalties; do not auto-start sleep or interrupt
  battle/training/exploration. Bad/untrusted calendar disables habit learning
  and calendar cues, not manual rest or monotonic recovery.
- Save sleeping/session duration, energy checkpoint, habits and reward night
  together in JSON and NVS full snapshots. Keep schema 3/numeric enums;
  additive sleepState v1 plus snapshot v4 reading v1/v2/v3/v4. Reboot restores
  sleeping without adding elapsed powered-off time or counting new lessons.

## Work

- [x] Add failing portable tests: exact time boundaries, DNA thresholds,
  three-night learning, exceptions, sleep timing, no duplicate rewards,
  JSON/byte round-trip and legacy/malformed/power-cut recovery.
- [x] Implement matching core routines and integrate active controllers with
  full-snapshot persistence, trusted civil time and no combat interruption.
- [x] Import originals without painting/re-generating supplied artwork;
  build 25-cell tired atlases with fixed viewport/baseline for all four.
  Wire tired idle animation without reducing Training/Arena performance.
- [x] Package approved night art explicitly, not via alphabetical source
  selection. Keep static backgrounds cached until hour/light state changes.
- [x] Run Python/native suites, real render/cross-language cases, Make Sim,
  firmware build and flash/filesystem budget checks. Inspect ES/EN previews.
- [x] Update architecture, roadmap and current status with actual results;
  distinguish implementation/build from physical board acceptance.

## Validation

Full suite: 1237 Python tests passed; native PlatformIO: 180 passed.
Final focused run: 111 passed, including real Renderer.cpp/AssetStore.cpp
pixels, 36 five-night Python/C++ traces, actual App sleep/wake/reboot, legacy
v1/v2/v3 recovery and atomic reward completion at every simulated write cut.
The 49 renderer cases cover four species, 25-frame tired cadence, day/night,
sleeping at dawn, exact RGB565 pixels/feet and static-background cache.
Host proofs are not photographs or physical animation/FPS acceptance.

Both T-Display and preserved Pico artifacts regenerated from source. Direct
headless simulator smoke ran 90 frames successfully. The Pico rebuild also
refreshes generated copies of previously delivered source contracts; no
manual edits were made to generated files. No Pico deployment is implied.

Approved originals copied intact from Downloads. Night artwork SHA-256:
`9206d647066bc506ef94ee31a9a97f4cdd81bb31e5fc1bd1ca030ab28dd83ea8`.
Review contact sheet: `out/night-sleep-preview.png`, generated with the real
firmware renderer on the host via `scripts/preview_sleep.py --renderer ...`.

The untrimmed new bundle is 11274688 bytes. Its tired indexed, already
quantized pixel data is cropped symmetrically at the sides and above, with
bottom-center anchoring in an 88px logical box. No scale, pixel, palette or
frame timing changes. Saves 210400 bytes; no new runtime framebuffer/cache.
208 packaged assets total 11064288 raw bytes. Preflight including manifest:
11117792/12451840 (10.71% free). RAM static 56100/327680; firmware linked
1014049/4194304 bytes. T-Display compile and preflight USB passed on board
08f9e0d00788, ESP32-D0WDQ6-V3, 16MB, /dev/cu.usbserial-57040013171.

## USB Delivery

Firmware and full LittleFS uploaded successfully on 2026-10-18; NVS was not
erased. Deploy OK: heap_free=66592, heap_min=66516,
fs=11890688/12451840, manifest=1. Independent esptool verify_flash reports
digest matched at both 0x10000 and 0x410000. SHA-256:

- Firmware: `902dbfa77748f84abab8b54c629d5e09fff4cd87c2aa3c8cf30e89f689ec1519`.
- LittleFS: `3c0b62c8b55a80ccb23e2e53eee10740b90f0785e3ca746e9cc64b0aa1864906`.

An additional normal reset was observed for 18s: VPET_READY,
heap_free=66596/heap_min=66528, BLE ADVERTISING then PAIRED/CONNECTED,
no Guru Meditation/Backtrace/Brownout/Stack-canary fatal. An 8s passive Mac
advertisement scan returned no match while the device was connected; this
does not establish discovery from a phone or a disconnect/reconnect cycle.
The missing sleepState key on the first legacy load correctly defaults to
a new routine, not a storage recovery failure. No sleep/progress was forced.

Fresh critical-state backup retained at:
`out/board-backups/20261018-sleep-routine/08f9e0d00788-20261018-212158-critical.bin`.
SHA-256: `c59868e3639682bf3cdf657edc01ed8572f3e9b56b1f1b10cb6c25d23ad78862`.
Partida/NVS is preserved. Photos and a real overnight session remain open.
Set Options Date/Time if the unbacked clock was lost on reset. USB verification
does not close visual acceptance, real-time overnight behavior or sustained BLE.
