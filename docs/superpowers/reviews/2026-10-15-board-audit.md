# T-Display Firmware Audit

Date: 2026-10-15. Read-only review of the current working tree, not a released
commit. Scope: active firmware/t-display. No flash, physical timing or radio
measurement. Agent findings were checked against source and a host harness.

## Findings

The numbered findings below record the original audit. Corrections are now
implemented in the working tree; verification and limitations are tracked in
[audit correction plan](../plans/2026-10-15-board-audit-fixes.md). In particular,
commit ambiguity has an explicit Pending state, rather than a false rejection.

1. **P1: interrupted backup swap loses the parked pet.**
   `lib/vpet_core/src/vpet/SettingsStore.cpp`, `swapBackup`: backup is overwritten
   before the restored pet is saved as active. A cut between writes leaves both
   slots with the previously active pet. Reproduced with Rookie active and
   Champion parked. Use a durable swap journal or staged snapshots.
2. **P1: ordinary saves can load mixed snapshots.**
   `SettingsStore.cpp`, `save`: independent key writes update schema/species
   before the rest of the snapshot. A cut can load Champion with old hunger.
   General save is not protected by the food/item journals. Several App callers
   ignore failures. Use versioned snapshot slots with a final commit marker
   and propagate errors to callers.
3. **P2: empty journal clearing reports failure on the real NVS adapter.**
   `src/NvsKeyValueStore.cpp`, `putString`: tests `Preferences::putString > 0`.
   The installed Preferences implementation returns strlen(value) after a
   successful commit: an empty value returns zero. Journal recovery therefore
   reports Unsupported after successfully clearing, then Loaded on retry.
   Reproduced with adapter-equivalent host semantics, not physical NVS.
   Implement explicit empty-value semantics and test the platform adapter.
4. **Withdrawn: care-time pause during Training/Arena.**
   This is intentional: architecture.md states that sessions pause care ticks.
   No corrective action is requested. Original numbering retained for traceability.
5. **P2: reboot resets the injury deadline.**
   `PetState.cpp`, `tick`, and `SettingsStore.cpp`: injuredMs_ is not persisted,
   although injury flag/count/death are. Saving at 5:59:59, loading, and ticking
   one second lets the restored pet survive the uninterrupted pet's deadline.
   Persist accumulated injury duration with a compatible optional field.
6. **P2: BLE cross-task state has no C++ synchronization.**
   `include/vpet/BleService.h` and `src/BleService.cpp`: volatile status fields
   and an ordinary initialized flag cross callback/application task boundaries.
   Volatile does not synchronize threads. Use atomics or queue events to the
   owning task. Source-derived risk; failure frequency has not been measured.
7. **P2: VPET_READY precedes application initialization.**
   `src/main.cpp` emits readiness before app.begin, storage recovery and restored
   BLE settings. Deployment can accept readiness prematurely and heap telemetry
   excludes subsequent BLE startup. Report application-ready after successful
   initialization and distinguish recovery failures explicitly.

These findings were not fixed by the visual change. The subsequent correction
adds snapshot/swap recovery, injury continuity, platform write confirmation,
atomic BLE callback state and post-init readiness. Physical power-loss, NVS
wear/GC and radio stress verification remain pending; host tests cannot certify
physical robustness or performance.

## Reproduction

Harness preserved at `/private/tmp/vpet-audit-readonly-check.cpp`. It compiles
against the actual core sources with c++17 and simulates interrupted key writes.
It does not emulate flash wear, radio timing, or physical power loss.

That original harness is local historical evidence. Portable corrected
regressions now live in `tests/persistence_atomic.cpp`, `tests/app_persistence.cpp`
and `tests/platform_adapters/host.cpp`; run their pytest wrappers from any
checkout. See the correction plan for verified results and remaining limits.

```sh
c++ -std=c++17 -Ifirmware/t-display/lib/vpet_core/src \
  /private/tmp/vpet-audit-readonly-check.cpp \
  firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp \
  firmware/t-display/lib/vpet_core/src/vpet/Nutrition.cpp \
  firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.cpp \
  firmware/t-display/lib/vpet_core/src/vpet/PracticeBattle.cpp \
  -o /private/tmp/vpet-audit-readonly-check
/private/tmp/vpet-audit-readonly-check
```

Observed output with successful assertions:

```text
EMPTY_CLEAR: first load Unsupported, second Loaded despite successful journal deletion
SWAP_CUT: live and backup both Rookie; original Champion lost
SAVE_CUT: load accepts Champion species mixed with old hunger=20
INJURY_REBOOT: reloaded pet survives original six-hour deadline
```

## Optimization Evidence

Positive source checks: framebuffer allocation is checked; input sampling has
its own task and bounded queue; item/food journals replay absolute values; BLE
callback ownership is retained with setCallbacks(callbacks_, false).

Two screen buffers account for 129,600 pixel bytes. A Home redraw copies 64,800
bytes and pushes a full screen. These are calculated costs, not measured
bottlenecks. Successful compilation and unit tests do not prove responsiveness.

Measure p50/p95/max loop, render, asset-read, input-dispatch and NVS durations
with esp_timer_get_time, aggregating outside hot paths. Record free/minimum
heap, largest block, stack high-water marks and input queue overflow after
startup and repeated BLE/menu/battle cycles. Exercise connect/disconnect/off
under rendering load. Do not claim the board is optimized until these exist.

Add interruption-at-every-write tests for save/swap, adapter empty strings,
injury save/reload continuity, and BLE lifecycle stress tests.
