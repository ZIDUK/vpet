#include "vpet/NvsKeyValueStore.h"

namespace vpet {

NvsKeyValueStore::NvsKeyValueStore(const char* nameSpace) : namespace_(nameSpace) {}

bool NvsKeyValueStore::ensureOpen() {
    if (!opened_) opened_ = preferences_.begin(namespace_, false);
    return opened_;
}

int32_t NvsKeyValueStore::getInt(const char* key, int32_t fallback) {
    return ensureOpen() ? preferences_.getInt(key, fallback) : fallback;
}

bool NvsKeyValueStore::putInt(const char* key, int32_t value) {
    return ensureOpen() && preferences_.putInt(key, value) > 0;
}

std::string NvsKeyValueStore::getString(const char* key, const char* fallback) {
    return ensureOpen() ? preferences_.getString(key, fallback).c_str() : fallback;
}

bool NvsKeyValueStore::putString(const char* key, const char* value) {
    return ensureOpen() && preferences_.putString(key, value) > 0;
}

}  // namespace vpet
