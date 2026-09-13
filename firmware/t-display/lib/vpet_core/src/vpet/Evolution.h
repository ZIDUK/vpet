#pragma once

#include "vpet/PetState.h"

namespace vpet {

struct EvolutionRule {
    SpeciesId from;
    SpeciesId to;
    bool automatic;
    bool pending;
    uint32_t minStageAgeSeconds;
    int8_t maxCareMistakes;
    uint8_t battlesRequired;
    uint8_t minHunger;
    uint8_t minEnergy;
    uint8_t minHappiness;
    uint8_t minHealth;
};

class Evolution {
public:
    bool check(const PetState& pet, uint32_t scale, SpeciesId& next) const;
    bool evolve(PetState& pet, uint32_t scale);
    bool force(PetState& pet);
    const EvolutionRule* ruleFor(SpeciesId from) const;
    void writeRequirements(SpeciesId from, bool spanish, char* buffer, int length) const;
    void writeReachRequirements(SpeciesId to, bool spanish, char* buffer, int length) const;

private:
    void apply(PetState& pet, SpeciesId next) const;
};

}  // namespace vpet
