#include <cassert>
#include <map>
#include <string>
#include "vpet/PracticeSession.h"
#include "vpet/SettingsStore.h"
#include "vpet/StateSnapshot.h"

struct Store : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    int32_t getInt(const char* k,int32_t d) override { return ints.count(k) ? ints[k] : d; }
    std::string getString(const char* k,const char* d) override { return strings.count(k) ? strings[k] : d; }
    bool putInt(const char* k,int32_t v) override { ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { strings[k]=v; return true; }
};

int main() {
    using namespace vpet;
    for (int stage=0;stage<3;++stage) {
        PetState pet;
        pet.evolveTo(static_cast<SpeciesId>(stage));
        pet.practice.training=6;
        assert(pet.techniqueCapacity()==stage+2);
        assert(pet.practice.toggle(1,pet.techniqueStage()));
        assert(pet.practice.toggle(3,pet.techniqueStage())==(stage>=1));
        assert(pet.practice.toggle(4,pet.techniqueStage())==(stage>=2));
        Store memory;
        Settings settings;
        SettingsStore store(memory);
        pet.practice.mastery[3]=70; pet.practice.mastery[4]=90;
        assert(store.save(pet,settings));
        PetState restored;
        assert(store.load(restored,settings)==LoadResult::Loaded);
        assert(restored.practice.equipped==pet.practice.equipped);
        assert(restored.practice.mastery[3]==70 && restored.practice.mastery[4]==90);
        assert(store.commitConsumables(restored));
        assert(store.load(restored,settings)==LoadResult::Loaded);
        assert(restored.practice.equipped==pet.practice.equipped);
    }
    practice::Battle battle;
    battle.player.equipped=1<<4;
    battle.player.bond=100;
    battle.player.mp=50;
    assert(battle.step(4));
    assert(battle.actions[0]==4);
    assert(battle.player.mp==32 && battle.player.cooldown[4]==2);
    assert(!battle.player.valid(4));
    Store legacy;
    legacy.ints["schema"]=3;
    legacy.ints["species"]=0;
    legacy.ints["techTrain"]=2;
    legacy.ints["techEquip"]=3;
    PetState old;
    Settings settings;
    assert(SettingsStore(legacy).load(old,settings)==LoadResult::Loaded);
    assert(old.practice.equipped==3 && old.practice.mastery[3]==0 && old.practice.mastery[4]==0);
    Store current;
    old.practice.mastery[3]=12; old.practice.mastery[4]=34;
    assert(SettingsStore(current).save(old,settings));
    storage::SnapshotStore captured;
    // Obtain a durable payload by capturing the writer through its public save.
    assert(SettingsStore(captured).save(old,settings));
    storage::SnapshotStore snapshot;
    std::string record=storage::encodeSnapshot(captured);
    assert(record.rfind("3\n",0)==0);
    for (const auto version : {"1", "2"}) {
        auto historical=record;
        historical.replace(0,1,version);
        for (const auto key : {"techM3", "techM4"}) {
            auto start=historical.find(std::string(key)+" ");
            historical.erase(start,historical.find('\n',start)-start+1);
        }
        if (version[0]=='1') {
            auto end=historical.rfind("END\n");
            auto start=historical.rfind('\n',end-2)+1;
            historical.erase(start,end-start);
        }
        assert(storage::decodeSnapshot(historical,snapshot));
        assert(!snapshot.ints.count("techM3") && !snapshot.ints.count("techM4"));
        Store recovered;
        recovered.strings["saveTx"]=historical;
        assert(SettingsStore(recovered).load(old,settings)==LoadResult::Loaded);
        assert(old.practice.equipped==3 && old.practice.mastery[3]==0 && old.practice.mastery[4]==0);
    }
}
