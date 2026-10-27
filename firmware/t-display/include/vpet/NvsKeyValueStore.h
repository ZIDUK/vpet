#pragma once

#include <Preferences.h>
#include <nvs.h>

#include "vpet/SettingsStore.h"

namespace vpet {

class NvsKeyValueStore : public KeyValueStore {
public:
    explicit NvsKeyValueStore(const char* nameSpace);
    ~NvsKeyValueStore() override;
    NvsKeyValueStore(const NvsKeyValueStore&) = delete;
    NvsKeyValueStore& operator=(const NvsKeyValueStore&) = delete;
    int32_t getInt(const char* key, int32_t fallback) override;
    bool putInt(const char* key, int32_t value) override;
    std::string getString(const char* key, const char* fallback) override;
    StoreRead readString(const char* key, std::string& value) override;
    bool putString(const char* key, const char* value) override;
    StoreCommit commitString(const char* key, const char* value) override;
    bool sync() override;

private:
    bool ensureOpen();
    StoreCommit commitHandle(nvs_handle_t handle);
    const char* namespace_;
    bool opened_ = false;
    Preferences preferences_;
    // A successful set followed by a failed commit is ambiguous, never rejected.
    bool pending_ = false;
    nvs_handle_t pendingHandle_ = 0;
};

}  // namespace vpet
