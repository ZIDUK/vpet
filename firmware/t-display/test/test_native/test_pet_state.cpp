#include <unity.h>

#include "vpet/PetState.h"

void test_feed_updates_stats_once_when_animation_completes() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.beginAction(vpet::Action::Feed);
    pet.completeAction();
    pet.completeAction();
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(1, pet.meals());
}

void test_training_updates_effort_once() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.beginAction(vpet::Action::Training);
    pet.completeAction();
    TEST_ASSERT_EQUAL(1, pet.trainingSessions());
    TEST_ASSERT_TRUE(pet.effort() > 0);
}

void test_new_pet_starts_as_egg_and_baby_cannot_attack() {
    vpet::PetState pet;
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Feed));
    pet.evolveTo(vpet::SpeciesId::Baby);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Training));
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Battle));
}

void test_persisted_species_values_remain_compatible() {
    TEST_ASSERT_EQUAL(0, static_cast<int>(vpet::SpeciesId::Rookie));
    TEST_ASSERT_EQUAL(1, static_cast<int>(vpet::SpeciesId::Champion));
    TEST_ASSERT_EQUAL(2, static_cast<int>(vpet::SpeciesId::Ultimate));
}

void test_force_next_form_walks_the_line() {
    vpet::PetState pet;
    TEST_ASSERT_TRUE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Baby, pet.species());
    TEST_ASSERT_TRUE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, pet.species());
    TEST_ASSERT_TRUE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Champion, pet.species());
    TEST_ASSERT_TRUE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Ultimate, pet.species());
    TEST_ASSERT_FALSE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Ultimate, pet.species());
}
