#pragma once
#include <functional>
#include <atomic>
#include <string>

constexpr int BLE_SM_IO_CAP_NO_IO = 0, BLE_GAP_DISC_MODE_GEN = 0;
constexpr int BLE_GAP_CONN_MODE_UND = 0, HID_KEYBOARD = 0;
namespace NIMBLE_PROPERTY { constexpr int READ = 1; }
class NimBLEServer;
struct NimBLEConnInfo {
    int getConnHandle() { return 1; }
    bool isEncrypted() { return true; }
};
struct NimBLEServerCallbacks {
    virtual ~NimBLEServerCallbacks() = default;
    virtual void onConnect(NimBLEServer*, NimBLEConnInfo&) {}
    virtual void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) {}
    virtual void onAuthenticationComplete(NimBLEConnInfo&) {}
};
namespace ble_stub {
inline bool failInit = false, failServer = false, failService = false;
inline bool failAdvertising = false, failStart = false, failDeinit = false;
inline std::atomic<int> starts{0}, clears{0}, security{0}, callbackDeletes{0};
inline std::atomic<bool> active{false};
inline std::function<void()> duringStop, duringStart, quiesce;
}
class NimBLEServer {
public:
    NimBLEServerCallbacks* callbacks = nullptr;
    bool owns = true, restart = false;
    ~NimBLEServer() {
        if (owns && callbacks) { ++ble_stub::callbackDeletes; delete callbacks; }
    }
    void setCallbacks(NimBLEServerCallbacks* cb, bool own = true) {
        callbacks = cb; owns = own;
    }
    void advertiseOnDisconnect(bool value) { restart = value; }
    void connect() { NimBLEConnInfo info; callbacks->onConnect(this, info); }
    void disconnect() {
        NimBLEConnInfo info;
        callbacks->onDisconnect(this, info, 0);
        if (restart) { ++ble_stub::starts; ble_stub::active = true; }
    }
};
struct NimBLECharacteristic {
    template<class T> void setValue(const T&) {}
};
struct NimBLEService {
    NimBLECharacteristic characteristic;
    const char* getUUID() { return "1812"; }
    NimBLECharacteristic* createCharacteristic(const char*, int) { return &characteristic; }
};
struct NimBLEAdvertising {
    void clearData() { ++ble_stub::clears; }
    void enableScanResponse(bool) {}
    void setDiscoverableMode(int) {}
    void setConnectableMode(int) {}
    void setAppearance(int) {}
    void setName(const std::string&) {}
    void addServiceUUID(const char*) {}
    void setMinInterval(int) {}
    void setMaxInterval(int) {}
    bool start() {
        ++ble_stub::starts;
        if (ble_stub::duringStart) ble_stub::duringStart();
        ble_stub::active = !ble_stub::failStart;
        return ble_stub::active;
    }
};
class NimBLEDevice {
public:
    inline static NimBLEServer* server = nullptr;
    inline static NimBLEAdvertising advertising;
    static bool init(const std::string&) { return !ble_stub::failInit; }
    static void setPower(int) {}
    static void setSecurityAuth(bool, bool, bool) {}
    static void setSecurityIOCap(int) {}
    static void startSecurity(int) { ++ble_stub::security; }
    static NimBLEServer* createServer() {
        if (ble_stub::failServer) return nullptr;
        return server = new NimBLEServer;
    }
    static NimBLEAdvertising* getAdvertising() {
        return ble_stub::failAdvertising ? nullptr : &advertising;
    }
    static void stopAdvertising() {
        if (ble_stub::duringStop) ble_stub::duringStop();
        ble_stub::active = false;
    }
    static bool deinit(bool clearAll) {
        if (ble_stub::failDeinit) return false;
        if (ble_stub::quiesce) {
            auto quiesce = std::move(ble_stub::quiesce);
            ble_stub::quiesce = {};
            quiesce();
        }
        if (clearAll) { delete server; server = nullptr; }
        ble_stub::active = false;
        return true;
    }
};
