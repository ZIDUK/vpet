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
