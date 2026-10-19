#pragma once

#include <stdint.h>

#include "vpet/PetState.h"

namespace vpet {

struct BodyCondition {
    uint8_t reference;
    uint16_t ratio;
    uint8_t offPenalty;
    uint8_t defPenalty;
    uint8_t spdPenalty;
};

uint8_t referenceWeight(SpeciesId species);
BodyCondition bodyCondition(SpeciesId species, uint8_t weight);
uint8_t effectiveStat(uint8_t base, uint8_t penalty);
uint8_t evolvedWeight(SpeciesId from, SpeciesId to, uint8_t weight);
uint8_t migrateLegacyWeight(SpeciesId species, uint8_t weight);

enum class FoodId : uint8_t { Meat = 0, Protein = 1 };
enum class FoodResult : uint8_t { Applied, Invalid, Egg, Dead, Frozen, Full, Cycle, Asleep };
FoodResult applyFood(PetState& pet, FoodId food);

}  // namespace vpet
