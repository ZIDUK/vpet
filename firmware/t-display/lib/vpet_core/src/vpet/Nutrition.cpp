#include "vpet/Nutrition.h"

namespace vpet {

uint8_t referenceWeight(SpeciesId species) {
    switch (species) {
        case SpeciesId::Baby: return 5;
        case SpeciesId::Rookie: return 10;
        case SpeciesId::Champion: return 20;
        case SpeciesId::Ultimate: return 35;
        case SpeciesId::Egg: return 0;
    }
    return 0;
}

BodyCondition bodyCondition(SpeciesId species, uint8_t weight) {
    const uint8_t reference = referenceWeight(species);
    const uint8_t safeWeight = weight < 1 ? 1 : (weight > 99 ? 99 : weight);
    if (reference == 0) return BodyCondition{0, 100, 0, 0, 0};
    const uint16_t ratio = static_cast<uint16_t>((100U * safeWeight + reference / 2U) / reference);
    const uint16_t lowExcess = ratio < 80 ? 80 - ratio : 0;
    const uint16_t highExcess = ratio > 120 ? ratio - 120 : 0;
    const uint8_t low = static_cast<uint8_t>(lowExcess == 0 ? 0 : ((lowExcess + 1) / 2 > 15 ? 15 : (lowExcess + 1) / 2));
    const uint8_t high = static_cast<uint8_t>(highExcess == 0 ? 0 : ((highExcess + 1) / 2 > 20 ? 20 : (highExcess + 1) / 2));
    return BodyCondition{reference, ratio, low, low, high};
}

uint8_t effectiveStat(uint8_t base, uint8_t penalty) {
    if (base < 1) base = 1;
    if (base > 99) base = 99;
    if (penalty > 100) penalty = 100;
    const uint16_t value = (static_cast<uint16_t>(base) * (100U - penalty) + 50U) / 100U;
    return static_cast<uint8_t>(value < 1 ? 1 : value);
}

uint8_t evolvedWeight(SpeciesId from, SpeciesId to, uint8_t weight) {
    const uint8_t source = referenceWeight(from);
    const uint8_t target = referenceWeight(to);
    if (source == 0 || target == 0) return weight < 1 ? 1 : (weight > 99 ? 99 : weight);
    const uint8_t safeWeight = weight < 1 ? 1 : (weight > 99 ? 99 : weight);
    uint16_t scaled = (static_cast<uint16_t>(safeWeight) * target + source / 2U) / source;
    if (scaled < 1) scaled = 1;
    if (scaled > 99) scaled = 99;
    return static_cast<uint8_t>(scaled);
}

uint8_t migrateLegacyWeight(SpeciesId species, uint8_t weight) {
    const uint8_t reference = referenceWeight(species);
    if (reference == 0) return weight < 1 ? 1 : (weight > 99 ? 99 : weight);
    const uint8_t low = static_cast<uint8_t>((80U * reference + 99U) / 100U);
    const uint8_t high = static_cast<uint8_t>((120U * reference) / 100U);
    const uint8_t safeWeight = weight < 1 ? 1 : (weight > 99 ? 99 : weight);
    if (safeWeight < low) return low;
    if (safeWeight > high) return high;
    return safeWeight;
}

FoodResult applyFood(PetState& pet, FoodId food) {
    if (food != FoodId::Meat && food != FoodId::Protein) return FoodResult::Invalid;
    if (pet.species() == SpeciesId::Egg) return FoodResult::Egg;
    if (pet.dead()) return FoodResult::Dead;
    if (pet.cold()) return FoodResult::Frozen;
    if (food == FoodId::Meat) {
        if (pet.hunger() >= 100 && pet.overfedThisCycle()) return FoodResult::Cycle;
        const int hungerGain = pet.hunger() >= 100 ? 0 : (pet.hunger() + items::kMeatHunger > 100 ? 100 - pet.hunger() : items::kMeatHunger);
        pet.setHunger(pet.hunger() + items::kMeatHunger);
        pet.setWeight(static_cast<uint8_t>(pet.weight() <= 99 - items::kMeatWeight ? pet.weight() + items::kMeatWeight : 99));
        pet.noteMeal(hungerGain == 0);
        return FoodResult::Applied;
    }
    if (pet.proteinFedThisCycle()) return FoodResult::Cycle;
    if (pet.energy() > 100 - items::kProteinEnergy) return FoodResult::Full;
    pet.setEnergy(pet.energy() + items::kProteinEnergy);
    pet.setWeight(static_cast<uint8_t>(pet.weight() <= 99 - items::kProteinWeight ? pet.weight() + items::kProteinWeight : 99));
    pet.noteProteinMeal();
    return FoodResult::Applied;
}

}  // namespace vpet
