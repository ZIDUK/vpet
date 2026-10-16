#pragma once
#include "NimBLEDevice.h"
#include <cstdint>
class NimBLEHIDDevice {
public:
    explicit NimBLEHIDDevice(NimBLEServer*) {}
    void setManufacturer(const char*) {}
    void setPnp(int, int, int, int) {}
    void setHidInfo(int, int) {}
    void setReportMap(uint8_t*, unsigned) {}
    void getInputReport(int) {}
    void setBatteryLevel(int) {}
    NimBLEService* getDeviceInfoService() {
        return ble_stub::failService ? nullptr : &service_;
    }
    NimBLEService* getHidService() { return &service_; }
private:
    NimBLEService service_;
};
