#pragma once

#include <stdint.h>
#include <string>

#include "vpet/PetState.h"
#include "vpet/PracticeProgress.h"

namespace vpet {

enum class StoreCommit : uint8_t { Rejected, Pending, Committed };

class KeyValueStore {
public:
    virtual ~KeyValueStore() = default;
    virtual int32_t getInt(const char* key, int32_t fallback) = 0;
    virtual bool putInt(const char* key, int32_t value) = 0;
    virtual std::string getString(const char* key, const char* fallback) = 0;
    virtual bool putString(const char* key, const char* value) = 0;
    virtual StoreCommit commitString(const char* key, const char* value) {
        return putString(key, value) ? StoreCommit::Committed : StoreCommit::Rejected;
    }
    virtual bool sync() { return true; }
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
    explicit SettingsStore(KeyValueStore& store, KeyValueStore* backup = nullptr,
                           ProfileGenerator profiles = nullptr)
        : store_(store), backup_(backup), profiles_(profiles) {}
    LoadResult load(PetState& pet, Settings& settings);
    bool save(PetState& pet, const Settings& settings);
    // Immutable snapshots cannot receive a newly allocated identity.
    bool save(const PetState& pet, const Settings& settings) {
        if (profiles_ && !pet.profile.assigned()) return false;
        PetState copy=pet;
        return save(copy,settings);
    }
    bool recoverPending() { return recoverAll(); }
    bool commitFood(const PetState& pet);
    // False means rejected. True includes accepted intents awaiting sync/replay.
    bool commitConsumables(const PetState& pet);
    bool loadPractice(PracticeProgress& progress, int stage=1) const;
    bool savePractice(const PracticeProgress& progress, int stage=1);
    bool restartLifeIfNeeded(PetState& pet, Settings& settings);
    bool needsLifeRestart() const { return store_.getInt("life", 0) == 0; }
    bool hasBackup() const;
    SpeciesId backupSpecies() const;
    bool swapOrPark(PetState& pet, Settings& settings);
    bool migratedDna() const { return migratedDna_; }
    // Explicit migration only: recover journals, then export strict schema-3
    // snapshots without assigning profiles, normalizing or replacing originals.
    bool exportLegacySnapshots(std::string& active, std::string& backup, bool& backupPresent);

private:
    bool recoverAll();
    bool recoverSnapshotTransaction();
    bool recoverSwapTransaction();
    bool writeSnapshot(const PetState& pet, const Settings& settings);
    bool recoverFoodTransaction();
    bool recoverConsumableTransaction();
    KeyValueStore& store_;
    KeyValueStore* backup_ = nullptr;
    bool migratedDna_ = false;
    ProfileGenerator profiles_ = nullptr;
};

}  // namespace vpet
