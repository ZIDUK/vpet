#pragma once

#include <memory>
#include "vpet/CollectionStore.h"
#include "vpet/Learning.h"
#include "vpet/PracticeBattle.h"

namespace vpet {

struct RuntimeExperience {
    uint8_t domain, context, action;
    int reward;
};

class LearningRepository {
public:
    virtual ~LearningRepository() = default;
    virtual bool read(const std::string& owner, const char* ref, std::string& record) = 0;
    // Immutable and durably readable before true. A failed preparation never
    // changes any existing file. Unreferenced files are harmless orphans.
    virtual bool prepare(const std::string& owner, const LearningState& policy, std::string& ref) = 0;
    virtual const char* failureReason() const { return "policy_prepare"; }
    virtual void setInterrupt(bool (*)(void*), void*) {}
    virtual bool interrupted() const { return false; }
};

class LearningRuntime {
public:
    explicit LearningRuntime(LearningRepository& repository) : repository_(repository) {}
    bool load(const CollectionSlot& slot, const CareRecord* progress=nullptr);
    bool readPolicy(const CollectionSlot& slot, std::unique_ptr<LearningState>& result);
    void adopt(std::unique_ptr<LearningState> policy, const std::string& owner, const char* ref);
    bool commit(CollectionStore& store, CollectionState& state, const PetState& pet,
                const Settings& settings, const RuntimeExperience* events, size_t count, uint32_t elapsedMs=0);
    bool checkpoint(CollectionStore& store, CollectionState& state, const PetState& pet,
                    const Settings& settings, uint32_t elapsedMs=0);
    void setInterrupt(bool (*callback)(void*),void* context) { repository_.setInterrupt(callback,context); }
    bool interrupted() const { return repository_.interrupted(); }
    bool inherit(const CollectionSlot& a, const CollectionSlot& b, const PetProfile& child, std::string& ref);
    int chooseAuto(const practice::Fighter& fighter, uint8_t learnedMask) const;
    const LearningState* policy() const { return active_.get(); }
    const char* commitFailure() const { return commitFailure_; }

private:
    LearningRepository& repository_;
    std::unique_ptr<LearningState> active_;
    std::string owner_;
    std::string activeRef_;
    const char* commitFailure_ = "none";
};
}  // namespace vpet
