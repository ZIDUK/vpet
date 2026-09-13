#include <unity.h>

#include "vpet/Evolution.h"
#include "vpet/PetState.h"
#include "vpet/SettingsStore.h"

#include <map>
#include <string>

namespace {

class FakeStore : public vpet::KeyValueStore {
public:
    int32_t getInt(const char* key, int32_t fallback) override {
        return ints.count(key) ? ints[key] : fallback;
    }
    bool putInt(const char* key, int32_t value) override { ints[key] = value; return true; }
    std::string getString(const char* key, const char* fallback) override {
        return strings.count(key) ? strings[key] : fallback;
    }
    bool putString(const char* key, const char* value) override { strings[key] = value; return true; }
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
};

void readyBars(vpet::PetState& pet) {
    pet.restore(pet.species(), 80, 80, 80, 0, 100, pet.ageSeconds());
}

vpet::PetState sparkmon(uint32_t stageAge, uint8_t cm) {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    readyBars(pet);
    pet.setStageAgeSeconds(stageAge);
    pet.setCareMistakes(cm);
    return pet;
}

vpet::PetState firemon(uint32_t stageAge, int hunger, int energy, int happiness, int health) {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restore(vpet::SpeciesId::Rookie, hunger, energy, happiness, 0, health, 0);
    pet.setStageAgeSeconds(stageAge);
    return pet;
}

vpet::PetState flamemon(uint32_t stageAge, int battles) {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Champion);
    readyBars(pet);
    pet.setStageAgeSeconds(stageAge);
    pet.setBattles(battles);
    return pet;
}

}

void test_egg_is_not_in_evolution_check() {
    vpet::PetState pet;
    pet.setStageAgeSeconds(99999);
    vpet::SpeciesId next = vpet::SpeciesId::Baby;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_sparkmon_one_second_short_does_not_evolve() {
    vpet::PetState pet = sparkmon(43799, 0);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_sparkmon_timer_and_cm_zero_evolves_to_firemon() {
    vpet::PetState pet = sparkmon(43800, 0);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_TRUE(vpet::Evolution().check(pet, 1, next));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, next);
}

void test_sparkmon_timer_with_two_cm_does_not_evolve() {
    vpet::PetState pet = sparkmon(43800, 2);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_firemon_timer_with_low_bars_does_not_evolve() {
    vpet::PetState pet = firemon(86400, 50, 50, 50, 70);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_firemon_timer_with_ready_bars_evolves_to_flamemon() {
    vpet::PetState pet = firemon(86400, 55, 55, 55, 75);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_TRUE(vpet::Evolution().check(pet, 1, next));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Champion, next);
}

void test_flamemon_timer_with_fourteen_battles_does_not_evolve() {
    vpet::PetState pet = flamemon(129600, 14);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_flamemon_timer_with_fifteen_battles_evolves_to_dragfiremon() {
    vpet::PetState pet = flamemon(129600, 15);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_TRUE(vpet::Evolution().check(pet, 1, next));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Ultimate, next);
}

void test_scale_600_evolves_sparkmon_at_seventy_three_seconds() {
    vpet::PetState pet = sparkmon(73, 0);
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_TRUE(vpet::Evolution().check(pet, 600, next));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, next);
}

void test_ignored_hunger_call_adds_one_care_mistake() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.restore(vpet::SpeciesId::Baby, 0, 80, 80, 0, 100, 0);
    TEST_ASSERT_EQUAL(vpet::CallUpdate::Started, pet.updateCall(0, 1));
    TEST_ASSERT_EQUAL(vpet::CallReason::Hunger, pet.callReason());
    TEST_ASSERT_EQUAL(vpet::CallUpdate::Missed, pet.updateCall(600001, 1));
    TEST_ASSERT_EQUAL(1, pet.careMistakes());
    TEST_ASSERT_EQUAL(vpet::CallReason::None, pet.callReason());
}

void test_bedtime_without_sleep_starts_lights_call() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.restore(vpet::SpeciesId::Baby, 80, 80, 80, 0, 100, 0);
    TEST_ASSERT_EQUAL(vpet::CallUpdate::Started, pet.updateCall(0, 1, 21, false));
    TEST_ASSERT_EQUAL(vpet::CallReason::Lights, pet.callReason());
}

void test_asleep_at_bedtime_does_not_start_lights_call() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.restore(vpet::SpeciesId::Baby, 80, 80, 80, 0, 100, 0);
    TEST_ASSERT_EQUAL(vpet::CallUpdate::None, pet.updateCall(0, 1, 21, true));
    TEST_ASSERT_EQUAL(vpet::CallReason::None, pet.callReason());
}

void test_rest_clears_lights_call() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.restore(vpet::SpeciesId::Baby, 80, 80, 80, 0, 100, 0);
    pet.updateCall(0, 1, 21, false);
    TEST_ASSERT_TRUE(pet.beginAction(vpet::Action::Rest));
    TEST_ASSERT_TRUE(pet.completeAction());
    TEST_ASSERT_EQUAL(vpet::CallReason::None, pet.callReason());
    TEST_ASSERT_EQUAL(vpet::CallUpdate::None, pet.updateCall(1000, 1, 22, false));
}

void test_ignored_lights_call_adds_one_care_mistake() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    pet.restore(vpet::SpeciesId::Baby, 80, 80, 80, 0, 100, 0);
    TEST_ASSERT_EQUAL(vpet::CallUpdate::Started, pet.updateCall(0, 1, 21, false));
    TEST_ASSERT_EQUAL(vpet::CallUpdate::None, pet.updateCall(600001, 1, 21, false));
    TEST_ASSERT_EQUAL(vpet::CallUpdate::Missed, pet.updateCall(3600001, 1, 21, false));
    TEST_ASSERT_EQUAL(1, pet.careMistakes());
    TEST_ASSERT_EQUAL(vpet::CallReason::None, pet.callReason());
    TEST_ASSERT_EQUAL(vpet::CallUpdate::None, pet.updateCall(3600002, 1, 22, false));
}

void test_evolution_apply_resets_care_and_keeps_wins() {
    vpet::PetState pet = sparkmon(43800, 1);
    pet.setWins(4);
    pet.setBattles(3);
    pet.restoreOverfeed(true, 3);
    TEST_ASSERT_TRUE(vpet::Evolution().evolve(pet, 1));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, pet.species());
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
    TEST_ASSERT_EQUAL(0, pet.battles());
    TEST_ASSERT_EQUAL(0, pet.stageAgeSeconds());
    TEST_ASSERT_EQUAL(4, pet.wins());
    TEST_ASSERT_EQUAL(0, pet.overfeeds());
    TEST_ASSERT_FALSE(pet.overfedThisCycle());
}

void test_force_skips_thresholds() {
    vpet::PetState pet = sparkmon(0, 9);
    TEST_ASSERT_TRUE(vpet::Evolution().force(pet));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, pet.species());
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
}

void test_schema1_load_uses_schema2_defaults_and_does_not_evolve() {
    FakeStore store;
    store.ints["schema"] = 1;
    store.ints["species"] = static_cast<int>(vpet::SpeciesId::Baby);
    store.ints["hunger"] = 80;
    store.ints["energy"] = 80;
    store.ints["happy"] = 80;
    store.ints["health"] = 100;
    store.ints["age"] = 99999;
    vpet::PetState pet;
    vpet::Settings settings;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Baby, pet.species());
    TEST_ASSERT_EQUAL(0, pet.stageAgeSeconds());
    TEST_ASSERT_EQUAL(0, pet.careMistakes());
    TEST_ASSERT_EQUAL(5, pet.weight());
    vpet::SpeciesId next = vpet::SpeciesId::Egg;
    TEST_ASSERT_FALSE(vpet::Evolution().check(pet, 1, next));
}

void test_settings_persist_care_trace() {
    FakeStore store;
    vpet::PetState saved;
    saved.evolveTo(vpet::SpeciesId::Champion);
    saved.setStageAgeSeconds(120);
    saved.setCareMistakes(2);
    saved.setBattles(7);
    saved.setWins(3);
    saved.setLosses(1);
    saved.restoreOverfeed(true, 2);
    vpet::Settings settings;
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, settings));
    TEST_ASSERT_EQUAL(3, store.ints["schema"]);
    vpet::PetState restored;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(restored, settings));
    TEST_ASSERT_EQUAL(120, restored.stageAgeSeconds());
    TEST_ASSERT_EQUAL(2, restored.careMistakes());
    TEST_ASSERT_EQUAL(7, restored.battles());
    TEST_ASSERT_EQUAL(3, restored.wins());
    TEST_ASSERT_EQUAL(1, restored.losses());
    TEST_ASSERT_EQUAL(2, restored.overfeeds());
    TEST_ASSERT_TRUE(restored.overfedThisCycle());
}

void test_unsupported_schema_is_rejected() {
    FakeStore store;
    store.ints["schema"] = 4;
    store.ints["species"] = static_cast<int>(vpet::SpeciesId::Ultimate);
    vpet::PetState pet;
    vpet::Settings settings;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Unsupported, vpet::SettingsStore(store).load(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
}

void test_care_event_ring_wraps() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    for (uint8_t i = 0; i < 33; ++i) {
        pet.record(vpet::CareEventType::Feed, i);
    }
    TEST_ASSERT_EQUAL(32, pet.careEventCount());
    TEST_ASSERT_EQUAL(1, pet.careEventIndex());
    TEST_ASSERT_EQUAL(32, pet.careEventAt(0).value);
}

void test_force_from_ultimate_restarts_as_egg() {
    vpet::PetState pet = flamemon(0, 0);
    pet.evolveTo(vpet::SpeciesId::Ultimate);
    pet.setWins(6);
    TEST_ASSERT_TRUE(vpet::Evolution().force(pet));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_EQUAL(80, pet.hunger());
    TEST_ASSERT_EQUAL(0, pet.wins());
    TEST_ASSERT_EQUAL(0, pet.stageAgeSeconds());
}

void test_reach_requirements_use_incoming_rule() {
    char buffer[40];
    vpet::Evolution evo;
    evo.writeReachRequirements(vpet::SpeciesId::Egg, false, buffer, sizeof(buffer));
    TEST_ASSERT_EQUAL_STRING("8S", buffer);
    evo.writeReachRequirements(vpet::SpeciesId::Baby, false, buffer, sizeof(buffer));
    TEST_ASSERT_EQUAL_STRING("8S", buffer);
    evo.writeReachRequirements(vpet::SpeciesId::Rookie, false, buffer, sizeof(buffer));
    TEST_ASSERT_EQUAL_STRING("12H10M CM<=1", buffer);
    evo.writeReachRequirements(vpet::SpeciesId::Champion, false, buffer, sizeof(buffer));
    TEST_ASSERT_EQUAL_STRING("24H H55 E55 P55 HP75", buffer);
    evo.writeReachRequirements(vpet::SpeciesId::Ultimate, false, buffer, sizeof(buffer));
    TEST_ASSERT_EQUAL_STRING("36H BAT15 WR60", buffer);
}

void test_missing_life_key_restarts_as_egg() {
    FakeStore store;
    store.ints["schema"] = 2;
    store.ints["species"] = static_cast<int>(vpet::SpeciesId::Ultimate);
    store.ints["hunger"] = 10;
    store.ints["age"] = 999;
    vpet::PetState pet;
    vpet::Settings settings;
    settings.language = "EN";
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).restartLifeIfNeeded(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_EQUAL(80, pet.hunger());
    TEST_ASSERT_EQUAL(1, store.ints["life"]);
    TEST_ASSERT_FALSE(vpet::SettingsStore(store).restartLifeIfNeeded(pet, settings));
}

void test_snapshot_is_twenty_bytes() {
    TEST_ASSERT_EQUAL(20, sizeof(vpet::CareSnapshot));
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Baby);
    const vpet::CareSnapshot snap = pet.snapshot();
    TEST_ASSERT_EQUAL(1, snap.schema);
    TEST_ASSERT_EQUAL(static_cast<uint8_t>(vpet::SpeciesId::Baby), snap.species);
}
