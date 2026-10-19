# Angry Sprites Implementation Plan

**Goal:** Complete the previously requested angry presentation with the four
user-supplied 25-frame sheets, using existing mood rules rather than changing care.

**Architecture:** Home-only idle/walk presentation selects angry when the
existing cue face is Angry and the cue is not suppressed. Tired/actions take
priority. Keep numeric states and NVS unchanged; use the existing 90ms/25-frame
presentation pattern and fixed 88px anchor. Pico retains its legacy behavior.

**Tech Stack:** Pillow asset builder, Python simulator, native C++ Renderer,
VPA1/LittleFS, pytest and PlatformIO.

## Constraints

No WiFi, no live-pet mood injection, no Status layout changes, no new motion
enum, no repainted sources or lowered filesystem safety threshold. New assets
require both firmware and FS deployment, a fresh backup, independent digests
and normal boot. USB is not visual acceptance.

## Tasks

- [x] RED: require four angry assets and 51 registered animations; test actual
  Renderer selection/priority, 25-frame colors/feet/cadence and simulator parity.
- [x] Import PNG originals; add fixed viewports to scripts/build.py and runtime
  validation. Regenerate artifacts, never hand-edit generated files.
- [x] Package angry plus existing Home actions (eat/walk/fly/sleep/punch/cast/
  hurt/block/dodge/hit/hit_react) with the existing
  transparent-padding trim. Verify anchored RGB565 pixels against untrimmed
  frames for every frame; leave idle, battle, training and Status assets intact.
- [x] Renderer/simulator select anger from existing cue, preserve bubbles and
  give tired/explicit actions/suppressed states priority. Mood recovery restores idle.
- [x] Full pytest/native, firmware build, previews and isolated simulator smoke;
  confirm the configured asset-byte budget margin remains at least 10 percent.
- [x] Update roadmap/evidence, back up and deploy, verify both digests and boot.
  Prepare scoped changes without saves/backups/logs. Physical acceptance separate.

Publication is verified in the final delivery report after push succeeds.

## Host Evidence

RED: `/tmp/vpet-angry-red.log`, 12 missing angry selections failed, 28 priority
cases already passed. No production change preceded that run. After integration:
163 focused cases passed; full suite 1376 passed, 9307 warnings, 214.29s.
Native 183 passed. T-Display and Pico artifacts regenerated; simulator headless
90 frames and ESP32 build passed. RAM 56108/327680, app 1014393/4194304.

All supplied sources were copied byte-for-byte (`cmp` on all four). SHA256:

- Sparkmon: `d6e0a7c9372a3ef1ecc0aa4aa66cf0096d88d0c5f21bdc825ab52f4e68376eeb`
- Firemon: `5ee2f5bf88f13d4a762109d6c8ea2beddd7febbdf53d4f85fa28c6bc0df4365f`
- Flamemon: `97d78f1ee6ec33ca0570a63f2150338c7cf14b04348fa22ed37dbfbf7c8239a7`
- Dragfiremon: `68434a6269449e643f7424c6edf45be74b117baae37ffde987242696c25a6d5f`

VPA1 unchanged. 51 animation registrations, 223 files, 10786603 payload bytes;
10843912 including manifest, 12.91% budget margin. No safety thresholds lowered.
The first packaging attempt was too close to the 10% preflight limit, so
transparent-padding trimming was extended only to Home actions. Every trimmed
frame is reconstructed and compared byte-for-byte to its untrimmed quantized
version; nothing is sampled away. Idle/results/Training/battle remain untouched.

Real Renderer/AssetStore host harness checks all four species and emotion vs
tired/action/sleep/injury/pause/calm priorities. Frames 0/8/24 compare all world
pixels, feet, palette and bubble against VPA and simulator sources. Other
regressions preserve day/night, light dimming, cache and Status geometry.
Reviewed `out/angry-preview/overview.png`: normal, angry and food-angry across
all four stages. Preview and tests never mutate the live board's happiness.

Independent boundary check against the previously verified, installed LittleFS
image (unpacked to a temporary directory): 191 existing VPA files are byte-for-byte
unchanged. Only 28 Home action VPAs differ; all 507 frames in those assets match
the installed versions exactly after restoring the original anchor/canvas.
This includes alpha and RGB565 palette results, not merely bounding boxes.
Evidence: `out/angry-board-deploy/asset-boundary-check.json` and
`installed-frame-check.log` (local only). Training/battle/UI/background/idle/
result assets are unchanged, aside from the four new angry sheets.

During this delivery the user separately confirmed the previous light fix:
lights off darkens, lights on restores brightness. This closes that visual
acceptance only, not the real-night or pause/resume matrix.

## Board Delivery

ESP32 08f9e0d00788, 16MB, `/dev/cu.usbserial-57040013171`. Fresh critical
backup retained and checksum verified:
`out/board-backups/20261019-angry-release/08f9e0d00788-20261019-070504-critical.bin`.
SHA256 `9f3faac3751e6db5179cd59f7ccdd34a8158ae43445e8760b8fa5065732c13cc`.
Firmware and FS upload succeeded without erasing NVS or the reserve.
Independent esptool verify matched both partitions at 0x10000 / 0x410000.

- Firmware SHA256: `d690b5fbd07b64a8504af6b0c77e4bd2113182f526f8002cf486c7cf62c46012`
- LittleFS SHA256: `89078b1a45ae27dd284f2ee91100957370e947711228070da17af35e6b5c2cff`

Deploy OK and normal VPET_READY: free heap 66148/minimum 66088, manifest 1;
FS 11677696/12451840, BLE PAIRED/CONNECTED. Actual free FS is 774144 bytes,
including filesystem overhead (not the 12.91% payload-budget margin).
Used FS decreases 266240 bytes compared with the prior verified installation.
Logs are local under `out/angry-board-deploy/`, excluded from publication.
Physical mood activation/animation acceptance remains open; no pet mood,
species, inventory or clock was injected to stage a demonstration.
The 45s startup observation ended with ANGRY_BOARD_BOOT_OK: four runtime
samples, free heap 66148 throughout, watermark 60972, BLE connected and no
fatal. First interval max 1015047us; subsequent maxima 92..93ms. This idle
observation is not an FPS, active-menu or long-session claim.
