# Responsive Feeding Implementation Plan

**Goal:** Start Eat before storage and persist accepted food with one bounded
background job, preserving the existing save format and nutrition rules.

**Approved design:** User approved immediate presentation plus a single writer,
an immutable snapshot and explicit durable completion. Scope is feeding only;
other gameplay transactions remain synchronous. A queued action is not durable.

## Constraints And Ownership

- App alone owns the live pet, navigation and TFT. Worker owns its copied meal
  snapshot and storage access until completion; App cannot read Collection or
  NVS in that interval. One pending meal blocks dependent ACTION/Back, not
  animation or Home NEXT. No unbounded queue, new assets, schema or enum values.
- Poll a completion barrier before accessing worker-owned storage metadata.
  Failed commits restore the pre-meal pet and enter the existing storage-error
  path. Queue/allocation failures must not silently fall back to blocking saves.
- Power loss before commit can lose the pending meal. Atomic old/new generation
  recovery remains the persistence contract; never replay food as a reward.
- Use one task on ESP32; deterministic injected deferred execution in host tests.
  Keep its FreeRTOS dependencies outside portable core. First Home draw precedes
  task submission. Flash contention can still stall reads and must be measured
  on hardware; do not promise zero stalls or cache all 25 frames in limited RAM.

## Execution

1. Add failing App tests: immediate frame before commit, several frames while
   queued, repeated input, success/failure/start failure, legacy and Collection,
   uint32 rollover, restart before commit and no duplicate effect after commit.
2. Add bounded task interface and ESP32 adapter, then integrate feeding with
   immutable request, first draw, completion/rollback and clock accounting.
3. Merge pending collection time into saveActive's single atomic generation;
   test cooldown/incubation and failed writes without losing pending time.
4. Add task-adapter concurrency tests with a host FreeRTOS shim. Measure and
   log queue/commit timing and stack/heap on ESP32; do not modify Status.
5. Run focused App/persistence/Collection/UI tests, native core and isolated
   firmware build, excluding concurrent Hub/Creator. Review ownership and
   failure paths, update architecture/status and record exact test evidence.
6. Ask for this revision's flash approval after verification; preserve current
   saves/assets with a fresh backup. Hardware response/animation/BLE checks
   remain separate from local passing tests.

## Regression Evidence And Review

- RED: first-frame-before-write assertion failed on the previous implementation
  (5.72 s). RED: combined save produced two commits instead of one (5.00 s).
- Deferred App jobs cover Collection and legacy, MEAT/PROTEIN, repeat input,
  rejection, late completion, restart before/after commit and uint32 rollover.
  The real FreeRTOS adapter runs with a multithreaded notification shim: bounded
  submission, publication barrier, creation failure, 30 reuses and destruction
  during work. This is not a hardware scheduler or flash-latency certification.
- Independent read-only review found care-boundary ordering, elapsed recovery,
  legacy full-checkpoint and retry-clock gaps. Added 30-second nutrition RED,
  retry-rate RED and explicit reload tests for evolution/missed care; preserved
  elapsed time through failed recovery and use full legacy saveTx snapshots.
- Accepted-but-unsettled journal tests inject sync, partial replay and journal
  clear failures. No second nutrition delta; failed attempts preserve the
  previous state and recovery catches up powered-on care rather than erasing it.
- An initial isolated full-suite run lacked generated build-tdisplay/runtime
  resources and a local environment link: 241 failed, 1763 passed, 16 errors
  (295.90 s). This is not a passing suite. Regenerate both display profiles and
  LittleFS data in the scratch tree and rerun before recording final results.
- The corrected isolated environment passed 2020 tests in 292.43 s (13278
  existing dependency/render warnings). Subsequently added explicit Eat
  cancellation on executor/commit rejection: wake() only exits Sleep. The
  final focused rerun and firmware build cover this last error-path adjustment;
  the full-suite count above predates it, not a second final full-suite run.
- Final read-only review accepted the clock/full-checkpoint fixes. No hardware
  action has been performed for this revision. Current physical acceptance of
  Eat belongs to firmware 81cee4b, not the new background writer.
- Final cancellation regression was checked against an isolated pre-fix
  wake() variant with the correct Home redraw: RED in 24.38 s. Restore the
  approved cancelAction implementation after this diagnostic; never flash
  the temporary variant. Final focused suite: 104 passed in 58.78 s.
- Final isolated build: 19.628 s, static RAM 52244 bytes, app 1106637 bytes.
  Bin/ELF and full-suite log preserved in out/responsive-feeding/; SHA-256
  b7a877acf5fafb6fbb4803b7563904c70619d85b989a022a7874857cba8393d0.
  Code restored after RED matches that compiled binary. Hardware load approval
  requested separately; latency, full Eat presentation, BLE and runtime
  heap/stack margin remain unverified for the new task.
- Final native suite: 185 passed in 0.933 s. Architecture and current project
  status reflect that this revision is prepared, not deployed.

## Approved Firmware-Only Deployment: 2026-10-26

- User explicitly approved loading and validating the background-save firmware,
  preserving saves, Collection and graphics. Code revision: 0752e79; Creator
  main.cpp changes remain outside the isolated build and this deployment.
- Fresh isolated PlatformIO build passed in 3.218 s. Ten relevant sources,
  including committed main.cpp, match HEAD. The rebuilt binary matches the
  approved SHA-256 above. Two focused App/task tests passed in 6.34 s.
- Fresh board backup: out/board-backups/responsive-feeding-20261026-183627/.
  Verified full current LittleFS, NVS/partition area and previous application
  before writing. Previous application SHA-256 matches firmware 81cee4b.
- Only 1113216 application bytes at 0x10000 were replaced. App digest verified;
  LittleFS, NVS, bootloader and partition digests unchanged before restart.
- Startup VPET_READY: free heap 82520, minimum 72936, flash 16777216,
  filesystem 11829248/12451840, manifest 1. This precedes lazy writer creation;
  it does not validate worker stack or heap margin during a real save.
- Manual MEAT/PROTEIN presentation, runtime writer telemetry, full animation
  and BLE remain pending. No feeding, pet switching or rewards were performed
  by the agent. No physical acceptance is inferred from successful flashing.

## User Visual Acceptance

- Asked to test FEED -> MEAT once, awake, pause OFF and satiety below 100,
  and confirm immediate eating with the complete animation without pauses.
  User replied "ahora si". Record qualitative visual acceptance for MEAT;
  this does not certify PROTEIN, numeric latency or memory under save load.
- Capture out/responsive-feeding/feeding-capture-20261026-184635.json closed
  after 180.061 s, before the response arrived: zero feeding inputs/results,
  zero presentation/save metrics, zero commands sent and no fatal lines.
  Do not infer writer stack/heap margin from idle runtime or startup figures.
  No extra meal or restart requested merely to obtain telemetry.
