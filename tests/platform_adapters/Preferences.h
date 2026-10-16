#pragma once
#include "nvs.h"
#include <cstring>

// Matches the installed Arduino Preferences: zero on error, strlen on success.
class Preferences {
public:
    ~Preferences() { if (opened_) nvs_close(handle_); }
    bool begin(const char* ns, bool) {
        opened_ = nvs_open(ns, NVS_READWRITE, &handle_) == ESP_OK;
        return opened_;
    }
    size_t putString(const char* key, const char* value) {
        if (!opened_ || !key || !value) return 0;
        if (nvs_set_str(handle_, key, value) != ESP_OK) return 0;
        if (nvs_commit(handle_) != ESP_OK) return 0;
        return std::strlen(value);
    }
    std::string getString(const char* key, const char* fallback) {
        const auto& values = storage_stub::visible[storage_stub::handles.at(handle_)];
        const auto it = values.find(key);
        return it == values.end() || !std::holds_alternative<std::string>(it->second)
            ? fallback : std::get<std::string>(it->second);
    }
    int32_t getInt(const char* key, int32_t fallback) {
        const auto& values = storage_stub::visible[storage_stub::handles.at(handle_)];
        const auto it = values.find(key);
        return it == values.end() || !std::holds_alternative<int32_t>(it->second)
            ? fallback : std::get<int32_t>(it->second);
    }
    size_t putInt(const char* key, int32_t value) {
        if (!opened_ || nvs_set_i32(handle_, key, value) != ESP_OK) return 0;
        return nvs_commit(handle_) == ESP_OK ? sizeof(value) : 0;
    }
private:
    bool opened_ = false;
    nvs_handle_t handle_ = 0;
};
