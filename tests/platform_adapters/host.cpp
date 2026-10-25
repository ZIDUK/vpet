#include "vpet/NvsKeyValueStore.h"
#include "vpet/BleService.h"
#include "vpet/StateSnapshot.h"
#include "Arduino.h"
#include "NimBLEDevice.h"
#include <atomic>
#include <cstdlib>
#include <iostream>
#include <thread>
#include <type_traits>

#define CHECK(condition) do { if (!(condition)) { \
    std::cerr << "line " << __LINE__ << ": " << #condition << '\n'; \
    std::exit(1); } } while (false)

using namespace vpet;

PetState makePet(int hunger) {
    PetState pet;
    pet.evolveTo(SpeciesId::Rookie);
    pet.rollDna(123);
    pet.setHunger(hunger);
    pet.adoptedStock.seed();
    return pet;
}

void checkSnapshotFields(const storage_stub::Namespace& actual,
                         const storage_stub::Namespace& expected) {
    for (const auto key : storage::kSnapshotKeys) CHECK(actual.at(key) == expected.at(key));
    for (const auto key : {"language", "adoptBag"}) CHECK(actual.at(key) == expected.at(key));
}

void checkPet(const PetState& actual, const PetState& expected) {
    CHECK(actual.species() == expected.species());
    CHECK(actual.hunger() == expected.hunger());
    CHECK(actual.energy() == expected.energy());
    CHECK(actual.practice.bond == expected.practice.bond);
    CHECK(actual.adoptedStock.encode() == expected.adoptedStock.encode());
    for (int i = 0; i < 4; ++i) CHECK(actual.dna()[i] == expected.dna()[i]);
}

void swapPending(const std::string& test) {
    using namespace storage_stub;
    const auto active = makePet(22);
    auto parked = makePet(88);
    parked.evolveTo(SpeciesId::Champion);
    parked.rollDna(987);
    parked.setHunger(88);
    parked.setEnergy(41);
    parked.practice.bond = 88;
    parked.adoptedStock.set(2, 7);
    const bool staging = test.find("stage") != std::string::npos;
    const bool mirror = test.find("backup") != std::string::npos;
    const bool resolves = test == "swap_backup_coordinator";
    const bool survives = test.find("durable") != std::string::npos || test == "swap_marker_reboot_new";
    {
        NvsKeyValueStore live("pet"), backup("parked");
        SettingsStore coordinator(live, &backup);
        Settings settings;
        CHECK(coordinator.save(active, settings));
        CHECK(SettingsStore(backup).save(parked, settings));
        const auto originalLive = durable["pet"], originalBackup = durable["parked"];
        persistFailedCommit = survives;
        failCommitNamespace = mirror ? "parked" : "pet";
        failCommitKey = mirror ? "hunger" : test.find("stage_live") != std::string::npos
            ? "swapLive" : staging ? "swapBack" : "swapTx";
        auto action = active;
        CHECK(coordinator.swapOrPark(action, settings) == !staging);
        checkPet(action, staging ? active : parked);
        if (staging) {
            CHECK(live.getString("swapTx", "").empty());
            CHECK(!live.sync());
        } else {
            CHECK(live.getString("swapTx", "") == "1");
            CHECK(mirror ? !backup.sync() : !live.sync());
        }
        checkSnapshotFields(visible["pet"], originalLive);
        checkSnapshotFields(durable["pet"], originalLive);
        if (!mirror) {
            checkSnapshotFields(visible["parked"], originalBackup);
            checkSnapshotFields(durable["parked"], originalBackup);
        } else {
            CHECK(backup.getInt("hunger", -1) == active.hunger());
            CHECK(std::get<int32_t>(durable["parked"].at("hunger")) == parked.hunger());
            CHECK(std::get<std::string>(durable["pet"].at("swapTx")) == "1");
        }
        // Restart the coordinator with the adapters retaining their pending handle.
        SettingsStore restarted(live, &backup);
        const int writes = sets;
        for (int retry = 0; retry < 3; ++retry) {
            CHECK(!restarted.recoverPending());
            auto blocked = makePet(66);
            CHECK(restarted.load(blocked, settings) == LoadResult::Unsupported);
            CHECK(blocked.hunger() == 66);
            CHECK(!restarted.save(active, settings));
            CHECK(sets == writes);
        }
        if (resolves) {
            failCommitKey.clear();
            CHECK(restarted.recoverPending());
            CHECK(live.getString("swapTx", "missing").empty());
            checkSnapshotFields(durable["pet"], visible["pet"]);
            checkSnapshotFields(durable["parked"], visible["parked"]);
        }
    }
    CHECK(handles.empty());
    reboot();
    NvsKeyValueStore live("pet"), backup("parked");
    SettingsStore coordinator(live, &backup);
    Settings settings;
    PetState restoredLive, restoredBackup;
    CHECK(coordinator.load(restoredLive, settings) == LoadResult::Loaded);
    CHECK(SettingsStore(backup).load(restoredBackup, settings) == LoadResult::Loaded);
    const bool swapped = mirror || (!staging && survives);
    checkPet(restoredLive, swapped ? parked : active);
    checkPet(restoredBackup, swapped ? active : parked);
    CHECK(live.getString("swapTx", "").empty());
    CHECK(coordinator.recoverPending());
    CHECK(coordinator.load(restoredLive, settings) == LoadResult::Loaded);
    CHECK(SettingsStore(backup).load(restoredBackup, settings) == LoadResult::Loaded);
    checkPet(restoredLive, swapped ? parked : active);
    checkPet(restoredBackup, swapped ? active : parked);
}

void settingsPending(const std::string& test) {
    using namespace storage_stub;
    auto old = makePet(20);
    auto next = old;
    next.setHunger(80);
    next.setEnergy(35);
    next.setWeight(12);
    const bool saveTest = test.find("_save_") != std::string::npos;
    const bool itemsTest = test.find("_items_") != std::string::npos;
    if (!itemsTest) next.noteMeal(false);
    if (saveTest || itemsTest) {
        next.practice.bond = 77;
        next.adoptedStock.set(0, 1);
    }
    const char* journal = saveTest ? "saveTx" : itemsTest ? "itemTx" : "foodTx";
    const bool rebootTest = test.find("reboot") != std::string::npos;
    const bool mirrorTest = test.find("mirror") != std::string::npos;
    const bool clearTest = test == "settings_clear_pending";
    {
        NvsKeyValueStore adapter("pet");
        SettingsStore persistence(adapter);
        Settings settings;
        CHECK(persistence.save(old, settings));
        const auto before = durable["pet"];
        persistFailedCommit = test == "settings_pending_reboot_new";
        failCommitKey = mirrorTest ? "hunger" : journal;
        if (clearTest) {
            // Clear an already committed journal, rather than rejecting its marker.
            CHECK(adapter.commitString("foodTx", "1,1,80,35,12,1,0,0,0,0,0,0") == StoreCommit::Pending);
            failCommitKey.clear();
            CHECK(adapter.sync());
            failCommitKey = "foodTx";
            CHECK(!persistence.recoverPending());
            CHECK(adapter.getString("foodTx", "missing").empty());
            CHECK(!std::get<std::string>(durable["pet"].at("foodTx")).empty());
        } else {
            auto action = next;
            // Model the caller's rollback contract using the actual SettingsStore:
            // accepted Pending must retain the action, never return rejection.
            const bool accepted = saveTest ? persistence.save(action, settings)
                : itemsTest ? persistence.commitConsumables(action) : persistence.commitFood(action);
            if (!accepted) action = old;
            CHECK(action.hunger() == next.hunger());
            CHECK(!adapter.sync());
            if (!mirrorTest) {
                CHECK(adapter.getInt("hunger", -1) == old.hunger());
                CHECK(adapter.getInt("energy", -1) == old.energy());
                CHECK(durable["pet"] == before || persistFailedCommit);
            } else {
                CHECK(adapter.getInt("hunger", -1) == next.hunger());
                CHECK(std::get<int32_t>(durable["pet"].at("hunger")) == old.hunger());
            }
        }
        const int writes = sets;
        for (int retry = 0; retry < 3; ++retry) {
            CHECK(!persistence.recoverPending());
            CHECK(!adapter.sync());
            auto blocked = makePet(66);
            CHECK(persistence.load(blocked, settings) == LoadResult::Unsupported);
            CHECK(blocked.hunger() == 66);
            CHECK(sets == writes);
        }
        CHECK(!adapter.putInt("overtake", 1));
        CHECK(!adapter.putString("overtake", "value"));
        CHECK(adapter.commitString("overtake", "value") == StoreCommit::Rejected);
        CHECK(sets == writes);
        if (!rebootTest) {
            failCommitKey.clear();
            CHECK(persistence.recoverPending());
            CHECK(adapter.getString(journal, "missing").empty());
        }
    }
    CHECK(handles.empty());
    reboot();
    NvsKeyValueStore restoredAdapter("pet");
    SettingsStore restoredStore(restoredAdapter);
    Settings settings;
    PetState restored;
    CHECK(restoredStore.load(restored, settings) == LoadResult::Loaded);
    const auto& expected = test.find("reboot_old") != std::string::npos ? old : next;
    CHECK(restored.hunger() == expected.hunger());
    CHECK(restored.energy() == expected.energy());
    CHECK(restored.weight() == expected.weight());
    CHECK(restored.meals() == expected.meals());
    CHECK(restored.adoptedStock.encode() == expected.adoptedStock.encode());
    CHECK(restored.practice.bond == expected.practice.bond);
    CHECK(restoredStore.load(restored, settings) == LoadResult::Loaded);
    CHECK(restored.meals() == expected.meals());
}

uint32_t profileSequence=100;
PetProfile newProfile() {
    const uint32_t words[]={profileSequence++,3,4,5};
    return PetProfile::fromWords(words);
}

void profilePending(const std::string& test) {
    using namespace storage_stub;
    Settings settings;
    std::string candidate;
    const bool rebootTest=test.find("reboot")!=std::string::npos;
    const bool mirror=test.find("mirror")!=std::string::npos;
    const bool survives=test.find("new")!=std::string::npos || mirror;
    {
        NvsKeyValueStore adapter("pet");
        auto pet=makePet(31);
        CHECK(SettingsStore(adapter).save(pet,settings));
        const auto dna=pet.dna()[0];
        SettingsStore migration(adapter,nullptr,newProfile);
        failCommitKey=mirror?"petProfile":"saveTx";
        persistFailedCommit=survives;
        CHECK(migration.load(pet,settings)==LoadResult::Unsupported);
        CHECK(pet.profile.assigned());
        candidate=pet.profile.encode();
        const auto calls=profileSequence;
        for(int retry=0;retry<3;++retry) {
            CHECK(migration.load(pet,settings)==LoadResult::Unsupported);
            CHECK(profileSequence==calls && pet.dna()[0]==dna && pet.hunger()==31);
        }
        if(!rebootTest) {
            failCommitKey.clear();
            CHECK(migration.load(pet,settings)==LoadResult::Loaded);
            CHECK(pet.profile.encode()==candidate);
        }
    }
    CHECK(handles.empty());
    reboot();
    NvsKeyValueStore adapter("pet");
    PetState pet;
    CHECK(SettingsStore(adapter,nullptr,newProfile).load(pet,settings)==LoadResult::Loaded);
    CHECK(pet.profile.assigned() && pet.hunger()==31);
    CHECK((pet.profile.encode()==candidate)==(!rebootTest || survives));
}

int main(int argc, char** argv) {
    CHECK(argc == 2);
    const std::string test = argv[1];
    using namespace vpet;
    if(test.compare(0,8,"profile_")==0) { profilePending(test); return 0; }
    if (test.compare(0, 5, "swap_") == 0) {
        swapPending(test);
        return 0;
    }
    if (test.compare(0, 9, "settings_") == 0) {
        settingsPending(test);
        return 0;
    }
    if (test.compare(0, 4, "nvs_") == 0) {
        NvsKeyValueStore store("pet");
        if (test == "nvs_nonempty") {
            CHECK(store.putString("journal", "pending"));
            CHECK(store.getString("journal", "missing") == "pending");
        } else if (test == "nvs_empty") {
            CHECK(store.putString("journal", "pending"));
            CHECK(store.putString("journal", ""));
            CHECK(store.getString("journal", "missing").empty());
            CHECK(store.putString("journal", ""));
            CHECK(store.putString("new_empty", ""));
            CHECK(store.getString("new_empty", "missing").empty());
        } else if (test == "nvs_failures") {
            CHECK(store.putString("journal", "pending"));
            storage_stub::failSet = true;
            CHECK(!store.putString("journal", ""));
            CHECK(!store.putString("journal", "new"));
            storage_stub::failSet = false;
            CHECK(store.putString("journal", ""));
            storage_stub::failCommit = true;
            // Even an already-empty readback cannot prove this commit succeeded.
            CHECK(!store.putString("journal", ""));
            CHECK(!store.putString("journal", "new"));
            storage_stub::failCommit = false;
            CHECK(store.sync());
            CHECK(!store.putString(nullptr, ""));
            CHECK(!store.putString("journal", nullptr));
            CHECK(!store.putString("", ""));
            CHECK(storage_stub::handles.size() == 1);
        } else if (test == "nvs_namespace") {
            NvsKeyValueStore other("other");
            CHECK(other.putString("journal", "other"));
            CHECK(store.putString("journal", ""));
            CHECK(other.getString("journal", "") == "other");
            storage_stub::failOpen = true;
            NvsKeyValueStore unavailable("unavailable");
            CHECK(!unavailable.putString("journal", ""));
            CHECK(!unavailable.putString("journal", "value"));
            CHECK(!store.putString("journal", ""));
        } else if (test == "nvs_pending" || test == "nvs_pending_empty" || test == "nvs_pending_int") {
            CHECK(store.putString("journal", "old"));
            CHECK(store.putInt("mirror", 10));
            const auto durableBefore = storage_stub::durable["pet"];
            const auto handlesBefore = storage_stub::handles.size();
            storage_stub::failCommit = true;
            if (test == "nvs_pending_int") {
                CHECK(!store.putInt("mirror", 20));
                CHECK(store.getInt("mirror", -1) == 20);
            } else {
                const char* value = test == "nvs_pending_empty" ? "" : "new";
                CHECK(store.commitString("journal", value) == StoreCommit::Pending);
                CHECK(store.getString("journal", "missing") == value);
            }
            CHECK(storage_stub::durable["pet"] == durableBefore);
            CHECK(storage_stub::handles.size() == handlesBefore + 1);
            const auto pendingHandle = storage_stub::lastSetHandle;
            const int sets = storage_stub::sets;
            for (int i = 0; i < 3; ++i) {
                CHECK(!store.sync());
                CHECK(storage_stub::lastCommitHandle == pendingHandle);
                CHECK(storage_stub::handles.count(pendingHandle) == 1);
                CHECK(!store.putInt("blocked", 1));
                CHECK(!store.putString("blocked", "value"));
                CHECK(store.commitString("blocked", "value") == StoreCommit::Rejected);
                CHECK(storage_stub::sets == sets);
            }
            storage_stub::failCommit = false;
            // Writes remain blocked until an explicit sync, even after faults clear.
            CHECK(!store.putInt("blocked", 1));
            CHECK(store.sync());
            CHECK(storage_stub::lastCommitHandle == pendingHandle);
            CHECK(storage_stub::handles.count(pendingHandle) == 0);
            CHECK(storage_stub::durable["pet"] == storage_stub::visible["pet"]);
            CHECK(store.sync());
            CHECK(store.putInt("unblocked", 1));
        } else if (test == "nvs_rejected") {
            CHECK(store.commitString("journal", "old") == StoreCommit::Committed);
            storage_stub::failSet = true;
            CHECK(store.commitString("journal", "new") == StoreCommit::Rejected);
            CHECK(!store.putInt("mirror", 1));
            CHECK(store.sync());
            storage_stub::failSet = false;
            CHECK(store.commitString(nullptr, "new") == StoreCommit::Rejected);
            CHECK(store.commitString("journal", nullptr) == StoreCommit::Rejected);
            CHECK(store.commitString("", "new") == StoreCommit::Rejected);
            CHECK(store.commitString("journal", "new") == StoreCommit::Committed);
        } else if (test == "nvs_handle_ownership") {
            CHECK(!std::is_copy_constructible<NvsKeyValueStore>::value);
            CHECK(!std::is_copy_assignable<NvsKeyValueStore>::value);
        } else CHECK(false);
        return 0;
    }

    BleService ble;
    ble.begin();
    CHECK(ble.status() == BleStatus::Off);
    if (test == "ble_failures") {
        for (bool* failure : {&ble_stub::failInit, &ble_stub::failServer,
                              &ble_stub::failService, &ble_stub::failAdvertising,
                              &ble_stub::failStart}) {
            *failure = true;
            CHECK(!ble.setEnabled(true));
            CHECK(ble.status() == BleStatus::Error);
            *failure = false;
            CHECK(ble.setEnabled(false));
            CHECK(ble.setEnabled(true));
            CHECK(ble.setEnabled(false));
        }
        return 0;
    }
    if (test == "ble_start_callback") {
        ble_stub::duringStart = [] { NimBLEDevice::server->connect(); };
    }
    CHECK(ble.setEnabled(true));
    auto* server = NimBLEDevice::server;
    CHECK(!server->owns && server->restart);
    if (test == "ble_lifecycle") {
        CHECK(ble.status() == BleStatus::Advertising);
        CHECK(ble.setEnabled(true));
        CHECK(ble_stub::starts == 1 && ble_stub::clears == 1);
        server->connect();
        CHECK(ble.status() == BleStatus::Connected);
        CHECK(ble_stub::security == 1);
        server->disconnect();
        CHECK(ble.status() == BleStatus::Advertising);
        CHECK(ble_stub::starts == 2 && ble_stub::active);
    } else if (test == "ble_stop_callbacks") {
        ble_stub::duringStop = [&] {
            server->connect();
            CHECK(ble.status() == BleStatus::Off);
            CHECK(ble_stub::security == 0);
            server->disconnect();
            CHECK(ble.status() == BleStatus::Off);
        };
    } else if (test == "ble_start_callback") {
        CHECK(ble.status() == BleStatus::Connected);
    } else if (test == "ble_name") {
        const char* name = ble.deviceName();
        ESP.mac = 0x1234;
        ble.begin();
        CHECK(std::string(name) == "vPet-F908");
        CHECK(ble.deviceName() == name);
        NimBLEConnInfo info;
        server->callbacks->onAuthenticationComplete(info);
    } else if (test == "ble_deinit_failure") {
        ble_stub::failDeinit = true;
        CHECK(!ble.setEnabled(false));
        CHECK(ble.status() == BleStatus::Error);
        CHECK(NimBLEDevice::server == server);
        server->connect();
        server->disconnect();
        CHECK(ble.status() == BleStatus::Error);
        ble_stub::failDeinit = false;
    } else if (test == "ble_stress") {
        for (int cycle = 0; cycle < 30; ++cycle) {
            std::atomic<bool> running{true};
            std::atomic<bool> started{false};
            server = NimBLEDevice::server;
            std::thread callback([&] {
                server->connect();
                server->disconnect();
                started = true;
                while (running.load()) { server->connect(); server->disconnect(); }
            });
            while (!started.load()) std::this_thread::yield();
            ble_stub::quiesce = [&] { running = false; callback.join(); };
            for (int i = 0; i < 1000; ++i) (void)ble.status();
            CHECK(ble.setEnabled(false));
            ble_stub::quiesce = {};
            CHECK(ble.status() == BleStatus::Off);
            CHECK(ble.setEnabled(true));
        }
    } else CHECK(false);
    CHECK(ble.setEnabled(false));
    CHECK(ble.status() == BleStatus::Off);
    CHECK(!ble_stub::active && !NimBLEDevice::server);
    CHECK(ble_stub::callbackDeletes == 0);
    ble_stub::duringStop = {};
    CHECK(ble.setEnabled(false));
    CHECK(ble.setEnabled(true));
    CHECK(ble.setEnabled(false));
}
