# Plan: Recuperacion De Guardado Y Ciclo De Huevos

Spec: [SPEC-GAME-RECOVERY-001](../specs/2026-10-28-battle-recovery-egg-lifecycle.md).
Requirements: REQ-GAME-REC-001, REQ-GAME-REC-002, REQ-GAME-REC-003, REQ-GAME-REC-004.

- [x] Add a recoverable pending-save screen path that exposes Home without allowing mutations.
- [x] Add a confirmed, atomic discard operation for non-active unhatched eggs.
- [x] Pin existing breeding egg creation behavior with an end-to-end controller/storage test.
- [x] Register implemented and proposed requirements in `docs/requirements.json`.
- [x] Run native tests, targeted Python tests, SDD collection, and T-Display build.
- [ ] Leave device flash and physical acceptance for a separately authorized delivery.

No profile or DNA migration is included. Do not mark the genetic-sex requirement
implemented until an approved versioned inheritance design and migration exist.

## Evidence

- `PLATFORMIO_CORE_DIR=/private/tmp/vpet-pio-core .venv-platformio/bin/pio test -d firmware/t-display -e native`: 185/185 passed.
- Targeted Python integration: save-pending App, Collection controller/store, and breeding: 3 passed.
- Full Python suite excluding generated duplicate tree `out/compact-care/source-ce68348`: 2,084 passed.
- `scripts/spec_check.py --collect`: 38 tests collected; 3 specs and 16 requirements structurally valid.
- `PLATFORMIO_CORE_DIR=/private/tmp/vpet-pio-core .venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`: success; RAM 53,460 bytes, flash image 1,116,341 bytes.
- No device flash or physical acceptance performed.
