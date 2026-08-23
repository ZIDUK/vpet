# vPet — Roadmap

## Vision
A Digimon-style virtual pet on Raspberry Pi Pico W + Waveshare Pico-LCD-1.44 (ST7735S 128×128).
Two evolution lines (Agumon, Gabumon), 4 stages each, with stats, actions, sleep, and turn-based battles.
Tangible, not screen-based — like a real Digivice.

## Milestones

### M0 — Project structure ✅ DONE
- Repo reorganized: `src/`, `assets/`, `build/`, `scripts/`, `tests/`, `docs/`, `.plan/`
- Build pipeline: `src/*.py` → `build/code.py` (flattened for CircuitPython)
- Deploy pipeline: `build/` → `/Volumes/CIRCUITPY/`
- Test suite: 24/24 passing on Mac (pytest)
- Display working on Pico W (verified in v14 baseline)

### M1 — Core gameplay (in progress)
- [x] Pet stats model (h/e/p/hp)
- [x] Decay over time
- [x] Actions: Feed/Heal/Play/Rest (F/H/P/E buttons)
- [x] Display: bars + buttons + selector ring
- [x] Persistence: JSON save/load to /pet_save.json
- [ ] **Real Agumon sprite** (placeholder currently; need actual 64×64 BMPs)
- [ ] Mood/face expressions (idle, hungry, sad, sick, sleep)
- [ ] Sound? (Pico W has no audio out, skip for now)
- [ ] Sleep state (separate screen, time-based)

### M2 — Evolution (next)
- [x] Evolution rules: stat thresholds + age + battles
- [x] Agumon line: 4 JSON files (agumon → greymon → metalgreymon → wargreymon)
- [x] Gabumon line: 4 JSON files (gabumon → garurumon → weregarurumon → metalgarurumon)
- [x] Evolution stability check (30s above threshold)
- [ ] **Greymon, MetalGreymon, WarGreymon sprites** (need source art)
- [ ] **Gabumon, Garurumon, WereGarurumon, MetalGarurumon sprites** (need source art)
- [ ] Evolution animation (flash + transform sprite)

### M3 — Battles
- [x] Battle system (turn-based, random damage)
- [x] 5 NPC templates (goburimon, kunemon, betamon, gabumon, meramon)
- [ ] Battle UI (HP bars, attack/exchange)
- [ ] Battle menu (find / flee / item)
- [ ] XP → stat gain

### M4 — Polish (later)
- [ ] Multiple backgrounds (jungle, night, digivice)
- [ ] Day/night cycle (use Pico RTC)
- [ ] Settings via settings.toml (WIFI creds for OTA updates?)
- [ ] OTA updates (mDNS + http server on Pico W)
- [ ] Animation frames per state (walk, eat, sleep)

## Tech notes
- **Hardware**: Waveshare Pico-LCD-1.44 (ST7735S, 128×128, SPI on GP10/11, DC GP8, CS GP9, RST GP12, BL GP13)
- **Firmware**: CircuitPython 10.2.1
- **Display lib**: `adafruit_st7735r.mpy` v2.0.x (needs CP 10 `0x4306` mpy)
- **Pins**: BTN0=GP15, BTN1=GP17 (active LOW, internal pull-up)
- **Persistence**: `/pet_save.json` (JSON, rewritable)
- **Bundle**: adafruit-circuitpython-bundle-10.x-mpy-20251008

## Out of scope
- Sound (Pico W has no audio output; would need external DAC)
- WiFi features (kept simple; OTA is stretch goal for M4)
- Multi-language UI (Spanish UI strings only)
- Power management (USB-powered only; battery is a future hardware revision)
