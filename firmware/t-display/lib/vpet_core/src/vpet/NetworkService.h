#pragma once

#include <stddef.h>
#include <string>

#include "vpet/SettingsStore.h"

namespace vpet {

enum class ConnectResult : uint8_t { Idle, Connecting, NoAssociation, LocalOnly, InternetAvailable };

class NetworkAdapter {
public:
    virtual ~NetworkAdapter() = default;
    virtual void startScan() = 0;
    virtual bool scanComplete() = 0;
    virtual size_t networkCount() const = 0;
    virtual std::string networkName(size_t index) const = 0;
    virtual void beginConnect(const char* ssid, const char* password) = 0;
    virtual ConnectResult connectionResult() = 0;
    virtual bool syncClock() = 0;
};

class NetworkService {
public:
    NetworkService(NetworkAdapter& adapter, KeyValueStore& credentials)
        : adapter_(adapter), credentials_(credentials) {}
    void startScan() { adapter_.startScan(); }
    bool scanComplete() { return adapter_.scanComplete(); }
    size_t networkCount() const { return adapter_.networkCount(); }
    std::string networkName(size_t index) const { return adapter_.networkName(index); }
    void connect(const std::string& ssid, const std::string& password);
    bool autoConnect();
    ConnectResult poll();
    ConnectResult status() const { return status_; }

private:
    NetworkAdapter& adapter_;
    KeyValueStore& credentials_;
    std::string pendingSsid_;
    std::string pendingPassword_;
    ConnectResult status_ = ConnectResult::Idle;
    bool credentialsSaved_ = false;
};

}  // namespace vpet
