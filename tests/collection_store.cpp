#include <cassert>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <type_traits>
#include <cstdio>
#include <cstdlib>
#include <sys/stat.h>
#include <unistd.h>
#include "vpet/CollectionStore.h"
#include "vpet/LittleFsCollectionRepository.h"

using namespace vpet;

// Implements the adapter's atomic visibility contract, with failure at every IO.
struct MemoryRepository : CollectionRepository {
    std::vector<uint8_t> durable, prepared;
    uint64_t sequence = 0;
    int failAt = -1, operations = 0, commits = 0;
    bool damagePrepared = false;
    bool step() { return operations++ != failAt; }
    CollectionRead size(size_t& bytes) override {
        if (!step()) return CollectionRead::Error;
        bytes = durable.size();
        return bytes ? CollectionRead::Present : CollectionRead::Missing;
    }
    bool read(size_t at, void* data, size_t bytes) override {
        if (!step() || at > durable.size() || bytes > durable.size()-at) return false;
        std::memcpy(data, durable.data()+at, bytes); return true;
    }
    bool begin(uint64_t expectedSequence, size_t bytes) override {
        if (!step() || expectedSequence != sequence || bytes > CollectionStore::kMaxRecordBytes) return false;
        prepared.assign(bytes, 0); return true;
    }
    bool write(size_t at, const void* data, size_t bytes) override {
        if (!step() || at > prepared.size() || bytes > prepared.size()-at) return false;
        std::memcpy(prepared.data()+at, data, bytes); return true;
    }
    bool readPrepared(size_t at, void* data, size_t bytes) override {
        if (!step() || at > prepared.size() || bytes > prepared.size()-at) return false;
        if (damagePrepared) { prepared.back() ^= 1; damagePrepared = false; }
        std::memcpy(data, prepared.data()+at, bytes); return true;
    }
    bool commit(uint64_t nextSequence) override {
        if (!step()) return false;
        durable.swap(prepared); prepared.clear(); sequence = nextSequence; ++commits; return true;
    }
    void abort() override { prepared.clear(); }
};

PetProfile profile(uint32_t n, const std::string& a = "", const std::string& b = "") {
    const uint32_t words[] = {n, 3, 4, 5};
    return PetProfile::fromWords(words, a, b);
}
PetState pet(uint32_t n, uint8_t stock = 2) {
    PetState p;
    p.profile = profile(n);
    p.restore(SpeciesId::Rookie, 90, 90, 90, 0, 100, 125);
    p.restoreItems(3, stock, 1, 1, 2, 1);
    const uint8_t dna[] = {12, 34, 56, 78}; p.restoreDna(dna);
    p.adoptedStock.set(0, 1); p.adoptedStock.cursor = 3; p.adoptedStock.rewards = 11;
    return p;
}
std::string capture(const PetState& p) {
    std::string record; assert(CollectionStore::capture(p, Settings(), record)); return record;
}
void initialize(MemoryRepository& repo, CollectionState& state, PetState& active, bool backup = true) {
    const auto a = capture(active), b = capture(pet(3, 99));
    CollectionStore store(repo);
    assert(store.migrate(state, a, backup ? &b : nullptr));
}
void roundtrip() {
    static_assert(std::is_trivially_copyable<CollectionState>::value, "Metadata must not own dynamic allocations");
    assert(sizeof(CollectionState) <= 2048);
    MemoryRepository repo; CollectionStore store(repo); CollectionState state;
    auto active = pet(2); initialize(repo, state, active);
    assert(state.count() == 2 && state.active == 0 && state.stock[1] == 2);
    assert(state.adoptedStock.rewards == 11 && state.slots[0].profile().petId() == active.profile.petId());
    CollectionState loaded;
    assert(store.load(loaded) == CollectionLoad::Loaded && loaded.sequence == state.sequence);
    PetState decoded; Settings settings;
    assert(store.readPet(loaded, 1, decoded, settings));
    assert(decoded.itemCount(1) == 2 && decoded.ageSeconds() == 125);
    assert(decoded.adoptedStock.encode() == state.adoptedStock.encode());
    auto original = decoded.profile.encode();
    assert(!CollectionStore::restore("future", decoded, settings) && decoded.profile.encode() == original);
    assert(repo.durable.size() <= CollectionStore::kMaxRecordBytes);
    assert(store.saveActive(state, active, settings, "policy-0001.bin"));
    assert(store.load(loaded) == CollectionLoad::Loaded && std::string(loaded.slots[0].learningRef) == "policy-0001.bin");
    const auto committed = repo.durable;
    assert(!store.saveActive(state, active, settings, "../unsafe") && repo.durable == committed);
    // Zero is a valid inherited genome, including after an egg becomes live.
    const uint8_t zeroDna[4] = {};
    auto zeroChild = pet(6);
    zeroChild.profile = profile(6, profile(2).petId(), profile(3).petId());
    zeroChild.restoreDna(zeroDna);
    PetState zeroDecoded;
    assert(CollectionStore::restore(capture(zeroChild), zeroDecoded, settings));
    assert(std::memcmp(zeroDecoded.dna(), zeroDna, sizeof(zeroDna)) == 0);
    MemoryRepository childRepo; CollectionStore childStore(childRepo); CollectionState childState;
    assert(childStore.migrate(childState, capture(zeroChild)));
    assert(childStore.readPet(childState, 0, zeroDecoded, settings));
    assert(std::memcmp(zeroDecoded.dna(), zeroDna, sizeof(zeroDna)) == 0);
    assert(childStore.saveActive(childState, zeroDecoded, settings));
    CollectionStore childReboot(childRepo); CollectionState reloaded;
    assert(childReboot.load(reloaded) == CollectionLoad::Loaded);
    assert(childReboot.readPet(reloaded, 0, zeroDecoded, settings));
    assert(std::memcmp(zeroDecoded.dna(), zeroDna, sizeof(zeroDna)) == 0);
    std::cout << "metadata bytes=" << sizeof(CollectionState) << ", record bytes=" << repo.durable.size() << '\n';
}
void migration() {
    auto p = pet(2); const auto a = capture(p);
    MemoryRepository repo; CollectionStore store(repo); CollectionState state;
    assert(store.migrate(state, a, &a) && state.count() == 1);
    const auto committed = repo.durable;
    assert(store.migrate(state, "ignored on retry") && repo.durable == committed);
    auto changed = p; changed.setHealth(81); const auto b = capture(changed);
    MemoryRepository conflict; CollectionStore conflicting(conflict); CollectionState untouched;
    assert(!conflicting.migrate(untouched, a, &b) && conflict.durable.empty() && untouched.count() == 0);
    MemoryRepository missing; CollectionStore migrating(missing);
    p.profile = PetProfile(); const auto legacy = capture(p);
    assert(!migrating.migrate(untouched, legacy));
    assert(migrating.migrate(untouched, legacy, nullptr, profile(42)));
    assert(untouched.slots[0].profile().petId() == profile(42).petId());
    const auto id = untouched.slots[0].profile().petId();
    assert(migrating.migrate(untouched, legacy, nullptr, profile(44)));
    assert(untouched.slots[0].profile().petId() == id);
}
void switching() {
    MemoryRepository repo; CollectionStore store(repo); CollectionState state;
    auto active = pet(2); initialize(repo, state, active); Settings settings;
    active.restoreItems(3, 0, 1, 1, 2, 1);
    active.adoptedStock.cursor = 5; active.adoptedStock.rewards = 19;
    CollectionSwitchGuard guard; guard.arena = true;
    const auto before = repo.durable;
    assert(!store.activate(state, 1, active, settings, guard, true));
    assert(repo.durable == before && state.active == 0);
    guard.arena = false;
    assert(!store.activate(state, 1, active, settings, guard, false));
    assert(store.activate(state, 1, active, settings, guard, true));
    assert(active.profile.petId() == profile(3).petId() && active.itemCount(1) == 0);
    assert(active.adoptedStock.rewards == 19 && state.stock[1] == 0);
    assert(store.activate(state, 0, active, settings, guard, true));
    assert(active.itemCount(1) == 0 && active.ageSeconds() == 125);
    active.beginAction(Action::Training);
    assert(!store.activate(state, 1, active, settings, guard, true));
}
void eggs() {
    MemoryRepository repo; CollectionStore store(repo); CollectionState state;
    auto active = pet(2); initialize(repo, state, active); Settings settings;
    PetState founder; founder.profile = profile(4);
    const auto before = repo.durable;
    assert(!store.addFounder(state, founder, settings, false) && repo.durable == before);
    assert(store.addFounder(state, founder, settings, true) && state.count() == 3);
    assert(state.slots[2].incubationRequiredMs == 0);
    assert(state.stock[1] == 2 && state.adoptedStock.rewards == 11);
    CollectionEggTransaction tx; tx.id = 77; tx.seed = 19; tx.parentA = 0; tx.parentB = 1;
    PetState egg; egg.profile = profile(6, profile(2).petId(), profile(3).petId());
    const uint8_t zeroDna[4] = {}; egg.restoreDna(zeroDna);
    size_t child = 99;
    assert(store.commitEgg(state, tx, egg, settings, child, true) && child == 3 && state.count() == 4);
    const auto committed = repo.durable; const auto sequence = state.sequence;
    tx.seed = 999; egg.profile = profile(8);
    assert(store.commitEgg(state, tx, egg, settings, child, true));
    assert(child == 3 && state.sequence == sequence && repo.durable == committed);
    assert(!store.addFounder(state, egg, settings, true));
    assert(state.slots[0].cooldownMs == 86400000 && state.slots[3].incubationMs == 0);
    assert(store.advance(state, 1000, false));
    assert(state.slots[0].cooldownMs == 86399000 && state.slots[3].incubationMs == 0);
    assert(store.activate(state, 3, active, settings, CollectionSwitchGuard(), true));
    assert(store.advance(state, 1000, false) && state.slots[3].incubationMs == 1000);
    assert(store.advance(state, 9000, true) && state.slots[3].incubationMs == 1000);
    assert(store.readPet(state, 3, egg, settings) && egg.itemCount(1) == 2);
    assert(std::memcmp(egg.dna(), zeroDna, sizeof(zeroDna)) == 0);
    assert(egg.profile.petId() == profile(6, profile(2).petId(), profile(3).petId()).petId());
    CollectionState reboot; assert(store.load(reboot) == CollectionLoad::Loaded);
    assert(reboot.slots[3].breedingId == 77 && reboot.slots[3].seed == 19);
    CollectionStore afterRestart(repo);
    assert(afterRestart.commitEgg(reboot, tx, egg, settings, child, true) && child == 3);
    assert(reboot.count() == 4 && reboot.slots[3].seed == 19);
    assert(afterRestart.advance(reboot, 1800000, false));
    egg.restore(SpeciesId::Baby, 90, 90, 90, 0, 100, 0);
    assert(afterRestart.saveActive(reboot, egg, settings));
    assert(afterRestart.readPet(reboot, child, egg, settings));
    assert(std::memcmp(egg.dna(), zeroDna, sizeof(zeroDna)) == 0);
}
template<class Operation>
void rejectAtEveryIo(const MemoryRepository& original, const CollectionState& initial, Operation operation) {
    MemoryRepository success = original; CollectionState next = initial;
    success.operations = 0; CollectionStore successful(success);
    assert(operation(successful, next));
    const auto expected = success.durable; const int count = success.operations;
    for (int cut = 0; cut < count; ++cut) {
        MemoryRepository repo = original; repo.operations = 0; repo.failAt = cut;
        CollectionState state = initial; const CollectionState before = state; CollectionStore store(repo);
        const bool ok = operation(store, state);
        if (!ok) {
            assert(std::memcmp(&state, &before, sizeof(state)) == 0 && repo.durable == original.durable);
        } else assert(repo.durable == expected);
        repo.failAt = -1; CollectionStore reboot(repo); CollectionState loaded;
        assert(reboot.load(loaded) == (repo.durable.empty() ? CollectionLoad::Missing : CollectionLoad::Loaded));
    }
    std::cout << "transaction IO failure points=" << count << '\n';
}
void failures() {
    MemoryRepository original; CollectionState initial; auto active = pet(2);
    initialize(original, initial, active);
    MemoryRepository successful = original; CollectionState next = initial;
    CollectionStore trial(successful); Settings settings; auto changed = active;
    changed.restoreItems(3, 0, 1, 1, 2, 1); successful.operations = 0;
    assert(trial.saveActive(next, changed, settings));
    const auto final = successful.durable; const int count = successful.operations;
    for (int cut = 0; cut < count; ++cut) {
        MemoryRepository repo = original; repo.operations = 0; repo.failAt = cut;
        CollectionState state = initial; CollectionStore store(repo);
        const bool ok = store.saveActive(state, changed, settings);
        if (!ok) {
            assert(state.sequence == initial.sequence && state.stock[1] == initial.stock[1]);
            assert(repo.durable == original.durable);
        } else assert(repo.durable == final);
        repo.failAt = -1; CollectionStore reboot(repo); CollectionState recovered;
        assert(reboot.load(recovered) == CollectionLoad::Loaded);
        assert(recovered.stock[1] == (ok ? 0 : 2));
    }
    // A stale view cannot overwrite a newer commit from another store object.
    CollectionStore stale(successful);
    assert(!stale.saveActive(initial, active, settings) && successful.durable == final);
    rejectAtEveryIo(original, initial, [&](CollectionStore& store, CollectionState& state) {
        auto currentPet = active; Settings currentSettings;
        const auto profileBefore = currentPet.profile.encode();
        const bool ok = store.activate(state, 1, currentPet, currentSettings, CollectionSwitchGuard(), true);
        if (!ok) assert(currentPet.profile.encode() == profileBefore);
        return ok;
    });
    rejectAtEveryIo(original, initial, [&](CollectionStore& store, CollectionState& state) {
        CollectionEggTransaction tx; tx.id = 91;
        PetState egg; egg.profile = profile(8, profile(2).petId(), profile(3).petId());
        size_t slot = 99;
        const bool ok = store.commitEgg(state, tx, egg, Settings(), slot, true);
        if (!ok) assert(slot == 99);
        return ok;
    });
    const auto legacy = capture(active), legacyBackup = capture(pet(3));
    rejectAtEveryIo(MemoryRepository(), CollectionState(), [&](CollectionStore& store, CollectionState& state) {
        return store.migrate(state, legacy, &legacyBackup);
    });
    MemoryRepository damaged = original; damaged.damagePrepared = true;
    CollectionStore damagedStore(damaged); CollectionState state = initial;
    assert(!damagedStore.saveActive(state, changed, settings));
    assert(damaged.durable == original.durable && state.sequence == initial.sequence);
    std::cout << "atomic IO failure points=" << count << '\n';
}
void corruption() {
    MemoryRepository original; CollectionState initial; auto active = pet(2);
    initialize(original, initial, active);
    for (size_t at = 0; at < original.durable.size(); ++at) {
        MemoryRepository repo = original; repo.durable[at] ^= 0x80;
        CollectionStore store(repo); CollectionState state;
        assert(store.load(state) != CollectionLoad::Loaded && state.count() == 0);
        const auto corrupt = repo.durable;
        assert(!store.saveActive(initial, active, Settings()) && repo.durable == corrupt);
    }
    MemoryRepository future = original; future.durable[4] = 2;
    CollectionStore store(future); CollectionState state;
    assert(store.load(state) == CollectionLoad::Future);
    assert(!store.migrate(state, capture(active)));
}
std::vector<uint8_t> fileBytes(const std::string& path) {
    auto* file = std::fopen(path.c_str(), "rb"); assert(file);
    std::vector<uint8_t> data; int c;
    while ((c = std::fgetc(file)) != EOF) data.push_back(c);
    assert(!std::ferror(file)); assert(std::fclose(file) == 0); return data;
}
void writeFile(const std::string& path, const std::vector<uint8_t>& bytes) {
    auto* file = std::fopen(path.c_str(), "wb"); assert(file);
    assert(std::fwrite(bytes.data(), 1, bytes.size(), file) == bytes.size());
    assert(std::fclose(file) == 0);
}
void filesystem() {
    char pattern[] = "/tmp/vpet-collection-XXXXXX";
    const auto* directory = mkdtemp(pattern); assert(directory);
    const std::string root = std::string(directory)+"/collection";
    LittleFsCollectionRepository repo(root.c_str()); CollectionStore store(repo); CollectionState state;
    struct stat info; assert(stat(root.c_str(), &info) != 0);  // Construction never mounts or migrates.
    auto active = pet(2); const auto first = capture(active);
    assert(store.migrate(state, first));
    const auto old = fileBytes(root+"/current.bin");
    active.restoreItems(3, 0, 1, 1, 2, 1);
    assert(store.saveActive(state, active, Settings()));
    const auto committed = fileBytes(root+"/current.bin");
    assert(fileBytes(root+"/previous.bin") == old);
    // An unusable backup path must leave both runtime and current intact.
    assert(std::remove((root+"/previous.bin").c_str()) == 0);
    assert(mkdir((root+"/previous.bin").c_str(), 0700) == 0);
    auto changed = active; changed.setHealth(81); const auto sequence = state.sequence;
    assert(!store.saveActive(state, changed, Settings()));
    assert(state.sequence == sequence && fileBytes(root+"/current.bin") == committed);
    assert(rmdir((root+"/previous.bin").c_str()) == 0);
    assert(store.load(state) == CollectionLoad::Loaded);  // Explicit recovery clears the IO block.
    assert(!repo.begin(state.sequence, CollectionStore::kMaxRecordBytes+1));
    assert(repo.begin(state.sequence, committed.size()));
    assert(repo.write(0, committed.data(), committed.size()));
    assert(!repo.commit(state.sequence+1));  // Wrong embedded sequence cannot publish.
    repo.abort(); assert(fileBytes(root+"/current.bin") == committed);
    // Orphan staging/half-written previous files never replace authoritative current.
    writeFile(root+"/pending.bin", {1, 2, 3});
    LittleFsCollectionRepository reboot(root.c_str()); CollectionStore restored(reboot); CollectionState loaded;
    assert(restored.load(loaded) == CollectionLoad::Loaded && loaded.stock[1] == 0);
    assert(restored.advance(loaded, 1, true));
    assert(restored.saveActive(loaded, active, Settings()));
    auto corrupt = fileBytes(root+"/current.bin"); corrupt.back() ^= 1;
    writeFile(root+"/current.bin", corrupt);
    LittleFsCollectionRepository damaged(root.c_str()); CollectionStore blocked(damaged);
    assert(blocked.load(loaded) == CollectionLoad::Corrupt);
    assert(!blocked.migrate(loaded, first) && fileBytes(root+"/current.bin") == corrupt);
    corrupt[4] = 2; writeFile(root+"/current.bin", corrupt);
    LittleFsCollectionRepository future(root.c_str()); CollectionStore futureStore(future);
    assert(futureStore.load(loaded) == CollectionLoad::Future);
    assert(std::remove((root+"/current.bin").c_str()) == 0);
    LittleFsCollectionRepository missing(root.c_str()); CollectionStore missingStore(missing);
    assert(missingStore.load(loaded) == CollectionLoad::Error);  // Previous needs explicit reconciliation.
    for (const auto name : {"previous.bin", "pending.bin"}) std::remove((root+"/"+name).c_str());
    assert(rmdir(root.c_str()) == 0); assert(rmdir(directory) == 0);
}
int main(int argc, char** argv) {
    assert(argc == 2); const std::string name = argv[1];
    if (name == "roundtrip") roundtrip();
    else if (name == "migration") migration();
    else if (name == "switch") switching();
    else if (name == "eggs") eggs();
    else if (name == "failures") failures();
    else if (name == "corruption") corruption();
    else if (name == "filesystem") filesystem();
    else return 2;
    std::cout << name << " passed\n";
}
