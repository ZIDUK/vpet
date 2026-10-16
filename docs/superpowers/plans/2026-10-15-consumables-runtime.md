# Consumables Runtime Integration

Goal: make the adopted catalog usable in simulator and firmware without flashing.

## Contract

- Stable string IDs from adopted_items.py. Legacy inventory indices 0..7 stay
  unchanged. Adopted menu index is 8 + catalog index; food indices stay hidden.
- Separate version-1 adopted inventory, clamped per-item stock, unknown IDs
  ignored. Seed once: small_recovery=2, mp_floppy=2, bandage=1, off_disk=1,
  blue_apple=1. Missing old record migrates to that seed; saved zero stays zero.
- One item per practice victory in catalog order, excluding unlimited food.
  Persist reward cursor with stock. Skip full stacks; no reward for defeat,
  draw, retreat or repeated terminal ticks. No economy or RNG.
- Manual max 1; +1 EV on next successfully saved attribute session, no stacking
  with old Guide. Cancellation, no headroom and failed save preserve it.
- Home bag shows stock and effect/context. Combat items are blocked at home.
  Arena adds a bag selector with three rows and Back. It does not allow extra
  attack orders while selecting; auto battle continues, including terminal
  result handling while bag is open. No revive, no consumption on zero effect.
- Item use and acquisition are transactions. On noncommitted save failure,
  restore stock and affected pet/battle state. Firmware uses an additive NVS
  journal with roll-forward after reboot, not dozens of independent stock keys.
- New NVS keys are additive; schema 3 and all existing numeric enums remain.

## Work

1. Tests for seed/migration/roundtrip, item-context visibility, acquisition once,
   stock caps and failures; implement Python inventory and battle controller.
2. Implement equivalent C++ stock, portable transactions, NVS journal, menu
   and practice controller. Preserve rollback and cold/away gates.
3. Connect real sprites and bilingual names/blurbs to both bag renderers and
   Arena. Keep action selector within 240px with bag and retreat.
4. Integrate manual in timed training transaction; test cancellation/retry.
5. Regenerate data/docs/assets; run full Python/native suites, compile firmware,
   build LittleFS and inspect ES/EN home bag and battle bag images. No flash.

## Verification 2026-10-15

- Runtime integration complete in both source paths. Full Python suite: 722
  passing tests; final focused combat/consumables run: 164 passing tests.
- PlatformIO native: 172 passing cases, including every journal write failure,
  legacy nutrition migration, Manual preview/commit, and last-order history.
- Catalog exporters pass consistency checks; generated T-Display assets:
  162 files, 7,162,184 bytes. ES/EN previews inspected in
  `out/consumables-runtime/gallery.png`.
- No board deployment. Physical persistence and interaction remain unverified.
- Final ESP32 firmware and LittleFS image compile successfully; no flash.
- Element audit is recorded in the technique standard and delivery roadmap;
  numeric parity does not close the outstanding Arena visual parity work.
