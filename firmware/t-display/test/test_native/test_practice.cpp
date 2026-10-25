#include <unity.h>

#include "vpet/PracticeBattle.h"
#include "vpet/PracticeSession.h"
#include "vpet/ConsumableEffects.h"
#include "vpet/Evolution.h"

void test_evolution_technique_slots_and_new_actions() {
    using namespace vpet;
    for (int stage=0;stage<3;++stage) {
        PetState pet;
        pet.evolveTo(static_cast<SpeciesId>(stage));
        pet.practice.training=6;
        TEST_ASSERT_EQUAL(stage+2,pet.techniqueCapacity());
        TEST_ASSERT_TRUE(pet.practice.toggle(1,pet.techniqueStage()));
        TEST_ASSERT_EQUAL(stage>=1,pet.practice.toggle(3,pet.techniqueStage()));
        TEST_ASSERT_EQUAL(stage>=2,pet.practice.toggle(4,pet.techniqueStage()));
        PracticeSession session;
        session.page=PracticeSession::Page::Tech;
        TEST_ASSERT_EQUAL(6,session.count(pet));
        TEST_ASSERT_EQUAL_STRING("VOLVER",session.label(pet,5));
    }
    PetState pet;
    pet.evolveTo(SpeciesId::Champion);
    pet.practice.training=3;
    TEST_ASSERT_FALSE(pet.practice.learned(3,pet.techniqueStage()));
    TEST_ASSERT_TRUE(pet.trainTechnique(3));
    TEST_ASSERT_TRUE(pet.practice.learned(3,pet.techniqueStage()));
    TEST_ASSERT_FALSE(pet.practice.isEquipped(3));
    TEST_ASSERT_FALSE(pet.trainTechnique(4));
    practice::Battle battle;
    battle.player.equipped=1<<4;
    battle.player.mp=50;
    TEST_ASSERT_TRUE(battle.step(4));
    TEST_ASSERT_EQUAL(4,battle.actions[0]);
    TEST_ASSERT_EQUAL(32,battle.player.mp);
    TEST_ASSERT_EQUAL(2,battle.player.cooldown[4]);
    TEST_ASSERT_FALSE(battle.player.valid(4));
}

void test_adopted_care_items_cap_and_consume() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.setEvAt(vpet::CombatStat::Off, pet.evLimit()-2);
    uint8_t stock = 2;
    uint8_t chip = 0;
    for (uint8_t i = 0; i < vpet::adopted::kCount; ++i)
        if (strcmp(vpet::adopted::kItems[i].id, "off_chip") == 0) chip = i;
    TEST_ASSERT_TRUE(vpet::consumables::useHome(pet, stock, chip));
    TEST_ASSERT_EQUAL(pet.evLimit(), pet.evAt(vpet::CombatStat::Off));
    TEST_ASSERT_EQUAL(1, stock);
    TEST_ASSERT_FALSE(vpet::consumables::useHome(pet, stock, chip));
    TEST_ASSERT_EQUAL(1, stock);
}

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
    TEST_ASSERT_EQUAL(vpet::practice::Element::Fire, session.battle.player.element);
    TEST_ASSERT_EQUAL(vpet::practice::Element::Fire, session.battle.rival.element);
    session.dirty = false;
    while (!session.battle.result) session.input(pet, vpet::InputEvent::Action, 1000);
    TEST_ASSERT_TRUE(session.dirty);
    TEST_ASSERT_EQUAL(session.battle.result==3 ? 0 : 1, pet.battles());
    const int bond = pet.practice.bond;
    session.input(pet, vpet::InputEvent::Action, 2000);
    TEST_ASSERT_EQUAL(bond, pet.practice.bond);
    pet.evolveTo(vpet::SpeciesId::Champion);
    TEST_ASSERT_TRUE(pet.practice.flameLearned());
    for (auto species : {vpet::SpeciesId::Rookie, vpet::SpeciesId::Champion,
                         vpet::SpeciesId::Ultimate}) {
        pet.evolveTo(species);
        vpet::PracticeSession arena;
        arena.cursor = 1;
        arena.input(pet, vpet::InputEvent::Action, 0);
        TEST_ASSERT_EQUAL(vpet::PracticeSession::Page::Arena, arena.page);
        TEST_ASSERT_EQUAL(vpet::practice::Element::Fire, arena.battle.player.element);
        TEST_ASSERT_EQUAL(vpet::practice::Element::Fire, arena.battle.rival.element);
    }
    pet.resetToEgg();
    TEST_ASSERT_FALSE(pet.practice.flameLearned());
}

void test_arena_results_unlock_evolution_once_without_care_costs() {
    using namespace vpet;
    for (int result : {1,2,3}) {
        PetState pet;
        pet.evolveTo(SpeciesId::Champion);
        pet.setStageAgeSeconds(129600);
        pet.setBattles(14); pet.setWins(8); pet.setLosses(6);
        const auto before=pet;
        PracticeSession session;
        session.page=PracticeSession::Page::Arena;
        session.battle.result=result;
        session.award(pet);
        TEST_ASSERT_EQUAL(result==3 ? 14 : 15,pet.battles());
        TEST_ASSERT_EQUAL(result==1 ? 9 : 8,pet.wins());
        TEST_ASSERT_EQUAL(result==2 ? 7 : 6,pet.losses());
        TEST_ASSERT_EQUAL(before.dp(),pet.dp());
        TEST_ASSERT_EQUAL(before.energy(),pet.energy());
        TEST_ASSERT_EQUAL(before.health(),pet.health());
        TEST_ASSERT_EQUAL(before.injuries(),pet.injuries());
        SpeciesId next;
        TEST_ASSERT_EQUAL(result==1,Evolution().check(pet,1,next));
        if(result==1) {
            TEST_ASSERT_EQUAL(SpeciesId::Ultimate,next);
            pet.setStageAgeSeconds(129599);
            TEST_ASSERT_FALSE(Evolution().check(pet,1,next));
        }
        session.award(pet);
        session.tick(pet,10000);
        TEST_ASSERT_EQUAL(result==3 ? 14 : 15,pet.battles());
    }
    PetState capped;
    capped.setBattles(INT32_MAX); capped.setWins(255); capped.setLosses(255);
    for (int result : {1,2}) {
        PracticeSession session;
        session.battle.result=result;
        session.award(capped);
        TEST_ASSERT_EQUAL(INT32_MAX,capped.battles());
        TEST_ASSERT_EQUAL(255,capped.wins());
        TEST_ASSERT_EQUAL(255,capped.losses());
    }
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

void test_practice_session_runs_rounds_without_action_input() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.rollDna(42);
    vpet::PracticeSession session;
    session.cursor = 1;
    session.input(pet, vpet::InputEvent::Action, 100);
    TEST_ASSERT_EQUAL(vpet::PracticeSession::Page::Arena, session.page);
    TEST_ASSERT_EQUAL(0, session.battle.round);
    session.tick(pet, 599);
    TEST_ASSERT_EQUAL(0, session.battle.round);
    session.cursor = 2;
    session.battle.player.hp = session.battle.rival.hp = 10000;
    session.tick(pet, 600);
    TEST_ASSERT_EQUAL(1, session.battle.round);
    TEST_ASSERT_EQUAL(2, session.cursor);
    TEST_ASSERT_EQUAL(2, session.lastOrder);
    session.tick(pet, 2049);
    TEST_ASSERT_EQUAL(1, session.battle.round);
    session.tick(pet, 2050);
    TEST_ASSERT_EQUAL(2, session.battle.round);
    TEST_ASSERT_EQUAL(2, session.cursor);
    session.input(pet, vpet::InputEvent::Action, 2100);
    TEST_ASSERT_EQUAL(2, session.cursor);
}
