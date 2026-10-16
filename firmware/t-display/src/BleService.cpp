#include "vpet/BleService.h"

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEHIDDevice.h>

namespace {
NimBLEHIDDevice* gHid = nullptr;
}

namespace vpet {
namespace {
// Boot-compatible keyboard map. Reports are never sent; iOS only needs the
// HID profile so Settings can list and pair vPet as an accessory.
static const uint8_t kHidReportMap[] = {
    0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x85, 0x01, 0x05, 0x07, 0x19, 0xE0,
    0x29, 0xE7, 0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x08, 0x81, 0x02,
    0x95, 0x01, 0x75, 0x08, 0x81, 0x01, 0x95, 0x06, 0x75, 0x08, 0x15, 0x00,
    0x25, 0x65, 0x05, 0x07, 0x19, 0x00, 0x29, 0x65, 0x81, 0x00, 0xC0,
};
}

class BleCallbacks final : public NimBLEServerCallbacks {
public:
    explicit BleCallbacks(BleService& service)
        : service_(service), deviceName_(service.deviceName()) {}

    void onConnect(NimBLEServer*, NimBLEConnInfo& connInfo) override {
        if (service_.onConnected()) {
            NimBLEDevice::startSecurity(connInfo.getConnHandle());
            Serial.printf("VPET_BLE status=CONNECTED name=%s\n", deviceName_.c_str());
        }
    }

    void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override {
        service_.onDisconnected();
    }

    void onAuthenticationComplete(NimBLEConnInfo& connInfo) override {
        Serial.printf(
            "VPET_BLE status=%s name=%s\n",
            connInfo.isEncrypted() ? "PAIRED" : "PAIR_FAILED",
            deviceName_.c_str()
        );
    }

private:
    BleService& service_;
    const std::string deviceName_;
};

void BleService::begin() {
    if (!deviceName_.empty()) return;
    const uint64_t mac = ESP.getEfuseMac();
    char name[16];
    snprintf(name, sizeof(name), "vPet-%04X", static_cast<unsigned>(mac & 0xFFFF));
    deviceName_ = name;
}

bool BleService::setEnabled(bool enabled) {
    if (!enabled) {
        return stop();
    }
    const BleStatus current = status();
    if (current == BleStatus::Advertising || current == BleStatus::Connected) return true;
    if (deviceName_.empty()) begin();
    if ((initialized_ || status_ == BleStatus::Error) && !stop()) return false;

    if (!NimBLEDevice::init(deviceName_)) {
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=INIT");
        return false;
    }

    initialized_ = true;
    NimBLEDevice::setPower(9);
    NimBLEDevice::setSecurityAuth(true, false, true);
    NimBLEDevice::setSecurityIOCap(BLE_SM_IO_CAP_NO_IO);

    NimBLEServer* server = NimBLEDevice::createServer();
    if (server == nullptr) {
        stop();
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=SERVER");
        return false;
    }

    delete callbacks_;
    callbacks_ = new BleCallbacks(*this);
    server->setCallbacks(callbacks_, false);
    server->advertiseOnDisconnect(true);

    delete gHid;
    gHid = new NimBLEHIDDevice(server);
    gHid->setManufacturer("vPet");
    gHid->setPnp(0x02, 0xE502, 0x000A, 0x0110);
    gHid->setHidInfo(0x00, 0x01);
    gHid->setReportMap(const_cast<uint8_t*>(kHidReportMap), sizeof(kHidReportMap));
    gHid->getInputReport(1);
    gHid->setBatteryLevel(100);

    NimBLEService* information = gHid->getDeviceInfoService();
    if (information == nullptr) {
        stop();
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=SERVICE");
        return false;
    }
    information->createCharacteristic("2A24", NIMBLE_PROPERTY::READ)->setValue("vPet T-Display");
    information->createCharacteristic("2A26", NIMBLE_PROPERTY::READ)->setValue("0.1.0");
    information->createCharacteristic("2A25", NIMBLE_PROPERTY::READ)->setValue(deviceName_);
    startAdvertising();
    const BleStatus started = status();
    return started == BleStatus::Advertising || started == BleStatus::Connected;
}

void BleService::startAdvertising() {
    if (!initialized_ || gHid == nullptr) return;
    NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();
    if (advertising == nullptr) {
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=ADVERTISING");
        return;
    }
    if (advertiseSession_.nextStart() == BleAdvertiseStep::Configure) {
        advertising->clearData();
        advertising->enableScanResponse(true);
        advertising->setDiscoverableMode(BLE_GAP_DISC_MODE_GEN);
        advertising->setConnectableMode(BLE_GAP_CONN_MODE_UND);
        advertising->setAppearance(HID_KEYBOARD);
        advertising->setName(deviceName_);
        advertising->addServiceUUID(gHid->getHidService()->getUUID());
        advertising->setMinInterval(32);
        advertising->setMaxInterval(96);
    }
    // Publish before start: a connection callback may run before start returns.
    status_ = BleStatus::Advertising;
    if (!advertising->start()) {
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=START");
        return;
    }
    Serial.printf("VPET_BLE status=ADVERTISING name=%s heap_free=%u heap_min=%u\n",
                  deviceName_.c_str(), ESP.getFreeHeap(), ESP.getMinFreeHeap());
}

bool BleService::stop() {
    // Close callback transitions before asking the host to stop. CAS in the
    // callbacks cannot resurrect Off, even if they raced with this store.
    status_ = BleStatus::Off;
    advertiseSession_.reset();
    if (!initialized_) {
        return true;
    }
    NimBLEDevice::stopAdvertising();
    // Stop/join the host before freeing anything a callback could still use.
    // deinit(true) clears objects even when host stop fails in installed NimBLE.
    if (!NimBLEDevice::deinit(false)) {
        status_ = BleStatus::Error;
        Serial.println("VPET_BLE status=ERROR reason=DEINIT");
        return false;
    }
    initialized_ = false;
    delete gHid;
    gHid = nullptr;
    NimBLEDevice::deinit(true);
    delete callbacks_;
    callbacks_ = nullptr;
    status_ = BleStatus::Off;
    Serial.println("VPET_BLE status=OFF");
    return true;
}

bool BleService::onConnected() {
    BleStatus expected = status_.load();
    while (expected == BleStatus::Advertising || expected == BleStatus::Connected) {
        if (status_.compare_exchange_weak(expected, BleStatus::Connected)) return true;
    }
    return false;
}

void BleService::onDisconnected() {
    BleStatus expected = BleStatus::Connected;
    status_.compare_exchange_strong(expected, BleStatus::Advertising);
}

}  // namespace vpet
