# Adopted Consumables Implementation Plan

Goal: replace the research-only list with a filtered, board-oriented catalog,
without SQLite, evolution items or fictional map mechanics.

1. Add a deterministic catalog with stable string IDs, explicit units and
   contexts. Retain existing persisted IDs as compatibility data; do not
   renumber NVS or silently reinterpret old stock.
2. Test recovery at 20/50/90/100 percent of combat maximum, rounded down with
   minimum one, clamped at maximum. Do not revive defeated fighters.
3. Implement portable recovery and non-stacking battle boosts in Python/C++.
   Keep battle changes local to the fighter, never permanent pet attributes.
4. Generate JSON, C++ definitions, official documentation and transparent
   sprites from the catalog. Exclude unsupported objects explicitly.
5. Validate generated artifacts and Python/C++ arithmetic parity. Document
   separately the remaining inventory UI, acquisition and NVS integration;
   metadata availability must never imply an executable board feature.

No flash, no SQLite, no changes to existing NVS enum values.

## Verification 2026-10-15

- Full Python suite: 653 passed (6346 existing Pillow/pytest warnings).
- Native suite: 162 passed, including capped permanent consumable use.
- Python/C++ recovery and temporary boost trace: passed.
- Firmware compilation and LittleFS image: success; not flashed.
- Assets: 162 files, 7162184 bytes; new 40 sprites add approximately 11 KB.
- Battle remains below its existing 256-byte static budget; the additional
  per-fighter boost state uses 12 bytes, not integer arrays.
- Scope remaining: distribution, extended inventory persistence, board/sim
  UI selection and Manual/Guide transaction integration. These are not
  completed by the catalog or effect functions.
