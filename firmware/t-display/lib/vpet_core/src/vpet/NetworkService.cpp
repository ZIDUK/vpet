#include "vpet/NetworkService.h"

namespace vpet {

void NetworkService::connect(const std::string& ssid, const std::string& password) {
    pendingSsid_ = ssid;
    pendingPassword_ = password;
    credentialsSaved_ = false;
    status_ = ConnectResult::Connecting;
    adapter_.beginConnect(ssid.c_str(), password.c_str());
}

bool NetworkService::autoConnect() {
    const std::string ssid = credentials_.getString("ssid", "");
    if (ssid.empty()) return false;
    connect(ssid, credentials_.getString("password", ""));
    return true;
}

ConnectResult NetworkService::poll() {
    status_ = adapter_.connectionResult();
    if (status_ == ConnectResult::InternetAvailable && !credentialsSaved_) {
        const bool ssidSaved = credentials_.putString("ssid", pendingSsid_.c_str());
        const bool passwordSaved = credentials_.putString("password", pendingPassword_.c_str());
        credentialsSaved_ = ssidSaved && passwordSaved;
        adapter_.syncClock();
    }
    return status_;
}

}  // namespace vpet
