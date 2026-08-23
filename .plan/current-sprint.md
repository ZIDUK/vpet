# Current sprint: M1 — Pet lifecycle

Started: 2026-08-23
Target: make the pet feel alive, not just a sprite that blinks.

## In progress
- [ ] Stats actually drive sprite mood (happy/sad/hurt/sick)
  - Decide: how many distinct moods? Start with 4 (happy/neutral/tired/sick)
  - Threshold logic: avg of stats > 80 = happy, < 30 = sick, etc.
  - Visual: change Agumon idle frame or swap to a different sprite sheet

## Backlog
- [ ] Evolution tree: 4 stages, 5-15 min each
  - rookie: 0-15 min, needs care
  - champion: 15-60 min, can battle
  - ultimate: 1-4 hours, walks on its own
  - mega: 4+ hours, fully autonomous
- [ ] Death by neglect: health < 20 for > 5 min = pet dies
- [ ] Persistence: save state.json on stats change, restore on boot

## Blocked / waiting
- ~~WiFi-feeding~~: deferred to M4 (T-Display died of overheating)

## Done this sprint
- 2026-08-23: v13.0 working on Pico-LCD-1.44 (commit 33ba7c7)
  - Agumon animated idle
  - Jungle background
  - 4 colored action squares with F/H/P/E letters
  - White selector ring
  - Auto-decay every 3s

## Next actions (in order)
1. Add mood system to pet state (compute_mood function)
2. Make sprite swap based on mood (use agumon_hurt.bmp when sick)
3. Add stats-driven evolution check on every tick
4. Add state.json persistence
5. Add death screen
