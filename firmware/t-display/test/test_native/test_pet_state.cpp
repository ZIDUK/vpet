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

void test_use_item_spends_stock_and_applies_stat() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(0));
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(1));
    TEST_ASSERT_EQUAL(1, pet.itemCount(1));
    TEST_ASSERT_EQUAL(100, pet.energy());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(2));
    TEST_ASSERT_EQUAL(0, pet.itemCount(2));
    TEST_ASSERT_EQUAL(8, pet.effort());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(3));
    TEST_ASSERT_EQUAL(0, pet.itemCount(3));
    TEST_ASSERT_EQUAL(95, pet.happiness());
}

void test_use_item_empty_and_egg_do_not_change_stats() {
    vpet::PetState pet;
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Blocked, pet.useItem(0));
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Back, pet.useItem(4));
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restoreItems(0, 0, 0, 0);
    const int hunger = pet.hunger();
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Empty, pet.useItem(0));
    TEST_ASSERT_EQUAL(hunger, pet.hunger());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Empty, pet.useItem(9));
}

void test_empty_items_disappear_from_inventory_list() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restoreItems(3, 0, 1, 0);
    TEST_ASSERT_EQUAL(3, pet.visibleInventoryCount());
    TEST_ASSERT_EQUAL(0, pet.inventoryIndexAt(0));
    TEST_ASSERT_EQUAL(2, pet.inventoryIndexAt(1));
    TEST_ASSERT_EQUAL(4, pet.inventoryIndexAt(2));
    TEST_ASSERT_EQUAL(2, pet.nextVisibleInventoryIndex(0));
    TEST_ASSERT_EQUAL(4, pet.nextVisibleInventoryIndex(2));
    TEST_ASSERT_EQUAL(0, pet.nextVisibleInventoryIndex(4));
    TEST_ASSERT_EQUAL(2, pet.clampVisibleInventoryIndex(1));

    pet.useItem(2);
    TEST_ASSERT_EQUAL(0, pet.itemCount(2));
    TEST_ASSERT_EQUAL(2, pet.visibleInventoryCount());
    TEST_ASSERT_EQUAL(4, pet.clampVisibleInventoryIndex(2));
    TEST_ASSERT_EQUAL(4, pet.inventoryIndexAt(1));
}
