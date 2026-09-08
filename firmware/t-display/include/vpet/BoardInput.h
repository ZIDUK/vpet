#pragma once

#include <Arduino.h>
#include "vpet/Input.h"

namespace vpet {

class BoardInput {
public:
    void begin();
    InputEvent poll(uint32_t nowMs);

private:
    Input input_;
};

}  // namespace vpet
