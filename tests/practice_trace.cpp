#include <iostream>
#include "vpet/PracticeBattle.h"

int main() {
    // The Python `test_python_cpp_round_traces_match` runs 24 scenarios with
    // alternating equipment patterns; keep the harness in lockstep so the
    // round-trip continues to hold.
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
    // Extended sweep: cover every technique + every personality with mastery
    // enabled, so any drift introduced after Phase 6 tuning is caught early.
    for (int scenario = 24; scenario < 56; ++scenario) {
        vpet::practice::Battle b;
        int values[6];
        for (int i = 0; i < 6; ++i) values[i] = 1 + (scenario * 11 + i * 7) % 99;
        b.player.init(values);
        int rivalValues[6];
        for (int i = 0; i < 6; ++i) rivalValues[i] = 1 + (scenario * 5 + i * 3) % 99;
        b.rival.init(rivalValues);
        b.player.personality = scenario % 3;
        b.player.bond = scenario * 3 + 1;
        if (scenario % 3 == 0) b.player.equipped = 5;      // punch + guard
        else if (scenario % 3 == 1) b.player.equipped = 3; // punch + flame
        else b.player.equipped = 7;                        // all three
        for (int i = 0; i < 3; ++i) b.player.mastery[i] = (scenario * 7 + i * 13) % 101;
        int rounds = 0;
        while (!b.result && rounds < 30) {
            int order = rounds % 3 == 0 ? -1 : (rounds % 3) - 1;
            b.step(order);
            std::cout << scenario << ',' << b.round << ',' << b.player.hp << ',' << b.player.mp << ','
                      << b.rival.hp << ',' << b.rival.mp << ',' << b.actions[0] << ',' << b.actions[1]
                      << ',' << b.result << '\n';
            ++rounds;
        }
    }
}
