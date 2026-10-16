#pragma once
#include "vpet/PracticeBattle.h"
#include "vpet/AdoptedItems.generated.h"
#include "vpet/PetState.h"
#include <string.h>

namespace vpet { namespace consumables {
inline int recovered(int current, int maximum, int percent) {
    if (maximum <= 0 || percent <= 0 || percent > 100) return current;
    int gain = maximum * percent / 100;
    if (gain < 1) gain = 1;
    int value = (current < 0 ? 0 : current) + gain;
    return value > maximum ? maximum : value;
}
inline bool recover(practice::Fighter& fighter, uint8_t& stock, int hpPercent, int mpPercent) {
    if (!stock || fighter.hp <= 0) return false;
    const int hp = hpPercent ? recovered(fighter.hp, fighter.maxHp, hpPercent) : fighter.hp;
    const int mp = mpPercent ? recovered(fighter.mp, fighter.maxMp, mpPercent) : fighter.mp;
    if (hp == fighter.hp && mp == fighter.mp) return false;
    fighter.hp = hp; fighter.mp = mp; --stock;
    return true;
}
inline bool boost(practice::Fighter& fighter, uint8_t& stock, int stat, int percent) {
    if (!stock || fighter.hp <= 0 || stat < 2 || stat > 5 || percent <= 0 || percent > 40)
        return false;
    if (fighter.itemBoosts[stat] >= percent) return false;
    const int base = fighter.itemBoosts[stat] ? fighter.itemBase[stat] : fighter.stats[stat];
    int gain = base * percent / 100;
    if (gain < 1) gain = 1;
    const int value = base + gain > 99 ? 99 : base + gain;
    if (value == fighter.stats[stat]) return false;
    fighter.itemBase[stat] = base; fighter.itemBoosts[stat] = percent;
    fighter.stats[stat] = value; --stock;
    return true;
}
inline bool use(practice::Battle& battle, uint8_t& stock, uint8_t itemIndex) {
    if (battle.result || !stock || itemIndex >= adopted::kCount) return false;
    const auto& item = adopted::kItems[itemIndex];
    practice::Fighter next = battle.player;
    bool changed = false;
    for (uint8_t n = 0; n < item.effectCount; ++n) {
        const auto& effect = item.effects[n];
        uint8_t one = 1;
        if (strcmp(effect.kind, "restore_percent") == 0) {
            changed = recover(next, one, strcmp(effect.target, "hp") == 0 ? effect.amount : 0,
                              strcmp(effect.target, "mp") == 0 ? effect.amount : 0) || changed;
        } else if (strcmp(effect.kind, "boost_percent") == 0) {
            int stat = strcmp(effect.target, "off") == 0 ? 2 :
                       strcmp(effect.target, "def") == 0 ? 3 :
                       strcmp(effect.target, "spd") == 0 ? 4 : 5;
            changed = boost(next, one, stat, effect.amount) || changed;
        } else return false;
    }
    if (!changed) return false;
    battle.player = next;
    --stock;
    return true;
}
inline bool useHome(PetState& pet, uint8_t& stock, uint8_t itemIndex) {
    if (!stock || pet.dead() || pet.species() == SpeciesId::Egg || itemIndex >= adopted::kCount)
        return false;
    const auto& item = adopted::kItems[itemIndex];
    if (strcmp(item.category, "care") && strcmp(item.category, "condition") &&
        strcmp(item.category, "permanent")) return false;
    if (!strcmp(item.category, "condition") && !pet.injured()) return false;
    PetState next = pet;
    bool changed = false;
    for (uint8_t n = 0; n < item.effectCount; ++n) {
        const auto& effect = item.effects[n];
        if (!strcmp(effect.kind, "ev")) {
            const char* keys[] = {"hp", "mp", "off", "def", "spd", "brn"};
            for (uint8_t i = 0; i < 6; ++i) if (!strcmp(effect.target, keys[i])) {
                const auto stat = static_cast<CombatStat>(i);
                const int before = next.evAt(stat);
                next.addEv(stat, effect.amount);
                changed = next.evAt(stat) != before || changed;
            }
        } else if (!strcmp(effect.kind, "weight")) {
            const int before = next.weight();
            int value = before + effect.amount;
            if (value < 1) value = 1;
            if (value > 99) value = 99;
            next.setWeight(value);
            changed = value != before || changed;
        } else if (!strcmp(effect.kind, "cure")) {
            changed = next.injured() || changed;
            next.setInjured(false);
        } else if (!strcmp(effect.kind, "restore_care")) {
            int before;
            if (!strcmp(effect.target, "h")) {
                before = next.hunger(); next.setHunger(before + effect.amount);
            } else if (!strcmp(effect.target, "p")) {
                before = next.happiness(); next.setHappiness(before + effect.amount);
            } else if (!strcmp(effect.target, "hp")) {
                before = next.health(); next.setHealth(before + effect.amount);
            } else return false;
            changed = before < 100 || changed;
        } else return false;
    }
    if (!changed) return false;
    pet = next; --stock;
    return true;
}
} }
