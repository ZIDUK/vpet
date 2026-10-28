#define main collection_baseline_main
#include "collection_app.cpp"
#undef main
#include "vpet/LittleFsCollectionRepository.h"
#include "vpet/LittleFsLearningRepository.h"

uint64_t learningWall=1791979200;
uint64_t learningClock() { return learningWall; }
struct PolicyFaults : vpet::LearningRepository {
    vpet::LearningRepository& files;
    bool fail=false;
    std::function<void()> onFailure;
    explicit PolicyFaults(vpet::LearningRepository& value) : files(value) {}
    bool read(const std::string& owner,const char* ref,std::string& record) override { return files.read(owner,ref,record); }
    bool prepare(const std::string& owner,const vpet::LearningState& p,std::string& ref) override {
        if (fail) { if(onFailure) onFailure(); return false; }
        return files.prepare(owner,p,ref);
    }
};

struct BattleStorageFaults : vpet::CollectionRepository {
    vpet::CollectionRepository& files;
    bool reject=false, unreadable=false;
    explicit BattleStorageFaults(vpet::CollectionRepository& value) : files(value) {}
    vpet::CollectionRead size(size_t& n) override { return unreadable?vpet::CollectionRead::Error:files.size(n); }
    bool read(size_t at,void* p,size_t n) override { return !unreadable && files.read(at,p,n); }
    bool begin(uint64_t seq,size_t n) override { return !reject && files.begin(seq,n); }
    bool write(size_t at,const void* p,size_t n) override { return files.write(at,p,n); }
    bool readPrepared(size_t at,void* p,size_t n) override { return files.readPrepared(at,p,n); }
    bool commit(uint64_t seq) override { return files.commit(seq); }
    void abort() override { files.abort(); }
};

void compactBattle(const std::string& root, const std::string& fault) {
    using namespace vpet;
    Store kv; SettingsStore legacy(kv); Settings settings; PetState original;
    original.restore(SpeciesId::Rookie,90,90,90,0,100,0);
    original.profile=profile(); original.rollDna(42);
    original.practice.equipped=1;
    std::string snapshot; assert(CollectionStore::capture(original,settings,snapshot));
    LittleFsCollectionRepository repository((root+"/collection").c_str());
    BattleStorageFaults storageFaults(repository);
    CareJournal journal(kv); CollectionStore store(storageFaults,&journal); CollectionState initial;
    assert(store.migrate(initial,snapshot));
    LittleFsLearningRepository files((root+"/collection/policies").c_str());
    PolicyFaults faults(files); LearningRuntime learning(faults);
    CollectionPanel panel(store,legacy,profile,seed,nullptr,nullptr,&learning);
    Renderer renderer; Panels panels; BleService ble;
    App app(renderer,panels,legacy,ble,learningClock,&panel);
    uint32_t ms=0; app.begin(ms); assert(app.ready());
    auto key=[&](InputEvent e) { ms+=50; app.tick(ms,e); };
    for(int i=0;i<4;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Next); key(InputEvent::Action);
    // A rejected policy preparation must retain a retryable terminal result.
    faults.fail=fault!="collection";
    storageFaults.reject=fault=="collection";
    if(fault=="unreadable") faults.onFailure=[&]() { storageFaults.unreadable=true; };
    for(int i=0;i<128 && !panels.arenaResult;++i) {
        ms+=1500; app.tick(ms,InputEvent::None);
    }
    assert(panels.arenaResult && app.ready()==(fault!="unreadable"));
    assert(learning.policy()->last_sequence()==0);
    storageFaults.unreadable=storageFaults.reject=false;
    if(fault=="unreadable") {
        ms+=1100; app.tick(ms,InputEvent::None);
        assert(app.ready() && learning.policy()->last_sequence()==0);
    }
    PetState saved; assert(store.readPet(panel.state(),panel.state().active,saved,settings));
    assert(saved.battles()==0);
    faults.fail=false;
    key(InputEvent::Action);
    assert(app.ready() && learning.policy()->last_sequence()>0);
    assert(store.readPet(panel.state(),panel.state().active,saved,settings) && saved.battles()==1);
    const auto committed=learning.policy()->last_sequence();
    for(int i=0;i<3;++i) key(InputEvent::None);
    assert(learning.policy()->last_sequence()==committed);
    App reboot(renderer,panels,legacy,ble,learningClock,&panel);
    reboot.begin(ms); assert(reboot.ready());
    assert(store.readPet(panel.state(),panel.state().active,saved,settings) && saved.battles()==1);
}

int main(int argc,char** argv) {
    assert(argc==2 || argc==3);
    if(argc==3) { compactBattle(argv[1],argv[2]); return 0; }
    using namespace vpet;
    const std::string root=argv[1];
    Store kv,bak; SettingsStore legacy(kv,&bak), reserve(bak); Settings settings;
    PetState a,b;
    a.restore(SpeciesId::Rookie,90,90,90,0,100,0); a.rollDna(42); a.profile=profile();
    b=a; b.profile=profile(); b.setSexLocus(b.profile.sex());
    b.sleep.start(learningWall,b.dna()[3]);
    assert(legacy.save(a,settings));
    Settings oldBackup=settings; oldBackup.language="EN"; oldBackup.soundEnabled=false;
    assert(reserve.save(b,oldBackup));
    const int nvsWrites=kv.writes+bak.writes;
    LittleFsCollectionRepository repository((root+"/collection").c_str()); CollectionStore store(repository);
    LittleFsLearningRepository files((root+"/collection/policies").c_str()); PolicyFaults faults(files);
    LearningRuntime learning(faults);
    CollectionPanel panel(store,legacy,profile,seed,nullptr,nullptr,&learning);
    // Legacy snapshots are validated, but the confirmed candidate uses live RAM.
    a.setHunger(88); a.addEv(CombatStat::Def,3);
    assert(panel.load(a,settings)==CollectionLoad::Missing);
    panel.open(); panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.enabled()); PetState saved; Settings savedSettings;
    assert(store.readPet(panel.state(),0,saved,savedSettings));
    assert(saved.hunger()==88 && saved.evAt(CombatStat::Def)==3);
    assert(kv.writes+bak.writes==nvsWrites);
    Renderer renderer; Panels panels; BleService ble;
    App app(renderer,panels,legacy,ble,learningClock,&panel); uint32_t ms=0;
    app.begin(ms); assert(app.ready());
    auto key=[&](InputEvent event) { ms+=50; app.tick(ms,event); };
    auto home=[&]() { app.begin(ms); assert(app.ready()); };
    // Read-only activity browsing and a cancelled session do not learn.
    for(int i=0;i<2;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action);
    key(InputEvent::Back); key(InputEvent::Next); key(InputEvent::Action);
    assert(learning.policy()->last_sequence()==0);
    home(); for(int i=0;i<2;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action);
    ms+=kTrainingDurationMs; app.tick(ms,InputEvent::None);
    assert(learning.policy()->last_sequence()==1);
    auto event=learning.policy()->event(0);
    assert(event.domain==0 && event.context==0 && event.action==0 && event.reward==52);
    assert(store.readPet(panel.state(),0,saved,savedSettings)); assert(saved.evAt(CombatStat::Off)==6);
    // Technique practice is a distinct learning context and must not bias AUTO.
    home(); for(int i=0;i<4;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action);
    assert(learning.policy()->last_sequence()==2);
    event=learning.policy()->event(1);
    assert(event.domain==1 && event.context==1 && event.action==0);
    assert(learning.policy()->estimate(1,0,0).count==0);
    // Only a confirmed terminal Arena result publishes its executed techniques.
    home(); for(int i=0;i<4;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Next); key(InputEvent::Action);
    const auto beforeArena=learning.policy()->last_sequence();
    for(int i=0;i<32 && learning.policy()->last_sequence()==beforeArena;++i) {
        ms+=1500; app.tick(ms,InputEvent::None);
    }
    assert(learning.policy()->last_sequence()>beforeArena);
    const auto afterArena=learning.policy()->last_sequence();
    for(int i=0;i<3;++i) key(InputEvent::None);
    assert(learning.policy()->last_sequence()==afterArena);
    assert(store.readPet(panel.state(),0,saved,savedSettings)); assert(saved.battles()==1);
    // Starting/acknowledging a journey does not learn. Claim does, once.
    home(); for(int i=0;i<3;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action);
    assert(learning.policy()->last_sequence()==afterArena);
    learningWall+=1800; key(InputEvent::Action);
    assert(learning.policy()->last_sequence()==afterArena+1);
    event=learning.policy()->event(learning.policy()->history_size()-1);
    assert(event.domain==2 && event.context==0 && event.action==0 && event.reward==50);
    key(InputEvent::Action); assert(learning.policy()->last_sequence()==afterArena+1);
    // The collection's development EVO option never changes a slot's life.
    home(); const auto beforeEvo=panel.state().sequence;
    for(int i=0;i<8;++i) key(InputEvent::Next); key(InputEvent::Action);
    for(int i=0;i<7;++i) key(InputEvent::Next); key(InputEvent::Action);
    assert(panel.state().sequence==beforeEvo && panel.state().slots[0].form==0);
    // Shared device settings survive switching and reboot (not inactive settings).
    assert(store.readPet(panel.state(),0,a,settings)); settings.language="ES"; settings.soundEnabled=true;
    panel.open(); panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.state().active==1 && learning.policy()->last_sequence()==0);
    assert(panel.load(a,settings)==CollectionLoad::Loaded && settings.language=="ES" && settings.soundEnabled);
    assert(a.sleep.asleep); // A frozen inactive sleeper remains reachable.
    home(); for(int i=0;i<5;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action);
    assert(store.readPet(panel.state(),1,a,settings) && !a.sleep.asleep);
    // Explicit breeding publishes inherited bias, with no copied events/counts.
    panel.open(); for(int i=0;i<5;++i) panel.input(InputEvent::Next,a,settings,{});
    panel.input(InputEvent::Action,a,settings,{}); panel.input(InputEvent::Action,a,settings,{});
    panel.input(InputEvent::Next,a,settings,{}); panel.input(InputEvent::Action,a,settings,{}); confirm(panel,a,settings);
    assert(panel.state().count()==3 && panel.state().slots[2].learningRef[0]);
    LearningRuntime child(files); assert(child.load(panel.state().slots[2]));
    assert(child.policy()->last_sequence()==0 && child.policy()->history_size()==0);
    assert(child.policy()->estimate(0,0,0).bias==25 && child.policy()->estimate(0,0,0).count==0);
    // A policy storage failure rolls training back and blocks further input.
    home(); assert(store.readPet(panel.state(),1,saved,savedSettings));
    const int beforeEnergy=saved.energy(); const int beforeEv=saved.evAt(CombatStat::Off);
    for(int i=0;i<2;++i) key(InputEvent::Next);
    key(InputEvent::Action); key(InputEvent::Action); key(InputEvent::Action);
    faults.fail=true; ms+=kTrainingDurationMs; app.tick(ms,InputEvent::None);
    assert(!app.ready() && learning.policy()->last_sequence()==0);
    assert(store.readPet(panel.state(),1,saved,savedSettings));
    assert(saved.energy()==beforeEnergy && saved.evAt(CombatStat::Off)==beforeEv);
    faults.fail=false; home(); assert(learning.policy()->last_sequence()==0);
    assert(kv.writes+bak.writes==nvsWrites);
    // Founders hatch fast, preserving even zero DNA, identity and shared items.
    PetState founder; founder.profile=profile(); founder.restoreItems(0,0,0,0,0,0);
    assert(store.addFounder(const_cast<CollectionState&>(panel.state()),founder,settings,true));
    assert(store.activate(const_cast<CollectionState&>(panel.state()),3,a,settings,{},true));
    home(); const auto founderId=founder.profile.petId();
    ms+=2001; app.tick(ms,InputEvent::None);
    assert(store.readPet(panel.state(),3,saved,savedSettings));
    const uint8_t zeros[4]={0,0,0,0};
    assert(saved.species()==SpeciesId::Baby && saved.profile.petId()==founderId && !std::memcmp(saved.dna(),zeros,4));
    assert(learning.policy()->last_sequence()==0);
}
