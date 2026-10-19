# Rest Simplification and Board Validation Plan

**Goal:** Deliver the approved light-only Rest menu and move Cold to Options
as Pause Pet, preserving the current pet, reserve and existing numeric IDs.

**Architecture:** Rest has two actions. Options appends pause ID 9 while Back
keeps ID 8; a small visual-order mapping puts Back last without migrations.
Both T-Display renderers/controllers share the same order. No new NVS keys.

**Tech Stack:** Python/Pillow/pytest, portable C++/Unity, ESP32/TFT/LittleFS.

## Approved contract

- Rest: LIGHTS OFF / APAGAR LUZ, or LIGHTS ON / ENCENDER LUZ when sleeping,
  plus BACK / VOLVER. No Cold, Backup or swap/park action in Rest.
- Pause Pet / Pausar crianza moves to Options with current on/off state.
  Turning pause on/off is saved, rollback on rejected writes; no deletion
  of vpet_bak or schema changes. Back is still semantic option 8.
- Pausing stops sleep progress as well as care/age/injuries/evolution,
  freezes Motion timing and preserves a pending Call's remaining grace.
  Python already blocks sleep recovery in cold mode; fix C++ parity.
- Simulator Rest gets the same two-step menu, not immediate sleep on entry.
- Validation distinguishes host tests, USB identity/digests/boot, passive
  serial observation, and user-operated physical acceptance. Never inject
  needs, evolve, advance clock or reset the live pet without permission.
- A real night needs actual powered time; hardware readback alone cannot
  confirm on-screen icons, FPS, button response or reward uniqueness.

## Tasks

- [x] Red tests: two Rest actions, ordered Options including pause, durable
  pause toggle/failed-save rollback, real App paused sleep/Call grace.
- [x] Implement core order map, Navigation/App, simulator options/Rest,
  renderer copy and current-state redraw. Preserve old option values.
- [x] Real Panels harness checks ES/EN Rest labels, no Cold/Backup, pause
  state and Back last. Update navigation/UI expectations, not geometry.
- [x] Full pytest, native tests, both generated artifacts, simulator smoke,
  ESP32 build and preview inspection. No changes to Status geometry/assets.
- [x] Fresh board backup; flash current firmware, verify firmware and
  installed unchanged LittleFS before deciding whether FS reload is needed.
  Record startup, bounded serial session and remaining physical cases.
- [x] Update roadmap/evidence and prepare scoped commit; no saves/backups/logs.

Publication to origin/master is verified in the final delivery report,
after push succeeds; this plan does not pre-claim that network operation.

## Checkpoint

Approved by the user: light-only Rest, remove reserve action from that menu,
move Cold to Options as Pause Pet, preserve existing data. Active safeguards:
no WiFi, no persistent enum/schema migrations, no hand edits to generated
assets, no live-pet injection, never delete board backups. Build/native/
full pytest/USB and physical acceptance are distinct evidence levels.

Red captured in `/tmp/vpet-rest-red.log`: missing pause option, unsaved pause
state, C++ advancing frozen sleep. Observer parser also failed before its
module existed. First focused App/controller run: 45 passed; expanded menu/
UI run: 131 passed. Full suite and device evidence recorded below when done.

Full suite: 1312 passed, 8931 warnings, 194.99s. Native: 183 passed.
Two obsolete expectations were adapted: Rest no longer swaps pets, and
its Back label is now rest-specific. Legacy reserve restoration is still
tested directly through SettingsStore then App startup/clock protection.
No failure-path or duplicate-reward checks were removed.

Both generated artifacts, 90-frame headless Make Sim and ESP32 build
succeeded. Static RAM 56108/327680 (+8 bytes for runtime counters), linked
app 1014141/4194304. Assets still 219 files/11075765 payload bytes;
with manifest 11131600/12451840. Existing sprites/Status geometry unchanged.
Reviewed `out/rest-preview/overview.png`, ES/EN, awake/asleep and pause
on/off. The TFT host adapter checks labels/pixels but does not rasterize
the board's actual fonts; physical acceptance is still separate.

Added read-only runtime telemetry and serial observer to support the physical
matrix. This does not provide remote actions or a hardware screenshot.

## Lights-off follow-up

The user physically accepted the Rest/Options commands, then reported that
the pet slept against a bright background. Calendar-only scene selection
did not express the light action. Keep day/night independent and dim Home
world pixels to one quarter of each RGB565 channel while asleep; leave the
top navigation and panels readable. No new assets, framebuffer or NVS keys.
Native sprite read/write APIs preserve TFT byte order. Each frame starts
from the undimmed scene cache, so darkness cannot accumulate and waking
restores brightness. Original sleep cadence/anchors are unchanged.

RED: the real Renderer harness failed at daytime sleep before the fix.
Focused run after the fix: 107 passed, including all four species, day/night,
feet/colors, unchanged header, wake restoration and cache reuse. Simulator
checks also preserve dawn without waking and keep panels undimmed.
Inspected `out/rest-preview/lighting.png` with day/night and light on/off.

Final host run: 1324 passed, 8931 existing warnings, 201.82s; native 183
passed. 90-frame headless simulator and ESP32 build passed. Static RAM
56108/327680, linked app 1014233/4194304. No asset changes for this follow-up.

Delivered 2026-10-19 to ESP32 08f9e0d00788, 16MB, USB serial
57040013171. A new verified critical-state backup is retained locally at
`out/board-backups/20261019-rest-darkness/08f9e0d00788-20261019-064324-critical.bin`:
SHA256 `2eb892e3bf1693c5999ad7f06126d80659a5027257827835ca35de823e5d9284`.
Firmware-only upload passed; independent esptool verify matched application
at 0x10000 and preserved LittleFS at 0x410000. SHA256 of installed artifacts:

- Firmware: `820baa24f076098a21260c8f4053e955be14356888fe38405ee5465d2b080bb0`
- LittleFS: `832f23c28450cf83f417761ac1966a2da190813458caa77841dc928aa1552c4c`

Normal startup: VPET_READY, manifest 1, free heap 66128/minimum 66108;
FS 11943936/12451840, BLE PAIRED/CONNECTED. Local upload, independent
verify and startup logs are under `out/rest-board-deploy/darkness-*`;
not included in Git. The user subsequently confirmed that lights off darkens
and lights on restores brightness; darkness is now visually accepted.
The 90s normal boot observation ended successfully: eight runtime samples,
free heap 66128 throughout, watermark 60988, BLE connected, zero input
events, no fatal or uptime regression. First interval max was 933565us;
later interval maxima 94..96ms. No active-menu/FPS claim from this idle run.

Pre-follow-up USB observation: 300.024s, 29 samples, 7 input events, BLE
connected; free heap 66060..66132, minimum watermark 43876 bytes. No fatal
or uptime regression between runtime samples. Maximum loop 927148us,
including a separate 800189us peak with input events; after 60s, interval
maxima were about 78..80ms. Not an FPS or leak/reconnect certification.

## Physical matrix

| Case | Required physical action/evidence | Acceptance |
| --- | --- | --- |
| Food bubble | Food need, feed, photo/video before/after | Pending user operation |
| Rest bubble | Fatigue, lights off, wake/recovery, before/after | Pending user operation |
| Injury bubble | Existing injury, medicine, before/after | Do not injure the live pet artificially |
| Night | Trusted date/time, learned bedtime, 8h+ powered sleep, checkpoints/restart | Needs real overnight observation |
| Skills / evolution | Learn/equip 3/4, Arena use and qualifying results | Use earned progress or approved separate test pet |
| Exploration / bag | Trips, receipt, consume, restart, compare stock/rewards | Pending user operation; no forced clock change |
| Stability / BLE | Active Training/Arena, memory sampling, connect/disconnect/reconnect | Serial alone cannot prove screen fluency |
