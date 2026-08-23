# Current Sprint — Repo reorg + Refactor

## Done in this sprint
- **Repo reorganized** from flat mess (30+ dirs) to clean structure:
  - `src/` — modular Python (hal, core, ui, app)
  - `assets/` — raw source art + processed atlases (NOT deployed)
  - `build/` — generated `code.py` + BMPs (the ONLY thing deployed)
  - `scripts/` — `build.py` (flatten src → build) and `deploy.py` (build → Pico)
  - `tests/` — pytest suite, 24/24 passing
  - `docs/` — hardware notes + this sprint plan
  - `.plan/` — roadmap, sprint, ideas
- **Refactored v14.0** monolithic code.py into 8 modules:
  - `hal.py` — display + button init
  - `core/pet.py` — stats, decay, save
  - `core/evolution.py` — rules
  - `core/battle.py` — turn-based combat
  - `core/save.py` — JSON persistence
  - `ui/sprites.py` — BMP loading
  - `ui/widgets.py` — bars/buttons/ring
  - `app.py` — entrypoint / main loop
- **Build pipeline** working: `python3 scripts/build.py` → `build/code.py` (13KB)
- **Deploy pipeline** working: `python3 scripts/deploy.py` → `/Volumes/CIRCUITPY/`
- **Verified on Pico**: refactored code runs cleanly, jungle BG + sprite + bars + buttons visible.

## What's still rough
- `build/code.py` has `# (import flattened)` noise lines (cosmetic; doesn't affect runtime)
- The placeholder sprite is colored squares, NOT real Agumon
- Greymon, MetalGreymon, WarGreymon, Gabumon, etc. sprites not yet sourced/generated
- Battle UI not yet on screen (logic is ready, no menu)
- Evolution animation not yet built

## Next sprint — M1.5 (Agumon real sprite + mood faces)
- Generate real Agumon idle animation (5+ frames, 64×64 each, 320×64 total)
- Generate Agumon state faces: idle, hungry, sick, sleep
- Wire sprite swap based on pet state in `app.py`
- Test in pygame simulator (so we can iterate without rebooting Pico)
