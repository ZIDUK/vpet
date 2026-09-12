#include "vpet/PetState.h"

namespace vpet {

int PetState::clampStat(int value) {
    return value < 0 ? 0 : (value > 100 ? 100 : value);
}

namespace {
uint8_t clampItem(int value) {
    if (value < 0) return 0;
    if (value > 99) return 99;
    return static_cast<uint8_t>(value);
}
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

void PetState::restoreItems(uint8_t meat, uint8_t energyItem, uint8_t expItem, uint8_t ring) {
    meat_ = clampItem(meat);
    energyItem_ = clampItem(energyItem);
    expItem_ = clampItem(expItem);
    ring_ = clampItem(ring);
}

uint8_t PetState::itemCount(uint8_t index) const {
    switch (index) {
        case 0: return meat_;
        case 1: return energyItem_;
        case 2: return expItem_;
        case 3: return ring_;
        default: return 0;
    }
}

ItemUseResult PetState::useItem(uint8_t index) {
    if (index == 4) return ItemUseResult::Back;
    if (index > 3) return ItemUseResult::Empty;
    if (species_ == SpeciesId::Egg) return ItemUseResult::Blocked;
    uint8_t* stock = nullptr;
    switch (index) {
        case 0: stock = &meat_; break;
        case 1: stock = &energyItem_; break;
        case 2: stock = &expItem_; break;
        case 3: stock = &ring_; break;
    }
    if (stock == nullptr || *stock == 0) return ItemUseResult::Empty;
    --(*stock);
    switch (index) {
        case 0: hunger_ = clampStat(hunger_ + 20); break;
        case 1: energy_ = clampStat(energy_ + 25); break;
        case 2: effort_ = clampStat(effort_ + 8); break;
        case 3: happiness_ = clampStat(happiness_ + 15); break;
    }
    return ItemUseResult::Used;
}

bool PetState::itemVisible(uint8_t index) const {
    if (index == 4) return true;
    return index < 4 && itemCount(index) > 0;
}

uint8_t PetState::visibleInventoryCount() const {
    uint8_t count = 1;
    for (uint8_t index = 0; index < 4; ++index) {
        if (itemVisible(index)) ++count;
    }
    return count;
}

uint8_t PetState::inventoryIndexAt(uint8_t visibleSlot) const {
    uint8_t slot = 0;
    for (uint8_t index = 0; index < 5; ++index) {
        if (!itemVisible(index)) continue;
        if (slot == visibleSlot) return index;
        ++slot;
    }
    return 4;
}

uint8_t PetState::nextVisibleInventoryIndex(uint8_t index) const {
    for (uint8_t step = 1; step <= 5; ++step) {
        const uint8_t candidate = static_cast<uint8_t>((index + step) % 5);
        if (itemVisible(candidate)) return candidate;
    }
    return 4;
}

uint8_t PetState::clampVisibleInventoryIndex(uint8_t index) const {
    return itemVisible(index) ? index : nextVisibleInventoryIndex(index);
}

bool PetState::hasDiscovered(SpeciesId species) const {
    if (species == SpeciesId::Egg || species == SpeciesId::Baby) return true;
    if (species == SpeciesId::Rookie) return rookieDiscovered_;
    if (species == SpeciesId::Champion) return championDiscovered_;
    return ultimateDiscovered_;
}

}  // namespace vpet
