#include <iostream>
#include "vpet/PracticeBattle.h"

int main() {
    using namespace vpet::practice;
    const Element targets[] = {Element::Fire, Element::Plant, Element::Water};
    for (Element target : targets) {
        Battle battle;
        const int stats[] = {25, 20, 24, 20, 22, 20};
        battle.player.init(stats);
        battle.player.equipped = 1 << 1;
        battle.player.bond = 100;
        battle.player.element = Element::Fire;
        battle.rival.init(stats);
        battle.rival.equipped = 1;
        battle.rival.element = target;
        battle.step(1);
        std::cout << battle.actions[0] << ',' << battle.damage[0] << '\n';
    }
    std::cout << elementalDamage(27, Element::Water, Element::Fire, false) << '\n';
    std::cout << elementalDamage(3, Element::Fire, Element::Plant, true) << '\n';
    const Element elements[] = {Element::Fire, Element::Plant, Element::Water,
        Element::Electric, Element::Wind, Element::Earth, Element::Light,
        Element::Dark, Element::Neutral};
    for (Element attack : elements) {
        for (Element target : elements) {
            for (int base : {1, 2, 3, 27, 99}) {
                for (bool guarding : {false, true}) {
                    std::cout << elementalDamage(base, attack, target, guarding) << '\n';
                }
            }
        }
    }
}
