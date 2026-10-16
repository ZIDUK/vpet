#include "vpet/NvsKeyValueStore.h"

#include <nvs.h>

namespace vpet {

NvsKeyValueStore::NvsKeyValueStore(const char* nameSpace) : namespace_(nameSpace) {}

NvsKeyValueStore::~NvsKeyValueStore() {
    if (pending_) nvs_close(pendingHandle_);
}

bool NvsKeyValueStore::ensureOpen() {
    if (!opened_) opened_ = preferences_.begin(namespace_, false);
    return opened_;
}

int32_t NvsKeyValueStore::getInt(const char* key, int32_t fallback) {
    return ensureOpen() ? preferences_.getInt(key, fallback) : fallback;
}

bool NvsKeyValueStore::putInt(const char* key, int32_t value) {
    if (pending_ || !key || !ensureOpen()) return false;
    nvs_handle_t handle;
    if (nvs_open(namespace_, NVS_READWRITE, &handle) != ESP_OK) return false;
    if (nvs_set_i32(handle, key, value) != ESP_OK) {
        nvs_close(handle);
        return false;
    }
    return commitHandle(handle) == StoreCommit::Committed;
}

std::string NvsKeyValueStore::getString(const char* key, const char* fallback) {
    return ensureOpen() ? preferences_.getString(key, fallback).c_str() : fallback;
}

bool NvsKeyValueStore::putString(const char* key, const char* value) {
    return commitString(key, value) == StoreCommit::Committed;
}

StoreCommit NvsKeyValueStore::commitString(const char* key, const char* value) {
    if (pending_ || !key || !value || !ensureOpen()) return StoreCommit::Rejected;
    // Preferences collapses empty success and all errors to zero. Raw NVS also
    // distinguishes a rejected set from an accepted but unconfirmed commit.
    nvs_handle_t handle;
    if (nvs_open(namespace_, NVS_READWRITE, &handle) != ESP_OK) return StoreCommit::Rejected;
    if (nvs_set_str(handle, key, value) != ESP_OK) {
        nvs_close(handle);
        return StoreCommit::Rejected;
    }
    return commitHandle(handle);
}

StoreCommit NvsKeyValueStore::commitHandle(nvs_handle_t handle) {
    if (nvs_commit(handle) != ESP_OK) {
        pendingHandle_ = handle;
        pending_ = true;
        return StoreCommit::Pending;
    }
    nvs_close(handle);
    return StoreCommit::Committed;
}

bool NvsKeyValueStore::sync() {
    if (!pending_) return true;
    if (nvs_commit(pendingHandle_) != ESP_OK) return false;
    nvs_close(pendingHandle_);
    pendingHandle_ = 0;
    pending_ = false;
    return true;
}

}  // namespace vpet
