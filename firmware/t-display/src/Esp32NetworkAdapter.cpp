#include "vpet/Esp32NetworkAdapter.h"

#include <HTTPClient.h>
#include <WiFi.h>

namespace vpet {

void Esp32NetworkAdapter::startScan() {
    WiFi.mode(WIFI_STA);
    WiFi.scanDelete();
    WiFi.scanNetworks(true, true);
    scanCount_ = 0;
}

bool Esp32NetworkAdapter::scanComplete() {
    const int result = WiFi.scanComplete();
    if (result == WIFI_SCAN_RUNNING) return false;
    scanCount_ = result < 0 ? 0 : result;
    return true;
}

size_t Esp32NetworkAdapter::networkCount() const {
    return static_cast<size_t>(scanCount_);
}

std::string Esp32NetworkAdapter::networkName(size_t index) const {
    if (index >= static_cast<size_t>(scanCount_)) return "";
    return WiFi.SSID(static_cast<int>(index)).c_str();
}

void Esp32NetworkAdapter::beginConnect(const char* ssid, const char* password) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    connectStartedMs_ = millis();
    internetChecked_ = false;
    result_ = ConnectResult::Connecting;
}

bool Esp32NetworkAdapter::verifyInternet() {
    IPAddress address;
    if (!WiFi.hostByName("connectivitycheck.gstatic.com", address)) return false;
    HTTPClient http;
    http.setConnectTimeout(5000);
    http.setTimeout(5000);
    if (!http.begin("http://connectivitycheck.gstatic.com/generate_204")) return false;
    const int code = http.GET();
    http.end();
    return code == 204 || code == 200;
}

ConnectResult Esp32NetworkAdapter::connectionResult() {
    if (WiFi.status() == WL_CONNECTED) {
        if (!internetChecked_) {
            internetChecked_ = true;
            result_ = verifyInternet() ? ConnectResult::InternetAvailable : ConnectResult::LocalOnly;
        }
        return result_;
    }
    if (result_ == ConnectResult::Connecting && millis() - connectStartedMs_ >= 5000) {
        result_ = ConnectResult::NoAssociation;
    }
    return result_;
}

bool Esp32NetworkAdapter::syncClock() {
    configTzTime("COT5", "pool.ntp.org", "time.google.com");
    return true;
}

}  // namespace vpet
