# Timed Training Contract

Effective 2026-10-10. The dumbbell attribute flow uses the same rules in the
Python simulator and T-Display firmware.

- Selecting an eligible attribute opens preparation without spending resources.
- START reserves one repetition and immediately begins a 10,000 ms session.
- One completed session costs 8 energy and grants up to 6 EV, capped at 252.
  Existing stat conversion and secondary effects are unchanged.
- Real pet values remain unchanged until completion. The timer advances on each
  application tick, without requiring input or blocking the application loop.
- Cancellation confirmation pauses the timer. Continue resumes the remaining
  duration; discard releases the draft with no charge, reward or save.
- Completion applies and saves once, then enters results automatically.
- A save failure restores the pre-apply snapshot. Retry attempts the same
  transaction without another timer or duplicate reward.
- Repeat returns to preparation and is unavailable when energy, EV or pet
  eligibility prevents another session. Back returns to attribute selection.
- Drafts and timers are transient; restarting does not grant partial rewards.
- NVS schema, existing state enum values and legacy domain training APIs remain
  compatible. The former manual confirmation state is not in the normal flow.

Validation: Python tests include an event-loop integration test proving that
completion happens with no button press. Native C++ tests cover completion,
pause/resume, cancellation, retry, caps and unsigned clock rollover. The pixel
comparison uses the production C++ Training renderer and packaged VPA assets at
240x135 in ES and EN; it is not a photograph of the physical display.

## Delivery checkpoint: 2026-10-11

Firmware and LittleFS were deployed successfully and startup telemetry was
received. The latest Python suite passed 511 tests; the expanded renderer
comparison passed 466 Training/Techniques frames. Physical acceptance of the
latest build remains open, including input, cancellation and persisted results.

Navigation returns to Home after 10 seconds without input, except during active
training or combat. Activity refreshes the inactivity clock; the return timer
must not cancel an active session. Cancellation dialogs and result screens
remain subject to inactivity. This is separate from the 10-second training timer.
