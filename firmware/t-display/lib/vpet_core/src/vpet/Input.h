#pragma once

#include <stdint.h>

namespace vpet {

enum class InputEvent : uint8_t { None, Next, Action, Back };

struct ButtonSample {
    bool nextDown;
    bool actionDown;
};

class Input {
public:
    explicit Input(uint32_t debounceMs = 25, uint32_t longPressMs = 2000);
    InputEvent poll(ButtonSample sample, uint32_t nowMs);

private:
    struct ButtonState {
        bool raw = false;
        bool stable = false;
        bool longEmitted = false;
        uint32_t changedAt = 0;
        uint32_t pressedAt = 0;
        uint32_t lastShortEventAt = 0;
        uint32_t lastRepeatAt = 0;
    };

    InputEvent updateButton(
        ButtonState& button,
        bool down,
        uint32_t nowMs,
        InputEvent shortEvent,
        bool supportsLongPress
    );

    uint32_t debounceMs_;
    uint32_t longPressMs_;
    ButtonState next_;
    ButtonState action_;
};

}  // namespace vpet
