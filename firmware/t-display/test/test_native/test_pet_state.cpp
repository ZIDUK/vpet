#include <unity.h>

#include "vpet/PetState.h"

void test_feed_updates_stats_once_when_animation_completes() {
    vpet::PetState pet;
    pet.beginAction(vpet::Action::Feed);
    pet.completeAction();
    pet.completeAction();
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(1, pet.meals());
}

void test_training_updates_effort_once() {
    vpet::PetState pet;
    pet.beginAction(vpet::Action::Training);
    pet.completeAction();
    TEST_ASSERT_EQUAL(1, pet.trainingSessions());
    TEST_ASSERT_TRUE(pet.effort() > 0);
}
