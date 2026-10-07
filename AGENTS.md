# AGENTS.md - vPet

> Repository guidance generated from the 2026-10-05 audit.

## Stack Context

Active target: PlatformIO Arduino C++ firmware for the 240x135 ESP32 T-Display,
with a Python/Pillow/pygame simulator and a preserved Pico/CircuitPython path.

## Guardrails

- Treat `firmware/t-display/` as the active hardware implementation.
- Keep domain rules portable and free of Arduino/TFT/NimBLE dependencies.
- Regenerate `build-tdisplay/` and LittleFS data; do not hand-edit generated files.
- Preserve NVS schema compatibility and existing numeric enum values.
- Do not enable WiFi or deploy to hardware without an explicit user request.
- Never delete `out/board-backups/` during cleanup.
- Keep historical Pico material under its existing legacy labels.

## Testing

- Run `.venv-platformio/bin/python -m pytest -q` for Python changes.
- Run `.venv-platformio/bin/pio test -d firmware/t-display -e native` for C++ core changes.
- Run `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay` for firmware changes.
- Physical behavior is unverified until an explicit board deployment and visual/radio check.

## Change Boundaries

- `src/core/` and `firmware/t-display/lib/vpet_core/`: deterministic domain logic.
- `scripts/`: build, simulation, validation and deployment orchestration.
- `firmware/t-display/src/`: platform adapters and rendering.
- `docs/`: update when architecture, persistence, connectivity or workflow changes.
