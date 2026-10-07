#include <iostream>
#include "vpet/PracticeBattle.h"

int main() {
    for (int scenario = 0; scenario < 24; ++scenario) {
        vpet::practice::Battle b;
        int values[6];
        for (int i = 0; i < 6; ++i) values[i] = 1 + (scenario * 7 + i * 13) % 99;
        b.player.init(values);
        b.player.personality = scenario % 3;
        b.player.bond = scenario * 4;
        b.player.equipped = scenario % 2 ? 3 : 5;
        while (!b.result) {
            int order = b.round % 3 == 0 ? -1 : 0;
            b.step(order);
            std::cout << scenario << ',' << b.round << ',' << b.player.hp << ',' << b.player.mp << ','
                      << b.rival.hp << ',' << b.rival.mp << ',' << b.actions[0] << ',' << b.actions[1]
                      << ',' << b.result << '\n';
        }
    }
}
