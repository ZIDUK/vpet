#include <iostream>
#include "vpet/PracticeBattle.h"

int main() {
    using namespace vpet::practice;
    Battle battle;
    battle.round = 1;
    battle.actions[0] = 0;
    battle.actions[1] = 2;
    battle.damage[0] = 8;
    std::cout << presentationAction(battle, 0) << ',' << presentationAction(battle, 1) << '\n';

    battle.damage[0] = 0;
    std::cout << presentationAction(battle, 0) << ',' << presentationAction(battle, 1) << '\n';

    battle.actions[0] = 0;
    battle.actions[1] = 0;
    battle.damage[0] = 8;
    battle.damage[1] = 5;
    std::cout << presentationAction(battle, 0) << ',' << presentationAction(battle, 1) << '\n';

    battle.round = 0;
    std::cout << kImpactMs << ',' << presentationAction(battle, 0) << '\n';
}
