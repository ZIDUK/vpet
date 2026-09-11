#pragma once

#include <stdint.h>
#include <string>

#include "vpet/BleAdvertiseSession.h"

namespace vpet {

enum class BleStatus : uint8_t { Off, Advertising, Connected, Error };

class BleCallbacks;

class BleService {
public:
    void begin();
    bool setEnabled(bool enabled);
    BleStatus status() const { return status_; }
    const char* deviceName() const { return deviceName_.c_str(); }

private:
    friend class BleCallbacks;

    void startAdvertising();
    void stop();
    void onConnected();
    void onDisconnected();

    volatile BleStatus status_ = BleStatus::Off;
    bool initialized_ = false;
    std::string deviceName_;
    BleAdvertiseSession advertiseSession_;
    BleCallbacks* callbacks_ = nullptr;
};

}  // namespace vpet
