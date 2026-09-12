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
