#pragma once

#include <stdint.h>
#include <atomic>
#include <string>

#include "vpet/BleAdvertiseSession.h"

namespace vpet {

enum class BleStatus : uint8_t { Off, Advertising, Connected, Error };

class BleCallbacks;

class BleService {
public:
    // Lifecycle and name access belong to the application task. Callbacks only
    // transition the atomic status and retain their own immutable name.
    void begin();
    bool setEnabled(bool enabled);
    BleStatus status() const { return status_.load(); }
    const char* deviceName() const { return deviceName_.c_str(); }

private:
    friend class BleCallbacks;

    void startAdvertising();
    bool stop();
    bool onConnected();
    void onDisconnected();

    std::atomic<BleStatus> status_{BleStatus::Off};
    bool initialized_ = false;
    std::string deviceName_;
    BleAdvertiseSession advertiseSession_;
    BleCallbacks* callbacks_ = nullptr;
};

}  // namespace vpet
