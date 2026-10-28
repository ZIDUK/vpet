#include "vpet/LearningRuntime.h"
#include <new>

namespace vpet {
bool LearningRuntime::readPolicy(const CollectionSlot& slot, std::unique_ptr<LearningState>& result) {
    const auto owner=slot.profile().petId();
    if (owner.empty() || !std::memchr(slot.learningRef,0,sizeof(slot.learningRef))) return false;
    std::unique_ptr<LearningState> candidate(new (std::nothrow) LearningState);
    if (!candidate) return false;
    if (slot.learningRef[0]) {
        std::string record;
        if (!repository_.read(owner,slot.learningRef,record) || !candidate->decode(record)) return false;
    }
    result=std::move(candidate); return true;
}
void LearningRuntime::adopt(std::unique_ptr<LearningState> policy, const std::string& owner, const char* ref) {
    active_=std::move(policy); owner_=owner; activeRef_=ref?ref:"";
}
bool LearningRuntime::load(const CollectionSlot& slot) {
    std::unique_ptr<LearningState> candidate;
    if (!readPolicy(slot,candidate)) return false;
    adopt(std::move(candidate),slot.profile().petId(),slot.learningRef); return true;
}
bool LearningRuntime::commit(CollectionStore& store, CollectionState& state, const PetState& pet,
                             const Settings& settings, const RuntimeExperience* events, size_t count) {
    commitFailure_="context";
    if (!active_ || owner_!=pet.profile.petId() || state.active>=4 ||
        state.slots[state.active].profile().petId()!=owner_ || activeRef_!=state.slots[state.active].learningRef ||
        count>8 || (count && !events)) return false;
    if (!count) {
        const bool saved=store.saveActive(state,pet,settings);
        commitFailure_=saved?"none":"collection_commit";
        return saved;
    }
    commitFailure_="memory";
    std::unique_ptr<LearningState> candidate(new (std::nothrow) LearningState(*active_));
    if (!candidate) return false;
    for (size_t i=0;i<count;++i) {
        commitFailure_="event";
        const auto& e=events[i];
        if (!candidate->record(candidate->next_sequence(),e.domain,e.context,e.action,e.reward)) return false;
    }
    std::string ref;
    if (!repository_.prepare(owner_,*candidate,ref)) {
        commitFailure_=repository_.failureReason(); return false;
    }
    commitFailure_="policy_reference";
    if (ref.empty() || ref.size()>64) return false;
    commitFailure_="collection_commit";
    if (!store.saveActive(state,pet,settings,ref.c_str())) return false;
    // Both the effects and policy receipt are now in the durable collection.
    active_=std::move(candidate); activeRef_=ref; commitFailure_="none"; return true;
}
bool LearningRuntime::inherit(const CollectionSlot& a, const CollectionSlot& b,
                              const PetProfile& child, std::string& ref) {
    if (!child.assigned() || child.parentA()!=a.profile().petId() || child.parentB()!=b.profile().petId()) return false;
    std::unique_ptr<LearningState> first, second;
    if (!readPolicy(a,first) || !readPolicy(b,second)) return false;
    std::unique_ptr<LearningState> inherited(new (std::nothrow) LearningState);
    if (!inherited) return false;
    inherited->inheritFrom(*first,*second);
    first.reset(); second.reset();
    return repository_.prepare(child.petId(),*inherited,ref);
}
int LearningRuntime::chooseAuto(const practice::Fighter& fighter, uint8_t learnedMask) const {
    // Do not invoke the installed callback recursively while finding fallback.
    practice::Fighter fixed=fighter; fixed.autoSelector=nullptr; fixed.autoContext=nullptr;
    fixed.equipped&=learnedMask;
    const int fallback=practice::choose(fixed);
    if (!active_) return fallback;
    uint8_t legal=0;
    for (int i=0;i<techniques::kCount;++i) if ((learnedMask & (1u<<i)) && fighter.valid(i)) legal|=1u<<i;
    const int learned=active_->choose(1,0,legal,fallback);
    return learned>=0 ? learned : fallback;
}
}  // namespace vpet
