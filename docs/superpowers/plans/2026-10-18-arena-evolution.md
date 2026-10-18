# Arena and Automatic Evolution Implementation Plan

Historical scope: the later approved
[technique expansion](2026-10-18-technique-expansion.md) supersedes this plan's
two-slot constraint and extends the snapshot format. This plan records the
earlier Arena outcome delivery, not restrictions on the newer work.

> **For agentic workers:** Execute inline with test-driven-development and verification-before-completion. Approval: user requests automatic evolution and Arena contribution on 2026-10-18.

**Goal:** Completed Arena wins/losses contribute to the existing automatic evolution requirements, exactly once and durably.

**Architecture:** Record completed Arena outcomes in the existing per-form battle counter and lifetime W/L counters. Reuse the full snapshot transaction for Arena saves; its current schema already includes counters, stock and technique progress. Evolution remains automatic after leaving Arena, never interrupts its result screen.

**Tech Stack:** Portable Python/C++, pygame simulator, ESP32 PlatformIO and existing NVS snapshot journal.

## Global Constraints

- Count victory/defeat only. No battle-count/WL progress for draw, retreat, opening Arena or interrupted fights; existing mastery/bond rules remain unchanged.
- Keep current thresholds: Champion age >=129600 seconds, >=15 battles in that form and lifetime wins/(wins+losses) >=60%.
- Preserve food, care, DP, injuries, EV, damage formulas, two equipped techniques and automatic evolution of all stages.
- No numeric enum changes, new NVS keys or journal format changes. Preserve old itemTx recovery.
- No retroactive awards for historical Arena sessions: their outcomes were not persisted.

## Task 1: Outcome Counting

Files: `scripts/practice_session.py`, `tests/test_practice.py`, `firmware/t-display/lib/vpet_core/src/vpet/PracticeSession.h`, `firmware/t-display/test/test_native/test_practice.cpp`.

- [x] Add failing tests for win/loss increment, unchanged care, terminal repeat and draw/retreat exclusion in Python/C++.
- [x] In the existing guarded award path, increment stage battles, and the matching W/L counter, saturating at current C++ storage limits. Do not invoke the legacy random battle action.
- [x] Test 14->15 wins unlocking Evolution.check, loss reducing win ratio, and age still blocking a premature evolution.

## Task 2: Durable Arena Results

Files: `firmware/t-display/src/App.cpp`, `tests/arena_evolution_app.cpp`, `tests/test_arena_evolution.py`, `tests/app_stubs/vpet/Panels.h`.

- [x] Drive actual App through Arena with a strong Champion fixture and read-only panel observation; assert counters survive load before exiting. The adapter does not mutate the session.
- [x] Replace the practice branch's partial itemTx commit with existing `settingsStore_.save(pet_,settings_)` so counters, rewards and mastery commit together.
- [x] Reject saveTx: restore counters/reward, retain terminal screen and offer retry. Pending sync blocks input until confirmed; reboot recovers the accepted snapshot once.
- [x] Exit Arena and tick App: assert automatic evolution saves the new species and resets only the existing per-form progress.

## Task 3: Simulator Automatic Evolution Persistence

Files: `scripts/sim_services.py`, `scripts/sim.py`, `tests/test_arena_evolution.py`.

- [x] Test save/load across 15th Arena result and automatic evolution, plus a rejected evolution save.
- [x] Add `SimulatorServices.evolve_and_save(pet,evolution)` using the existing atomic save; roll back the pet on rejection and return false so the animation waits for a successful save.
- [x] Call it from the existing idle evolution gate. No cloning on every frame when requirements fail.

## Task 4: Validation and Documentation

- [x] Run targeted tests, full `.venv-platformio/bin/python -m pytest -q`, native tests, T-Display build and headless Make Sim sequentially with asset generation.
- [x] Update architecture, project status and delivery roadmap: Arena now contributes to counters, current lifetime ratio, exact-once transaction and no retroactive progress.
- [x] Under existing deploy authorization, back up NVS, verify unchanged assets, upload fresh firmware and verify digests/VPET_READY. Physical evolution acceptance remains a user check.
- [x] Leave existing uncommitted work intact; do not commit or push the mixed tree without a fresh request.

## Validation Evidence

2026-10-18: 1120 Python tests passed (6564 existing Pillow warnings), 174
native tests passed. The new suite runs actual App.cpp in five modes:
normal, rejected commit/retry, pending commit/recovery, reboot while pending,
and insufficient age. It also drives pygame with NEXT/ACTION/QUIT through
a real Arena win, automatic evolution and saved species reload; no force
evolve key or user's save is used.

T-Display build: static RAM 56036/327680; flash 1007489/4194304.
`make sim SIM_ARGS='--max-frames 90'` passed headless. Backup before upload:
`out/board-backups/20261018-arena-evolution/08f9e0d00788-20261018-104802-critical.bin`.
Logs: `out/arena-evolution-board-deploy/`. Full snapshots need no schema,
enum or key migration. No damage, element, EV or equipped-slot changes.

## USB Deployment

2026-10-18: fresh firmware uploaded without rewriting LittleFS or erasing NVS.
`verify_flash` confirms firmware at 0x10000 and LittleFS at 0x410000 match
their local digests. Final 18-second boot observation: `ARENA_EVOLUTION_BOARD_OK`,
`VPET_READY`, heap free 66644/minimum 66576, filesystem 11292672/12451840,
manifest 1; BLE PAIRED/CONNECTED. No fatal, Guru Meditation, brownout or abort
observed. The optional missing swapTx key logs NOT_FOUND without blocking boot.

Firmware SHA-256:
`b3fcfa71eb75da18ef618b8fb7a6f91b6514fde5a0e393405c8a45b8a74c3b0b`.
Unchanged LittleFS SHA-256:
`e6bccba9af18786d60f8512b4f480dd991c5f943737d2be19704c64147742563`.
Physical acceptance of evolution after real Arena play remains pending;
the user's pet was not force-evolved or given test wins.
