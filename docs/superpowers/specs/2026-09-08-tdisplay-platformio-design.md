# LILYGO T-Display PlatformIO Port Design

## Goal

Port vPet to the original LILYGO/TTGO T-Display using PlatformIO, the Arduino
framework and TFT_eSPI. The physical board becomes the default deployment
target while the existing Pico W CircuitPython path remains available as an
explicit compatibility target.

The desktop simulator and T-Display must present the same gameplay state,
navigation order, artwork and screen geometry. `make sim` is the normal feature
development loop. `make deploy` builds, validates and uploads the same feature
set to the connected T-Display.

## Confirmed Hardware Profile

The target is the original ESP32 T-Display, not the T-Display S3:

| Capability | Value |
|---|---|
| MCU | ESP32-D0WDQ6-V3, dual core, 240 MHz |
| Flash | 16 MB |
| PSRAM | None |
| Display | ST7789V IPS, 1.14 inch |
| Native display | 135x240 pixels |
| Application orientation | 240x135 landscape |
| USB serial | WCH bridge, currently `/dev/cu.usbserial-57040013171` |

The firmware configures TFT_eSPI with MOSI 19, SCLK 18, CS 5, DC 16, RST 23
and backlight 4. The backlight is active high.

GPIO35 is the NEXT/selector button and GPIO0 is the ACTION button. Both are
active low and use the pull-up circuitry provided by the board. GPIO0 is also a
boot strap pin, so the documentation warns against holding ACTION while the
board resets or begins an upload.

## Approved Screen Layout

All primary rendering uses a 240x135 logical framebuffer. No runtime stretches
the previous 128x128 interface.

- The top menu is 24 pixels high and contains eight 30x24 cells.
- Each menu icon fits within 20x20 pixels and is centered in its cell.
- The selected cell uses a two-pixel yellow border without changing layout.
- The content area is 240x111 pixels, from y=24 through y=134.
- Normal pet frames fit within an 88x88 box. Build-time trimming preserves a
  transparent margin and prevents any frame from crossing the content bounds.
- Autonomous motion clamps the frame to the content rectangle. Dragfiremon uses
  the fly animation as its movement cycle.
- Full-screen panels use the complete 240x111 content area rather than cards
  inherited from the square layout.
- Pixel art uses nearest-neighbor scaling and integer coordinates. Sprite
  sources are regenerated directly at the new target size instead of enlarging
  the existing 64-pixel BMP atlases.

The approved visual reference is the companion mockup under
`.superpowers/brainstorm/50109-1788882468/content/index.html`.

## Evolution Guide Adaptation

The compact evolution-tree behavior in
`2026-09-05-evolution-tree-design.md` remains authoritative for discovery,
branch traversal, details and hidden forms. This port supersedes only its
128x128 dimensions and CircuitPython rendering details.

The T-Display overview uses 36x36 portraits in a three-stage horizontal window.
NEXT visits nodes left to right and top to bottom, including sibling branches;
ACTION opens details. Undiscovered forms are black silhouettes labeled `???`.
The detail screen may use an 88x88 idle frame. Every portrait, connector and
label is clipped to the 240x111 panel bounds.

## Repository Structure

The port adds a native target without duplicating the original artwork or pet
catalog:

```text
src/                         Python gameplay reference and Pico runtime
assets/                      Original artwork
firmware/t-display/          PlatformIO Arduino project
firmware/t-display/src/      ESP32 application and renderers
firmware/t-display/include/  Generated-compatible data contracts
firmware/t-display/data/     Generated LittleFS asset package
scripts/                     Shared build, simulation and deployment tools
build/                       Generated Pico artifact
build-t-display/             Generated T-Display assets and reports
```

`src/data` and the source-art registry remain the canonical catalog. A build
step exports validated C++ data tables for species, menu actions and evolution
edges. Gameplay calculations that exist in Python receive matching native unit
tests with shared JSON fixtures so divergence is detected instead of hidden.

## PlatformIO Configuration

The PlatformIO environment uses the `esp32dev` board profile, the Arduino
framework and a pinned TFT_eSPI dependency. Display pins and driver options live
in a project-owned TFT_eSPI setup header selected through build flags; no file
inside a downloaded library is edited. The profile explicitly sets 16 MB flash
and the default 921600-baud upload speed may fall back to 460800 through the
`UPLOAD_SPEED` Make variable when a USB bridge is unreliable.

PlatformIO is installed into a repository-local `.venv-platformio` environment
through a bootstrap script. Make targets call that environment explicitly, so
the workflow does not depend on a globally installed `pio` executable.

The custom 16 MB partition table is fixed and checked after linking:

| Partition | Offset | Size | Purpose |
|---|---:|---:|---|
| NVS | `0x9000` | `0x5000` | Settings, WiFi and saved game |
| Application | `0x10000` | `0x400000` | Single factory application |
| LittleFS | `0x410000` | `0xBE0000` | Generated asset package |
| Coredump | `0xFF0000` | `0x10000` | Crash diagnostics |

The application and LittleFS partitions each retain at least ten percent free
space after a successful build. The post-boot free heap must be at least 64 KiB
and the minimum observed heap must remain at least 48 KiB during the startup
check. These thresholds are centralized deployment constants and covered by
tests.

Normal deploys never erase the complete flash and never erase NVS.

## Asset Pipeline

`scripts/build.py` continues to validate source sheets and produce the Pico
artifact. A T-Display asset builder uses the same registry and creates:

- 88x88 trimmed animation frames for normal states.
- 120x111 maximum evolution-transition frames, clipped to the content area.
- 36x36 evolution portraits and matching silhouettes.
- 20x20 menu icons.
- 240x135 day and night backgrounds.

Animations are stored in LittleFS as indexed-color frame data with one
transparent palette index and compact frame metadata. The firmware converts
only the frame being drawn to RGB565 in bounded scan-line buffers. Large source
PNGs and uncompressed full RGB565 atlases are never uploaded.

The generated manifest records each file's dimensions, frame count, byte size
and SHA-256 digest. Build validation rejects missing files, invalid graph
targets, oversized frames and pixels outside declared bounds.

## Native Firmware Architecture

The Arduino application is a non-blocking state machine driven by `millis()`.
It contains the following boundaries:

| Component | Responsibility |
|---|---|
| `App` | Main loop, active screen and command routing |
| `Input` | Debounce, short press and deliberate long-press handling |
| `PetState` | Stats, current species, inventory and discovered species |
| `Motion` | Idle/walk/fly timing, direction and bounded movement |
| `Renderer` | TFT_eSPI drawing and panel composition |
| `AssetStore` | Manifest validation and LittleFS frame loading |
| `SettingsStore` | Versioned NVS save/load and migration |
| `NetworkService` | WiFi scan, association, Internet check and NTP time |

The main loop never waits through an animation, network scan or save. Long
operations expose progress screens and continue servicing input and rendering.

## Input Contract

The two physical buttons and simulator keys share one semantic contract:

| Action | Board | Simulator |
|---|---|---|
| NEXT | GPIO35 short press | `n` |
| ACTION | GPIO0 short press | `a` |
| BACK | GPIO35 long press | `b` or Backspace |
| Development evolution | Not exposed in production | `e` |
| Quit | Power/disconnect | `q` |

NEXT advances selectors and wraps. ACTION opens or confirms the selected item.
BACK returns one level without losing edits; screens that require confirmation
provide an explicit CANCEL/BACK row as an alternative.

## Persistence, WiFi And Clock

The ESP32 implementation uses versioned NVS namespaces:

- `vpet_state` stores pet state, inventory and discovery history.
- `vpet_config` stores language, sound preference and clock settings.
- `vpet_wifi` stores the selected SSID and password only after a successful
  connection.

The options screen can scan nearby networks, select an SSID and edit its
password with the approved two-button character editor. After association, the
firmware performs a DNS lookup and a bounded HTTP connectivity check. It reports
local-network-only access separately from Internet access.

When Internet is available, NTP updates the ESP32 clock using the configured
timezone. Manual date and time remain editable and are saved as an offset when
network time is unavailable. The simulator performs equivalent operations
without changing the Mac's active network or system clock.

## Make Targets

The public workflow becomes:

```text
make sim             Build shared assets and run the 240x135 simulator
make test            Run Python, asset-contract and native tests
make build           Build simulator/Pico assets and T-Display firmware
make deploy          Verify and deploy to the connected T-Display
make deploy-pico     Run the preserved CircuitPython deployment path
make sim-pico        Optional 128x128 compatibility preview
make monitor         Open the T-Display serial monitor
```

`make sim` remains usable before PlatformIO is installed; it depends only on
the Python development environment. Native build and deploy targets bootstrap
PlatformIO when needed.

## T-Display Deployment Contract

`make deploy` performs these steps in order:

1. Detect one compatible serial device, or use `PORT=/dev/...` when supplied.
2. Query the chip with esptool and reject non-classic-ESP32 targets.
3. Confirm 16 MB flash before using the custom partition table.
4. On the first deployment, save a timestamped full-flash backup under
   `out/board-backups/`; later deploys preserve that backup.
5. Regenerate assets and run the complete test suite.
6. Build the PlatformIO firmware and LittleFS image.
7. Parse program flash, static RAM and filesystem usage. Stop before upload if
   any partition overflows or configured safety margins are crossed.
8. Upload the firmware and LittleFS image without a whole-chip erase.
9. Reset the board and monitor serial output for a bounded startup period.
10. Require a `VPET_READY` record containing free heap, minimum free heap,
    flash size, filesystem used/free bytes and loaded manifest version.

The command fails with a specific memory category:

- `FLASH_OVERFLOW` when the application exceeds its partition.
- `ASSET_STORAGE_OVERFLOW` when LittleFS cannot contain the generated package.
- `STATIC_RAM_OVERFLOW` when link-time RAM crosses its budget.
- `HEAP_STARTUP_LOW` when post-boot free or minimum heap is below the configured
  safety floor.
- `STARTUP_CRASH` for resets, exceptions or a missing readiness record.

Failed deployment reports retain PlatformIO and serial diagnostics. A complete
flash erase is a separate recovery command and is never part of `make deploy`.

## Backup And Recovery

The first T-Display deployment may replace unknown firmware currently on the
board, so the full 16 MB flash backup is mandatory. The backup filename records
the detected chip, MAC-derived board identifier and timestamp. Its SHA-256 is
stored beside it.

Recovery documentation provides one explicit esptool command to restore that
image. Restoring or erasing flash remains a deliberate manual operation. A
normal deployment preserves NVS, saved status, discoveries and WiFi settings.

## Verification

Automated verification covers:

- 240x135 dimensions, menu geometry and content clipping.
- Frame transparency, bounds, counts and manifest hashes.
- Idle/movement variation and Dragfiremon fly movement.
- Feed, training, sleep/night and battle animation routing for every species.
- Evolution graph traversal, branches, silhouettes and discovery persistence.
- Status, inventory, options, WiFi password editing and clock navigation.
- Button debounce, NEXT/ACTION mapping, long-press BACK and GPIO0 boot warning.
- Versioned NVS serialization and migration fixtures.
- Deployment device detection, first-backup behavior and every memory failure
  category using mocked command output.

The final acceptance sequence is:

```text
make test
make sim
make deploy
```

Acceptance requires a clean 240x135 simulator render, a successful native build,
a verified LittleFS upload and a post-reset `VPET_READY` serial report.

## Out Of Scope

This port does not define the pending gameplay requirements for evolving from
Flamemon to Dragfiremon, add a new sibling evolution, implement enemy battle
logic, or add sound hardware. It preserves those items as explicit future work
without inventing rules.
