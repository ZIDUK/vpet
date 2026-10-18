#include <cassert>
#include <map>
#include <string>
#include <Arduino.h>
#include "vpet/App.h"

SerialMock Serial;

struct Store : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    bool reject=false, pending=false, syncFailed=false;
    int32_t getInt(const char* k,int32_t f) override { return ints.count(k) ? ints[k] : f; }
    std::string getString(const char* k,const char* f) override { return strings.count(k) ? strings[k] : f; }
    bool putInt(const char* k,int32_t v) override { ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { strings[k]=v; return true; }
    vpet::StoreCommit commitString(const char* k,const char* v) override {
        if(reject && std::string(k)=="saveTx") return vpet::StoreCommit::Rejected;
        putString(k,v);
        if(pending) { syncFailed=true; return vpet::StoreCommit::Pending; }
        return vpet::StoreCommit::Committed;
    }
    bool sync() override { return !syncFailed; }
};

int main(int argc,char** argv) {
    using namespace vpet;
    assert(argc==2);
    const int mode=std::stoi(argv[1]);
    Store kv;
    SettingsStore storage(kv);
    Settings settings;
    PetState pet;
    pet.restore(SpeciesId::Champion,100,100,100,0,100,0);
    pet.rollDna(42); pet.setWeight(20);
    for(int i=0;i<6;++i) pet.setEvAt(static_cast<CombatStat>(i),252);
    pet.practice.equipped=1; pet.practice.bond=100; pet.practice.mastery[0]=100;
    pet.setStageAgeSeconds(mode==4 ? 129599 : 129600);
    pet.setBattles(14); pet.setWins(8); pet.setLosses(6);
    assert(storage.save(pet,settings));
    Renderer renderer; Panels panels; BleService ble;
    App app(renderer,panels,storage,ble);
    app.begin(0); assert(app.ready());
    uint32_t ms=0;
    auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
    for(int i=0;i<4;++i) key(InputEvent::Next);
    key(InputEvent::Action); // Battle menu.
    key(InputEvent::Next); key(InputEvent::Action); // Arena.
    kv.reject=mode==1;
    kv.pending=mode==2 || mode==3;
    for(int i=0;i<500 && !panels.arenaResult && app.ready();++i) {
        ms+=50;
        app.tick(ms,InputEvent::None);
    }
    if(mode==2 || mode==3) {
        assert(!app.ready());
        assert(kv.ints["battles"]==14 && kv.ints["wins"]==8);
        assert(!kv.strings["saveTx"].empty());
        key(InputEvent::Action); // Pending commit must block retry/input.
        kv.pending=kv.syncFailed=false;
        if(mode==3) {
            App reboot(renderer,panels,storage,ble);
            reboot.begin(ms);
            assert(reboot.ready());
            assert(storage.load(pet,settings)==LoadResult::Loaded);
            assert(pet.battles()==15 && pet.wins()==9);
            reboot.tick(ms+50,InputEvent::None);
            assert(storage.load(pet,settings)==LoadResult::Loaded);
            assert(pet.species()==SpeciesId::Ultimate && pet.battles()==0);
            assert(pet.wins()==9 && pet.losses()==6 && pet.adoptedStock.rewards==1);
            return 0;
        }
        ms+=1100; app.tick(ms,InputEvent::None);
        assert(app.ready());
        ms+=50; app.tick(ms,InputEvent::None);
    }
    assert(panels.arenaResult==1);
    if(mode==1) {
        assert(storage.load(pet,settings)==LoadResult::Loaded);
        assert(pet.battles()==14 && pet.wins()==8 && pet.adoptedStock.rewards==0);
        key(InputEvent::None);
        kv.reject=false;
        key(InputEvent::Action); // Retry accepted once.
    }
    assert(app.ready());
    for(int i=0;i<3;++i) key(InputEvent::None);
    assert(storage.load(pet,settings)==LoadResult::Loaded);
    assert(pet.species()==SpeciesId::Champion); // Never interrupt the result screen.
    assert(pet.battles()==15 && pet.wins()==9 && pet.losses()==6);
    assert(pet.adoptedStock.rewards==1);
    key(InputEvent::Action); // Result -> battle menu.
    key(InputEvent::Back); // Return Home.
    key(InputEvent::None); // Automatic evolution, no confirmation.
    assert(storage.load(pet,settings)==LoadResult::Loaded);
    if(mode==4) {
        assert(pet.species()==SpeciesId::Champion && pet.battles()==15);
        ms+=1100; app.tick(ms,InputEvent::None);
        assert(storage.load(pet,settings)==LoadResult::Loaded);
    }
    assert(pet.species()==SpeciesId::Ultimate && pet.battles()==0);
    assert(pet.wins()==9 && pet.losses()==6 && pet.adoptedStock.rewards==1);
    App reboot(renderer,panels,storage,ble);
    reboot.begin(ms+100); reboot.tick(ms+150,InputEvent::None);
    assert(storage.load(pet,settings)==LoadResult::Loaded);
    assert(pet.species()==SpeciesId::Ultimate && pet.adoptedStock.rewards==1);
}
