# Repeated Feeding Implementation Plan

> **For agentic workers:** Use executing-plans to implement this plan task-by-task.

**Goal:** Implement SPEC-GAME-FOOD-001, approved by the user on 2026-10-29.

**Architecture:** Keep the existing portable nutrition functions and asynchronous
progress writer. Only replace cycle gates with effect-availability checks.

**Tech Stack:** Python, portable C++, Arduino/PlatformIO, pytest and Unity.

## Global Constraints

Trace: REQ-GAME-FOOD-001 / AC-GAME-FOOD-001 (Task 1),
REQ-GAME-FOOD-002 / AC-GAME-FOOD-002 (Task 1),
REQ-GAME-FOOD-003 / AC-GAME-FOOD-003 (Tasks 1 and 2).

- Meat restores 20 hunger and adds 1 weight; protein restores 20 energy and adds 2 weight.
- Stat cap 100, weight cap 99; reject only when neither effect can change state.
- No EV/DP/effort, schema/enum changes, Status edits or Hub changes.
- Retain egg/dead/asleep/cold/busy restrictions and durable rollback.

## Task 1: Portable Rules And Callers

Files: src/core/nutrition.py, src/core/pet.py,
firmware/t-display/lib/vpet_core/src/vpet/Nutrition.cpp and PetState.cpp;
tests/test_nutrition.py, tests/test_balance_sim.py,
firmware/t-display/test/test_native/test_pet_state.cpp, tests/collection_app.cpp.

Interfaces: preserve applyFood(PetState&, FoodId), food_preview and apply_food.

- [x] Add red tests: six proteins from energy 0/weight 10 end at 100/22;
  three meats at hunger 100/weight 10 end at 100/13. Persisted cycle flags
  cannot block either. At weight 99, restore a deficient stat, then reject
  without changing counters or EV. Preview must not mutate state.
- [x] Run `.venv-platformio/bin/python -m pytest -q tests/test_nutrition.py`
  and native tests with PLATFORMIO_CORE_DIR=/private/tmp/vpet-platformio-core;
  record behavioral failures before implementation.
- [x] Replace meat guard with `hunger >= 100 && weight >= 99`, protein guard
  with `energy >= 100 && weight >= 99`. Keep capped deltas and counters.
  Match canFeed/can_feed and replace obsolete test expectations.
- [x] Exercise actual App food transactions through
  tests/progress_app_coordinator.cpp and tests/test_progress_app_coordinator.py:
  repeated portions, queued input once, storage rejection rollback and reload.

## Task 2: Availability, Catalog And Delivery

Files: firmware/t-display/src/Panels.cpp, scripts/sim_renderer.py,
src/core/item_catalog.py, scripts/export_item_catalog.py,
docs/items-and-rewards.md, docs/architecture.md, docs/requirements.json.

- [x] Feeding availability reflects stat/weight caps, not old cycle flags.
  Keep the existing unlimited-food UI and use FULL only when no effect exists.
- [x] Replace obsolete catalog limits with hunger_or_weight_below_cap and
  energy_or_weight_below_cap; run
  `.venv-platformio/bin/python scripts/export_item_catalog.py`.
- [x] Run focused nutrition/controller tests, full `pytest -q tests`,
  `make spec-check`, native tests and fresh `pio run -e tdisplay`.
- [x] Review the scoped diff and write a verification report separating local
  results, user-reported training success and unverified physical feeding.
- [ ] Back up critical board data, flash firmware only under standing user
  authorization, commit exact owned paths and push. Do not include Hub edits.

## Execution Evidence

Pending execution; results will be recorded in the verification report.
