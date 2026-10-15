# Project Documentation

> Generated: 2026-10-05 | Mode: FULL | Scope: repository audit

## Tech Stack

- Active hardware: LILYGO TTGO T-Display classic ESP32, ST7789 240x135.
- Firmware: C++17-compatible portable core, Arduino ESP32, PlatformIO.
- Graphics: TFT_eSPI, LittleFS, generated VPA1 assets.
- Simulator and asset pipeline: Python 3, Pillow, pygame, pytest.
- Bluetooth: NimBLE-Arduino 2.5.1. WiFi UI is intentionally disabled.
- Legacy compatibility: Raspberry Pi Pico W/CircuitPython remains supported by the preserved build/deploy path.

## Architecture Pattern

Layered architecture with a portable domain core. Python is the simulator and
asset reference; `firmware/t-display/lib/vpet_core` contains portable C++ rules;
the ESP32 adapter owns TFT, GPIO, BLE, NVS and LittleFS. Generated assets are
build products, not hand-edited source.

## Folder Structure

- `assets/`: curated source PNGs.
- `src/`: Python model, simulator support and preserved Pico runtime.
- `scripts/`: asset conversion, simulator, validation and deployment tooling.
- `firmware/t-display/`: active PlatformIO firmware.
- `tests/`: Python tests, cross-language traces and native Unity tests.
- `docs/`: architecture, operations, hardware and historical plans.
- `build/`: committed Pico compatibility artifact.
- `build-tdisplay/`, `.pio/`, `out/`: local generated outputs; do not commit.

## Key Contracts

- Assets are source PNGs under `assets/`; T-Display payloads are regenerated.
- NVS schema 3 is the current firmware save schema; older schemas 1 and 2 migrate.
- IV/EV values are preserved in saves and feed combat stats.
- Practice combat is currently complete in Python/simulator and portable C++;
  firmware UI/NVS integration is not complete.
- BLE is enabled on demand. WiFi remains out of the current product surface.

## Testing

- Python: pytest unit/integration tests, including simulator rendering and
  Python/C++ practice trace parity.
- C++: PlatformIO native Unity tests for input, navigation, state, BLE session,
  evolution, and practice combat.
- Firmware: PlatformIO compile for `tdisplay`.
- Physical tests are intentionally separate and require explicit deployment.

## Operational Entry Points

- `make sim`: normal T-Display simulator.
- `make sim-practice`: Firemon Tech/practice simulator.
- `make test`: Python suite.
- `make native-test`: portable C++ tests.
- `make firmware`: compile firmware without uploading.
- `make deploy`: build, test, backup and upload; requires explicit approval.

The interactive architecture artifact is
`.archify/architecture-vpet-20261005/review-2/vpet-architecture.html`.

## Cleanup Findings

- Removed local Python caches, pytest cache and temporary practice preview output.
- Kept committed `build/` because it is the documented Pico compatibility
  artifact used by `make build-pico` and `make deploy-pico`.
- Kept `docs/legacy/` and historical plans as explicitly labeled history.
- Kept `src/core/battle.py` because existing Pico/runtime tests still exercise it.
- Kept `out/board-backups/` because those files are recovery material.

## Last Scanned

2026-10-05
