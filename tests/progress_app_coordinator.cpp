#define main collection_baseline_main
#include "collection_app.cpp"
#undef main
#include <iostream>
#include <sys/time.h>

uint64_t coordinatorWall=1791979200;
uint64_t coordinatorClock() { return coordinatorWall; }
int clockWrites=0;
bool clockWorker=false;
int coordinatorSetTime(const timeval* clock,const void*) {
    assert(clockWorker); ++clockWrites; coordinatorWall=clock->tv_sec; return 0;
}

struct CoordinatorTask : vpet::SaveTask {
    Work work=nullptr;
    void* context=nullptr;
    bool done=false, executing=false, reject=false;
    int starts=0, waits=0;
    bool start(Work next, void* value) override {
        assert(!work);
        ++starts;
        if(reject) return false;
        work=next; context=value; return true;
    }
    bool finished() const override { return done; }
    void reset() override { assert(done); work=nullptr; context=nullptr; done=false; }
    void complete() {
        assert(work && !done); executing=clockWorker=true;
        work(context); executing=clockWorker=false; done=true;
    }
    void wait() override { ++waits; if(work && !done) complete(); }
    void access() const { assert(!work || done || executing); }
};

struct CoordinatorKv : Store {
    CoordinatorTask& task;
    explicit CoordinatorKv(CoordinatorTask& value) : task(value) {}
    int32_t getInt(const char* k,int32_t f) override { task.access(); return Store::getInt(k,f); }
    std::string getString(const char* k,const char* f) override { task.access(); return Store::getString(k,f); }
    bool putInt(const char* k,int32_t v) override { task.access(); return Store::putInt(k,v); }
    bool putString(const char* k,const char* v) override { task.access(); return Store::putString(k,v); }
    bool sync() override { task.access(); return Store::sync(); }
};

struct CoordinatorRepository : Repository {
    CoordinatorTask& task;
    bool (*interrupt)(void*)=nullptr;
    void* context=nullptr;
    int begins=0;
    explicit CoordinatorRepository(CoordinatorTask& value) : task(value) {}
    vpet::CollectionRead size(size_t& n) override { task.access(); return Repository::size(n); }
    bool read(size_t at,void* out,size_t n) override { task.access(); return Repository::read(at,out,n); }
    bool begin(uint64_t seq,size_t n) override {
        task.access(); ++begins;
        return !interrupted() && Repository::begin(seq,n);
    }
    bool write(size_t at,const void* in,size_t n) override {
        task.access(); return !interrupted() && Repository::write(at,in,n);
    }
    bool commit(uint64_t seq) override { task.access(); return !interrupted() && Repository::commit(seq); }
    void setInterrupt(bool (*fn)(void*),void* arg) override { interrupt=fn; context=arg; }
    bool interrupted() const override { return interrupt && interrupt(context); }
};

struct CoordinatorPolicies : vpet::LearningRepository {
    CoordinatorTask& task;
    std::map<std::string,std::string> files;
    int prepares=0;
    bool (*interrupt)(void*)=nullptr;
    void* context=nullptr;
    explicit CoordinatorPolicies(CoordinatorTask& value) : task(value) {}
    bool read(const std::string&,const char* ref,std::string& record) override {
        task.access(); record=files[ref]; return !record.empty();
    }
    bool prepare(const std::string&,const vpet::LearningState& policy,std::string& ref) override {
        task.access(); ++prepares;
        if(interrupted()) return false;
        ref="policy"+std::to_string(prepares); files[ref]=policy.encode(); return true;
    }
    void setInterrupt(bool (*fn)(void*),void* arg) override { interrupt=fn; context=arg; }
    bool interrupted() const override { return interrupt && interrupt(context); }
};

struct CoordinatorPanel : vpet::CollectionPanel {
    CoordinatorTask& task;
    int inputs=0, frames=0;
    bool rejectRecovery=false;
    using CollectionPanel::input;
    CoordinatorPanel(vpet::CollectionStore& store,vpet::SettingsStore& legacy,
                     vpet::LearningRuntime& learning,CoordinatorTask& value)
        : CollectionPanel(store,legacy,profile,seed,nullptr,nullptr,&learning), task(value) {}
    bool input(vpet::InputEvent e,vpet::PetState& p,vpet::Settings& s,const vpet::CollectionSwitchGuard& g) override {
        task.access();
        if(e==vpet::InputEvent::Action && page()==Page::List) assert(task.executing);
        ++inputs; return CollectionPanel::input(e,p,s,g);
    }
    void draw(const char*) override { task.access(); ++frames; }
    bool accumulate(uint32_t ms,bool paused) override { task.access(); return CollectionPanel::accumulate(ms,paused); }
    bool recoverRejectedSave() override {
        assert(task.executing);
        return !rejectRecovery && CollectionPanel::recoverRejectedSave();
    }
    int chooseAuto(const vpet::practice::Fighter& f,uint8_t mask) const override {
        task.access(); return CollectionPanel::chooseAuto(f,mask);
    }
};

struct Fixture {
    CoordinatorTask task;
    CoordinatorKv kv{task};
    vpet::SettingsStore legacy{kv};
    CoordinatorRepository repository{task};
    vpet::CareJournal journal{kv};
    vpet::CollectionStore store;
    CoordinatorPolicies policies{task};
    vpet::LearningRuntime learning{policies};
    CoordinatorPanel collection{store,legacy,learning,task};
    vpet::Renderer renderer;
    vpet::Panels panels;
    vpet::BleService ble;
    vpet::App app{renderer,panels,legacy,ble,coordinatorClock,&collection,&task};
    uint32_t ms=0;
    explicit Fixture(bool progress=true) : store(repository,&journal,progress) {
        vpet::PetState p; vpet::Settings settings;
        p.restore(vpet::SpeciesId::Rookie,40,90,80,0,100,0);
        p.rollDna(42); p.profile=profile();
        std::string snapshot;
        assert(vpet::CollectionStore::capture(p,settings,snapshot));
        vpet::CollectionState initial; assert(store.migrate(initial,snapshot));
        simulatedMillis=0; app.begin(0); assert(app.ready());
    }
    void key(vpet::InputEvent e,uint32_t delta=50) { ms+=delta; simulatedMillis=ms; app.tick(ms,e); }
    void complete(vpet::InputEvent e=vpet::InputEvent::None) { task.complete(); key(e); }
    void drain() { for(int i=0;task.work && i<20;++i) complete(); assert(!task.work); }
    void menu(int n) { for(int i=0;i<n;++i) key(vpet::InputEvent::Next); key(vpet::InputEvent::Action); }
    vpet::PetState saved(vpet::Settings* out=nullptr) {
        task.access(); vpet::PetState p; vpet::Settings s;
        assert(store.readPet(collection.state(),collection.state().active,p,s));
        if(out) *out=s;
        return p;
    }
};

void settingsAsync() {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next);
    const auto generation=f.repository.sequence;
    f.key(InputEvent::Action);
    assert(f.task.starts==1 && !f.app.ready());
    assert(f.collection.progressCount()==0 && f.policies.prepares==0);
    f.complete(); assert(f.app.ready());
    Settings s; f.saved(&s); assert(s.language=="EN");
    assert(f.repository.sequence==generation && f.task.waits==0);
}

void trainingQueue() {
    using namespace vpet;
    Fixture f; f.menu(2); f.key(InputEvent::Action); f.key(InputEvent::Action);
    f.key(InputEvent::None,kTrainingDurationMs);
    assert(f.task.starts==1 && !f.app.ready());
    assert(!f.panels.trainingSaving && f.panels.trainingResultFrames>0);
    const auto frames=f.panels.trainingFrames;
    for(auto e : {InputEvent::Next,InputEvent::Next,InputEvent::Action,InputEvent::Next}) f.key(e);
    assert(f.panels.trainingFrames>frames && f.task.starts==1);
    f.complete(InputEvent::Next);
    assert(f.saved().evAt(CombatStat::Off)==6 && f.learning.policy()->last_sequence()==1);
    f.key(InputEvent::Action); // Back was selected by the completion-tick input.
    f.key(InputEvent::Action); f.key(InputEvent::Action);
    f.key(InputEvent::None,kTrainingDurationMs);
    assert(f.task.starts==2); f.complete();
    assert(f.saved().evAt(CombatStat::Off)==12 && f.learning.policy()->last_sequence()==2);
    assert(f.task.waits==0);
}

void orderedQueue(bool overflow) {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next); f.key(InputEvent::Action);
    for(int i=0;i<(overflow?9:8);++i) f.key(InputEvent::Action);
    assert(f.task.starts==1);
    f.drain();
    Settings s; f.saved(&s);
    assert(f.task.starts==9 && s.language=="EN" && f.app.ready());
    assert(f.task.waits==0 && f.repository.commits==1);
    assert((Serial.output.find("VPET_PROGRESS_INPUT rejected=capacity")!=std::string::npos)==overflow);
}

void careAsync(bool reject) {
    using namespace vpet;
    Fixture f; f.menu(1); f.key(InputEvent::Action);
    assert(f.task.starts==1 && !f.app.ready() && f.renderer.hunger==60);
    const auto changes=f.renderer.frameChanges;
    f.key(InputEvent::None,150); f.key(InputEvent::None,150);
    assert(f.renderer.frameChanges>changes);
    f.kv.rejectCommit=reject; f.complete();
    assert(f.app.ready());
    const auto p=f.saved();
    assert(p.hunger()==(reject?40:60) && p.meals()==(reject?0:1));
    assert(f.repository.commits==1 && f.policies.prepares==0);
    if(reject) assert(f.panels.errors>0);
}

void repeatedFood(bool reject) {
    using namespace vpet;
    Fixture f; f.menu(1); f.key(InputEvent::Next); // Protein, initially energy 90.
    f.key(InputEvent::Action);
    assert(f.task.starts==1 && !f.app.ready());
    // Queue reopening Feeding, selecting protein and consuming another portion.
    f.key(InputEvent::Action); f.key(InputEvent::Next); f.key(InputEvent::Action);
    f.complete(); f.drain();
    auto p=f.saved();
    assert(f.task.starts==2 && p.energy()==100 && p.weight()==14);
    f.key(InputEvent::Action); f.key(InputEvent::Next); f.key(InputEvent::Action);
    assert(f.task.starts==3 && !f.app.ready());
    f.kv.rejectCommit=reject;
    f.complete();
    p=f.saved();
    assert(p.energy()==100 && p.weight()==(reject?14:16));
    assert(p.evAt(CombatStat::Off)==0 && f.task.waits==0);
    if(reject) assert(f.panels.errors>0);
    assert(f.repository.commits==1); // Small durable receipts, no full checkpoint.
    CareJournal rebootJournal(f.kv);
    CollectionStore reboot(f.repository,&rebootJournal,true); CollectionState state;
    assert(reboot.load(state)==CollectionLoad::Loaded);
    Settings s; PetState recovered;
    assert(reboot.readPet(state,state.active,recovered,s));
    assert(recovered.weight()==p.weight() && recovered.energy()==p.energy());
}

void rejectedSettings() {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next); f.key(InputEvent::Action);
    f.kv.rejectCommit=true; f.complete();
    Settings s; f.saved(&s); assert(s.language=="ES" && f.app.ready());
    f.kv.rejectCommit=false; f.key(InputEvent::Action); f.complete();
    f.saved(&s); assert(s.language=="EN");
}

void rejectedTraining() {
    using namespace vpet;
    Fixture f; f.menu(2); f.key(InputEvent::Action); f.key(InputEvent::Action);
    f.key(InputEvent::None,kTrainingDurationMs);
    f.kv.rejectCommit=true; f.complete();
    assert(f.app.ready() && f.saved().evAt(CombatStat::Off)==0);
    assert(f.learning.policy()->last_sequence()==0);
    f.kv.rejectCommit=false; f.key(InputEvent::Action); f.complete();
    assert(f.saved().evAt(CombatStat::Off)==6 && f.learning.policy()->last_sequence()==1);
}

void pendingReceipt() {
    using namespace vpet;
    Fixture f; f.menu(2); f.key(InputEvent::Action); f.key(InputEvent::Action);
    f.key(InputEvent::None,kTrainingDurationMs);
    f.kv.foodFault=1; f.complete();
    assert(!f.app.ready() && f.learning.policy()->last_sequence()==1);
    f.key(InputEvent::None,1000);
    assert(f.task.starts==2); f.complete();
    assert(!f.app.ready() && f.learning.policy()->last_sequence()==1);
    f.kv.foodFault=0; f.kv.replayFault=false;
    f.key(InputEvent::None,1000); f.complete();
    assert(f.app.ready() && f.saved().evAt(CombatStat::Off)==6);
    assert(f.learning.policy()->last_sequence()==1 && f.repository.commits==1);
}

void maintenance() {
    using namespace vpet;
    Fixture f;
    f.key(InputEvent::None,5000);
    assert(f.task.starts==1 && !f.app.ready());
    const auto draws=f.renderer.draws, frames=f.panels.trainingFrames;
    const auto generation=f.repository.sequence;
    f.key(InputEvent::Next);
    assert(f.renderer.draws==draws && f.panels.trainingFrames==frames);
    f.complete();
    assert(f.repository.sequence==generation && f.collection.dirty() && f.app.ready());
    assert(f.panels.errors==0 && f.renderer.menuIndex==1);
    f.key(InputEvent::None,5000);
    assert(f.task.starts==2 && !f.app.ready()); f.complete();
    assert(f.repository.sequence==generation+1 && f.app.ready());
}

void sleepMaintenance() {
    using namespace vpet;
    Fixture f; f.menu(5); f.key(InputEvent::Action);
    assert(f.task.starts==1 && f.renderer.sleeping);
    f.complete(); assert(f.task.starts==2 && !f.app.ready());
    f.complete(); assert(f.app.ready() && f.saved().sleep.asleep);
}

void collectionWorker() {
    using namespace vpet;
    Fixture f; f.menu(8);
    for(int i=0;i<option_menu::slot(option_menu::collection);++i) f.key(InputEvent::Next);
    f.key(InputEvent::Action);
    assert(f.collection.page()==CollectionPanel::Page::List);
    f.key(InputEvent::Next); assert(!f.task.work); // Pure cursor navigation stays on main.
    f.key(InputEvent::Action); assert(f.task.starts==1 && !f.app.ready());
    const auto frames=f.collection.frames;
    f.key(InputEvent::Next); assert(f.collection.frames==frames && f.collection.inputs==1);
    f.complete(); assert(f.collection.inputs==3 && f.app.ready());
}

void capacity() {
    using namespace vpet;
    Fixture f;
    auto p=f.saved(); Settings settings;
    RuntimeExperience events[8]; for(auto& e:events) e={0,0,0,1};
    for(int i=0;i<8;++i) assert(f.collection.saveExperience(p,settings,events,8));
    assert(f.collection.progressCount()==64);
    f.menu(8); // Capacity maintenance owns the worker before the first navigation input.
    assert(f.task.starts==1 && !f.app.ready());
    f.drain();
    assert(f.collection.progressCount()==0 && f.learning.policy()->last_sequence()==64);
    assert(f.repository.commits==2 && f.task.waits==0);
}

void stress() {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next);
    for(int i=0;i<512;++i) { f.key(InputEvent::Action); assert(!f.app.ready()); f.complete(); assert(f.app.ready()); }
    assert(f.task.starts==512 && f.repository.commits==1 && f.policies.prepares==0);
    Settings s; f.saved(&s); assert(s.language=="ES");
}

void explorationAsync(bool reject) {
    using namespace vpet;
    Fixture f; f.menu(3); f.key(InputEvent::Action); f.key(InputEvent::Action);
    assert(f.task.starts==1 && !f.app.ready() && f.panels.away);
    f.complete(); assert(f.saved().exploration.away());
    const int energy=f.saved().energy();
    coordinatorWall+=1800;
    f.key(InputEvent::Action); assert(f.task.starts==2 && !f.app.ready());
    assert(f.panels.explorePage==ExplorationSession::Page::Receipt);
    f.kv.rejectCommit=reject; f.complete();
    auto p=f.saved();
    assert(p.exploration.away()==reject && p.exploration.hasReceipt()!=reject);
    assert(f.learning.policy()->last_sequence()==(reject?0:1));
    if(reject) {
        assert(p.energy()==energy);
        f.kv.rejectCommit=false; f.key(InputEvent::Action); f.complete();
        p=f.saved(); assert(!p.exploration.away() && p.exploration.hasReceipt());
    }
    const auto rewardEnergy=p.energy();
    f.key(InputEvent::Action); assert(!f.app.ready()); f.complete();
    p=f.saved(); assert(!p.exploration.hasReceipt() && p.energy()==rewardEnergy);
    assert(f.learning.policy()->last_sequence()==1 && f.repository.commits==1);
}

void battleAsync(bool reject) {
    using namespace vpet;
    Fixture f; f.menu(4); f.key(InputEvent::Next); f.key(InputEvent::Action);
    for(int i=0;i<128 && !f.task.work;++i) f.key(InputEvent::None,1500);
    assert(f.task.starts==1 && f.panels.arenaResult && !f.app.ready());
    f.kv.rejectCommit=reject; f.complete();
    auto p=f.saved();
    assert(p.battles()==(reject?0:1));
    if(reject) {
        assert(f.learning.policy()->last_sequence()==0);
        f.kv.rejectCommit=false; f.key(InputEvent::Action); f.complete();
        p=f.saved(); assert(p.battles()==1);
    }
    assert(f.learning.policy()->last_sequence()>0 && f.repository.commits==1);
    assert(f.policies.prepares==0);
}

void clockAsync(bool reject) {
    using namespace vpet;
    Fixture f; f.menu(8);
    for(int i=0;i<6;++i) f.key(InputEvent::Next);
    f.key(InputEvent::Action);
    for(int i=0;i<4;++i) f.key(InputEvent::Next);
    f.key(InputEvent::Action);
    assert(f.task.starts==1 && !f.app.ready() && clockWrites==0);
    f.kv.rejectCommit=reject; f.complete();
    assert(clockWrites==(reject?0:1) && f.app.ready());
}

void warningPersists() {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next); f.key(InputEvent::Action);
    f.kv.rejectCommit=true; f.complete();
    assert(f.panels.errorVisible);
    const auto errors=f.panels.errors;
    f.key(InputEvent::Next,100);
    assert(f.panels.errors>errors && f.panels.panelIndex==2 && f.panels.errorVisible);
    f.key(InputEvent::None,1000); assert(f.panels.errorVisible);
    // The input was processed even while the warning remains visible.
    f.kv.rejectCommit=false; f.key(InputEvent::Action); f.complete();
    Settings s; f.saved(&s); assert(!s.soundEnabled && s.language=="ES");
    f.key(InputEvent::None,2100); assert(!f.panels.errorVisible);
}

void legacyUnchanged() {
    using namespace vpet;
    Fixture f(false); f.menu(8); f.key(InputEvent::Next); f.key(InputEvent::Action);
    assert(!f.task.work && f.task.starts==0 && f.app.ready());
    Settings s; f.saved(&s); assert(s.language=="ES");
}

void permanentFailureBackHome(bool accepted, bool duringRetry) {
    using namespace vpet;
    Fixture f; f.menu(8); f.key(InputEvent::Next); f.key(InputEvent::Action);
    if (accepted) f.kv.foodFault=1;
    else { f.kv.rejectCommit=true; f.collection.rejectRecovery=true; }
    f.complete(); assert(!f.app.ready() && !f.task.work);
    // This mutation must keep its original Options context ahead of BACK.
    f.key(InputEvent::Action);
    if (duringRetry) {
        f.key(InputEvent::None,1000);
        assert(f.task.work);
    }
    const auto errors=f.panels.errors;
    const auto draws=f.renderer.draws;
    f.key(InputEvent::Back);
    if (duringRetry) f.complete();
    assert(f.renderer.draws>draws && !f.app.ready());
    assert(f.panels.errors==errors); // The recovery warning must not cover Home again.
    for (int i=0;i<3;++i) {
        f.key(InputEvent::None,1000); assert(f.task.work);
        f.complete();
        assert(!f.app.ready() && f.panels.errors==errors);
    }
    const auto steadyDraws=f.renderer.draws;
    f.key(InputEvent::None,100);
    assert(f.renderer.draws>steadyDraws && f.task.waits==0);
    assert(f.learning.policy()->last_sequence()==0 && f.repository.commits==1);

    f.kv.rejectCommit=false; f.kv.foodFault=0; f.kv.replayFault=false;
    f.collection.rejectRecovery=false;
    f.key(InputEvent::None,1000); f.complete();
    assert(f.task.work); // The queued Options ACTION is persisted exactly once.
    f.drain(); assert(f.app.ready());
    Settings settings; f.saved(&settings);
    assert(settings.language==(accepted?"ES":"EN"));
    const auto starts=f.task.starts;
    f.key(InputEvent::Action); // Home's cursor still points at Options.
    assert(f.panels.lastPanel==PanelId::Options && f.task.starts==starts);
}

int main(int argc,char** argv) {
    assert(argc==2);
    const std::string scenario=argv[1];
    if(scenario=="settings") settingsAsync();
    else if(scenario=="training_queue") trainingQueue();
    else if(scenario=="queue") orderedQueue(false);
    else if(scenario=="overflow") orderedQueue(true);
    else if(scenario=="care") careAsync(false);
    else if(scenario=="care_reject") careAsync(true);
    else if(scenario=="food_repeat") repeatedFood(false);
    else if(scenario=="food_repeat_reject") repeatedFood(true);
    else if(scenario=="settings_reject") rejectedSettings();
    else if(scenario=="training_reject") rejectedTraining();
    else if(scenario=="accepted_pending") pendingReceipt();
    else if(scenario=="maintenance") maintenance();
    else if(scenario=="sleep") sleepMaintenance();
    else if(scenario=="collection") collectionWorker();
    else if(scenario=="capacity") capacity();
    else if(scenario=="stress") stress();
    else if(scenario=="explore") explorationAsync(false);
    else if(scenario=="explore_reject") explorationAsync(true);
    else if(scenario=="battle") battleAsync(false);
    else if(scenario=="battle_reject") battleAsync(true);
    else if(scenario=="clock") clockAsync(false);
    else if(scenario=="clock_reject") clockAsync(true);
    else if(scenario=="warning") warningPersists();
    else if(scenario=="legacy") legacyUnchanged();
    else if(scenario=="permanent_back_rejected_idle") permanentFailureBackHome(false,false);
    else if(scenario=="permanent_back_rejected_retry") permanentFailureBackHome(false,true);
    else if(scenario=="permanent_back_accepted_idle") permanentFailureBackHome(true,false);
    else if(scenario=="permanent_back_accepted_retry") permanentFailureBackHome(true,true);
    else assert(false);
    std::cout<<"PROGRESS_COORDINATOR_OK\n";
}
