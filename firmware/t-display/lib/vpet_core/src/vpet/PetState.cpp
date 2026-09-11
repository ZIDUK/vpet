#include "vpet/PetState.h"

namespace vpet {

int PetState::clampStat(int value) {
    return value < 0 ? 0 : (value > 100 ? 100 : value);
}

void PetState::tick(uint32_t elapsedMs) {
    ageMs_ += elapsedMs;
    if (species_ == SpeciesId::Egg) return;
    decayMs_ += elapsedMs;
    while (decayMs_ >= 30000) {
        decayMs_ -= 30000;
        hunger_ = clampStat(hunger_ - 1);
        energy_ = clampStat(energy_ - 1);
        happiness_ = clampStat(happiness_ - 1);
    }
}

bool PetState::beginAction(Action action) {
    if (action == Action::None || pendingAction_ != Action::None) {
        return false;
    }
    if (species_ == SpeciesId::Egg) return false;
    if (species_ == SpeciesId::Baby && (action == Action::Training || action == Action::Battle)) {
        return false;
    }
    pendingAction_ = action;
    return true;
}

bool PetState::completeAction() {
    const Action action = pendingAction_;
    pendingAction_ = Action::None;
    switch (action) {
        case Action::Feed:
            hunger_ = clampStat(hunger_ + 20);
            energy_ = clampStat(energy_ + 5);
            ++meals_;
            return true;
        case Action::Training:
            effort_ = clampStat(effort_ + 8);
            energy_ = clampStat(energy_ - 8);
            happiness_ = clampStat(happiness_ + 3);
            ++trainingSessions_;
            return true;
        case Action::Battle:
            energy_ = clampStat(energy_ - 12);
            effort_ = clampStat(effort_ + 4);
            ++battles_;
            return true;
        case Action::Rest:
            energy_ = clampStat(energy_ + 25);
            health_ = clampStat(health_ + 5);
            return true;
        case Action::None:
            return false;
    }
    return false;
}

bool PetState::forceNextForm() {
    switch (species_) {
        case SpeciesId::Egg: evolveTo(SpeciesId::Baby); return true;
        case SpeciesId::Baby: evolveTo(SpeciesId::Rookie); return true;
        case SpeciesId::Rookie: evolveTo(SpeciesId::Champion); return true;
        case SpeciesId::Champion: evolveTo(SpeciesId::Ultimate); return true;
        case SpeciesId::Ultimate: return false;
    }
    return false;
}

void PetState::evolveTo(SpeciesId species) {
    species_ = species;
    if (species == SpeciesId::Rookie) rookieDiscovered_ = true;
    if (species == SpeciesId::Champion) championDiscovered_ = true;
    if (species == SpeciesId::Ultimate) {
        rookieDiscovered_ = true;
        championDiscovered_ = true;
        ultimateDiscovered_ = true;
    }
}

void PetState::restore(
    SpeciesId species,
    int hunger,
    int energy,
    int happiness,
    int effort,
    int health,
    uint32_t ageSeconds
) {
    evolveTo(species);
    hunger_ = clampStat(hunger);
    energy_ = clampStat(energy);
    happiness_ = clampStat(happiness);
    effort_ = clampStat(effort);
    health_ = clampStat(health);
    ageMs_ = ageSeconds * 1000U;
}

bool PetState::hasDiscovered(SpeciesId species) const {
    if (species == SpeciesId::Egg || species == SpeciesId::Baby) return true;
    if (species == SpeciesId::Rookie) return rookieDiscovered_;
    if (species == SpeciesId::Champion) return championDiscovered_;
    return ultimateDiscovered_;
}

}  // namespace vpet
