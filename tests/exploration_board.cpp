#include <cassert>
#include <iostream>
#include <map>
#include <cstdlib>
#include <vector>
#include "vpet/Exploration.h"
#include "vpet/SettingsStore.h"
#include "vpet/StateSnapshot.h"
#include "vpet/TrainingSession.h"

using namespace vpet;
constexpr uint64_t now = 1791979200;
struct Store : KeyValueStore {
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    StoreCommit result = StoreCommit::Committed;
    bool blocked = false;
    int cut = -1, writes = 0;
    bool writing() { if (cut >= 0 && writes++ == cut) throw 1; return !blocked; }
    int32_t getInt(const char* k, int32_t f) override { return ints.count(k) ? ints[k] : f; }
    std::string getString(const char* k, const char* f) override { return strings.count(k) ? strings[k] : f; }
    bool putInt(const char* k, int32_t v) override { if (!writing()) return false; ints[k]=v; return true; }
    bool putString(const char* k, const char* v) override { if (!writing()) return false; strings[k]=v; return true; }
    StoreCommit commitString(const char* k, const char* v) override {
        if (result == StoreCommit::Rejected) return result;
        if (!putString(k,v)) return StoreCommit::Rejected;
        if (result == StoreCommit::Pending) blocked = true;
        return result;
    }
};
PetState pet() {
    PetState p; p.evolveTo(SpeciesId::Rookie);
    p.setHunger(70); p.setEnergy(70); p.setHappiness(70); return p;
}
void rules() {
    PetState egg; assert(!egg.exploration.start(egg,ExploreRoute::Patio,CombatStat::Off,now));
    auto p=pet(); auto& e=p.exploration;
    assert(!e.start(p,static_cast<ExploreRoute>(3),CombatStat::Off,now));
    assert(!e.start(p,ExploreRoute::Jornada,static_cast<CombatStat>(6),now));
    assert(e.start(p,ExploreRoute::Patio,CombatStat::Off,now));
    assert(!e.start(p,ExploreRoute::Patio,CombatStat::Off,now));
    assert(e.remaining(now-1)==1800 && e.preview(p,now-1).energy==0);
    p.setHunger(0); assert(e.preview(p,now+1800).energy==25);
    assert(e.claim(p,now+1800) && p.energy()==95 && e.hasReceipt());
    const auto receipt=e.encode(); assert(!e.claim(p,now+99999) && receipt==e.encode());
    e.acknowledge(); assert(!e.hasReceipt()); p.setHunger(70);
    for (int i=0;i<6;++i) {
        assert(e.start(p,ExploreRoute::Jornada,CombatStat::Off,now));
        assert(e.claim(p,now+28800));
    }
    assert(p.evAt(CombatStat::Off)==8 && e.weekEv==8 && e.guide);
    const uint64_t week=e.week;
    e.start(p,ExploreRoute::Jornada,CombatStat::Off,now-604800);
    assert(e.preview(p,now-604800+28800).ev==0);
    e.claim(p,now-604800+28800); assert(e.week==week);
    e.start(p,ExploreRoute::Jornada,CombatStat::Off,now+604800);
    assert(e.preview(p,now+604800+28800).ev==2); e.claim(p,now+604800+28800);
    assert(e.weekEv==2);
    const auto conserved=e.encode();
    p.evolveTo(SpeciesId::Champion); assert(p.exploration.encode()==conserved);
    p=pet();
    for (int i=0;i<2;++i) {
        assert(p.exploration.start(p,ExploreRoute::Noche,CombatStat::Hp,now));
        auto r=p.exploration.preview(p,now+28800);
        assert(r.learning==1 && r.learned==(i==1));
        p.exploration.claim(p,now+28800);
    }
    assert(p.practice.flameLearned() && p.practice.equipped==5);
    for (int i=0;i<3;++i) {
        p.exploration.start(p,ExploreRoute::Noche,CombatStat::Hp,now);
        p.exploration.claim(p,now+28800);
    }
    assert(p.practice.mastery[1]==4 && p.exploration.weekMastery==4);
    p.exploration.guide=true; p.evolveTo(SpeciesId::Champion); assert(p.exploration.guide);
    p.resetToEgg(); assert(p.exploration.encode()==Exploration().encode());
}
void codec() {
    auto p=pet(); auto& e=p.exploration;
    e.clockCheckpoint=UINT64_C(9007199254740991);
    e.start(p,ExploreRoute::Noche,CombatStat::Off,now);
    Exploration restored; assert(restored.decode(e.encode())); assert(restored.encode()==e.encode());
    assert(restored.clockCheckpoint==e.clockCheckpoint);
    e.claim(p,now+28800); assert(restored.decode(e.encode()) && restored.hasReceipt());
    const auto valid=restored.encode();
    for (auto bad : {std::string("2,0"), valid+",0", valid+"\n", std::string("1,-1"), valid.substr(0,valid.size()-1)}) {
        assert(!restored.decode(bad)); assert(restored.encode()==valid);
    }
    std::vector<std::string> fields; std::istringstream input(valid); std::string field;
    while (std::getline(input,field,',')) fields.push_back(field);
    for (const auto mutation : {std::make_pair(0,"2"), std::make_pair(1,"99999999999999999999"),
         std::make_pair(2,"9"), std::make_pair(3,"5"), std::make_pair(6,"9007199254740992"),
         std::make_pair(7,"1"), std::make_pair(8,"3"), std::make_pair(9,"6"),
         std::make_pair(17,"0"), std::make_pair(19,"1"), std::make_pair(20,"1")}) {
        auto bad=fields; bad[mutation.first]=mutation.second;
        std::string record;
        for (size_t i=0;i<bad.size();++i) { if (i) record+=','; record+=bad[i]; }
        assert(!restored.decode(record)); assert(restored.encode()==valid);
    }
    assert(restored.decode("") && restored.encode()==Exploration().encode());
}
void persistence() {
    Store kv, backup; Settings s; SettingsStore db(kv,&backup); auto p=pet();
    p.exploration.clockCheckpoint=now;
    p.exploration.start(p,ExploreRoute::Jornada,CombatStat::Off,now);
    assert(db.save(p,s)); const auto trip=p.exploration.encode();
    PetState loaded; assert(db.load(loaded,s)==LoadResult::Loaded && loaded.exploration.encode()==trip);
    auto before=p; p.exploration.claim(p,now+28800);
    kv.result=StoreCommit::Rejected;
    assert(!db.save(p,s)); p=before;
    assert(db.load(loaded,s)==LoadResult::Loaded && loaded.exploration.encode()==trip);
    p.exploration.claim(p,now+28800); const auto receipt=p.exploration.encode();
    kv.result=StoreCommit::Pending; assert(db.save(p,s));
    kv.blocked=false; kv.result=StoreCommit::Committed;
    assert(db.load(loaded,s)==LoadResult::Loaded && loaded.exploration.encode()==receipt);
    assert(loaded.evAt(CombatStat::Off)==2 && !loaded.exploration.claim(loaded,now+28800));
    assert(db.swapOrPark(p,s) && !p.exploration.hasReceipt());
    assert(db.swapOrPark(p,s) && p.exploration.encode()==receipt);
    storage::SnapshotStore snapshot; snapshot.ints=kv.ints; snapshot.strings=kv.strings;
    auto v2=storage::encodeSnapshot(snapshot); assert(v2.substr(0,2)=="3\n");
    v2.replace(0,1,"2");
    for (const auto key : {"techM3", "techM4"}) {
        const auto start=v2.find(std::string(key)+" ");
        assert(start!=std::string::npos);
        v2.erase(start,v2.find('\n',start)-start+1);
    }
    const auto pos=v2.rfind(receipt+"\nEND\n"); assert(pos!=std::string::npos);
    auto v1=v2; v1.replace(0,1,"1"); v1.erase(pos,receipt.size()+1);
    kv.strings["saveTx"]=v1;
    assert(db.load(loaded,s)==LoadResult::Loaded && loaded.exploration.encode()==receipt);
    kv.strings.erase("expState");
    assert(db.load(loaded,s)==LoadResult::Loaded && loaded.exploration.encode()==Exploration().encode());
    kv.strings["expState"]="99,future";
    assert(db.load(loaded,s)==LoadResult::Unsupported);
    Store empty; SettingsStore fresh(empty); auto departure=pet(); auto atHome=departure;
    departure.exploration.start(departure,ExploreRoute::Patio,CombatStat::Off,now);
    empty.result=StoreCommit::Rejected;
    assert(!fresh.save(departure,s)); departure=atHome;
    assert(!departure.exploration.away());
    departure.exploration.start(departure,ExploreRoute::Patio,CombatStat::Off,now);
    empty.result=StoreCommit::Pending; assert(fresh.save(departure,s));
    empty.blocked=false;
    assert(fresh.load(loaded,s)==LoadResult::Loaded && loaded.exploration.away());
}
bool reject(PetState&) { return false; }
Store* trainingStore=nullptr;
bool saveTraining(PetState& p) { Settings s; return SettingsStore(*trainingStore).save(p,s); }
void training() {
    auto p=pet(); p.exploration.guide=true;
    const int manual=adopted::indexOf("training_manual"); p.adoptedStock.set(manual,1);
    assert(p.itemCount(7)==1 && p.itemVisible(7) && p.canOpenTrainingManual(7));
    assert(trainingPreviewEv(p,CombatStat::Off,6)==7);
    TrainingSession session;
    session.input(p,InputEvent::Action,0); session.input(p,InputEvent::Action,1);
    session.input(p,InputEvent::None,10001);
    assert(p.evAt(CombatStat::Off)==7 && !p.exploration.guide && p.adoptedStock.count(manual)==1);
    session.rollbackFromSnapshot(p);
    assert(p.evAt(CombatStat::Off)==0 && p.exploration.guide && p.adoptedStock.count(manual)==1);
    try { trainingCommit(p,CombatStat::Off,1,reject); assert(false); } catch (const BatchSaveError&) {}
    assert(p.exploration.guide && p.evAt(CombatStat::Off)==0);
    auto applied=trainingCommit(p,CombatStat::Off,1,nullptr);
    assert(applied.evAdded==7 && !p.exploration.guide && p.adoptedStock.count(manual)==1);
    p.exploration.guide=true; p.setEvAt(CombatStat::Off,246);
    applied=trainingCommit(p,CombatStat::Off,1,nullptr);
    assert(applied.evAdded==6 && p.exploration.guide);
    p=pet(); p.exploration.guidePending=true;
    p.exploration.start(p,ExploreRoute::Jornada,CombatStat::Off,now);
    assert(!p.exploration.preview(p,now+28800).guide);
    assert(trainingPreviewEv(p,CombatStat::Off,0)==0);
    assert(trainingApply(p,CombatStat::Off,1).reps==0);
    Store kv; trainingStore=&kv; Settings s;
    p=pet(); p.exploration.guide=true; assert(SettingsStore(kv).save(p,s));
    kv.result=StoreCommit::Rejected;
    try { trainingCommit(p,CombatStat::Off,1,saveTraining); assert(false); } catch (const BatchSaveError&) {}
    assert(p.exploration.guide && p.evAt(CombatStat::Off)==0);
    kv.result=StoreCommit::Pending;
    assert(trainingCommit(p,CombatStat::Off,1,saveTraining).evAdded==7);
    kv.blocked=false; PetState loaded;
    assert(SettingsStore(kv).load(loaded,s)==LoadResult::Loaded);
    assert(!loaded.exploration.guide && loaded.evAt(CombatStat::Off)==7);
    assert(trainingCommit(loaded,CombatStat::Off,0,nullptr).reps==0);
    trainingStore=nullptr;
}
void interruptions() {
    Store base; Settings s; auto old=pet(); assert(SettingsStore(base).save(old,s));
    for (int mode=0;mode<2;++mode) {
      auto next=old; next.exploration.start(next,ExploreRoute::Jornada,CombatStat::Off,now);
      if (mode) next.exploration.claim(next,now+28800);
      for (int cut=0;cut<90;++cut) {
        auto kv=base; kv.cut=cut;
        try { SettingsStore(kv).save(next,s); } catch (int) {}
        const bool committed=!kv.getString("saveTx","").empty() || kv.getString("expState","")==next.exploration.encode();
        kv.cut=-1; PetState loaded;
        assert(SettingsStore(kv).load(loaded,s)==LoadResult::Loaded);
        const auto& expected=committed ? next : old;
        assert(loaded.exploration.encode()==expected.exploration.encode());
        assert(loaded.evAt(CombatStat::Off)==expected.evAt(CombatStat::Off));
      }
    }
    auto active=old, parked=old;
    active.exploration.start(active,ExploreRoute::Jornada,CombatStat::Off,now);
    parked.exploration.start(parked,ExploreRoute::Noche,CombatStat::Off,now);
    parked.exploration.claim(parked,now+28800);
    Store live, backup;
    assert(SettingsStore(live).save(active,s)); assert(SettingsStore(backup).save(parked,s));
    for (int cut=0;cut<90;++cut) {
        auto a=live,b=backup; a.cut=cut; auto p=active;
        SettingsStore db(a,&b);
        try { db.swapOrPark(p,s); } catch (int) {}
        const bool committed=a.getString("swapTx","")=="1" || a.getString("expState","")==parked.exploration.encode();
        a.cut=-1; PetState loaded, other;
        assert(db.load(loaded,s)==LoadResult::Loaded);
        assert(SettingsStore(b).load(other,s)==LoadResult::Loaded);
        assert(loaded.exploration.encode()==(committed ? parked : active).exploration.encode());
        assert(other.exploration.encode()==(committed ? active : parked).exploration.encode());
    }
}
int main(int argc,char** argv) {
    const std::string which=argc>1 ? argv[1] : "rules";
    if (which=="rules") rules();
    if (which=="codec") codec();
    if (which=="persistence") persistence();
    if (which=="training") training();
    if (which=="interruptions") interruptions();
    if (which=="vector") {
        auto p=pet(); p.setHunger(std::atoi(argv[4]) ? 70 : 0);
        const std::string profile=argv[5];
        if (profile=="capped") {
            p.setEvAt(CombatStat::Off,251); p.exploration.week=(now+259200)/604800;
            p.exploration.weekEv=7; p.exploration.guide=true;
            p.practice.training=2; p.practice.mastery[1]=99;
        } else if (profile=="mastery") {
            p.practice.training=2; p.exploration.week=(now+259200)/604800;
            p.exploration.weekMastery=3;
        }
        const std::string name=argv[2];
        const auto route=name=="patio" ? ExploreRoute::Patio : name=="jornada" ? ExploreRoute::Jornada : ExploreRoute::Noche;
        p.exploration.start(p,route,CombatStat::Off,now);
        auto r=p.exploration.preview(p,now+std::strtoull(argv[3],nullptr,10));
        std::cout<<r.elapsed<<' '<<r.full<<' '<<int(r.energy)<<' '<<int(r.ev)<<' '<<int(r.mastery)<<' '<<int(r.learning)<<' '<<r.guide<<' '<<r.learned<<'\n';
    }
}
