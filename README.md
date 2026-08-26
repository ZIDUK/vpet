# vPet

A Digimon-style virtual pet on a Raspberry Pi Pico W with a Waveshare Pico-LCD-1.44 (ST7735S 128×128).

## What it is

Two evolution lines (Sprout, Agumon), 6 stages each (egg → baby → rookie → champion → ultimate → mega).
Real stats (hunger/energy/happiness/HP), real actions (feed/heal/play/rest), real turn-based battles,
real persistence across reboots. It's a Tamagotchi that grows up, evolves, and remembers what happened.

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
  data/        — JSON config: 6 evolution forms + NPCs
  app.py       — entrypoint / main loop

assets/        — raw art, dev only (NOT deployed)
  digimon/     — sprite BMPs by line/stage/state
  ui/          — button icons
  backgrounds/ — background BMPs

build/         — generated output (deployed to the Pico)
  code.py      — flattened from src/ by scripts/build.py
  digimon1/    — sprite BMPs (collapsed <line>/<stage>/<file>.bmp)
  Background/  — background BMPs
  UI/buttons/  — button icon BMPs
  settings.toml

scripts/       — dev tooling
  build.py     — src/ + assets/ → build/ (with BMP height-sign normalization)
  deploy.py    — build/ → /Volumes/CIRCUITPY/
  sim.py       — pygame simulator (preview UI on Mac without flashing)

tests/         — pytest, run on Mac
docs/          — architecture, hardware notes
  hardware.md  — Pico-LCD-1.44 spec, pinout, SPI protocol
  architecture.md — software architecture, data flow, module map
.plan/         — roadmap, current sprint, ideas

boot.py        — runs before code.py on every Pico boot (disables REPL display)
```

## Quick start (first time, on a new machine)

```bash
# 1. Clone the repo
git clone git@github.com:ZIDUK/vpet.git
cd vpet

# 2. Make sure Python 3.10+ is installed
python3 --version

# 3. Install dev deps (for build, test, deploy)
python3 -m pip install pytest pillow

# 4. (Optional, for the simulator) install pygame
# Use the system Python that has displayio/adafruit-blinka
/usr/bin/python3 -m pip install --user pygame

# 5. Plug in the Pico W (must already have CircuitPython 10.2.1 firmware)
ls /Volumes/CIRCUITPY/  # if you see boot_out.txt, you're good

# 6. Build + test + deploy
make all
```

After `make all`, the Pico reboots and shows the vPet on the display.

## Workflow (every day)

| Command | What it does |
|---|---|
| `make build` | Flatten `src/*.py` → `build/code.py`, copy + normalize BMPs |
| `make test` | Run pytest (game logic tests) |
| `make deploy` | Copy `build/*` to `/Volumes/CIRCUITPY/` (Pico must be plugged in) |
| `make all` | clean + build + test + deploy in one shot |
| `make sim` | Open the vPet in a pygame window on Mac (no Pico needed) |
| `make sim-record` | Same as sim but saves every frame as PNG to `out/sim_frames/` |
| `make clean` | Delete `build/*` except `code.py` and `settings.toml` |

## Simulator (preview UI on Mac)

The `make sim` target runs `scripts/sim.py` which renders the same UI the
Pico shows, in a pygame window on your Mac. Same BMPs, same layout, same
colors — but you can iterate in milliseconds instead of flashing the device.

**Setup** (one time):
```bash
# pygame
/usr/bin/python3 -m pip install --user pygame
# PIL is already needed for the build pipeline
```

**Run**:
```bash
make sim
```

A 512×512 window opens (4× scale of the 128×128 internal framebuffer).
The simulator reads from `build/` so run `make build` first if you
changed sprites in `assets/`.

**Keys while running**:
- `n` — NEXT button (cycle menu selection)
- `a` — ACTION button (apply selected action; raises the focused stat)
- `r` — reset all stat values to defaults
- `1`-`6` — switch digimon (egg / baby / rookie / champion / ultimate / mega)
- `q` / `ESC` — quit

## Deployment guide

### A. First time — flash CircuitPython firmware

The Pico W must be running CircuitPython 10.2.1 or newer.

1. Download firmware: https://circuitpython.org/board/raspberry_pi_pico_w/
   Pick the latest stable `.uf2` for Pico W.
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
2. Copy `code.py`, `boot.py`, `settings.toml`, `digimon1/`, `Background/`, `UI/buttons/` to the device.
3. Download CircuitPython 10 lib bundle (cached in `~/.cache/vpet/cp10_bundle.zip`).
4. Sync the needed `.mpy` files to `/Volumes/CIRCUITPY/lib/`.
5. Normalize all BMPs to positive height (CP 10.2.1 bug workaround).
6. Clean macOS AppleDouble metadata (`._*` files).

After ~10 seconds, the Pico reboots and shows the vPet on screen.

### C. Day-to-day — change code and re-deploy

```bash
# 1. Edit src/ or assets/
# 2. (Optional) Preview the UI on Mac
make sim
# 3. Build + test + deploy
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

## What works now

- [x] Display: jungle background, animated sprite, 4 stat bars, 4 action buttons
- [x] Buttons: navigate menu, apply action
- [x] Stats: hunger, energy, happiness, HP — decay over time, action effects, caps at 100
- [x] State machine: egg → hatching (8s animation) → live
- [x] Persistence: save/load to `/pet_save.json` (survives reboot)
- [x] Build pipeline: src/ → build/code.py + asset normalization
- [x] Deploy pipeline: build/ → /Volumes/CIRCUITPY/
- [x] Pygame simulator: preview UI on Mac without flashing
- [x] Tests: 32/32 passing on Mac

## Hardware gotchas (CP 10.2.1)

- `displayio.OnDiskBitmap` misreads BMPs with **negative height** (top-down) — bug in 10.2.1. The build
  pipeline normalizes all BMPs to positive height + bottom-up rows. Symptom: blank black or
  garbled sprites that load fine on the Mac.
- `displayio.Palette` with 1 entry and a single index, no `make_transparent` call, can render the
  whole bitmap as the display's clear color. Use 2+ entry palettes for anything with transparency.
- `print()` in `code.py` activates `CIRCUITPYTHON_TERMINAL` which takes over the display. We silence
  prints at runtime; use the REPL for debug output.
- `supervisor.runtime.display = None` is brittle; we set it from `boot.py` instead, which runs before
  the auto-attached REPL display claim.
- macOS AppleDouble (`._*`) files: 40KB+ of waste on every deploy. `make deploy` cleans them up.
- The autoreload race on `code.py` write: deploy copies other files first, `code.py` last, with
  retry on `OSError: [Errno 22]`.

## Quick reference

- **Pinout**: see `docs/hardware.md`
- **Architecture**: see `docs/architecture.md`
- **Roadmap**: see `.plan/roadmap.md`
- **Current sprint**: see `.plan/current-sprint.md`
