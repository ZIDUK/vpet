#include "vpet/SettingsStore.h"

namespace vpet {

LoadResult SettingsStore::load(PetState& pet, Settings& settings) {
    const int version = store_.getInt("schema", 0);
    if (version == 0) {
        pet.evolveTo(pet.species());
        return LoadResult::Missing;
    }
    if (version != 1) return LoadResult::Unsupported;
    pet.restore(
        static_cast<SpeciesId>(store_.getInt("species", 0)),
        store_.getInt("hunger", 80),
        store_.getInt("energy", 80),
        store_.getInt("happy", 80),
        store_.getInt("effort", 0),
        store_.getInt("health", 100),
        store_.getInt("age", 0)
    );
    settings.language = store_.getString("language", "ES");
    settings.soundEnabled = store_.getInt("sound", 1) != 0;
    return LoadResult::Loaded;
}

bool SettingsStore::save(const PetState& pet, const Settings& settings) {
    bool ok = store_.putInt("schema", 1);
    ok = store_.putInt("species", static_cast<int>(pet.species())) && ok;
    ok = store_.putInt("hunger", pet.hunger()) && ok;
    ok = store_.putInt("energy", pet.energy()) && ok;
    ok = store_.putInt("happy", pet.happiness()) && ok;
    ok = store_.putInt("effort", pet.effort()) && ok;
    ok = store_.putInt("health", pet.health()) && ok;
    ok = store_.putInt("age", pet.ageSeconds()) && ok;
    ok = store_.putString("language", settings.language.c_str()) && ok;
    ok = store_.putInt("sound", settings.soundEnabled ? 1 : 0) && ok;
    return ok;
}

}  // namespace vpet
