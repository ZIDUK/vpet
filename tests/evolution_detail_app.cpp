#include <cassert>
#include <map>
#include <string>
#include <Arduino.h>
#include "vpet/App.h"

SerialMock Serial;
struct Store : vpet::KeyValueStore {
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    int32_t getInt(const char* k, int32_t fallback) override { return ints.count(k) ? ints[k] : fallback; }
    std::string getString(const char* k, const char* fallback) override { return strings.count(k) ? strings[k] : fallback; }
    bool putInt(const char* k, int32_t value) override { ints[k] = value; return true; }
    bool putString(const char* k, const char* value) override { strings[k] = value; return true; }
};

int main() {
    using namespace vpet;
    Store kv;
    SettingsStore storage(kv);
    Settings settings;
    PetState pet;
    pet.restore(SpeciesId::Rookie, 80, 80, 80, 0, 90, 0);
    pet.rollDna(42);
    pet.setWeight(10);
    assert(storage.save(pet, settings));
    Renderer renderer;
    Panels panels;
    BleService ble;
    App app(renderer, panels, storage, ble);
    app.begin(0);
    assert(app.ready());
    const auto ints = kv.ints;
    const auto strings = kv.strings;
    uint32_t ms = 0;
    auto key = [&](InputEvent event) { ms += 50; app.tick(ms, event); };
    for (int i = 0; i < 7; ++i) key(InputEvent::Next);
    key(InputEvent::Action);
    assert(panels.lastPanel == PanelId::EvolutionTree && panels.panelIndex == 2);
    key(InputEvent::Action);
    assert(panels.lastPanel == PanelId::EvolutionDetail && panels.detailPage == 0);
    key(InputEvent::Next);
    assert(panels.panelIndex == 2 && panels.detailPage == 1);
    key(InputEvent::Next);
    assert(panels.panelIndex == 2 && panels.detailPage == 0);
    key(InputEvent::Next);
    key(InputEvent::Back);
    assert(panels.lastPanel == PanelId::EvolutionTree && panels.panelIndex == 2);
    key(InputEvent::Action);
    assert(panels.lastPanel == PanelId::EvolutionDetail && panels.detailPage == 0);
    key(InputEvent::Action);
    assert(panels.lastPanel == PanelId::EvolutionTree && panels.panelIndex == 2);
    // Past stages keep a single page and never compare this pet's current stats.
    key(InputEvent::Next); key(InputEvent::Next); key(InputEvent::Next); key(InputEvent::Next);
    assert(panels.panelIndex == 1);
    key(InputEvent::Action);
    key(InputEvent::Next);
    assert(panels.panelIndex == 1 && panels.detailPage == 0);
    assert(kv.ints == ints && kv.strings == strings);
}
