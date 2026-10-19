# Mood Bubbles Implementation Plan

**Goal:** Replace the Home corner cue with a pet-anchored needs bubble and
show a mood face inside the existing Status mood-icon slot. User approved
the proposal and explicitly requested flash, commit and push.

**Architecture:** Read-only portable classifiers in Python/C++; precompose
small indexed bitmap assets during the existing build. Renderer overlays
one 32x28 bubble after the pet; Status uses one 20px source face scaled into
its existing 16px slot. No additional framebuffer, saves, enums on disk,
care penalties, environment preferences, sickness or lifespan rules.

**Tech Stack:** Python/Pillow/pytest; portable C++/Unity; TFT_eSPI/LittleFS.

## Contract

- Need priority: injury > hunger <=20 (or Hunger call) > tired/energy <=20
  (or Strength/Lights call) > low mood. Only Home idle/walk shows bubbles;
  hide during egg, death, freeze, away, sleep, actions and panels.
- Face: injured=sad; mood <20=angry; mood <50 with food/rest need=angry;
  otherwise mood <50=sad, 50..74=neutral, >=75=happy.
- Anger mark is limited to food/rest needs with mood <50. Hunger alone
  does not mean anger. Low mood alone gets a sad/angry face bubble.
- Existing menu Call highlight/blink and underlying care timers remain;
  remove the lower-right corner icon on T-Display Home only. New soft
  hunger/mood cues do not start Calls or alter their grace periods.
- Bubble origin follows head/facing, flips near edges, clamps below the
  24px menu, never changes pet scale or animation. Resolve need => remove
  or show the next current need immediately, no dismissal state.
- Source: approved hungry/angry concept plus a transparent generated
  3x2 atlas (happy/neutral/sad; angry/empty bubble/anger glyph). Preserve
  originals. Extract/threshold/resize/quantize only in the asset pipeline.
- Four Status page geometries, text, bars and values stay unchanged.

## Tasks

- [x] TDD domain: exact mood/hunger boundaries, independent anger, priority,
  suppression, read-only JSON and exhaustive bubble-position bounds.
  `tests/test_mood_cues.py` -> `src/core/cues.py` and portable `UiCue.h`.
  Compare the same numeric vectors with a compiled C++ harness.
- [x] Package sources through `scripts/mood_assets.py`, `scripts/build.py`
  and `scripts/build_tdisplay.py`. Produce seven 32x28 bubbles and four
  20x20 faces; test alpha, dimensions, palette and deterministic bytes.
- [x] Wire Home overlays and Status faces in real firmware/sim renderers.
  Test production Renderer.cpp/AssetStore.cpp/Status paths at screen edges,
  all species, day/night, ES/EN, suppression and menu/corner invariants.
  Update the prior tired-screen expectations to include its rest bubble.
- [x] Run full pytest, native tests, Make Sim and firmware budgets. Inspect
  previews at 240x135; preserve Training/Arena and current Status layout.
- [x] Back up current NVS, deploy current firmware+LittleFS on the connected
  board, verify both digests and VPET_READY; keep physical acceptance open.
- [x] Update architecture, roadmap and evidence; exclude saves/logs/backups;
  prepare publication to the authorized ZIDUK/vpet master destination.
  The exact publication commit is recorded in Git rather than a self-reference.

## Local evidence

- Red: missing cue module and missing asset builder, captured before
  implementation. The old lower-right badge expectation also failed after
  replacing it; its regression now requires the head bubble and intact Call.
- Domain/asset focused run: 21 passed. Added 34 cue-renderer cases plus
  the existing 49 sleep-image cases, including all four species/day/night.
- Shared classifier/placement vectors: 1,536 Python/C++ combinations.
  Bounds cover each Home x=0..152 and both facing directions.
- Unity: 183/183 passed. New cases cover priority, read-only calls/counters,
  sleep suppression and edge placement.
- Final full Python suite: 1292 passed, 8931 Pillow warnings, 185.97s.
  The adjusted corner test samples outside the centered pet rather than
  mistaking its feet for a bottom status bar. No production fix was needed.
- `make build-tdisplay`, `make build-pico`, 90-frame headless `make sim`
  and ESP32 compilation succeeded. Static RAM 56100/327680 unchanged;
  linked app 1014749/4194304. 219 assets, 11075765 payload bytes;
  including manifest 11131600/12451840 (10.60% raw reserve).
- Source atlas and approved food/anger concept are tracked; 11 runtime
  mood files occupy 11477 bytes. No third framebuffer or new save fields.
- Reviewed Home mood sheet and all four Status pages ES/EN at 240x135.
  Previews in `out/mood-bubbles-preview/` and `out/status-preview/`.
  They are host evidence, not physical screenshots or FPS measurements.
- Flash authorization: explicit user request in this turn, preserving the
  current Status adjustments and the prior user confirmation in this chat.
  No new geometry changes; physical acceptance of the new icons remains open.
- USB preflight recognized the same ESP32-D0WDQ6-V3, 16MB, id
  `08f9e0d00788`, port `/dev/cu.usbserial-57040013171`. Budgets passed.

## Board evidence

New critical-partition backup before writing:
`out/board-backups/20261018-mood-bubbles/08f9e0d00788-20261018-220144-critical.bin`.
SHA256 `8740601b88dcba357f0abbe1b73ed54598adf0326713a0a9372ddde6d3ca1d17`.
Backups, saved pets and raw logs stay local and are excluded from the commit.

Firmware SHA256:
`b82a31962429b340dffa26da00aae647702d8a7486223466e82bc7b55ee56573`.
LittleFS SHA256:
`bafe00a3c06a676d47b21260903712207ff67d85ff50e43181b05851d675b039`.

Deploy completed: heap free 66568/minimum 66492, FS
11943936/12451840, manifest 1. Independent `esptool verify_flash` matched
both digests (firmware 0x10000, LittleFS 0x410000).

Fresh normal reset observed for 18 seconds: `MOOD_BUBBLES_BOARD_BOOT_OK`,
`VPET_READY`, heap free 66572/minimum 66528, same filesystem/manifest,
BLE ADVERTISING -> PAIRED -> CONNECTED. No Guru Meditation, backtrace,
brownout or stack-canary failure. Preferences logs `swapTx NOT_FOUND`:
the existing recovery code reads the absent optional transaction marker
with empty fallback and treats it as no pending swap; no persistence change.

Raw local evidence: `out/mood-bubbles-board-deploy/deploy.log`, `verify.log`
and `boot.log`. The backup SHA256 sidecar also passed `shasum -c`.
No WiFi, forced evolution, artificial needs or saved-pet edits were used.
Physical appearance, button response, sustained BLE and FPS are not proven
by these USB/host checks and remain open for user acceptance.
