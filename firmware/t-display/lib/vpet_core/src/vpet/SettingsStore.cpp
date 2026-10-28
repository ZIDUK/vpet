#include "vpet/SettingsStore.h"
#include "vpet/Nutrition.h"
#include "vpet/StateSnapshot.h"

#include <cstdio>
#include <sstream>

namespace vpet {
namespace {
const char* kItemTxKeys[] = {"hunger","energy","happy","effort","health","weight",
    "injured","training","nutTrainRem","evHp","evMp","evOff","evDef","evSpd","evBrn",
    "techTrain","techBond","techM0","techM1","techM2","techEquip",
    "nutVer","nutHunRem","nutProtein","legacyWeight"};
constexpr size_t kItemTxCount=sizeof(kItemTxKeys)/sizeof(kItemTxKeys[0]);
uint8_t safeWeight(int value) {
    if (value < 1) return 1;
    if (value > 99) return 99;
    return static_cast<uint8_t>(value);
}
}

LoadResult SettingsStore::load(PetState& pet, Settings& settings) {
    if (!recoverAll()) return LoadResult::Unsupported;
    PetProfile profile;
    if (!profile.decode(store_.getString("petProfile", ""))) return LoadResult::Unsupported;
    if (!pet.exploration.decode(store_.getString("expState", ""))) return LoadResult::Unsupported;
    if (!pet.sleep.decode(store_.getString("sleepState", ""))) return LoadResult::Unsupported;
    if (!pet.adoptedStock.decode(store_.getString("adoptBag", ""))) return LoadResult::Unsupported;
    const int version = store_.getInt("schema", 0);
    if (version == 0) {
        pet.evolveTo(pet.species());
        return LoadResult::Missing;
    }
    if (version != 1 && version != 2 && version != 3) return LoadResult::Unsupported;
    pet.profile = profile;
    pet.restore(
        static_cast<SpeciesId>(store_.getInt("species", 0)),
        store_.getInt("hunger", 80),
        store_.getInt("energy", 80),
        store_.getInt("happy", 80),
        store_.getInt("effort", 0),
        store_.getInt("health", 100),
        store_.getInt("age", 0)
    );
    pet.restoreItems(
        static_cast<uint8_t>(store_.getInt("invMeat", 3)),
        static_cast<uint8_t>(store_.getInt("invEner", 2)),
        static_cast<uint8_t>(store_.getInt("invExp", 1)),
        static_cast<uint8_t>(store_.getInt("invRing", 1)),
        static_cast<uint8_t>(store_.getInt("invProt", 2)),
        static_cast<uint8_t>(store_.getInt("invMed", 1))
    );
    if (version == 2 || version == 3) {
        pet.restoreCare(
            static_cast<uint32_t>(store_.getInt("stageAge", 0)),
            static_cast<uint8_t>(store_.getInt("cm", 0)),
            static_cast<CallReason>(store_.getInt("call", 0)),
            store_.getInt("meals", 0),
            store_.getInt("training", 0),
            store_.getInt("battles", 0),
            static_cast<uint8_t>(store_.getInt("wins", 0)),
            static_cast<uint8_t>(store_.getInt("losses", 0)),
            safeWeight(store_.getInt("weight", 5)),
            static_cast<uint8_t>(store_.getInt("dp", 0)),
            static_cast<uint8_t>(store_.getInt("protein", 0))
        );
        pet.restoreOverfeed(
            store_.getInt("overfed", 0) != 0,
            static_cast<uint8_t>(store_.getInt("overfeeds", 0))
        );
        pet.restoreInjury(
            store_.getInt("injured", 0) != 0,
            static_cast<uint8_t>(store_.getInt("injuries", 0)),
            store_.getInt("dead", 0) != 0,
            static_cast<uint32_t>(store_.getInt("injuredMs", 0) < 0 ? 0 : store_.getInt("injuredMs", 0))
        );
        pet.restoreSurvival(
            static_cast<uint32_t>(store_.getInt("hunCritMs", 0) < 0 ? 0 : store_.getInt("hunCritMs", 0)),
            static_cast<uint32_t>(store_.getInt("eneCritMs", 0) < 0 ? 0 : store_.getInt("eneCritMs", 0))
        );
        if (store_.getInt("nutVer", 0) >= 1) {
            const int hungerRemainder = store_.getInt("nutHunRem", 0);
            const int trainingRemainder = store_.getInt("nutTrainRem", 0);
            pet.setNutritionState(
                static_cast<uint8_t>(hungerRemainder < 0 ? 0 : (hungerRemainder > 19 ? 19 : hungerRemainder)),
                static_cast<uint8_t>(trainingRemainder < 0 ? 0 : (trainingRemainder > 3 ? 3 : trainingRemainder)),
                store_.getInt("nutProtein", 0) != 0
            );
        } else {
            pet.setWeight(migrateLegacyWeight(pet.species(), safeWeight(store_.getInt("weight", 5))));
        }
    } else {
        pet.restoreCare(0, 0, CallReason::None, 0, 0, 0, 0, 0, 5, 1, 0);
    }
    pet.setCold(store_.getInt("cold", 0) != 0);
    if (version == 3) {
        const uint8_t dna[] = {
            static_cast<uint8_t>(store_.getInt("dna0", 0)),
            static_cast<uint8_t>(store_.getInt("dna1", 0)),
            static_cast<uint8_t>(store_.getInt("dna2", 0)),
            static_cast<uint8_t>(store_.getInt("dna3", 0)),
        };
        const uint8_t ev[] = {
            static_cast<uint8_t>(store_.getInt("evHp", 0)),
            static_cast<uint8_t>(store_.getInt("evMp", 0)),
            static_cast<uint8_t>(store_.getInt("evOff", 0)),
            static_cast<uint8_t>(store_.getInt("evDef", 0)),
            static_cast<uint8_t>(store_.getInt("evSpd", 0)),
            static_cast<uint8_t>(store_.getInt("evBrn", 0)),
        };
        pet.restoreDna(dna);
        const int locus = store_.getInt("dna4", pet.profile.assigned() ?
            (pet.profile.sex() == Sex::Male ? 1 : 2) : 0);
        if (locus == 1 || locus == 2) {
            pet.setSexLocus(locus == 1 ? Sex::Male : Sex::Female);
            pet.profile.setSex(locus == 1 ? Sex::Male : Sex::Female);
        }
        pet.restoreEv(ev);
    }
    migratedDna_ = false;
    if (pet.species() != SpeciesId::Egg && !pet.hasDna()) {
        pet.rollDna(
            pet.ageSeconds() * 2654435761U +
            static_cast<uint32_t>(pet.species()) +
            static_cast<uint32_t>(pet.wins()) * 17U
        );
        migratedDna_ = true;
    }
    loadPractice(pet.practice,pet.techniqueStage());
    settings.language = store_.getString("language", "ES");
    settings.soundEnabled = store_.getInt("sound", 1) != 0;
    settings.bluetoothEnabled = store_.getInt("bluetooth", 0) != 0;
    if (profiles_ && !pet.profile.assigned() && !needsLifeRestart() &&
        (!save(pet,settings) || !recoverAll()))
        return LoadResult::Unsupported;
    return LoadResult::Loaded;
}

bool SettingsStore::restartLifeIfNeeded(PetState& pet, Settings& settings) {
    if (store_.getInt("life", 0) != 0) return false;
    const PetState before = pet;
    pet.resetToEgg();
    if (!save(pet, settings)) { pet = before; return false; }
    return true;
}

bool SettingsStore::save(PetState& pet, const Settings& settings) {
    if (!recoverAll()) return false;
    PetState candidate=pet;
    if (profiles_ && !candidate.profile.assigned()) {
        candidate.profile=profiles_();
        if (!candidate.profile.assigned()) return false;
    }
    if (candidate.sexLocus() == Sex::Unknown && candidate.profile.assigned())
        candidate.setSexLocus(candidate.profile.sex());
    storage::SnapshotStore captured(&store_);
    SettingsStore writer(captured);
    if (!writer.writeSnapshot(candidate, settings)) return false;
    const auto record = storage::encodeSnapshot(captured);
    storage::SnapshotStore validated;
    if (!storage::decodeSnapshot(record, validated)) return false;
    // A single atomic NVS string write commits the complete desired state.
    if (store_.commitString("saveTx", record.c_str()) == StoreCommit::Rejected) return false;
    pet.profile=candidate.profile;
    recoverSnapshotTransaction();
    return true;
}

bool SettingsStore::recoverAll() {
    return store_.sync() && recoverSwapTransaction() && recoverSnapshotTransaction() &&
        recoverFoodTransaction() && recoverConsumableTransaction();
}

bool SettingsStore::recoverSnapshotTransaction() {
    if (!store_.sync()) return false;
    const auto record = store_.getString("saveTx", "");
    if (record.empty()) return true;
    storage::SnapshotStore snapshot;
    if (!storage::decodeSnapshot(record, snapshot) || !storage::replaySnapshot(store_, snapshot)) return false;
    return store_.putString("saveTx", "");
}

bool SettingsStore::recoverSwapTransaction() {
    if (!store_.sync()) return false;
    const auto marker = store_.getString("swapTx", "");
    if (marker.empty()) return true;
    if (marker != "1" || backup_ == nullptr || !backup_->sync()) return false;
    storage::SnapshotStore active, parked;
    if (!storage::decodeSnapshot(store_.getString("swapLive", ""), active) ||
        !storage::decodeSnapshot(store_.getString("swapBack", ""), parked)) return false;
    if (!storage::replaySnapshot(*backup_, parked) || !storage::replaySnapshot(store_, active)) return false;
    return store_.putString("swapTx", "");
}

bool SettingsStore::writeSnapshot(const PetState& pet, const Settings& settings) {
    bool ok = true;
    ok = store_.putInt("legacyWeight", safeWeight(store_.getInt("legacyWeight", store_.getInt("weight", 5)))) && ok;
    ok = store_.putInt("schema", 3) && ok;
    ok = store_.putInt("nutVer", 1) && ok;
    ok = store_.putInt("species", static_cast<int>(pet.species())) && ok;
    ok = store_.putInt("hunger", pet.hunger()) && ok;
    ok = store_.putInt("energy", pet.energy()) && ok;
    ok = store_.putInt("happy", pet.happiness()) && ok;
    ok = store_.putInt("effort", pet.effort()) && ok;
    ok = store_.putInt("health", pet.health()) && ok;
    ok = store_.putInt("age", pet.ageSeconds()) && ok;
    ok = store_.putInt("invMeat", pet.itemCount(0)) && ok;
    ok = store_.putInt("invEner", pet.itemCount(1)) && ok;
    ok = store_.putInt("invExp", pet.itemCount(2)) && ok;
    ok = store_.putInt("invRing", pet.itemCount(3)) && ok;
    ok = store_.putInt("invProt", pet.itemCount(4)) && ok;
    ok = store_.putInt("invMed", pet.itemCount(5)) && ok;
    ok = store_.putInt("stageAge", static_cast<int>(pet.stageAgeSeconds())) && ok;
    ok = store_.putInt("cm", pet.careMistakes()) && ok;
    ok = store_.putInt("call", static_cast<int>(pet.callReason())) && ok;
    ok = store_.putInt("meals", pet.meals()) && ok;
    ok = store_.putInt("training", pet.trainingSessions()) && ok;
    ok = store_.putInt("battles", pet.battles()) && ok;
    ok = store_.putInt("wins", pet.wins()) && ok;
    ok = store_.putInt("losses", pet.losses()) && ok;
    ok = store_.putInt("weight", pet.weight()) && ok;
    ok = store_.putInt("nutHunRem", pet.hungerCycleRemainder()) && ok;
    ok = store_.putInt("nutTrainRem", pet.trainingWeightRemainder()) && ok;
    ok = store_.putInt("nutProtein", pet.proteinFedThisCycle() ? 1 : 0) && ok;
    ok = store_.putInt("dp", pet.dp()) && ok;
    ok = store_.putInt("protein", pet.protein()) && ok;
    ok = store_.putInt("overfed", pet.overfedThisCycle() ? 1 : 0) && ok;
    ok = store_.putInt("overfeeds", pet.overfeeds()) && ok;
    ok = store_.putInt("injured", pet.injured() ? 1 : 0) && ok;
    ok = store_.putInt("injuries", pet.injuries()) && ok;
    ok = store_.putInt("injuredMs", pet.injuredMs()) && ok;
    ok = store_.putInt("dead", pet.dead() ? 1 : 0) && ok;
    ok = store_.putInt("hunCritMs", pet.hungerCriticalMs()) && ok;
    ok = store_.putInt("eneCritMs", pet.energyCriticalMs()) && ok;
    ok = store_.putInt("cold", pet.cold() ? 1 : 0) && ok;
    ok = store_.putInt("dna0", pet.dna()[0]) && ok;
    ok = store_.putInt("dna1", pet.dna()[1]) && ok;
    ok = store_.putInt("dna2", pet.dna()[2]) && ok;
    ok = store_.putInt("dna3", pet.dna()[3]) && ok;
    ok = store_.putInt("dna4", pet.dna()[4]) && ok;
    ok = store_.putInt("evHp", pet.evAt(CombatStat::Hp)) && ok;
    ok = store_.putInt("evMp", pet.evAt(CombatStat::Mp)) && ok;
    ok = store_.putInt("evOff", pet.evAt(CombatStat::Off)) && ok;
    ok = store_.putInt("evDef", pet.evAt(CombatStat::Def)) && ok;
    ok = store_.putInt("evSpd", pet.evAt(CombatStat::Spd)) && ok;
    ok = store_.putInt("evBrn", pet.evAt(CombatStat::Brn)) && ok;
    ok = store_.putInt("life", 1) && ok;
    ok = store_.putString("language", settings.language.c_str()) && ok;
    ok = store_.putInt("sound", settings.soundEnabled ? 1 : 0) && ok;
    ok = store_.putInt("bluetooth", settings.bluetoothEnabled ? 1 : 0) && ok;
    ok = savePractice(pet.practice,pet.techniqueStage()) && ok;
    if (ok) ok = store_.putString("adoptBag", pet.adoptedStock.encode().c_str());
    if (ok) ok = store_.putString("expState", pet.exploration.encode().c_str());
    if (ok) ok = store_.putString("sleepState", pet.sleep.encode().c_str());
    if (ok) ok = store_.putString("petProfile", pet.profile.encode().c_str());
    return ok;
}

bool SettingsStore::commitConsumables(const PetState& pet) {
    if (!recoverAll()) return false;
    // The single string write is the commit point. Replay is idempotent.
    std::ostringstream out;
    out << pet.adoptedStock.encode() << '\n';
    const int values[] = {pet.hunger(),pet.energy(),pet.happiness(),pet.effort(),pet.health(),pet.weight(),
        pet.injured()?1:0,pet.trainingSessions(),pet.trainingWeightRemainder(),
        pet.evAt(CombatStat::Hp),pet.evAt(CombatStat::Mp),pet.evAt(CombatStat::Off),
        pet.evAt(CombatStat::Def),pet.evAt(CombatStat::Spd),pet.evAt(CombatStat::Brn),
        pet.practice.training,pet.practice.bond,pet.practice.mastery[0],pet.practice.mastery[1],
        pet.practice.mastery[2],pet.practice.equipped,1,pet.hungerCycleRemainder(),
        pet.proteinFedThisCycle()?1:0,
        safeWeight(store_.getInt("legacyWeight",store_.getInt("weight",5)))};
    for (size_t i=0; i<kItemTxCount; ++i) out << kItemTxKeys[i] << ' ' << values[i] << '\n';
    if (store_.commitString("itemTx",out.str().c_str()) == StoreCommit::Rejected) return false;
    recoverConsumableTransaction();
    return true;
}

bool SettingsStore::recoverConsumableTransaction() {
    if (!store_.sync()) return false;
    const auto journal=store_.getString("itemTx", "");
    if (journal.empty()) return true;
    std::istringstream in(journal);
    std::string bag;
    std::getline(in,bag);
    AdoptedInventory stock;
    if (bag.empty() || !stock.decode(bag)) return false;
    int32_t values[kItemTxCount];
    std::string key;
    const int maxima[] = {100,100,100,100,100,99,1,2147483647,3,252,252,252,252,252,252,255,100,100,100,100,31,
        1,19,1,99};
    for (size_t i=0; i<kItemTxCount; ++i) {
        if (!(in>>key>>values[i]) || key!=kItemTxKeys[i] || values[i]<0 || values[i]>maxima[i]) return false;
    }
    if (values[5]<1 || values[21]!=1 || values[24]<1 || in>>key) return false;
    bool ok=true;
    for (size_t i=0;i<kItemTxCount;++i) ok=store_.putInt(kItemTxKeys[i],values[i]) && ok;
    ok=store_.putString("adoptBag",bag.c_str()) && ok;
    if (!ok) return false;
    return store_.putString("itemTx", "");
}

bool SettingsStore::commitFood(const PetState& pet) {
    if (!recoverAll()) return false;
    char journal[80];
    const int previousSequence = store_.getInt("foodSeq", 0);
    const int sequence = previousSequence < 1 || previousSequence >= 2147483647
        ? 1 : previousSequence + 1;
    snprintf(journal, sizeof(journal), "1,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
             sequence, pet.hunger(), pet.energy(), pet.weight(), pet.meals(),
             static_cast<int>(pet.callReason()), pet.overfedThisCycle() ? 1 : 0,
             pet.overfeeds(), pet.hungerCycleRemainder(),
             pet.trainingWeightRemainder(), pet.proteinFedThisCycle() ? 1 : 0);
    if (store_.commitString("foodTx", journal) == StoreCommit::Rejected) return false;
    recoverFoodTransaction();
    return true;
}

bool SettingsStore::recoverFoodTransaction() {
    if (!store_.sync()) return false;
    const std::string journal = store_.getString("foodTx", "");
    if (journal.empty()) return true;
    int version = 0, sequence = 0, hunger = 0, energy = 0, weight = 0, meals = 0;
    int call = 0, overfed = 0, overfeeds = 0, hungerRem = 0, trainRem = 0, protein = 0;
    int consumed = 0;
    const int fields = sscanf(journal.c_str(), "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d%n",
                              &version, &sequence, &hunger, &energy, &weight, &meals, &call,
                              &overfed, &overfeeds, &hungerRem, &trainRem, &protein, &consumed);
    if (fields != 12 || journal[consumed] != '\0' || version != 1 || sequence < 1 ||
        hunger < 0 || hunger > 100 ||
        energy < 0 || energy > 100 || weight < 1 || weight > 99 || meals < 0 || meals > 255 ||
        call < 0 || call > 3 || (overfed != 0 && overfed != 1) || overfeeds < 0 || overfeeds > 99 ||
        hungerRem < 0 || hungerRem > 19 || trainRem < 0 || trainRem > 3 ||
        (protein != 0 && protein != 1)) return false;

    bool ok = true;
    ok = store_.putInt("foodSeq", sequence) && ok;
    ok = store_.putInt("hunger", hunger) && ok;
    ok = store_.putInt("energy", energy) && ok;
    ok = store_.putInt("weight", weight) && ok;
    ok = store_.putInt("meals", meals) && ok;
    ok = store_.putInt("call", call) && ok;
    ok = store_.putInt("overfed", overfed) && ok;
    ok = store_.putInt("overfeeds", overfeeds) && ok;
    ok = store_.putInt("nutHunRem", hungerRem) && ok;
    ok = store_.putInt("nutTrainRem", trainRem) && ok;
    ok = store_.putInt("nutProtein", protein) && ok;
    if (!ok) return false;
    return store_.putString("foodTx", "");
}

bool SettingsStore::loadPractice(PracticeProgress& progress, int stage) const {
    progress = PracticeProgress();
    if (store_.getInt("techVer", 1) != 1) return false;
    const auto byte = [this](const char* key, int fallback, int maximum) {
        const int value = store_.getInt(key, fallback);
        return static_cast<uint8_t>(value < 0 ? 0 : (value > maximum ? maximum : value));
    };
    progress.version = static_cast<uint8_t>(store_.getInt("techVer", 1));
    progress.training = byte("techTrain", 0, 255);
    progress.bond = byte("techBond", 50, 100);
    progress.mastery[0] = byte("techM0", 0, 100);
    progress.mastery[1] = byte("techM1", 0, 100);
    progress.mastery[2] = byte("techM2", 0, 100);
    progress.mastery[3] = byte("techM3", 0, 100);
    progress.mastery[4] = byte("techM4", 0, 100);
    progress.equipped = byte("techEquip", 0b101, 31);
    progress.sanitize(stage);
    return progress.version == 1;
}

bool SettingsStore::savePractice(const PracticeProgress& input, int stage) {
    PracticeProgress progress = input;
    progress.sanitize(stage);
    bool ok = store_.putInt("techVer", progress.version);
    ok = store_.putInt("techTrain", progress.training) && ok;
    ok = store_.putInt("techBond", progress.bond) && ok;
    ok = store_.putInt("techM0", progress.mastery[0]) && ok;
    ok = store_.putInt("techM1", progress.mastery[1]) && ok;
    ok = store_.putInt("techM2", progress.mastery[2]) && ok;
    ok = store_.putInt("techM3", progress.mastery[3]) && ok;
    ok = store_.putInt("techM4", progress.mastery[4]) && ok;
    ok = store_.putInt("techEquip", progress.equipped) && ok;
    return ok;
}

bool SettingsStore::hasBackup() const {
    return backup_ != nullptr && backup_->getInt("schema", 0) != 0;
}

bool SettingsStore::exportLegacySnapshots(std::string& active, std::string& backup, bool& backupPresent) {
    if (!recoverAll()) return false;
    if (backup_ && !SettingsStore(*backup_).recoverPending()) return false;
    const auto capture = [](KeyValueStore& source, std::string& result) {
        storage::SnapshotStore snapshot;
        for (const auto key : storage::kSnapshotKeys)
            snapshot.ints[key] = source.getInt(key, -1);
        for (const auto key : {"techM3", "techM4"}) snapshot.ints[key] = source.getInt(key, 0);
        for (const auto key : {"language", "adoptBag", "expState", "sleepState", "petProfile"})
            snapshot.strings[key] = source.getString(key, "");
        PetProfile profile;
        if (!profile.decode(snapshot.strings["petProfile"])) return false;
        const int fallbackLocus = profile.sex() == Sex::Male ? 1 :
            profile.sex() == Sex::Female ? 2 : 0;
        snapshot.ints["dna4"] = source.getInt("dna4", fallbackLocus);
        const auto encoded = storage::encodeSnapshot(snapshot);
        storage::SnapshotStore checked;
        if (encoded.empty() || !storage::decodeSnapshot(encoded, checked)) return false;
        result = encoded;
        return true;
    };
    std::string nextActive, nextBackup;
    const bool present = backup_ && backup_->getInt("schema", 0) != 0;
    if (!capture(store_, nextActive) || (present && !capture(*backup_, nextBackup))) return false;
    active = std::move(nextActive); backup = std::move(nextBackup); backupPresent = present;
    return true;
}

SpeciesId SettingsStore::backupSpecies() const {
    if (!hasBackup()) return SpeciesId::Egg;
    return static_cast<SpeciesId>(backup_->getInt("species", static_cast<int>(SpeciesId::Egg)));
}

bool SettingsStore::swapOrPark(PetState& pet, Settings& settings) {
    if (profiles_ && !pet.profile.assigned()) return false;
    if (backup_ == nullptr || !recoverAll()) return false;
    SettingsStore parkedStore(*backup_,nullptr,profiles_);
    PetState target;
    Settings ignored;
    const auto result = parkedStore.load(target, ignored);
    if (result == LoadResult::Unsupported) return false;
    if (result == LoadResult::Missing) { target = pet; target.resetToEgg(); }
    if (profiles_ && !target.profile.assigned()) {
        target.profile=profiles_();
        if (!target.profile.assigned()) return false;
    }
    storage::SnapshotStore active(&store_), parked(backup_);
    SettingsStore activeWriter(active), parkedWriter(parked);
    if (!activeWriter.writeSnapshot(target, settings) || !parkedWriter.writeSnapshot(pet, settings)) return false;
    const auto activeRecord = storage::encodeSnapshot(active), parkedRecord = storage::encodeSnapshot(parked);
    storage::SnapshotStore validated;
    if (!storage::decodeSnapshot(activeRecord, validated) || !storage::decodeSnapshot(parkedRecord, validated)) return false;
    // Staging writes do not change either pet. Only the final marker commits.
    if (!store_.putString("swapLive", activeRecord.c_str()) ||
        !store_.putString("swapBack", parkedRecord.c_str()) ||
        store_.commitString("swapTx", "1") == StoreCommit::Rejected) return false;
    pet = target;
    recoverSwapTransaction();
    return true;
}

}  // namespace vpet
