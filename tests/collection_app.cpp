#include <cassert>
#include <map>
#include <functional>
#include <cstring>
#include <Arduino.h>
#include <TFT_eSPI.h>
#include "vpet/App.h"
#include "vpet/CollectionPanel.h"
#include "vpet/AssetStore.h"

SerialMock Serial;
bool vpet::AssetStore::drawFrameScaled(TFT_eSprite&,const char*,uint16_t,int16_t,int16_t,int16_t,int16_t,bool,int32_t,uint8_t,uint16_t) { return true; }
bool vpet::AssetStore::drawFrame(TFT_eSprite&,const char*,uint16_t,int16_t,int16_t,bool,int32_t,uint8_t,uint16_t,int16_t*) { return true; }

struct Store : vpet::KeyValueStore {
    std::map<std::string,int32_t> ints;
    std::map<std::string,std::string> strings;
    int writes=0, reads=0, syncs=0;
    bool rejectCommit=false;
    int foodFault=0, writesBeforeFailure=2;
    bool replayFault=false;
    int32_t getInt(const char* k,int32_t f) override { ++reads; return ints.count(k)?ints[k]:f; }
    std::string getString(const char* k,const char* f) override { ++reads; return strings.count(k)?strings[k]:f; }
    bool putInt(const char* k,int32_t v) override {
        if(replayFault && foodFault==2 && writesBeforeFailure--<=0) return false;
        ++writes; ints[k]=v; return true;
    }
    bool putString(const char* k,const char* v) override {
        if(replayFault && foodFault==3 && (std::string(k)=="foodTx" || std::string(k)=="saveTx") && !*v) return false;
        ++writes; strings[k]=v; return true;
    }
    bool sync() override { ++syncs; return !(replayFault && foodFault==1); }
    vpet::StoreCommit commitString(const char* k,const char* v) override {
        if(rejectCommit) return vpet::StoreCommit::Rejected;
        const auto result=KeyValueStore::commitString(k,v);
        if(foodFault && (std::string(k)=="foodTx" || std::string(k)=="saveTx") && result!=vpet::StoreCommit::Rejected) {
            replayFault=true; return vpet::StoreCommit::Pending;
        }
        return result;
    }
};
struct Repository : vpet::CollectionRepository {
    std::string durable, pending;
    uint64_t sequence=0;
    bool fail=false;
    int commits=0;
    vpet::CollectionRead size(size_t& bytes) override {
        bytes=durable.size(); return bytes?vpet::CollectionRead::Present:vpet::CollectionRead::Missing;
    }
    bool read(size_t at,void* out,size_t n) override {
        if(at+n>durable.size()) return false;
        std::memcpy(out,durable.data()+at,n); return true;
    }
    bool begin(uint64_t expected,size_t n) override {
        if(fail || expected!=sequence) return false;
        pending.assign(n,0); return true;
    }
    bool write(size_t at,const void* in,size_t n) override {
        if(at+n>pending.size()) return false;
        std::memcpy(&pending[at],in,n); return true;
    }
    bool readPrepared(size_t at,void* out,size_t n) override {
        if(at+n>pending.size()) return false;
        std::memcpy(out,pending.data()+at,n); return true;
    }
    bool commit(uint64_t next) override {
        durable=pending; pending.clear(); sequence=next; ++commits; return true;
    }
    void abort() override { pending.clear(); }
};
uint32_t allocation=100;
vpet::PetProfile profile() { uint32_t w[]={allocation++,2,3,4}; return vpet::PetProfile::fromWords(w); }
uint32_t seed() { return 1234; }
uint64_t clockNow() { return 1791979200; }

struct DeferredSaveTask : vpet::SaveTask {
    Work work=nullptr;
    void* context=nullptr;
    bool done=false, reject=false;
    int starts=0;
    std::function<void()> onStart;
    bool start(Work next,void* value) override {
        ++starts;
        if(onStart) onStart();
        if(reject || work) return false;
        work=next; context=value; return true;
    }
    bool finished() const override { return done; }
    void complete() { assert(work && !done); work(context); done=true; }
    void reset() override { assert(done); work=nullptr; done=false; }
    void wait() override { if(work && !done) complete(); }
};

void confirm(vpet::CollectionPanel& panel,vpet::PetState& p,vpet::Settings& s) {
    panel.input(vpet::InputEvent::Next,p,s,{});
    panel.input(vpet::InputEvent::Action,p,s,{});
}

int main() {
    using namespace vpet;
    assert(Navigation::kMenuCount == 9);
    assert(option_menu::count == 11);
    const uint8_t expected[] = {0,1,2,3,4,5,6,7,9,10,8};
    Navigation navigation;
    navigation.setPanel(PanelId::Options);
    for (auto option : expected) {
        assert(navigation.panelIndex() == option);
        navigation.dispatch(InputEvent::Next);
    }
    assert(navigation.panelIndex() == 0);

    Store live, backup;
    SettingsStore legacy(live,&backup), reserve(backup);
    PetState a,b; Settings settings;
    a.restore(SpeciesId::Rookie,90,90,90,0,100,0); a.profile=profile(); a.rollDna(9);
    b=a; b.profile=profile(); b.rollDna(10);
    a.restoreItems(2,1,1,1,1,1); b.restoreItems(9,9,9,9,9,9);
    assert(legacy.save(a,settings) && reserve.save(b,settings));
    const auto backupInts=backup.ints; const auto backupStrings=backup.strings;
    Repository repository; CollectionStore store(repository);
    TFT_eSprite canvas; AssetStore assets;
    CollectionPanel panel(store,legacy,profile,seed,&canvas,&assets);
    Renderer renderer; Panels panels; BleService ble;
    App app(renderer,panels,legacy,ble,clockNow,&panel);
    app.begin(0); assert(app.ready()); assert(repository.durable.empty());
    uint32_t ms=0;
    auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
    for(int i=0;i<8;++i) key(InputEvent::Next);
    key(InputEvent::Action);
    for(int i=0;i<9;++i) key(InputEvent::Next);
    key(InputEvent::Action); assert(panel.page()==CollectionPanel::Page::Migration);
    key(InputEvent::Back); assert(repository.durable.empty());
    key(InputEvent::Action); // Reopen Collection from its retained option.
    key(InputEvent::Action); // Confirmation defaults to Cancel.
    key(InputEvent::Next); key(InputEvent::Action);
    assert(panel.enabled() && panel.state().count()==2);
    assert(panel.state().stock[0]==2);
    assert(backup.ints==backupInts && backup.strings==backupStrings);
    const int legacyWrites=live.writes;
    {
        App forceApp(renderer,panels,legacy,ble,clockNow,&panel); forceApp.begin(0);
        const auto sequence=panel.state().sequence;
        uint32_t forceMs=0;
        auto forceKey=[&](InputEvent e) { forceMs+=50; forceApp.tick(forceMs,e); };
        for(int i=0;i<8;++i) forceKey(InputEvent::Next);
        forceKey(InputEvent::Action);
        for(int i=0;i<7;++i) forceKey(InputEvent::Next);
        forceKey(InputEvent::Action);
        assert(panel.state().sequence==sequence && panel.state().slots[0].form==0);
    }
    // App's real pause/save path must write collection only after migration.
    key(InputEvent::Back); // Options, collection selected.
    for(int i=0;i<10;++i) key(InputEvent::Next); // Pause (9).
    key(InputEvent::Action);
    assert(live.writes==legacyWrites);
    PetState paused; Settings pausedSettings;
    assert(store.readPet(panel.state(),panel.state().active,paused,pausedSettings) && paused.cold());
    key(InputEvent::Action); // Unpause.
    assert(store.readPet(panel.state(),panel.state().active,paused,pausedSettings) && !paused.cold());
    // Browsing and cancel do not commit a snapshot or allocate a founder.
    auto before=repository.durable; const auto allocated=allocation;
    panel.open(); panel.input(InputEvent::Action,a,settings,{});
    panel.input(InputEvent::Back,a,settings,{});
    assert(repository.durable==before && allocated==allocation);
    // A founder is added only after explicit confirmation and never replaces active.
    for(int i=0;i<4;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{});
    panel.input(InputEvent::Back,a,settings,{});
    assert(panel.state().count()==2);
    panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.state().count()==3 && panel.state().active==0 && panel.state().stock[0]==2);
    PetState founder; Settings ignored;
    assert(store.readPet(panel.state(),2,founder,ignored));
    assert(founder.species()==SpeciesId::Egg && founder.profile.assigned());
    assert(panel.state().slots[2].incubationRequiredMs==0);
    // Switching and breeding use the same shared stock and preserve parents.
    before=repository.durable;
    panel.open(); panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); panel.input(InputEvent::Action,a,settings,{});
    panel.input(InputEvent::Next,a,settings,{});
    CollectionSwitchGuard busyGuard; busyGuard.training=true;
    panel.input(InputEvent::Action,a,settings,busyGuard);
    assert(panel.state().active==0 && repository.durable==before);
    panel.open(); panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); panel.input(InputEvent::Action,a,settings,{});
    confirm(panel,a,settings); assert(panel.state().active==1 && a.profile.petId()==b.profile.petId());
    assert(a.itemCount(0)==2);
    panel.open(); for(int i=0;i<5;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); // Choose first parent.
    panel.input(InputEvent::Action,a,settings,{});
    panel.input(InputEvent::Next,a,settings,{}); panel.input(InputEvent::Action,a,settings,{});
    assert(panel.page()==CollectionPanel::Page::ConfirmBreed);
    confirm(panel,a,settings);
    assert(panel.state().count()==4 && panel.state().slots[0].cooldownMs==86400000);
    assert(panel.state().slots[1].cooldownMs==86400000 && panel.state().slots[3].seed==1234);
    const auto child=panel.state().slots[3].profile();
    assert(child.parentA()!=child.parentB());
    assert(panel.advance(1000,false));
    const int beforeCombined=repository.commits;
    assert(panel.save(a,settings));
    assert(repository.commits==beforeCombined+1);
    assert(panel.state().slots[0].cooldownMs==86400000-1000);
    before=repository.durable;
    const auto fullAllocations=allocation;
    panel.open(); for(int i=0;i<4;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.state().count()==4 && allocation==fullAllocations && repository.durable==before);
    assert(panel.advance(60000,false));
    assert(panel.state().slots[0].cooldownMs==86339000 && panel.state().slots[3].incubationMs==0);
    panel.open(); for(int i=0;i<3;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); panel.input(InputEvent::Action,a,settings,{});
    confirm(panel,a,settings); assert(panel.state().active==3);
    // Real App hatch uses only powered-on time and never rerolls a zero genome.
    {
        Repository hatchRepository=repository; CollectionStore hatchStore(hatchRepository);
        CollectionPanel hatchPanel(hatchStore,legacy,profile,seed);
        PetState zeroEgg; Settings zeroSettings;
        assert(hatchPanel.load(zeroEgg,zeroSettings)==CollectionLoad::Loaded);
        const uint8_t zeroGenome[4]={0,0,0,0}; zeroEgg.restoreDna(zeroGenome);
        assert(hatchPanel.save(zeroEgg,zeroSettings));
        App hatchApp(renderer,panels,legacy,ble,clockNow,&hatchPanel);
        hatchApp.begin(90000000); // A later startup time grants no offline credit.
        hatchApp.tick(90002000,InputEvent::None);
        assert(hatchStore.readPet(hatchPanel.state(),3,zeroEgg,zeroSettings));
        assert(zeroEgg.species()==SpeciesId::Egg);
        hatchApp.tick(91799999,InputEvent::None);
        assert(hatchStore.readPet(hatchPanel.state(),3,zeroEgg,zeroSettings));
        assert(zeroEgg.species()==SpeciesId::Egg);
        hatchApp.tick(91800000,InputEvent::None);
        assert(hatchStore.readPet(hatchPanel.state(),3,zeroEgg,zeroSettings));
        assert(zeroEgg.species()==SpeciesId::Baby && zeroEgg.profile.petId()==child.petId());
        assert(std::memcmp(zeroEgg.dna(),zeroGenome,4)==0);
    }
    for(int i=0;i<29;++i) assert(panel.advance(60000,false));
    assert(!panel.hatchReady());
    assert(panel.advance(60000,true)); assert(!panel.hatchReady());
    assert(panel.advance(60000,false)); assert(panel.hatchReady());
    const auto dna=std::string(reinterpret_cast<const char*>(a.dna()),4);
    a.evolveTo(SpeciesId::Baby); assert(panel.save(a,settings));
    assert(panel.state().slots[3].profile().petId()==child.petId());
    // Reboot loads collection before consulting stale NVS. No legacy overwrite.
    app.begin(ms); assert(app.ready());
    assert(live.writes==legacyWrites);
    PetState loaded; assert(panel.load(loaded,settings)==CollectionLoad::Loaded);
    assert(loaded.profile.petId()==child.petId() && loaded.species()==SpeciesId::Baby);
    assert(std::string(reinterpret_cast<const char*>(loaded.dna()),4)==dna);
    // Actual App feeding transaction routes stock/effect to CollectionStore.
    ms+=50; app.tick(ms,InputEvent::Next); // Food for a Baby.
    ms+=50; app.tick(ms,InputEvent::Action);
    ms+=50; app.tick(ms,InputEvent::Action);
    assert(live.writes==legacyWrites);
    assert(store.readPet(panel.state(),panel.state().active,loaded,settings));
    assert(loaded.hunger()>=90);
    // All-zero inherited DNA is a valid genome, including after hatching.
    const uint8_t zeros[4]={0,0,0,0};
    loaded.restoreDna(zeros); assert(panel.save(loaded,settings));
    assert(panel.load(loaded,settings)==CollectionLoad::Loaded);
    assert(std::memcmp(loaded.dna(),zeros,4)==0);
    // A durable write failure blocks mutations and never falls back to old NVS.
    repository.fail=true;
    assert(!panel.save(loaded,settings));
    assert(live.writes==legacyWrites && backup.ints==backupInts);
    repository.fail=false;
    repository.durable[0]='?';
    const int reads=live.reads;
    app.begin(ms); assert(!app.ready()); assert(live.reads==reads);
    // Same-ID divergent legacy states reject migration without altering either source.
    Store conflictLive,conflictBack; SettingsStore conflictLegacy(conflictLive,&conflictBack), conflictReserve(conflictBack);
    PetState conflictA=b, conflictB=b; conflictB.setHunger(70);
    assert(conflictLegacy.save(conflictA,settings) && conflictReserve.save(conflictB,settings));
    const int conflictWrites=conflictLive.writes+conflictBack.writes;
    Repository conflictRepo; CollectionStore conflictStore(conflictRepo);
    CollectionPanel conflict(conflictStore,conflictLegacy,profile,seed);
    assert(conflict.load(conflictA,settings)==CollectionLoad::Missing);
    conflict.open(); conflict.input(InputEvent::Action,conflictA,settings,{}); confirm(conflict,conflictA,settings);
    assert(conflict.failed() && conflictRepo.durable.empty());
    assert(conflictLive.writes+conflictBack.writes==conflictWrites);
    // Blocked activation must explain its actual cause in both languages,
    // without touching the legacy save, allocating identities or committing.
    Repository blockedRepository; CollectionStore blockedStore(blockedRepository);
    CollectionPanel blockedPanel(blockedStore,legacy,profile,seed,&canvas,&assets);
    const char* reasonsEn[]={"Pet is asleep","Care is paused","Pet is exploring",
        "Training active","Battle active","Action in progress","Save pending","Storage blocked"};
    const char* reasonsEs[]={"Esta dormido","Crianza pausada","Esta explorando",
        "Entrenamiento activo","Batalla activa","Accion en curso","Guardado pendiente","Almacen bloqueado"};
    for(int cause=0;cause<8;++cause) {
        PetState blockedPet; blockedPet.restore(SpeciesId::Rookie,90,90,90,0,100,0);
        CollectionSwitchGuard guard;
        if(cause==0) blockedPet.sleep.asleep=true;
        if(cause==1) blockedPet.setCold(true);
        if(cause==2) assert(blockedPet.exploration.start(blockedPet,ExploreRoute::Patio,CombatStat::Hp,1));
        if(cause==3) guard.training=true;
        if(cause==4) guard.arena=true;
        if(cause==5) assert(blockedPet.beginAction(Action::Feed));
        if(cause==6) guard.pendingJournal=true;
        if(cause==7) guard.storageError=true;
        const int writes=live.writes+backup.writes; const auto identities=allocation;
        blockedPanel.open();
        blockedPanel.input(InputEvent::Action,blockedPet,settings,guard);
        blockedPanel.input(InputEvent::Next,blockedPet,settings,guard);
        blockedPanel.input(InputEvent::Action,blockedPet,settings,guard);
        assert(blockedPanel.page()==CollectionPanel::Page::Error && !blockedPanel.failed());
        assert(blockedRepository.durable.empty() && blockedRepository.commits==0);
        assert(writes==live.writes+backup.writes && identities==allocation);
        for(const auto language:{"ES","EN"}) {
            canvas.labels.clear(); blockedPanel.draw(language);
            const char* expectedReason=!std::strcmp(language,"ES")?reasonsEs[cause]:reasonsEn[cause];
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),expectedReason)!=canvas.labels.end());
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),"NOT AVAILABLE")==canvas.labels.end());
        }
    }
    // Exercise the real menu flow with an exhausted, initially paused reserve.
    {
        Store motionLive,motionBackup; Settings motionSettings;
        SettingsStore motionLegacy(motionLive,&motionBackup), motionReserve(motionBackup);
        PetState fire,flame;
        fire.restore(SpeciesId::Rookie,90,90,90,0,100,0); fire.profile=profile(); fire.rollDna(7);
        flame.restore(SpeciesId::Champion,90,0,90,0,100,0); flame.profile=profile(); flame.rollDna(8);
        flame.setCold(true);
        assert(motionLegacy.save(fire,motionSettings) && motionReserve.save(flame,motionSettings));
        Repository motionRepository; CollectionStore motionStore(motionRepository);
        CollectionPanel motionPanel(motionStore,motionLegacy,profile,seed);
        Renderer motionRenderer; Panels motionPanels; BleService motionBle;
        App motionApp(motionRenderer,motionPanels,motionLegacy,motionBle,clockNow,&motionPanel);
        uint32_t now=0; motionApp.begin(now);
        auto input=[&](InputEvent event) { now+=50; motionApp.tick(now,event); };
        for(int i=0;i<8;++i) input(InputEvent::Next);
        input(InputEvent::Action);
        for(int i=0;i<9;++i) input(InputEvent::Next);
        input(InputEvent::Action); input(InputEvent::Action);
        input(InputEvent::Next); input(InputEvent::Action);
        assert(motionPanel.enabled());
        input(InputEvent::Next); input(InputEvent::Action); input(InputEvent::Action);
        input(InputEvent::Next); input(InputEvent::Action);
        assert(motionPanel.state().active==1 && motionApp.ready());
        input(InputEvent::Back);
        input(InputEvent::Next); input(InputEvent::Action); // Options -> Back -> Home.
        const int pausedChanges=motionRenderer.frameChanges;
        for(int i=0;i<120;++i) input(InputEvent::None);
        assert(motionRenderer.frameChanges==pausedChanges);
        input(InputEvent::Action); // Reopen Options, retaining the Home cursor.
        for(int i=0;i<9;++i) input(InputEvent::Next); // Collection.
        for(int i=0;i<10;++i) input(InputEvent::Next);
        input(InputEvent::Action); // Pause Pet ON -> OFF, through App persistence.
        PetState resumed; Settings ignoredSettings;
        assert(motionStore.readPet(motionPanel.state(),1,resumed,ignoredSettings) && !resumed.cold());
        input(InputEvent::Next); input(InputEvent::Next); input(InputEvent::Action); // Options -> Back -> Home.
        const int changes=motionRenderer.frameChanges;
        for(int i=0;i<120;++i) input(InputEvent::None);
        assert(motionApp.ready() && motionRenderer.species==SpeciesId::Champion);
        assert(motionRenderer.tired);
        assert(motionRenderer.frameChanges>changes+2);
    }
    // Accepted food must animate with Collection; rejected food must not mutate it.
    for (const auto species : {SpeciesId::Rookie, SpeciesId::Champion}) {
        for (int scenario=0;scenario<7;++scenario) {
            Store foodLegacy; SettingsStore foodSettings(foodLegacy); Settings settings;
            PetState hungry;
            hungry.restore(species,70,70,90,0,100,0); hungry.profile=profile(); hungry.rollDna(17);
            if (scenario==2) { hungry.setHunger(100); hungry.restoreOverfeed(true,1); }
            if (scenario==3) hungry.setCold(true);
            if (scenario>=4) { hungry.setHunger(6); hungry.setEnergy(0); hungry.setHappiness(0); }
            const bool protein=scenario==1 || scenario==5;
            const bool accepted=scenario<2 || scenario>=4;
            const int expectedHunger=hungry.hunger()+(protein?0:20);
            const int expectedEnergy=hungry.energy()+(protein?20:0);
            Repository foodRepository; CollectionStore foodStore(foodRepository); CollectionState state;
            std::string snapshot; assert(CollectionStore::capture(hungry,settings,snapshot));
            assert(foodStore.migrate(state,snapshot));
            CollectionPanel foodPanel(foodStore,foodSettings,profile,seed);
            Renderer foodRenderer; Panels foodPanels; BleService foodBle;
            App foodApp(foodRenderer,foodPanels,foodSettings,foodBle,clockNow,&foodPanel);
            uint32_t now=0; foodApp.begin(now); assert(foodApp.ready());
            auto input=[&](InputEvent event) {
                now+=50; simulatedMillis=now; foodApp.tick(now,event); now=simulatedMillis;
            };
            input(InputEvent::Next); input(InputEvent::Action);
            assert(foodPanels.lastPanel==PanelId::Feeding);
            if (protein) input(InputEvent::Next);
            const auto before=foodRepository.durable;
            const int changes=foodRenderer.frameChanges;
            foodRepository.fail=scenario==6;
            Serial.output.clear();
            input(InputEvent::Action);
            assert(Serial.output.find("VPET_FEED input index=")!=std::string::npos);
            const int result=accepted?0:(scenario==2?6:4);
            const std::string outcome="VPET_FEED result="+std::to_string(result)+
                " committed="+(accepted && scenario!=6?"1":"0");
            assert(Serial.output.find(outcome)!=std::string::npos);
            if (scenario==6) {
                assert(!foodApp.ready() && foodRepository.durable==before);
                assert(foodRenderer.motionState==MotionState::Eat && foodPanels.errors>0);
                Serial.output.clear(); input(InputEvent::Action);
                assert(Serial.output.find("saving=1")!=std::string::npos);
                assert(Serial.output.find("VPET_FEED result=")==std::string::npos);
                foodRepository.fail=false;
                assert(foodStore.load(state)==CollectionLoad::Loaded);
                PetState unchanged; Settings ignored;
                assert(foodStore.readPet(state,0,unchanged,ignored));
                assert(unchanged.hunger()==6 && unchanged.energy()==0 && unchanged.happiness()==0);
                assert(foodLegacy.writes==0);
                continue;
            }
            assert(foodApp.ready());
            PetState fed; Settings ignored;
            assert(foodStore.readPet(foodPanel.state(),0,fed,ignored));
            if (accepted) {
                assert(foodRenderer.motionState==MotionState::Eat);
                assert(foodRenderer.lastFrame==0 && foodRepository.durable!=before);
                assert(fed.hunger()==expectedHunger);
                assert(fed.energy()==expectedEnergy);
                for (int i=0;i<10;++i) input(InputEvent::None);
                assert(foodRenderer.motionState==MotionState::Eat);
                assert(foodRenderer.frameChanges>changes+1);
                // Finishing the presentation must not apply a second meal.
                for (int i=0;i<200;++i) input(InputEvent::None);
                assert(foodRenderer.motionState!=MotionState::Eat);
                assert(foodStore.readPet(foodPanel.state(),0,fed,ignored));
                assert(fed.hunger()==expectedHunger && fed.energy()==expectedEnergy);
            } else {
                assert(foodPanels.lastPanel==PanelId::Feeding);
                assert(foodRenderer.motionState!=MotionState::Eat && foodRepository.durable==before);
                assert(fed.hunger()==hungry.hunger() && fed.energy()==hungry.energy());
            }
            assert(foodLegacy.writes==0);
        }
    }
    // A blocked worker must not block presentation, use live mutable state, or
    // allow another transaction. The same path handles legacy NVS and Collection.
    for(bool useCollection : {false,true}) for(int scenario=0;scenario<7;++scenario) {
        Store legacyStore; SettingsStore settingsStore(legacyStore); Settings settings;
        PetState hungry;
        hungry.restore(SpeciesId::Champion,70,70,90,0,100,0);
        if(scenario==6) hungry.setHunger(100);
        hungry.profile=profile(); hungry.rollDna(29);
        assert(settingsStore.save(hungry,settings));
        const int legacyWrites=legacyStore.writes;
        Repository repository; CollectionStore store(repository); CollectionState state;
        std::string snapshot; assert(CollectionStore::capture(hungry,settings,snapshot));
        if(useCollection) assert(store.migrate(state,snapshot));
        CollectionPanel panel(store,settingsStore,profile,seed);
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,useCollection?&panel:nullptr,&task);
        uint32_t now=scenario==4?0xfffff000U:0;
        simulatedMillis=now; app.begin(now); assert(app.ready());
        auto input=[&](InputEvent event) { now+=50; simulatedMillis=now; app.tick(now,event); };
        input(InputEvent::Next); input(InputEvent::Action);
        const bool protein=scenario==5;
        if(protein) input(InputEvent::Next);
        if(scenario==6) {
            // Keep FEED open and cross the 30-second decay boundary on ACTION.
            for(uint32_t delta : {9900U,9900U,10050U}) {
                now+=delta; simulatedMillis=now; app.tick(now,InputEvent::Next);
            }
            assert(now==29950 && panels.panelIndex==0);
        }
        const auto before=repository.durable;
        const int commits=repository.commits;
        task.onStart=[&] { assert(renderer.motionState==MotionState::Eat && renderer.lastFrame==0); };
        task.reject=scenario==2;
        input(InputEvent::Action);
        assert(renderer.motionState==MotionState::Eat && renderer.lastFrame==0);
        assert(repository.durable==before && legacyStore.writes==legacyWrites);
        if(task.reject) {
            assert(app.ready() && panels.errors>0 && !task.work);
            input(InputEvent::Back); // Leave the error/FEED surface and redraw Home.
            assert(renderer.motionState!=MotionState::Eat);
            continue;
        }
        assert(!app.ready() && task.starts==1);
        const int frames=renderer.frameChanges;
        for(int i=0;i<10;++i) input(i%2?InputEvent::Action:InputEvent::Back);
        assert(renderer.motionState==MotionState::Eat && renderer.frameChanges>frames);
        assert(task.starts==1 && repository.commits==commits && legacyStore.writes==legacyWrites);
        // Reboot before the durable commit sees only the previous meal state.
        PetState rebooted; Settings reloaded;
        if(useCollection) {
            CollectionStore rebootStore(repository); CollectionState old;
            assert(rebootStore.load(old)==CollectionLoad::Loaded);
            assert(rebootStore.readPet(old,0,rebooted,reloaded));
        } else assert(settingsStore.load(rebooted,reloaded)==LoadResult::Loaded);
        assert(rebooted.hunger()==(scenario==6?100:70) && rebooted.energy()==70);
        if(scenario==3) {
            for(int i=0;i<100;++i) input(InputEvent::Next);
            assert(renderer.motionState!=MotionState::Eat && !app.ready());
        }
        repository.fail=scenario==1;
        legacyStore.rejectCommit=scenario==1;
        task.complete();
        input(InputEvent::Action); // Completion must discard this repeated ACTION.
        if(scenario==1) {
            assert(!app.ready() && panels.errors>0 && repository.durable==before);
            assert(legacyStore.writes==legacyWrites);
            if(!useCollection) {
                assert(settingsStore.load(rebooted,reloaded)==LoadResult::Loaded);
                assert(rebooted.hunger()==70 && rebooted.energy()==70);
            }
            continue;
        }
        assert(app.ready() && task.starts==1);
        if(useCollection) {
            assert(repository.commits==commits+1 && legacyStore.writes==legacyWrites);
            CollectionStore rebootStore(repository); CollectionState saved;
            assert(rebootStore.load(saved)==CollectionLoad::Loaded);
            assert(rebootStore.readPet(saved,0,rebooted,reloaded));
        } else assert(settingsStore.load(rebooted,reloaded)==LoadResult::Loaded);
        assert(rebooted.hunger()==(scenario==6?100:protein?70:90));
        assert(rebooted.energy()==(scenario==6?69:protein?90:70));
        if(scenario==6) assert(rebooted.overfeeds()==0);
        for(int i=0;i<120;++i) input(InputEvent::None);
        assert(task.starts==1 && renderer.motionState!=MotionState::Eat);
        if(useCollection) assert(repository.commits==commits+1);
    }
    // Accepted NVS intents are not rolled back when sync/replay/clear fails.
    // Rejection and accepted-but-unsettled saves both preserve elapsed care.
    for(int fault=0;fault<4;++fault) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        pet.restore(SpeciesId::Champion,70,70,90,0,100,0); pet.profile=profile(); pet.rollDna(9);
        assert(settingsStore.save(pet,settings));
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,nullptr,&task);
        uint32_t now=fault==3?0xfffff000U:0;
        app.begin(now);
        auto input=[&](InputEvent event,uint32_t delta=50) {
            now+=delta; simulatedMillis=now; app.tick(now,event);
        };
        input(InputEvent::Next); input(InputEvent::Action); input(InputEvent::Action);
        assert(!app.ready());
        input(InputEvent::None,30000); // The writer has not completed yet.
        kv.rejectCommit=fault==0; kv.foodFault=fault;
        task.complete(); input(InputEvent::Action);
        assert(!app.ready() && panels.errors>0);
        if(fault) assert(!kv.strings["saveTx"].empty() || !kv.strings["foodTx"].empty());
        input(InputEvent::Action,1000); // Failed recovery cannot accept another meal.
        assert(!app.ready() && task.starts==1);
        const int syncs=kv.syncs;
        for(int i=0;i<5;++i) input(InputEvent::None);
        assert(kv.syncs==syncs); // Recovery retries are rate-limited independently of care.
        kv.rejectCommit=false; kv.replayFault=false; kv.foodFault=0;
        input(InputEvent::None,1000);
        assert(app.ready() && task.starts==1 && kv.strings["foodTx"].empty() && kv.strings["saveTx"].empty());
        PetState saved; Settings ignored;
        assert(settingsStore.load(saved,ignored)==LoadResult::Loaded);
        assert(saved.hunger()==(fault?90:70));
        assert(saved.meals()==(fault?pet.meals()+1:pet.meals()));
        input(InputEvent::None);
        assert(renderer.ageSeconds>=32);
        assert(renderer.hunger==(fault?89:69) && renderer.energy==69);
    }
    // Full legacy checkpoints retain evolution/missed-call changes on a meal
    // boundary, including when the executor rejects the meal submission.
    for(int boundary=0;boundary<3;++boundary) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        const bool missed=boundary==2;
        pet.restore(missed?SpeciesId::Champion:SpeciesId::Rookie,missed?0:70,70,90,0,100,0);
        pet.profile=profile(); pet.rollDna(31);
        if(!missed) pet.restoreCare(86399,0,CallReason::None,0,0,0,0,0,10,1,0);
        assert(settingsStore.save(pet,settings));
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,nullptr,&task);
        uint32_t now=0; app.begin(now);
        auto input=[&](InputEvent event,uint32_t delta=50) {
            now+=delta; simulatedMillis=now; app.tick(now,event);
        };
        input(InputEvent::Next); input(InputEvent::Action);
        if(missed) {
            for(int i=0;i<66;++i) input(InputEvent::Next,9000);
            input(InputEvent::Next,5900); input(InputEvent::Next,0); input(InputEvent::Next,0);
            assert(now==600000);
        } else input(InputEvent::None,850);
        task.reject=boundary==1;
        input(InputEvent::Action);
        if(task.reject) {
            assert(!app.ready() && panels.errors>0);
            input(InputEvent::None,1000);
        } else {
            assert(!app.ready() && renderer.motionState==MotionState::Eat);
            task.complete(); input(InputEvent::None);
        }
        assert(app.ready());
        PetState saved; Settings ignored;
        assert(settingsStore.load(saved,ignored)==LoadResult::Loaded);
        assert(saved.species()==SpeciesId::Champion);
        assert(saved.careMistakes()==(missed?1:0));
        assert(saved.meals()==(task.reject?0:1));
    }
    // Items and lights present their new state before any writer is released.
    for(bool useCollection : {false,true}) for(int operation=0;operation<3;++operation)
    for(int failure=0;failure<3;++failure) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        pet.restore(SpeciesId::Champion,70,40,70,0,100,0);
        pet.profile=profile(); pet.rollDna(9); pet.restoreItems(0,2,0,0,0,0);
        const bool waking=operation==2;
        if(waking) pet.sleep.start(clockNow(),pet.dna()[3]);
        assert(settingsStore.save(pet,settings));
        Repository repository; CollectionStore store(repository); CollectionState state;
        std::string snapshot; assert(CollectionStore::capture(pet,settings,snapshot));
        if(useCollection) assert(store.migrate(state,snapshot));
        CollectionPanel panel(store,settingsStore,profile,seed);
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,useCollection?&panel:nullptr,&task);
        uint32_t now=0; simulatedMillis=now; app.begin(now);
        auto input=[&](InputEvent event,uint32_t delta=50) {
            now+=delta; simulatedMillis=now; app.tick(now,event);
        };
        for(int i=0;i<(operation==0?6:5);++i) input(InputEvent::Next);
        input(InputEvent::Action);
        const int writes=kv.writes, commits=repository.commits;
        const auto durable=repository.durable;
        task.onStart=[&] {
            if(operation==0) assert(panels.lastPanel==PanelId::Inventory && panels.itemCount==1);
            else assert(renderer.sleeping==!waking);
        };
        task.reject=failure==1;
        input(InputEvent::Action);
        assert(kv.writes==writes && repository.commits==commits);
        assert(task.starts==1);
        if(task.reject) {
            assert(app.ready() && panels.errors>0 && !task.work);
            input(InputEvent::Back);
            if(operation) assert(renderer.sleeping==waking);
            continue;
        }
        assert(!app.ready());
        const int reads=kv.reads;
        for(int i=0;i<6;++i) input(i%2?InputEvent::Action:InputEvent::None);
        assert(task.starts==1 && kv.writes==writes && kv.reads==reads);
        if(operation==0) assert(panels.itemCount==1);
        else assert(renderer.sleeping==!waking);
        PetState reloaded; Settings ignored;
        if(useCollection) {
            CollectionStore reboot(repository); CollectionState previous;
            assert(reboot.load(previous)==CollectionLoad::Loaded);
            assert(reboot.readPet(previous,0,reloaded,ignored));
        } else assert(settingsStore.load(reloaded,ignored)==LoadResult::Loaded);
        assert(reloaded.itemCount(1)==2 && reloaded.sleep.asleep==waking);
        repository.fail=failure==2; kv.rejectCommit=failure==2;
        task.complete(); input(InputEvent::Action);
        assert(task.starts==1);
        if(failure==2) {
            assert(panels.errors>0 && repository.durable==durable && kv.writes==writes);
            continue;
        }
        assert(app.ready());
        if(useCollection) {
            assert(repository.commits==commits+1 && kv.writes==writes);
            CollectionStore reboot(repository); CollectionState saved;
            assert(reboot.load(saved)==CollectionLoad::Loaded);
            assert(reboot.readPet(saved,0,reloaded,ignored));
        } else assert(settingsStore.load(reloaded,ignored)==LoadResult::Loaded);
        assert(reloaded.itemCount(1)==(operation==0?1:2));
        assert(reloaded.sleep.asleep==(operation? !waking:waking));
        if(operation==0) assert(reloaded.energy()>pet.energy());
    }
    // Adopted care stock uses the full legacy journal too. Accepted but unsettled
    // writes never roll back or reapply the item during recovery.
    for(int fault=0;fault<4;++fault) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        pet.restore(SpeciesId::Champion,70,40,70,0,100,0); pet.profile=profile(); pet.rollDna(7);
        pet.restoreItems(0,0,0,0,0,0);
        uint8_t apple=0;
        for(uint8_t i=0;i<adopted::kCount;++i) {
            pet.adoptedStock.set(i,0);
            if(!std::strcmp(adopted::kItems[i].id,"blue_apple")) apple=i;
        }
        pet.adoptedStock.set(apple,2);
        assert(settingsStore.save(pet,settings));
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,nullptr,&task);
        uint32_t now=0; app.begin(now);
        auto input=[&](InputEvent event,uint32_t delta=50) {
            now+=delta; simulatedMillis=now; app.tick(now,event);
        };
        for(int i=0;i<6;++i) input(InputEvent::Next);
        input(InputEvent::Action); input(InputEvent::Action);
        assert(!app.ready() && panels.panelIndex==8+apple && panels.selectedStock==1);
        kv.rejectCommit=fault==0; kv.foodFault=fault;
        kv.writesBeforeFailure=0; // This item changes only one persisted integer.
        task.complete(); input(InputEvent::Action);
        assert(!app.ready() && panels.errors>0 && task.starts==1);
        kv.rejectCommit=false; kv.replayFault=false; kv.foodFault=0;
        input(InputEvent::None,1000);
        assert(app.ready() && task.starts==1);
        PetState saved; Settings ignored;
        assert(settingsStore.load(saved,ignored)==LoadResult::Loaded);
        assert(saved.adoptedStock.count(apple)==(fault?1:2));
        assert(saved.happiness()==(fault?90:70));
    }
    // Consecutive eligible meals need not wait for the previous Eat clip to end;
    // the single durable writer must have completed before a second consumption.
    for(bool useCollection : {false,true}) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        pet.restore(SpeciesId::Champion,40,70,70,0,100,0); pet.profile=profile(); pet.rollDna(7);
        assert(settingsStore.save(pet,settings));
        Repository repository; CollectionStore store(repository); CollectionState state;
        std::string snapshot; assert(CollectionStore::capture(pet,settings,snapshot));
        if(useCollection) assert(store.migrate(state,snapshot));
        CollectionPanel panel(store,settingsStore,profile,seed);
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,useCollection?&panel:nullptr,&task);
        uint32_t now=0; app.begin(now);
        auto input=[&](InputEvent event) { now+=50; simulatedMillis=now; app.tick(now,event); };
        input(InputEvent::Next);
        for(int meal=1;meal<=3;++meal) {
            input(InputEvent::Action); input(InputEvent::Action);
            assert(!app.ready() && task.starts==meal && renderer.motionState==MotionState::Eat);
            task.complete(); input(InputEvent::None);
            assert(app.ready());
        }
        PetState saved; Settings ignored;
        if(useCollection) {
            CollectionStore reboot(repository); CollectionState persisted;
            assert(reboot.load(persisted)==CollectionLoad::Loaded);
            assert(reboot.readPet(persisted,0,saved,ignored));
        } else assert(settingsStore.load(saved,ignored)==LoadResult::Loaded);
        assert(saved.hunger()==100 && saved.meals()==3);
        input(InputEvent::Action); input(InputEvent::Action);
        assert(!app.ready() && task.starts==4); // Existing rules allow one overfeed per cycle.
        task.complete(); input(InputEvent::None);
        input(InputEvent::Action); input(InputEvent::Action);
        assert(app.ready() && task.starts==4); // The next full-satiety meal is blocked.
    }
    // A long light-save interval is caught up under the new sleep state, not
    // discarded or credited twice. Turning lights on catches up awake care.
    for(bool waking : {false,true}) {
        Store kv; SettingsStore settingsStore(kv); Settings settings; PetState pet;
        pet.restore(SpeciesId::Champion,70,40,70,0,100,0); pet.profile=profile(); pet.rollDna(3);
        if(waking) pet.sleep.start(clockNow(),pet.dna()[3]);
        assert(settingsStore.save(pet,settings));
        Renderer renderer; Panels panels; BleService ble; DeferredSaveTask task;
        App app(renderer,panels,settingsStore,ble,clockNow,nullptr,&task);
        uint32_t now=0; app.begin(now);
        auto input=[&](InputEvent event,uint32_t delta=50) {
            now+=delta; simulatedMillis=now; app.tick(now,event);
        };
        for(int i=0;i<5;++i) input(InputEvent::Next);
        input(InputEvent::Action); input(InputEvent::Action);
        input(InputEvent::None,300000);
        assert(!app.ready()); task.complete(); input(InputEvent::None);
        input(InputEvent::None);
        assert(app.ready() && renderer.sleeping==!waking);
        assert(renderer.hunger==(waking?60:70));
        assert(renderer.energy==(waking?30:41));
    }
    // The separate panel uses bounded text coordinates on the 240x135 surface.
    for(const auto& draw:canvas.textDraws) {
        assert(draw.x>=0 && draw.y>=0 && draw.y<128);
        assert(draw.x+canvas.textWidth(draw.value)<=240);
    }
}
