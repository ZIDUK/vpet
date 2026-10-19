#include <unity.h>
#include "vpet/PetState.h"
#include "vpet/Motion.h"
using namespace vpet;
static uint64_t night(int day,int hour=23) { return (20000ULL+day)*86400+hour*3600; }
void test_sleep_night_boundaries_and_dna_thresholds() {
    TEST_ASSERT_FALSE(SleepRoutine::isNight(1079));
    TEST_ASSERT_TRUE(SleepRoutine::isNight(1080));
    TEST_ASSERT_TRUE(SleepRoutine::isNight(359));
    TEST_ASSERT_FALSE(SleepRoutine::isNight(360));
    for(int trait=0;trait<3;++trait) {
        SleepRoutine s;
        TEST_ASSERT_EQUAL(1080+(2-trait)*15,s.preferred(trait));
        TEST_ASSERT_TRUE(s.tired(20+trait*5,trait,720));
        TEST_ASSERT_TRUE(s.tired(29+trait*5,trait,720));
        TEST_ASSERT_FALSE(s.tired(30+trait*5,trait,720));
        TEST_ASSERT_TRUE(s.tired(100,trait,1380));
    }
}
void test_sleep_learns_only_completed_consistent_nights() {
    SleepRoutine s; int energy=0; bool reward=false;
    for(int day=0;day<3;++day) {
        TEST_ASSERT_TRUE(s.start(night(day),1));
        TEST_ASSERT_EQUAL(28800,s.required);
        TEST_ASSERT_TRUE(s.advance(28800,energy,reward));
        TEST_ASSERT_TRUE(reward);
    }
    TEST_ASSERT_EQUAL(1110,s.bedtime);
    s.start(night(2),1); s.advance(28800,energy,reward);
    TEST_ASSERT_FALSE(reward); TEST_ASSERT_EQUAL(1110,s.bedtime);
    s.start(night(3,19),1); s.advance(28800,energy,reward);
    TEST_ASSERT_EQUAL(1110,s.bedtime); // One exceptional night does not retrain.
}
void test_sleep_codec_resumes_without_offline_credit() {
    SleepRoutine s; int energy=0; bool reward=false;
    s.start(night(0),1); s.advanceMs(25200001,energy,reward);
    SleepRoutine restored; TEST_ASSERT_TRUE(restored.decode(s.encode()));
    TEST_ASSERT_EQUAL_STRING(s.encode().c_str(),restored.encode().c_str());
    TEST_ASSERT_EQUAL(84,energy); TEST_ASSERT_TRUE(restored.asleep);
    TEST_ASSERT_TRUE(restored.advanceMs(3600000,energy,reward));
    TEST_ASSERT_TRUE(reward); TEST_ASSERT_EQUAL(96,energy);
    const auto valid=restored.encode();
    TEST_ASSERT_FALSE(restored.decode("99,future"));
    TEST_ASSERT_EQUAL_STRING(valid.c_str(),restored.encode().c_str());
}
void test_sleep_pauses_metabolism_not_injury_and_keeps_routine_on_evolution() {
    PetState p; p.evolveTo(SpeciesId::Rookie); p.setEnergy(20);
    p.sleep.bedtime=1200; p.tick(300000,true);
    TEST_ASSERT_EQUAL(20,p.energy()); TEST_ASSERT_EQUAL(300,p.stageAgeSeconds());
    p.forceNextForm(); TEST_ASSERT_EQUAL(1200,p.sleep.bedtime);
    p.restoreInjury(true,1,false,21599999); p.tick(1,true);
    TEST_ASSERT_TRUE(p.dead());
    p.resetToEgg(); TEST_ASSERT_EQUAL(0,p.sleep.bedtime);
}
void test_tired_motion_stays_idle_but_does_not_interrupt_actions() {
    Motion motion(240,135,24,88); motion.setSpecies(SpeciesId::Rookie);
    motion.startWalking(0); motion.setTired(true,10); motion.tick(100000);
    TEST_ASSERT_EQUAL(MotionState::Idle,motion.state());
    motion.startAction(Action::Training,100000); motion.setTired(true,100010);
    TEST_ASSERT_EQUAL(MotionState::Punch,motion.state());
}
