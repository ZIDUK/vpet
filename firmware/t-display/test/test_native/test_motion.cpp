#include <unity.h>

#include "vpet/Layout.h"
#include "vpet/Motion.h"

void test_dragfiremon_moves_with_fly_state() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Ultimate);
    motion.startWalking(1000);
    const int startingX = motion.x();
    TEST_ASSERT_EQUAL(vpet::AnimationId::DragfiremonFly, motion.animation());
    for (uint32_t now = 1000; now < 2000; now += 16) {
        motion.tick(now);
    }
    TEST_ASSERT_NOT_EQUAL(startingX, motion.x());
    TEST_ASSERT_TRUE(motion.x() >= 0 && motion.x() <= 152);
    TEST_ASSERT_TRUE(motion.y() >= 24 && motion.y() <= 47);
}

void test_action_animation_returns_to_idle() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.startAction(vpet::Action::Feed, 100);
    TEST_ASSERT_EQUAL(vpet::MotionState::Eat, motion.state());
    motion.tick(3000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
}

void test_sleep_loops_until_explicit_wake() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Rookie);
    motion.startAction(vpet::Action::Rest, 100);

    motion.tick(4000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());

    motion.wake(4100);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_TRUE(motion.consumeActionCompleted());
}

void test_dragfiremon_sleep_loops_lying_frames() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Ultimate);
    motion.startAction(vpet::Action::Rest, 100);

    motion.tick(100 + 11 * 105);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());
    TEST_ASSERT_EQUAL(11, motion.frame());

    motion.tick(100 + 14 * 105);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());
    TEST_ASSERT_EQUAL(14, motion.frame());

    motion.tick(100 + 15 * 105);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());
    TEST_ASSERT_EQUAL(11, motion.frame());

    motion.tick(100 + 16 * 105);
    TEST_ASSERT_EQUAL(12, motion.frame());
}

void test_dragfiremon_idle_keeps_full_sheet() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Ultimate);
    motion.startWalking(0);
    motion.tick(3000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());

    motion.tick(3000 + 15 * 85);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_EQUAL(15, motion.frame());
    motion.tick(3000 + 24 * 85);
    TEST_ASSERT_EQUAL(24, motion.frame());
}

void test_egg_idle_loops_intact_sheet() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Egg);

    motion.tick(0);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_EQUAL(0, motion.frame());
    motion.tick(85);
    TEST_ASSERT_EQUAL(1, motion.frame());
    motion.tick(16 * 85);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_EQUAL(0, motion.frame());
}

void test_egg_hatch_plays_break_frames_once() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Egg);
    motion.startHatch(0);

    TEST_ASSERT_EQUAL(vpet::MotionState::Hatch, motion.state());
    motion.tick(0);
    TEST_ASSERT_EQUAL(0, motion.frame());
    motion.tick(80);
    TEST_ASSERT_EQUAL(1, motion.frame());
    motion.tick(9 * 80);
    TEST_ASSERT_EQUAL(9, motion.frame());
    motion.tick(20 * 80);
    TEST_ASSERT_EQUAL(vpet::MotionState::Hatch, motion.state());
    TEST_ASSERT_EQUAL(9, motion.frame());
}

void test_baby_animates_after_leaving_egg_hatch() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Egg);
    motion.startHatch(0);
    motion.tick(800);

    motion.setSpecies(vpet::SpeciesId::Baby);
    motion.alignClock(800);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_EQUAL(0, motion.frame());

    motion.tick(800 + 85);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_EQUAL(1, motion.frame());
}

void test_helix_helpers_use_dna_or_gray() {
    const uint8_t dna[] = {0x12, 0x34, 0x56, 0x78};
    const uint8_t empty[] = {0, 0, 0, 0};
    TEST_ASSERT_EQUAL(0x1234, vpet::helixColor(dna, 0));
    TEST_ASSERT_EQUAL(0x5678, vpet::helixColor(dna, 1));
    TEST_ASSERT_EQUAL(0x7BEF, vpet::helixColor(empty, 0));
    TEST_ASSERT_TRUE(vpet::helixX(0, 0, 28) != vpet::helixX(1, 0, 28));
    TEST_ASSERT_TRUE(vpet::helixSample(0, 4, 32, 32) > vpet::helixSample(1, 4, 32, 32));
    TEST_ASSERT_EQUAL(vpet::helixSample(0, 0, 32, 32), vpet::helixSample(1, 0, 32, 32));
    TEST_ASSERT_TRUE(vpet::helixSample(0, 0, 32, 32, 0.f) != vpet::helixSample(0, 0, 32, 32, 1.5708f));
    TEST_ASSERT_TRUE(vpet::helixSpin(0) != vpet::helixSpin(1200));
    TEST_ASSERT_EQUAL(100, vpet::kStatusSplitX);
    TEST_ASSERT_EQUAL(6, vpet::statusPetX(88));
    TEST_ASSERT_EQUAL(54, vpet::kStatusCardY);
    TEST_ASSERT_EQUAL(27, vpet::kStatusCardRow);
    TEST_ASSERT_EQUAL(24, vpet::kStatusCardH);
    TEST_ASSERT_TRUE(vpet::kStatusCardRow - vpet::kStatusCardH >= 3);
    TEST_ASSERT_EQUAL(3, vpet::kInventoryWindow);
    TEST_ASSERT_EQUAL(0, vpet::inventoryWindowStart(7, 0));
    TEST_ASSERT_EQUAL(2, vpet::inventoryWindowStart(7, 3));
    TEST_ASSERT_EQUAL(4, vpet::inventoryWindowStart(7, 6));
    TEST_ASSERT_EQUAL(56, vpet::kHelixY);
    TEST_ASSERT_EQUAL(36, vpet::kHelixWidth);
    TEST_ASSERT_EQUAL(74, vpet::kHelixHeight);
    TEST_ASSERT_EQUAL(6, vpet::kHelixRungs);
    TEST_ASSERT_EQUAL(1.f, vpet::kHelixTurns);
}

void test_call_cues_the_matching_care_icon() {
    TEST_ASSERT_EQUAL(255, vpet::callMenuIndex(vpet::CallReason::None));
    TEST_ASSERT_EQUAL(1, vpet::callMenuIndex(vpet::CallReason::Hunger));
    TEST_ASSERT_EQUAL(2, vpet::callMenuIndex(vpet::CallReason::Strength));
    TEST_ASSERT_EQUAL(4, vpet::callMenuIndex(vpet::CallReason::Lights));
}

void test_call_blink_toggles_every_400ms() {
    TEST_ASSERT_TRUE(vpet::callBlinkOn(0));
    TEST_ASSERT_TRUE(vpet::callBlinkOn(399));
    TEST_ASSERT_FALSE(vpet::callBlinkOn(400));
    TEST_ASSERT_TRUE(vpet::callBlinkOn(800));
}

void test_punching_bag_stays_inside_bottom_edge() {
    constexpr int kDisplayHeight = 135;
    constexpr int kBagHeight = 88;
    constexpr int kPetY = kDisplayHeight - kBagHeight - 4;

    TEST_ASSERT_EQUAL(43, kPetY);
    TEST_ASSERT_EQUAL(kPetY, vpet::bagDrawY(kPetY, kBagHeight, kDisplayHeight));
    TEST_ASSERT_TRUE(vpet::bagDrawY(kPetY, kBagHeight, kDisplayHeight) + kBagHeight <= kDisplayHeight);
    TEST_ASSERT_EQUAL(
        kDisplayHeight - kBagHeight,
        vpet::bagDrawY(kPetY + 16, kBagHeight, kDisplayHeight)
    );
}

void test_battle_reaction_picks_combat_sheet() {
    vpet::Motion motion(240, 135, 24, 88);

    motion.startReaction(true, false, 100);
    TEST_ASSERT_EQUAL(vpet::MotionState::Dodge, motion.state());
    motion.tick(100 + 15 * 70);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
    TEST_ASSERT_TRUE(motion.consumeActionCompleted());

    motion.startReaction(true, true, 2000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Block, motion.state());

    motion.startReaction(false, false, 3000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Hit, motion.state());

    motion.startReaction(false, true, 4000);
    TEST_ASSERT_EQUAL(vpet::MotionState::Hurt, motion.state());
}

void test_sparkmon_evolution_uses_sixteen_frames() {
    vpet::Motion motion(240, 135, 24, 88);
    motion.setSpecies(vpet::SpeciesId::Rookie);
    motion.startEvolution(100);

    motion.tick(100 + 15 * 85);
    TEST_ASSERT_EQUAL(vpet::MotionState::Evolution, motion.state());
    TEST_ASSERT_EQUAL(15, motion.frame());

    motion.tick(100 + 16 * 85);
    TEST_ASSERT_EQUAL(vpet::MotionState::Idle, motion.state());
}
