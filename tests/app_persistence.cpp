#include <cassert>
#include <map>
#include <string>
#include <Arduino.h>
#include "vpet/App.h"
SerialMock Serial;

struct Store : vpet::KeyValueStore {
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    bool fail = false;
    bool syncFail = false, pendingOnCommit = false;
    int32_t getInt(const char* k, int32_t f) override { return ints.count(k) ? ints[k] : f; }
    bool putInt(const char* k, int32_t v) override { if(fail) return false; ints[k] = v; return true; }
    std::string getString(const char* k, const char* f) override { return strings.count(k) ? strings[k] : f; }
    bool putString(const char* k, const char* v) override { if(fail) return false; strings[k] = v; return true; }
    vpet::StoreCommit commitString(const char* k, const char* v) override {
        if (!putString(k, v)) return vpet::StoreCommit::Rejected;
        if (pendingOnCommit) { syncFail = true; return vpet::StoreCommit::Pending; }
        return vpet::StoreCommit::Committed;
    }
    bool sync() override { return !syncFail; }
};

int main() {
    using namespace vpet;
    Store kv; SettingsStore storage(kv); Renderer renderer; Panels panels; BleService ble;
    App app(renderer, panels, storage, ble);
    kv.fail = true;
    app.begin(0);
    assert(!app.ready());
    assert(kv.ints.empty());
    kv.fail = false;
    app.tick(1100, InputEvent::None);
    assert(app.ready());
    assert(kv.ints["life"] == 1);

    kv.strings["saveTx"] = "99 future";
    app.begin(2000);
    assert(!app.ready());
    assert(kv.strings["saveTx"] == "99 future");
    kv.strings["saveTx"].clear();

    PetState pet;
    pet.evolveTo(SpeciesId::Rookie); pet.rollDna(42); pet.setInjured(true);
    Settings settings;
    assert(storage.save(pet, settings));
    app.begin(3000); assert(app.ready());
    kv.fail = true;
    app.tick(63000, InputEvent::None);
    assert(!app.ready());
    assert(panels.errors > 0);
    assert(Serial.output.find("VPET_SAVE_PENDING") != std::string::npos);
    kv.fail = false;
    app.tick(64000, InputEvent::Action);
    assert(app.ready());
    PetState reloaded;
    assert(storage.load(reloaded, settings) == LoadResult::Loaded);
    assert(reloaded.injuredMs() == 60000);

    settings.bluetoothEnabled = true;
    assert(storage.save(reloaded, settings));
    ble.fail = true;
    app.begin(65000); assert(!app.ready());
    ble.fail = false;
    app.tick(66100, InputEvent::None); assert(app.ready());
    assert(ble.enabled);
    kv.pendingOnCommit = true;
    app.tick(126100, InputEvent::None);
    assert(!app.ready());
    assert(kv.ints["injuredMs"] == 60000);  // No mirror before confirmed sync.
    kv.pendingOnCommit = kv.syncFail = false;
    app.tick(127100, InputEvent::None);
    assert(app.ready());
    assert(storage.load(reloaded, settings) == LoadResult::Loaded);
    assert(reloaded.injuredMs() == 120000);
}
