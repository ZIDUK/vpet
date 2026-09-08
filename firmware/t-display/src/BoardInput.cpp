#include "vpet/BoardInput.h"

namespace vpet {
namespace {
constexpr uint8_t kNextPin = 0;
constexpr uint8_t kActionPin = 35;
}

void BoardInput::begin() {
    pinMode(kNextPin, INPUT_PULLUP);
    pinMode(kActionPin, INPUT);
}

InputEvent BoardInput::poll(uint32_t nowMs) {
    return input_.poll(
        {digitalRead(kNextPin) == LOW, digitalRead(kActionPin) == LOW},
        nowMs
    );
}

}  // namespace vpet
