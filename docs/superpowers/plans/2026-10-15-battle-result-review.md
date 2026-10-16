# Battle Result and Navigation Review

User report: missing feet in Firemon's happy animation, confusing round
diagnostics below Victory, and inconsistent Explore/Back navigation symbols.

## Changes

- Root cause: happy/sad sheet cells are 256px, with opaque content extending to
  y220. Their old shared viewport ended at y190. Both now use a padded square
  viewport (20,20)-(228,228), retaining all selected source pixels and stable
  animation positioning. Source artwork is unchanged; regenerate both builds.
- Terminal results show only result, summary, round count, reward/save error,
  reaction and Back/Retry. Order/action/reason/damage feedback remains in active
  rounds but is not painted after battle completion.
- Result panel extends to y110, above the selector at y115. Reaction uses a
  48px square at (174,57), fully inside the panel. C++ uses the same reaction
  paths for Rookie happy/sad instead of always showing idle.
- Explore becomes a shaded compass; Back becomes a left-facing return arrow.
  Both use a shared dark beveled frame and neutral background. Selection color
  remains the menu renderer's responsibility. Build uses these symbols instead
  of the signpost and oversized legacy arrow PNG, for sim and LittleFS.

## Evidence

- tests/test_result_artwork.py checks every selected source-frame bounding box
  and compares all 15 rendered happy/sad frames in ES/EN against isolated
  sprite rendering, proving that the panel does not overwrite their feet.
- tests/test_practice_ui.py checks no terminal diagnostic labels are painted;
  existing bounds/overlap, victory/defeat/draw and language tests are retained.
- tests/test_menu_icon_style.py checks shared neutral frames at 16/20/32px.
- scripts/preview_battle_results.py generates isolated result PNGs, animated
  GIFs and icon previews in out/battle-result-review. Does not touch saves.
- Firmware compiles. Full production Arena pixel parity is still not claimed.
  No flash, commit or push in this change.
- Final verification: 726 Python tests passed; focused artwork/UI suite 73
  passed; ESP32 firmware and LittleFS builds succeeded. Existing Pillow/pytest
  deprecation warnings remain. Physical behavior is not verified.

The separate read-only firmware audit is in
[board audit](../reviews/2026-10-15-board-audit.md). Its persistence/BLE findings
remain open; these visual fixes do not resolve them.
