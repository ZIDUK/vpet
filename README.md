# vPet

A Digimon-style virtual pet on a Raspberry Pi Pico W with a Waveshare Pico-LCD-1.44 (ST7735S 128×128).

## What it is

Two evolution lines (Agumon, Gabumon), 4 stages each. Real stats (hunger/energy/happiness/HP),
real actions (feed/heal/play/rest), real turn-based battles, real persistence across reboots.
It's a Tamagotchi that grows up, evolves, and remembers what happened.

## Hardware

- **MCU**: Raspberry Pi Pico W (RP2040, 264KB RAM, 2MB flash)
- **Display**: Waveshare Pico-LCD-1.44 (ST7735S 128×128, SPI)
- **Buttons**: 2× tactile switches on GP15/GP17 (active LOW)
- **Firmware**: CircuitPython 10.2.1

## Repo layout

```
src/           — modular Python (the source of truth)
  hal.py       — display + button init
  core/        — game logic (pet, evolution, battle, save)
  ui/          — display widgets (bars, buttons, sprites)
  data/        — JSON config: 8 evolution forms + NPCs
  app.py       — entrypoint / main loop

assets/        — raw art, dev only (NOT deployed)
  raw/         — original source files (Agumon_atlas, Greymon, etc.)
  atlas/       — generated sprite atlases
  backgrounds/ — background BMPs
  mockups/     — UI sketches

build/         — generated output (deployed to the Pico)
  code.py      — flattened from src/ by scripts/build.py
  Agumon/      — sprite BMPs
  Background/  — background BMPs
  settings.toml

scripts/       — dev tooling
  build.py     — src/ → build/code.py
  deploy.py    — build/ → /Volumes/CIRCUITPY/
  simulator.py — run vPet on Mac in pygame (TODO)

tests/         — pytest, run on Mac
docs/          — architecture, hardware notes, ADRs
.plan/         — roadmap, current sprint, ideas
```

## Workflow

```bash
make build     # src/ → build/code.py
make test      # run pytest
make deploy    # build/ → /Volumes/CIRCUITPY/  (Pico must be plugged in)
make all       # build + test + deploy
```

## What works now (M0 + M1)

- [x] Display: jungle background, animated sprite, 4 stat bars, 4 action buttons
- [x] Buttons: navigate menu, apply action
- [x] Stats: hunger, energy, happiness, HP — decay over time, action effects, caps at 100
- [x] Persistence: save/load to `/pet_save.json` (survives reboot)
- [x] Build pipeline: src/ → build/code.py
- [x] Deploy pipeline: build/ → /Volumes/CIRCUITPY/
- [x] Tests: 24/24 passing on Mac

## What's next

- [ ] Real Agumon sprite (placeholder is just colored squares)
- [ ] Other 7 evolution forms (greymon, metalgreymon, wargreymon, gabumon, garurumon, weregarurumon, metalgarurumon)
- [ ] Battle UI on the screen
- [ ] Pygame simulator (test on Mac without flashing Pico)
- [ ] Evolution animation (flash + sprite swap)

## Hardware pinout

| Pin | Function |
|-----|----------|
| GP10 | SPI SCK |
| GP11 | SPI MOSI |
| GP8  | LCD DC |
| GP9  | LCD CS |
| GP12 | LCD RST |
| GP13 | LCD backlight (active HIGH) |
| GP15 | Button 0 (next) |
| GP17 | Button 1 (action) |

See `docs/hardware-notes.md` for the gotchas (CP 10.2.1 API, lib version mismatch,
AppleDouble noise on FAT, etc).
