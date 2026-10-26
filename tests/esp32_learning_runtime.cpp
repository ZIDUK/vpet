#include <cassert>
#include <cstdio>
#include <fstream>
#include <memory>
#include <dirent.h>
#include <sys/stat.h>
#include <string>
#include "vpet/LearningRuntime.h"
#include "vpet/LittleFsLearningRepository.h"
#include "vpet/LittleFsCollectionRepository.h"

using namespace vpet;

struct FailingRepository : LearningRepository {
    LearningRepository& base;
    bool fail=false;
    explicit FailingRepository(LearningRepository& value) : base(value) {}
    bool read(const std::string& owner,const char* ref,std::string& record) override {
        return base.read(owner,ref,record);
    }
    bool prepare(const std::string& owner,const LearningState& policy,std::string& ref) override {
        if(fail) return false;
        return base.prepare(owner,policy,ref);
    }
};
struct CollectionFaults : CollectionRepository {
    CollectionRepository& base;
    int phase=0;
    explicit CollectionFaults(CollectionRepository& value) : base(value) {}
    CollectionRead size(size_t& bytes) override { return base.size(bytes); }
    bool read(size_t at,void* out,size_t bytes) override { return base.read(at,out,bytes); }
    bool begin(uint64_t seq,size_t bytes) override { return phase!=1 && base.begin(seq,bytes); }
    bool write(size_t at,const void* data,size_t bytes) override { return phase!=2 && base.write(at,data,bytes); }
    bool readPrepared(size_t at,void* out,size_t bytes) override { return phase!=3 && base.readPrepared(at,out,bytes); }
    bool commit(uint64_t seq) override { return phase!=4 && base.commit(seq); }
    void abort() override { base.abort(); }
};

int main(int argc,char** argv) {
    assert(argc==2);
    const std::string root=argv[1];
    LittleFsCollectionRepository repository((root+"/collection").c_str());
    CollectionFaults collectionFaults(repository);
    CollectionStore store(collectionFaults); CollectionState collection;
    PetState pet; Settings settings;
    uint32_t words[]={2,3,4,5}; pet.profile=PetProfile::fromWords(words);
    pet.restore(SpeciesId::Rookie,90,90,90,0,100,0); pet.rollDna(42);
    std::string snapshot; assert(CollectionStore::capture(pet,settings,snapshot));
    assert(store.migrate(collection,snapshot));
    LittleFsLearningRepository files((root+"/collection/policies").c_str());
    FailingRepository faults(files); LearningRuntime runtime(faults);
    assert(runtime.load(collection.slots[0]));
    assert(runtime.policy() && runtime.policy()->last_sequence()==0);
    RuntimeExperience training{0,0,0,58};
    pet.addEv(CombatStat::Off,6); pet.setEnergy(88);
    assert(runtime.commit(store,collection,pet,settings,&training,1));
    const std::string first=collection.slots[0].learningRef;
    assert(!first.empty() && first.size()<=64 && runtime.policy()->last_sequence()==1);
    LearningRuntime reboot(files); assert(reboot.load(collection.slots[0]));
    assert(reboot.policy()->estimate(0,0,0).mean==58);
    PetState restored; Settings ignored;
    assert(store.readPet(collection,0,restored,ignored));
    assert(restored.evAt(CombatStat::Off)==6 && restored.energy()==88);
    // Failure before the collection commit never exposes the new policy.
    faults.fail=true;
    const auto sequence=collection.sequence;
    assert(!runtime.commit(store,collection,pet,settings,&training,1));
    assert(collection.sequence==sequence && first==collection.slots[0].learningRef);
    assert(runtime.policy()->last_sequence()==1);
    faults.fail=false;
    // An orphan from a cut after blob preparation remains harmless on reboot.
    auto candidate=std::unique_ptr<LearningState>(new LearningState(*runtime.policy()));
    assert(candidate->record(2,0,0,0,-40)); std::string orphan;
    assert(files.prepare(pet.profile.petId(),*candidate,orphan));
    assert(reboot.load(collection.slots[0]) && reboot.policy()->last_sequence()==1);
    assert(runtime.commit(store,collection,pet,settings,&training,1));
    assert(runtime.policy()->last_sequence()==2);
    // Previous referenced files are never overwritten by a different proposal.
    std::string original; assert(files.read(pet.profile.petId(),first.c_str(),original));
    assert(original==reboot.policy()->encode());
    // Cuts at each collection preparation/verification/commit boundary leave
    // effects and policy sequence on the old generation, including on reboot.
    for(int phase=1;phase<=4;++phase) {
        const std::string beforeRef=collection.slots[0].learningRef;
        const auto beforeSequence=runtime.policy()->last_sequence();
        collectionFaults.phase=phase;
        assert(!runtime.commit(store,collection,pet,settings,&training,1));
        collectionFaults.phase=0;
        assert(store.load(collection)==CollectionLoad::Loaded);
        assert(collection.slots[0].learningRef==beforeRef);
        assert(runtime.policy()->last_sequence()==beforeSequence);
        assert(reboot.load(collection.slots[0]) && reboot.policy()->last_sequence()==beforeSequence);
    }
    // Long sessions/history wrap stay bounded; current AND previous remain
    // readable while only this adapter's unreferenced immutable files are GC'd.
    assert(runtime.load(collection.slots[0]));
    for(int i=0;i<270;++i) assert(runtime.commit(store,collection,pet,settings,&training,1));
    assert(runtime.policy()->history_size()==256);
    size_t policyBytes=0; unsigned policyFiles=0;
    DIR* directory=::opendir((root+"/collection/policies").c_str()); assert(directory);
    while(auto* entry=::readdir(directory)) {
        const std::string name=entry->d_name;
        if(name=="." || name=="..") continue;
        struct stat info; assert(!::stat((root+"/collection/policies/"+name).c_str(),&info));
        policyBytes+=info.st_size; ++policyFiles;
    }
    ::closedir(directory);
    assert(policyFiles<=3 && policyBytes<=LittleFsLearningRepository::kStorageBudgetBytes);
    // Policies are bound to their exact individual; invalid/missing refs fail closed.
    const auto valid=collection.slots[0]; auto invalid=valid;
    assert(reboot.load(valid)); const auto lastLoaded=reboot.policy()->last_sequence();
    words[0]=9; invalid.setProfile(PetProfile::fromWords(words));
    assert(!reboot.load(invalid)); assert(reboot.policy()->last_sequence()==lastLoaded);
    invalid=valid; std::snprintf(invalid.learningRef,sizeof(invalid.learningRef),"../escape");
    assert(!reboot.load(invalid));
    // Moderate inheritance copies no history, counts or reward sequence.
    candidate->record(3,1,0,0,100);
    std::string parentRef; assert(files.prepare(pet.profile.petId(),*candidate,parentRef));
    auto a=valid; std::snprintf(a.learningRef,sizeof(a.learningRef),"%s",parentRef.c_str());
    auto b=valid; words[0]=11; b.setProfile(PetProfile::fromWords(words)); b.learningRef[0]=0;
    auto child=PetProfile::fromWords(words,pet.profile.petId(),b.profile().petId());
    words[0]=12; child=PetProfile::fromWords(words,pet.profile.petId(),b.profile().petId());
    std::string childRef; assert(runtime.inherit(a,b,child,childRef));
    CollectionSlot childSlot; childSlot.setProfile(child);
    std::snprintf(childSlot.learningRef,sizeof(childSlot.learningRef),"%s",childRef.c_str());
    assert(reboot.load(childSlot)); assert(reboot.policy()->last_sequence()==0);
    assert(reboot.policy()->history_size()==0 && reboot.policy()->estimate(1,0,0).count==0);
    assert(reboot.policy()->estimate(1,0,0).bias==25);
    // Learned AUTO filters equipment, MP, cooldown and learned-technique mask.
    practice::Fighter fighter; fighter.equipped=3; fighter.mp=99;
    assert(reboot.chooseAuto(fighter,3)==0);
    fighter.cooldown[0]=1; assert(reboot.chooseAuto(fighter,3)==1);
    fighter.mp=0; assert(reboot.chooseAuto(fighter,3)==practice::choose(fighter));
    fighter.cooldown[0]=0; assert(reboot.chooseAuto(fighter,0)==2); // universal guard, no unlearned attack
    fighter.autoSelector=[](void* context,const practice::Fighter& input,int) {
        return static_cast<LearningRuntime*>(context)->chooseAuto(input,3);
    };
    fighter.autoContext=&reboot; fighter.mp=99; fighter.bond=100;
    assert(practice::choose(fighter)==0 && practice::choose(fighter,1)==1);
    // Unknown files are neither deleted nor allowed to bypass the storage cap.
    const auto reserved=root+"/collection/policies/reserved.dat";
    {
        std::ofstream large(reserved,std::ios::binary);
        large << std::string(LittleFsLearningRepository::kStorageBudgetBytes,'x');
    }
    std::string rejected;
    assert(!files.prepare(pet.profile.petId(),*runtime.policy(),rejected));
    struct stat reservedInfo; assert(!::stat(reserved.c_str(),&reservedInfo));
    assert(reservedInfo.st_size==LittleFsLearningRepository::kStorageBudgetBytes);
    assert(!std::remove(reserved.c_str()));
    // Uncertain/corrupt previous metadata blocks GC before any orphan removal.
    const auto orphanPath=root+"/collection/policies/L"+pet.profile.petId()+".0.12345678";
    { std::ofstream unused(orphanPath); unused << "unreferenced"; }
    auto* previous=std::fopen((root+"/collection/previous.bin").c_str(),"r+b"); assert(previous);
    assert(std::fputc('?',previous)!=EOF); assert(!std::fclose(previous));
    assert(!files.prepare(pet.profile.petId(),*runtime.policy(),rejected));
    struct stat orphanInfo; assert(!::stat(orphanPath.c_str(),&orphanInfo));
    // Corrupt policy bytes never reset to an empty policy or grant a new receipt.
    std::ofstream broken(root+"/collection/policies/"+childRef,std::ios::binary|std::ios::trunc);
    broken << "broken"; broken.close();
    assert(!reboot.load(childSlot)); assert(reboot.policy()->last_sequence()==0);
}
