#include <iostream>
#include "vpet/PracticeBattle.h"
int main() {
    using namespace vpet;
    for (int scenario=0;scenario<48;++scenario) {
        practice::Battle b;
        int stats[6];
        for (int i=0;i<6;++i) stats[i]=1+(scenario*7+i*11)%99;
        b.player.init(stats);
        b.player.equipped=scenario%2 ? 27 : 29;
        b.player.personality=scenario%3;
        b.player.bond=100;
        b.player.element=practice::Element::Fire;
        b.rival.element=scenario%3==0 ? practice::Element::Plant : scenario%3==1 ? practice::Element::Water : practice::Element::Fire;
        for (int i=0;i<techniques::kCount;++i) b.player.mastery[i]=(scenario*3+i*17)%101;
        while (!b.result) {
            b.step(b.round%3==0 ? -1 : b.round%2 ? 3 : 4);
            std::cout<<scenario<<','<<b.round<<','<<b.player.hp<<','<<b.player.mp<<','<<b.rival.hp<<','<<b.rival.mp<<','
                <<b.actions[0]<<','<<b.actions[1]<<','<<b.damage[0]<<','<<b.damage[1]<<','
                <<int(b.player.cooldown[3])<<','<<int(b.player.cooldown[4])<<','<<b.result<<'\n';
        }
    }
}
