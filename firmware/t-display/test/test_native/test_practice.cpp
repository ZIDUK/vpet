#include <unity.h>

#include "vpet/PracticeBattle.h"
#include "vpet/PracticeSession.h"

void test_practice_session_training_battle_and_reset() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.rollDna(42);
    vpet::PracticeSession session;
    session.input(pet, vpet::InputEvent::Action, 0);
    session.input(pet, vpet::InputEvent::Next, 0);
    session.input(pet, vpet::InputEvent::Action, 0);
    const int energy = pet.energy();
    session.input(pet, vpet::InputEvent::Action, 0);
    session.input(pet, vpet::InputEvent::Action, 0);
    TEST_ASSERT_TRUE(pet.practice.flameLearned());
    TEST_ASSERT_EQUAL(energy - 8, pet.energy());
    session.input(pet, vpet::InputEvent::Next, 0);
    session.input(pet, vpet::InputEvent::Action, 0);
    TEST_ASSERT_EQUAL(3, pet.practice.equipped);
    session.input(pet, vpet::InputEvent::Back, 0);
    session.input(pet, vpet::InputEvent::Next, 0);
    session.input(pet, vpet::InputEvent::Action, 0);
    TEST_ASSERT_EQUAL(vpet::PracticeSession::Page::Arena, session.page);
    session.dirty = false;
    while (!session.battle.result) session.input(pet, vpet::InputEvent::Action, 1000);
    TEST_ASSERT_TRUE(session.dirty);
    TEST_ASSERT_EQUAL(0, pet.battles());
    const int bond = pet.practice.bond;
    session.input(pet, vpet::InputEvent::Action, 2000);
    TEST_ASSERT_EQUAL(bond, pet.practice.bond);
    pet.evolveTo(vpet::SpeciesId::Champion);
    TEST_ASSERT_TRUE(pet.practice.flameLearned());
    pet.resetToEgg();
    TEST_ASSERT_FALSE(pet.practice.flameLearned());
}

void test_practice_cpp_respects_mp_and_cooldown() {
    const int stats[6] = {30, 20, 30, 20, 30, 20};
    vpet::practice::Battle battle;
    battle.player.init(stats);
    battle.rival.init(stats);
    battle.rival.hp = battle.rival.maxHp = 1000;

    TEST_ASSERT_TRUE(battle.step(1));
    TEST_ASSERT_EQUAL(22, battle.player.mp);
    TEST_ASSERT_EQUAL(1, battle.player.cooldown[1]);
    TEST_ASSERT_TRUE(battle.step(1));
    TEST_ASSERT_NOT_EQUAL(1, battle.actions[0]);
    TEST_ASSERT_TRUE(battle.player.mp >= 0);
}

void test_practice_cpp_guard_caps_mp_and_halves_damage() {
    const int stats[6] = {30, 20, 30, 20, 30, 20};
    vpet::practice::Battle battle;
    battle.player.init(stats);
    battle.rival.init(stats);
    battle.player.equipped = 4;
    battle.rival.equipped = 1;
    battle.player.mp = battle.player.maxMp - 1;

    TEST_ASSERT_TRUE(battle.step(2));
    TEST_ASSERT_EQUAL(battle.player.maxMp, battle.player.mp);
    TEST_ASSERT_EQUAL((12 + 30 / 3 - 20 / 4) / 2, battle.damage[1]);
}

void test_practice_cpp_stops_after_draw_limit() {
    const int stats[6] = {30, 20, 30, 20, 30, 20};
    vpet::practice::Battle battle;
    battle.player.init(stats);
    battle.rival.init(stats);
    battle.player.equipped = 4;
    battle.rival.equipped = 4;

    for (int i = 0; i < 30; ++i) TEST_ASSERT_TRUE(battle.step(2));
    TEST_ASSERT_EQUAL(3, battle.result);
    TEST_ASSERT_FALSE(battle.step(2));
}
