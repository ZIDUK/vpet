#pragma once

#include <stdint.h>

namespace vpet {

// Keep the original numeric values stable because they are persisted in NVS.
enum class SpeciesId : uint8_t { Rookie = 0, Champion = 1, Ultimate = 2, Egg = 3, Baby = 4 };
enum class Action : uint8_t { None, Feed, Training, Battle, Rest };

class PetState {
public:
    void tick(uint32_t elapsedMs);
    bool beginAction(Action action);
    bool completeAction();
    void evolveTo(SpeciesId species);
    void restore(SpeciesId species, int hunger, int energy, int happiness, int effort, int health, uint32_t ageSeconds);
    bool hasDiscovered(SpeciesId species) const;

    SpeciesId species() const { return species_; }
    int hunger() const { return hunger_; }
    int energy() const { return energy_; }
    int happiness() const { return happiness_; }
    int effort() const { return effort_; }
    int health() const { return health_; }
    int meals() const { return meals_; }
    int trainingSessions() const { return trainingSessions_; }
    int battles() const { return battles_; }
    uint32_t ageSeconds() const { return ageMs_ / 1000; }
    Action pendingAction() const { return pendingAction_; }

private:
    static int clampStat(int value);

    SpeciesId species_ = SpeciesId::Egg;
    Action pendingAction_ = Action::None;
    int hunger_ = 80;
    int energy_ = 80;
    int happiness_ = 80;
    int effort_ = 0;
    int health_ = 100;
    int meals_ = 0;
    int trainingSessions_ = 0;
    int battles_ = 0;
    uint32_t ageMs_ = 0;
    uint32_t decayMs_ = 0;
    bool championDiscovered_ = false;
    bool ultimateDiscovered_ = false;
    bool rookieDiscovered_ = false;
};

}  // namespace vpet
