#include <iostream>
#include "vpet/UiCue.h"
int main() {
    int h,e,p,inj,tired,hcall,rcall,x,y,facing;
    while(std::cin>>h>>e>>p>>inj>>tired>>hcall>>rcall>>x>>y>>facing) {
        const auto c=vpet::cue::classify(h,e,p,inj,tired,hcall,rcall);
        const auto pos=vpet::cue::position(x,y,facing);
        std::cout<<int(c.need)<<' '<<int(c.face)<<' '<<c.angry<<' '<<pos.x<<' '<<pos.y<<' '<<pos.flip<<'\n';
    }
}
