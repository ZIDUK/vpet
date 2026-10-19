#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include <Arduino.h>
#include "vpet/App.h"
#include "vpet/StateSnapshot.h"
#include "vpet/Nutrition.h"
SerialMock Serial;
uint64_t wall=20000ULL*86400+23*3600;
uint64_t clockNow() { return wall; }
struct Store : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    bool fail=false;
    int32_t getInt(const char* k,int32_t f) override { return ints.count(k)?ints[k]:f; }
    std::string getString(const char* k,const char* f) override { return strings.count(k)?strings[k]:f; }
    bool putInt(const char* k,int32_t v) override { if(fail)return false; ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { if(fail)return false; strings[k]=v; return true; }
};
int main(int argc,char** argv) {
    using namespace vpet;
    if(argc==2 && std::string(argv[1])=="menus") {
        Store kv,bak; SettingsStore storage(kv,&bak); Settings settings;
        PetState p; p.restore(SpeciesId::Rookie,0,10,80,0,80,0);
        assert(storage.save(p,settings));
        PetState reserved; reserved.evolveTo(SpeciesId::Champion);
        assert(SettingsStore(bak).save(reserved,settings));
        const auto backupInts=bak.ints; const auto backupStrings=bak.strings;
        Renderer renderer; Panels panels; BleService ble;
        App app(renderer,panels,storage,ble,clockNow); app.begin(0);
        uint32_t ms=0;
        auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
        for(int i=0;i<8;++i) key(InputEvent::Next);
        key(InputEvent::Action);
        for(int i=0;i<8;++i) key(InputEvent::Next);
        kv.fail=true; key(InputEvent::Action); kv.fail=false;
        assert(storage.load(p,settings)==LoadResult::Loaded && !p.cold());
        key(InputEvent::Action);
        assert(storage.load(p,settings)==LoadResult::Loaded && p.cold());
        ms+=3600000; app.tick(ms,InputEvent::Back);
        key(InputEvent::Action);
        assert(storage.load(p,settings)==LoadResult::Loaded && !p.cold());
        assert(p.careMistakes()==0 && p.callReason()==CallReason::Hunger);
        key(InputEvent::Next); key(InputEvent::Action); // Back after Pause.
        for(int i=0;i<6;++i) key(InputEvent::Next);
        key(InputEvent::Action); key(InputEvent::Next); key(InputEvent::Action);
        assert(storage.load(p,settings)==LoadResult::Loaded && p.species()==SpeciesId::Rookie && !p.sleep.asleep);
        assert(bak.ints==backupInts && bak.strings==backupStrings);
        key(InputEvent::Action); key(InputEvent::Action);
        assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.asleep);
        key(InputEvent::Action);
        assert(panels.lastPanel==PanelId::Rest);
        assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.asleep);
        key(InputEvent::Action);
        assert(storage.load(p,settings)==LoadResult::Loaded && !p.sleep.asleep);
        return 0;
    }
    if(argc==2 && std::string(argv[1])=="paused") {
        Store kv; SettingsStore storage(kv); Settings settings;
        PetState p; p.restore(SpeciesId::Rookie,70,10,70,0,80,0);
        p.sleep.start(wall,1); p.setCold(true);
        assert(storage.save(p,settings));
        Renderer renderer; Panels panels; BleService ble;
        App app(renderer,panels,storage,ble,clockNow); app.begin(0);
        app.tick(600000,InputEvent::None);
        // Checkpoints must not credit ten minutes of frozen sleep.
        assert(storage.load(p,settings)==LoadResult::Loaded);
        assert(p.sleep.elapsed==0 && p.energy()==10 && p.sleep.asleep);
        return 0;
    }
    if (argc>1) {
        SleepRoutine r; int energy=0;
        for(int day=0;day<5;++day) {
            assert(r.start((20000ULL+day)*86400+std::stoi(argv[1])*3600,std::stoi(argv[2])));
            bool reward=false;
            r.advanceMs(std::stoi(argv[3]),energy,reward);
            std::cout<<r.encode()<<' '<<energy<<' '<<reward<<'\n';
            if(r.asleep) r.stop();
        }
        return 0;
    }
    Store kv; SettingsStore storage(kv); Settings settings;
    PetState p; p.restore(SpeciesId::Rookie,70,0,70,0,80,0); p.rollDna(42);
    assert(storage.save(p,settings));
    Renderer renderer; Panels panels; BleService ble;
    App app(renderer,panels,storage,ble,clockNow); app.begin(0);
    uint32_t ms=0;
    auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
    for(int i=0;i<5;++i) key(InputEvent::Next);
    key(InputEvent::Action);
    kv.fail=true; key(InputEvent::Action); kv.fail=false;
    assert(storage.load(p,settings)==LoadResult::Loaded && !p.sleep.asleep);
    key(InputEvent::Action); key(InputEvent::Action);
    assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.asleep);
    assert(!p.beginAction(Action::Training));
    assert(applyFood(p,FoodId::Meat)==FoodResult::Asleep);
    assert(p.useItem(1)==ItemUseResult::Blocked);
    assert(!p.exploration.start(p,ExploreRoute::Patio,CombatStat::Off,wall));
    const int hunger=p.hunger(), mistakes=p.careMistakes();
    const int hp=p.health(), ev=p.evAt(CombatStat::Mp);
    ms+=7*3600000; wall+=7*3600; app.tick(ms,InputEvent::None);
    assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.asleep);
    assert(p.energy()==84 && p.hunger()==hunger && p.careMistakes()==mistakes);
    assert(renderer.minute==360 && renderer.sleeping); // Dawn is not wake-up.
    const int saved=p.sleep.elapsed;
    App reboot(renderer,panels,storage,ble,clockNow); wall+=86400; reboot.begin(0);
    reboot.tick(50,InputEvent::None);
    assert(renderer.sleeping); // Off-device calendar jump earns no rest.
    assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.elapsed==saved);
    reboot.tick(3600050,InputEvent::None);
    assert(storage.load(p,settings)==LoadResult::Loaded && !p.sleep.asleep);
    assert(p.energy()==96 && p.health()==hp+5 && p.evAt(CombatStat::Mp)==ev+2);
    SleepRoutine complete=p.sleep;
    assert(complete.start(20000ULL*86400+23*3600,1));
    int energy=0; bool reward=false; complete.advance(28800,energy,reward);
    assert(!reward); // No repeated or backward-calendar rewards.

    // V3 journals replay without erasing the additive sleep key.
    storage::SnapshotStore captured; assert(SettingsStore(captured).save(p,settings));
    auto old=storage::encodeSnapshot(captured);
    auto end=old.rfind("END\n"), start=old.rfind('\n',end-2)+1;
    old.erase(start,end-start); old[0]='3';
    storage::SnapshotStore decoded; assert(storage::decodeSnapshot(old,decoded));
    assert(!decoded.strings.count("sleepState"));
    const auto preserved=p.sleep.encode();
    kv.strings["saveTx"]=old;
    assert(storage.load(p,settings)==LoadResult::Loaded && p.sleep.encode()==preserved);
    kv.strings["sleepState"]="99,future";
    assert(storage.load(p,settings)==LoadResult::Unsupported);
}
