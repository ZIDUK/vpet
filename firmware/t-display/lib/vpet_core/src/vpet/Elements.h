#pragma once

#include <stdint.h>

namespace vpet {
namespace practice {

enum class Element : uint8_t {
    None, Fire, Plant, Water, Electric, Wind, Earth, Light, Dark, Neutral
};

inline bool elementBeats(Element attack, Element target) {
    return (attack == Element::Fire && target == Element::Plant) ||
           (attack == Element::Plant && target == Element::Water) ||
           (attack == Element::Water && target == Element::Fire) ||
           (attack == Element::Electric && target == Element::Wind) ||
           (attack == Element::Wind && target == Element::Earth) ||
           (attack == Element::Earth && target == Element::Electric) ||
           (attack == Element::Light && target == Element::Dark) ||
           (attack == Element::Dark && target == Element::Light);
}

inline Element techniqueElement(int action) {
    return action == 0 ? Element::Neutral :
           action == 1 ? Element::Fire : Element::None;
}

inline int elementalDamage(int baseDamage, Element attack, Element target, bool guarding) {
    int damage = baseDamage < 1 ? 1 : baseDamage;
    if (elementBeats(attack, target)) damage = damage * 3 / 2;
    if (guarding) {
        damage /= 2;
        if (damage < 1) damage = 1;
    }
    return damage;
}

}  // namespace practice
}  // namespace vpet
