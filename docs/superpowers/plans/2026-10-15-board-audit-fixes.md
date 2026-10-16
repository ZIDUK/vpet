# Board Audit Corrections

Scope: correct the six open audit findings; keep care-time pause intentional.
Preserve schema 3, enum values, legacy keys and saves. No flash.

1. Add versioned absolute snapshot journal for ordinary save and a coordinated
   two-slot journal for park/swap. Commit durable intent before mutating keys,
   replay idempotently before loading, reject malformed/future journals.
   A false return means rejection. An accepted intent may still need explicit
   sync confirmation before replay or UI acknowledgement. Ambiguous NVS commit
   failures must never trigger effect rollback followed by surprise replay.
2. Persist accumulated injury time as an optional, capped millisecond key.
3. Correct platform empty-string write semantics; test the real adapter with
   host stubs matching Preferences success/failure behavior.
4. Synchronize BLE callback state without changing profile/ownership behavior.
5. Propagate ordinary save failures and report ready only after App init.
6. Run interruption-at-every-write, repeated recovery/failure, old schema,
   malformed journal, injury continuity, BLE and application regressions.
   Run full pytest, native tests, firmware, asset and LittleFS builds; review
   and inspect generated visuals. Update audit/architecture/roadmap.
7. Review staged content for secrets/unrelated generated output; commit and
   push the completed accumulated project work. Report exact commit and remote.

Physical power-loss and BLE stress timing remain unverified without deploying.

Implementation: saveTx, swapLive/swapBack/swapTx v1; all recovery is gated by
sync. Strict decoding, END footer, unchanged-key replay, optional injuredMs,
minute checkpoints, App retry/freeze and post-initialization readiness.
Care time does not advance during Training/Arena or failed-save retry.

Tests include repeated power cuts during recovery itself, a first save,
full-stock payload size, malformed/truncated/future records, actual App.cpp
against display stubs, and actual platform adapters against a durable/cache
NVS model. ASan/UBSan validate the portable persistence harness; TSan validates
the simulated callback lifecycle. These are not physical-board measurements.

## Verification

- Full Python suite: 769 passed. Native PlatformIO suite: 172 passed.
- Focused persistence/App/platform suite: 43 passed, including 36 real-adapter
  host cases for Pending, mirror/clear failure, reboot, both swap namespaces
  and BLE lifecycle. Reviewer reported no material blockers.
- Portable harness under ASan/UBSan: 199 interruption/recovery scenarios,
  including successful completion controls. Full-stock snapshot: 1108 bytes.
- Callback stress under TSan: completed without reports.
- Firmware, regenerated assets and LittleFS compile successfully. Assets:
  162 files, 7,162,780 bytes. Smoke run: actual SDL simulator, 180 frames,
  headless, isolated save root in /private/tmp; normal player save untouched.
- Existing Pillow/pytest deprecation and no-touchscreen TFT warnings remain.
- No flash. Physical power cuts, NVS garbage collection/wear, phone BLE stress
  and real input/render latency measurements are still required before
  certifying production performance. Arena's full pixel parity remains a
  separate roadmap item; this audit does not close it.
