#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include "vpet/SettingsStore.h"

struct Fault {
    int cut = -1, writes = 0;
    bool fail = false;
    bool before() {
        if (cut >= 0 && writes == cut) throw 1;
        ++writes;
        return !fail;
    }
};
struct Store : vpet::KeyValueStore {
    Fault* fault;
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    explicit Store(Fault& f) : fault(&f) {}
    int32_t getInt(const char* k, int32_t f) override { return ints.count(k) ? ints[k] : f; }
    bool putInt(const char* k, int32_t v) override {
        if (!fault->before()) return false;
        ints[k] = v; return true;
    }
    std::string getString(const char* k, const char* f) override { return strings.count(k) ? strings[k] : f; }
    bool putString(const char* k, const char* v) override {
        if (!fault->before()) return false;
        strings[k] = v; return true;
    }
};
using namespace vpet;

PetState pet(SpeciesId species, int hunger) {
    PetState p;
    p.evolveTo(species); p.rollDna(hunger); p.setHunger(hunger);
    p.practice.bond = hunger;
    p.adoptedStock.seed();
    p.adoptedStock.set(2, hunger);
    return p;
}
void identity(const PetState& p, const PetState& expected) {
    assert(p.species() == expected.species());
    assert(p.hunger() == expected.hunger());
    assert(p.practice.bond == expected.practice.bond);
    assert(p.adoptedStock.encode() == expected.adoptedStock.encode());
    for (int i = 0; i < 4; ++i) assert(p.dna()[i] == expected.dna()[i]);
}

void save_cuts() {
    Fault f; Store initial(f); Settings settings;
    auto old = pet(SpeciesId::Rookie, 20), next = pet(SpeciesId::Champion, 90);
    assert(SettingsStore(initial).save(old, settings));
    Store expected = initial; f.writes = 0;
    assert(SettingsStore(expected).save(next, settings));
    const int writes = f.writes;
    for (int cut = 0; cut <= writes; ++cut) {
        Store kv = initial; SettingsStore persistence(kv);
        f.writes = 0; f.cut = cut;
        try { persistence.save(next, settings); } catch (int) {}
        f.cut = -1;
        PetState restored;
        assert(persistence.load(restored, settings) == LoadResult::Loaded);
        identity(restored, cut == 0 ? old : next);
        assert(kv.ints == (cut == 0 ? initial.ints : expected.ints));
        PetState again;
        assert(persistence.load(again, settings) == LoadResult::Loaded);
        identity(again, restored);
    }
    std::cout << "save: " << writes + 1 << " interruption points\n";
}

void swap_cuts(bool park) {
    Fault f; Store live(f), backup(f); Settings settings;
    auto active = pet(SpeciesId::Rookie, 22), parked = pet(SpeciesId::Champion, 88);
    SettingsStore persistence(live, &backup);
    assert(persistence.save(active, settings));
    if (!park) assert(SettingsStore(backup).save(parked, settings));
    const Store originalLive = live, originalBackup = backup;
    PetState target = active;
    f.writes = 0; assert(persistence.swapOrPark(target, settings));
    const int writes = f.writes;
    const Store expectedLive = live, expectedBackup = backup;
    for (int cut = 0; cut <= writes; ++cut) {
        live = originalLive; backup = originalBackup;
        f.writes = 0; f.cut = cut;
        PetState current = active;
        try { persistence.swapOrPark(current, settings); } catch (int) {}
        const bool committed = live.getString("swapTx", "") == "1" || cut == writes;
        f.cut = -1;
        PetState restored;
        assert(persistence.load(restored, settings) == LoadResult::Loaded);
        identity(restored, committed ? target : active);
        assert(live.ints == (committed ? expectedLive.ints : originalLive.ints));
        assert(backup.ints == (committed ? expectedBackup.ints : originalBackup.ints));
        if (committed || !park) {
            PetState other;
            assert(SettingsStore(backup).load(other, settings) == LoadResult::Loaded);
            identity(other, committed ? active : parked);
        }
    }
    std::cout << (park ? "park" : "swap") << ": " << writes + 1 << " interruption points\n";
}

void injury_continuity() {
    Fault f; Store kv(f); Settings settings;
    auto p = pet(SpeciesId::Rookie, 80);
    p.setInjured(true); p.tick(21599000);
    assert(!p.dead());
    assert(SettingsStore(kv).save(p, settings));
    PetState restored;
    assert(SettingsStore(kv).load(restored, settings) == LoadResult::Loaded);
    restored.tick(1000); assert(restored.dead());
    kv.ints.erase("injuredMs");
    assert(SettingsStore(kv).load(restored, settings) == LoadResult::Loaded);
    restored.tick(1000); assert(!restored.dead());
    std::cout << "injury: continuity and legacy default\n";
}

void invalid_journals() {
    Fault f; Store kv(f), backup(f); Settings settings;
    auto original = pet(SpeciesId::Rookie, 60);
    SettingsStore store(kv, &backup);
    assert(store.save(original, settings));
    const auto before = kv.ints;
    for (const char* key : {"saveTx", "swapTx"}) {
        kv.strings[key] = "99 broken";
        PetState loaded;
        assert(store.load(loaded, settings) == LoadResult::Unsupported);
        assert(kv.ints == before);
        kv.strings[key].clear();
    }
    std::cout << "journals: unknown versions fail closed\n";
}

void recovery_cuts(bool swap) {
    Fault f; Store live(f), backup(f); Settings settings;
    auto old = pet(SpeciesId::Rookie, 20), next = pet(SpeciesId::Champion, 90);
    SettingsStore persistence(live, &backup);
    assert(persistence.save(old, settings));
    assert(SettingsStore(backup).save(next, settings));
    f.writes = 0; f.cut = swap ? 3 : 1;
    auto current = old;
    try {
        if (swap) persistence.swapOrPark(current, settings);
        else persistence.save(next, settings);
    } catch (int) {}
    f.cut = -1;
    const Store pendingLive = live, pendingBackup = backup;
    f.writes = 0;
    PetState restored;
    assert(persistence.load(restored, settings) == LoadResult::Loaded);
    const int writes = f.writes;
    for (int cut = 0; cut <= writes; ++cut) {
        live = pendingLive; backup = pendingBackup;
        f.writes = 0; f.cut = cut;
        try { persistence.load(restored, settings); } catch (int) {}
        f.cut = -1; f.fail = true;
        assert(persistence.load(restored, settings) == (cut == writes ? LoadResult::Loaded : LoadResult::Unsupported));
        f.fail = false;
        assert(persistence.load(restored, settings) == LoadResult::Loaded);
        identity(restored, next);
        assert(persistence.load(restored, settings) == LoadResult::Loaded);
        identity(restored, next);
        if (swap) {
            assert(SettingsStore(backup).load(restored, settings) == LoadResult::Loaded);
            identity(restored, old);
        }
    }
    std::cout << (swap ? "swap recovery" : "save recovery") << ": " << writes + 1 << " repeated failure points\n";
}

void first_save_and_limits() {
    Fault f; Store kv(f); Settings settings;
    auto next = pet(SpeciesId::Ultimate, 99);
    for (int i = 0; i < adopted::kCount; ++i) next.adoptedStock.set(i, 99);
    next.adoptedStock.cursor = 39; next.adoptedStock.rewards = UINT32_MAX;
    f.cut = 1;
    try { SettingsStore(kv).save(next, settings); } catch (int) {}
    f.cut = -1;
    const std::string record = kv.strings["saveTx"];
    assert(!record.empty() && record.size() < 3800);
    const Store pending = kv;
    f.writes = 0; PetState restored;
    assert(SettingsStore(kv).load(restored, settings) == LoadResult::Loaded);
    const int writes = f.writes;
    for (int cut = 0; cut <= writes; ++cut) {
        kv = pending; f.writes = 0; f.cut = cut;
        try { SettingsStore(kv).load(restored, settings); } catch (int) {}
        f.cut = -1;
        assert(SettingsStore(kv).load(restored, settings) == LoadResult::Loaded);
        identity(restored, next);
    }
    const auto ints = kv.ints;
    for (auto invalid : {record.substr(0, record.size() / 2), std::string(4001, 'x'), record + "trailing\n"}) {
        kv.strings["saveTx"] = invalid;
        const auto result = SettingsStore(kv).load(restored, settings);
        if (result != LoadResult::Unsupported) std::cerr << "accepted invalid snapshot: " << invalid.size() << " bytes\n";
        assert(result == LoadResult::Unsupported);
        assert(kv.ints == ints);
    }
    std::cout << "initial recovery: " << writes + 1 << " points; max-stock payload " << record.size() << " bytes\n";
}

int main(int argc, char** argv) {
    const std::string which = argc > 1 ? argv[1] : "all";
    if (which == "save" || which == "all") save_cuts();
    if (which == "swap" || which == "all") { swap_cuts(false); swap_cuts(true); }
    if (which == "injury" || which == "all") injury_continuity();
    if (which == "invalid" || which == "all") invalid_journals();
    if (which == "recovery" || which == "all") { recovery_cuts(false); recovery_cuts(true); first_save_and_limits(); }
}
