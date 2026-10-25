#include <cassert>
#include <iostream>
#include <map>
#include "vpet/SettingsStore.h"
#include "vpet/PetState.h"
#include "vpet/TrainingSession.h"
#include "vpet/ConsumableEffects.h"
#include "vpet/PracticeSession.h"
#include "vpet/Nutrition.h"

struct MemoryStore : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    int32_t getInt(const char* key,int32_t fallback) override {
        const auto it=ints.find(key); return it==ints.end() ? fallback : it->second;
    }
    bool putInt(const char* key,int32_t value) override { ints[key]=value; return true; }
    std::string getString(const char* key,const char* fallback) override {
        const auto it=strings.find(key); return it==strings.end() ? fallback : it->second;
    }
    bool putString(const char* key,const char* value) override { strings[key]=value; return true; }
};

int main() {
    using namespace vpet;
    PetState pet;
    for (int rank = 1; rank <= 3; ++rank) for (int iv = 0; iv < 16; ++iv)
        for (int ev = 0; ev <= 252; ++ev) {
            pet.restore(static_cast<SpeciesId>(rank-1),80,100,80,0,100,0);
            const uint8_t dna[] = {static_cast<uint8_t>(iv),0,0,1};
            const uint8_t values[] = {static_cast<uint8_t>(ev),0,0,0,0,0};
            pet.restoreDna(dna); pet.restoreEv(values);
            const int before = pet.combatStat(CombatStat::Hp);
            pet.addEv(CombatStat::Hp, 6);
            std::cout << before << ' ' << pet.statLimit(CombatStat::Hp) << ' '
                      << static_cast<int>(pet.evLimit()) << ' '
                      << static_cast<int>(pet.evAt(CombatStat::Hp)) << '\n';
        }
    pet.restore(SpeciesId::Rookie,80,100,80,0,100,0);
    pet.setEvAt(CombatStat::Off,82);
    auto summary = trainingApply(pet,CombatStat::Off,12);
    assert(summary.reps==1 && summary.evAdded==2 && pet.energy()==92);
    pet.setEvAt(CombatStat::Off,200);
    const auto snapshot = pet.snapshot();
    pet.addEv(CombatStat::Off,7);
    assert(pet.evAt(CombatStat::Off)==200);
    const auto after = pet.snapshot();
    assert(memcmp(&snapshot,&after,sizeof(snapshot))==0);
    practice::Battle battle;
    const int stats[]={320,320,320,320,320,320};
    battle.player.init(stats);
    assert(battle.player.maxHp==680 && battle.player.maxMp==330);
    uint8_t stock=2;
    assert(consumables::boost(battle.player,stock,2,20));
    assert(battle.player.stats[2]==384 && battle.player.itemBase[2]==320);
    assert(consumables::boost(battle.player,stock,2,40));
    assert(battle.player.stats[2]==448 && stock==0);
    assert(effectiveStat(320,10)==288);
    pet.setEffort(100); pet.setEvAt(CombatStat::Brn,pet.evLimit());
    assert(pet.useItem(2)==ItemUseResult::Blocked);
    MemoryStore mainStore, backup;
    Settings settings;
    SettingsStore store(mainStore,&backup);
    const uint8_t savedDna[]={0xff,0xff,0xff,0x12};
    const uint8_t savedEv[]={252,200,168,100,84,0};
    pet.restoreDna(savedDna); pet.restoreEv(savedEv);
    assert(store.save(pet,settings));
    PetState loaded;
    assert(store.load(loaded,settings)==LoadResult::Loaded);
    for(int i=0;i<6;++i) assert(loaded.evAt(static_cast<CombatStat>(i))==savedEv[i]);
    for(int i=0;i<4;++i) assert(loaded.dna()[i]==savedDna[i]);
    assert(loaded.combatStat(CombatStat::Hp)==107);
    assert(mainStore.ints["schema"]==3);
    assert(store.swapOrPark(loaded,settings));
    assert(store.hasBackup());
    assert(store.swapOrPark(loaded,settings));
    for(int i=0;i<6;++i) assert(loaded.evAt(static_cast<CombatStat>(i))==savedEv[i]);
    assert(loaded.combatStat(CombatStat::Hp)==107);
}
