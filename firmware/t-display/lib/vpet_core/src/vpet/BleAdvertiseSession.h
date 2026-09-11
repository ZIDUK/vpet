#pragma once

#include <stdint.h>

namespace vpet {

enum class BleAdvertiseStep : uint8_t { Configure, StartOnly };

class BleAdvertiseSession {
public:
    BleAdvertiseStep nextStart() {
        if (configured_) return BleAdvertiseStep::StartOnly;
        configured_ = true;
        return BleAdvertiseStep::Configure;
    }

    void reset() { configured_ = false; }

private:
    bool configured_ = false;
};

}  // namespace vpet
