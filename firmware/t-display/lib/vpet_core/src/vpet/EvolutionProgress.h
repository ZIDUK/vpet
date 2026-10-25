#pragma once

#include "vpet/Evolution.h"

namespace vpet { namespace evolution_progress {
constexpr uint8_t rowsPerPage = 4;
constexpr SpeciesId stages[] = {SpeciesId::Egg, SpeciesId::Baby, SpeciesId::Rookie,
                               SpeciesId::Champion, SpeciesId::Ultimate};
enum class State : uint8_t { Progress, Reached, Hidden, Final, Egg, Unavailable };
enum class Kind : uint8_t { Time, Mistakes, Battles, Wins, Hunger, Energy, Mood, Health, Weight };
struct Row {
    Kind kind;
    uint32_t current, target, upper, remaining;
    bool met;
};
struct Progress {
    State state = State::Progress;
    uint8_t stage = 0, count = 0;
    Row rows[9]{};
    uint8_t pages() const { return count ? (count + rowsPerPage - 1) / rowsPerPage : 1; }
    void add(Kind kind, uint32_t current, uint32_t target, bool met, uint32_t upper = 0, uint32_t remaining = 0) {
        rows[count++] = {kind, current, target, upper, remaining, met};
    }
};
inline const char* name(uint8_t stage) {
    static const char* const names[] = {"EGG", "SPARKMON", "FIREMON", "FLAMEMON", "DRAGFIREMON"};
    return names[stage % 5];
}
inline uint8_t stageFor(SpeciesId species) {
    for (uint8_t i = 0; i < 5; ++i) if (stages[i] == species) return i;
    return 0;
}
inline Progress forPet(const PetState& pet, uint8_t selected, uint32_t scale = 1) {
    Progress p;
    p.stage = selected % 5;
    const uint8_t currentStage = stageFor(pet.species());
    if (p.stage != currentStage) {
        p.state = p.stage < currentStage ? State::Reached : State::Hidden;
        return p;
    }
    if (p.stage == 0) { p.state = State::Egg; return p; }
    const auto* rule = Evolution().ruleFor(pet.species());
    if (!rule) { p.state = State::Final; return p; }
    if (rule->pending || !rule->automatic) { p.state = State::Unavailable; return p; }
    if (!scale) scale = 1;
    if (rule->minStageAgeSeconds) {
        const uint64_t age = static_cast<uint64_t>(pet.stageAgeSeconds()) * scale;
        const uint32_t target = rule->minStageAgeSeconds;
        const uint32_t remaining = age >= target ? 0 : (target - age + scale - 1) / scale;
        p.add(Kind::Time, age > UINT32_MAX ? UINT32_MAX : age, target, age >= target, 0, remaining);
    }
    if (rule->maxCareMistakes >= 0)
        p.add(Kind::Mistakes, pet.careMistakes(), rule->maxCareMistakes, pet.careMistakes() <= rule->maxCareMistakes);
    if (rule->battlesRequired) {
        p.add(Kind::Battles, pet.battles(), rule->battlesRequired, pet.battles() >= rule->battlesRequired);
        const uint32_t played = pet.wins() + pet.losses();
        p.add(Kind::Wins, played ? pet.wins() * 100 / played : 0, 60,
              !played || pet.wins() * 100 >= 60 * played, played);
    }
    if (rule->minHunger) p.add(Kind::Hunger, pet.hunger(), rule->minHunger, pet.hunger() >= rule->minHunger);
    if (rule->minEnergy) p.add(Kind::Energy, pet.energy(), rule->minEnergy, pet.energy() >= rule->minEnergy);
    if (rule->minHappiness) p.add(Kind::Mood, pet.happiness(), rule->minHappiness, pet.happiness() >= rule->minHappiness);
    if (rule->minHealth) p.add(Kind::Health, pet.health(), rule->minHealth, pet.health() >= rule->minHealth);
    if (rule->minWeight || rule->maxWeight) {
        const uint32_t low = rule->minWeight ? rule->minWeight : 1;
        const uint32_t high = rule->maxWeight ? rule->maxWeight : 99;
        p.add(Kind::Weight, pet.weight(), low, pet.weight() >= low && pet.weight() <= high, high);
    }
    return p;
}
} }
