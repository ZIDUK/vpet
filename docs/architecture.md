# vPet Architecture

## Layered design

```
┌─────────────────────────────────────────┐
│  src/app.py        (entrypoint)         │  ← game loop, state machine
├─────────────────────────────────────────┤
│  src/ui/           (display)            │  ← screen layout, widgets, sprites
├─────────────────────────────────────────┤
│  src/core/         (game logic)         │  ← pet, evolution, battle, save
├─────────────────────────────────────────┤
│  src/hal.py        (hardware)           │  ← display + button drivers
├─────────────────────────────────────────┤
│  CircuitPython + adafruit libs          │
└─────────────────────────────────────────┘
```

The build script flattens all of `src/` into a single `build/code.py` because
CircuitPython doesn't support multi-file user modules from the root FS.

## Data flow (M1 baseline)

```
Buttons → app.py
  ├── next_btn fell → menu_idx = (idx + 1) % 4
  └── action_btn fell → pet.apply_action(menu_idx)

Each iteration:
  ├── pet.decay_if_due() → reduce stats every 3s
  ├── sprite frame advance (every 0.12s)
  └── save_pet(pet) every 30s
```

## Evolution flow (M2)

```
Loop:
  pet.update(...)
    └── if age > threshold AND stats > min AND battles_won > req:
          pet.species = evolves_to
          swap sprite on display
          add +10 to all stats (evolution boost)
```

## Battle flow (M3)

```
User selects "Fight" → pick NPC from data/npcs/wild.json
  → Battle(pet, npc) initialized
  → loop: pet_attack, npc_attack until one HP=0
  → commit_to_pet() (writes HP back to pet.stats)
  → if won: pet.battles_won += 1
  → if lost: pet.stats["p"] -= 20
```

## Module map

| File | Purpose | RAM cost on Pico |
|------|---------|-----------------|
| `hal.py` | displayio, FourWire, Debouncer init | low (delegated) |
| `core/pet.py` | stats dict, decay, apply_action | ~200 bytes |
| `core/evolution.py` | Evolution class with registry | ~500 bytes |
| `core/battle.py` | turn-based combat | ~400 bytes |
| `core/save.py` | JSON write/read to /pet_save.json | ~150 bytes |
| `ui/sprites.py` | BMP + TileGrid helpers | low |
| `ui/widgets.py` | bars, buttons, ring | ~300 bytes |
| `app.py` | main loop, state, draw | ~600 bytes |

Total estimated RAM: ~3KB (excluding displayio and framebuffer).
Pico W has 264KB RAM total. Plenty of headroom for future features.

## Adding a new Digimon

1. Create `src/data/digimon/<name>.json` with:
   - `name`, `line`, `stage`, `sprite` (path to BMP)
   - `evolves_to` (or null)
   - `requirements` (stat thresholds)
   - `battles_required`, `min_age_seconds`
2. Add `<name>_idle.bmp` (and any state BMPs) to `build/`
3. Update the registry in `app.py` to include the new form
4. `make deploy` to push to Pico
5. `make test` to verify the JSON is valid

## Adding a new action

1. Add the action's effects to `ACTION_EFFECTS` in `core/pet.py`
2. Add a button label to `BUTTON_LABELS` in `app.py`
3. Add the corresponding letter glyph to `GLYPHS` in `ui/widgets.py`
4. Update `BUTTON_COLORS` if you want a custom color
5. `make test` + `make deploy`

## Adding a new screen state

Currently the app has only the "home" screen. To add a new screen (e.g. menu,
battle, evolution animation):

1. Create a `screens/` subdir under `src/ui/`
2. Each screen exports a class with `enter()`, `update(buttons)`, `draw(group)`, `exit()`
3. Add a state variable in `app.py` and a state machine dispatcher
