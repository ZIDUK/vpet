#define main storage_interrupt_adapter_main
#include "../storage_interrupt.cpp"
#undef main
#include <Arduino.h>
#include <TFT_eSPI.h>
#include "vpet/CollectionPanel.h"
#include "vpet/AssetStore.h"

SerialMock Serial;
bool vpet::AssetStore::drawFrameScaled(TFT_eSprite&,const char*,uint16_t,int16_t,int16_t,int16_t,int16_t,bool,int32_t,uint8_t,uint16_t) { return true; }
bool vpet::AssetStore::drawFrame(TFT_eSprite&,const char*,uint16_t,int16_t,int16_t,bool,int32_t,uint8_t,uint16_t,int16_t*) { return true; }

struct JournalKv : vpet::KeyValueStore {
    std::string receipt;
    int32_t getInt(const char*,int32_t fallback) override { return fallback; }
    bool putInt(const char*,int32_t) override { return false; }
    std::string getString(const char* key,const char* fallback) override {
        CHECK(!std::strcmp(key,"colCare")); return receipt.empty()?fallback:receipt;
    }
    bool putString(const char* key,const char* value) override {
        CHECK(!std::strcmp(key,"colCare")); receipt=value; return true;
    }
};

int main(int argc,char** argv) {
    CHECK(argc==3);
    Fixture f(argv[2]); const std::string mode=argv[1];
    JournalKv kv; CareJournal journal(kv); SettingsStore legacy(kv);
    CollectionStore store(f.collection,&journal,true); LearningRuntime learning(f.learning);
    CollectionPanel panel(store,legacy,nullptr,nullptr,nullptr,nullptr,&learning);
    CHECK(panel.load(f.pet,f.settings)==CollectionLoad::Loaded);
    CHECK(panel.accumulate(1234,false)); f.pet.setEnergy(45);
    const RuntimeExperience event{0,0,0,50};
    CHECK(panel.saveExperience(f.pet,f.settings,&event,1));
    CHECK(panel.progressCount()==1 && panel.dirty() && !panel.failed());
    CHECK(panel.accumulate(222,false));
    const auto receipt=kv.receipt;
    const auto policy=learning.policy()->encode();
    const auto learned=learning.policy()->last_sequence();
    const auto sequence=panel.state().sequence;
    const std::string ref=panel.state().slots[panel.state().active].learningRef;
    panel.setInterrupt(interrupt,&control);
    if (mode=="load") {
        // Policy publication finishes first; cancel the core's subsequent load.
        watch("read","/current.bin"); control.armEvent="rename"; control.armPath="/policies/P";
    } else if (mode=="policy") watch("write","/.pending");
    else if (mode=="backup") watch("write","/previous.");
    else if (mode=="backup_publish") watch("rename","/previous.bin");
    else { CHECK(mode=="publish"); watch("rename","/current.bin"); }
    const bool saved=panel.checkpoint(f.pet,f.settings);
    CHECK(control.requested && f.collection.interrupted() && f.learning.interrupted());
    CHECK(saved==(mode=="publish"));
    CHECK(!panel.failed() && !store.blocked() && learning.policy()->encode()==policy);
    CHECK(kv.receipt==receipt);
    if (!saved) {
        CHECK(panel.state().sequence==sequence && panel.dirty() && panel.progressCount()==1);
        CHECK(ref==panel.state().slots[panel.state().active].learningRef);
        CHECK(contents(f.root+"/current.bin")==f.current);
        CHECK(contents(f.policies+"/"+f.first)==f.firstBytes);
        CHECK(contents(f.policies+"/"+f.second)==f.secondBytes);
        CHECK(contents(f.root+"/previous.bin")==f.previous || contents(f.root+"/previous.bin")==f.current);
        control=Control{};
        CHECK(panel.checkpoint(f.pet,f.settings));
    }
    control=Control{};
    CHECK(panel.state().sequence==sequence+1 && !panel.dirty() && !panel.failed() && !store.blocked());
    CareJournal rebootJournal(kv); CollectionStore reboot(f.collection,&rebootJournal,true);
    CollectionState state; PetState pet; Settings settings; LearningRuntime rebootPolicy(f.learning);
    CHECK(reboot.load(state)==CollectionLoad::Loaded && !reboot.progressRecord());
    CHECK(reboot.readPet(state,state.active,pet,settings) && pet.energy()==45);
    CHECK(rebootPolicy.load(state.slots[state.active]) && rebootPolicy.policy()->last_sequence()==learned);
    CHECK(rebootPolicy.policy()->encode()==policy);
    f.collection.abort(); CHECK(streams.empty());
}
