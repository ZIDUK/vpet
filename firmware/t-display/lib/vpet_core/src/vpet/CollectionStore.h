#pragma once

#include "vpet/Collection.h"
#include "vpet/SettingsStore.h"

namespace vpet {

enum class CollectionRead : uint8_t { Missing, Present, Error };
enum class CollectionLoad : uint8_t { Missing, Loaded, Corrupt, Future, Error };

// No hardware implementation is supplied here. An adapter must reserve space for
// two durable generations plus staging, preserve the previous valid generation,
// and resolve its journal before exposing size/read. Never silently fall back
// from a corrupt/future committed record or overwrite it as an empty collection.
class CollectionRepository {
public:
    virtual ~CollectionRepository() = default;
    virtual CollectionRead size(size_t& bytes) = 0;
    virtual bool read(size_t offset, void* data, size_t bytes) = 0;
    // Compare-and-swap guard on the durable sequence; zero means missing.
    virtual bool begin(uint64_t expectedSequence, size_t bytes) = 0;
    virtual bool write(size_t offset, const void* data, size_t bytes) = 0;
    virtual bool readPrepared(size_t offset, void* data, size_t bytes) = 0;
    // True ONLY when durable and visible; false MUST leave the old record visible.
    // An uncertain/Pending outcome must be resolved inside the adapter.
    virtual bool commit(uint64_t nextSequence) = 0;
    virtual void abort() = 0;
};

class CollectionStore {
public:
    static constexpr size_t kMaxRecordBytes = 24 * 1024;
    static constexpr size_t kMaxSnapshotBytes = 3800;
    explicit CollectionStore(CollectionRepository& repository) : repository_(repository) {}

    CollectionLoad load(CollectionState& state);
    bool blocked() const { return blocked_; }
    static bool capture(const PetState& pet, const Settings& settings, std::string& record);
    static bool restore(const std::string& record, PetState& pet, Settings& settings);
    bool readPet(const CollectionState& state, size_t slot, PetState& pet, Settings& settings);

    // Caller recovers legacy journals FIRST and supplies validated snapshot strings.
    // Originals remain untouched. Missing IDs require explicit stable allocations.
    bool migrate(CollectionState& state, const std::string& active,
                 const std::string* backup = nullptr,
                 const PetProfile& missingActive = PetProfile(),
                 const PetProfile& missingBackup = PetProfile());
    bool saveActive(CollectionState& state, const PetState& pet, const Settings& settings,
                    const char* learningRef = nullptr);
    bool activate(CollectionState& state, size_t target, PetState& pet, Settings& settings,
                  const CollectionSwitchGuard& guard, bool confirmed);
    bool addFounder(CollectionState& state, const PetState& egg, const Settings& settings, bool confirmed);
    // Caller must run breeding::check_pair on live parents (including paused /
    // busy flags and ancestry), prepare DNA/policy, and require explicit consent.
    // This persistence boundary only rechecks the stored basic eligibility.
    bool commitEgg(CollectionState& state, const CollectionEggTransaction& transaction,
                   const PetState& egg, const Settings& settings, size_t& childSlot, bool confirmed);
    // Batched trusted powered-on deltas only, checkpointed conservatively by the
    // adapter (not every frame). Never ticks PetState or performs hatching.
    bool advance(CollectionState& state, uint32_t elapsedMs, bool paused);

private:
    bool persist(CollectionState& state, const CollectionState& proposed,
                 const std::string* const replacements[CollectionState::kSlots]);
    bool readBody(const CollectionSlot& slot, std::string& body);
    bool current(const CollectionState& state);
    CollectionRepository& repository_;
    bool blocked_ = false;
};

}  // namespace vpet
