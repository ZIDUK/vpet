#include "vpet/Input.h"

namespace vpet {
namespace {
// Mechanical buttons can bounce for a few milliseconds.  Lock subsequent
// press edges briefly, but emit the first edge immediately for responsive UI.
constexpr uint32_t kPressLockoutMs = 70;
constexpr uint32_t kRepeatDelayMs = 320;
constexpr uint32_t kRepeatEveryMs = 180;
}

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

    if (button.raw && !button.stable) {
        button.stable = true;
        button.pressedAt = nowMs;
        button.longEmitted = false;
        button.lastRepeatAt = 0;
        if (nowMs - button.lastShortEventAt < kPressLockoutMs) {
            return InputEvent::None;
        }
        button.lastShortEventAt = nowMs;
        return shortEvent;
    }

    // Releasing is debounced so a noisy release cannot become another press.
    if (!button.raw && button.stable && nowMs - button.changedAt >= debounceMs_) {
        button.stable = false;
        return InputEvent::None;
    }

    if (supportsLongPress && button.stable && button.raw && !button.longEmitted) {
        if (nowMs - button.pressedAt >= longPressMs_) {
            button.longEmitted = true;
            return InputEvent::Back;
        }
        if (nowMs - button.pressedAt >= kRepeatDelayMs) {
            if (button.lastRepeatAt == 0 || nowMs - button.lastRepeatAt >= kRepeatEveryMs) {
                button.lastRepeatAt = nowMs;
                return shortEvent;
            }
        }
    }

    return InputEvent::None;
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
