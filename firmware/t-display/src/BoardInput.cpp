#include "vpet/BoardInput.h"

namespace vpet {
namespace {
constexpr uint8_t kNextPin = 35;
constexpr uint8_t kActionPin = 0;
}

void BoardInput::begin() {
    pinMode(kNextPin, INPUT);
    pinMode(kActionPin, INPUT_PULLUP);
}

InputEvent BoardInput::poll(uint32_t nowMs) {
    return input_.poll(
        {digitalRead(kNextPin) == LOW, digitalRead(kActionPin) == LOW},
        nowMs
    );
}

}  // namespace vpet
