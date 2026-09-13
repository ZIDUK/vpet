#include "vpet/SettingsStore.h"

namespace vpet {

LoadResult SettingsStore::load(PetState& pet, Settings& settings) {
    const int version = store_.getInt("schema", 0);
    if (version == 0) {
        pet.evolveTo(pet.species());
        return LoadResult::Missing;
    }
    if (version != 1 && version != 2 && version != 3) return LoadResult::Unsupported;
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
            static_cast<uint8_t>(store_.getInt("weight", 5)),
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
            store_.getInt("dead", 0) != 0
        );
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
    settings.language = store_.getString("language", "ES");
    settings.soundEnabled = store_.getInt("sound", 1) != 0;
    settings.bluetoothEnabled = store_.getInt("bluetooth", 0) != 0;
    return LoadResult::Loaded;
}

bool SettingsStore::restartLifeIfNeeded(PetState& pet, Settings& settings) {
    if (store_.getInt("life", 0) != 0) return false;
    pet.resetToEgg();
    store_.putInt("life", 1);
    save(pet, settings);
    return true;
}

bool SettingsStore::save(const PetState& pet, const Settings& settings) {
    bool ok = store_.putInt("schema", 3);
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
    ok = store_.putInt("dp", pet.dp()) && ok;
    ok = store_.putInt("protein", pet.protein()) && ok;
    ok = store_.putInt("overfed", pet.overfedThisCycle() ? 1 : 0) && ok;
    ok = store_.putInt("overfeeds", pet.overfeeds()) && ok;
    ok = store_.putInt("injured", pet.injured() ? 1 : 0) && ok;
    ok = store_.putInt("injuries", pet.injuries()) && ok;
    ok = store_.putInt("dead", pet.dead() ? 1 : 0) && ok;
    ok = store_.putInt("cold", pet.cold() ? 1 : 0) && ok;
    ok = store_.putInt("dna0", pet.dna()[0]) && ok;
    ok = store_.putInt("dna1", pet.dna()[1]) && ok;
    ok = store_.putInt("dna2", pet.dna()[2]) && ok;
    ok = store_.putInt("dna3", pet.dna()[3]) && ok;
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
    return ok;
}

bool SettingsStore::hasBackup() const {
    return backup_ != nullptr && backup_->getInt("schema", 0) != 0;
}

SpeciesId SettingsStore::backupSpecies() const {
    if (!hasBackup()) return SpeciesId::Egg;
    return static_cast<SpeciesId>(backup_->getInt("species", static_cast<int>(SpeciesId::Egg)));
}

bool SettingsStore::swapOrPark(PetState& pet, Settings& settings) {
    if (backup_ == nullptr) return false;
    SettingsStore parkedStore(*backup_);
    if (!hasBackup()) {
        if (!parkedStore.save(pet, settings)) return false;
        pet.resetToEgg();
        return save(pet, settings);
    }
    PetState parked;
    Settings ignored;
    if (parkedStore.load(parked, ignored) != LoadResult::Loaded) return false;
    if (!parkedStore.save(pet, settings)) return false;
    pet = parked;
    return save(pet, settings);
}

}  // namespace vpet
