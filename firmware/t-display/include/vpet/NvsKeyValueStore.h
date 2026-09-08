#pragma once

#include <Preferences.h>

#include "vpet/SettingsStore.h"

namespace vpet {

class NvsKeyValueStore : public KeyValueStore {
public:
    explicit NvsKeyValueStore(const char* nameSpace);
    int32_t getInt(const char* key, int32_t fallback) override;
    bool putInt(const char* key, int32_t value) override;
    std::string getString(const char* key, const char* fallback) override;
    bool putString(const char* key, const char* value) override;

private:
    bool ensureOpen();
    const char* namespace_;
    bool opened_ = false;
    Preferences preferences_;
};

}  // namespace vpet
