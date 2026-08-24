# vPet

A Digimon-style virtual pet on a Raspberry Pi Pico W with a Waveshare Pico-LCD-1.44 (ST7735S 128×128).

## What it is

Two evolution lines (Agumon, Gabumon), 4 stages each. Real stats (hunger/energy/happiness/HP),
real actions (feed/heal/play/rest), real turn-based battles, real persistence across reboots.
It's a Tamagotchi that grows up, evolves, and remembers what happened.

## Hardware

- **MCU**: Raspberry Pi Pico W (RP2040 dual-core ARM Cortex-M0+, 264KB RAM, 2MB flash)
- **Display**: Waveshare Pico-LCD-1.44 (1.44" TFT, ST7735S driver, 128×128 px, 65K RGB, SPI)
- **Buttons**: 2× tactile switches on GP15/GP17 (KEY0/KEY1)
- **Firmware**: CircuitPython 10.2.1
- **Power**: USB (VBUS 5V) or VSYS 1.8V-5.5V

See [`docs/hardware.md`](docs/hardware.md) for the full pinout, electrical specs, and protocol details.

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
  hardware.md  — Pico-LCD-1.44 spec, pinout, SPI protocol
  architecture.md — software architecture, data flow, module map
.plan/         — roadmap, current sprint, ideas
```

## Quick start (first time, on a new machine)

```bash
# 1. Clone the repo
git clone git@github.com:ZIDUK/vpet.git
cd vpet

# 2. Make sure Python 3.10+ is installed (for build, test, deploy scripts)
python3 --version

# 3. Install pytest (only dev dep)
python3 -m pip install pytest

# 4. Plug in the Pico W (must already have CircuitPython 10.2.1 firmware)
ls /Volumes/CIRCUITPY/  # if you see boot_out.txt, you're good

# 5. Build + test + deploy
make all
```

After `make all`, the Pico reboots and shows the vPet on the display.

## Workflow (every day)

| Command | What it does |
|---|---|
| `make build` | Flatten `src/*.py` → `build/code.py` (single file CircuitPython can run) |
| `make test` | Run pytest (24 tests) |
| `make deploy` | Copy `build/*` to `/Volumes/CIRCUITPY/` (Pico must be plugged in) |
| `make all` | build + test + deploy in one shot |
| `make sim` | Run the vPet in a pygame window on Mac (TODO) |
| `make clean` | Delete `build/code.py` |

## Deployment guide (the step-by-step)

### A. First time — flash CircuitPython firmware

The Pico W must be running CircuitPython 10.2.1 or newer.

1. Download firmware: https://circuitpython.org/board/raspberry_pi_pico_w/
   - Pick the latest stable `.uf2` for Pico W.
2. Enter bootloader mode:
   - Hold the **BOOT** button on the Pico.
   - While holding, plug the USB cable into your Mac.
   - Release BOOT after 1 second.
   - Mac will mount a drive called `RPI-RP2`.
3. Copy the `.uf2` file to `RPI-RP2`. The drive will auto-eject and remount as `CIRCUITPY`.
4. Verify: `ls /Volumes/CIRCUITPY/boot_out.txt` exists.

### B. First time — install this app

With the Pico mounted as `CIRCUITPY`:

```bash
cd /path/to/vpet
make deploy
```

This will:
1. Build `src/ → build/code.py` (one flattened file).
2. Copy `code.py`, `settings.toml`, `Agumon/`, `Background/` to the device.
3. Download CircuitPython 10 lib bundle (cached in `~/.cache/vpet/cp10_bundle.zip`).
4. Sync the needed `.mpy` files to `/Volumes/CIRCUITPY/lib/`.
5. Clean macOS AppleDouble metadata (`._*` files).

After ~10 seconds, the Pico reboots and shows the vPet on screen.

### C. Day-to-day — change code and re-deploy

```bash
# 1. Edit src/app.py or any module
# 2. (Optional) Run tests on Mac
make test
# 3. Build + deploy
make deploy
# 4. Pico auto-reboots (via CircuitPython's autoreload on file write)
#    If autoreload is disabled, press the physical RESET button on the Pico
#    or run: python3 -m mpremote connect /dev/cu.usbmodem1301 exec "import supervisor; supervisor.reload()"
```

### D. Debug — read the serial console

```bash
# Install mpremote if not already
python3 -m pip install mpremote

# Open REPL
python3 -m mpremote connect /dev/cu.usbmodem1301

# In REPL, common commands:
#   Ctrl+C         → break out of code.py
#   Ctrl+D         → soft-reboot
#   import os; os.listdir('/')  → see files on device
#   help('modules') → list all loaded modules
#   print(board.GP15.value)     → read button state
#   import displayio; ...       → inspect display state
```

The serial port on macOS is `/dev/cu.usbmodem1301` (the `usbmodem` number can change).
To find yours: `ls /dev/cu.usb*`.

### E. Reset / reflash the Pico

If the device gets into a bad state:

```bash
# Soft reset (runs code.py fresh)
python3 -m mpremote connect /dev/cu.usbmodem1301 exec "import supervisor; supervisor.reload()"

# Hard reset (unplug and replug USB)

# Full reflash (erases everything including lib/ and saved state)
# 1. Hold BOOT, plug USB, release BOOT (mounts as RPI-RP2)
# 2. Copy the CircuitPython .uf2 firmware again
# 3. Re-run make deploy
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

## Quick reference

- **Pinout**: see `docs/hardware.md`
- **Architecture**: see `docs/architecture.md`
- **Roadmap**: see `.plan/roadmap.md`
- **Current sprint**: see `.plan/current-sprint.md`
- **Hardware gotchas**: see `docs/hardware-notes.md` (CP 10.2.1 API, lib version, AppleDouble, etc.)
