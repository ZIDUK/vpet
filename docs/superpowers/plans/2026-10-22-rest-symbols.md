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
- [ ] USB deployment requires connected hardware and repository prerequisites;
  no serial port was detected. Publication is verified against origin/master
  after commit/push, not inferred from a local commit alone.

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
- USB serial not detected; no board deployment or physical acceptance yet.

Prepared binary/source SHA-256 (not verification of flashed hardware):

```text
firmware.bin 7b8a2b24d46f06efd534705b04a6f8d762492f5aeebfdd7eb84cb641e7e2a08f
littlefs.bin 4b9ad7781b66729334f99498bab21c3417a99bafde18366cd264e4001ccfa062
fatigue-drops-v1.png 91666034f596b4561949ac7f5caf7aedfaeb8852795d863bea5f5c4892789e40
sleepy-face-v1.png c8d05181296fe42809fa54a51d25da9aa5af8bb34e46412d30ceae364302decb
```
