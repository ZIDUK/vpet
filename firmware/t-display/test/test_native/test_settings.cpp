#include <map>
#include <string>
#include <unity.h>

#include "vpet/BleAdvertiseSession.h"
#include "vpet/SettingsStore.h"

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

void test_missing_save_keeps_current_species_discovered() {
    FakeStore store;
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Champion);
    vpet::Settings settings;
    vpet::SettingsStore(store).load(pet, settings);
    TEST_ASSERT_TRUE(pet.hasDiscovered(vpet::SpeciesId::Champion));
}

void test_first_advertise_configures_payload_later_restarts_only() {
    vpet::BleAdvertiseSession session;
    TEST_ASSERT_EQUAL(vpet::BleAdvertiseStep::Configure, session.nextStart());
    TEST_ASSERT_EQUAL(vpet::BleAdvertiseStep::StartOnly, session.nextStart());
    TEST_ASSERT_EQUAL(vpet::BleAdvertiseStep::StartOnly, session.nextStart());
    session.reset();
    TEST_ASSERT_EQUAL(vpet::BleAdvertiseStep::Configure, session.nextStart());
}

void test_settings_persist_bluetooth_preference() {
    FakeStore store;
    vpet::PetState saved;
    vpet::Settings before;
    before.bluetoothEnabled = true;
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, before));

    vpet::PetState restored;
    vpet::Settings after;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded,
                      vpet::SettingsStore(store).load(restored, after));
    TEST_ASSERT_TRUE(after.bluetoothEnabled);
}

void test_settings_persist_inventory_counts() {
    FakeStore store;
    vpet::PetState saved;
    saved.evolveTo(vpet::SpeciesId::Rookie);
    saved.useItem(0);
    vpet::Settings settings;
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, settings));
    vpet::PetState restored;
    vpet::Settings after;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(restored, after));
    TEST_ASSERT_EQUAL(2, restored.itemCount(0));
    TEST_ASSERT_EQUAL(2, restored.itemCount(1));
}

void test_backup_parks_current_pet_and_starts_egg() {
    FakeStore live;
    FakeStore backup;
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restore(vpet::SpeciesId::Rookie, 80, 80, 80, 0, 100, 40);
    vpet::Settings settings;
    vpet::SettingsStore store(live, &backup);
    TEST_ASSERT_FALSE(store.hasBackup());
    TEST_ASSERT_TRUE(store.swapOrPark(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_TRUE(store.hasBackup());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Rookie, store.backupSpecies());
}

void test_backup_swap_restores_parked_pet() {
    FakeStore live;
    FakeStore backup;
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Champion, 70, 70, 70, 0, 90, 10);
    pet.setCold(true);
    vpet::Settings settings;
    vpet::SettingsStore store(live, &backup);
    TEST_ASSERT_TRUE(store.swapOrPark(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Egg, pet.species());
    TEST_ASSERT_FALSE(pet.cold());
    TEST_ASSERT_TRUE(store.swapOrPark(pet, settings));
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Champion, pet.species());
    TEST_ASSERT_EQUAL(70, pet.hunger());
    TEST_ASSERT_TRUE(pet.cold());
}

void test_settings_persist_dna_and_ev() {
    FakeStore store;
    vpet::PetState saved;
    saved.evolveTo(vpet::SpeciesId::Rookie);
    saved.rollDna(42);
    const uint8_t ev[] = {10, 8, 6, 4, 2, 12};
    saved.restoreEv(ev);
    vpet::Settings settings;
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, settings));
    TEST_ASSERT_EQUAL(3, store.ints["schema"]);
    vpet::PetState restored;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(restored, settings));
    TEST_ASSERT_EQUAL(saved.dna()[0], restored.dna()[0]);
    TEST_ASSERT_EQUAL(saved.dna()[3], restored.dna()[3]);
    TEST_ASSERT_EQUAL(10, restored.evAt(vpet::CombatStat::Hp));
    TEST_ASSERT_EQUAL(12, restored.evAt(vpet::CombatStat::Brn));
}

void test_schema2_rookie_synthesizes_stable_dna() {
    FakeStore store;
    store.ints["schema"] = 2;
    store.ints["species"] = static_cast<int>(vpet::SpeciesId::Rookie);
    store.ints["hunger"] = 80;
    store.ints["energy"] = 80;
    store.ints["happy"] = 80;
    store.ints["health"] = 100;
    store.ints["age"] = 40;
    store.ints["wins"] = 0;
    vpet::PetState first;
    vpet::Settings settings;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(first, settings));
    TEST_ASSERT_TRUE(first.hasDna());
    vpet::PetState second;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(second, settings));
    TEST_ASSERT_EQUAL(first.dna()[0], second.dna()[0]);
    TEST_ASSERT_EQUAL(first.dna()[1], second.dna()[1]);
    TEST_ASSERT_EQUAL(first.dna()[2], second.dna()[2]);
    TEST_ASSERT_EQUAL(first.dna()[3], second.dna()[3]);
    vpet::PetState expected;
    expected.rollDna(40U * 2654435761U + static_cast<uint32_t>(vpet::SpeciesId::Rookie));
    TEST_ASSERT_EQUAL(expected.dna()[0], first.dna()[0]);
    TEST_ASSERT_EQUAL(expected.dna()[1], first.dna()[1]);
}

void test_missing_inventory_keys_use_defaults() {
    FakeStore store;
    store.ints["schema"] = 1;
    store.ints["species"] = 0;
    vpet::PetState pet;
    vpet::Settings settings;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(pet, settings));
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(1));
    TEST_ASSERT_EQUAL(1, pet.itemCount(2));
    TEST_ASSERT_EQUAL(1, pet.itemCount(3));
}
