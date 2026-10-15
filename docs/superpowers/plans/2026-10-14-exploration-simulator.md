# Exploration Simulator Implementation Plan

**Goal:** Complete the approved Patio/Jornada/Noche loop in Make Sim.

**Architecture:** Portable exploration state and deterministic rewards belong in
`src/core/exploration.py`; `scripts/exploration_session.py` owns navigation and
atomic save transactions. The renderer reads this state. Pet saves retain a
versioned exploration record. Hardware integration follows simulator acceptance.

**Tech Stack:** Python, Pillow, pygame, pytest; existing atomic JSON save service.

## Constraints

- Patio 1800 seconds; Jornada/Noche 28800 seconds, real elapsed wall time.
- No energy cost. Rookie and later stages; one trip at a time.
- Jornada +2 EV, half at 4 hours, maximum 8 per Monday-based week.
- Noche +2 mastery, half at 4 hours, maximum 4 per week; two complete
  learning nights unlock Flame. Patio only recovers energy (+25/+10).
- Guarded atomic start/claim; no reward until the whole pet save succeeds.
- Guide capacity one; +1 EV in the next completed attribute session.
- Existing numeric inventory IDs, firmware enums and NVS remain compatible.

## Execution

- [x] Add versioned exploration record, care snapshot, calendar week tracking,
  reward preview and transactional claim. Test boundary clocks, caps and retry.
- [x] Persist the record with Pet; restore on ordinary simulator startup and use
  a real-time clock for travel. Freeze care while absent and gate home actions.
- [x] Add departure confirmation, live journey, recall confirmation and receipt;
  retain choices, localize ES/EN and scroll all six Jornada stats.
- [x] Integrate the Guide as an extra inventory entry without renumbering legacy
  entries; consume it atomically with successful attribute training.
- [x] Render routes, progress, return and receipt on 240x135; inspect screenshots
  and exercise real pygame event navigation with a controlled clock.
- [x] Run the Python suite, build simulator assets, run Make Sim and document
  implemented rules, assumptions and the separate hardware work.

## Explicit Runtime Decisions

Good care at departure means hunger, energy and mood all >=50 and no injury.
This threshold was unspecified in the design and is now a documented balance
parameter. Poor care changes Patio recovery and Guide eligibility; the defined
EV/technique rewards keep their approved quantities. An early return floors
energy proportionally; permanent rewards use the approved four/eight-hour steps.
A Guide requires a complete, well-cared-for Jornada. Noche targets Flame:
learning if locked at departure, mastery otherwise. Caps are charged in the
claim week; rolling the clock backward cannot reset spent weekly allowance.
There is no general bag capacity in the existing inventory; the one-Guide cap
applies and another Guide is not queued when one is already owned.

## Verification

Final complete Python suite: 634 passed. Final exploration regressions: 69
passed after UI polish. Make Sim ran on the actual macOS display for 80 frames
and exited successfully. Preview gallery: `out/exploration-previews/gallery.png`.
The new feature uses simulator JSON persistence; hardware/NVS integration and
physical acceptance remain a separate delivery. No board flashing performed.
