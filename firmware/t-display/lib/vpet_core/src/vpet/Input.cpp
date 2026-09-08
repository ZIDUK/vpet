#include "vpet/Input.h"

namespace vpet {

Input::Input(uint32_t debounceMs, uint32_t longPressMs)
    : debounceMs_(debounceMs), longPressMs_(longPressMs) {}

InputEvent Input::updateButton(
    ButtonState& button,
    bool down,
    uint32_t nowMs,
    InputEvent shortEvent,
    bool supportsLongPress
) {
    if (down != button.raw) {
        button.raw = down;
        button.changedAt = nowMs;
    }
    if (button.raw == button.stable || nowMs - button.changedAt < debounceMs_) {
        return InputEvent::None;
    }

    button.stable = button.raw;
    if (button.stable) {
        button.pressedAt = nowMs;
        return InputEvent::None;
    }
    if (supportsLongPress && nowMs - button.pressedAt >= longPressMs_) {
        return InputEvent::Back;
    }
    return shortEvent;
}

InputEvent Input::poll(ButtonSample sample, uint32_t nowMs) {
    InputEvent event = updateButton(
        next_, sample.nextDown, nowMs, InputEvent::Next, true
    );
    if (event != InputEvent::None) {
        return event;
    }
    return updateButton(
        action_, sample.actionDown, nowMs, InputEvent::Action, false
    );
}

}  // namespace vpet
