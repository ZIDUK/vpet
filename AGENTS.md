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
- **T-Display deploy authorization (2026-10-08):** the user has explicitly granted
  Mavis permission to flash the connected ESP32 T-Display board for vPet work.
  Preconditions before flashing: (1) the user has confirmed the final build
  incorporates the current Status adjustments in `scripts/sim_renderer.py` and
  `firmware/t-display/src/Panels.cpp`; (2) `pio run -d firmware/t-display -e tdisplay`
  completes with the new build artifacts. Do not flash an older binary.
  **User update (2026-10-29):** physical evidence or screenshots of the four
  Status pages are no longer required before flashing. This does not turn a
  successful upload into verified physical gameplay, visual or radio acceptance.
- Never delete `out/board-backups/` during cleanup.
- Keep historical Pico material under its existing legacy labels.

## Testing

- Local spec-driven pilot (2026-10-28): follow `docs/spec-driven-development.md`.
  New features use `docs/templates/spec.md`, stable REQ/AC IDs in
  `docs/requirements.json`, a separate spec/plan and explicit acceptance criteria.
  Historical documents migrate incrementally; never invent retrospective approval.
- Run `make spec-check` and `make verify-local` for the Creator/process pilot;
  use `make verify-local-full` for whole-project local verification.
  Report actual scope and failures. Never equate structural links with passing tests,
  or automated tests with human approval, publication or physical board acceptance.
- Do not add GitHub Actions or install Git hooks/config for this workflow.
  Verification is local; approval/traceability status is never promoted automatically.

- Run `.venv-platformio/bin/python -m pytest -q` for Python changes.
- Run `.venv-platformio/bin/pio test -d firmware/t-display -e native` for C++ core changes.
- Run `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay` for firmware changes.
- Physical behavior is unverified until an explicit board deployment and visual/radio check.

## Change Boundaries

- `src/core/` and `firmware/t-display/lib/vpet_core/`: deterministic domain logic.
- `scripts/`: build, simulation, validation and deployment orchestration.
- `firmware/t-display/src/`: platform adapters and rendering.
- `docs/`: update when architecture, persistence, connectivity or workflow changes.

## Coordination (effective 2026-10-08)

- **Codex** owns the Status menu layout/drawing (`scripts/sim_renderer.py`,
  `scripts/preview_status.py`) and the pixel-level comparison against the approved
  mockup, including the layout/UI tests that pin pixel positions.
- **Mavis (M3)** owns the Status domain surface: model, values, rules,
  i18n/data catalog, and contracts (`src/core/pet.py`, `src/core/status_card.py`,
  `src/core/i18n.py`, helpers `format_age`, `tr_status_dna_label`,
  `combat_stat`, `format_dna_id`, `helix_spin`, `helix_color565`,
  `src/core/menu.py` rules and enums).
- **Do not edit** the renderers or layout/UI tests while Codex is adjusting the
  Status UI. Domain contracts must stay backward-compatible so the renderer can
  swap to the new mockup without breaking pet persistence (NVS schema, numeric
  enums, balance, save rules preserved).
- Document only domain facts in `docs/`; visual/layout decisions live with Codex.
