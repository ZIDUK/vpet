#include <map>
#include <string>
#include <unity.h>

#include "vpet/NetworkService.h"
#include "vpet/PasswordEditor.h"
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

class FakeNetwork : public vpet::NetworkAdapter {
public:
    void startScan() override {}
    bool scanComplete() override { return true; }
    size_t networkCount() const override { return 1; }
    std::string networkName(size_t) const override { return "Home"; }
    void beginConnect(const char*, const char*) override {}
    vpet::ConnectResult connectionResult() override { return result; }
    bool syncClock() override { return true; }
    vpet::ConnectResult result = vpet::ConnectResult::Connecting;
};

void test_missing_save_keeps_current_species_discovered() {
    FakeStore store;
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Champion);
    vpet::Settings settings;
    vpet::SettingsStore(store).load(pet, settings);
    TEST_ASSERT_TRUE(pet.hasDiscovered(vpet::SpeciesId::Champion));
}

void test_credentials_are_saved_only_after_internet_capable_connection() {
    FakeStore store;
    FakeNetwork wifi;
    vpet::NetworkService service(wifi, store);
    service.connect("Home", "secret");
    wifi.result = vpet::ConnectResult::LocalOnly;
    service.poll();
    TEST_ASSERT_EQUAL_STRING("", store.getString("ssid", "").c_str());
    wifi.result = vpet::ConnectResult::InternetAvailable;
    service.poll();
    TEST_ASSERT_EQUAL_STRING("Home", store.getString("ssid", "").c_str());
    TEST_ASSERT_EQUAL_STRING("secret", store.getString("password", "").c_str());
}

void test_password_editor_cycles_groups_and_submits_masked_value() {
    vpet::PasswordEditor editor;
    editor.select();
    TEST_ASSERT_EQUAL_STRING("A", editor.password().c_str());
    editor.selectCommand(vpet::PasswordCommand::Mode);
    editor.select();
    TEST_ASSERT_EQUAL_STRING("Aa", editor.password().c_str());
    TEST_ASSERT_TRUE(editor.selectCommand(vpet::PasswordCommand::Connect));
}
