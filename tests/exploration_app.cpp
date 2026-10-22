#include <cassert>
#include <map>
#include <string>
#include <Arduino.h>
#include "vpet/App.h"
SerialMock Serial;
uint64_t wall=1791979200;
uint64_t clockNow() { return wall; }

struct Store : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    bool fail=false, syncFail=false, pending=false;
    int32_t getInt(const char* k,int32_t f) override { return ints.count(k) ? ints[k] : f; }
    std::string getString(const char* k,const char* f) override { return strings.count(k) ? strings[k] : f; }
    bool putInt(const char* k,int32_t v) override { if(fail) return false; ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { if(fail) return false; strings[k]=v; return true; }
    vpet::StoreCommit commitString(const char* k,const char* v) override {
        if(!putString(k,v)) return vpet::StoreCommit::Rejected;
        if(pending) { syncFail=true; return vpet::StoreCommit::Pending; }
        return vpet::StoreCommit::Committed;
    }
    bool sync() override { return !syncFail; }
};

int main() {
    using namespace vpet;
    ExplorationClock clock;
    clock.begin(0,wall); assert(!clock.trusted(0));
    clock.begin(wall,wall); assert(clock.trusted(wall));
    clock.begin(wall-1,wall); assert(!clock.trusted(wall-1));
    clock.adjusted(wall-1); assert(clock.trusted(wall-1));
    Store kv; SettingsStore storage(kv); Renderer renderer; Panels panels; BleService ble;
    PetState p; p.restore(SpeciesId::Rookie,70,60,70,0,90,0); p.rollDna(42);
    Settings settings; assert(storage.save(p,settings));
    App app(renderer,panels,storage,ble,clockNow); app.begin(0);
    uint32_t ms=0;
    auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
    for(int i=0;i<3;++i) key(InputEvent::Next);
    key(InputEvent::Action); assert(panels.explorePage==ExplorationSession::Page::Routes);
    const int frames=panels.explorationFrames;
    const int invalidations=renderer.invalidations;
    for(int i=0;i<10;++i) { ms+=20; app.tick(ms,InputEvent::None); }
    assert(panels.explorationFrames==frames); // Static lists leave time for button polling.
    assert(renderer.invalidations==invalidations);
    key(InputEvent::Next); assert(panels.explorationFrames==frames+1);
    key(InputEvent::Back); key(InputEvent::Action); // Reopen Patio before transaction checks.
    key(InputEvent::Action); assert(panels.explorePage==ExplorationSession::Page::Confirm);
    kv.fail=true; key(InputEvent::Action); assert(app.ready());
    assert(storage.load(p,settings)==LoadResult::Loaded && !p.exploration.away());
    kv.fail=false; key(InputEvent::Action);
    assert(storage.load(p,settings)==LoadResult::Loaded && p.exploration.away());
    assert(panels.explorePage==ExplorationSession::Page::Trip);
    const uint32_t age=p.ageSeconds();
    const int hunger=p.hunger();
    ms+=120000; app.tick(ms,InputEvent::None);
    assert(storage.load(p,settings)==LoadResult::Loaded);
    assert(p.ageSeconds()==age && p.hunger()==hunger && p.energy()==60);
    assert(panels.exploreHome);  // Inactivity closes the panel, not the trip.
    key(InputEvent::Action); assert(!panels.exploreHome);
    key(InputEvent::Action); assert(panels.exploreHome);
    key(InputEvent::Next); key(InputEvent::Action);
    assert(panels.explorePage==ExplorationSession::Page::Trip && !panels.exploreHome);
    wall+=1800;
    const int initial=p.energy();
    kv.pending=true; key(InputEvent::Action); assert(!app.ready());
    key(InputEvent::Action); assert(!app.ready());
    kv.pending=kv.syncFail=false; ms+=1100; app.tick(ms,InputEvent::None); assert(app.ready());
    assert(storage.load(p,settings)==LoadResult::Loaded && !p.exploration.away());
    assert(p.exploration.hasReceipt()); assert(p.energy()==initial+25);
    key(InputEvent::Action);  // Acknowledge receipt, never reapply.
    assert(storage.load(p,settings)==LoadResult::Loaded && p.energy()==initial+25);
    assert(!p.exploration.hasReceipt());
    // Invalid cold-boot calendar permits browsing, but never starts a trip.
    wall=0;
    App cold(renderer,panels,storage,ble,clockNow); cold.begin(0); ms=0;
    auto coldKey=[&](InputEvent e) { ms+=50; cold.tick(ms,e); };
    for(int i=0;i<3;++i) coldKey(InputEvent::Next);
    coldKey(InputEvent::Action); coldKey(InputEvent::Action); coldKey(InputEvent::Action);
    assert(panels.explorePage==ExplorationSession::Page::Clock);
    assert(storage.load(p,settings)==LoadResult::Loaded && !p.exploration.away());
    coldKey(InputEvent::Action); assert(panels.lastPanel==PanelId::DateTime);
    ms+=11000; cold.tick(ms,InputEvent::None);
    for(int i=0;i<5;++i) coldKey(InputEvent::Next);
    coldKey(InputEvent::Action);
    for(int i=0;i<5;++i) coldKey(InputEvent::Next);
    coldKey(InputEvent::Action); assert(panels.lastPanel==PanelId::DateTime);
    for(int i=0;i<6;++i) coldKey(InputEvent::Next);
    coldKey(InputEvent::Action);
    assert(panels.lastPanel==PanelId::Options);

    // A pending care call keeps its remaining grace while the pet is away.
    wall=1791979200;
    Store callKv; SettingsStore callStorage(callKv);
    PetState hungry; hungry.restore(SpeciesId::Rookie,0,70,70,0,90,0); hungry.rollDna(12);
    assert(hungry.updateCall(0,1,12,false)==CallUpdate::Started);
    assert(hungry.exploration.start(hungry,ExploreRoute::Patio,CombatStat::Off,wall));
    assert(callStorage.save(hungry,settings));
    App calling(renderer,panels,callStorage,ble,clockNow); calling.begin(0);
    calling.tick(1800000,InputEvent::None);
    uint32_t callMs=1800000;
    auto callKey=[&](InputEvent e) { callMs+=50; calling.tick(callMs,e); };
    for(int i=0;i<8;++i) callKey(InputEvent::Next);
    callKey(InputEvent::Action);
    for(int i=0;i<4;++i) callKey(InputEvent::Next);
    callKey(InputEvent::Action);  // Reload the active call into the same object.
    for(int i=0;i<4;++i) callKey(InputEvent::Next);
    callKey(InputEvent::Action);
    for(int i=0;i<4;++i) callKey(InputEvent::Next);
    callKey(InputEvent::Action); wall+=1800;
    callKey(InputEvent::Action); callKey(InputEvent::None);
    assert(callStorage.load(hungry,settings)==LoadResult::Loaded);
    assert(hungry.careMistakes()==0);

    // Clock trust belongs to the loaded pet, not to the previous active slot.
    Store live,back; SettingsStore swapping(live,&back), parked(back);
    PetState a; a.restore(SpeciesId::Rookie,70,70,70,0,90,0); a.rollDna(42);
    a.exploration.clockCheckpoint=wall; assert(swapping.save(a,settings));
    PetState b=a; b.exploration.clockCheckpoint=wall+100000;
    assert(parked.save(b,settings));
    // Legacy reserves still restore safely; Rest no longer exposes swapping.
    assert(swapping.swapOrPark(a,settings));
    App swapped(renderer,panels,swapping,ble,clockNow); swapped.begin(0); ms=0;
    auto swapKey=[&](InputEvent e) { ms+=50; swapped.tick(ms,e); };
    for(int i=0;i<3;++i) swapKey(InputEvent::Next);
    swapKey(InputEvent::Action); swapKey(InputEvent::Action); swapKey(InputEvent::Action);
    assert(panels.explorePage==ExplorationSession::Page::Clock);

    // Training borrows Home's scene buffer; Home must rebuild after returning.
    Store trainingKv; SettingsStore trainingStorage(trainingKv);
    assert(trainingStorage.save(a,settings));
    App training(renderer,panels,trainingStorage,ble,clockNow);
    training.begin(0);
    training.tick(50,InputEvent::Next);
    training.tick(100,InputEvent::Next);
    training.tick(150,InputEvent::Action);
    const int beforeTraining=renderer.invalidations;
    training.tick(200,InputEvent::None);
    assert(renderer.invalidations==beforeTraining+1);
}
