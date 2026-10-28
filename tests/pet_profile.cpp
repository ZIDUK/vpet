#include <cassert>
#include <iostream>
#include <map>
#include <stdexcept>
#include "vpet/PetProfile.h"
#include "vpet/StateSnapshot.h"
using namespace vpet;

struct Store : KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    int cut=-1, writes=0;
    void step() { if (writes++ == cut) throw std::runtime_error("power loss"); }
    int32_t getInt(const char* k,int32_t f) override { return ints.count(k)?ints[k]:f; }
    std::string getString(const char* k,const char* f) override { return strings.count(k)?strings[k]:f; }
    bool putInt(const char* k,int32_t v) override { step(); ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { step(); strings[k]=v; return true; }
};
uint32_t sequence=10;
PetProfile generate() {
    const uint32_t words[]={sequence++,3,4,5};
    return PetProfile::fromWords(words);
}

int main(int argc,char** argv) {
    if(argc>2) {
        PetProfile profile;
        std::cout<<(profile.decode(argv[2])?profile.encode():"!")<<'\n';
        return 0;
    }
    if (argc>1) {
        for(uint32_t n=0;n<1024;++n) {
            const uint32_t words[]={n,3,4,5};
            std::cout<<PetProfile::fromWords(words).encode()<<'\n';
        }
        return 0;
    }
    auto a=generate(), b=generate();
    const uint32_t words[]={42,3,4,5};
    auto child=PetProfile::fromWords(words,a.petId(),b.petId());
    PetProfile decoded;
    assert(decoded.decode(child.encode()) && decoded.parentA()==a.petId() && decoded.parentB()==b.petId());
    const auto valid=decoded.encode();
    for(const auto bad : {"2:future", "1:00000000000000000000000000000000:M:-:-", "1:aa:X:-:-"}) {
        assert(!decoded.decode(bad) && decoded.encode()==valid);
    }
    PetState pet;
    pet.profile=child;
    const uint8_t dna[]={10,20,30,40}, ev[]={252,83,168,4,5,6};
    pet.restoreDna(dna); pet.restoreEv(ev);
    assert(pet.sexLocus()==child.sex());
    for(const auto form : {SpeciesId::Baby,SpeciesId::Rookie,SpeciesId::Champion,SpeciesId::Ultimate}) {
        pet.evolveTo(form);
        assert(pet.profile.encode()==valid && pet.dna()[0]==10 && pet.evAt(CombatStat::Hp)==252);
    }
    Store live, backup; Settings settings;
    SettingsStore storage(live,&backup,generate);
    PetState notSaved;
    assert(!storage.swapOrPark(notSaved,settings));
    assert(storage.save(pet,settings));
    assert(live.ints["schema"]==3 && live.strings["petProfile"]==valid);
    assert(live.ints["dna4"]==(child.sex()==Sex::Male?1:2));
    storage::SnapshotStore sexSnapshot;
    assert(SettingsStore(sexSnapshot).save(pet,settings));
    const auto sexRecord=storage::encodeSnapshot(sexSnapshot);
    assert(sexRecord.rfind("6\n",0)==0);
    storage::SnapshotStore sexDecoded;
    assert(storage::decodeSnapshot(sexRecord,sexDecoded) && sexDecoded.ints.at("dna4")==live.ints["dna4"]);
    const PetState immutable=pet;
    assert(storage.save(immutable,settings));
    const PetState unassigned;
    assert(!storage.save(unassigned,settings));
    assert(storage.swapOrPark(pet,settings) && pet.profile.assigned() && pet.profile.encode()!=valid);
    const auto eggId=pet.profile.encode();
    assert(storage.swapOrPark(pet,settings) && pet.profile.encode()==valid);
    assert(backup.strings["petProfile"]==eggId);
    pet.resetToEgg();
    assert(!pet.profile.assigned());
    assert(storage.save(pet,settings) && pet.profile.encode()!=eggId && pet.profile.encode()!=valid);

    // Migration and swap are interrupted before EVERY individual store write.
    Store legacy;
    PetState old; old.evolveTo(SpeciesId::Rookie); old.restoreDna(dna); old.restoreEv(ev);
    assert(SettingsStore(legacy).save(old,settings)); // No entropy in isolated legacy fixture.
    Store restartLegacy=legacy;
    restartLegacy.ints["life"]=0;
    SettingsStore restarting(restartLegacy,nullptr,generate);
    PetState newLife;
    assert(restarting.load(newLife,settings)==LoadResult::Loaded);
    assert(restarting.needsLifeRestart() && !newLife.profile.assigned());
    assert(restarting.restartLifeIfNeeded(newLife,settings));
    assert(newLife.species()==SpeciesId::Egg && newLife.profile.assigned());
    Store complete=legacy; PetState migrated;
    assert(SettingsStore(complete,nullptr,generate).load(migrated,settings)==LoadResult::Loaded);
    complete.ints.erase("dna4");
    assert(SettingsStore(complete,nullptr,generate).load(migrated,settings)==LoadResult::Loaded);
    assert(migrated.sexLocus()==migrated.profile.sex());
    const int migrationWrites=complete.writes-legacy.writes;
    for(int cut=0;cut<=migrationWrites;++cut) {
        Store interrupted=legacy; interrupted.writes=0; interrupted.cut=cut;
        try { SettingsStore(interrupted,nullptr,generate).load(migrated,settings); } catch(const std::runtime_error&) {}
        storage::SnapshotStore intent;
        std::string accepted=interrupted.strings["petProfile"];
        if(!interrupted.strings["saveTx"].empty()) {
            assert(storage::decodeSnapshot(interrupted.strings["saveTx"],intent));
            accepted=intent.strings["petProfile"];
        }
        interrupted.cut=-1;
        assert(SettingsStore(interrupted,nullptr,generate).load(migrated,settings)==LoadResult::Loaded);
        assert(migrated.profile.assigned() && migrated.dna()[0]==10 && migrated.evAt(CombatStat::Hp)==252);
        if(!accepted.empty()) assert(migrated.profile.encode()==accepted);
        const auto stable=migrated.profile.encode();
        assert(SettingsStore(interrupted,nullptr,generate).load(migrated,settings)==LoadResult::Loaded);
        assert(migrated.profile.encode()==stable);
    }
    live=complete; backup=complete;
    PetState other; assert(SettingsStore(backup,nullptr,generate).load(other,settings)==LoadResult::Loaded);
    other.resetToEgg(); assert(SettingsStore(backup,nullptr,generate).save(other,settings));
    const auto first=live.strings["petProfile"], second=backup.strings["petProfile"];
    Store trial=live, trialBackup=backup; trial.writes=0; trialBackup.writes=0;
    assert(SettingsStore(trial,&trialBackup,generate).load(pet,settings)==LoadResult::Loaded);
    assert(SettingsStore(trial,&trialBackup,generate).swapOrPark(pet,settings));
    for(int side=0;side<2;++side) for(int cut=0;cut<=(side?trialBackup.writes:trial.writes);++cut) {
        Store x=live,y=backup; x.writes=y.writes=0;
        assert(SettingsStore(x,&y,generate).load(pet,settings)==LoadResult::Loaded);
        (side?y:x).cut=cut;
        try { SettingsStore(x,&y,generate).swapOrPark(pet,settings); } catch(const std::runtime_error&) {}
        const bool committed=x.strings["swapTx"]=="1" || x.strings["petProfile"]==second;
        x.cut=y.cut=-1;
        assert(SettingsStore(x,&y,generate).load(pet,settings)==LoadResult::Loaded);
        assert(x.strings["petProfile"]==(committed?second:first));
        assert(y.strings["petProfile"]==(committed?first:second));
    }
    live.strings["petProfile"]="2:future";
    assert(SettingsStore(live,nullptr,generate).load(pet,settings)==LoadResult::Unsupported);
    assert(live.strings["petProfile"]=="2:future");
    // A v4 journal is still decodable and must not erase the additive profile.
    storage::SnapshotStore captured;
    old.profile=PetProfile(); assert(SettingsStore(captured).save(old,settings));
    const auto historical=storage::encodeSnapshot(captured);
    assert(historical.rfind("4\n",0)==0);
    storage::SnapshotStore recovered;
    assert(storage::decodeSnapshot(historical,recovered));
    live.strings["petProfile"]=first;
    live.strings["saveTx"]=historical;
    assert(SettingsStore(live,nullptr,generate).load(pet,settings)==LoadResult::Loaded);
    assert(pet.profile.encode()==first);
    std::cout<<"profile lifecycle, migration writes="<<migrationWrites<<", swap cutpoints passed\n";
}
