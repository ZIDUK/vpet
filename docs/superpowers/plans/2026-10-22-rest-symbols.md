# Rest Symbols Implementation Plan

**Goal:** Apply the requested visual revision: sweat drops for low energy,
and a sleepy face without any caption or time for bedtime.

**Architecture:** Keep RestKind, cue priorities, energy recovery goals and
sleep/persistence rules unchanged. Replace only the two source glyphs used
by the existing energy/rest bubble variants. Draw the existing energy
caption only for Energy, never for Bedtime, in both renderers.

**Tech Stack:** Python/Pillow, portable C++, TFT/LittleFS, pytest.

## Approved Scope

- Low energy retains its numeric goal and bar; replace lightning with sweat.
- Bedtime is bubble-only: sleepy face, no title, clock or black caption.
- Keep angry variants, suppression, positions, dimensions and frame cadence.
- Do not alter hunger, feeding, Status, Training, Arena, sleep duration,
  recovery rate, learned bedtime, saved data or enum values.
- Preserve generated image originals; package them using the normal builder.
- Rest -> Apagar luz already starts a 30-minute daytime nap or a nighttime
  session of at least eight hours/until dawn. Recovery is +1 per five minutes
  while powered. This delivery changes none of those existing rules.

## Tasks

- [x] RED: bedtime has no text/time/black caption in real Renderer and sim;
  existing energy goal/bar stays visible. Keep full sleep pixel comparisons.
- [x] Integrate two generated transparent glyphs into mood_assets.py,
  regenerate assets and keep the other nine mood assets byte-identical.
- [x] Restrict captions to Energy in Renderer.cpp and sim_renderer.py.
- [x] Inspect scaled/native previews, run focused/full Python and firmware
  validation, regenerate Pico and smoke-test the isolated simulator.
- [x] Update current roadmap and record host/USB evidence separately.
- [x] USB deployment: user reconnected hardware and explicitly waived prior
  physical Status validation for this delivery. Fresh build/backup, upload,
  independent firmware/FS verification and normal startup observation passed.

## Evidence

- RED: 12 bedtime cases failed on the old text/time caption; six Energy
  cases already passed. Source-independence test also failed because the
  old builder required the menu bulb tile.
- Focused tests: 198 passed before expanding caption cases to both normal
  and low mood. Full suite includes that expanded matrix (ES/EN, both
  bedtime reasons, three positions, both moods).
- Native tests: 185 passed. No core, enum or persistence changes.
- Final full Python suite: 1432 passed in 235.95 seconds, including the
  expanded low-mood captionless matrix. Existing Pillow/pytest deprecation
  warnings remain; no test failures. `git diff --check` passed.
- Firmware compiled: static RAM 56108/327680; app 1015085/4194304.
- Regenerated assets: 225 files, 10789125 payload bytes. Only four mood
  assets differ; all nine others (including hunger and Status faces) match
  the prior output byte-for-byte.
- Inspected `out/rest-symbols/overview.png`: droplets with energy goals,
  bedtime face without caption, ES/EN and left/center/right positions.
  Previews use independent pets, not live save injection.
- Eight Status views (four pages, ES/EN) remain byte-identical to the prior
  renderer at the same inputs. Isolated simulator smoke run: 90 frames, exit 0.
- LittleFS image built successfully. Payload plus manifest: 10846862 bytes,
  12.89% asset-budget margin; not a measurement of actual filesystem free space.
- Sources: two transparent image_gen originals added to the exact mood PNG
  allowlist in .gitignore; normal builder packs them without repainting.
- At initial preparation USB serial was not detected. Subsequent deployment
  is recorded below; physical visual acceptance remains separate.

Prepared binary/source SHA-256 (not verification of flashed hardware):

```text
firmware.bin 7b8a2b24d46f06efd534705b04a6f8d762492f5aeebfdd7eb84cb641e7e2a08f
littlefs.bin 4b9ad7781b66729334f99498bab21c3417a99bafde18366cd264e4001ccfa062
fatigue-drops-v1.png 91666034f596b4561949ac7f5caf7aedfaeb8852795d863bea5f5c4892789e40
sleepy-face-v1.png c8d05181296fe42809fa54a51d25da9aa5af8bb34e46412d30ceae364302decb
```

## USB Follow-Up: 2026-10-22

The user connected the board and explicitly authorized deploying this
revision without the repository's pending prior physical validation of the
four Status pages. This exception applies to this delivery only; it does
not close physical Status acceptance or change the standing guardrail.
The eight host Status views remain byte-identical to the previous renderer.

Fresh build of source revision `3a9c406` succeeded before upload; firmware
SHA-256 still matches the prepared image above. Detected ESP32-D0WDQ6-V3,
MAC 08f9e0d00788, 16 MB, `/dev/cu.usbserial-57040013171`.

Fresh critical backup (partition table + NVS, 24576 bytes) retained:
`out/board-backups/20261022-rest-symbols-deploy/08f9e0d00788-20261022-135455-critical.bin`.
Stored and recomputed SHA-256 match:
`9f3faac3751e6db5179cd59f7ccdd34a8158ae43445e8760b8fa5065732c13cc`.
No live-pet state was injected to stage the needs or mood.

`uploadfs` rebuilt the LittleFS image during deployment. Its digest for
this upload is `7cdeabc8a7c3f3a682b6236cf381e00e534572fd02344a076de39d3c9125b40d`,
distinct from the earlier prepared image above. All 225 source assets were
checked against their manifest (sizes and SHA-256), payload 10789125 bytes.
Independent USB verification used the actual rebuilt upload image.

Firmware and LittleFS uploaded successfully without erasing NVS/reserve.
Independent esptool verification matched both images at 0x10000 and
0x410000. Firmware digest is unchanged from the prepared image; installed
LittleFS digest is the rebuilt value above. Local evidence (not published):
`out/rest-symbols/deploy.log`, `verify-flash.log` and `board-boot.log`.

Deploy OK / VPET_READY: heap free 66144, minimum at ready 66124, flash
16777216, manifest 1, filesystem 11685888/12451840. Actual filesystem free
space is 765952 bytes including overhead, not the 12.89% asset-budget margin.

Normal reset plus 45-second serial observation ended with
`REST_SYMBOLS_BOARD_BOOT_OK`: four runtime samples, free heap 66144 in each,
watermark 61008, BLE ADVERTISING/PAIRED/CONNECTED (runtime state 2), zero
fatal lines and no observed restart. First loop maximum 430369us, later
maxima 65913/66017/65668us. This is idle startup evidence, not an FPS,
long-session/reconnection claim or visual acceptance of the physical screen.
