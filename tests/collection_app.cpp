#include <cassert>
#include <map>
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
    int writes=0, reads=0;
    int32_t getInt(const char* k,int32_t f) override { ++reads; return ints.count(k)?ints[k]:f; }
    std::string getString(const char* k,const char* f) override { ++reads; return strings.count(k)?strings[k]:f; }
    bool putInt(const char* k,int32_t v) override { ++writes; ints[k]=v; return true; }
    bool putString(const char* k,const char* v) override { ++writes; strings[k]=v; return true; }
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
    before=repository.durable;
    const auto fullAllocations=allocation;
    panel.open(); for(int i=0;i<4;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.state().count()==4 && allocation==fullAllocations && repository.durable==before);
    assert(panel.advance(60000,false));
    assert(panel.state().slots[0].cooldownMs==86340000 && panel.state().slots[3].incubationMs==0);
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
    // The separate panel uses bounded text coordinates on the 240x135 surface.
    for(const auto& draw:canvas.textDraws) {
        assert(draw.x>=0 && draw.y>=0 && draw.y<128);
        assert(draw.x+canvas.textWidth(draw.value)<=240);
    }
}
