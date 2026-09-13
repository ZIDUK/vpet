#include "vpet/Evolution.h"

#include <stdio.h>
#include <string.h>

namespace vpet {
namespace {

constexpr EvolutionRule kRules[] = {
    {SpeciesId::Baby, SpeciesId::Rookie, true, false, 43800, 1, 0, 0, 0, 0, 0},
    {SpeciesId::Rookie, SpeciesId::Champion, true, false, 86400, -1, 0, 55, 55, 55, 75},
    {SpeciesId::Champion, SpeciesId::Ultimate, true, false, 129600, -1, 15, 0, 0, 0, 0},
};

bool barsMet(const EvolutionRule& rule, const PetState& pet) {
    if (rule.minHunger == 0 && rule.minEnergy == 0 && rule.minHappiness == 0 && rule.minHealth == 0) {
        return true;
    }
    return pet.hunger() >= rule.minHunger &&
           pet.energy() >= rule.minEnergy &&
           pet.happiness() >= rule.minHappiness &&
           pet.health() >= rule.minHealth;
}

bool winRatioMet(const PetState& pet) {
    const int played = static_cast<int>(pet.wins()) + static_cast<int>(pet.losses());
    if (played == 0) return true;
    return pet.wins() * 100 >= 60 * played;
}

}

const EvolutionRule* Evolution::ruleFor(SpeciesId from) const {
    for (const EvolutionRule& rule : kRules) {
        if (rule.from == from) return &rule;
    }
    return nullptr;
}

bool Evolution::check(const PetState& pet, uint32_t scale, SpeciesId& next) const {
    if (pet.species() == SpeciesId::Egg) return false;
    const EvolutionRule* rule = ruleFor(pet.species());
    if (rule == nullptr || !rule->automatic || rule->pending) return false;
    const uint32_t scaledAge = pet.stageAgeSeconds() * scale;
    if (scaledAge < rule->minStageAgeSeconds) return false;
    if (rule->maxCareMistakes >= 0 && pet.careMistakes() > rule->maxCareMistakes) return false;
    if (!barsMet(*rule, pet)) return false;
    if (pet.battles() < rule->battlesRequired) return false;
    if (rule->battlesRequired > 0 && !winRatioMet(pet)) return false;
    next = rule->to;
    return true;
}

void Evolution::apply(PetState& pet, SpeciesId next) const {
    pet.evolveTo(next);
    pet.resetAfterEvolution();
    pet.record(CareEventType::Evo, static_cast<uint8_t>(next));
}

bool Evolution::evolve(PetState& pet, uint32_t scale) {
    SpeciesId next = SpeciesId::Egg;
    if (!check(pet, scale, next)) return false;
    apply(pet, next);
    return true;
}

bool Evolution::force(PetState& pet) {
    if (!pet.forceNextForm()) return false;
    pet.resetAfterEvolution();
    pet.record(CareEventType::Evo, static_cast<uint8_t>(pet.species()));
    return true;
}

void Evolution::writeRequirements(SpeciesId from, bool spanish, char* buffer, int length) const {
    if (buffer == nullptr || length <= 0) return;
    const EvolutionRule* rule = ruleFor(from);
    if (rule == nullptr) {
        if (from == SpeciesId::Egg) {
            snprintf(buffer, static_cast<size_t>(length), "8S");
        } else {
            snprintf(buffer, static_cast<size_t>(length), "%s", spanish ? "FINAL POR AHORA" : "FINAL FOR NOW");
        }
        return;
    }
    if (rule->pending) {
        buffer[0] = '\0';
        return;
    }
    char parts[4][24];
    uint8_t count = 0;
    const uint32_t hours = rule->minStageAgeSeconds / 3600;
    const uint32_t minutes = (rule->minStageAgeSeconds % 3600) / 60;
    if (minutes == 0) {
        snprintf(parts[count++], sizeof(parts[0]), "%luH", static_cast<unsigned long>(hours));
    } else {
        snprintf(parts[count++], sizeof(parts[0]), "%luH%luM", static_cast<unsigned long>(hours), static_cast<unsigned long>(minutes));
    }
    if (rule->maxCareMistakes >= 0) {
        snprintf(parts[count++], sizeof(parts[0]), "CM<=%d", rule->maxCareMistakes);
    }
    if (rule->battlesRequired > 0) {
        snprintf(parts[count++], sizeof(parts[0]), "BAT%d WR60", rule->battlesRequired);
    }
    if (rule->minHunger > 0 || rule->minEnergy > 0 || rule->minHappiness > 0 || rule->minHealth > 0) {
        snprintf(
            parts[count++],
            sizeof(parts[0]),
            "H%d E%d P%d HP%d",
            rule->minHunger,
            rule->minEnergy,
            rule->minHappiness,
            rule->minHealth
        );
    }
    buffer[0] = '\0';
    for (uint8_t i = 0; i < count; ++i) {
        snprintf(buffer + strlen(buffer), static_cast<size_t>(length) - strlen(buffer), "%s%s", i == 0 ? "" : " ", parts[i]);
    }
}

void Evolution::writeReachRequirements(SpeciesId to, bool spanish, char* buffer, int length) const {
    if (buffer == nullptr || length <= 0) return;
    if (to == SpeciesId::Egg || to == SpeciesId::Baby) {
        snprintf(buffer, static_cast<size_t>(length), "8S");
        return;
    }
    SpeciesId from = SpeciesId::Egg;
    if (to == SpeciesId::Rookie) from = SpeciesId::Baby;
    else if (to == SpeciesId::Champion) from = SpeciesId::Rookie;
    else if (to == SpeciesId::Ultimate) from = SpeciesId::Champion;
    writeRequirements(from, spanish, buffer, length);
}

}  // namespace vpet
