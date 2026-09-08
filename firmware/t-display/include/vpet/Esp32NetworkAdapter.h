#pragma once

#include <Arduino.h>

#include "vpet/NetworkService.h"

namespace vpet {

class Esp32NetworkAdapter : public NetworkAdapter {
public:
    void startScan() override;
    bool scanComplete() override;
    size_t networkCount() const override;
    std::string networkName(size_t index) const override;
    void beginConnect(const char* ssid, const char* password) override;
    ConnectResult connectionResult() override;
    bool syncClock() override;

private:
    bool verifyInternet();

    int scanCount_ = 0;
    uint32_t connectStartedMs_ = 0;
    bool internetChecked_ = false;
    ConnectResult result_ = ConnectResult::Idle;
};

}  // namespace vpet
