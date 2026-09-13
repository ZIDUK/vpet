#pragma once

#include <stdint.h>
#include <string>

#include "vpet/PetState.h"

namespace vpet {

class KeyValueStore {
public:
    virtual ~KeyValueStore() = default;
    virtual int32_t getInt(const char* key, int32_t fallback) = 0;
    virtual bool putInt(const char* key, int32_t value) = 0;
    virtual std::string getString(const char* key, const char* fallback) = 0;
    virtual bool putString(const char* key, const char* value) = 0;
};

struct Settings {
    std::string language = "ES";
    bool soundEnabled = true;
    bool bluetoothEnabled = false;
    int64_t manualEpochOffset = 0;
};

enum class LoadResult : uint8_t { Missing, Loaded, Unsupported };

class SettingsStore {
public:
    explicit SettingsStore(KeyValueStore& store, KeyValueStore* backup = nullptr)
        : store_(store), backup_(backup) {}
    LoadResult load(PetState& pet, Settings& settings);
    bool save(const PetState& pet, const Settings& settings);
    bool restartLifeIfNeeded(PetState& pet, Settings& settings);
    bool hasBackup() const;
    SpeciesId backupSpecies() const;
    bool swapOrPark(PetState& pet, Settings& settings);
    bool migratedDna() const { return migratedDna_; }

private:
    KeyValueStore& store_;
    KeyValueStore* backup_ = nullptr;
    bool migratedDna_ = false;
};

}  // namespace vpet
