# Evolution Progress Implementation Plan

> For agentic workers: implement inline, test-first, with verification before completion.

**Goal:** replace confusing Evolution Detail with the approved, paginated next-evolution progress sheet in simulator and firmware.
**Approval:** user accepts the earlier redesign on 2026-10-23; no evolution-rule, save-schema, package or breeding changes.
**Architecture:** read-only progress adapters consume current EvolutionRule/config; a dedicated renderer owns only Evolution Detail. Preserve the tree and four Status pages. NEXT pages requirements, ACTION/BACK returns to the selected tree node.
**Stack:** existing C++/PlatformIO, Pillow, VPA and bitmap fonts already generated for Training.

## Constraints

- Read next-stage conditions from the current form, not conditions to reach it.
- Four rows per page, full current name, larger portrait, dark background,
  white text and distinct completed/pending markers; targets not color-only.
- Show time remaining in minutes/hours, actual/target for other requirements,
  upper bound for care mistakes and range for weight. No raw seconds/CM/WR.
- Past, unknown, egg and final forms get explicit non-progress states.
- Scale affects time display exactly as supplied: board 1, running simulator 600.
- No changes to conditions, rewards, DNA, EV, NVS/enums, Home, Arena or Status.
- No generated assets edited manually; reuse assets/fonts. No board deployment
  implied by approval of implementation; physical acceptance stays open.

## Task 1: Read-only progress and navigation

Files: `src/core/evolution_progress.py`,
`firmware/t-display/lib/vpet_core/src/vpet/EvolutionProgress.h`,
`Navigation.h`, `App.cpp`, `scripts/sim.py`, `tests/test_evolution_progress.py`.

- [x] Write tests before implementation: Rookie has 6 requirements including
  24 h and weight 8..14, not Baby's 12h10/care-mistake condition; Champion
  uses 15 battles plus lifetime ratio 60%; distinguish unknown/past/final/egg.
- [x] Run `.venv-platformio/bin/python -m pytest -q tests/test_evolution_progress.py`
  and observe missing-function failure, then implement the read-only model.
- [x] Test all thresholds, 0/0 battles, time scale, page wrap and no mutations.
- [x] Maintain selected stage separately from transient detail page; reset
  page on entry, and restore tree selection on ACTION/BACK.

## Task 2: Render the approved sheet

Files: `firmware/t-display/include/vpet/EvolutionUi.h`, `Panels.cpp`,
`scripts/evolution_renderer.py`, `scripts/sim_renderer.py`,
`tests/evolution_progress.cpp`, `tests/test_evolution_progress_pixels.py`.

- [x] First pin expected body/background and page differences in failing tests.
- [x] Replace only Evolution Detail, keep upper menu and tree unchanged.
- [x] Reuse existing idle/portrait assets and font9/font10. Draw four rows
  with labels, values, progress and check/pending markers within 240x135.
- [x] Render real Panels.cpp/AssetStore.cpp with production EvolutionUi and
  compare against simulator pixels below the existing navigation bar.
- [x] Produce ES/EN gallery for Baby, Rookie pages, Champion, final, past,
  unknown, egg and met/unmet conditions; inspect images at native scale.

## Task 3: Regressions and documentation

- [x] Run focused progress, evolution, navigation, App, renderer and menu tests.
- [x] Run complete Python suite, native core tests and T-Display compilation.
- [x] Update architecture, guide, roadmap, current status and video checklist:
  implemented/tested locally is not flashed/accepted physically.
- [x] Keep earlier unrelated documentation edits; no blanket staging/reverts.
- [x] Report actual results, preview path, and any unverified hardware behavior.

## Verification: 2026-10-23

- Red: 19 progress tests failed before the new module existed; pixel test
  failed against the old panel. Green: read-only model and production raster.
- 189 focused tests passed (96.40 s), including existing tree/Status tests,
  App pagination and read-only storage verification, plus progress parity.
- Full Python suite: 1653 passed in 340.54 s. Existing Pillow/pytest
  deprecation warnings remain; no test failed.
- Native PlatformIO: 185 passed in 7.99 s. First sandboxed attempt could
  not write ~/.platformio/platforms.lock; rerun with allowed cache access
  completed. This was not a firmware or board failure.
- ESP32 release compilation succeeded in 39.14 s: static RAM 56116/327680
  bytes, unchanged; application 1017761/4194304 bytes. Existing TFT touch
  pin warning remains. No upload or filesystem write to the board.
- Firmware SHA-256: `a6f4c7c467fab7bdd2f2a54db95f8e2da71015db2c4e19488fa93786cd275a47`.
- Reused 227 VPA assets, no asset source changes. Gallery and RGB565
  comparisons in `out/evolution-progress/`; generated files not edited by hand.
- Final model/render/App subset: 51 passed in 15.12 s. Preview gallery has
  18 ES/EN comparisons with zero different body pixels; enlarged Firemon
  pages are `out/evolution-progress/firemon-pages.png`.
- Documentation link check: 149 local links in 11 changed/new Markdown
  documents resolve; no whitespace errors in the checked files or git diff.
- Physical validation is open: request deployment authorization/gate or
  explicit exception for this revision before flashing. Existing Status
  acceptance remains open; no new heap/FPS/radio claim is made.
