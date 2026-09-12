#include <unity.h>

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

    motion.tick(100 + 12 * 105);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());
    TEST_ASSERT_EQUAL(12, motion.frame());

    motion.tick(100 + 15 * 105);
    TEST_ASSERT_EQUAL(vpet::MotionState::Sleep, motion.state());
    TEST_ASSERT_EQUAL(12, motion.frame());

    motion.tick(100 + 16 * 105);
    TEST_ASSERT_EQUAL(13, motion.frame());
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
