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
bool LearningRuntime::load(const CollectionSlot& slot, const CareRecord* progress) {
    std::unique_ptr<LearningState> candidate;
    if (!readPolicy(slot,candidate)) return false;
    if (progress && !progress->experiences.empty() &&
        !ProgressEvents::replay(progress->experiences,progress->learningBase,*candidate)) return false;
    adopt(std::move(candidate),slot.profile().petId(),slot.learningRef); return true;
}
bool LearningRuntime::commit(CollectionStore& store, CollectionState& state, const PetState& pet,
                             const Settings& settings, const RuntimeExperience* events, size_t count, uint32_t elapsedMs) {
    commitFailure_="context";
    if (!active_ || owner_!=pet.profile.petId() || state.active>=4 ||
        state.slots[state.active].profile().petId()!=owner_ || activeRef_!=state.slots[state.active].learningRef ||
        count>8 || (count && !events)) return false;
    if (!count) {
        const bool saved=store.progressEnabled()?store.saveCare(state,pet,settings,elapsedMs):store.saveActive(state,pet,settings);
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
    if(store.progressEnabled()) {
        const auto* pending=store.progressRecord();
        std::string log=pending?pending->experiences:"";
        const uint64_t base=pending && !log.empty()?pending->learningBase:active_->last_sequence();
        if (base>UINT64_MAX-log.size()/6 || base+log.size()/6!=active_->last_sequence()) return false;
        for(size_t i=0;i<count;++i) if(!ProgressEvents::append(log,events[i].domain,events[i].context,events[i].action,events[i].reward)) {
            commitFailure_="progress_capacity"; return false;
        }
        commitFailure_="progress_commit";
        if(!store.saveProgress(state,pet,settings,base,log,elapsedMs)) return false;
        active_=std::move(candidate); commitFailure_="none"; return true;
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
bool LearningRuntime::checkpoint(CollectionStore& store, CollectionState& state, const PetState& pet,
                                 const Settings& settings,uint32_t elapsedMs) {
    const auto* pending=store.progressRecord();
    if(!pending || pending->experiences.empty()) return store.saveActive(state,pet,settings,nullptr,elapsedMs);
    if(!active_ || owner_!=pet.profile.petId() || state.active>=4 ||
        activeRef_!=state.slots[state.active].learningRef) return false;
    std::string ref;
    if(!repository_.prepare(owner_,*active_,ref) || ref.empty() || ref.size()>64 || repository_.interrupted()) return false;
    if(!store.saveActive(state,pet,settings,ref.c_str(),elapsedMs)) return false;
    activeRef_=ref;
    return true;
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
