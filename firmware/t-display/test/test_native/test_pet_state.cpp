#include <unity.h>

#include "vpet/PetState.h"

void test_cold_mode_freezes_decay_and_blocks_calls() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 10, 10, 70, 0, 70, 0);
    pet.setCold(true);
    pet.tick(120000);
    TEST_ASSERT_EQUAL(10, pet.hunger());
    TEST_ASSERT_EQUAL(10, pet.energy());
    TEST_ASSERT_EQUAL(0, pet.stageAgeSeconds());
    TEST_ASSERT_EQUAL(vpet::CallUpdate::None, pet.updateCall(0, 1));
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Feed));
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Battle));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Blocked, pet.useItem(0));
    pet.setCold(false);
    pet.tick(30000);
    TEST_ASSERT_EQUAL(9, pet.hunger());
}

void test_hunger_and_energy_map_to_four_hearts() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 0, 0, 70, 0, 70, 0);
    TEST_ASSERT_EQUAL(0, pet.hungerHearts());
    TEST_ASSERT_EQUAL(0, pet.strengthHearts());
    pet.restore(vpet::SpeciesId::Rookie, 1, 26, 70, 0, 70, 0);
    TEST_ASSERT_EQUAL(1, pet.hungerHearts());
    TEST_ASSERT_EQUAL(2, pet.strengthHearts());
    pet.restore(vpet::SpeciesId::Rookie, 76, 100, 70, 0, 70, 0);
    TEST_ASSERT_EQUAL(4, pet.hungerHearts());
    TEST_ASSERT_EQUAL(4, pet.strengthHearts());
}

void test_win_ratio_is_zero_until_a_battle_is_played() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    TEST_ASSERT_FALSE(pet.hasWinRatio());
    TEST_ASSERT_EQUAL(0, pet.winRatioPercent());
    pet.restoreCare(0, 0, vpet::CallReason::None, 0, 0, 3, 2, 1, 5, 1, 0);
    TEST_ASSERT_TRUE(pet.hasWinRatio());
    TEST_ASSERT_EQUAL(66, pet.winRatioPercent());
}

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
    TEST_ASSERT_TRUE(pet.forceNextForm());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_EQUAL(80, pet.hunger());
    TEST_ASSERT_EQUAL(0, pet.ageSeconds());
    TEST_ASSERT_FALSE(pet.hasDiscovered(vpet::SpeciesId::Rookie));
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
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Back, pet.useItem(6));
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
    TEST_ASSERT_EQUAL(6, pet.inventoryIndexAt(2));
    TEST_ASSERT_EQUAL(2, pet.nextVisibleInventoryIndex(0));
    TEST_ASSERT_EQUAL(6, pet.nextVisibleInventoryIndex(2));
    TEST_ASSERT_EQUAL(0, pet.nextVisibleInventoryIndex(6));
    TEST_ASSERT_EQUAL(2, pet.clampVisibleInventoryIndex(1));

    pet.useItem(2);
    TEST_ASSERT_EQUAL(0, pet.itemCount(2));
    TEST_ASSERT_EQUAL(2, pet.visibleInventoryCount());
    TEST_ASSERT_EQUAL(6, pet.clampVisibleInventoryIndex(2));
    TEST_ASSERT_EQUAL(6, pet.inventoryIndexAt(1));
}

void test_overfeed_once_when_full_is_not_a_care_mistake() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 100, 80, 80, 0, 100, 0);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
    TEST_ASSERT_TRUE(pet.overfedThisCycle());
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
    TEST_ASSERT_EQUAL(6, pet.weight());
    TEST_ASSERT_EQUAL(1, pet.meals());
}

void test_second_feed_while_full_is_rejected() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 100, 80, 80, 0, 100, 0);
    pet.beginAction(vpet::Action::Feed);
    pet.completeAction();
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Feed));
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
    TEST_ASSERT_EQUAL(1, pet.meals());
}

void test_hunger_drop_allows_another_overfeed() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 100, 80, 80, 0, 100, 0);
    pet.beginAction(vpet::Action::Feed);
    pet.completeAction();
    pet.tick(30000);
    TEST_ASSERT_EQUAL(99, pet.hunger());
    TEST_ASSERT_FALSE(pet.overfedThisCycle());
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(2, pet.overfeeds());
}

void test_meat_item_blocked_after_overfeed() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 100, 80, 80, 0, 100, 0);
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(0));
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Blocked, pet.useItem(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(0));
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
}

void test_wake_at_night_adds_care_mistake() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.noteWake(22);
    TEST_ASSERT_EQUAL(1, pet.careMistakes());
    pet.noteWake(7);
    TEST_ASSERT_EQUAL(2, pet.careMistakes());
}

void test_wake_during_day_does_not_add_care_mistake() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.noteWake(8);
    pet.noteWake(12);
    pet.noteWake(20);
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
}

void test_egg_wake_does_not_add_care_mistake() {
    vpet::PetState pet;
    pet.noteWake(23);
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
}

void test_protein_every_four_uses_raises_overdose_and_dp() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restoreItems(3, 2, 1, 1, 4, 1);
    TEST_ASSERT_EQUAL(4, pet.itemCount(4));
    TEST_ASSERT_EQUAL(1, pet.dp());
    TEST_ASSERT_EQUAL(0, pet.protein());
    for (int i = 0; i < 4; ++i) {
        TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(4));
    }
    TEST_ASSERT_EQUAL(0, pet.itemCount(4));
    TEST_ASSERT_EQUAL(1, pet.protein());
    TEST_ASSERT_EQUAL(2, pet.dp());
    TEST_ASSERT_TRUE(pet.energy() >= 80);
}

void test_medkit_heals_injury_and_is_blocked_when_healthy() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restoreItems(3, 2, 1, 1, 2, 1);
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Blocked, pet.useItem(5));
    TEST_ASSERT_EQUAL(1, pet.itemCount(5));
    pet.setInjured(true);
    pet.setHealth(40);
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(5));
    TEST_ASSERT_EQUAL(0, pet.itemCount(5));
    TEST_ASSERT_FALSE(pet.injured());
    TEST_ASSERT_EQUAL(60, pet.health());
}

void test_four_trains_make_one_effort_heart() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    TEST_ASSERT_EQUAL(0, pet.effortHearts());
    for (int i = 0; i < 4; ++i) {
        pet.beginAction(vpet::Action::Training);
        pet.completeAction();
    }
    TEST_ASSERT_EQUAL(1, pet.effortHearts());
    TEST_ASSERT_EQUAL(4, pet.trainingSessions());
}

void test_battle_requires_dp_and_records_win() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 0);
    pet.setDp(0);
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Battle));
    pet.setDp(1);
    pet.setBattleRoll(0);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Battle));
    pet.completeAction();
    TEST_ASSERT_EQUAL(0, pet.dp());
    TEST_ASSERT_EQUAL(1, pet.wins());
    TEST_ASSERT_EQUAL(0, pet.losses());
    TEST_ASSERT_FALSE(pet.injured());
    TEST_ASSERT_TRUE(pet.lastBattleWon());
}

void test_battle_loss_injures_and_medkit_clears_it() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 0);
    pet.setDp(1);
    pet.setBattleRoll(99);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Battle));
    pet.completeAction();
    TEST_ASSERT_EQUAL(1, pet.losses());
    TEST_ASSERT_TRUE(pet.injured());
    TEST_ASSERT_EQUAL(1, pet.injuries());
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Battle));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(5));
    TEST_ASSERT_FALSE(pet.injured());
}

void test_fifteen_injuries_kill_and_grave_restarts_egg() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 0);
    pet.setInjuries(15);
    TEST_ASSERT_TRUE(pet.dead());
    TEST_ASSERT_FALSE(pet.beginAction(vpet::Action::Feed));
    pet.resetToEgg();
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_FALSE(pet.dead());
}

void test_six_hours_injured_kills() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 0);
    pet.setInjured(true);
    pet.tick(21600000);
    TEST_ASSERT_TRUE(pet.dead());
}

void test_rest_restores_one_dp() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 0);
    pet.setDp(0);
    pet.beginAction(vpet::Action::Rest);
    pet.completeAction();
    TEST_ASSERT_EQUAL(1, pet.dp());
}

void test_roll_dna_differs_and_is_never_zero() {
    vpet::PetState a;
    vpet::PetState b;
    a.rollDna(1);
    b.rollDna(2);
    TEST_ASSERT_TRUE(a.hasDna());
    TEST_ASSERT_TRUE(b.hasDna());
    TEST_ASSERT_TRUE(
        a.dna()[0] != b.dna()[0] || a.dna()[1] != b.dna()[1] ||
        a.dna()[2] != b.dna()[2] || a.dna()[3] != b.dna()[3]
    );
}

void test_ivs_read_dna_nibbles() {
    vpet::PetState pet;
    const uint8_t dna[] = {0x21, 0x43, 0x65, 0x87};
    pet.restoreDna(dna);
    TEST_ASSERT_EQUAL(1, pet.ivAt(vpet::CombatStat::Hp));
    TEST_ASSERT_EQUAL(2, pet.ivAt(vpet::CombatStat::Mp));
    TEST_ASSERT_EQUAL(3, pet.ivAt(vpet::CombatStat::Off));
    TEST_ASSERT_EQUAL(4, pet.ivAt(vpet::CombatStat::Def));
    TEST_ASSERT_EQUAL(5, pet.ivAt(vpet::CombatStat::Spd));
    TEST_ASSERT_EQUAL(6, pet.ivAt(vpet::CombatStat::Brn));
}

void test_combat_stat_uses_iv_ev_formula() {
    vpet::PetState pet;
    const uint8_t dna[] = {0x0F, 0x00, 0x00, 0x01};
    const uint8_t ev[] = {252, 0, 0, 0, 0, 0};
    pet.restoreDna(dna);
    pet.restoreEv(ev);
    TEST_ASSERT_EQUAL(10, pet.combatStat(vpet::CombatStat::Mp));
    TEST_ASSERT_EQUAL(97, pet.combatStat(vpet::CombatStat::Hp));
}

void test_care_and_items_gain_ev_with_caps() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 40, 80, 80, 0, 100, 0);
    pet.setDp(3);
    pet.setBattleRoll(0);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(2, pet.evAt(vpet::CombatStat::Hp));
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Training));
    pet.completeAction();
    TEST_ASSERT_EQUAL(2, pet.evAt(vpet::CombatStat::Off));
    TEST_ASSERT_EQUAL(1, pet.evAt(vpet::CombatStat::Spd));
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Battle));
    pet.completeAction();
    TEST_ASSERT_EQUAL(3, pet.evAt(vpet::CombatStat::Off));
    TEST_ASSERT_EQUAL(1, pet.evAt(vpet::CombatStat::Brn));
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Rest));
    pet.completeAction();
    TEST_ASSERT_EQUAL(2, pet.evAt(vpet::CombatStat::Mp));
    TEST_ASSERT_EQUAL(1, pet.evAt(vpet::CombatStat::Def));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(0));
    TEST_ASSERT_EQUAL(4, pet.evAt(vpet::CombatStat::Hp));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(1));
    TEST_ASSERT_EQUAL(4, pet.evAt(vpet::CombatStat::Mp));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(2));
    TEST_ASSERT_EQUAL(3, pet.evAt(vpet::CombatStat::Brn));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(4));
    TEST_ASSERT_EQUAL(5, pet.evAt(vpet::CombatStat::Off));
    const uint8_t beforeRing = pet.evAt(vpet::CombatStat::Hp);
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(3));
    TEST_ASSERT_EQUAL(beforeRing, pet.evAt(vpet::CombatStat::Hp));
    pet.setInjured(true);
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(5));
    TEST_ASSERT_EQUAL(5, pet.evAt(vpet::CombatStat::Off));
    const uint8_t cap[] = {251, 0, 0, 0, 0, 0};
    pet.restoreEv(cap);
    pet.restore(vpet::SpeciesId::Rookie, 50, 80, 80, 0, 100, 0);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(252, pet.evAt(vpet::CombatStat::Hp));
}

void test_overfeed_does_not_gain_ev() {
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie, 100, 80, 80, 0, 100, 0);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Feed));
    pet.completeAction();
    TEST_ASSERT_EQUAL(0, pet.evAt(vpet::CombatStat::Hp));
    TEST_ASSERT_EQUAL(1, pet.overfeeds());
}

void test_reset_to_egg_clears_dna_and_ev() {
    vpet::PetState pet;
    pet.rollDna(9);
    const uint8_t ev[] = {8, 4, 2, 1, 3, 5};
    pet.restoreEv(ev);
    pet.resetToEgg();
    TEST_ASSERT_FALSE(pet.hasDna());
    TEST_ASSERT_EQUAL(0, pet.evAt(vpet::CombatStat::Hp));
}

void test_evolution_keeps_dna_and_ev() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.rollDna(11);
    const uint8_t ev[] = {6, 0, 4, 0, 2, 0};
    pet.restoreEv(ev);
    const uint8_t d0 = pet.dna()[0];
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.resetAfterEvolution();
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, pet.species());
    TEST_ASSERT_EQUAL(d0, pet.dna()[0]);
    TEST_ASSERT_EQUAL(6, pet.evAt(vpet::CombatStat::Hp));
    TEST_ASSERT_EQUAL(4, pet.evAt(vpet::CombatStat::Off));
}
