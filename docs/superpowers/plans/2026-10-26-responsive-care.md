# Responsive Backpack, Lights And Repeated Feeding

**Goal:** Remove synchronous persistence from item/light presentation and reduce
collection save I/O so the existing single-writer barrier is shorter.

**Architecture:** Reuse the bounded snapshot writer for Food, Item and Light.
The main loop owns UI/live state; the worker exclusively owns persistence until
completion. Keep one pending durable transaction, rollback rejected actions and
never queue repeated consumption without bounds or call an enqueued action saved.
No assets, Status, balance, schema, enum values, WiFi or Creator changes.

## Regression And Implementation

1. Add deferred App tests for immediate stock redraw and sleep/wake state before
   any storage write, ignored repeat ACTION, complete single consumption, reboot,
   executor rejection and storage rollback in Collection and legacy modes.
2. Add a real filesystem adapter operation-count regression for a two-pet save.
   Preserve CRC, stale-sequence rejection, previous-generation backup, explicit
   recovery and the single atomic rename visibility point.
3. Generalize the feeding job and its pure-RAM presentation to items and lights.
   Account care/sleep elapsed before inputs and after blocked writer intervals;
   no storage access through rendering while the worker owns persistence.
4. Reduce repeated file opens/seeks using bounded per-adapter read/write buffers
   and a read handle refreshed at every size probe and invalidated on commit.
   Retain final sync/readback/CRC and previous-generation copy before rename.
5. Run focused App/task/collection/learning tests, native core and an isolated
   T-Display build excluding concurrent Creator. Review failure, ownership and
   memory paths. Record exact results and any incomplete hardware validation.
6. Ask for approval for this new firmware before flashing. With approval, make a
   fresh board backup, firmware-only load and digest checks, then measure repeated
   food, item and light response plus writer stack/heap with user-operated inputs.

## Important Limits

The previous firmware shows the first Eat frame before writing but deliberately
blocks dependent ACTION/Back until the writer finishes. A thread does not remove
flash contention. Host operation counts are not milliseconds on ESP32. No claim
that repeated meals are responsive or the save ends during Eat without hardware
timing. Power loss before commit can lose the latest pending action.

## Evidence

- RED: deferred item regression found writes before worker submission (5.88 s).
  RED: two-pet filesystem save opened 56 streams and sought 81 times (2.38 s).
  Optimized adapter: 9 opens, 5 seeks. Bounded buffers total 1024 bytes, no
  whole-generation RAM cache. C update-stream transitions explicitly position.
- Deferred tests cover items/lights in Collection and legacy, repeat ACTION,
  single commit, rejection, executor failure, precommit reboot, full snapshot
  reload, accepted-but-unsettled adopted-item journals and no repeated effect.
  Three meals can start before their predecessors' Eat clips finish once each
  writer completes. Existing one-overfeed-per-cycle policy remains unchanged.
- A five-minute delayed light save catches up sleep recovery or awake decay
  according to the resulting state. The adapter regression also checks staged
  read -> write at the same cursor and refresh after external corruption.
- First isolated full suite: 1 failed, 2020 passed in 318.45 s (13278 existing
  warnings). The legacy sleep test attempted a retry before the new storage
  recovery barrier expired. Adapt it to wait for recovery, preserving rollback,
  sleep/reboot and completed-night reward assertions. This run is not green.
- Final focused care/sleep/collection/task/learning suite: 54 passed in 29.74 s.
  Native suite: 185 passed in 1.793 s. Independent read-only reviewer found no
  actionable issue in ownership, rollback, sleep clock or buffered I/O.
- Final isolated T-Display build passed in 7.670 s: static RAM 53284 bytes,
  app 1106513 bytes; buffers add 1040 bytes to static usage including metadata.
  Firmware SHA-256: 804d3c8c420c4832e92bf12940c12033e120341cd154ec5a6d85078a5f9c2fd4.
  Bin/ELF retained in out/responsive-care; ten changed source/test files match
  the isolated tree and main.cpp matches committed code, excluding Creator.
- Final isolated full rerun: 2021 passed in 305.91 s, 13278 existing warnings.
  JUnit evidence: out/responsive-care/test-results.xml. No firmware from
  this correction has been flashed, and no board input/save/reward was performed
  by the agent. Runtime save latency, repeated response, heap/stack and BLE remain
  unverified for this correction.
