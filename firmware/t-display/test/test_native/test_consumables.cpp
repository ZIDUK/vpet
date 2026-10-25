#include <unity.h>
#include <map>
#include "vpet/SettingsStore.h"
#include "vpet/PracticeSession.h"
#include "vpet/TrainingSession.h"

namespace {
class ItemStore : public vpet::KeyValueStore {
public:
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    bool failJournal = false, failReplay = false;
    int failAt=-1, writes=0;
    int32_t getInt(const char* k, int32_t d) override { return ints.count(k) ? ints[k] : d; }
    std::string getString(const char* k, const char* d) override { return strings.count(k) ? strings[k] : d; }
    bool putInt(const char* k, int32_t v) override {
        if (++writes==failAt || failReplay) return false;
        ints[k]=v; return true;
    }
    bool putString(const char* k, const char* v) override {
        if (++writes==failAt) return false;
        if (failJournal && std::string(k)=="itemTx") return false;
        if (failReplay && std::string(k)!="itemTx") return false;
        strings[k]=v; return true;
    }
};
}

void test_adopted_runtime() {
    using namespace vpet;
    ItemStore kv;
    SettingsStore store(kv);
    Settings settings;
    PetState pet;
    store.load(pet, settings);
    const int recovery = adopted::indexOf("small_recovery");
    const int manual = adopted::indexOf("training_manual");
    TEST_ASSERT_EQUAL(2, pet.adoptedStock.count(recovery));
    pet.resetToEgg();
    TEST_ASSERT_EQUAL(2, pet.adoptedStock.count(recovery));
    pet.adoptedStock.set(recovery, 0);
    pet.adoptedStock.set(manual, 99);
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.count(manual));
    TEST_ASSERT_TRUE(store.save(pet, settings));
    PetState restored;
    TEST_ASSERT_EQUAL(LoadResult::Loaded, store.load(restored, settings));
    TEST_ASSERT_EQUAL(0, restored.adoptedStock.count(recovery));
    TEST_ASSERT_EQUAL(1, restored.adoptedStock.count(manual));
    TEST_ASSERT_FALSE(restored.itemVisible(8));
    TEST_ASSERT_EQUAL(1, kv.ints["nutVer"]);
    TEST_ASSERT_EQUAL(3, kv.ints["schema"]);

    pet.setHappiness(10);
    pet.evolveTo(SpeciesId::Rookie);
    const int apple = adopted::indexOf("blue_apple");
    const PetState before = pet;
    TEST_ASSERT_EQUAL(ItemUseResult::Used, pet.useItem(8+apple));
    kv.failJournal = true;
    TEST_ASSERT_FALSE(store.commitConsumables(pet));
    pet = before;
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.count(apple));
    kv.failJournal = false;
    TEST_ASSERT_EQUAL(ItemUseResult::Used, pet.useItem(8+apple));
    kv.failReplay = true;
    TEST_ASSERT_TRUE(store.commitConsumables(pet));
    TEST_ASSERT_FALSE(kv.strings["itemTx"].empty());
    kv.failReplay = false;
    TEST_ASSERT_EQUAL(LoadResult::Loaded, store.load(restored, settings));
    TEST_ASSERT_EQUAL(30, restored.happiness());
    TEST_ASSERT_EQUAL(0, restored.adoptedStock.count(apple));
    TEST_ASSERT_TRUE(kv.strings["itemTx"].empty());
    pet.setTrainingSessions(300);
    TEST_ASSERT_TRUE(store.commitConsumables(pet));
    TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(restored,settings));
    TEST_ASSERT_EQUAL(300,restored.trainingSessions());
    kv.strings["itemTx"]="1 0 0\nhunger 20\n";
    TEST_ASSERT_EQUAL(LoadResult::Unsupported,store.load(restored,settings));
    TEST_ASSERT_FALSE(store.commitConsumables(pet));
    TEST_ASSERT_FALSE(store.save(pet,settings));
}

void test_adopted_battle_and_rewards() {
    using namespace vpet;
    PetState pet;
    pet.adoptedStock.seed();
    PracticeSession session;
    session.page = PracticeSession::Page::Arena;
    TEST_ASSERT_EQUAL(4,session.bagCount(pet));
    TEST_ASSERT_EQUAL(adopted::indexOf("small_recovery"),session.bagItemAt(pet,0));
    TEST_ASSERT_EQUAL(adopted::indexOf("mp_floppy"),session.bagItemAt(pet,1));
    TEST_ASSERT_EQUAL(adopted::indexOf("off_disk"),session.bagItemAt(pet,2));
    TEST_ASSERT_EQUAL(-1,session.bagItemAt(pet,3));
    const int recovery = adopted::indexOf("small_recovery");
    TEST_ASSERT_FALSE(session.useItem(pet, recovery));
    session.battle.player.hp = 1;
    {
        const PetState before=pet;
        const PracticeSession previous=session;
        TEST_ASSERT_TRUE(session.useItem(pet,recovery));
        ItemStore kv;
        kv.failJournal=true;
        const bool committed=SettingsStore(kv).commitConsumables(pet);
        TEST_ASSERT_FALSE(committed);
        session.finishSave(pet,before,previous,committed);
        TEST_ASSERT_EQUAL(1,session.battle.player.hp);
        TEST_ASSERT_EQUAL(2,pet.adoptedStock.count(recovery));
    }
    TEST_ASSERT_TRUE(session.useItem(pet, recovery));
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.count(recovery));
    session.battle.player.hp = 0;
    TEST_ASSERT_FALSE(session.useItem(pet, recovery));
    session.battle.result = 1;
    TEST_ASSERT_FALSE(session.useItem(pet, recovery));
    session.award(pet);
    TEST_ASSERT_EQUAL(recovery,session.rewardItem);
    const auto record = pet.adoptedStock.encode();
    session.award(pet);
    TEST_ASSERT_EQUAL_STRING(record.c_str(), pet.adoptedStock.encode().c_str());
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.rewards);
    session.page = PracticeSession::Page::Bag;
    session.tick(pet, 10000);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Arena, session.page);
    // Opening the bag and selecting an item do not issue extra attack orders.
    PracticeSession live;
    live.page=PracticeSession::Page::Arena;
    live.cursor=live.count(pet)-2;
    TEST_ASSERT_EQUAL(-1,live.requestedOrder(pet));
    live.input(pet,InputEvent::Action,0);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Bag,live.page);
    TEST_ASSERT_EQUAL(0,live.battle.round);
    live.nextRoundAt=100;
    live.tick(pet,100);
    TEST_ASSERT_EQUAL(1,live.battle.round);
    const int rounds=live.battle.round;
    live.input(pet,InputEvent::Action,100);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Bag,live.page);
    TEST_ASSERT_EQUAL(rounds,live.battle.round);
    live.cursor=live.count(pet)-1;
    TEST_ASSERT_EQUAL(-1,live.requestedOrder(pet));

    AdoptedInventory stock;
    TEST_ASSERT_EQUAL(recovery,stock.reward());
    TEST_ASSERT_EQUAL(3,stock.cursor);
    stock.set(3,99);
    TEST_ASSERT_EQUAL(4,stock.reward());
    for (int i=0;i<adopted::kCount;++i) stock.set(i,99);
    TEST_ASSERT_EQUAL(-1,stock.reward());
    TEST_ASSERT_EQUAL(2,stock.rewards);
    const auto full=stock.encode();
    TEST_ASSERT_TRUE(stock.decode(full+" unknown_future 90"));
    TEST_ASSERT_EQUAL_STRING(full.c_str(),stock.encode().c_str());
    TEST_ASSERT_FALSE(stock.decode("2 0 0"));
    TEST_ASSERT_FALSE(stock.decode("1 0 0 small_recovery"));
    TEST_ASSERT_EQUAL_STRING(full.c_str(),stock.encode().c_str());
    TEST_ASSERT_TRUE(stock.decode("1 -1 0 small_recovery 2"));
    TEST_ASSERT_EQUAL(0,stock.cursor);
    TEST_ASSERT_TRUE(stock.decode("1 43 0"));
    TEST_ASSERT_EQUAL(3,stock.cursor);

    for (int result=2;result<=3;++result) {
        PracticeSession lost;
        lost.battle.result=result;
        const auto previous=pet.adoptedStock.encode();
        lost.award(pet);
        TEST_ASSERT_EQUAL_STRING(previous.c_str(),pet.adoptedStock.encode().c_str());
    }
}

void test_adopted_manual_rollback() {
    using namespace vpet;
    PetState pet;
    pet.evolveTo(SpeciesId::Rookie);
    const int manual = adopted::indexOf("training_manual");
    pet.adoptedStock.set(manual, 1);
    TrainingSession s;
    s.chosenStat = CombatStat::Off;
    s.repsCompleted = 1;
    s.state = TrainingSession::State::Confirm;
    s.input(pet, InputEvent::Back, 0);
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.count(manual));
    s.state = TrainingSession::State::Confirm;
    s.input(pet, InputEvent::Action, 0);
    TEST_ASSERT_EQUAL(7, pet.evAt(CombatStat::Off));
    TEST_ASSERT_EQUAL(0, pet.adoptedStock.count(manual));
    s.rollbackFromSnapshot(pet);
    TEST_ASSERT_EQUAL(0, pet.evAt(CombatStat::Off));
    TEST_ASSERT_EQUAL(1, pet.adoptedStock.count(manual));
    s.state = TrainingSession::State::Confirm;
    s.input(pet, InputEvent::Action, 0);
    TEST_ASSERT_EQUAL(7, pet.evAt(CombatStat::Off));
    ItemStore kv;
    SettingsStore store(kv);
    Settings settings;
    TEST_ASSERT_TRUE(store.save(pet,settings));
    s.rollbackFromSnapshot(pet);
    TEST_ASSERT_EQUAL(1,pet.adoptedStock.count(manual));
    s.state=TrainingSession::State::Confirm;
    s.input(pet,InputEvent::Action,0);
    kv.failJournal=true;
    TEST_ASSERT_FALSE(store.commitConsumables(pet));
    s.rollbackFromSnapshot(pet);
    TEST_ASSERT_EQUAL(1,pet.adoptedStock.count(manual));
    TEST_ASSERT_EQUAL(0,pet.evAt(CombatStat::Off));
    s.state=TrainingSession::State::Confirm;
    s.input(pet,InputEvent::Action,0);
    kv.failJournal=false;
    kv.failReplay=true;
    TEST_ASSERT_TRUE(store.commitConsumables(pet));
    kv.failReplay=false;
    PetState restored;
    TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(restored,settings));
    TEST_ASSERT_EQUAL(7,restored.evAt(CombatStat::Off));
    TEST_ASSERT_EQUAL(0,restored.adoptedStock.count(manual));
    pet.adoptedStock.set(manual,1);
    pet.setEvAt(CombatStat::Off,pet.evLimit()-2);
    s.state=TrainingSession::State::Confirm;
    s.input(pet,InputEvent::Action,0);
    TEST_ASSERT_EQUAL(pet.evLimit(),pet.evAt(CombatStat::Off));
    TEST_ASSERT_EQUAL(1,pet.adoptedStock.count(manual));
}

void test_adopted_journal_each_write_failure() {
    using namespace vpet;
    ItemStore baseline;
    Settings settings;
    PetState initial;
    TEST_ASSERT_TRUE(SettingsStore(baseline).save(initial,settings));
    const int initialWrites=baseline.writes;
    TEST_ASSERT_TRUE(SettingsStore(baseline).commitConsumables(initial));
    const int checkpoints=baseline.writes-initialWrites;
    // Commit, every replay field, bag record and journal acknowledgement.
    for (int failure=1; failure<=checkpoints; ++failure) {
        ItemStore kv;
        SettingsStore store(kv);
        Settings settings;
        PetState pet;
        pet.evolveTo(SpeciesId::Rookie);
        pet.adoptedStock.seed();
        pet.setHappiness(10);
        TEST_ASSERT_TRUE(store.save(pet,settings));
        const PetState before=pet;
        TEST_ASSERT_EQUAL(ItemUseResult::Used,pet.useItem(8+adopted::indexOf("blue_apple")));
        kv.failAt=kv.writes+failure;
        const bool committed=store.commitConsumables(pet);
        TEST_ASSERT_EQUAL(failure!=1,committed);
        if (!committed) pet=before;
        TEST_ASSERT_EQUAL(failure==1 ? 10 : 30,pet.happiness());
        PetState restored;
        TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(restored,settings));
        TEST_ASSERT_EQUAL(pet.happiness(),restored.happiness());
        TEST_ASSERT_EQUAL_STRING(pet.adoptedStock.encode().c_str(),restored.adoptedStock.encode().c_str());
        TEST_ASSERT_TRUE(store.load(restored,settings)==LoadResult::Loaded);
        TEST_ASSERT_EQUAL(pet.happiness(),restored.happiness());
    }
}

void test_adopted_terminal_and_reward_rollback() {
    using namespace vpet;
    ItemStore kv;
    SettingsStore store(kv);
    Settings settings;
    PetState pet;
    pet.evolveTo(SpeciesId::Rookie);
    pet.adoptedStock.seed();
    TEST_ASSERT_TRUE(store.save(pet,settings));
    PracticeSession s;
    s.page=PracticeSession::Page::Bag;
    s.battle.rival.hp=1;
    s.battle.player.stats[4]=99;
    s.battle.player.equipped=1;
    s.battle.player.personality=0;
    const PetState previous=pet;
    const PracticeSession previousSession=s;
    s.tick(pet,1000);
    TEST_ASSERT_EQUAL(1,s.battle.result);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Arena,s.page);
    TEST_ASSERT_EQUAL(1,pet.adoptedStock.rewards);
    TEST_ASSERT_EQUAL(adopted::indexOf("small_recovery"),s.rewardItem);
    kv.failJournal=true;
    const bool committed=store.commitConsumables(pet);
    TEST_ASSERT_FALSE(committed);
    s.finishSave(pet,previous,previousSession,committed);
    TEST_ASSERT_EQUAL(0,pet.adoptedStock.rewards);
    TEST_ASSERT_EQUAL(1,s.battle.result);
    TEST_ASSERT_TRUE(s.pendingAward);
    TEST_ASSERT_EQUAL(-1,s.rewardItem);
    s.tick(pet,10000);
    TEST_ASSERT_EQUAL(0,pet.adoptedStock.rewards);
    s.input(pet,InputEvent::Action,10000);
    TEST_ASSERT_EQUAL(1,pet.adoptedStock.rewards);
    TEST_ASSERT_EQUAL(adopted::indexOf("small_recovery"),s.rewardItem);
    kv.failJournal=false;
    TEST_ASSERT_TRUE(store.commitConsumables(pet));
    const auto awarded=pet.adoptedStock.encode();
    s.tick(pet,10000);
    s.tick(pet,20000);
    TEST_ASSERT_EQUAL_STRING(awarded.c_str(),pet.adoptedStock.encode().c_str());
    PetState restored;
    TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(restored,settings));
    TEST_ASSERT_EQUAL(1,restored.adoptedStock.rewards);
    TEST_ASSERT_EQUAL(3,restored.adoptedStock.cursor);
    const auto record=restored.adoptedStock.encode();
    restored.resetToEgg();
    restored.resetToEgg();
    TEST_ASSERT_EQUAL_STRING(record.c_str(),restored.adoptedStock.encode().c_str());
}

void test_adopted_bag_depletion_and_icons() {
    using namespace vpet;
    PetState pet;
    pet.adoptedStock.set(adopted::indexOf("blue_apple"),1);
    pet.adoptedStock.set(adopted::indexOf("off_disk"),1);
    pet.adoptedStock.set(adopted::indexOf("small_recovery"),1);
    PracticeSession s;
    s.page=PracticeSession::Page::Bag;
    s.cursor=1;
    s.input(pet,InputEvent::Action,0);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Bag,s.page);
    TEST_ASSERT_EQUAL(2,s.bagCount(pet));
    TEST_ASSERT_EQUAL(1,s.cursor);
    TEST_ASSERT_EQUAL(-1,s.bagItemAt(pet,s.cursor));
    TEST_ASSERT_EQUAL(0,pet.adoptedStock.count(adopted::indexOf("off_disk")));
    TEST_ASSERT_EQUAL(0,s.battle.round);
    s.input(pet,InputEvent::Action,0);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Arena,s.page);
    pet.practice.equipped=7;
    TEST_ASSERT_EQUAL_STRING("/ui/icons/brain.vpa",s.actionIcon(pet,0));
    TEST_ASSERT_EQUAL_STRING("/training/tech_punch.vpa",s.actionIcon(pet,1));
    TEST_ASSERT_EQUAL_STRING("/training/tech_flame.vpa",s.actionIcon(pet,2));
    TEST_ASSERT_EQUAL_STRING("/training/tech_guard.vpa",s.actionIcon(pet,3));
    TEST_ASSERT_EQUAL_STRING("/ui/icons/backpack.vpa",s.actionIcon(pet,4));
    TEST_ASSERT_EQUAL_STRING("/ui/icons/back.vpa",s.actionIcon(pet,5));
}

void test_adopted_save_failure_preserves_bag_and_manual_gate() {
    using namespace vpet;
    ItemStore kv;
    SettingsStore store(kv);
    Settings settings;
    PetState pet;
    pet.adoptedStock.seed();
    const int manual=adopted::indexOf("training_manual");
    pet.adoptedStock.set(manual,1);
    const auto before=pet.adoptedStock.encode();
    TEST_ASSERT_TRUE(store.save(pet,settings));
    pet.adoptedStock.set(manual,0);
    kv.failAt=kv.writes+1;  // Fail before the durable snapshot commit point.
    TEST_ASSERT_FALSE(store.save(pet,settings));
    TEST_ASSERT_EQUAL_STRING(before.c_str(),kv.strings["adoptBag"].c_str());
    pet.adoptedStock.set(manual,1);
    TEST_ASSERT_FALSE(pet.canOpenTrainingManual(8+manual));
    pet.evolveTo(SpeciesId::Rookie);
    TEST_ASSERT_TRUE(pet.canOpenTrainingManual(8+manual));
    TEST_ASSERT_FALSE(pet.canOpenTrainingManual(255));
    TEST_ASSERT_FALSE(pet.canOpenTrainingManual(7));
    TEST_ASSERT_FALSE(pet.canOpenTrainingManual(8));
    pet.setCold(true);
    TEST_ASSERT_FALSE(pet.canOpenTrainingManual(8+manual));
}

void test_adopted_manual_preview_matches_commit() {
    using namespace vpet;
    PetState pet;
    pet.evolveTo(SpeciesId::Rookie);
    pet.adoptedStock.set(adopted::indexOf("training_manual"),1);
    for (int ev : {0,77,78,82,84,200,252}) {
        pet.setEvAt(CombatStat::Off,ev);
        const auto base=trainingPlanOneRep(pet,CombatStat::Off);
        const int expected=ev<78 ? 7 : ev<84 ? 84-ev : 0;
        TEST_ASSERT_EQUAL(expected,trainingPreviewEv(pet,CombatStat::Off,base.evAdded));
        TEST_ASSERT_EQUAL(0,trainingPreviewEv(pet,CombatStat::Off,0));
    }
    pet.setEvAt(CombatStat::Off,0);
    pet.adoptedStock.set(adopted::indexOf("training_manual"),0);
    TEST_ASSERT_EQUAL(6,trainingPreviewEv(pet,CombatStat::Off,6));
}

void test_practice_last_order_survives_cursor_changes() {
    using namespace vpet;
    PetState pet;
    pet.evolveTo(SpeciesId::Rookie);
    pet.practice.equipped=7;
    PracticeSession session;
    TEST_ASSERT_EQUAL(-1,session.lastOrder);
    session.page=PracticeSession::Page::Arena;
    session.cursor=2;
    session.input(pet,InputEvent::Action,0);
    TEST_ASSERT_EQUAL(1,session.lastOrder);
    TEST_ASSERT_EQUAL(2,session.cursor);
    session.input(pet,InputEvent::Next,1);
    TEST_ASSERT_EQUAL(1,session.lastOrder);
    session.cursor=session.count(pet)-2;
    session.input(pet,InputEvent::Action,2);
    TEST_ASSERT_EQUAL(PracticeSession::Page::Bag,session.page);
    TEST_ASSERT_EQUAL(1,session.lastOrder);
    session.tick(pet,1450);
    TEST_ASSERT_EQUAL(-1,session.lastOrder);
    TEST_ASSERT_EQUAL(2,session.battle.round);
    session.round(pet,0,1451);
    TEST_ASSERT_EQUAL(0,session.lastOrder);
    session.round(pet,9,1452);
    TEST_ASSERT_EQUAL(0,session.lastOrder);
    session.page=PracticeSession::Page::Menu;
    session.cursor=1;
    session.input(pet,InputEvent::Action,1500);
    TEST_ASSERT_EQUAL(-1,session.lastOrder);
    TEST_ASSERT_EQUAL(0,session.battle.round);
}

void test_adopted_journal_finishes_legacy_nutrition_migration() {
    using namespace vpet;
    ItemStore kv;
    kv.ints["schema"]=3;
    kv.ints["species"]=static_cast<int>(SpeciesId::Rookie);
    kv.ints["weight"]=5;
    Settings settings;
    SettingsStore store(kv);
    PetState pet;
    TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(pet,settings));
    TEST_ASSERT_EQUAL(8,pet.weight());
    pet.setNutritionState(7,2,true);
    const int pear=adopted::indexOf("prickly_pear");
    pet.adoptedStock.set(pear,1);
    TEST_ASSERT_EQUAL(ItemUseResult::Used,pet.useItem(8+pear));
    TEST_ASSERT_EQUAL(6,pet.weight());
    kv.failReplay=true;
    TEST_ASSERT_TRUE(store.commitConsumables(pet));
    kv.failReplay=false;
    PetState restored;
    TEST_ASSERT_EQUAL(LoadResult::Loaded,store.load(restored,settings));
    TEST_ASSERT_EQUAL(6,restored.weight());
    TEST_ASSERT_EQUAL(7,restored.hungerCycleRemainder());
    TEST_ASSERT_EQUAL(2,restored.trainingWeightRemainder());
    TEST_ASSERT_TRUE(restored.proteinFedThisCycle());
    TEST_ASSERT_EQUAL(0,restored.adoptedStock.count(pear));
    TEST_ASSERT_EQUAL(1,kv.ints["nutVer"]);
    TEST_ASSERT_EQUAL(5,kv.ints["legacyWeight"]);
    TEST_ASSERT_EQUAL(3,kv.ints["schema"]);
    TEST_ASSERT_TRUE(store.commitConsumables(restored));
    TEST_ASSERT_EQUAL(5,kv.ints["legacyWeight"]);
}
