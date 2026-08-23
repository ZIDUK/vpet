# vPet — Pocket Digimon-Style Virtual Pet Keychain

A real Agumon virtual pet on a 128x128 color display, two buttons, with full stats,
evolution, and a future web admin for remote care.

## Hardware (current)
- **Waveshare Pico-LCD-1.44** (Raspberry Pi Pico W + ST7735S 128x128 color LCD)
- 2 buttons (GP15, GP17)
- Backlight on GP13

## Quick start

### 1. Plug in your Pico
Connect the Pico-LCD-1.44 via USB. The `CIRCUITPY` volume should auto-mount.

### 2. Deploy
```bash
./deploy/deploy_to_pico.sh
```

This copies the runtime files (code.py, lib, assets, settings.toml) to the device.
The Pico auto-reloads in ~2 seconds.

### 3. Reset
If anything looks broken:
```bash
mv /Volumes/CIRCUITPY/code.py.bak /Volumes/CIRCUITPY/code.py
```

Or hard-reset: unplug, wait 5s, replug.

## Project structure

```
vpet/
├── code.py                 # vPet v13.0 - main runtime, deploy this
├── lib/                    # Adafruit libraries (CP 10.2.1 compatible)
│   ├── adafruit_st7735r.mpy
│   ├── adafruit_debouncer.mpy
│   ├── adafruit_ticks.mpy
│   └── adafruit_imageload/  # for sprite loading
├── Agumon/                 # Agumon sprite sheets (10 animations)
├── Background/             # Background images
├── icons/                  # Digimon-style action icons (for future use)
├── settings.toml           # WiFi config (for future M4)
│
├── deploy/                 # deployment scripts
│   └── deploy_to_pico.sh
│
├── docs/                   # Documentation, code snapshots
│   ├── code_v7_reference.py
│   └── code_v13_snapshot.py
│
├── .plan/                  # Planning (not deployed)
│   ├── roadmap.md          # milestones and vision
│   ├── current-sprint.md   # what we're working on now
│   └── ideas.md            # backlog of features
│
└── .gitignore              # excludes dev-only and future-scope files
```

## What's deployed vs not

**Deployed to the device** (only these):
- `code.py`
- `lib/` (just the .mpy files we need)
- `Agumon/`, `Background/`, `icons/`
- `settings.toml`

**Stays in the repo** (for development):
- `docs/` — code history, design notes
- `.plan/` — sprint plans, roadmap, ideas
- `deploy/` — scripts
- All other dev-only files (see `.gitignore`)

## Hardware
- See `docs/hardware-notes.md` (todo) for full pinout and gotchas

## Roadmap
See `.plan/roadmap.md`.

Current sprint: **M1 — Pet lifecycle** (mood, evolution, death, persistence).
See `.plan/current-sprint.md`.

## Tech notes

- **CircuitPython 10.2.1** on Pico W
- **`from fourwire import FourWire`** (not `from displayio import FourWire` — moved in CP 10)
- **ST7735S display**: 128x128, needs `colstart=2, rowstart=2, rotation=180` for proper centering
- **Backlight** must be enabled manually on GP13 (display doesn't auto-enable)
- **Sprite transparency**: `bmp.pixel_shader.make_transparent(0)` works, but only AFTER the bitmap is loaded into a TileGrid
- **Pico RAM**: 264KB total. With v13.0 running, ~140KB free. Plenty for M1 features.

## Development

The repo is a normal git project. Push to github.com/ZIDUK/vpet.

```bash
git add -A
git commit -m "your message"
git push origin master
```

To test changes on the device, just rerun `./deploy/deploy_to_pico.sh`.

## Status

- **v13.0** running on Pico-LCD-1.44 (committed as `33ba7c7`)
- T-Display variant was abandoned (overheating, killed the regulator)
- WiFi-feeding deferred to M4 (waiting for safer hardware)
