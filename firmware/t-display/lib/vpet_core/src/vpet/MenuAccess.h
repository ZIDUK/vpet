#pragma once
#include "vpet/PetState.h"

namespace vpet { namespace menu_access {
constexpr uint8_t count = 9;

inline bool availableAtStage(SpeciesId species, uint8_t index) {
    if (index == 2 || index == 3 || index == 4)
        return species != SpeciesId::Egg && species != SpeciesId::Baby;
    if (index == 1 || index == 5) return species != SpeciesId::Egg;
    return true;
}

inline uint8_t next(SpeciesId species, uint8_t index) {
    for (uint8_t checked = 0; checked < count; ++checked) {
        index = (index + 1) % count;
        if (availableAtStage(species, index)) return index;
    }
    return 0;
}
} }
