# Digital Monster vPet — Implementation Plan

## Vision

Transform the current Greymon-only virtual pet into a full **Digital Monster vPet** that mirrors the modern sprite sheet design (32×32 tile size, 168×132 display). The digimon hatches from a Digi-Egg, evolves through Rookie → Champion → Ultimate, and has a full menu system (FEED, TRAIN, BATTLE, BATH, HEALTH, SCAN, etc.) backed by a stat system (HP/EN/EXP/Level/Mood).

## Target display

- **Hardware**: Raspberry Pi Pico W, ST7735R 168×132 LCD
- **RAM budget**: 264 KB total, ~150–180 KB usable for user code + preloaded bitmaps
- **Flash budget**: 2 MB total, ~1.5 MB free (state + asset storage)
- **Sprite tile size**: 32×32 (4× more compact than current 64×78)

## Architecture overview

```
┌──────────────────────── Pico W (CircuitPython 8.2.9) ────────────────────────┐
│                                                                              │
│  dmonmain.py  ── entry point, asyncio loop                                  │
│      ├── state.py        ── digimon state, stats, evolution                  │
│      ├── persist.py     ── save/load to flash (state.json)                  │
│      ├── sprites.py     ── bitmap preload + lazy load helpers               │
│      ├── ui.py          ── view groups (main, menus, evolution)            │
│      ├── actions.py     ── move_*, menu handlers                            │
│      └── anim.py        ── animation primitives (cycle, blink, tween)       │
│                                                                              │
│  /Greymon/   /Agumon/   /MetalGreymon/   /Egg/   /icons/   /ui/   /bg/      │
│  (sprite bitmaps, all 8-bit BMP, palette idx 0 = transparent)               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data model

```python
# state.py
DIGIMON_STAGES = ("egg", "rookie", "champion", "ultimate")
STAGE_DISPLAY  = {"egg": "Digi-Egg", "rookie": "Agumon",
                  "champion": "Greymon", "ultimate": "MetalGreymon"}

# Stats: integer 0..max
hp      = 100 / 100    # health
en      = 50  / 100    # energy
exp     = 0   / 350    # experience to next level
level   = 1            # 1..99
mood    = "good"       # excellent / good / normal / bad / sad / sleepy
hunger  = 0            # 0..100, grows over time
clean   = 100          # 0..100, drops over time
strength= 10           # battle stat, grows with training
stage   = "egg"        # current evolution stage
age_days= 0            # lifetime
```

## Persistence

- **One file**: `/state.json` on CIRCUITPY flash (~1 KB)
- **Written on**: every menu action that changes state (feed, train, sleep, evolution, level up)
- **Read on**: boot
- **No write during animation** (would slow frame rate)

## Menu structure

| Top row | Bottom row |
|---|---|
| **FEED**     — give meat/pill, raises hunger | **ITEM**     — inventory (future) |
| **TRAIN**    — increases strength, costs EN  | **DIGIDEX**  — catalog of seen digimon |
| **BATTLE**   — PvE encounter, costs HP risk  | **DIGIVOLVE** — manual evolution attempt |
| **BATH**     — restores clean stat          | **MAP**      — location selector (future) |
| **HEALTH**   — HP/EN/EXP view + rest         | **STATUS**   — full stats screen |
| **SCAN**     — mood / sick check             | **OPTIONS**  — sound, brightness (future) |

Cycle with **button0** (next view), select with **button1**, back with **button2** (matches current hardware).

## Evolution criteria

- **egg → rookie**: age ≥ 1 day AND hunger > 0 (any interaction)
- **rookie → champion**: level ≥ 11 AND exp ≥ 100
- **champion → ultimate**: level ≥ 25 AND exp ≥ 250 AND strength ≥ 50

Evolution plays a cutscene (5 sec animation) then swaps the active sprite set.

## Phased plan

| Phase | Scope | Estimated time |
|---|---|---|
| **1. Assets** | Extract sprite sheets + UI icons from reference images, save as 8-bit BMP | now |
| 2. Core | State machine, stats, persistence, new main screen layout | next session |
| 3. Menus | Implement the 12 menu options, one per sub-screen | next session |
| 4. Evolution | Digi-egg → Rookie → Champion → Ultimate + cutscene | next session |
| 5. Polish | Mood decay, time-based stats, save indicator, transitions | later |
| 6. Digidex | Catalog of seen digimon, view from menu | later |
| 7. Battle | PvE encounters, basic AI, win/lose flow | later |

## File structure (target)

```
vPet/
├── code.py                 # entry: just imports vpet.main
├── lib/
│   ├── vpet/
│   │   ├── __init__.py
│   │   ├── main.py         # asyncio entry
│   │   ├── state.py        # DigimonState class
│   │   ├── persist.py      # load/save state.json
│   │   ├── sprites.py      # bitmap preloads
│   │   ├── anim.py         # animation primitives
│   │   ├── ui.py           # view construction
│   │   ├── actions.py      # menu handlers
│   │   └── views/
│   │       ├── main.py     # main screen (digimon + stats)
│   │       ├── feed.py
│   │       ├── train.py
│   │       └── ...
│   ├── adafruit_*          # existing libraries
│   └── dmonmain.py         # legacy entry (kept for compat until migration done)
├── Greymon/                # existing 64x64 sprites (legacy, will phase out)
├── Agumon/                 # NEW: 32x32 Rookie sprites
├── MetalGreymon/           # NEW: 32x32 Ultimate sprites
├── Egg/                    # NEW: 32x32 Digi-Egg sprites
├── icons/                  # 32x32 menu icons (FEED, TRAIN, etc)
├── ui/                     # status bars, mood icons, notifications
├── bg/                     # background scenes (jungle, city, sky)
├── state.json              # runtime state (gitignored)
└── PLAN.md                 # this file
```

## RAM math (32×32 sprites)

Each sprite frame: 32×32 = 1,024 pixels = 1 KB (8-bit indexed). 4 frames per action = 4 KB.
- Preload 4 stages × 4 actions × 4 KB = **64 KB** for all digimon anims
- Preload 12 menu icons × 4 states × 0.5 KB = **24 KB** for UI
- Preload 4 backgrounds × 160×128 / 2 = **~40 KB**
- Preload status bar + mood + notif = **~10 KB**
- **Total preloaded: ~140 KB** — tight but feasible, no lazy-load needed

If we hit OOM, fallback: lazy-load backgrounds only (each is 40 KB).

## Asset extraction strategy

Reference images (provided by user):
- `spritesheet_1536x1024.png` — full sprite sheet, 32×32 tile size
- `ui_1412x1114.png` — UI mockup with menu icons, bars, mood, notifications

Extraction steps:
1. **Detect grid** in the sprite sheet (rows by labeled animation, columns by frame index)
2. **Crop** each row × each frame → individual PNG strips
3. **Convert** to 8-bit indexed BMP with index 0 = transparent (matching project format)
4. **Organize** into `/Agumon/`, `/MetalGreymon/`, `/Egg/`, `/icons/`, `/ui/`, `/bg/`
5. **Sync** to CIRCUITPY (clear AppleDouble first, watch free space)

## Decision log

- 2026-07-27: Persistence = flash save (recommended, low cost, huge UX win)
- 2026-07-27: Sprite source = extract from user-provided reference images
- 2026-07-27: Approach = full plan + start Phase 1
- 2026-07-27: Tile size = 32×32 (per reference, 4× more compact than current 64×64)
