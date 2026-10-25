#include <assert.h>
#include <iostream>
#include <string>
#include "vpet/GrowthPilot.h"
#include "vpet/PracticeBattle.h"

int main(int argc, char** argv) {
    using namespace vpet::growth_pilot;
    if (argc > 1 && std::string(argv[1]) == "battle") {
        vpet::practice::Battle battle;
        for (auto* fighter : {&battle.player, &battle.rival}) {
            // Host-only fixture bypasses init's 99 clamp; never used by App.
            for (int& stat : fighter->stats) {
                if (!(std::cin >> stat) || stat < 1 || stat > 320) return 2;
            }
            fighter->hp = fighter->maxHp = 40 + 2 * fighter->stats[0];
            fighter->mp = fighter->maxMp = 10 + fighter->stats[1];
            fighter->personality = 0;
            fighter->equipped = 31;
            fighter->element = vpet::practice::Element::Fire;
        }
        while (battle.step()) {
            std::cout << battle.round << ' ' << battle.player.hp << ' ' << battle.rival.hp
                      << ' ' << battle.player.mp << ' ' << battle.rival.mp
                      << ' ' << battle.actions[0] << ' ' << battle.actions[1]
                      << ' ' << battle.damage[0] << ' ' << battle.damage[1] << '\n';
        }
        return 0;
    }
    Point invalid;
    for (int iv : {-1, 16}) assert(!point(iv, 0, 1, 3, invalid));
    for (int ev : {-1, 253}) assert(!point(0, ev, 1, 3, invalid));
    for (int rank : {0, 4}) assert(!point(0, 0, rank, 3, invalid));
    for (int ranks : {0, 4}) assert(!point(0, 0, 1, ranks, invalid));
    assert(!point(0, 0, 2, 1, invalid));
    Projection t;
    for (int gain : {-1, 0, 253}) assert(!projectTraining(0, 0, 1, 3, gain, t));
    for (int ranks : {1, 2, 3}) for (int rank = 1; rank <= ranks; ++rank)
        for (int iv = 0; iv < 16; ++iv) for (int ev = 0; ev <= 252; ++ev)
            for (int gain : {1, 6, 7, 252}) {
                assert(projectTraining(iv, ev, rank, ranks, gain, t));
                const auto& p = t.before;
                std::cout << p.base << ' ' << p.cap << ' ' << p.capEv << ' ' << p.stat
                          << ' ' << p.activeEv << ' ' << p.storedEv << ' ' << t.added
                          << ' ' << static_cast<int>(t.energyCost) << ' ' << t.after.stat
                          << ' ' << t.after.storedEv << '\n';
            }
}
