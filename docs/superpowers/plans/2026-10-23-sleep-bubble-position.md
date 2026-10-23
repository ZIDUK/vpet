# Sleep Bubble Position Correction

## Approved Direction

User confirms Zzz appears on hardware but wants it directly above the pet,
not detached toward the top of Home. Change only its position; retain
the approved fixed glyph, darkness, actions, persistence and Status.

## Implementation

- [x] Pin horizontal center of the 32px bubble to the 88px pet, both facing
  directions and at x=0/76/152, in actual C++ and simulator tests.
- [x] Anchor vertically to the sprite's first visible row minus 30px,
  clamped below navigation. Transparent space above a lying pet must not
  separate it from its bubble.
- [x] Extend AssetStore::drawFrame with optional visibleTop output. Capture
  it from existing visible runs, including the icon cache; no extra I/O
  or allocation. Existing callers remain compatible.
- [x] Match that bound using the simulator's existing transparency mask.
- [x] Inspect C++ pixels for four species standing/lying, unchanged tired
  bubbles, darkness and wake behavior; run focused/native tests and build.
- [x] Finish full Python suite and record results: 1602 passed in 234.27 s;
  existing warnings retained. Generated consumable catalog check passed.
- [ ] Obtain revision-specific Status waiver before firmware-only load.
- [ ] Back up current NVS/table, load only app, independently verify digest
  and unchanged critical bytes, confirm normal boot and bounded liveness.
- [ ] Obtain physical acceptance of corrected position; Status stays open.

## Evidence

Focused suite: 213 passed, including cached/cold opaque-row reporting and
missing-asset sentinel. Native: 185 passed. Firmware built: 1015849 app
bytes, static RAM 56116 unchanged. Images:
`out/sleep-bubble-position/home-lying.png`, `sleep-gallery.png`.
Initial regression failed against the prior lateral anchor. No asset or
domain file changes; no new persistent values.

## Deployment Boundary

Original Zzz revision 7815af9 was loaded and accepted only as present.
This position correction is not loaded. Requested user authorization to
load firmware without first repeating physical validation of all four
Status pages; that reply is pending. Do not reuse the earlier revision's
waiver or claim physical placement acceptance from host pixels.
