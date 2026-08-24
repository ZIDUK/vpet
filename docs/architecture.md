# Software Architecture

This document describes the vPet software architecture: how the modules fit together,
the data flow, and the technical constraints of running on a Pico W.

> **Companion doc**: [hardware.md](hardware.md) covers the board, display protocol,
> and pinout. Read both for full context.

## High-level design

```
┌────────────────────────────────────────────────────────────────────┐
│                         DEV MACHINE (macOS)                        │
│                                                                    │
│  src/app.py        ──┐                                              │
│  src/core/pet.py     ├──┐                                           │
│  src/core/evolution. ├──┤  (editable Python modules)                │
│  src/core/battle.py  ├──┤                                           │
│  src/core/save.py    ├──┘                                           │
│  src/hal.py          ──┘                                           │
│  src/ui/*, src/data/*                                              │
│         │                                                          │
│         │  python3 scripts/build.py                                │
│         ▼                                                          │
│  build/code.py  (single file, ~13 KB)                              │
│         │                                                          │
│         │  python3 scripts/deploy.py                               │
│         ▼                                                          │
│              /Volumes/CIRCUITPY/code.py                            │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                         TARGET BOARD (Pico W)                      │
│                                                                    │
│   /code.py  ──runs on boot──→  app + hal + core + ui (flattened)   │
│   /lib/*.mpy                   adafruit drivers (downloaded once)  │
│   /Agumon/*.bmp                sprite assets                       │
│   /Background/*.bmp            background art                      │
│   /pet_save.json               runtime state (auto-saved)          │
│   /settings.toml               future: WiFi creds, config          │
└────────────────────────────────────────────────────────────────────┘
```

## Why the build step?

CircuitPython has constraints that shape our architecture:

1. **No user packages on the root FS.** You can `import` from `lib/`, but you can't
   `from src.core import pet` because `src/` is not a package the import system knows
   about. So either:
   - (a) flatten all our modules into a single `code.py`, **or**
   - (b) install each module as a `.mpy` in `lib/`.

   We chose (a) — simpler, easier to debug, single source of truth.

2. **Author-time vs run-time split.** All human-edited code lives in `src/`. The
   `build/code.py` is generated and **should never be hand-edited**. The
   `deploy.py` script copies `build/*` to the device.

3. **Why `.mpy` libs at all?** The Adafruit driver code (`adafruit_st7735r.py`,
   `adafruit_debouncer.py`, etc.) is compiled to `.mpy` bytecode by Adafruit and
   shipped in their lib bundle. Compiling ahead-of-time saves RAM on the Pico.
   We download the matching bundle for our CircuitPython version (10.2.1) on first
   `make deploy` and cache it in `~/.cache/vpet/cp10_bundle.zip`.

## Module map

| File | Imports | RAM cost | Purpose |
|------|---------|----------|---------|
| `hal.py` | board, busio, displayio, digitalio, fourwire, adafruit_st7735r, adafruit_debouncer | low | Hardware init: SPI display + 2 buttons |
| `core/pet.py` | time | ~300B | Pet model: stats dict, decay, apply_action |
| `core/evolution.py` | time | ~500B | Evolution class with registry check |
| `core/battle.py` | random | ~400B | Turn-based battle vs NPC |
| `core/save.py` | json (built-in) | ~200B | JSON load/save to /pet_save.json |
| `ui/sprites.py` | displayio | low | BMP loading + TileGrid helpers |
| `ui/widgets.py` | displayio | ~400B | Stat bar, action button, selection ring |
| `app.py` | all of the above | ~1KB | Main loop, state machine, draw dispatch |

Total code footprint: ~3 KB compiled. The displayio + framebuffer + adafruit libs
take most of the Pico's 264 KB RAM. We have plenty of headroom for new features.

## Data flow (one frame of the main loop)

```
                       ┌─────────────────┐
                       │   Pico W boot   │
                       └────────┬────────┘
                                │ runs /code.py
                                ▼
        ┌───────────────────────────────────────────┐
        │  hal.init_display()    → ST7735R(...)      │
        │  hal.init_buttons()    → Debouncer × 2     │
        │  Pet()                 → stats = {70,70,..}│
        │  load_pet(pet)         → restore from JSON │
        │  Build displayio.Group → BG + sprite + bars│
        └───────────────────────────┬───────────────┘
                                    │
                                    ▼
   ┌──────────── Main loop (every 50ms) ────────────┐
   │                                                │
   │  b0.update() / b1.update()  ── sample pins     │
   │      │                                         │
   │      ├── b0.fell (KEY0 pressed)                │
   │      │     menu_idx = (menu_idx + 1) % 4       │
   │      │     sel_tg.x = 8 + menu_idx * 29        │
   │      │                                         │
   │      └── b1.fell (KEY1 pressed)                │
   │            pet.apply_action(menu_idx)          │
   │              → ACTION_EFFECTS[menu_idx]        │
   │              → stats[stat] += delta (cap 100)  │
   │            draw_bars()                         │
   │                                                │
   │  time.monotonic() every 0.12s                  │
   │      → sp_tg[0] = (frame + 1) % n_idle         │
   │      (sprite frame advance)                    │
   │                                                │
   │  pet.decay_if_due() every 3s                   │
   │      → stats[stat] -= 1 for all stats          │
   │      → draw_bars()                             │
   │                                                │
   │  time.monotonic() every 30s                    │
   │      → save_pet(pet) → /pet_save.json          │
   │                                                │
   │  time.sleep(0.05)                              │
   │                                                │
   └────────────────────────────────────────────────┘
```

## State management

The app holds all in-memory state in a single `Pet` object (see `src/core/pet.py`):

```python
@dataclass-like:
  species: str           # "agumon", "greymon", ...
  line: str              # "agumon_line" | "gabumon_line"
  stats: dict[str, int]  # {"h": 70, "e": 70, "p": 70, "hp": 70}
  born_at: float         # time.monotonic() at creation
  last_decay: float      # time.monotonic() of last decay
  battles_won: int
```

The Pet is serialized to JSON on every state change, plus every 30s as a safety
net. The save file lives at `/pet_save.json` on the device's flash. Format:

```json
{
  "species": "agumon",
  "line": "agumon_line",
  "stats": {"h": 70, "e": 70, "p": 70, "hp": 70},
  "battles_won": 0
}
```

`born_at` and `last_decay` are NOT persisted — they're reset to `time.monotonic()` on
load. This means a pet loaded from disk has its age "reset" to 0, but in practice
this is fine because evolution thresholds are based on `pet.age_seconds` (which is
just `now - born_at`).

## Data model: Digimon forms

Each form (8 total) is a JSON file in `src/data/digimon/`:

```json
{
  "name": "Agumon",
  "line": "agumon_line",
  "stage": "rookie",
  "sprite": "/Agumon/agumon_idle.bmp",
  "evolves_to": "greymon",
  "min_age_seconds": 60,
  "battles_required": 0,
  "requirements": {"h": 50, "e": 50, "p": 50, "hp": 70}
}
```

The evolution rules in `core/evolution.py` check these fields:

1. `species.evolves_to` is not null (else already at final form)
2. `pet.age_seconds >= min_age_seconds`
3. For each `(stat, min)` in `requirements`: `pet.get(stat) >= min`
4. `pet.battles_won >= battles_required`

If all pass for `STABILITY_SECONDS` (30s) continuously, evolution triggers.

The 8 forms, in order:

| Line | Stage 0 | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|---|
| agumon_line | Agumon (rookie) | Greymon (champion) | MetalGreymon (ultimate) | WarGreymon (mega) |
| gabumon_line | Gabumon (rookie) | Garurumon (champion) | WereGarurumon (ultimate) | MetalGarurumon (mega) |

## Data model: NPCs

Wild digimon to fight (in `src/data/npcs/wild.json`):

| id | name | HP | attack |
|---|---|---|---|
| goburimon | Goburimon | 30 | 8 |
| kunemon | Kunemon | 40 | 10 |
| betamon | Betamon | 50 | 12 |
| gabumon_wild | Gabumon | 60 | 14 |
| meramon | Meramon | 80 | 18 |

The battle system (in `core/battle.py`) is turn-based. Each round, the pet attacks
(power = (happiness + energy) / 4, ±3 random), then the NPC attacks (attack stat,
±2 random). Battle ends when either HP hits 0. Win → `battles_won++`. Loss →
`happiness -= 20`.

## Adding a new Digimon

1. Create `src/data/digimon/<name>.json` with the schema above.
2. Add the sprite BMP to `build/<species>/<name>_idle.bmp`.
3. Update `app.py` to load it: see `app.py`'s sprite loading section.
4. `make test` (verifies JSON is valid + chain is consistent).
5. `make deploy`.

## Adding a new action

1. Add effects to `ACTION_EFFECTS` in `src/core/pet.py`:
   ```python
   ACTION_EFFECTS[4] = {"h": +50}  # new "GIVE_DRINK" action
   ```
2. Add a button label to `BUTTON_LABELS` in `src/app.py`:
   ```python
   BUTTON_LABELS = ["F", "H", "P", "E", "D"]  # 5 actions now
   ```
3. Add the letter glyph to `GLYPHS` in `src/ui/widgets.py`:
   ```python
   "D": [(0,0),(0,1),...]
   ```
4. Update `BUTTON_X` spacing if 5 buttons don't fit (currently spaced 29 px apart,
   4 buttons span 8 + 3*29 + 24 = 119 px, fits 128 px width).
5. `make test && make deploy`.

## Adding a new screen

Currently there's only the home screen. To add a new screen (battle, evolution
animation, settings):

1. Create `src/ui/screens/<name>.py` with a class:
   ```python
   class BattleScreen:
       def __init__(self, display, group, pet):
           ...
       def update(self, buttons, now) -> "self | HomeScreen":
           ...
       def draw(self):
           ...
   ```
2. Add a state variable in `app.py`:
   ```python
   current_screen = HomeScreen(...)
   while True:
       next_screen = current_screen.update(...)
       if next_screen is not current_screen:
           current_screen = next_screen
           # rebuild displayio group
   ```
3. Persist the pet between screens.

## Why CircuitPython 10.2.1?

- **displayio** is mature, easy to use
- **adafruit_debouncer** handles button bounce well
- **adafruit_st7735r** is the canonical driver for ST7735S
- CP 10 added the `fourwire` module that decouples SPI from the display driver
  (CP 8 had `displayio.FourWire` baked in, which made the 4-wire display protocol
  a bit confusing)
- CP 10 .mpy files have `0x4306` magic, distinct from CP 8's `0x4305`

## Memory budget (Pico W = 264 KB RAM)

```
CircuitPython 10.2.1 runtime:  ~80 KB
displayio + framebuffer (128×128×2 bytes):  ~32 KB
adafruit_st7735r.mpy:          ~5 KB
adafruit_debouncer.mpy:        ~3 KB
adafruit_imageload/*.mpy:      ~10 KB
adafruit_ticks.mpy:            ~1 KB
Our code (flattened):          ~3 KB
Heap (free for Python objects): ~130 KB
```

Plenty of headroom. We can load 10+ sprites, complex UI trees, etc. without worry.

The constraint that DOES bite us is **flash** (2 MB total, ~491 KB free after
CircuitPython firmware). Each BMP eats a few KB. We're at ~50 KB used so far.

## Testing strategy

- **Unit tests on Mac** (pytest, 24 tests): cover the data model and game logic.
  The `tests/conftest.py` adds `src/` to `sys.path` so tests can `from core.pet
  import Pet` directly without a build step.
- **No on-device tests** (yet). The Pico is too slow to run pytest, and we'd need
  a way to inject mocks for `time.monotonic()`. Future: a CircuitPython test
  runner that uses mocks.
- **Manual smoke test**: `make deploy` then eyeball the Pico. Verify BG, sprite,
  bars, buttons all visible. Press buttons, verify response.

## References

- [CircuitPython displayio docs](https://docs.circuitpython.org/en/latest/shared-bindings/displayio/)
- [Adafruit ST7735R library](https://github.com/adafruit/Adafruit_CircuitPython_ST7735R)
- [Adafruit Debouncer library](https://github.com/adafruit/Adafruit_CircuitPython_Debouncer)
- [CircuitPython 10 release notes](https://github.com/adafruit/circuitpython/releases)
